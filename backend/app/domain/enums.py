from enum import StrEnum


class TopicStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(StrEnum):
    CREATED = "created"
    ADMITTED = "admitted"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"


class ExpertKind(StrEnum):
    HOST = "host"
    EXPERT = "expert"


class ExpertState(StrEnum):
    WAITING = "waiting"
    PREPARING = "preparing"
    SPEAKING = "speaking"


class SpeakerRole(StrEnum):
    HOST = "host"
    EXPERT = "expert"
    SYSTEM = "system"


class BranchType(StrEnum):
    CONCEPT = "concept"
    ASSUMPTION = "assumption"
    CONFLICT = "conflict"
    QUESTION = "question"
    DIRECTION = "direction"
