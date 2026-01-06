"""Audit logging service."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import Request

from ..config import settings
from ..models.audit import AuditLog, AuditAction, AuditCategory, AuditLogQuery, AuditStats
from ..models.users import User
from .cosmos_service import get_cosmos_client

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging."""

    COLLECTION = "audit_logs"

    # In-memory storage fallback
    _memory_store: List[dict] = []

    def __init__(self):
        self.cosmos = get_cosmos_client()

    async def log(
        self,
        action: AuditAction,
        category: AuditCategory,
        entity_type: str,
        entity_id: str,
        user: User,
        request: Optional[Request] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog(
            id=f"AUD-{uuid4().hex[:12]}",
            action=action,
            category=category,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user.id,
            user_name=user.name,
            user_role=user.role,
            user_ip=self._get_client_ip(request) if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_method=request.method if request else "N/A",
            request_path=str(request.url.path) if request else "N/A",
            old_value=old_value,
            new_value=new_value,
            change_summary=change_summary,
            success=success,
            error_message=error_message,
            response_status=200 if success else 500,
        )

        audit_dict = audit_log.model_dump()
        audit_dict["timestamp"] = audit_dict["timestamp"].isoformat()

        if settings.cosmos_db_configured:
            await self.cosmos.create_document(
                collection=self.COLLECTION,
                document=audit_dict,
                partition_key=audit_log.partition_key,
            )
        else:
            self._memory_store.append(audit_dict)

        logger.debug(f"Audit log: {action.value} on {entity_type}/{entity_id} by {user.name}")
        return audit_log

    async def log_config_change_request(
        self,
        request: Request,
        user: User,
        change_type: str,
        approval_id: str,
    ):
        """Log a configuration change request (before approval)."""
        await self.log(
            action=AuditAction.CONFIG_CHANGE,
            category=AuditCategory(change_type) if change_type in [e.value for e in AuditCategory] else AuditCategory.SYSTEM,
            entity_type="approval",
            entity_id=approval_id,
            user=user,
            request=request,
            change_summary=f"Config change request created: {approval_id}",
            success=True,
        )

    async def log_login(
        self,
        user: User,
        request: Request,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """Log a login attempt."""
        await self.log(
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            category=AuditCategory.AUTHENTICATION,
            entity_type="user",
            entity_id=user.id if user else "unknown",
            user=user,
            request=request,
            success=success,
            error_message=error_message,
        )

    async def query(
        self,
        query_params: AuditLogQuery,
    ) -> Tuple[List[AuditLog], int]:
        """Query audit logs with filters."""
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []

        if query_params.start_date:
            query += " AND c.timestamp >= @start_date"
            parameters.append({
                "name": "@start_date",
                "value": query_params.start_date.isoformat()
            })

        if query_params.end_date:
            query += " AND c.timestamp <= @end_date"
            parameters.append({
                "name": "@end_date",
                "value": query_params.end_date.isoformat()
            })

        if query_params.action:
            query += " AND c.action = @action"
            parameters.append({"name": "@action", "value": query_params.action.value})

        if query_params.category:
            query += " AND c.category = @category"
            parameters.append({"name": "@category", "value": query_params.category.value})

        if query_params.user_id:
            query += " AND c.user_id = @user_id"
            parameters.append({"name": "@user_id", "value": query_params.user_id})

        if query_params.entity_type:
            query += " AND c.entity_type = @entity_type"
            parameters.append({"name": "@entity_type", "value": query_params.entity_type})

        if query_params.entity_id:
            query += " AND c.entity_id = @entity_id"
            parameters.append({"name": "@entity_id", "value": query_params.entity_id})

        if query_params.success_only:
            query += " AND c.success = true"

        query += " ORDER BY c.timestamp DESC"

        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query=query,
                parameters=parameters,
            )
        else:
            # Filter memory store
            results = self._filter_memory_store(query_params)

        total = len(results)
        paginated = results[query_params.offset:query_params.offset + query_params.limit]

        logs = [AuditLog(**r) for r in paginated]
        return logs, total

    def _filter_memory_store(self, query_params: AuditLogQuery) -> List[dict]:
        """Filter in-memory audit logs."""
        results = self._memory_store.copy()

        if query_params.start_date:
            start_str = query_params.start_date.isoformat()
            results = [r for r in results if r.get("timestamp", "") >= start_str]

        if query_params.end_date:
            end_str = query_params.end_date.isoformat()
            results = [r for r in results if r.get("timestamp", "") <= end_str]

        if query_params.action:
            results = [r for r in results if r.get("action") == query_params.action.value]

        if query_params.category:
            results = [r for r in results if r.get("category") == query_params.category.value]

        if query_params.user_id:
            results = [r for r in results if r.get("user_id") == query_params.user_id]

        if query_params.entity_type:
            results = [r for r in results if r.get("entity_type") == query_params.entity_type]

        if query_params.entity_id:
            results = [r for r in results if r.get("entity_id") == query_params.entity_id]

        if query_params.success_only:
            results = [r for r in results if r.get("success") is True]

        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)

    async def get_stats(self) -> AuditStats:
        """Get audit statistics."""
        now = datetime.utcnow()
        today = now.date()
        week_ago = (now - timedelta(days=7)).isoformat()
        month_ago = (now - timedelta(days=30)).isoformat()

        if settings.cosmos_db_configured:
            all_logs = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query=f"SELECT * FROM c WHERE c.timestamp >= @month_ago",
                parameters=[{"name": "@month_ago", "value": month_ago}],
            )
        else:
            all_logs = [
                r for r in self._memory_store
                if r.get("timestamp", "") >= month_ago
            ]

        stats = AuditStats()
        stats.total_events = len(all_logs)

        for log in all_logs:
            timestamp = log.get("timestamp", "")
            action = log.get("action", "")
            category = log.get("category", "")
            user_id = log.get("user_id", "")
            success = log.get("success", True)

            # Count by time period
            if timestamp >= today.isoformat():
                stats.events_today += 1
            if timestamp >= week_ago:
                stats.events_this_week += 1
            stats.events_this_month += 1

            # Count by action
            stats.by_action[action] = stats.by_action.get(action, 0) + 1

            # Count by category
            stats.by_category[category] = stats.by_category.get(category, 0) + 1

            # Count by user
            stats.by_user[user_id] = stats.by_user.get(user_id, 0) + 1

            # Count failures
            if not success:
                stats.failed_events += 1

        return stats

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"


# Singleton
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get audit service singleton."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
