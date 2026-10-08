import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from sqlalchemy.orm import Session, sessionmaker

from .hub import EventHub
from .store import EventStore


def encode_sse(event: dict) -> str:
    return (
        f"id: {event['eventId']}\n"
        f"event: {event['eventType']}\n"
        f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )


async def stream_session_events(
    *,
    session_id: str,
    after: int,
    session_factory: sessionmaker[Session],
    hub: EventHub,
    heartbeat_seconds: float = 15.0,
) -> AsyncIterator[str]:
    last_seen = after
    async with hub.subscribe(session_id) as queue:
        with session_factory() as db:
            replay = EventStore(db).list_after(session_id, after)
        for event in replay:
            last_seen = max(last_seen, event["eventId"])
            yield encode_sse(event)

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
                if event["eventId"] <= last_seen:
                    continue
                last_seen = event["eventId"]
                yield encode_sse(event)
            except asyncio.TimeoutError:
                heartbeat = {
                    "eventId": last_seen,
                    "topicId": None,
                    "sessionId": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "eventType": "heartbeat",
                    "payload": {},
                }
                yield encode_sse(heartbeat)
