"""Configuration settings for the Admin Portal service."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_env_file() -> Path:
    """Find .env file by searching up directory tree."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        env_path = current / ".env"
        if env_path.exists():
            return env_path
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path(".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service Configuration
    SERVICE_NAME: str = "ws8_admin_portal"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DEV_MODE: bool = True  # Disables authentication for development

    # ===========================================
    # PORT CONFIGURATION - Single source of truth
    # ===========================================
    BACKEND_PORT: int = Field(default=8008, description="Backend API port")
    FRONTEND_PORT: int = Field(default=8081, description="Frontend UI port")

    # Legacy alias for backward compatibility
    @computed_field
    @property
    def PORT(self) -> int:
        """Alias for BACKEND_PORT."""
        return self.BACKEND_PORT

    # Server Configuration
    HOST: str = "0.0.0.0"

    # Authentication
    JWT_SECRET_KEY: str = Field(
        default="admin-portal-secret-key-change-in-production",
        description="JWT signing key"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Azure AD Configuration (for SSO)
    AZURE_AD_TENANT_ID: str = Field(default="", description="Azure AD tenant ID")
    AZURE_AD_CLIENT_ID: str = Field(default="", description="Azure AD client ID")
    AZURE_AD_CLIENT_SECRET: str = Field(default="", description="Azure AD client secret")

    # Cosmos DB Configuration
    COSMOS_DB_ENDPOINT: str = Field(default="", description="Cosmos DB endpoint")
    COSMOS_DB_KEY: str = Field(default="", description="Cosmos DB key")
    COSMOS_DB_DATABASE: str = Field(default="admin-portal", description="Database name")

    # Azure Cost Management
    AZURE_SUBSCRIPTION_ID: str = Field(default="", description="Azure subscription ID")
    AZURE_COST_MANAGEMENT_SCOPE: str = Field(
        default="",
        description="Cost management scope (subscription or resource group)"
    )
    AZURE_RESOURCE_GROUP_FILTER: str = Field(
        default="",
        description="Comma-separated resource group name patterns to filter (e.g., 'eis,dynamics')"
    )

    # AWS Cost Explorer
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS secret key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_SERVICE_FILTER: str = Field(
        default="",
        description="Comma-separated AWS service names to filter (e.g., 'Bedrock,Lambda,S3')"
    )

    @computed_field
    @property
    def azure_resource_groups(self) -> List[str]:
        """Parse Azure resource group filter patterns."""
        if not self.AZURE_RESOURCE_GROUP_FILTER:
            return []
        return [rg.strip() for rg in self.AZURE_RESOURCE_GROUP_FILTER.split(",") if rg.strip()]

    @computed_field
    @property
    def aws_services(self) -> List[str]:
        """Parse AWS service filter."""
        if not self.AWS_SERVICE_FILTER:
            return []
        return [svc.strip() for svc in self.AWS_SERVICE_FILTER.split(",") if svc.strip()]

    # Service Bus (for notifications)
    SERVICE_BUS_CONNECTION_STRING: str = Field(
        default="",
        description="Service Bus connection string"
    )
    APPROVAL_NOTIFICATION_QUEUE: str = Field(
        default="approval-notifications",
        description="Queue name for approval notifications"
    )

    # ===========================================
    # CORS CONFIGURATION - Config driven
    # ===========================================
    # For production, set this via environment variable as comma-separated list
    # e.g., CORS_ORIGINS=https://admin.example.com,https://app.example.com
    CORS_ORIGINS: List[str] = Field(
        default=[],
        description="Allowed CORS origins (comma-separated in env)"
    )

    @computed_field
    @property
    def cors_origins_resolved(self) -> List[str]:
        """
        Returns CORS origins based on environment:
        - If CORS_ORIGINS is set, use those (production)
        - If DEBUG mode, auto-generate localhost origins from ports
        """
        if self.CORS_ORIGINS:
            return self.CORS_ORIGINS

        # In debug mode, auto-generate from configured ports
        if self.DEBUG:
            return [
                f"http://localhost:{self.FRONTEND_PORT}",
                f"http://127.0.0.1:{self.FRONTEND_PORT}",
            ]

        # Production without explicit CORS - empty (will fail CORS)
        return []

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Maker-Checker Configuration
    REQUIRE_APPROVAL_FOR: List[str] = Field(
        default=["ai_config", "claims_rules", "rating_config", "policy_config"],
        description="Config types that require approval"
    )
    APPROVAL_EXPIRY_HOURS: int = Field(
        default=72,
        description="Hours until pending approval expires"
    )

    # Default Admin User (for initial setup)
    DEFAULT_ADMIN_EMAIL: str = Field(
        default="admin@eis-dynamics.com",
        description="Default admin email"
    )
    DEFAULT_ADMIN_NAME: str = Field(
        default="System Administrator",
        description="Default admin name"
    )

    @property
    def cosmos_db_configured(self) -> bool:
        """Check if Cosmos DB is configured."""
        return bool(self.COSMOS_DB_ENDPOINT and self.COSMOS_DB_KEY)

    @property
    def azure_cost_configured(self) -> bool:
        """Check if Azure Cost Management is configured."""
        return bool(self.AZURE_SUBSCRIPTION_ID)

    @property
    def aws_cost_configured(self) -> bool:
        """Check if AWS Cost Explorer is configured."""
        return bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
