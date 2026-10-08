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
    panel_generation: int
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


class GeneratedParticipant(ApiModel):
    name: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=160)
    stance: str = Field(min_length=1, max_length=1000)
    public_profile: str = Field(min_length=1, max_length=1000)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class PanelGenerationResult(ApiModel):
    host: GeneratedParticipant
    experts: list[GeneratedParticipant] = Field(min_length=2, max_length=8)


class PanelMemberUpdate(ApiModel):
    id: str
    name: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=160)
    stance: str = Field(min_length=1, max_length=1000)
    public_profile: str = Field(min_length=1, max_length=1000)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class PanelUpdateRequest(ApiModel):
    generation: int = Field(ge=1)
    host: PanelMemberUpdate
    experts: list[PanelMemberUpdate] = Field(min_length=2, max_length=8)


class ExpertRead(ApiModel):
    id: str
    topic_id: str
    kind: str
    name: str
    title: str
    stance: str
    public_profile: str
    color: str
    display_order: int
    admitted: bool


class PanelRead(ApiModel):
    topic_id: str
    generation: int
    host: ExpertRead
    experts: list[ExpertRead]


class PanelAdmitRequest(ApiModel):
    generation: int = Field(ge=1)


class SessionCreate(ApiModel):
    max_turns: int = Field(default=18, ge=4, le=60)


class SessionRead(ApiModel):
    id: str
    topic_id: str
    status: str
    turn_count: int
    max_turns: int
    last_event_sequence: int
    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None

    @field_validator("created_at", "started_at", "ended_at", mode="before")
    @classmethod
    def ensure_session_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class TranscriptSpeakerRead(ApiModel):
    id: str
    name: str
    title: str
    color: str
    role: str


class TranscriptMessageRead(ApiModel):
    id: str
    sequence: int
    content: str
    created_at: datetime
    speaker: TranscriptSpeakerRead

    @field_validator("created_at", mode="before")
    @classmethod
    def ensure_message_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class TranscriptList(ApiModel):
    items: list[TranscriptMessageRead]


class SessionList(ApiModel):
    items: list[SessionRead]


class BranchRead(ApiModel):
    id: str
    branch_type: str
    title: str
    summary: str
    source_message_id: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def ensure_branch_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class BranchList(ApiModel):
    items: list[BranchRead]


class SummaryRead(ApiModel):
    natural_text: str
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_summary_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ErrorBody(ApiModel):
    code: str
    message: str
    request_id: str
    retryable: bool = False
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(ApiModel):
    error: ErrorBody
