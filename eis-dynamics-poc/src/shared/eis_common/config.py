"""Configuration management for EIS-D365 POC."""
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


def find_env_file() -> str:
    """Find .env file by searching up from current directory."""
    current = Path.cwd()

    # Search up to 5 levels up for .env
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fallback: look relative to this file's location (project root)
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        return str(env_path)

    return ".env"  # Default fallback


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Azure Key Vault
    key_vault_uri: str = Field(default="", alias="KEY_VAULT_URI")

    # Dataverse / D365
    dataverse_url: str = Field(default="", alias="DATAVERSE_URL")
    dataverse_client_id: str = Field(default="", alias="DATAVERSE_CLIENT_ID")
    dataverse_client_secret: str = Field(default="", alias="DATAVERSE_CLIENT_SECRET")
    dataverse_tenant_id: str = Field(default="", alias="DATAVERSE_TENANT_ID")

    # Azure Service Bus
    service_bus_namespace: str = Field(default="", alias="SERVICE_BUS_NAMESPACE")
    service_bus_connection_string: str = Field(default="", alias="SERVICE_BUS_CONNECTION_STRING")

    # Azure Cosmos DB
    cosmos_db_endpoint: str = Field(default="", alias="COSMOS_DB_ENDPOINT")
    cosmos_db_key: str = Field(default="", alias="COSMOS_DB_KEY")
    cosmos_db_database: str = Field(default="insurance-data", alias="COSMOS_DB_DATABASE")

    # Azure Storage
    storage_account_name: str = Field(default="", alias="STORAGE_ACCOUNT_NAME")
    storage_connection_string: str = Field(default="", alias="STORAGE_CONNECTION_STRING")

    # Azure OpenAI (for Azure-hosted models)
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_deployment_name: str = Field(
        default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT_NAME"
    )

    # OpenAI API (regular ChatGPT API - api.openai.com)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # Anthropic Claude
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Application
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: List[str] = Field(
        default=[], alias="CORS_ORIGINS"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Internal Service URLs (all configurable via env vars)
    eis_mock_url: str = Field(default="", alias="EIS_MOCK_URL")
    ws2_ai_claims_url: str = Field(default="", alias="WS2_AI_CLAIMS_URL")
    ws3_integration_url: str = Field(default="", alias="WS3_INTEGRATION_URL")
    ws5_rating_url: str = Field(default="", alias="WS5_RATING_URL")
    ws6_pipeline_url: str = Field(default="", alias="WS6_PIPELINE_URL")
    ws7_docgen_url: str = Field(default="", alias="WS7_DOCGEN_URL")
    ws8_admin_url: str = Field(default="", alias="WS8_ADMIN_URL")

    model_config = {
        "env_file": find_env_file(),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


async def get_secret_from_keyvault(secret_name: str) -> Optional[str]:
    """Retrieve secret from Azure Key Vault."""
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    settings = get_settings()
    if not settings.key_vault_uri:
        return None

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=settings.key_vault_uri, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception:
        return None
