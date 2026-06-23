from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = 8000
    database_url: str
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    history_limit: int = 5
    low_confidence_threshold: float = 0.7
    disruptive_actions: set[str] = {"rollback", "scale_up"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
