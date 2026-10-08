import json
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import InternalEvent, PanelSession


def utc_iso(value) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class EventStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def append(self, session_id: str, event_type: str, payload: dict) -> dict:
        panel_session = self.db.get(PanelSession, session_id)
        if panel_session is None:
            raise AppError("RESOURCE_NOT_FOUND", "没有找到这场讨论。", status_code=404)
        panel_session.last_event_sequence += 1
        event = InternalEvent(
            session_id=session_id,
            sequence=panel_session.last_event_sequence,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
        self.db.add(event)
        self.db.flush()
        return self.serialize(event, panel_session.topic_id)

    def list_after(self, session_id: str, after: int) -> list[dict]:
        panel_session = self.db.get(PanelSession, session_id)
        if panel_session is None:
            raise AppError("RESOURCE_NOT_FOUND", "没有找到这场讨论。", status_code=404)
        events = list(
            self.db.scalars(
                select(InternalEvent)
                .where(
                    InternalEvent.session_id == session_id,
                    InternalEvent.sequence > after,
                )
                .order_by(InternalEvent.sequence)
            )
        )
        return [self.serialize(event, panel_session.topic_id) for event in events]

    @staticmethod
    def serialize(event: InternalEvent, topic_id: str) -> dict:
        return {
            "eventId": event.sequence,
            "topicId": topic_id,
            "sessionId": event.session_id,
            "timestamp": utc_iso(event.created_at),
            "eventType": event.event_type,
            "payload": json.loads(event.payload_json),
        }
