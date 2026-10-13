from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HabitInput(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=300)

    @field_validator("name", "description", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class Habit(HabitInput):
    id: str
    created_at: str
    start_date: date
    completed: bool


class DailyActivity(StrictModel):
    day: date
    completed: int = Field(ge=0)


class Overview(StrictModel):
    today: date
    timezone: str
    habits: list[Habit]
    completed: int
    total: int
    remaining: int = Field(ge=0)
    completion_percentage: float | None = Field(ge=0, le=100)
    recent_days: list[DailyActivity]


class HistoryItem(StrictModel):
    habit_id: str
    habit_name: str
    day: date


class Progress(StrictModel):
    today: date
    recorded_completions: int
    history: list[HistoryItem]


class ChatInput(StrictModel):
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class Choice(StrictModel):
    id: str
    question: str


class ChatReply(StrictModel):
    message: str
    source: Literal["verified_local_data", "prepared_faq", "application_help", "clarification", "scope_limit"]
    choices: list[Choice] = Field(default_factory=list)
    question_id: str | None = None
    suggestions: list[Choice] = Field(default_factory=list, max_length=4)
