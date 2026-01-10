"""
Approvals Service - Provides approval workflow endpoints for Admin Portal.
Handles pending approvals, approval stats, and approval actions.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
from uuid import uuid4

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== ENUMS ====================

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ApprovalType(str, Enum):
    CONFIG_CHANGE = "config_change"
    CLAIM_OVERRIDE = "claim_override"
    POLICY_EXCEPTION = "policy_exception"
    RATE_CHANGE = "rate_change"
    USER_ACCESS = "user_access"


# ==================== MODELS ====================

class ApprovalItem(BaseModel):
    """Individual approval item."""
    id: str
    type: str
    title: str
    description: str
    requester: str
    requester_email: str
    status: str = "pending"
    priority: str = "normal"
    created_at: datetime
    updated_at: datetime
    data: dict = {}
    approvers: List[str] = []
    comments: List[dict] = []


class ApprovalStats(BaseModel):
    """Approval statistics."""
    total_pending: int
    total_approved_today: int
    total_rejected_today: int
    average_approval_time_hours: float
    by_type: dict
    by_priority: dict
    oldest_pending_days: int


class ApprovalAction(BaseModel):
    """Approval action request."""
    action: str  # approve, reject, escalate
    comment: Optional[str] = None
    approver: str = "admin@example.com"


# ==================== MOCK DATA ====================

def generate_mock_approvals() -> List[ApprovalItem]:
    """Generate mock approval items."""
    now = datetime.utcnow()
    return [
        ApprovalItem(
            id="apr-001",
            type="config_change",
            title="AI Model Change Request",
            description="Request to switch from Claude 3.5 Sonnet to Claude Sonnet 4",
            requester="John Smith",
            requester_email="john.smith@example.com",
            status="pending",
            priority="high",
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
            data={
                "current_model": "claude-3-5-sonnet-20241022",
                "requested_model": "claude-sonnet-4-20250514",
                "reason": "Better performance for complex claims",
            },
            approvers=["admin@example.com"],
        ),
        ApprovalItem(
            id="apr-002",
            type="claim_override",
            title="Claim Amount Override",
            description="Override claim CLM-2024-001234 amount from $500 to $750",
            requester="Sarah Johnson",
            requester_email="sarah.j@example.com",
            status="pending",
            priority="normal",
            created_at=now - timedelta(hours=5),
            updated_at=now - timedelta(hours=5),
            data={
                "claim_id": "CLM-2024-001234",
                "original_amount": 500.00,
                "requested_amount": 750.00,
                "justification": "Additional vet consultation required",
            },
            approvers=["admin@example.com", "manager@example.com"],
        ),
        ApprovalItem(
            id="apr-003",
            type="rate_change",
            title="Breed Factor Adjustment",
            description="Request to reduce Bulldog breed factor from 1.5 to 1.4",
            requester="Mike Wilson",
            requester_email="m.wilson@example.com",
            status="pending",
            priority="low",
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
            data={
                "breed": "Bulldog",
                "current_factor": 1.5,
                "requested_factor": 1.4,
                "analysis": "Recent claims data shows lower risk profile",
            },
            approvers=["admin@example.com"],
        ),
        ApprovalItem(
            id="apr-004",
            type="policy_exception",
            title="Waiting Period Waiver",
            description="Waive 14-day illness waiting period for policy POL-2024-5678",
            requester="Emily Davis",
            requester_email="emily.d@example.com",
            status="pending",
            priority="high",
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=8),
            data={
                "policy_id": "POL-2024-5678",
                "waiver_type": "illness_waiting_period",
                "reason": "Transfer from competitor with continuous coverage",
            },
            approvers=["admin@example.com", "underwriter@example.com"],
        ),
        ApprovalItem(
            id="apr-005",
            type="user_access",
            title="Admin Access Request",
            description="Request admin portal access for new team member",
            requester="HR System",
            requester_email="hr@example.com",
            status="pending",
            priority="normal",
            created_at=now - timedelta(hours=12),
            updated_at=now - timedelta(hours=12),
            data={
                "user_email": "new.hire@example.com",
                "requested_role": "claims_reviewer",
                "department": "Claims Processing",
            },
            approvers=["admin@example.com"],
        ),
    ]


# In-memory storage for demo
_approvals_cache: List[ApprovalItem] = []


def get_approvals() -> List[ApprovalItem]:
    """Get all approvals (lazy load mock data)."""
    global _approvals_cache
    if not _approvals_cache:
        _approvals_cache = generate_mock_approvals()
    return _approvals_cache


# ==================== ENDPOINTS ====================

@router.get("/stats", response_model=ApprovalStats)
async def get_approval_stats():
    """Get approval statistics for dashboard."""
    approvals = get_approvals()
    pending = [a for a in approvals if a.status == "pending"]

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate by type
    by_type = {}
    for a in pending:
        by_type[a.type] = by_type.get(a.type, 0) + 1

    # Calculate by priority
    by_priority = {}
    for a in pending:
        by_priority[a.priority] = by_priority.get(a.priority, 0) + 1

    # Calculate oldest pending
    oldest_days = 0
    if pending:
        oldest = min(a.created_at for a in pending)
        oldest_days = (now - oldest).days

    return ApprovalStats(
        total_pending=len(pending),
        total_approved_today=2,  # Mock
        total_rejected_today=1,  # Mock
        average_approval_time_hours=4.5,  # Mock
        by_type=by_type,
        by_priority=by_priority,
        oldest_pending_days=oldest_days,
    )


@router.get("/pending", response_model=List[ApprovalItem])
async def get_pending_approvals(
    type: Optional[str] = Query(None, description="Filter by approval type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get pending approval items."""
    approvals = get_approvals()
    pending = [a for a in approvals if a.status == "pending"]

    # Apply filters
    if type:
        pending = [a for a in pending if a.type == type]
    if priority:
        pending = [a for a in pending if a.priority == priority]

    # Sort by priority (high first) then by created_at (oldest first)
    priority_order = {"high": 0, "normal": 1, "low": 2}
    pending.sort(key=lambda x: (priority_order.get(x.priority, 1), x.created_at))

    return pending[offset:offset + limit]


