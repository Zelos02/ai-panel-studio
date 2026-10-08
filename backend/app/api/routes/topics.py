from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas import TopicCreate, TopicList, TopicRead
from ...services import TopicService

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
