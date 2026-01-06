"""AI Configuration models."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class AIProvider(BaseModel):
    """AI provider configuration."""
    provider_id: str
    name: str
    enabled: bool = True
    api_key_set: bool = False  # Indicates if API key is configured
    endpoint: Optional[str] = None
    description: Optional[str] = None


class AIModel(BaseModel):
    """AI model configuration."""
    model_id: str
    provider: str
    display_name: str
    description: str
    max_tokens: int
    supports_streaming: bool = True
    supports_function_calling: bool = True
    supports_vision: bool = False
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None


class AIConfiguration(BaseModel):
    """Complete AI configuration."""
    id: str = "ai_config"
    config_type: str = "ai_config"  # Partition key
    version: int = 1

    # Active configuration
    active_provider: str = "claude"
    active_model: str = "claude-sonnet-4-20250514"

    # Fallback configuration
    fallback_provider: Optional[str] = "openai"
    fallback_model: Optional[str] = "gpt-4o"
    enable_fallback: bool = True

    # Model parameters
    temperature: float = Field(default=0.1, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=100, le=32000)
    timeout_seconds: int = Field(default=60, ge=10, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)

    # Feature flags
    enable_streaming: bool = True
    enable_function_calling: bool = True
    enable_vision: bool = False

    # Rate limiting
    max_requests_per_minute: int = Field(default=60, ge=1, le=1000)
    max_tokens_per_minute: int = Field(default=100000, ge=1000)

    # Provider configurations (stored separately, API keys in Key Vault)
    providers: List[AIProvider] = Field(default_factory=lambda: [
        AIProvider(
            provider_id="claude",
            name="Anthropic Claude",
            enabled=True,
            description="Anthropic's Claude models"
        ),
        AIProvider(
            provider_id="openai",
            name="OpenAI",
            enabled=True,
            description="OpenAI GPT models"
        ),
        AIProvider(
            provider_id="azure_openai",
            name="Azure OpenAI",
            enabled=True,
            description="Azure-hosted OpenAI models"
        ),
    ])

    # Available models
    models: List[AIModel] = Field(default_factory=lambda: [
        AIModel(
            model_id="claude-sonnet-4-20250514",
            provider="claude",
            display_name="Claude Sonnet 4",
            description="Latest Claude model, balanced performance and cost",
            max_tokens=8192,
            supports_vision=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
        ),
        AIModel(
            model_id="claude-3-5-sonnet-20241022",
            provider="claude",
            display_name="Claude 3.5 Sonnet",
            description="Previous generation Claude, excellent for complex tasks",
            max_tokens=8192,
            supports_vision=True,
            cost_per_1k_input_tokens=0.003,
            cost_per_1k_output_tokens=0.015,
        ),
        AIModel(
            model_id="claude-3-5-haiku-20241022",
            provider="claude",
            display_name="Claude 3.5 Haiku",
            description="Fast and cost-effective for simpler tasks",
            max_tokens=4096,
            cost_per_1k_input_tokens=0.0008,
            cost_per_1k_output_tokens=0.004,
        ),
        AIModel(
            model_id="gpt-4o",
            provider="openai",
            display_name="GPT-4o",
            description="OpenAI's latest multimodal model",
            max_tokens=4096,
            supports_vision=True,
            cost_per_1k_input_tokens=0.005,
            cost_per_1k_output_tokens=0.015,
        ),
        AIModel(
            model_id="gpt-4-turbo",
            provider="openai",
            display_name="GPT-4 Turbo",
            description="High capability model with vision support",
            max_tokens=4096,
            supports_vision=True,
            cost_per_1k_input_tokens=0.01,
            cost_per_1k_output_tokens=0.03,
        ),
        AIModel(
            model_id="gpt-3.5-turbo",
            provider="openai",
            display_name="GPT-3.5 Turbo",
            description="Cost-effective for simpler tasks",
            max_tokens=4096,
            cost_per_1k_input_tokens=0.0005,
            cost_per_1k_output_tokens=0.0015,
        ),
    ])

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


class AIConfigUpdate(BaseModel):
    """Request to update AI configuration."""
    active_provider: Optional[str] = None
    active_model: Optional[str] = None
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    enable_fallback: Optional[bool] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=32000)
    timeout_seconds: Optional[int] = Field(default=None, ge=10, le=300)
    retry_attempts: Optional[int] = Field(default=None, ge=0, le=10)
    enable_streaming: Optional[bool] = None
    enable_function_calling: Optional[bool] = None
    enable_vision: Optional[bool] = None
    max_requests_per_minute: Optional[int] = Field(default=None, ge=1, le=1000)
    max_tokens_per_minute: Optional[int] = Field(default=None, ge=1000)


class AIConfigVersion(BaseModel):
    """Historical version of AI configuration."""
    id: str
    config_id: str = "ai_config"
    version: int
    value: dict
    changed_by: str
    changed_by_name: str
    changed_at: datetime
    approval_id: Optional[str] = None
    change_summary: str
