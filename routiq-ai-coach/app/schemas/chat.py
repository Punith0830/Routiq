"""Proposed canonical API contract, reconciling the two source examples."""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Screen(str, Enum):
    TODAY = "TODAY"
    PROGRESS = "PROGRESS"
    HABIT_DETAIL = "HABIT_DETAIL"


class ScreenContext(StrictModel):
    screen: Literal["TODAY", "PROGRESS", "HABIT_DETAIL"]
    habit_id: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def require_selected_habit(self):
        if self.screen == "HABIT_DETAIL" and not self.habit_id:
            raise ValueError("HABIT_DETAIL requires habit_id")
        if self.screen != "HABIT_DETAIL" and self.habit_id is not None:
            raise ValueError("habit_id is only supported for HABIT_DETAIL")
        return self


class ChatRequest(StrictModel):
    conversation_id: str | None = Field(default=None, min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    context: ScreenContext

    @model_validator(mode="after")
    def reject_blank_message(self):
        if not self.message.strip():
            raise ValueError("message must contain text")
        return self


class SuggestedQuestion(StrictModel):
    text: str = Field(min_length=1)
    intent_id: str = Field(min_length=1)


class Insight(StrictModel):
    type: str
    description: str
    evidence: dict


class Recommendation(StrictModel):
    title: str
    description: str
    type: Literal["OPTIONAL_EXPERIMENT"] = "OPTIONAL_EXPERIMENT"


class BehaviorContext(StrictModel):
    state: str
    evidence: list[str]
    confidence: Literal["UNDETERMINED"] = "UNDETERMINED"


class ChatResponse(StrictModel):
    conversation_id: str | None
    intents: list[str]
    message: str
    behavior_context: list[BehaviorContext] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    suggested_questions: list[SuggestedQuestion] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ErrorResponse(StrictModel):
    code: str
    message: str
