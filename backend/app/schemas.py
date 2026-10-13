from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["beginner", "intermediate", "advanced"]


class LearnerProfileUpdate(BaseModel):
    learning_topic: str | None = Field(default=None, max_length=200)
    motivation: str | None = Field(default=None, max_length=5000)
    goal: str | None = Field(default=None, max_length=5000)
    deadline: str | None = Field(default=None, max_length=100)
    current_level: Level | None = None
    daily_minutes: int | None = Field(default=None, ge=1, le=1440)
    language: str | None = Field(default=None, min_length=1, max_length=50)
    device_limits: str | None = Field(default=None, max_length=2000)
    internet_limits: str | None = Field(default=None, max_length=2000)
    preferences: dict[str, Any] | None = None


class LearnerProfileResponse(LearnerProfileUpdate):
    model_config = ConfigDict(from_attributes=True)

    onboarding_step: int
    created_at: datetime
    updated_at: datetime


class OnboardingAnswer(BaseModel):
    step: int = Field(ge=0, le=20)
    answer: str | list[str] = Field(min_length=1)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=30)


class SourceCitation(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer_id: int
    message: str
    provider: str
    model: str
    sources: list[SourceCitation]


class WrongAnswerReport(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)
