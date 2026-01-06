"""Notification service for approval workflows."""

import logging
from typing import List, Optional

from ..config import settings
from ..models.approval import ApprovalRequest

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications."""

    def __init__(self):
        self._service_bus_client = None

    async def notify_approvers(self, approval: ApprovalRequest):
        """Notify approvers of a new pending approval request."""
        logger.info(f"Notifying approvers of new approval request: {approval.id}")

        # Get approvers
        from .user_service import get_user_service
        user_service = get_user_service()
        approvers = await user_service.get_approvers()

        if not approvers:
            logger.warning("No approvers found to notify")
            return

        # In a real implementation, this would:
        # 1. Send emails to approvers
        # 2. Send Slack/Teams notifications
        # 3. Push to Service Bus for async processing

        for approver in approvers:
            if approver.id != approval.requested_by:  # Don't notify the requester
                await self._send_notification(
                    recipient_email=approver.email,
                    subject=f"[Action Required] New Approval Request: {approval.change_summary}",
                    message=self._build_approval_request_message(approval, approver.name),
                )

    async def notify_approval_result(self, approval: ApprovalRequest, action: str):
        """Notify requester of approval result."""
        logger.info(f"Notifying requester of approval {action}: {approval.id}")

        # Get requester
        from .user_service import get_user_service
        user_service = get_user_service()
        requester = await user_service.get_user(approval.requested_by)

        if not requester:
            logger.warning(f"Requester not found: {approval.requested_by}")
            return

        subject_prefix = {
            "approve": "[Approved]",
            "reject": "[Rejected]",
            "cancel": "[Cancelled]",
        }.get(action, "[Update]")

        await self._send_notification(
            recipient_email=requester.email,
            subject=f"{subject_prefix} {approval.change_summary}",
            message=self._build_result_message(approval, action),
        )

    async def send_budget_alert(
        self,
        alert_name: str,
        provider: str,
        current_spend: float,
        budget_amount: float,
        percent_used: float,
        recipients: List[str],
        is_critical: bool = False,
    ):
        """Send budget alert notification."""
        severity = "CRITICAL" if is_critical else "WARNING"
        logger.info(f"Sending {severity} budget alert: {alert_name}")

        subject = f"[{severity}] Budget Alert: {alert_name}"
        message = f"""
Budget Alert: {alert_name}

Provider: {provider.upper()}
Current Spend: ${current_spend:,.2f}
Budget: ${budget_amount:,.2f}
Usage: {percent_used:.1f}%

{"⚠️ CRITICAL: Budget exceeded!" if is_critical else "⚡ Warning: Approaching budget limit."}

Please review your cloud spending in the Admin Portal.
"""

        for recipient in recipients:
            await self._send_notification(
                recipient_email=recipient,
                subject=subject,
                message=message,
            )

    async def _send_notification(
        self,
        recipient_email: str,
        subject: str,
        message: str,
    ):
        """
        Send notification to recipient.

        In production, this would integrate with:
        - SendGrid/SES for email
        - Slack/Teams webhooks
        - Azure Service Bus for async processing
        """
        logger.info(f"[NOTIFICATION] To: {recipient_email}")
        logger.info(f"[NOTIFICATION] Subject: {subject}")
        logger.debug(f"[NOTIFICATION] Message: {message[:200]}...")

        # TODO: Implement actual notification sending
        # For now, just log the notification

        if settings.SERVICE_BUS_CONNECTION_STRING:
            # Queue notification for async processing
            await self._queue_notification({
                "recipient": recipient_email,
                "subject": subject,
                "message": message,
            })

    async def _queue_notification(self, notification: dict):
        """Queue notification to Service Bus for async processing."""
        # TODO: Implement Service Bus integration
        pass

    def _build_approval_request_message(self, approval: ApprovalRequest, approver_name: str) -> str:
        """Build approval request notification message."""
        return f"""
Hello {approver_name},

A new configuration change request requires your approval:

Request ID: {approval.id}
Type: {approval.change_type}
Requested By: {approval.requested_by_name}
Summary: {approval.change_summary}

Reason for Change:
{approval.change_reason}

Expires: {approval.expires_at}

Please review and approve/reject this request in the Admin Portal.

---
EIS-D365 Admin Portal
"""

    def _build_result_message(self, approval: ApprovalRequest, action: str) -> str:
        """Build approval result notification message."""
        status_text = {
            "approve": "approved",
            "reject": "rejected",
            "cancel": "cancelled",
        }.get(action, action)

        message = f"""
Hello {approval.requested_by_name},

Your configuration change request has been {status_text}:

Request ID: {approval.id}
Type: {approval.change_type}
Summary: {approval.change_summary}
"""

        if action == "approve":
            message += f"""
Approved By: {approval.approved_by_name}
Approved At: {approval.approved_at}

The configuration change has been applied.
"""
        elif action == "reject":
            message += f"""
Rejected By: {approval.approved_by_name}
Reason: {approval.rejection_reason or "No reason provided"}

Please review the feedback and submit a new request if needed.
"""
        elif action == "cancel":
            message += """
The request has been cancelled and no changes were made.
"""

        message += """
---
EIS-D365 Admin Portal
"""
        return message


# Singleton
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
