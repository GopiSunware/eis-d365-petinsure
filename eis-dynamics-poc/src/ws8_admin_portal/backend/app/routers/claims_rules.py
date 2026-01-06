"""Claims rules configuration endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..middleware.auth import require_permission
from ..models.users import User, Permission
from ..models.claims_rules import (
    ClaimsRulesConfig,
    ClaimsRulesUpdate,
    AutoAdjudicationConfig,
    FraudDetectionConfig,
    EscalationRules,
)
from ..models.approval import ApprovalRequestCreate, ConfigChangeType
from ..services.config_service import get_config_service
from ..services.approval_service import get_approval_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ClaimsRulesConfig)
async def get_claims_rules(
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_READ)),
):
    """Get current claims rules configuration."""
    config_service = get_config_service()
    return await config_service.get_claims_rules()


@router.get("/rules", response_model=ClaimsRulesConfig)
async def get_claims_rules_alias(
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_READ)),
):
    """Get current claims rules configuration (alias)."""
    return await get_claims_rules(current_user)


@router.put("")
async def update_claims_rules(
    request: Request,
    update: ClaimsRulesUpdate,
    change_reason: str = Query(..., min_length=10, description="Reason for change"),
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_WRITE)),
):
    """
    Update claims rules configuration.
    Changes require approval.
    """
    config_service = get_config_service()
    approval_service = get_approval_service()
    audit_service = get_audit_service()

    # Get current config
    current_config = await config_service.get_claims_rules()

    # Build proposed changes
    proposed = current_config.model_dump()
    update_fields = []
    for key, value in update.model_dump(exclude_none=True).items():
        if value is not None:
            proposed[key] = value if not hasattr(value, 'model_dump') else value.model_dump()
            update_fields.append(key)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No changes detected")

    # Create approval request
    approval_request = ApprovalRequestCreate(
        change_type=ConfigChangeType.CLAIMS_RULES,
        entity_id="claims_rules",
        proposed_value=proposed,
        change_summary=f"Claims rules update: {', '.join(update_fields)}",
        change_reason=change_reason,
    )

    approval = await approval_service.create_approval(
        request=approval_request,
        current_value=current_config.model_dump(),
        requester=current_user,
    )

    await audit_service.log_config_change_request(
        request=request,
        user=current_user,
        change_type="claims_rules",
        approval_id=approval.id,
    )

    return {
        "status": "pending_approval",
        "approval_id": approval.id,
        "message": "Claims rules change submitted for approval",
        "changes": update_fields,
    }


@router.get("/auto-adjudication", response_model=AutoAdjudicationConfig)
async def get_auto_adjudication_config(
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_READ)),
):
    """Get auto-adjudication configuration."""
    config_service = get_config_service()
    config = await config_service.get_claims_rules()
    return config.auto_adjudication


@router.put("/auto-adjudication")
async def update_auto_adjudication(
    request: Request,
    update: AutoAdjudicationConfig,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_WRITE)),
):
    """Update auto-adjudication configuration."""
    return await update_claims_rules(
        request=request,
        update=ClaimsRulesUpdate(auto_adjudication=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/fraud", response_model=FraudDetectionConfig)
async def get_fraud_detection_config(
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_READ)),
):
    """Get fraud detection configuration."""
    config_service = get_config_service()
    config = await config_service.get_claims_rules()
    return config.fraud_detection


@router.put("/fraud")
async def update_fraud_detection(
    request: Request,
    update: FraudDetectionConfig,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_WRITE)),
):
    """Update fraud detection configuration."""
    return await update_claims_rules(
        request=request,
        update=ClaimsRulesUpdate(fraud_detection=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/escalation", response_model=EscalationRules)
async def get_escalation_rules(
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_READ)),
):
    """Get escalation rules configuration."""
    config_service = get_config_service()
    config = await config_service.get_claims_rules()
    return config.escalation_rules


@router.put("/escalation")
async def update_escalation_rules(
    request: Request,
    update: EscalationRules,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_CLAIMS_WRITE)),
):
    """Update escalation rules."""
    return await update_claims_rules(
        request=request,
        update=ClaimsRulesUpdate(escalation_rules=update),
        change_reason=change_reason,
        current_user=current_user,
    )
