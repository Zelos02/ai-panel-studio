from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..domain import ExpertKind, SessionStatus, TopicStatus
from ..errors import AppError
from ..llm import LLMCallTimeout, LLMInvalidOutput, LLMProvider, ValidatedLLMClient
from ..llm.prompts import PANEL_SYSTEM
from ..models import Expert, ExpertStatus, PanelSession, Topic
from ..schemas import PanelGenerationResult, PanelRead, ExpertRead, SessionCreate


class PanelService:
    def __init__(self, session: Session, provider: LLMProvider) -> None:
        self.session = session
        self.provider = provider

    def _get_topic(self, topic_id: str) -> Topic:
        topic = self.session.get(Topic, topic_id)
        if topic is None:
            raise AppError("RESOURCE_NOT_FOUND", "没有找到这个讨论话题。", status_code=404)
        return topic

    async def generate(self, topic_id: str) -> PanelRead:
        topic = self._get_topic(topic_id)
        admitted = self.session.scalar(
            select(Expert.id).where(Expert.topic_id == topic_id, Expert.admitted.is_(True)).limit(1)
        )
        if admitted is not None:
            raise AppError(
                "PANEL_ALREADY_ADMITTED", "阵容已经确认，不能直接重新生成。", status_code=409
            )

        user_prompt = (
            f"讨论主题：{topic.title}\n"
            f"背景：{topic.background or '未提供'}\n"
            f"目标：{topic.goal or '未提供'}\n"
            f"专家人数：{topic.requested_expert_count}\n"
        )
        try:
            generated = await ValidatedLLMClient(self.provider).call(
                PanelGenerationResult,
                system_prompt=PANEL_SYSTEM,
                user_prompt=user_prompt,
            )
        except LLMInvalidOutput as exc:
            raise AppError(
                "LLM_INVALID_OUTPUT",
                "模型返回的专家阵容不完整，请重试。",
                status_code=502,
                retryable=True,
            ) from exc
        except LLMCallTimeout as exc:
            raise AppError(
                "LLM_TIMEOUT", "生成专家阵容超时，请重试。", status_code=504, retryable=True
            ) from exc
        except Exception as exc:
            raise AppError(
                "LLM_UNAVAILABLE", "暂时无法生成专家阵容，请稍后重试。", status_code=503, retryable=True
            ) from exc

        if len(generated.experts) != topic.requested_expert_count:
            raise AppError(
                "LLM_INVALID_OUTPUT",
                "模型返回的专家人数与请求不一致，请重试。",
                status_code=502,
                retryable=True,
            )

        self.session.execute(delete(Expert).where(Expert.topic_id == topic_id))
        topic.panel_generation += 1
        host = self._member_to_model(topic_id, generated.host, ExpertKind.HOST, 0)
        experts = [
            self._member_to_model(topic_id, member, ExpertKind.EXPERT, index + 1)
            for index, member in enumerate(generated.experts)
        ]
        self.session.add_all([host, *experts])
        self.session.commit()
        return self._panel_read(topic, [host, *experts])

    def get_panel(self, topic_id: str) -> PanelRead:
        topic = self._get_topic(topic_id)
        members = list(
            self.session.scalars(
                select(Expert).where(Expert.topic_id == topic_id).order_by(Expert.display_order)
            )
        )
        if not members:
            raise AppError("RESOURCE_NOT_FOUND", "这个话题还没有专家阵容。", status_code=404)
        return self._panel_read(topic, members)

    def admit(self, topic_id: str, generation: int) -> PanelRead:
        topic = self._get_topic(topic_id)
        if generation != topic.panel_generation:
            raise AppError(
                "PANEL_GENERATION_STALE",
                "专家阵容已经更新，请确认最新阵容。",
                status_code=409,
            )
        members = list(
            self.session.scalars(
                select(Expert).where(Expert.topic_id == topic_id).order_by(Expert.display_order)
            )
        )
        hosts = [member for member in members if member.kind == ExpertKind.HOST.value]
        experts = [member for member in members if member.kind == ExpertKind.EXPERT.value]
        if len(hosts) != 1 or len(experts) != topic.requested_expert_count:
            raise AppError(
                "PANEL_INVALID_STATE", "当前专家阵容不完整，请重新生成。", status_code=409
            )
        for member in members:
            member.admitted = True
        topic.status = TopicStatus.READY.value
        topic.version += 1
        self.session.commit()
        return self._panel_read(topic, members)

    def create_session(self, topic_id: str, data: SessionCreate) -> PanelSession:
        topic = self._get_topic(topic_id)
        admitted_members = list(
            self.session.scalars(
                select(Expert).where(Expert.topic_id == topic_id, Expert.admitted.is_(True))
            )
        )
        if topic.status != TopicStatus.READY.value or len(admitted_members) < 3:
            raise AppError(
                "PANEL_INVALID_STATE", "当前阵容尚未确认，无法创建讨论。", status_code=409
            )
        active = self.session.scalar(
            select(PanelSession.id)
            .where(
                PanelSession.topic_id == topic_id,
                PanelSession.status.in_(
                    [SessionStatus.ADMITTED.value, SessionStatus.RUNNING.value, SessionStatus.PAUSED.value]
                ),
            )
            .limit(1)
        )
        if active is not None:
            raise AppError(
                "SESSION_ALREADY_ACTIVE", "这个话题已经有一场待开始或进行中的讨论。", status_code=409
            )
        panel_session = PanelSession(
            topic_id=topic_id,
            status=SessionStatus.ADMITTED.value,
            max_turns=data.max_turns,
        )
        self.session.add(panel_session)
        self.session.flush()
        self.session.add_all(
            [
                ExpertStatus(session_id=panel_session.id, expert_id=member.id)
                for member in admitted_members
            ]
        )
        self.session.commit()
        return panel_session

    @staticmethod
    def _member_to_model(topic_id, member, kind: ExpertKind, display_order: int) -> Expert:
        return Expert(
            topic_id=topic_id,
            kind=kind.value,
            name=member.name,
            title=member.title,
            stance=member.stance,
            public_profile=member.public_profile,
            color=member.color.upper(),
            display_order=display_order,
            admitted=False,
        )

    @staticmethod
    def _panel_read(topic: Topic, members: list[Expert]) -> PanelRead:
        host = next(member for member in members if member.kind == ExpertKind.HOST.value)
        experts = [member for member in members if member.kind == ExpertKind.EXPERT.value]
        return PanelRead(
            topic_id=topic.id,
            generation=topic.panel_generation,
            host=ExpertRead.model_validate(host),
            experts=[ExpertRead.model_validate(expert) for expert in experts],
        )
