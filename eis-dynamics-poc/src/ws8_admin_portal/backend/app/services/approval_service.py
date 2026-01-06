"""Maker-Checker approval workflow service."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import uuid4

from ..config import settings
from ..models.approval import (
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalStatus,
    ApprovalAction,
    ConfigChangeType,
    ApprovalStats,
)
from ..models.users import User, UserRole
from .cosmos_service import get_cosmos_client
from .notification_service import get_notification_service

logger = logging.getLogger(__name__)


class ApprovalService:
    """Service for managing approval workflows."""

    COLLECTION = "config_pending_approvals"

    # In-memory storage fallback
    _memory_store: List[dict] = []

    def __init__(self):
        self.cosmos = get_cosmos_client()
        self.notification_service = get_notification_service()

    async def create_approval(
        self,
        request: ApprovalRequestCreate,
        current_value: dict,
        requester: User,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        approval_id = f"APR-{uuid4().hex[:8].upper()}"

        approval = ApprovalRequest(
            id=approval_id,
            change_type=request.change_type,
            entity_id=request.entity_id,
            current_value=current_value,
            proposed_value=request.proposed_value,
            change_summary=request.change_summary,
            change_reason=request.change_reason,
            requested_by=requester.id,
            requested_by_name=requester.name,
            requested_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=settings.APPROVAL_EXPIRY_HOURS),
            tags=request.tags,
        )

        approval_dict = approval.model_dump()
        approval_dict["requested_at"] = approval_dict["requested_at"].isoformat()
        approval_dict["expires_at"] = approval_dict["expires_at"].isoformat()

        # Store in Cosmos DB or memory
        if settings.cosmos_db_configured:
            await self.cosmos.create_document(
                collection=self.COLLECTION,
                document=approval_dict,
                partition_key=approval.change_type,
            )
        else:
            self._memory_store.append(approval_dict)

        # Send notification to approvers
        await self.notification_service.notify_approvers(approval)

        logger.info(f"Created approval request {approval_id} for {request.change_type}")
        return approval

    async def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        if settings.cosmos_db_configured:
            # Query across partitions since we don't know the change_type
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": approval_id}],
            )
            if results:
                return ApprovalRequest(**results[0])
        else:
            for doc in self._memory_store:
                if doc.get("id") == approval_id:
                    return ApprovalRequest(**doc)

        return None

    async def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        change_type: Optional[ConfigChangeType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ApprovalRequest], int, int]:
        """
        List approval requests with optional filters.
        Returns (approvals, total, pending_count).
        """
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []

        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status.value})

        if change_type:
            query += " AND c.change_type = @change_type"
            parameters.append({"name": "@change_type", "value": change_type.value})

        query += " ORDER BY c.requested_at DESC"

        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query=query,
                parameters=parameters,
            )
        else:
            # Filter memory store
            results = self._memory_store
            if status:
                results = [r for r in results if r.get("status") == status.value]
            if change_type:
                results = [r for r in results if r.get("change_type") == change_type.value]
            results = sorted(results, key=lambda x: x.get("requested_at", ""), reverse=True)

        # Count pending
        pending_count = len([r for r in results if r.get("status") == ApprovalStatus.PENDING.value])

        total = len(results)
        paginated = results[offset:offset + limit]

        approvals = [ApprovalRequest(**r) for r in paginated]
        return approvals, total, pending_count

    async def process_approval(
        self,
        approval_id: str,
        action: ApprovalAction,
        approver: User,
    ) -> ApprovalRequest:
        """Process an approval (approve/reject/cancel)."""
        approval = await self.get_approval(approval_id)

        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")

        # Check expiry
        if datetime.utcnow() > approval.expires_at:
            approval.status = ApprovalStatus.EXPIRED
            await self._update_approval(approval)
            raise ValueError(f"Approval {approval_id} has expired")

        # Validate action permissions
        if action.action in ["approve", "reject"]:
            # Cannot approve own request
            if approver.id == approval.requested_by:
                raise ValueError("Cannot approve your own request")

            # Must have approver role
            if approver.role not in [UserRole.ADMIN.value, UserRole.APPROVER.value, "admin", "approver"]:
                raise ValueError("User does not have approval permission")

        elif action.action == "cancel":
            # Only requester or admin can cancel
            if approver.id != approval.requested_by and approver.role not in [UserRole.ADMIN.value, "admin"]:
                raise ValueError("Only requester or admin can cancel")

        # Process the action
        now = datetime.utcnow()

        if action.action == "approve":
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = approver.id
            approval.approved_by_name = approver.name
            approval.approved_at = now
            approval.approval_comment = action.comment

            # Apply the configuration change
            await self._apply_config_change(approval)

        elif action.action == "reject":
            approval.status = ApprovalStatus.REJECTED
            approval.approved_by = approver.id
            approval.approved_by_name = approver.name
            approval.approved_at = now
            approval.rejection_reason = action.rejection_reason or action.comment

        elif action.action == "cancel":
            approval.status = ApprovalStatus.CANCELLED

        # Update in storage
        await self._update_approval(approval)

        # Send notification
        await self.notification_service.notify_approval_result(approval, action.action)

        logger.info(f"Approval {approval_id} {action.action}ed by {approver.name}")
        return approval

    async def _update_approval(self, approval: ApprovalRequest):
        """Update approval in storage."""
        approval_dict = approval.model_dump()

        # Convert datetimes to ISO strings
        for key in ["requested_at", "expires_at", "approved_at"]:
            if approval_dict.get(key) and isinstance(approval_dict[key], datetime):
                approval_dict[key] = approval_dict[key].isoformat()

        if settings.cosmos_db_configured:
            await self.cosmos.update_document(
                collection=self.COLLECTION,
                document_id=approval.id,
                document=approval_dict,
                partition_key=approval.change_type,
            )
        else:
            # Update in memory store
            for i, doc in enumerate(self._memory_store):
                if doc.get("id") == approval.id:
                    self._memory_store[i] = approval_dict
                    break

    async def _apply_config_change(self, approval: ApprovalRequest):
        """Apply the approved configuration change."""
        from .config_service import get_config_service

        config_service = get_config_service()

        change_type = ConfigChangeType(approval.change_type) if isinstance(approval.change_type, str) else approval.change_type

        if change_type == ConfigChangeType.AI_CONFIG:
            await config_service.update_ai_config_direct(
                approval.proposed_value,
                approved_by=approval.approved_by,
                approval_id=approval.id,
            )
        elif change_type == ConfigChangeType.CLAIMS_RULES:
            await config_service.update_claims_rules_direct(
                approval.entity_id,
                approval.proposed_value,
                approved_by=approval.approved_by,
                approval_id=approval.id,
            )
        elif change_type == ConfigChangeType.RATING_CONFIG:
            await config_service.update_rating_config_direct(
                approval.entity_id,
                approval.proposed_value,
                approved_by=approval.approved_by,
                approval_id=approval.id,
            )
        elif change_type == ConfigChangeType.POLICY_CONFIG:
            await config_service.update_policy_config_direct(
                approval.entity_id,
                approval.proposed_value,
                approved_by=approval.approved_by,
                approval_id=approval.id,
            )

        logger.info(f"Applied config change from approval {approval.id}")

    async def expire_old_approvals(self) -> int:
        """Mark expired approvals. Returns count of expired."""
        now = datetime.utcnow()
        expired_count = 0

        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query="SELECT * FROM c WHERE c.status = 'pending'",
            )
        else:
            results = [r for r in self._memory_store if r.get("status") == "pending"]

        for doc in results:
            expires_at = doc.get("expires_at")
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if now > expires_at:
                    doc["status"] = ApprovalStatus.EXPIRED.value
                    if settings.cosmos_db_configured:
                        await self.cosmos.update_document(
                            collection=self.COLLECTION,
                            document_id=doc["id"],
                            document=doc,
                            partition_key=doc["change_type"],
                        )
                    expired_count += 1
                    logger.info(f"Expired approval {doc['id']}")

        return expired_count

    async def get_stats(self) -> ApprovalStats:
        """Get approval statistics."""
        if settings.cosmos_db_configured:
            all_approvals = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query="SELECT * FROM c",
            )
        else:
            all_approvals = self._memory_store

        today = datetime.utcnow().date()
        stats = ApprovalStats()

        for approval in all_approvals:
            status = approval.get("status")
            approved_at = approval.get("approved_at")

            if status == "pending":
                stats.pending += 1
            elif approved_at:
                if isinstance(approved_at, str):
                    approved_at = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
                if approved_at.date() == today:
                    if status == "approved":
                        stats.approved_today += 1
                    elif status == "rejected":
                        stats.rejected_today += 1
                    elif status == "expired":
                        stats.expired_today += 1

        return stats


# Singleton
_approval_service: Optional[ApprovalService] = None


def get_approval_service() -> ApprovalService:
    """Get approval service singleton."""
    global _approval_service
    if _approval_service is None:
        _approval_service = ApprovalService()
    return _approval_service
