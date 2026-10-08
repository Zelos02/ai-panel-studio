from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ..domain import ExpertKind, SessionStatus, TopicStatus
from ..errors import AppError
from ..events import EventHub, EventStore
from ..llm import LLMAgentGateway, LLMProvider, ValidatedLLMClient
from ..models import Expert, ExpertStatus, PanelSession, Topic, TranscriptMessage
from ..orchestration import (
    AgentProfile,
    OrchestrationEvent,
    PanelOrchestrator,
    PanelRunState,
    SentencePolicy,
    TranscriptEntry,
)

logger = logging.getLogger("panel_studio.discussion")


class PersistentEventSink:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        hub: EventHub,
    ) -> None:
        self.session_factory = session_factory
        self.hub = hub
        self.sentence_policy = SentencePolicy()

    async def __call__(self, event: OrchestrationEvent) -> None:
        with self.session_factory() as db:
            panel_session = db.get(PanelSession, event.session_id)
            if panel_session is None:
                raise AppError("RESOURCE_NOT_FOUND", "没有找到这场讨论。", status_code=404)
            topic = db.get(Topic, panel_session.topic_id)
            payload = dict(event.payload)

            if event.event_type == "session.state":
                status = str(payload["status"])
                panel_session.status = status
                panel_session.version += 1
                if status == SessionStatus.RUNNING.value:
                    panel_session.started_at = panel_session.started_at or datetime.now(timezone.utc)
                    if topic:
                        topic.status = TopicStatus.RUNNING.value
                elif status == SessionStatus.COMPLETED.value:
                    panel_session.ended_at = datetime.now(timezone.utc)
                    if topic:
                        topic.status = TopicStatus.COMPLETED.value
                elif status == SessionStatus.FAILED.value and topic:
                    topic.status = TopicStatus.FAILED.value

            elif event.event_type == "expert.status":
                status_row = db.scalar(
                    select(ExpertStatus).where(
                        ExpertStatus.session_id == event.session_id,
                        ExpertStatus.expert_id == payload["expertId"],
                    )
                )
                if status_row is not None:
                    status_row.state = str(payload["state"])
                    status_row.public_focus = str(payload.get("publicFocus") or "")[:300]
                    status_row.version += 1

            elif event.event_type == "transcript.append":
                expert = db.get(Expert, payload["speakerId"])
                content = str(payload["content"])
                message = TranscriptMessage(
                    session_id=event.session_id,
                    speaker_expert_id=expert.id if expert else None,
                    speaker_role=str(payload["speakerRole"]),
                    sequence=int(payload["sequence"]),
                    content=content,
                    sentence_count=self.sentence_policy.count(content),
                )
                db.add(message)
                db.flush()
                payload = {
                    "message": {
                        "id": message.id,
                        "sequence": message.sequence,
                        "content": message.content,
                        "createdAt": message.created_at.isoformat().replace("+00:00", "Z"),
                        "speaker": {
                            "id": expert.id if expert else payload["speakerId"],
                            "name": expert.name if expert else "系统",
                            "title": expert.title if expert else "",
                            "color": expert.color if expert else "#8093A8",
                            "role": payload["speakerRole"],
                        },
                    }
                }
                if payload["message"]["speaker"]["role"] == ExpertKind.EXPERT.value:
                    panel_session.turn_count += 1

            stored = EventStore(db).append(event.session_id, event.event_type, payload)
            db.commit()
        await self.hub.publish(event.session_id, stored)


class DiscussionRunner:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        provider: LLMProvider,
        hub: EventHub,
    ) -> None:
        self.session_factory = session_factory
        self.provider = provider
        self.hub = hub

    async def run(self, session_id: str) -> None:
        state = self._load_state(session_id)
        sink = PersistentEventSink(session_factory=self.session_factory, hub=self.hub)
        gateway = LLMAgentGateway(ValidatedLLMClient(self.provider))
        orchestrator = PanelOrchestrator(gateway=gateway, event_sink=sink)
        try:
            await orchestrator.run(state)
        except Exception as exc:
            logger.exception(
                "discussion_failed session_id=%s error_type=%s",
                session_id,
                type(exc).__name__,
            )
            await sink(
                OrchestrationEvent(
                    event_type="stream.error",
                    session_id=session_id,
                    payload={
                        "code": "DISCUSSION_FAILED",
                        "message": "讨论暂时中断，可以稍后重试。",
                        "retryable": True,
                    },
                )
            )

    def _load_state(self, session_id: str) -> PanelRunState:
        with self.session_factory() as db:
            panel_session = db.get(PanelSession, session_id)
            if panel_session is None:
                raise AppError("RESOURCE_NOT_FOUND", "没有找到这场讨论。", status_code=404)
            if panel_session.status not in {
                SessionStatus.ADMITTED.value,
                SessionStatus.PAUSED.value,
            }:
                raise AppError(
                    "PANEL_INVALID_STATE", "当前讨论状态不能启动。", status_code=409
                )
            topic = db.get(Topic, panel_session.topic_id)
            members = list(
                db.scalars(
                    select(Expert)
                    .where(Expert.topic_id == panel_session.topic_id, Expert.admitted.is_(True))
                    .order_by(Expert.display_order)
                )
            )
            host_model = next((item for item in members if item.kind == ExpertKind.HOST.value), None)
            expert_models = [item for item in members if item.kind == ExpertKind.EXPERT.value]
            if topic is None or host_model is None or not expert_models:
                raise AppError(
                    "PANEL_INVALID_STATE", "讨论阵容不完整，无法启动。", status_code=409
                )
            messages = list(
                db.scalars(
                    select(TranscriptMessage)
                    .where(TranscriptMessage.session_id == session_id)
                    .order_by(TranscriptMessage.sequence)
                )
            )
            return PanelRunState(
                topic_id=topic.id,
                session_id=panel_session.id,
                title=topic.title,
                host=self._profile(host_model),
                experts=[self._profile(model) for model in expert_models],
                status=panel_session.status,
                max_turns=panel_session.max_turns,
                turn_count=panel_session.turn_count,
                transcript=[
                    TranscriptEntry(
                        session_id=session_id,
                        sequence=message.sequence,
                        speaker_id=message.speaker_expert_id or "system",
                        speaker_role=message.speaker_role,
                        content=message.content,
                    )
                    for message in messages
                ],
            )

    @staticmethod
    def _profile(model: Expert) -> AgentProfile:
        return AgentProfile(
            id=model.id,
            name=model.name,
            title=model.title,
            stance=model.stance,
            color=model.color,
            kind=model.kind,
        )
