from types import SimpleNamespace

from app.llm.anthropic import AnthropicProvider
from app.llm.base import ChatMessage
from app.llm.gemini import GeminiProvider


async def test_anthropic_adapter_maps_text_response(monkeypatch) -> None:
    provider = AnthropicProvider("test-key", "test-model")

    async def create(**kwargs):
        assert kwargs["system"] == "Teach safely."
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Hi from Claude")]
        )

    monkeypatch.setattr(provider.client.messages, "create", create)
    response = await provider.generate(
        [ChatMessage(role="user", content="Hello")],
        system_prompt="Teach safely.",
    )

    assert response.text == "Hi from Claude"
    assert response.provider == "anthropic"


async def test_gemini_adapter_maps_text_response(monkeypatch) -> None:
    provider = GeminiProvider("test-key", "test-model")

    async def generate_content(**kwargs):
        assert kwargs["model"] == "test-model"
        return SimpleNamespace(text="Hi from Gemini")

    monkeypatch.setattr(
        provider.client.aio.models,
        "generate_content",
        generate_content,
    )
    response = await provider.generate(
        [ChatMessage(role="user", content="Hello")],
        system_prompt="Teach safely.",
    )

    assert response.text == "Hi from Gemini"
    assert response.provider == "gemini"
