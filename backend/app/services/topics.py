from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain import SessionStatus
from ..errors import AppError
from ..models import PanelSession, Topic
from ..repositories import TopicRepository
from ..schemas import TopicCreate


class TopicService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = TopicRepository(session)

    def create(self, data: TopicCreate) -> Topic:
        topic = Topic(
            title=data.title.strip(),
            background=data.background,
            goal=data.goal,
            requested_expert_count=data.requested_expert_count,
        )
        if not topic.title:
            raise AppError("VALIDATION_ERROR", "讨论主题不能为空。", status_code=422)
        self.repository.add(topic)
        self.session.commit()
        return topic

    def get(self, topic_id: str) -> Topic:
        topic = self.repository.get(topic_id)
        if topic is None:
            raise AppError("RESOURCE_NOT_FOUND", "没有找到这个讨论话题。", status_code=404)
        return topic

    def list_recent(self, limit: int = 20) -> list[Topic]:
        return self.repository.list_recent(limit)

    def delete(self, topic_id: str) -> None:
        topic = self.get(topic_id)
        active_session = self.session.scalar(
            select(PanelSession.id)
            .where(
                PanelSession.topic_id == topic_id,
                PanelSession.status.in_(
                    [
                        SessionStatus.RUNNING.value,
                        SessionStatus.PAUSED.value,
                        SessionStatus.STOPPING.value,
                    ]
                ),
            )
            .limit(1)
        )
        if active_session is not None:
            raise AppError(
                "TOPIC_DELETE_LOCKED",
                "正在进行或暂停中的讨论不能删除，请先结束讨论。",
                status_code=409,
            )
        self.session.delete(topic)
        self.session.commit()
