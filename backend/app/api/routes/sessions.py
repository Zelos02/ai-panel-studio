import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import get_db
from ...domain import SessionStatus
from ...errors import AppError
from ...events import stream_session_events
from ...models import Expert, PanelSession, TranscriptMessage
from ...schemas import (
    SessionRead,
    TranscriptList,
    TranscriptMessageRead,
    TranscriptSpeakerRead,
)
from ...services.discussions import DiscussionRunner

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_or_404(db: Session, session_id: str) -> PanelSession:
    panel_session = db.get(PanelSession, session_id)
    if panel_session is None:
        raise AppError("RESOURCE_NOT_FOUND", "没有找到这场讨论。", status_code=404)
    return panel_session


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: str, db: Annotated[Session, Depends(get_db)]) -> SessionRead:
    return SessionRead.model_validate(get_session_or_404(db, session_id))


@router.post("/{session_id}:start", response_model=SessionRead, status_code=status.HTTP_202_ACCEPTED)
async def start_session(
    session_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> SessionRead:
    panel_session = get_session_or_404(db, session_id)
    if panel_session.status not in {SessionStatus.ADMITTED.value, SessionStatus.PAUSED.value}:
        raise AppError("PANEL_INVALID_STATE", "当前讨论状态不能启动。", status_code=409)
    existing = request.app.state.discussion_tasks.get(session_id)
    if existing is not None and not existing.done():
        return SessionRead.model_validate(panel_session)

    runner = DiscussionRunner(
        session_factory=request.app.state.session_factory,
        provider=request.app.state.llm_provider,
        hub=request.app.state.event_hub,
    )
    task = asyncio.create_task(runner.run(session_id), name=f"discussion:{session_id}")
    request.app.state.discussion_tasks[session_id] = task

    def remove_finished(_: asyncio.Task) -> None:
        request.app.state.discussion_tasks.pop(session_id, None)

    task.add_done_callback(remove_finished)
    return SessionRead.model_validate(panel_session)


@router.get("/{session_id}/transcript", response_model=TranscriptList)
def get_transcript(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    after_sequence: Annotated[int, Query(alias="afterSequence", ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> TranscriptList:
    get_session_or_404(db, session_id)
    rows = list(
        db.scalars(
            select(TranscriptMessage)
            .where(
                TranscriptMessage.session_id == session_id,
                TranscriptMessage.sequence > after_sequence,
            )
            .order_by(TranscriptMessage.sequence)
            .limit(limit)
        )
    )
    items = []
    for row in rows:
        expert = db.get(Expert, row.speaker_expert_id) if row.speaker_expert_id else None
        items.append(
            TranscriptMessageRead(
                id=row.id,
                sequence=row.sequence,
                content=row.content,
                created_at=row.created_at,
                speaker=TranscriptSpeakerRead(
                    id=expert.id if expert else "system",
                    name=expert.name if expert else "系统",
                    title=expert.title if expert else "",
                    color=expert.color if expert else "#8093A8",
                    role=row.speaker_role,
                ),
            )
        )
    return TranscriptList(items=items)


@router.get("/{session_id}/events")
def session_events(
    session_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    after: Annotated[int, Query(ge=0)] = 0,
    last_event_id: Annotated[int | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    get_session_or_404(db, session_id)
    start_after = max(after, last_event_id or 0)
    generator = stream_session_events(
        session_id=session_id,
        after=start_after,
        session_factory=request.app.state.session_factory,
        hub=request.app.state.event_hub,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
