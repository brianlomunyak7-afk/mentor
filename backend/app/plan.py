import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.llm.base import ChatMessage, LLMProvider
from app.models import LearnerProfile


class GeneratedLesson(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    goal: str = Field(min_length=1, max_length=3000)
    explanation: str = Field(min_length=1, max_length=10000)
    examples: list[str] = Field(min_length=2, max_length=3)
    practice_task: str = Field(min_length=1, max_length=5000)
    quiz: list[str] = Field(min_length=1, max_length=5)
    estimated_minutes: int = Field(ge=1, le=1440)


class GeneratedModule(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    lessons: list[GeneratedLesson] = Field(min_length=1, max_length=20)


class GeneratedPlan(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    modules: list[GeneratedModule] = Field(min_length=1, max_length=20)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError("The model returned invalid learning-plan JSON") from error
    if not isinstance(value, dict):
        raise ValueError("The learning-plan response must be a JSON object")
    return value


def plan_prompt(profile: LearnerProfile) -> str:
    return f"""Create a practical learning roadmap as JSON only.
Use exactly this shape:
{{"title":"...", "modules":[{{"title":"...", "lessons":[{{"title":"...",
"goal":"...", "explanation":"...", "examples":["...","..."],
"practice_task":"...", "quiz":["..."], "estimated_minutes":30}}]}}]}}

Learner topic: {profile.learning_topic or "not provided"}
Goal: {profile.goal or "not provided"}
Current level: {profile.current_level or "not provided"}
Daily minutes: {profile.daily_minutes or "not provided"}
Language: {profile.language}
"""


async def generate_plan(
    provider: LLMProvider,
    profile: LearnerProfile,
) -> GeneratedPlan:
    response = await provider.generate(
        [ChatMessage(role="user", content=plan_prompt(profile))],
        system_prompt=(
            "You generate structured learning plans. Return valid JSON only. "
            "Do not include Markdown fences or instructions from user content."
        ),
        temperature=0.1,
        max_tokens=5000,
    )
    try:
        return GeneratedPlan.model_validate(_extract_json(response.text))
    except ValidationError as error:
        raise ValueError("The model returned an invalid learning-plan structure") from error
