from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class TopicCreate(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    background: str | None = Field(default=None, max_length=4000)
    goal: str | None = Field(default=None, max_length=2000)
    requested_expert_count: int = Field(default=4, ge=2, le=8)


class TopicRead(ApiModel):
    id: str
    title: str
    background: str | None
    goal: str | None
    requested_expert_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class TopicList(ApiModel):
    items: list[TopicRead]
    next_cursor: str | None = None


class HealthRead(ApiModel):
    status: str
    environment: str
    llm_provider: str


class ErrorBody(ApiModel):
    code: str
    message: str
    request_id: str
    retryable: bool = False
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(ApiModel):
    error: ErrorBody
