"""AI Configuration management endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..middleware.auth import get_current_user, require_permission
from ..models.users import User, Permission
from ..models.ai_config import AIConfiguration, AIConfigUpdate, AIProvider, AIModel
from ..models.approval import ApprovalRequestCreate, ConfigChangeType
from ..services.config_service import get_config_service
from ..services.approval_service import get_approval_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=AIConfiguration)
async def get_ai_config(
    current_user: User = Depends(require_permission(Permission.CONFIG_AI_READ)),
):
    """Get current AI configuration."""
    config_service = get_config_service()
    return await config_service.get_ai_config()


@router.put("")
async def update_ai_config(
    request: Request,
    update: AIConfigUpdate,
    change_reason: str = Query(..., min_length=10, description="Reason for change"),
    current_user: User = Depends(require_permission(Permission.CONFIG_AI_WRITE)),
):
    """
    Update AI configuration.

    Changes require approval from a user with APPROVER role.
    Returns the pending approval request.
    """
    config_service = get_config_service()
    approval_service = get_approval_service()
    audit_service = get_audit_service()

    # Get current config
    current_config = await config_service.get_ai_config()

    # Build proposed changes
    proposed = current_config.model_dump()
    update_fields = []
    for key, value in update.model_dump(exclude_none=True).items():
        if proposed.get(key) != value:
            proposed[key] = value
            update_fields.append(key)

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No changes detected"
        )

    # Create approval request
    approval_request = ApprovalRequestCreate(
        change_type=ConfigChangeType.AI_CONFIG,
        entity_id="ai_config",
        proposed_value=proposed,
        change_summary=f"AI config update: {', '.join(update_fields)}",
        change_reason=change_reason,
    )

    approval = await approval_service.create_approval(
        request=approval_request,
        current_value=current_config.model_dump(),
        requester=current_user,
    )

    # Log audit
    await audit_service.log_config_change_request(
        request=request,
        user=current_user,
        change_type="ai_config",
        approval_id=approval.id,
    )

    return {
        "status": "pending_approval",
        "approval_id": approval.id,
        "message": "Configuration change submitted for approval",
        "changes": update_fields,
    }


@router.get("/providers", response_model=List[AIProvider])
async def get_ai_providers(
    current_user: User = Depends(require_permission(Permission.CONFIG_AI_READ)),
):
    """Get available AI providers."""
    config_service = get_config_service()
    config = await config_service.get_ai_config()
    return config.providers


@router.get("/models", response_model=List[AIModel])
async def get_ai_models(
    provider: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.CONFIG_AI_READ)),
):
    """Get available AI models, optionally filtered by provider."""
    config_service = get_config_service()
    config = await config_service.get_ai_config()
    models = config.models

    if provider:
        models = [m for m in models if m.provider == provider]

    return models


@router.get("/history")
async def get_ai_config_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_permission(Permission.CONFIG_AI_READ)),
):
    """Get AI configuration change history."""
    config_service = get_config_service()
    history = await config_service.get_ai_config_history(limit=limit)
    return {"history": history, "total": len(history)}


@router.post("/test-connection")
async def test_ai_connection(
    provider: str = Query(..., description="Provider to test: claude, openai, azure_openai"),
    current_user: User = Depends(require_permission(Permission.CONFIG_AI_READ)),
):
    """Test connection to AI provider."""
    # In a real implementation, this would make a test call to the provider
    # For now, return mock status
    return {
        "provider": provider,
        "status": "connected",
        "latency_ms": 145,
        "message": f"Successfully connected to {provider}",
    }
