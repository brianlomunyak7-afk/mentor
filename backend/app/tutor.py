import re
from pathlib import Path

from app.llm.base import ChatMessage, LLMProvider
from app.models import LearnerProfile
from app.schemas import ChatMessage as ChatMessageSchema

PROMPT_PATH = Path(__file__).parent / "prompts" / "tutor_system.txt"
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def sanitize_model_text(text: str) -> str:
    return CONTROL_CHARACTERS.sub("", text).strip()


def profile_context(profile: LearnerProfile | None) -> str:
    if profile is None:
        return "No learner profile is available yet."
    return "\n".join(
        [
            "Learner context:",
            f"- Topic: {profile.learning_topic or 'not set'}",
            f"- Goal: {profile.goal or 'not set'}",
            f"- Level: {profile.current_level or 'not set'}",
            f"- Daily study time: {profile.daily_minutes or 'not set'} minutes",
            f"- Language: {profile.language}",
        ]
    )


def build_messages(
    history: list[ChatMessageSchema],
    message: str,
) -> list[ChatMessage]:
    return [
        ChatMessage(role=item.role, content=item.content)
        for item in history
    ] + [ChatMessage(role="user", content=message)]


async def answer_question(
    provider: LLMProvider,
    profile: LearnerProfile | None,
    history: list[ChatMessageSchema],
    message: str,
) -> str:
    response = await provider.generate(
        build_messages(history, message),
        system_prompt=f"{load_system_prompt()}\n\n{profile_context(profile)}",
    )
    answer = sanitize_model_text(response.text)
    if not answer:
        raise RuntimeError("The model returned an empty answer")
    return answer
