"""AI Configuration API - Runtime model selection for demo."""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from eis_common.ai_config import (
    AIConfigState,
    AIModelConfig,
    get_ai_config,
    set_ai_config,
    get_available_models,
    get_models_by_provider,
)
from eis_common.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()


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


@router.get("/config", response_model=AIConfigResponse)
async def get_current_config():
    """Get current AI configuration."""
    config = get_ai_config()

    # Check which providers are configured
    # OpenAI is configured if EITHER regular OpenAI key OR Azure OpenAI is set
    openai_configured = bool(settings.openai_api_key) or bool(
        settings.azure_openai_api_key and settings.azure_openai_endpoint
    )

    provider_status = {
        "claude": {
            "configured": bool(settings.anthropic_api_key),
            "api_key_set": bool(settings.anthropic_api_key),
        },
        "openai": {
            "configured": openai_configured,
            "api_key_set": bool(settings.openai_api_key or settings.azure_openai_api_key),
            "is_azure": bool(settings.azure_openai_endpoint),
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

    # Validate provider is configured
    if request.provider == "claude" and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=400,
            detail="Claude API key not configured. Set ANTHROPIC_API_KEY environment variable."
        )

    # Check OpenAI - either regular or Azure
    openai_configured = bool(settings.openai_api_key) or bool(
        settings.azure_openai_api_key and settings.azure_openai_endpoint
    )
    if request.provider == "openai" and not openai_configured:
        raise HTTPException(
            status_code=400,
            detail="OpenAI not configured. Set OPENAI_API_KEY or AZURE_OPENAI_* environment variables."
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
    provider_status = {
        "claude": {"configured": bool(settings.anthropic_api_key)},
        "openai": {"configured": bool(settings.azure_openai_api_key)},
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
    """Test current AI configuration with a simple prompt."""
    config = get_ai_config()

    try:
        if config.provider == "claude":
            from eis_common.azure import get_claude_client
            client = get_claude_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Say 'AI connection successful' in exactly those words."}],
                max_tokens=50,
            )
        else:
            from eis_common.azure import get_openai_client
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'AI connection successful' in exactly those words."},
                ],
                max_tokens=50,
            )

        return {
            "status": "success",
            "provider": config.provider,
            "model": config.model_id,
            "response": response.strip(),
        }

    except Exception as e:
        logger.error(f"AI test failed: {e}")
        return {
            "status": "error",
            "provider": config.provider,
            "model": config.model_id,
            "error": str(e),
        }
