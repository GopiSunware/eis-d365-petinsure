"""Audit log endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from ..middleware.auth import require_permission
from ..models.users import User, Permission
from ..models.audit import (
    AuditLog,
    AuditAction,
    AuditCategory,
    AuditLogQuery,
    AuditLogResponse,
    AuditStats,
)
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=AuditLogResponse)
async def get_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action: Optional[AuditAction] = None,
    category: Optional[AuditCategory] = None,
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    success_only: bool = False,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Query audit logs with filters."""
    audit_service = get_audit_service()

    query_params = AuditLogQuery(
        start_date=start_date,
        end_date=end_date,
        action=action,
        category=category,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        success_only=success_only,
        limit=limit,
        offset=offset,
    )

    logs, total = await audit_service.query(query_params)

    return AuditLogResponse(
        logs=logs,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=AuditStats)
async def get_audit_stats(
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Get audit statistics."""
    audit_service = get_audit_service()
    return await audit_service.get_stats()


@router.get("/{log_id}", response_model=AuditLog)
async def get_audit_log(
    log_id: str,
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Get a specific audit log entry."""
    audit_service = get_audit_service()

    query = AuditLogQuery(limit=1)
    logs, _ = await audit_service.query(query)

    for log in logs:
        if log.id == log_id:
            return log

    # If not found in recent logs, do a specific query
    from ..services.cosmos_service import get_cosmos_client
    from ..config import settings

    cosmos = get_cosmos_client()
    if settings.cosmos_db_configured:
        results = await cosmos.query_documents(
            collection="audit_logs",
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": log_id}],
        )
        if results:
            return AuditLog(**results[0])

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Audit log {log_id} not found")


@router.get("/actions/types")
async def get_audit_action_types(
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Get available audit action types."""
    return {
        "actions": [action.value for action in AuditAction],
        "categories": [category.value for category in AuditCategory],
    }


@router.post("/event")
async def log_frontend_event(
    request: Request,
    event_type: str = Query(..., description="Event type: page_view, button_click, form_submit, etc."),
    page: str = Query(..., description="Page or component name"),
    action: Optional[str] = Query(None, description="Specific action taken"),
    entity_type: Optional[str] = Query(None, description="Entity being viewed/interacted with"),
    entity_id: Optional[str] = Query(None, description="Entity ID"),
    metadata: Optional[str] = Query(None, description="Additional metadata as JSON string"),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """
    Log frontend events for comprehensive audit trail.
    Called by frontend when users navigate pages or interact with elements.
    """
    import json

    audit_service = get_audit_service()

    # Map event types to audit actions
    action_map = {
        "page_view": AuditAction.READ,
        "button_click": AuditAction.READ,
        "form_submit": AuditAction.UPDATE,
        "config_view": AuditAction.READ,
        "export": AuditAction.EXPORT,
    }

    audit_action = action_map.get(event_type, AuditAction.READ)

    # Parse metadata if provided
    extra_data = {}
    if metadata:
        try:
            extra_data = json.loads(metadata)
        except json.JSONDecodeError:
            extra_data = {"raw": metadata}

    await audit_service.log(
        action=audit_action,
        category=AuditCategory.SYSTEM,
        entity_type=entity_type or page,
        entity_id=entity_id or page,
        user=current_user,
        request=request,
        new_value={"event_type": event_type, "page": page, "action": action, **extra_data},
        change_summary=f"{event_type}: {page}" + (f" - {action}" if action else ""),
    )

    return {"status": "logged", "event_type": event_type, "page": page}


@router.post("/export")
async def export_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action: Optional[AuditAction] = None,
    category: Optional[AuditCategory] = None,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    current_user: User = Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """
    Export audit logs for compliance/reporting.
    Returns data in specified format.
    """
    audit_service = get_audit_service()

    query_params = AuditLogQuery(
        start_date=start_date,
        end_date=end_date,
        action=action,
        category=category,
        limit=10000,  # Max export size
    )

    logs, total = await audit_service.query(query_params)

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Timestamp", "Action", "Category", "Entity Type", "Entity ID",
            "User ID", "User Name", "User Role", "Success", "Error Message"
        ])

        # Data rows
        for log in logs:
            writer.writerow([
                log.id, log.timestamp.isoformat(), log.action, log.category,
                log.entity_type, log.entity_id, log.user_id, log.user_name,
                log.user_role, log.success, log.error_message or ""
            ])

        return {
            "format": "csv",
            "total_records": total,
            "data": output.getvalue(),
        }

    # JSON format
    return {
        "format": "json",
        "total_records": total,
        "data": [log.model_dump() for log in logs],
    }
