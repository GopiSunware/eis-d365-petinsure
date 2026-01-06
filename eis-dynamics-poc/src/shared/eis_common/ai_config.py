"""Runtime AI Configuration Manager for demo purposes."""
from typing import Dict, List, Optional
from pydantic import BaseModel


class AIModelConfig(BaseModel):
    """Configuration for a specific AI model."""
    provider: str  # "claude" or "openai"
    model_id: str
    display_name: str
    description: str


# Available models for selection
AVAILABLE_MODELS: List[AIModelConfig] = [
    # Claude models
    AIModelConfig(
        provider="claude",
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        description="Latest Claude model - fast and capable"
    ),
    AIModelConfig(
        provider="claude",
        model_id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        description="Previous generation - stable and reliable"
    ),
    AIModelConfig(
        provider="claude",
        model_id="claude-3-haiku-20240307",
        display_name="Claude 3 Haiku",
        description="Fastest Claude model - good for quick tasks"
    ),
    # OpenAI models
    AIModelConfig(
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o",
        description="OpenAI's flagship multimodal model"
    ),
    AIModelConfig(
        provider="openai",
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        description="Fast GPT-4 variant with large context"
    ),
    AIModelConfig(
        provider="openai",
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        description="Fast and cost-effective"
    ),
]


class AIConfigState(BaseModel):
    """Current AI configuration state."""
    provider: str = "claude"
    model_id: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 2000


# Global runtime state (for demo - in production would use database)
_current_config = AIConfigState()


def get_ai_config() -> AIConfigState:
    """Get current AI configuration."""
    return _current_config


def set_ai_config(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AIConfigState:
    """Update AI configuration at runtime."""
    global _current_config

    if provider is not None:
        _current_config.provider = provider
    if model_id is not None:
        _current_config.model_id = model_id
    if temperature is not None:
        _current_config.temperature = temperature
    if max_tokens is not None:
        _current_config.max_tokens = max_tokens

    return _current_config


def get_available_models() -> List[AIModelConfig]:
    """Get list of available AI models."""
    return AVAILABLE_MODELS


def get_models_by_provider(provider: str) -> List[AIModelConfig]:
    """Get models filtered by provider."""
    return [m for m in AVAILABLE_MODELS if m.provider == provider]
