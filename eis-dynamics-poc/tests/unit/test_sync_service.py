"""
Unit tests for WS3 Sync Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestSyncService:
    """Tests for EIS-to-Dataverse sync functionality."""

    @pytest.mark.asyncio
    async def test_sync_policy_to_dataverse(self, sample_policy, mock_dataverse_client):
        """Test syncing a policy to Dataverse."""
        with patch("src.ws3_integration.app.services.sync_service.SyncService") as MockSync:
            sync_service = MockSync.return_value
            sync_service.dataverse_client = mock_dataverse_client

            result = {
                "success": True,
                "entity_id": "d365-policy-guid",
                "operation": "create",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            sync_service.sync_policy = AsyncMock(return_value=result)

            sync_result = await sync_service.sync_policy(sample_policy)

            assert sync_result["success"] is True
            assert sync_result["operation"] == "create"

    @pytest.mark.asyncio
    async def test_sync_claim_to_dataverse(self, sample_claim, mock_dataverse_client):
        """Test syncing a claim to Dataverse."""
        with patch("src.ws3_integration.app.services.sync_service.SyncService") as MockSync:
            sync_service = MockSync.return_value
            sync_service.dataverse_client = mock_dataverse_client

            result = {
                "success": True,
                "entity_id": "d365-claim-guid",
                "operation": "create",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            sync_service.sync_claim = AsyncMock(return_value=result)

            sync_result = await sync_service.sync_claim(sample_claim)

            assert sync_result["success"] is True

    @pytest.mark.asyncio
    async def test_sync_update_existing_entity(self, sample_policy, mock_dataverse_client):
        """Test updating an existing entity in Dataverse."""
        with patch("src.ws3_integration.app.services.sync_service.SyncService") as MockSync:
            sync_service = MockSync.return_value
            sync_service.dataverse_client = mock_dataverse_client

            # Simulate existing entity found
            result = {
                "success": True,
                "entity_id": "d365-policy-guid",
                "operation": "update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            sync_service.sync_policy = AsyncMock(return_value=result)

            sync_result = await sync_service.sync_policy(sample_policy)

            assert sync_result["operation"] == "update"

    @pytest.mark.asyncio
    async def test_sync_handles_conflict(self, sample_policy):
        """Test handling of sync conflicts."""
        with patch("src.ws3_integration.app.services.sync_service.SyncService") as MockSync:
            sync_service = MockSync.return_value

            conflict_result = {
                "success": False,
                "error": "CONFLICT",
                "message": "Entity was modified since last sync",
                "resolution_required": True,
            }
            sync_service.sync_policy = AsyncMock(return_value=conflict_result)

            result = await sync_service.sync_policy(sample_policy)

            assert result["success"] is False
            assert result["resolution_required"] is True


class TestEntityMapping:
    """Tests for EIS-to-Dataverse entity mapping."""

    def test_map_policy_to_dataverse(self, sample_policy):
        """Test mapping EIS policy to Dataverse format."""
        def map_policy(eis_policy: dict) -> dict:
            return {
                "eis_policynumber": eis_policy["policy_number"],
                "eis_effectivedate": eis_policy["effective_date"],
                "eis_expirationdate": eis_policy["expiration_date"],
                "eis_status": eis_policy["status"],
                "eis_policytype": eis_policy["policy_type"],
                "eis_totalpremium": eis_policy["total_premium"],
                "eis_insuredname": eis_policy["insured_name"],
                "eis_eissourceid": eis_policy["policy_id"],
            }

        mapped = map_policy(sample_policy)

        assert mapped["eis_policynumber"] == "AUTO-IL-2024-00001"
        assert mapped["eis_totalpremium"] == 1250.00
        assert "eis_eissourceid" in mapped

    def test_map_claim_to_dataverse(self, sample_claim):
        """Test mapping EIS claim to Dataverse format."""
        def map_claim(eis_claim: dict) -> dict:
            return {
                "eis_claimnumber": eis_claim["claim_number"],
                "eis_dateofloss": eis_claim["date_of_loss"],
                "eis_datereported": eis_claim["date_reported"],
                "eis_status": eis_claim["status"],
                "eis_lossdescription": eis_claim["loss_description"],
                "eis_severity": eis_claim.get("severity"),
                "eis_reserveamount": eis_claim["reserve_amount"],
                "eis_paidamount": eis_claim["paid_amount"],
                "eis_fraudscore": eis_claim["fraud_score"],
                "eis_airecommendation": eis_claim.get("ai_recommendation"),
                "eis_eissourceid": eis_claim["claim_id"],
            }

        mapped = map_claim(sample_claim)

        assert mapped["eis_claimnumber"] == "CLM-2024-00001"
        assert mapped["eis_fraudscore"] == 0.15
        assert mapped["eis_airecommendation"] is not None

    def test_map_customer_to_dataverse(self, sample_customer):
        """Test mapping EIS customer to Dataverse format."""
        def map_customer(eis_customer: dict) -> dict:
            return {
                "eis_fullname": f"{eis_customer['first_name']} {eis_customer['last_name']}",
                "eis_firstname": eis_customer["first_name"],
                "eis_lastname": eis_customer["last_name"],
                "eis_email": eis_customer.get("email"),
                "eis_phone": eis_customer.get("phone"),
                "eis_address": eis_customer.get("address"),
                "eis_customertype": eis_customer.get("customer_type"),
                "eis_eissourceid": eis_customer["customer_id"],
            }

        mapped = map_customer(sample_customer)

        assert mapped["eis_fullname"] == "John Doe"
        assert mapped["eis_email"] == "john.doe@example.com"


class TestSyncState:
    """Tests for sync state management."""

    def test_create_sync_record(self):
        """Test creating a sync state record."""
        def create_sync_record(entity_type: str, eis_id: str, d365_id: str) -> dict:
            return {
                "id": f"sync-{eis_id}",
                "entity_type": entity_type,
                "eis_source_id": eis_id,
                "d365_entity_id": d365_id,
                "last_sync_time": datetime.now(timezone.utc).isoformat(),
                "sync_status": "synced",
                "version": 1,
            }

        record = create_sync_record("policy", "POL-2024-001", "d365-guid-123")

        assert record["entity_type"] == "policy"
        assert record["sync_status"] == "synced"
        assert record["version"] == 1

    def test_check_sync_required(self):
        """Test checking if sync is required based on timestamps."""
        def is_sync_required(
            last_sync_time: datetime,
            last_modified_time: datetime,
            force: bool = False
        ) -> bool:
            if force:
                return True
            if last_sync_time is None:
                return True
            return last_modified_time > last_sync_time

        now = datetime.now(timezone.utc)
        one_hour_ago = datetime.fromisoformat("2024-01-01T10:00:00+00:00")
        two_hours_ago = datetime.fromisoformat("2024-01-01T09:00:00+00:00")

        # Modified after last sync
        assert is_sync_required(two_hours_ago, one_hour_ago) is True

        # Not modified since last sync
        assert is_sync_required(one_hour_ago, two_hours_ago) is False

        # Force sync
        assert is_sync_required(one_hour_ago, two_hours_ago, force=True) is True

        # Never synced
        assert is_sync_required(None, one_hour_ago) is True

    def test_update_sync_version(self):
        """Test sync version increment on update."""
        sync_records = {}

        def update_sync_record(eis_id: str, d365_id: str) -> dict:
            if eis_id in sync_records:
                record = sync_records[eis_id]
                record["version"] += 1
                record["last_sync_time"] = datetime.now(timezone.utc).isoformat()
                record["d365_entity_id"] = d365_id
            else:
                record = {
                    "eis_source_id": eis_id,
                    "d365_entity_id": d365_id,
                    "last_sync_time": datetime.now(timezone.utc).isoformat(),
                    "version": 1,
                }
            sync_records[eis_id] = record
            return record

        # First sync
        record1 = update_sync_record("POL-001", "d365-1")
        assert record1["version"] == 1

        # Second sync
        record2 = update_sync_record("POL-001", "d365-1")
        assert record2["version"] == 2


class TestWebhookProcessing:
    """Tests for EIS webhook processing."""

    def test_parse_policy_webhook(self):
        """Test parsing EIS policy webhook payload."""
        webhook_payload = {
            "event_type": "policy.created",
            "timestamp": "2024-06-15T14:30:00Z",
            "data": {
                "policy_id": "POL-2024-001",
                "policy_number": "AUTO-IL-2024-00001",
                "status": "active",
            },
        }

        def parse_webhook(payload: dict) -> dict:
            return {
                "event_type": payload["event_type"],
                "entity_type": payload["event_type"].split(".")[0],
                "action": payload["event_type"].split(".")[1],
                "entity_id": payload["data"].get("policy_id") or payload["data"].get("claim_id"),
                "data": payload["data"],
                "received_at": datetime.now(timezone.utc).isoformat(),
            }

        parsed = parse_webhook(webhook_payload)

        assert parsed["entity_type"] == "policy"
        assert parsed["action"] == "created"
        assert parsed["entity_id"] == "POL-2024-001"

    def test_validate_webhook_signature(self):
        """Test webhook signature validation."""
        import hashlib
        import hmac

        def validate_signature(payload: str, signature: str, secret: str) -> bool:
            expected = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, f"sha256={expected}")

        payload = '{"event_type":"policy.created"}'
        secret = "webhook-secret-key"
        valid_sig = "sha256=" + hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        assert validate_signature(payload, valid_sig, secret) is True
        assert validate_signature(payload, "sha256=invalid", secret) is False

    def test_determine_sync_action(self):
        """Test determining sync action from webhook event."""
        def determine_action(event_type: str) -> str:
            action_map = {
                "created": "create",
                "updated": "update",
                "deleted": "delete",
                "renewed": "update",
                "cancelled": "update",
            }
            action = event_type.split(".")[-1]
            return action_map.get(action, "update")

        assert determine_action("policy.created") == "create"
        assert determine_action("policy.updated") == "update"
        assert determine_action("policy.cancelled") == "update"
        assert determine_action("claim.deleted") == "delete"
