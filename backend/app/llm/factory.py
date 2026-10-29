from app.config import Settings, get_settings
from app.llm.anthropic import AnthropicProvider
from app.llm.base import LLMProvider
from app.llm.gemini import GeminiProvider


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    config = settings or get_settings()
    provider = config.llm_provider.strip().lower()

    if provider == "anthropic":
        if config.anthropic_api_key is None:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicProvider(config.anthropic_api_key, config.anthropic_model)
    if provider == "gemini":
        if config.gemini_api_key is None:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return GeminiProvider(config.gemini_api_key, config.gemini_model)
    raise ValueError(
        f"Unsupported LLM_PROVIDER={config.llm_provider!r}; use anthropic or gemini"
    )
