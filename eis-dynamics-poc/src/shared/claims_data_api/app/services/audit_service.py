"""
Audit Service - Provides audit logging and compliance endpoints for Admin Portal.
Tracks system changes, user actions, and provides audit trail for compliance.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== ENUMS ====================

class AuditEventType(str, Enum):
    CONFIG_CHANGE = "config_change"
    USER_ACTION = "user_action"
    CLAIM_ACTION = "claim_action"
    POLICY_ACTION = "policy_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    DATA_ACCESS = "data_access"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ==================== MODELS ====================

class AuditEvent(BaseModel):
    """Individual audit event."""
    id: str
    timestamp: datetime
    event_type: str
    severity: str = "info"
    actor: str
    actor_email: str
    action: str
    resource_type: str
    resource_id: str
    description: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: str = "0.0.0.0"
    user_agent: str = ""
    metadata: dict = {}


class AuditStats(BaseModel):
    """Audit statistics for dashboard."""
    total_events_today: int
    total_events_week: int
    total_events_month: int
    events_by_type: dict
    events_by_severity: dict
    top_actors: List[dict]
    recent_critical: List[dict]


class AuditSearchResult(BaseModel):
    """Audit search results."""
    total: int
    page: int
    page_size: int
    events: List[AuditEvent]


# ==================== MOCK DATA ====================

def generate_mock_audit_events() -> List[AuditEvent]:
    """Generate mock audit events."""
    now = datetime.utcnow()
    return [
        AuditEvent(
            id="aud-001",
            timestamp=now - timedelta(minutes=15),
            event_type="config_change",
            severity="info",
            actor="Admin User",
            actor_email="admin@example.com",
            action="update",
            resource_type="ai_config",
            resource_id="ai-config-001",
            description="Updated AI model temperature from 0.7 to 0.5",
            old_value={"temperature": 0.7},
            new_value={"temperature": 0.5},
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        ),
        AuditEvent(
            id="aud-002",
            timestamp=now - timedelta(minutes=45),
            event_type="claim_action",
            severity="info",
            actor="Claims Processor",
            actor_email="processor@example.com",
            action="approve",
            resource_type="claim",
            resource_id="CLM-2024-001234",
            description="Approved claim CLM-2024-001234 for $450.00",
            old_value={"status": "pending"},
            new_value={"status": "approved", "amount": 450.00},
            ip_address="192.168.1.101",
        ),
        AuditEvent(
            id="aud-003",
            timestamp=now - timedelta(hours=2),
            event_type="user_action",
            severity="info",
            actor="John Smith",
            actor_email="john.smith@example.com",
            action="login",
            resource_type="session",
            resource_id="sess-abc123",
            description="User logged in successfully",
            ip_address="192.168.1.50",
            user_agent="Chrome/120.0",
        ),
        AuditEvent(
            id="aud-004",
            timestamp=now - timedelta(hours=3),
            event_type="security_event",
            severity="warning",
            actor="Unknown",
            actor_email="unknown@example.com",
            action="failed_login",
            resource_type="authentication",
            resource_id="auth-attempt-001",
            description="Failed login attempt - invalid credentials",
            ip_address="203.0.113.50",
            metadata={"attempts": 3},
        ),
        AuditEvent(
            id="aud-005",
            timestamp=now - timedelta(hours=5),
            event_type="policy_action",
            severity="info",
            actor="Underwriter",
            actor_email="underwriter@example.com",
            action="create",
            resource_type="policy",
            resource_id="POL-2024-5678",
            description="Created new policy POL-2024-5678",
            new_value={"policy_type": "comprehensive", "coverage": 15000},
            ip_address="192.168.1.102",
        ),
        AuditEvent(
            id="aud-006",
            timestamp=now - timedelta(hours=8),
            event_type="data_access",
            severity="info",
            actor="Reports System",
            actor_email="reports@example.com",
            action="export",
            resource_type="claims_report",
            resource_id="report-monthly-001",
            description="Exported monthly claims report",
            metadata={"records": 1250, "format": "csv"},
        ),
        AuditEvent(
            id="aud-007",
            timestamp=now - timedelta(days=1),
            event_type="system_event",
            severity="info",
            actor="System",
            actor_email="system@example.com",
            action="backup",
            resource_type="database",
            resource_id="db-backup-001",
            description="Daily database backup completed",
            metadata={"size_mb": 256, "duration_seconds": 45},
        ),
        AuditEvent(
            id="aud-008",
            timestamp=now - timedelta(days=1, hours=2),
            event_type="config_change",
            severity="warning",
            actor="Admin User",
            actor_email="admin@example.com",
            action="update",
            resource_type="fraud_settings",
            resource_id="fraud-config-001",
            description="Lowered fraud detection threshold from 0.8 to 0.7",
            old_value={"threshold": 0.8},
            new_value={"threshold": 0.7},
            ip_address="192.168.1.100",
        ),
        AuditEvent(
            id="aud-009",
            timestamp=now - timedelta(days=2),
            event_type="security_event",
            severity="critical",
            actor="Security System",
            actor_email="security@example.com",
            action="alert",
            resource_type="intrusion_detection",
            resource_id="ids-alert-001",
            description="Potential brute force attack detected",
            metadata={"source_ip": "198.51.100.25", "attempts": 50},
        ),
        AuditEvent(
            id="aud-010",
            timestamp=now - timedelta(days=3),
            event_type="claim_action",
            severity="warning",
            actor="Claims Processor",
            actor_email="processor@example.com",
            action="override",
            resource_type="claim",
            resource_id="CLM-2024-000999",
            description="Manual override of claim denial",
            old_value={"status": "denied", "reason": "pre_existing"},
            new_value={"status": "approved", "override_reason": "documentation provided"},
        ),
    ]


# ==================== ENDPOINTS ====================

@router.get("/stats", response_model=AuditStats)
async def get_audit_stats():
    """Get audit statistics for dashboard."""
    events = generate_mock_audit_events()
    now = datetime.utcnow()

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    events_today = [e for e in events if e.timestamp >= today_start]
    events_week = [e for e in events if e.timestamp >= week_start]
    events_month = [e for e in events if e.timestamp >= month_start]

    # Events by type
    by_type = {}
    for e in events_month:
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

    # Events by severity
    by_severity = {}
    for e in events_month:
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1

    # Top actors
    actor_counts = {}
    for e in events_month:
        actor_counts[e.actor_email] = actor_counts.get(e.actor_email, 0) + 1
    top_actors = sorted(
        [{"email": k, "count": v} for k, v in actor_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]

    # Recent critical events
    critical = [e for e in events if e.severity in ["critical", "error"]]
    recent_critical = [
        {"id": e.id, "timestamp": e.timestamp.isoformat(), "description": e.description}
        for e in critical[:5]
    ]

    return AuditStats(
        total_events_today=len(events_today),
        total_events_week=len(events_week),
        total_events_month=len(events_month),
        events_by_type=by_type,
        events_by_severity=by_severity,
        top_actors=top_actors,
        recent_critical=recent_critical,
    )


@router.get("/events", response_model=AuditSearchResult)
async def search_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    actor: Optional[str] = Query(None, description="Filter by actor email"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    search: Optional[str] = Query(None, description="Search in description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """Search audit events with filters."""
    events = generate_mock_audit_events()

    # Apply filters
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    if severity:
        events = [e for e in events if e.severity == severity]
    if actor:
        events = [e for e in events if actor.lower() in e.actor_email.lower()]
    if resource_type:
        events = [e for e in events if e.resource_type == resource_type]
    if start_date:
        events = [e for e in events if e.timestamp >= start_date]
    if end_date:
        events = [e for e in events if e.timestamp <= end_date]
    if search:
        events = [e for e in events if search.lower() in e.description.lower()]

    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x.timestamp, reverse=True)

    total = len(events)
    start = (page - 1) * page_size
    end = start + page_size

    return AuditSearchResult(
        total=total,
        page=page,
        page_size=page_size,
        events=events[start:end],
    )


@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_audit_event(event_id: str):
    """Get a specific audit event."""
    events = generate_mock_audit_events()
    for e in events:
        if e.id == event_id:
            return e
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Audit event {event_id} not found")


@router.get("/timeline")
async def get_audit_timeline(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
):
    """Get audit timeline for a specific resource or general timeline."""
    events = generate_mock_audit_events()
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours)

    events = [e for e in events if e.timestamp >= cutoff]

    if resource_type:
        events = [e for e in events if e.resource_type == resource_type]
    if resource_id:
        events = [e for e in events if e.resource_id == resource_id]

    events.sort(key=lambda x: x.timestamp, reverse=True)

    return {
        "period_hours": hours,
        "total_events": len(events),
        "timeline": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "severity": e.severity,
                "actor": e.actor,
                "action": e.action,
                "description": e.description,
            }
            for e in events
        ],
    }


@router.get("/export")
async def export_audit_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[str] = Query(None),
):
    """Export audit logs (returns mock data structure)."""
    events = generate_mock_audit_events()

    if start_date:
        events = [e for e in events if e.timestamp >= start_date]
    if end_date:
        events = [e for e in events if e.timestamp <= end_date]
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    return {
        "format": format,
        "total_records": len(events),
        "generated_at": datetime.utcnow().isoformat(),
        "note": "In production, this would return a downloadable file",
        "sample_data": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "actor": e.actor_email,
                "action": e.action,
                "description": e.description,
            }
            for e in events[:5]
        ],
    }


@router.get("/compliance-report")
async def get_compliance_report(
    report_type: str = Query("summary", regex="^(summary|detailed|security)$"),
    period_days: int = Query(30, ge=1, le=365),
):
    """Generate compliance report."""
    events = generate_mock_audit_events()
    now = datetime.utcnow()

    return {
        "report_type": report_type,
        "period_days": period_days,
        "generated_at": now.isoformat(),
        "summary": {
            "total_events": len(events),
            "config_changes": len([e for e in events if e.event_type == "config_change"]),
            "security_events": len([e for e in events if e.event_type == "security_event"]),
            "data_access_events": len([e for e in events if e.event_type == "data_access"]),
            "critical_events": len([e for e in events if e.severity == "critical"]),
            "warning_events": len([e for e in events if e.severity == "warning"]),
        },
        "compliance_status": {
            "audit_logging": "enabled",
            "data_retention": "90_days",
            "encryption_at_rest": "enabled",
            "access_controls": "enabled",
            "last_review": (now - timedelta(days=7)).isoformat(),
        },
        "recommendations": [
            "Review failed login attempts from IP 203.0.113.50",
            "Schedule security review for fraud detection threshold change",
            "Update data retention policy documentation",
        ],
    }
