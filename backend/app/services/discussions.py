from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ..domain import ExpertKind, SessionStatus, TopicStatus
from ..errors import AppError
from ..events import EventHub, EventStore
from ..llm import LLMAgentGateway, LLMContractError, LLMProvider, ValidatedLLMClient
from ..llm.contracts import BranchSuggestion, SessionSummaryResult
from ..llm.prompts import BRANCH_SYSTEM, SUMMARY_SYSTEM
from ..models import (
    Expert,
    ExpertStatus,
    KnowledgeBranch,
    PanelSession,
    SessionSummary,
    Topic,
    TranscriptMessage,
)
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

    async def __call__(self, event: OrchestrationEvent) -> dict:
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

            elif event.event_type == "branch.created":
                branch_data = payload["branch"]
                branch = KnowledgeBranch(
                    session_id=event.session_id,
                    source_message_id=branch_data["sourceMessageId"],
                    branch_type=branch_data["branchType"],
                    title=branch_data["title"],
                    summary=branch_data["summary"],
                    fingerprint=branch_data["fingerprint"],
                )
                db.add(branch)
                db.flush()
                payload = {
                    "branch": {
                        "id": branch.id,
                        "branchType": branch.branch_type,
                        "title": branch.title,
                        "summary": branch.summary,
                        "sourceMessageId": branch.source_message_id,
                    }
                }

            elif event.event_type == "summary.ready":
                summary = db.scalar(
                    select(SessionSummary).where(SessionSummary.session_id == event.session_id)
                )
                if summary is None:
                    summary = SessionSummary(session_id=event.session_id, natural_text="")
                    db.add(summary)
                summary.natural_text = str(payload["naturalText"])
                summary.structured_json = json.dumps(payload["structured"], ensure_ascii=False)
                payload = {"naturalText": summary.natural_text}

            stored = EventStore(db).append(event.session_id, event.event_type, payload)
            db.commit()
        await self.hub.publish(event.session_id, stored)
        return stored


class DiscussionEventPipeline:
    def __init__(self, *, sink: PersistentEventSink, provider: LLMProvider) -> None:
        self.sink = sink
        self.client = ValidatedLLMClient(provider)

    async def __call__(self, event: OrchestrationEvent) -> None:
        stored = await self.sink(event)
        if event.event_type == "transcript.append":
            message = stored["payload"]["message"]
            if message["speaker"]["role"] == ExpertKind.EXPERT.value:
                await self._maybe_create_branch(event.session_id, message)
        elif event.event_type == "session.state" and event.payload.get("status") == "completed":
            await self._create_summary(event.session_id)

    async def _maybe_create_branch(self, session_id: str, message: dict) -> None:
        try:
            suggestion = await self.client.call(
                BranchSuggestion,
                system_prompt=BRANCH_SYSTEM,
                user_prompt=(
                    f"最新发言 ID：{message['id']}\n"
                    f"发言人：{message['speaker']['name']}\n"
                    f"内容：{message['content']}"
                ),
            )
        except LLMContractError as exc:
            logger.warning(
                "branch_detection_skipped session_id=%s error_type=%s",
                session_id,
                type(exc).__name__,
            )
            return
        if not suggestion.shouldCreate:
            return
        fingerprint = hashlib.sha256(
            f"{suggestion.branchType}:{suggestion.title}".lower().encode("utf-8")
        ).hexdigest()
        with self.sink.session_factory() as db:
            existing = db.scalar(
                select(KnowledgeBranch.id).where(
                    KnowledgeBranch.session_id == session_id,
                    KnowledgeBranch.fingerprint == fingerprint,
                )
            )
        if existing is not None:
            return
        await self.sink(
            OrchestrationEvent(
                event_type="branch.created",
                session_id=session_id,
                payload={
                    "branch": {
                        "branchType": suggestion.branchType,
                        "title": suggestion.title,
                        "summary": suggestion.summary,
                        "sourceMessageId": message["id"],
                        "fingerprint": fingerprint,
                    }
                },
            )
        )

    async def _create_summary(self, session_id: str) -> None:
        with self.sink.session_factory() as db:
            messages = list(
                db.scalars(
                    select(TranscriptMessage)
                    .where(TranscriptMessage.session_id == session_id)
                    .order_by(TranscriptMessage.sequence)
                )
            )
            public_transcript = [
                {"role": message.speaker_role, "content": message.content}
                for message in messages
            ]
        try:
            summary = await self.client.call(
                SessionSummaryResult,
                system_prompt=SUMMARY_SYSTEM,
                user_prompt=json.dumps(public_transcript, ensure_ascii=False),
            )
        except LLMContractError as exc:
            logger.warning(
                "summary_generation_failed session_id=%s error_type=%s",
                session_id,
                type(exc).__name__,
            )
            await self.sink(
                OrchestrationEvent(
                    event_type="stream.error",
                    session_id=session_id,
                    payload={
                        "code": "SUMMARY_FAILED",
                        "message": "讨论已完成，但总结生成失败，可以稍后重试。",
                        "retryable": True,
                    },
                )
            )
            return
        await self.sink(
            OrchestrationEvent(
                event_type="summary.ready",
                session_id=session_id,
                payload={
                    "naturalText": summary.naturalText,
                    "structured": summary.model_dump(),
                },
            )
        )


class DiscussionRunner:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        provider: LLMProvider,
        hub: EventHub,
        state_registry: dict[str, PanelRunState] | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.provider = provider
        self.hub = hub
        self.state_registry = state_registry if state_registry is not None else {}

    async def run(self, session_id: str) -> None:
        state = self._load_state(session_id)
        self.state_registry[session_id] = state
        sink = PersistentEventSink(session_factory=self.session_factory, hub=self.hub)
        pipeline = DiscussionEventPipeline(sink=sink, provider=self.provider)
        gateway = LLMAgentGateway(ValidatedLLMClient(self.provider))
        orchestrator = PanelOrchestrator(gateway=gateway, event_sink=pipeline)
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
        finally:
            self.state_registry.pop(session_id, None)

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
