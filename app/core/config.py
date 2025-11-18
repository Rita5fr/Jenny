"""Application configuration management."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed configuration values."""

    app_name: str = Field(default="Jenny", description="Service name.")
    environment: Literal["dev", "prod", "test"] = Field(
        default="dev", description="Current deployment environment."
    )
    api_host: str = Field(default="0.0.0.0", description="Main API bind address.")
    api_port: int = Field(default=8000, description="Main API port.")
    mem0_host: str = Field(default="mem0", description="Mem0 service host.")
    mem0_port: int = Field(default=8081, description="Mem0 service port.")
    postgres_dsn: str = Field(
        default="postgresql+asyncpg://jenny:jenny@postgres:5432/jenny",
        description="Async connection string for Postgres.",
    )
    redis_url: str = Field(
        default="redis://redis:6379/0", description="Redis connection URL."
    )
    neo4j_url: str = Field(
        default="neo4j://neo4j:7687", description="Neo4j connection URI."
    )
    neo4j_user: str = Field(default="neo4j", description="Neo4j username.")
    neo4j_password: str = Field(default="neo4jpass", description="Neo4j password.")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def mem0_base_url(self) -> str:
        """Return the full URL for reaching the Mem0 microservice."""

        return f"http://{self.mem0_host}:{self.mem0_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()
