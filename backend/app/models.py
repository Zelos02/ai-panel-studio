from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .domain.enums import SessionStatus, TopicStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"
    __table_args__ = (
        Index("ix_topics_status", "status"),
        Index("ix_topics_updated_at", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    background: Mapped[str | None] = mapped_column(Text)
    goal: Mapped[str | None] = mapped_column(Text)
    requested_expert_count: Mapped[int] = mapped_column(Integer, default=4)
    panel_generation: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default=TopicStatus.DRAFT.value)
    version: Mapped[int] = mapped_column(Integer, default=1)

    experts: Mapped[list[Expert]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    sessions: Mapped[list[PanelSession]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )


class Expert(TimestampMixin, Base):
    __tablename__ = "experts"
    __table_args__ = (
        UniqueConstraint("topic_id", "display_order", name="uq_expert_topic_order"),
        Index("ix_experts_topic_id", "topic_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    topic_id: Mapped[str] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    stance: Mapped[str] = mapped_column(Text, nullable=False)
    public_profile: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    admitted: Mapped[bool] = mapped_column(Boolean, default=False)

    topic: Mapped[Topic] = relationship(back_populates="experts")
    statuses: Mapped[list[ExpertStatus]] = relationship(
        back_populates="expert", cascade="all, delete-orphan"
    )
    messages: Mapped[list[TranscriptMessage]] = relationship(back_populates="speaker")


class PanelSession(TimestampMixin, Base):
    __tablename__ = "panel_sessions"
    __table_args__ = (
        Index("ix_sessions_topic_id", "topic_id"),
        Index("ix_sessions_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    topic_id: Mapped[str] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.CREATED.value)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    max_turns: Mapped[int] = mapped_column(Integer, default=18)
    context_summary: Mapped[str | None] = mapped_column(Text)
    last_event_sequence: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)

    topic: Mapped[Topic] = relationship(back_populates="sessions")
    messages: Mapped[list[TranscriptMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    statuses: Mapped[list[ExpertStatus]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    branches: Mapped[list[KnowledgeBranch]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    events: Mapped[list[InternalEvent]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    summary: Mapped[SessionSummary | None] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )


class TranscriptMessage(Base):
    __tablename__ = "transcript_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_message_session_sequence"),
        Index("ix_messages_session_id", "session_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("panel_sessions.id", ondelete="CASCADE"), nullable=False
    )
    speaker_expert_id: Mapped[str | None] = mapped_column(
        ForeignKey("experts.id", ondelete="SET NULL")
    )
    speaker_role: Mapped[str] = mapped_column(String(16), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sentence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped[PanelSession] = relationship(back_populates="messages")
    speaker: Mapped[Expert | None] = relationship(back_populates="messages")
    sourced_branches: Mapped[list[KnowledgeBranch]] = relationship(back_populates="source_message")


class ExpertStatus(Base):
    __tablename__ = "expert_statuses"
    __table_args__ = (
        UniqueConstraint("session_id", "expert_id", name="uq_status_session_expert"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("panel_sessions.id", ondelete="CASCADE"), nullable=False
    )
    expert_id: Mapped[str] = mapped_column(
        ForeignKey("experts.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(20), default="waiting")
    public_focus: Mapped[str | None] = mapped_column(String(300))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    session: Mapped[PanelSession] = relationship(back_populates="statuses")
    expert: Mapped[Expert] = relationship(back_populates="statuses")


class KnowledgeBranch(TimestampMixin, Base):
    __tablename__ = "knowledge_branches"
    __table_args__ = (
        UniqueConstraint("session_id", "fingerprint", name="uq_branch_session_fingerprint"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("panel_sessions.id", ondelete="CASCADE"), nullable=False
    )
    source_message_id: Mapped[str] = mapped_column(
        ForeignKey("transcript_messages.id", ondelete="CASCADE"), nullable=False
    )
    branch_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    session: Mapped[PanelSession] = relationship(back_populates="branches")
    source_message: Mapped[TranscriptMessage] = relationship(back_populates="sourced_branches")


class InternalEvent(Base):
    __tablename__ = "internal_events"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_event_session_sequence"),
        Index("ix_events_session_sequence", "session_id", "sequence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("panel_sessions.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped[PanelSession] = relationship(back_populates="events")


class SessionSummary(TimestampMixin, Base):
    __tablename__ = "session_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("panel_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    natural_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_json: Mapped[str | None] = mapped_column(Text)

    session: Mapped[PanelSession] = relationship(back_populates="summary")
