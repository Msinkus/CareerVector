from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://careervector:careervector@localhost:5433/careervector"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_vacancies: str = "vacancies"
    qdrant_collection_candidates: str = "candidates"

    redis_url: str = "redis://localhost:6379/0"

    llm_provider: Literal["deepseek", "anthropic"] = "deepseek"

    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-sonnet-5"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_default_model: str = "deepseek-chat"

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    rate_limit_default: str = "100/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
