from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://tutorai:tutorai@localhost:5432/tutorai"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    cors_origins: str = "http://localhost:5173"
    llm_provider: str = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    youtube_api_key: str | None = None
    web_search_provider: str | None = None
    web_search_api_key: str | None = None
    api_rate_limit_per_minute: int = 60
    jwt_secret: str = "change-me-in-local-env"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    secure_cookies: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
