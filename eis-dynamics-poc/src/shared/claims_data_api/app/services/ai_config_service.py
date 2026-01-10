"""
AI Configuration Service - Runtime model selection.
Provides endpoints for managing AI provider and model configuration.
"""

import os
import logging
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== ENUMS ====================

class AIProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"


# ==================== MODELS ====================

class AIModelConfig(BaseModel):
    """AI model configuration."""
    provider: str
    model_id: str
    display_name: str
    description: str
    max_tokens: int
    supports_vision: bool = False
    supports_tools: bool = True


class AIConfigState(BaseModel):
    """Current AI configuration state."""
    provider: str = "claude"
    model_id: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 2000


class AIConfigUpdateRequest(BaseModel):
    """Request to update AI configuration."""
    provider: Optional[str] = Field(None, description="AI provider: 'claude' or 'openai'")
    model_id: Optional[str] = Field(None, description="Model ID to use")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Temperature (0-2)")
    max_tokens: Optional[int] = Field(None, ge=100, le=8000, description="Max tokens")


class AIConfigResponse(BaseModel):
    """Current AI configuration response."""
    provider: str
    model_id: str
    temperature: float
    max_tokens: int
    provider_status: dict


class AvailableModelsResponse(BaseModel):
    """Available AI models response."""
    models: List[AIModelConfig]
    current_provider: str
    current_model: str


# ==================== AVAILABLE MODELS ====================

AVAILABLE_MODELS = [
    # Claude Models
    AIModelConfig(
        provider="claude",
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        description="Latest Claude Sonnet with superior reasoning",
        max_tokens=8192,
        supports_vision=True,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="claude",
        model_id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        description="Most intelligent model, best for complex reasoning",
        max_tokens=8192,
        supports_vision=True,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="claude",
        model_id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        description="Fastest model, great for quick tasks",
        max_tokens=8192,
        supports_vision=True,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="claude",
        model_id="claude-3-opus-20240229",
        display_name="Claude 3 Opus",
        description="Most capable Claude 3 model",
        max_tokens=4096,
        supports_vision=True,
        supports_tools=True,
    ),
    # OpenAI Models
    AIModelConfig(
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o",
        description="Most capable GPT-4 with vision support",
        max_tokens=4096,
        supports_vision=True,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        description="Fast and cost-effective GPT-4o variant",
        max_tokens=4096,
        supports_vision=True,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="openai",
        model_id="gpt-4-turbo-preview",
        display_name="GPT-4 Turbo",
        description="Latest GPT-4 with improved performance",
        max_tokens=4096,
        supports_vision=True,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="openai",
        model_id="gpt-4",
        display_name="GPT-4",
        description="Most capable GPT-4 model",
        max_tokens=8192,
        supports_vision=False,
        supports_tools=True,
    ),
    AIModelConfig(
        provider="openai",
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        description="Fast and cost-effective",
        max_tokens=4096,
        supports_vision=False,
        supports_tools=True,
    ),
]


# ==================== STATE ====================

# Current configuration state (in-memory, resets on restart)
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
    """Update AI configuration."""
    global _current_config

    if provider:
        _current_config.provider = provider
        # Set default model for provider if not specified
        if not model_id:
            if provider == "claude":
                _current_config.model_id = "claude-3-5-sonnet-20241022"
            else:
                _current_config.model_id = "gpt-4-turbo-preview"

    if model_id:
        _current_config.model_id = model_id

    if temperature is not None:
        _current_config.temperature = temperature

    if max_tokens is not None:
        _current_config.max_tokens = max_tokens

    return _current_config


def get_available_models() -> List[AIModelConfig]:
    """Get all available models."""
    return AVAILABLE_MODELS


def get_models_by_provider(provider: str) -> List[AIModelConfig]:
    """Get models filtered by provider."""
    return [m for m in AVAILABLE_MODELS if m.provider == provider]


# ==================== ENDPOINTS ====================

@router.get("/config", response_model=AIConfigResponse)
async def get_current_config():
    """Get current AI configuration."""
    config = get_ai_config()

    # Check which providers are configured via environment variables
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    azure_openai_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")

    openai_configured = bool(openai_key) or bool(azure_openai_key and azure_openai_endpoint)

    provider_status = {
        "claude": {
            "configured": bool(anthropic_key),
            "api_key_set": bool(anthropic_key),
        },
        "openai": {
            "configured": openai_configured,
            "api_key_set": bool(openai_key or azure_openai_key),
            "is_azure": bool(azure_openai_endpoint),
        },
    }

    return AIConfigResponse(
        provider=config.provider,
        model_id=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        provider_status=provider_status,
    )


@router.put("/config", response_model=AIConfigResponse)
async def update_config(request: AIConfigUpdateRequest):
    """Update AI configuration at runtime."""
    logger.info(f"Updating AI config: {request}")

    # Validate provider if changing
    if request.provider and request.provider not in ["claude", "openai"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Must be 'claude' or 'openai'"
        )

    # Update config
    updated = set_ai_config(
        provider=request.provider,
        model_id=request.model_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    logger.info(f"AI config updated: provider={updated.provider}, model={updated.model_id}")

    # Get provider status for response
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    azure_openai_key = os.environ.get("AZURE_OPENAI_API_KEY", "")

    provider_status = {
        "claude": {"configured": bool(anthropic_key)},
        "openai": {"configured": bool(openai_key or azure_openai_key)},
    }

    return AIConfigResponse(
        provider=updated.provider,
        model_id=updated.model_id,
        temperature=updated.temperature,
        max_tokens=updated.max_tokens,
        provider_status=provider_status,
    )


@router.get("/models", response_model=AvailableModelsResponse)
async def get_models(provider: Optional[str] = None):
    """Get available AI models, optionally filtered by provider."""
    config = get_ai_config()

    if provider:
        models = get_models_by_provider(provider)
    else:
        models = get_available_models()

    return AvailableModelsResponse(
        models=models,
        current_provider=config.provider,
        current_model=config.model_id,
    )


@router.post("/test")
async def test_ai_connection():
    """Test current AI configuration (simulated for demo)."""
    config = get_ai_config()

    # For demo purposes, return success if provider is configured
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    azure_openai_key = os.environ.get("AZURE_OPENAI_API_KEY", "")

    if config.provider == "claude":
        if anthropic_key:
            return {
                "status": "success",
                "provider": config.provider,
                "model": config.model_id,
                "response": "AI connection successful - Claude is ready",
            }
        else:
            return {
                "status": "warning",
                "provider": config.provider,
                "model": config.model_id,
                "response": "Claude API key not configured, but service is running in demo mode",
            }
    else:  # openai
        if openai_key or azure_openai_key:
            return {
                "status": "success",
                "provider": config.provider,
                "model": config.model_id,
                "response": "AI connection successful - OpenAI is ready",
            }
        else:
            return {
                "status": "warning",
                "provider": config.provider,
                "model": config.model_id,
                "response": "OpenAI API key not configured, but service is running in demo mode",
            }
