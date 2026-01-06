"""Approval workflow endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..middleware.auth import get_current_user, require_permission, require_role
from ..models.users import User, UserRole, Permission
from ..models.approval import (
    ApprovalRequest,
    ApprovalRequestResponse,
    ApprovalListResponse,
    ApprovalAction,
    ApprovalStatus,
    ApprovalStats,
    ConfigChangeType,
)
from ..models.audit import AuditAction, AuditCategory
from ..services.approval_service import get_approval_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    status: Optional[ApprovalStatus] = None,
    change_type: Optional[ConfigChangeType] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """List approval requests with optional filters."""
    approval_service = get_approval_service()

    approvals, total, pending_count = await approval_service.list_approvals(
        status=status,
        change_type=change_type,
        limit=limit,
        offset=offset,
    )

    responses = [
        ApprovalRequestResponse(
            id=a.id,
            change_type=a.change_type,
            entity_id=a.entity_id,
            current_value=a.current_value,
            proposed_value=a.proposed_value,
            change_summary=a.change_summary,
            change_reason=a.change_reason,
            status=a.status,
            requested_by=a.requested_by,
            requested_by_name=a.requested_by_name,
            requested_at=a.requested_at,
            approved_by=a.approved_by,
            approved_by_name=a.approved_by_name,
            approved_at=a.approved_at,
            approval_comment=a.approval_comment,
            rejection_reason=a.rejection_reason,
            expires_at=a.expires_at,
            tags=a.tags,
        )
        for a in approvals
    ]

    return ApprovalListResponse(
        approvals=responses,
        total=total,
        pending_count=pending_count,
        limit=limit,
        offset=offset,
    )


@router.get("/pending", response_model=ApprovalListResponse)
async def list_pending_approvals(
    change_type: Optional[ConfigChangeType] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """List only pending approval requests."""
    return await list_approvals(
        status=ApprovalStatus.PENDING,
        change_type=change_type,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get("/stats", response_model=ApprovalStats)
async def get_approval_stats(
    current_user: User = Depends(get_current_user),
):
    """Get approval statistics."""
    approval_service = get_approval_service()
    return await approval_service.get_stats()


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval(
    approval_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific approval request."""
    approval_service = get_approval_service()
    approval = await approval_service.get_approval(approval_id)

    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")

    return ApprovalRequestResponse(
        id=approval.id,
        change_type=approval.change_type,
        entity_id=approval.entity_id,
        current_value=approval.current_value,
        proposed_value=approval.proposed_value,
        change_summary=approval.change_summary,
        change_reason=approval.change_reason,
        status=approval.status,
        requested_by=approval.requested_by,
        requested_by_name=approval.requested_by_name,
        requested_at=approval.requested_at,
        approved_by=approval.approved_by,
        approved_by_name=approval.approved_by_name,
        approved_at=approval.approved_at,
        approval_comment=approval.approval_comment,
        rejection_reason=approval.rejection_reason,
        expires_at=approval.expires_at,
        tags=approval.tags,
    )


@router.post("/{approval_id}/process", response_model=ApprovalRequestResponse)
async def process_approval(
    approval_id: str,
    request: Request,
    action: ApprovalAction,
    current_user: User = Depends(get_current_user),
):
    """Process an approval request (approve/reject/cancel)."""
    approval_service = get_approval_service()
    audit_service = get_audit_service()

    try:
        approval = await approval_service.process_approval(
            approval_id=approval_id,
            action=action,
            approver=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Audit log
    audit_action = {
        "approve": AuditAction.APPROVE,
        "reject": AuditAction.REJECT,
        "cancel": AuditAction.CANCEL,
    }.get(action.action, AuditAction.UPDATE)

    await audit_service.log(
        action=audit_action,
        category=AuditCategory.APPROVAL_WORKFLOW,
        entity_type="approval",
        entity_id=approval_id,
        user=current_user,
        request=request,
        change_summary=f"Approval {approval_id} {action.action}ed",
        new_value={
            "status": approval.status,
            "action": action.action,
            "comment": action.comment,
        },
    )

    return ApprovalRequestResponse(
        id=approval.id,
        change_type=approval.change_type,
        entity_id=approval.entity_id,
        current_value=approval.current_value,
        proposed_value=approval.proposed_value,
        change_summary=approval.change_summary,
        change_reason=approval.change_reason,
        status=approval.status,
        requested_by=approval.requested_by,
        requested_by_name=approval.requested_by_name,
        requested_at=approval.requested_at,
        approved_by=approval.approved_by,
        approved_by_name=approval.approved_by_name,
        approved_at=approval.approved_at,
        approval_comment=approval.approval_comment,
        rejection_reason=approval.rejection_reason,
        expires_at=approval.expires_at,
        tags=approval.tags,
    )


@router.post("/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    request: Request,
    comment: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.APPROVER)),
):
    """Approve an approval request (shortcut endpoint)."""
    return await process_approval(
        approval_id=approval_id,
        request=request,
        action=ApprovalAction(action="approve", comment=comment),
        current_user=current_user,
    )


@router.post("/{approval_id}/reject")
async def reject_request(
    approval_id: str,
    request: Request,
    rejection_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.APPROVER)),
):
    """Reject an approval request (shortcut endpoint)."""
    return await process_approval(
        approval_id=approval_id,
        request=request,
        action=ApprovalAction(action="reject", rejection_reason=rejection_reason),
        current_user=current_user,
    )


@router.post("/{approval_id}/cancel")
async def cancel_request(
    approval_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Cancel an approval request (only by requester or admin)."""
    return await process_approval(
        approval_id=approval_id,
        request=request,
        action=ApprovalAction(action="cancel"),
        current_user=current_user,
    )


@router.post("/expire-old")
async def expire_old_approvals(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Manually trigger expiration of old approval requests."""
    approval_service = get_approval_service()
    expired_count = await approval_service.expire_old_approvals()
    return {"message": f"Expired {expired_count} approval requests"}
