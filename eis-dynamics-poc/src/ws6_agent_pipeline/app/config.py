"""
Configuration settings for the Agent Pipeline service.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> Path:
    """Find .env file by searching up directory tree."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Max 10 levels up
        env_path = current / ".env"
        if env_path.exists():
            return env_path
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path(".env")  # Fallback


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service Configuration
    SERVICE_NAME: str = "ws6_agent_pipeline"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8006

    # CORS (configure via env var CORS_ORIGINS as comma-separated list)
    CORS_ORIGINS: list[str] = []

    # AI Provider Configuration
    AI_PROVIDER: Literal["claude", "openai"] = "claude"
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key for Claude")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")

    # Model Configuration
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_MODEL: str = "gpt-4o"

    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TEMPERATURE: float = 0.1
    AGENT_TIMEOUT_SECONDS: int = 120
    
    # LangGraph Recursion Limits (configurable via env vars)
    AGENT_RECURSION_LIMIT: int = 11  # Max iterations for LangGraph agents
    AGENT_FORCE_FINISH_AT: int = 9   # Force agent to finish at this iteration

    # Redis Configuration (for event streaming)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Storage Configuration (Agent-specific storage for comparison)
    AGENT_STORAGE_TYPE: Literal["local", "azure"] = "local"
    AGENT_STORAGE_PATH: str = "./data/agent_pipeline"

    # Azure Storage (when AGENT_STORAGE_TYPE=azure)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "agent-medallion"

    # Delta Lake Configuration
    DELTA_BRONZE_PATH: str = "./data/agent_pipeline/bronze"
    DELTA_SILVER_PATH: str = "./data/agent_pipeline/silver"
    DELTA_GOLD_PATH: str = "./data/agent_pipeline/gold"

    # Integration URLs (configure via env vars)
    PETINSURE360_URL: str = ""
    EIS_AI_CLAIMS_URL: str = ""
    EIS_INTEGRATION_URL: str = ""

    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def ai_api_key(self) -> str:
        """Get the appropriate API key based on provider."""
        if self.AI_PROVIDER == "claude":
            return self.ANTHROPIC_API_KEY
        return self.OPENAI_API_KEY

    @property
    def ai_model(self) -> str:
        """Get the appropriate model based on provider."""
        if self.AI_PROVIDER == "claude":
            return self.CLAUDE_MODEL
        return self.OPENAI_MODEL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience instance
settings = get_settings()
