"""Maker-Checker approval workflow models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ConfigChangeType(str, Enum):
    """Type of configuration change."""
    AI_CONFIG = "ai_config"
    CLAIMS_RULES = "claims_rules"
    POLICY_CONFIG = "policy_config"
    RATING_CONFIG = "rating_config"
    USER_ROLE = "user_role"


class ApprovalRequest(BaseModel):
    """Approval request for configuration change."""
    id: Optional[str] = None
    change_type: ConfigChangeType
    entity_id: str  # ID of the config being changed

    # Change details
    current_value: dict[str, Any] = Field(default_factory=dict)
    proposed_value: dict[str, Any]
    change_summary: str
    change_reason: str

    # Workflow
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str  # User ID of requester (Maker)
    requested_by_name: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    # Approval details
    approved_by: Optional[str] = None  # User ID of approver (Checker)
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Expiry
    expires_at: datetime

    # Metadata
    version: int = 1
    tags: List[str] = Field(default_factory=list)

    model_config = {"use_enum_values": True}


class ApprovalRequestCreate(BaseModel):
    """Request to create an approval."""
    change_type: ConfigChangeType
    entity_id: str
    proposed_value: dict[str, Any]
    change_summary: str
    change_reason: str
    tags: List[str] = Field(default_factory=list)


class ApprovalAction(BaseModel):
    """Action on an approval request."""
    action: str = Field(..., pattern="^(approve|reject|cancel)$")
    comment: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalRequestResponse(BaseModel):
    """Approval request response."""
    id: str
    change_type: str
    entity_id: str
    current_value: dict[str, Any]
    proposed_value: dict[str, Any]
    change_summary: str
    change_reason: str
    status: str
    requested_by: str
    requested_by_name: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    expires_at: datetime
    tags: List[str] = Field(default_factory=list)


class ApprovalListResponse(BaseModel):
    """Response for listing approvals."""
    approvals: List[ApprovalRequestResponse]
    total: int
    pending_count: int
    limit: int
    offset: int


class ApprovalStats(BaseModel):
    """Approval statistics."""
    pending: int = 0
    approved_today: int = 0
    rejected_today: int = 0
    expired_today: int = 0
    avg_approval_time_hours: Optional[float] = None
