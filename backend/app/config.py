from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./data/panel_studio.db"
    llm_provider: Literal["fake", "openai_compatible"] = "fake"
    llm_api_key: str | None = Field(default=None, repr=False)
    llm_base_url: str = "https://api.example.com/v1"
    llm_model: str = "replace-with-your-model"
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
