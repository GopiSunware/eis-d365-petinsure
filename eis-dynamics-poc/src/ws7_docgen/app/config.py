"""Configuration for DocGen Service."""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """DocGen service configuration."""

    # Service
    SERVICE_NAME: str = "docgen"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8007
    DEBUG: bool = False

    # CORS (configure via env var CORS_ORIGINS as comma-separated list)
    CORS_ORIGINS: List[str] = []

    # AI Provider
    AI_PROVIDER: str = "claude"  # claude or openai
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_MODEL: str = "gpt-4o"

    # Azure Document Intelligence (OCR)
    AZURE_FORM_RECOGNIZER_ENDPOINT: Optional[str] = None
    AZURE_FORM_RECOGNIZER_KEY: Optional[str] = None

    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    DOCGEN_STORAGE_CONTAINER: str = "docgen-uploads"
    DOCGEN_EXPORT_CONTAINER: str = "docgen-exports"

    # Local Storage (fallback)
    LOCAL_STORAGE_PATH: str = "/tmp/docgen/storage"
    USE_LOCAL_STORAGE: bool = True  # Set to False in production

    # ZIP Processing
    MAX_ZIP_SIZE_MB: int = 50
    MAX_FILES_PER_ZIP: int = 20
    TEMP_DIR: str = "/tmp/docgen/temp"

    # Export
    EXPORT_URL_EXPIRY_HOURS: int = 24

    # Internal Service URLs (configure via env vars)
    CLAIMS_DATA_API_URL: str = ""
    WS6_PIPELINE_URL: str = ""

    # File Upload Limits
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".jpg", ".jpeg", ".png", ".heic",
        ".doc", ".docx", ".zip", ".txt"
    ]
    ALLOWED_CONTENT_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/heic",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/x-zip-compressed",
        "text/plain",
    ]

    class Config:
        # Look for .env in multiple locations (ws7_docgen dir, src dir, and root)
        env_file = ("../../.env", "../../../.env", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env not in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
