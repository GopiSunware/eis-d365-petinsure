"""Policy configuration endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..middleware.auth import require_permission
from ..models.users import User, Permission
from ..models.policy_config import (
    PolicyPlansConfig,
    PolicyConfigUpdate,
    PlanDefinition,
    WaitingPeriods,
    Exclusions,
    CoverageRules,
)
from ..models.approval import ApprovalRequestCreate, ConfigChangeType
from ..services.config_service import get_config_service
from ..services.approval_service import get_approval_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=PolicyPlansConfig)
async def get_policy_config(
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_READ)),
):
    """Get current policy configuration."""
    config_service = get_config_service()
    return await config_service.get_policy_config()


@router.put("")
async def update_policy_config(
    request: Request,
    update: PolicyConfigUpdate,
    change_reason: str = Query(..., min_length=10, description="Reason for change"),
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_WRITE)),
):
    """
    Update policy configuration.
    Changes require approval.
    """
    config_service = get_config_service()
    approval_service = get_approval_service()
    audit_service = get_audit_service()

    current_config = await config_service.get_policy_config()

    proposed = current_config.model_dump()
    update_fields = []
    for key, value in update.model_dump(exclude_none=True).items():
        if value is not None:
            if hasattr(value, 'model_dump'):
                proposed[key] = value.model_dump()
            elif isinstance(value, list):
                proposed[key] = [v.model_dump() if hasattr(v, 'model_dump') else v for v in value]
            else:
                proposed[key] = value
            update_fields.append(key)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No changes detected")

    approval_request = ApprovalRequestCreate(
        change_type=ConfigChangeType.POLICY_CONFIG,
        entity_id="policy_config",
        proposed_value=proposed,
        change_summary=f"Policy config update: {', '.join(update_fields)}",
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
        change_type="policy_config",
        approval_id=approval.id,
    )

    return {
        "status": "pending_approval",
        "approval_id": approval.id,
        "message": "Policy config change submitted for approval",
        "changes": update_fields,
    }


@router.get("/plans", response_model=List[PlanDefinition])
async def get_plans(
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_READ)),
):
    """Get all plan definitions."""
    config_service = get_config_service()
    config = await config_service.get_policy_config()
    return config.plans


@router.get("/plans/{plan_id}", response_model=PlanDefinition)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_READ)),
):
    """Get a specific plan by ID."""
    config_service = get_config_service()
    config = await config_service.get_policy_config()

    for plan in config.plans:
        if plan.plan_id == plan_id:
            return plan

    raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")


@router.get("/waiting-periods", response_model=WaitingPeriods)
async def get_waiting_periods(
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_READ)),
):
    """Get waiting periods configuration."""
    config_service = get_config_service()
    config = await config_service.get_policy_config()
    return config.waiting_periods


@router.put("/waiting-periods")
async def update_waiting_periods(
    request: Request,
    update: WaitingPeriods,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_WRITE)),
):
    """Update waiting periods."""
    return await update_policy_config(
        request=request,
        update=PolicyConfigUpdate(waiting_periods=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/exclusions", response_model=Exclusions)
async def get_exclusions(
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_READ)),
):
    """Get exclusions configuration."""
    config_service = get_config_service()
    config = await config_service.get_policy_config()
    return config.exclusions


@router.put("/exclusions")
async def update_exclusions(
    request: Request,
    update: Exclusions,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_WRITE)),
):
    """Update exclusions."""
    return await update_policy_config(
        request=request,
        update=PolicyConfigUpdate(exclusions=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/coverage-rules", response_model=CoverageRules)
async def get_coverage_rules(
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_READ)),
):
    """Get coverage rules."""
    config_service = get_config_service()
    config = await config_service.get_policy_config()
    return config.coverage_rules


@router.put("/coverage-rules")
async def update_coverage_rules(
    request: Request,
    update: CoverageRules,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_POLICY_WRITE)),
):
    """Update coverage rules."""
    return await update_policy_config(
        request=request,
        update=PolicyConfigUpdate(coverage_rules=update),
        change_reason=change_reason,
        current_user=current_user,
    )
