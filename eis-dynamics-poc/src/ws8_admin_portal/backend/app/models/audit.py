"""Audit logging models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Type of audited action."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    CONFIG_CHANGE = "config_change"
    EXPORT = "export"
    CANCEL = "cancel"


class AuditCategory(str, Enum):
    """Category of audit event."""
    AI_CONFIG = "ai_config"
    CLAIMS_RULES = "claims_rules"
    POLICY_CONFIG = "policy_config"
    RATING_CONFIG = "rating_config"
    USER_MANAGEMENT = "user_management"
    APPROVAL_WORKFLOW = "approval_workflow"
    COST_MONITORING = "cost_monitoring"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"


class AuditLog(BaseModel):
    """Audit log entry."""
    id: Optional[str] = None

    # Event details
    action: AuditAction
    category: AuditCategory
    entity_type: str
    entity_id: str

    # User details
    user_id: str
    user_name: str
    user_role: str
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None

    # Request details
    request_method: str
    request_path: str
    request_body: Optional[dict] = None

    # Change details
    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    change_summary: Optional[str] = None

    # Result
    success: bool = True
    error_message: Optional[str] = None
    response_status: Optional[int] = None

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Partition key for Cosmos DB (YYYY-MM format)
    partition_key: str = ""

    model_config = {"use_enum_values": True}

    def __init__(self, **data):
        super().__init__(**data)
        if not self.partition_key:
            self.partition_key = self.timestamp.strftime("%Y-%m")


class AuditLogQuery(BaseModel):
    """Query parameters for audit logs."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    action: Optional[AuditAction] = None
    category: Optional[AuditCategory] = None
    user_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    success_only: bool = False
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditLogResponse(BaseModel):
    """Response for audit log queries."""
    logs: List[AuditLog]
    total: int
    limit: int
    offset: int


class AuditStats(BaseModel):
    """Audit statistics."""
    total_events: int = 0
    events_today: int = 0
    events_this_week: int = 0
    events_this_month: int = 0
    by_action: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_user: dict[str, int] = Field(default_factory=dict)
    failed_events: int = 0
