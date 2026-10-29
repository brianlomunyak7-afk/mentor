from dataclasses import dataclass
from typing import Protocol


class LLMProviderError(RuntimeError):
    """Raised when a configured model provider cannot complete a request."""


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> LLMResponse:
        """Generate one response from an ordered conversation."""
