from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "Trend Analysis System API"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_debug: bool = True

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/trends_db"
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    topic_count: int = 5
    top_words_per_topic: int = 7
    default_sentiment_lexicon_lang: str = "ru"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
