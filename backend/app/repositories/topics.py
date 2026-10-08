from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from ..models import Topic


class TopicRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, topic: Topic) -> Topic:
        self.session.add(topic)
        self.session.flush()
        return topic

    def get(self, topic_id: str) -> Topic | None:
        return self.session.get(Topic, topic_id)

    def list_recent(self, limit: int = 20) -> list[Topic]:
        statement: Select[tuple[Topic]] = select(Topic).order_by(desc(Topic.updated_at)).limit(limit)
        return list(self.session.scalars(statement))
