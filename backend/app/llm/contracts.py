from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class TurnDecisionContract(Contract):
    action: Literal["wait", "raise_hand", "supplement", "rebut", "speak"]
    urgency: int = Field(ge=0, le=100)
    publicFocus: str = Field(min_length=1, max_length=300)
    targetMessageId: str | None = None


class UtteranceResult(Contract):
    content: str = Field(min_length=1, max_length=1200)


class BranchSuggestion(Contract):
    shouldCreate: bool
    branchType: Literal["concept", "assumption", "conflict", "question", "direction"] | None = None
    title: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=600)
    sourceMessageId: str | None = None

    @model_validator(mode="after")
    def require_branch_fields(self):
        if self.shouldCreate and not all(
            [self.branchType, self.title, self.summary, self.sourceMessageId]
        ):
            raise ValueError("branch fields are required when shouldCreate is true")
        return self


class SessionSummaryResult(Contract):
    focus: str = Field(min_length=1, max_length=600)
    viewpoints: list[str] = Field(min_length=1, max_length=12)
    disagreements: list[str] = Field(max_length=12)
    consensus: list[str] = Field(max_length=12)
    openQuestions: list[str] = Field(max_length=12)
    nextSteps: list[str] = Field(max_length=12)
    naturalText: str = Field(min_length=1, max_length=6000)
