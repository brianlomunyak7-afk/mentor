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


class LessonResponse(BaseModel):
    id: int
    module_number: int
    lesson_number: int
    title: str
    goal: str
    explanation: str
    examples: list[str]
    practice_task: str
    quiz: list[str]
    estimated_minutes: int
    status: str


class LearningPlanResponse(BaseModel):
    id: int
    title: str
    goal: str
    status: str
    lessons: list[LessonResponse]


class LessonProgressUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]


class ResourceResponse(BaseModel):
    title: str
    url: str
    source: str
    duration_seconds: int | None
    reason: str


class NoteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=20000)
    lesson_id: int | None = Field(default=None, ge=1)


class NoteResponse(NoteRequest):
    id: int
    created_at: datetime
    updated_at: datetime


class BookmarkRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2000)
    source: str = Field(min_length=1, max_length=50)


class BookmarkResponse(BookmarkRequest):
    id: int
    created_at: datetime


class QuizSubmission(BaseModel):
    answers: list[str] = Field(min_length=1, max_length=20)


class QuizResult(BaseModel):
    attempt_id: int
    score: int
    total: int
    feedback: str


class ProgressSummary(BaseModel):
    lessons_completed: int
    lessons_total: int
    completion_percent: int
    streak_days: int
    weak_area: str | None
