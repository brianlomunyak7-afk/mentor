import pytest

from app.config import Settings
from app.llm.anthropic import AnthropicProvider
from app.llm.factory import create_llm_provider
from app.llm.gemini import GeminiProvider


def test_factory_selects_anthropic() -> None:
    provider = create_llm_provider(
        Settings(llm_provider="anthropic", anthropic_api_key="test-key")
    )
    assert isinstance(provider, AnthropicProvider)
    assert provider.model_name == "claude-3-5-sonnet-latest"


def test_factory_selects_gemini() -> None:
    provider = create_llm_provider(
        Settings(llm_provider="gemini", gemini_api_key="test-key")
    )
    assert isinstance(provider, GeminiProvider)
    assert provider.model_name == "gemini-2.0-flash"


@pytest.mark.parametrize(
    ("provider", "settings"),
    [
        ("anthropic", Settings(llm_provider="anthropic")),
        ("gemini", Settings(llm_provider="gemini")),
        ("unknown", Settings(llm_provider="unknown")),
    ],
)
def test_factory_rejects_invalid_configuration(
    provider: str, settings: Settings
) -> None:
    with pytest.raises(ValueError, match=provider):
        create_llm_provider(settings)
