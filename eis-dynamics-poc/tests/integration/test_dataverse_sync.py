"""
Integration tests for Dataverse synchronization.
Tests the full sync flow from EIS to Dataverse.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import asyncio


class TestDataverseSyncIntegration:
    """Integration tests for EIS-to-Dataverse sync flow."""

    @pytest.fixture
    def mock_dataverse_environment(self):
        """Set up mock Dataverse environment."""
        dataverse_data = {
            "eis_policies": {},
            "eis_claims": {},
            "eis_insuredparties": {},
        }

        async def mock_create(entity_name: str, data: dict):
            entity_id = f"d365-{len(dataverse_data[entity_name]) + 1}"
            dataverse_data[entity_name][entity_id] = {**data, "id": entity_id}
            return {"id": entity_id}

        async def mock_update(entity_name: str, entity_id: str, data: dict):
            if entity_id in dataverse_data[entity_name]:
                dataverse_data[entity_name][entity_id].update(data)
                return True
            return False

        async def mock_get(entity_name: str, entity_id: str):
            return dataverse_data[entity_name].get(entity_id)

        async def mock_query(entity_name: str, filter_query: str):
            # Simple mock query - returns all entities
            return list(dataverse_data[entity_name].values())

        return {
            "data": dataverse_data,
            "create": mock_create,
            "update": mock_update,
            "get": mock_get,
            "query": mock_query,
        }

    @pytest.mark.asyncio
    async def test_full_policy_sync_flow(self, sample_policy, mock_dataverse_environment):
        """Test complete policy sync from EIS to Dataverse."""
        # Step 1: Receive EIS policy data
        eis_policy = sample_policy.copy()

        # Step 2: Map to Dataverse format
        dataverse_policy = {
            "eis_policynumber": eis_policy["policy_number"],
            "eis_effectivedate": eis_policy["effective_date"],
            "eis_expirationdate": eis_policy["expiration_date"],
            "eis_status": eis_policy["status"],
            "eis_policytype": eis_policy["policy_type"],
            "eis_totalpremium": eis_policy["total_premium"],
            "eis_insuredname": eis_policy["insured_name"],
            "eis_eissourceid": eis_policy["policy_id"],
        }

        # Step 3: Create in Dataverse
        result = await mock_dataverse_environment["create"]("eis_policies", dataverse_policy)

        assert "id" in result
        assert result["id"].startswith("d365-")

        # Step 4: Verify data persisted
        stored = await mock_dataverse_environment["get"]("eis_policies", result["id"])
        assert stored["eis_policynumber"] == "AUTO-IL-2024-00001"
        assert stored["eis_totalpremium"] == 1250.00

    @pytest.mark.asyncio
    async def test_policy_update_sync(self, sample_policy, mock_dataverse_environment):
        """Test updating an existing policy in Dataverse."""
        # Create initial policy
        initial_data = {
            "eis_policynumber": sample_policy["policy_number"],
            "eis_status": "active",
            "eis_totalpremium": 1250.00,
            "eis_eissourceid": sample_policy["policy_id"],
        }
        result = await mock_dataverse_environment["create"]("eis_policies", initial_data)
        entity_id = result["id"]

        # Update policy (e.g., premium change)
        updated_data = {
            "eis_totalpremium": 1350.00,
            "eis_status": "active",
        }
        update_success = await mock_dataverse_environment["update"](
            "eis_policies", entity_id, updated_data
        )

        assert update_success is True

        # Verify update
        stored = await mock_dataverse_environment["get"]("eis_policies", entity_id)
        assert stored["eis_totalpremium"] == 1350.00

    @pytest.mark.asyncio
    async def test_claim_sync_with_policy_lookup(
        self, sample_claim, sample_policy, mock_dataverse_environment
    ):
        """Test syncing a claim with policy relationship."""
        # First sync the policy
        policy_data = {
            "eis_policynumber": sample_policy["policy_number"],
            "eis_eissourceid": sample_policy["policy_id"],
        }
        policy_result = await mock_dataverse_environment["create"]("eis_policies", policy_data)

        # Now sync the claim with policy reference
        claim_data = {
            "eis_claimnumber": sample_claim["claim_number"],
            "eis_dateofloss": sample_claim["date_of_loss"],
            "eis_status": sample_claim["status"],
            "eis_reserveamount": sample_claim["reserve_amount"],
            "eis_policyid": policy_result["id"],  # Lookup reference
            "eis_eissourceid": sample_claim["claim_id"],
        }
        claim_result = await mock_dataverse_environment["create"]("eis_claims", claim_data)

        assert claim_result["id"] is not None

        # Verify claim references policy
        stored_claim = await mock_dataverse_environment["get"]("eis_claims", claim_result["id"])
        assert stored_claim["eis_policyid"] == policy_result["id"]

    @pytest.mark.asyncio
    async def test_batch_sync_multiple_policies(self, mock_dataverse_environment):
        """Test syncing multiple policies in batch."""
        policies = [
            {"policy_id": f"POL-{i}", "policy_number": f"AUTO-IL-2024-{i:05d}", "premium": 1000 + i * 100}
            for i in range(1, 6)
        ]

        results = []
        for policy in policies:
            data = {
                "eis_policynumber": policy["policy_number"],
                "eis_totalpremium": policy["premium"],
                "eis_eissourceid": policy["policy_id"],
            }
            result = await mock_dataverse_environment["create"]("eis_policies", data)
            results.append(result)

        assert len(results) == 5
        assert all("id" in r for r in results)

        # Verify all stored
        all_policies = await mock_dataverse_environment["query"]("eis_policies", "")
        assert len(all_policies) == 5

    @pytest.mark.asyncio
    async def test_sync_idempotency(self, sample_policy, mock_dataverse_environment):
        """Test that syncing the same entity twice is idempotent."""
        policy_data = {
            "eis_policynumber": sample_policy["policy_number"],
            "eis_eissourceid": sample_policy["policy_id"],
            "eis_totalpremium": 1250.00,
        }

        # First sync - creates
        result1 = await mock_dataverse_environment["create"]("eis_policies", policy_data)

        # Simulate second sync - should find existing and update
        existing = await mock_dataverse_environment["query"]("eis_policies", "")
        matching = [e for e in existing if e.get("eis_eissourceid") == sample_policy["policy_id"]]

        if matching:
            # Update existing instead of creating duplicate
            await mock_dataverse_environment["update"](
                "eis_policies", matching[0]["id"], policy_data
            )
            result2_id = matching[0]["id"]
        else:
            result2 = await mock_dataverse_environment["create"]("eis_policies", policy_data)
            result2_id = result2["id"]

        # Should have same ID (no duplicate created)
        assert result1["id"] == result2_id

        # Only one entity should exist
        all_policies = await mock_dataverse_environment["query"]("eis_policies", "")
        matching = [e for e in all_policies if e.get("eis_eissourceid") == sample_policy["policy_id"]]
        assert len(matching) == 1


class TestServiceBusIntegration:
    """Integration tests for Azure Service Bus messaging."""

    @pytest.fixture
    def mock_service_bus(self):
        """Set up mock Service Bus environment."""
        queues = {
            "policy-sync-queue": [],
            "claim-sync-queue": [],
        }
        topics = {
            "policy-events": [],
            "claim-events": [],
        }

        def send_to_queue(queue_name: str, message: dict):
            if queue_name in queues:
                queues[queue_name].append({
                    "body": message,
                    "enqueued_at": datetime.now(timezone.utc).isoformat(),
                })
                return True
            return False

        def receive_from_queue(queue_name: str, max_messages: int = 1):
            if queue_name in queues and queues[queue_name]:
                return [queues[queue_name].pop(0) for _ in range(min(max_messages, len(queues[queue_name])))]
            return []

        def publish_to_topic(topic_name: str, message: dict):
            if topic_name in topics:
                topics[topic_name].append({
                    "body": message,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                })
                return True
            return False

        return {
            "queues": queues,
            "topics": topics,
            "send": send_to_queue,
            "receive": receive_from_queue,
            "publish": publish_to_topic,
        }

    def test_send_policy_sync_message(self, sample_policy, mock_service_bus):
        """Test sending a policy sync message to queue."""
        message = {
            "event_type": "policy.sync_requested",
            "entity_id": sample_policy["policy_id"],
            "data": sample_policy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        result = mock_service_bus["send"]("policy-sync-queue", message)

        assert result is True
        assert len(mock_service_bus["queues"]["policy-sync-queue"]) == 1

    def test_receive_and_process_sync_message(self, sample_policy, mock_service_bus):
        """Test receiving and processing a sync message."""
        # Send message
        message = {
            "event_type": "policy.sync_requested",
            "entity_id": sample_policy["policy_id"],
            "data": sample_policy,
        }
        mock_service_bus["send"]("policy-sync-queue", message)

        # Receive message
        messages = mock_service_bus["receive"]("policy-sync-queue")

        assert len(messages) == 1
        received = messages[0]["body"]
        assert received["entity_id"] == sample_policy["policy_id"]
        assert received["data"]["policy_number"] == sample_policy["policy_number"]

        # Queue should be empty after receive
        assert len(mock_service_bus["queues"]["policy-sync-queue"]) == 0

    def test_publish_policy_event(self, sample_policy, mock_service_bus):
        """Test publishing a policy event to topic."""
        event = {
            "event_type": "policy.created",
            "entity_id": sample_policy["policy_id"],
            "policy_number": sample_policy["policy_number"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        result = mock_service_bus["publish"]("policy-events", event)

        assert result is True
        assert len(mock_service_bus["topics"]["policy-events"]) == 1

    def test_message_ordering(self, mock_service_bus):
        """Test that messages are processed in order."""
        messages = [
            {"event_type": "policy.created", "sequence": 1},
            {"event_type": "policy.updated", "sequence": 2},
            {"event_type": "policy.updated", "sequence": 3},
        ]

        for msg in messages:
            mock_service_bus["send"]("policy-sync-queue", msg)

        received = []
        while mock_service_bus["queues"]["policy-sync-queue"]:
            batch = mock_service_bus["receive"]("policy-sync-queue")
            received.extend([m["body"]["sequence"] for m in batch])

        assert received == [1, 2, 3]


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client for testing."""
        data_store = {
            "policies": {},
            "claims": {},
            "customers": {},
        }

        class MockAPIClient:
            async def get_policies(self):
                return list(data_store["policies"].values())

            async def get_policy(self, policy_id: str):
                return data_store["policies"].get(policy_id)

            async def create_policy(self, policy_data: dict):
                policy_id = policy_data.get("policy_id", f"POL-{len(data_store['policies']) + 1}")
                data_store["policies"][policy_id] = {**policy_data, "policy_id": policy_id}
                return data_store["policies"][policy_id]

            async def get_claims(self):
                return list(data_store["claims"].values())

            async def get_claim(self, claim_number: str):
                return data_store["claims"].get(claim_number)

            async def submit_fnol(self, fnol_data: dict):
                claim_number = f"CLM-2024-{len(data_store['claims']) + 1:05d}"
                claim = {
                    "claim_number": claim_number,
                    "status": "fnol_received",
                    **fnol_data,
                }
                data_store["claims"][claim_number] = claim
                return claim

        return MockAPIClient()

    @pytest.mark.asyncio
    async def test_policy_crud_flow(self, mock_api_client, sample_policy):
        """Test full policy CRUD through API."""
        # Create
        created = await mock_api_client.create_policy(sample_policy)
        assert created["policy_id"] is not None

        # Read
        fetched = await mock_api_client.get_policy(created["policy_id"])
        assert fetched["policy_number"] == sample_policy["policy_number"]

        # List
        all_policies = await mock_api_client.get_policies()
        assert len(all_policies) >= 1

    @pytest.mark.asyncio
    async def test_fnol_to_claim_flow(self, mock_api_client, sample_fnol_request):
        """Test FNOL submission creates claim."""
        # Submit FNOL
        claim = await mock_api_client.submit_fnol(sample_fnol_request)

        assert claim["claim_number"].startswith("CLM-")
        assert claim["status"] == "fnol_received"

        # Verify claim retrievable
        fetched = await mock_api_client.get_claim(claim["claim_number"])
        assert fetched is not None
        assert fetched["description"] == sample_fnol_request["description"]