@router.get("/history", response_model=List[ApprovalItem])
async def get_approval_history(
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=100),
):
    """Get approval history."""
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)

    # Return mock historical data
    history = [
        ApprovalItem(
            id="apr-hist-001",
            type="config_change",
            title="Temperature Adjustment",
            description="Changed AI temperature from 0.7 to 0.5",
            requester="Admin",
            requester_email="admin@example.com",
            status="approved",
            priority="normal",
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3),
            data={"old_value": 0.7, "new_value": 0.5},
            comments=[{"user": "admin@example.com", "text": "Approved for production", "timestamp": (now - timedelta(days=3)).isoformat()}],
        ),
        ApprovalItem(
            id="apr-hist-002",
            type="claim_override",
            title="Claim Denial Override",
            description="Override denial for claim CLM-2024-000999",
            requester="Claims Manager",
            requester_email="claims@example.com",
            status="rejected",
            priority="high",
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5),
            data={"claim_id": "CLM-2024-000999", "reason": "Pre-existing condition"},
            comments=[{"user": "admin@example.com", "text": "Insufficient documentation", "timestamp": (now - timedelta(days=5)).isoformat()}],
        ),
    ]

    if status:
        history = [h for h in history if h.status == status]

    return history[:limit]


@router.get("/{approval_id}", response_model=ApprovalItem)
async def get_approval_detail(approval_id: str):
    """Get details of a specific approval."""
    approvals = get_approvals()
    for a in approvals:
        if a.id == approval_id:
            return a
    raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")


@router.post("/{approval_id}/action")
async def process_approval_action(approval_id: str, action: ApprovalAction):
    """Process an approval action (approve, reject, escalate)."""
    global _approvals_cache
    approvals = get_approvals()

    for i, a in enumerate(approvals):
        if a.id == approval_id:
            if action.action == "approve":
                approvals[i].status = "approved"
            elif action.action == "reject":
                approvals[i].status = "rejected"
            elif action.action == "escalate":
                approvals[i].status = "escalated"
            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action.action}")

            approvals[i].updated_at = datetime.utcnow()
            if action.comment:
                approvals[i].comments.append({
                    "user": action.approver,
                    "text": action.comment,
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": action.action,
                })

            _approvals_cache = approvals
            return {
                "message": f"Approval {approval_id} {action.action}d successfully",
                "approval": approvals[i],
            }

    raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")


@router.post("/")
async def create_approval_request(data: dict):
    """Create a new approval request."""
    global _approvals_cache

    new_approval = ApprovalItem(
        id=f"apr-{uuid4().hex[:8]}",
        type=data.get("type", "config_change"),
        title=data.get("title", "New Approval Request"),
        description=data.get("description", ""),
        requester=data.get("requester", "System"),
        requester_email=data.get("requester_email", "system@example.com"),
        status="pending",
        priority=data.get("priority", "normal"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        data=data.get("data", {}),
        approvers=data.get("approvers", ["admin@example.com"]),
    )

    _approvals_cache = get_approvals()
    _approvals_cache.append(new_approval)

    return {"message": "Approval request created", "approval": new_approval}
