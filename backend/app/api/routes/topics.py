from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas import (
    PanelAdmitRequest,
    PanelRead,
    SessionCreate,
    SessionRead,
    TopicCreate,
    TopicList,
    TopicRead,
)
from ...services import PanelService, TopicService

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=TopicList)
def list_topics(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TopicList:
    topics = TopicService(db).list_recent(limit)
    return TopicList(items=[TopicRead.model_validate(topic) for topic in topics])


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(data: TopicCreate, db: Annotated[Session, Depends(get_db)]) -> TopicRead:
    topic = TopicService(db).create(data)
    return TopicRead.model_validate(topic)


@router.get("/{topic_id}", response_model=TopicRead)
def get_topic(topic_id: str, db: Annotated[Session, Depends(get_db)]) -> TopicRead:
    topic = TopicService(db).get(topic_id)
    return TopicRead.model_validate(topic)


@router.post("/{topic_id}/panel:generate", response_model=PanelRead)
async def generate_panel(
    topic_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PanelRead:
    return await PanelService(db, request.app.state.llm_provider).generate(topic_id)


@router.get("/{topic_id}/experts", response_model=PanelRead)
def get_panel(
    topic_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PanelRead:
    return PanelService(db, request.app.state.llm_provider).get_panel(topic_id)


@router.put("/{topic_id}/panel:admit", response_model=PanelRead)
def admit_panel(
    topic_id: str,
    data: PanelAdmitRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PanelRead:
    return PanelService(db, request.app.state.llm_provider).admit(topic_id, data.generation)


@router.post(
    "/{topic_id}/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED
)
def create_session(
    topic_id: str,
    data: SessionCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> SessionRead:
    panel_session = PanelService(db, request.app.state.llm_provider).create_session(topic_id, data)
    return SessionRead.model_validate(panel_session)
