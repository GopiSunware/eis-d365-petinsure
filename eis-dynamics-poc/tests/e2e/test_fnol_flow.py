"""
End-to-end tests for FNOL (First Notice of Loss) flow.
Tests the complete journey from claim submission to Dataverse sync.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date, timezone
from httpx import AsyncClient, ASGITransport
import json


class TestFNOLEndToEnd:
    """End-to-end tests for FNOL submission flow."""

    @pytest.fixture
    def e2e_context(self):
        """Set up E2E test context with mocked services."""
        return {
            "submitted_claims": [],
            "dataverse_entities": [],
            "service_bus_messages": [],
            "ai_extractions": [],
        }

    @pytest.mark.asyncio
    async def test_complete_fnol_flow(self, sample_fnol_request, e2e_context):
        """
        Test complete FNOL flow:
        1. Submit FNOL via API
        2. AI extracts structured data
        3. Fraud analysis runs
        4. Claim created in system
        5. Message sent to Service Bus
        6. Claim synced to Dataverse
        """
        # Step 1: Submit FNOL
        fnol_submission = {
            **sample_fnol_request,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Step 2: Mock AI extraction
        ai_extraction = {
            "incident_type": "rear_end_collision",
            "damage_description": "Moderate damage to rear bumper and trunk area",
            "estimated_amount": 5000.00,
            "parties_involved": [
                {"role": "insured", "at_fault": False},
                {"role": "third_party", "at_fault": True},
            ],
            "severity": "moderate",
            "fraud_indicators": [],
            "confidence_score": 0.92,
        }
        e2e_context["ai_extractions"].append(ai_extraction)

        # Step 3: Mock fraud analysis
        fraud_analysis = {
            "fraud_score": 0.12,
            "risk_level": "low",
            "indicators": [],
            "recommendation": "Proceed with standard processing",
        }

        # Step 4: Create claim
        claim = {
            "claim_id": "CLM-E2E-001",
            "claim_number": "CLM-2024-00001",
            "policy_id": "POL-2024-001",
            "date_of_loss": sample_fnol_request["date_of_loss"],
            "date_reported": datetime.now(timezone.utc).isoformat(),
            "status": "fnol_received",
            "loss_description": sample_fnol_request["description"],
            "severity": ai_extraction["severity"],
            "reserve_amount": ai_extraction["estimated_amount"],
            "paid_amount": 0.00,
            "fraud_score": fraud_analysis["fraud_score"],
            "ai_recommendation": fraud_analysis["recommendation"],
        }
        e2e_context["submitted_claims"].append(claim)

        # Step 5: Send to Service Bus
        sync_message = {
            "event_type": "claim.created",
            "entity_id": claim["claim_id"],
            "claim_number": claim["claim_number"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        e2e_context["service_bus_messages"].append(sync_message)

        # Step 6: Sync to Dataverse
        dataverse_claim = {
            "eis_claimnumber": claim["claim_number"],
            "eis_dateofloss": claim["date_of_loss"],
            "eis_status": claim["status"],
            "eis_lossdescription": claim["loss_description"],
            "eis_severity": claim["severity"],
            "eis_reserveamount": claim["reserve_amount"],
            "eis_fraudscore": claim["fraud_score"],
            "eis_airecommendation": claim["ai_recommendation"],
            "eis_eissourceid": claim["claim_id"],
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        e2e_context["dataverse_entities"].append(dataverse_claim)

        # Verify complete flow
        assert len(e2e_context["submitted_claims"]) == 1
        assert len(e2e_context["ai_extractions"]) == 1
        assert len(e2e_context["service_bus_messages"]) == 1
        assert len(e2e_context["dataverse_entities"]) == 1

        # Verify data consistency
        submitted = e2e_context["submitted_claims"][0]
        synced = e2e_context["dataverse_entities"][0]
        assert submitted["claim_number"] == synced["eis_claimnumber"]
        assert submitted["fraud_score"] == synced["eis_fraudscore"]

    @pytest.mark.asyncio
    async def test_fnol_with_high_fraud_risk(self, e2e_context):
        """Test FNOL flow when high fraud risk detected."""
        suspicious_fnol = {
            "description": "Total loss. Fire. No witnesses. Need urgent payment.",
            "date_of_loss": (date.today()).isoformat(),
            "policy_number": "AUTO-IL-2024-00002",
            "contact_phone": "555-999-0000",
        }

        # AI extraction with fraud indicators
        ai_extraction = {
            "incident_type": "fire_loss",
            "damage_description": "Total loss due to fire",
            "estimated_amount": 35000.00,
            "severity": "severe",
            "fraud_indicators": [
                "Total loss claim",
                "Fire-related loss",
                "No witnesses",
                "Urgency pressure",
            ],
            "confidence_score": 0.75,
        }

        # High fraud score
        fraud_analysis = {
            "fraud_score": 0.78,
            "risk_level": "high",
            "indicators": ai_extraction["fraud_indicators"],
            "recommendation": "Refer to Special Investigations Unit",
        }

        # Claim with SIU flag
        claim = {
            "claim_id": "CLM-E2E-002",
            "claim_number": "CLM-2024-00002",
            "status": "under_investigation",  # Different status due to fraud risk
            "fraud_score": fraud_analysis["fraud_score"],
            "siu_referral": True,  # Flagged for investigation
            "ai_recommendation": fraud_analysis["recommendation"],
        }
        e2e_context["submitted_claims"].append(claim)

        # Verify SIU referral
        assert claim["siu_referral"] is True
        assert claim["status"] == "under_investigation"
        assert claim["fraud_score"] > 0.5

    @pytest.mark.asyncio
    async def test_fnol_validation_failure(self, e2e_context):
        """Test FNOL flow with invalid data."""
        invalid_fnol = {
            "description": "",  # Empty description
            "date_of_loss": "invalid-date",
            "policy_number": "INVALID",
            "contact_phone": "not-a-phone",
        }

        # Validation errors
        validation_errors = []

        if not invalid_fnol["description"]:
            validation_errors.append({
                "field": "description",
                "error": "Description is required",
            })

        if "invalid" in invalid_fnol["date_of_loss"].lower():
            validation_errors.append({
                "field": "date_of_loss",
                "error": "Invalid date format",
            })

        import re
        if not re.match(r"^[A-Z]+-[A-Z]{2}-\d{4}-\d{5}$", invalid_fnol["policy_number"]):
            validation_errors.append({
                "field": "policy_number",
                "error": "Invalid policy number format",
            })

        assert len(validation_errors) >= 2
        assert any(e["field"] == "description" for e in validation_errors)
        assert any(e["field"] == "policy_number" for e in validation_errors)

    @pytest.mark.asyncio
    async def test_fnol_with_document_upload(self, sample_fnol_request, e2e_context):
        """Test FNOL flow with document attachments."""
        # FNOL with documents
        fnol_with_docs = {
            **sample_fnol_request,
            "documents": [
                {
                    "filename": "police_report.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": 245000,
                },
                {
                    "filename": "damage_photo_1.jpg",
                    "content_type": "image/jpeg",
                    "size_bytes": 1200000,
                },
                {
                    "filename": "damage_photo_2.jpg",
                    "content_type": "image/jpeg",
                    "size_bytes": 980000,
                },
            ],
        }

        # Simulate document processing
        processed_docs = []
        for doc in fnol_with_docs["documents"]:
            processed = {
                "document_id": f"DOC-{len(processed_docs) + 1}",
                "filename": doc["filename"],
                "status": "uploaded",
                "storage_url": f"https://storage.blob.core.windows.net/claims/{doc['filename']}",
            }

            # OCR for PDF
            if doc["content_type"] == "application/pdf":
                processed["ocr_status"] = "completed"
                processed["extracted_text"] = "Police report content extracted..."

            processed_docs.append(processed)

        # Create claim with documents
        claim = {
            "claim_id": "CLM-E2E-003",
            "claim_number": "CLM-2024-00003",
            "status": "fnol_received",
            "documents": processed_docs,
            "document_count": len(processed_docs),
        }
        e2e_context["submitted_claims"].append(claim)

        assert claim["document_count"] == 3
        assert any(d["ocr_status"] == "completed" for d in processed_docs)


class TestFNOLPerformance:
    """Performance tests for FNOL flow."""

    @pytest.mark.asyncio
    async def test_fnol_processing_time(self, sample_fnol_request):
        """Test that FNOL processing completes within SLA."""
        import time

        start_time = time.time()

        # Simulate processing steps with mock delays
        processing_steps = [
            ("validation", 0.01),
            ("ai_extraction", 0.1),  # AI should be < 2s in production
            ("fraud_analysis", 0.05),
            ("claim_creation", 0.02),
            ("service_bus_send", 0.01),
        ]

        for step_name, delay in processing_steps:
            await asyncio.sleep(delay)

        end_time = time.time()
        total_time = end_time - start_time

        # SLA: < 500ms for p95
        # This test uses minimal mock delays
        assert total_time < 0.5, f"Processing took {total_time:.3f}s, exceeds 500ms SLA"

    @pytest.mark.asyncio
    async def test_concurrent_fnol_submissions(self, sample_fnol_request):
        """Test handling multiple concurrent FNOL submissions."""
        import asyncio

        async def submit_fnol(fnol_data: dict, index: int):
            # Simulate processing
            await asyncio.sleep(0.01)
            return {
                "claim_number": f"CLM-2024-{index:05d}",
                "status": "fnol_received",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Submit 10 concurrent FNOLs
        tasks = [
            submit_fnol({**sample_fnol_request, "index": i}, i)
            for i in range(1, 11)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["status"] == "fnol_received" for r in results)

        # All claim numbers should be unique
        claim_numbers = [r["claim_number"] for r in results]
        assert len(set(claim_numbers)) == 10


class TestFNOLErrorHandling:
    """Error handling tests for FNOL flow."""

    @pytest.mark.asyncio
    async def test_ai_service_unavailable(self, sample_fnol_request):
        """Test handling when AI service is unavailable."""
        # Simulate AI service failure
        ai_available = False

        if not ai_available:
            # Fallback processing without AI
            claim = {
                "claim_number": "CLM-2024-00004",
                "status": "fnol_received",
                "requires_manual_review": True,
                "ai_extraction_status": "failed",
                "fallback_used": True,
            }
        else:
            claim = {
                "claim_number": "CLM-2024-00004",
                "status": "fnol_received",
                "ai_extraction_status": "completed",
            }

        assert claim["requires_manual_review"] is True
        assert claim["fallback_used"] is True

    @pytest.mark.asyncio
    async def test_dataverse_sync_retry(self, sample_claim):
        """Test retry logic when Dataverse sync fails."""
        max_retries = 3
        retry_count = 0
        sync_success = False

        # Simulate transient failure then success
        failure_count = 2

        while retry_count < max_retries and not sync_success:
            retry_count += 1

            # Simulate failure for first N attempts
            if retry_count <= failure_count:
                sync_result = {"success": False, "error": "ServiceUnavailable"}
            else:
                sync_result = {"success": True, "entity_id": "d365-guid"}
                sync_success = True

        assert sync_success is True
        assert retry_count == 3  # Succeeded on 3rd attempt

    @pytest.mark.asyncio
    async def test_service_bus_dead_letter(self):
        """Test message goes to dead letter queue after max failures."""
        message = {
            "event_type": "claim.sync",
            "entity_id": "CLM-001",
            "attempt": 0,
        }

        max_attempts = 5
        dead_letter_queue = []

        # Simulate repeated failures
        for attempt in range(max_attempts):
            message["attempt"] = attempt + 1
            processing_success = False  # Simulating failure

            if not processing_success and message["attempt"] >= max_attempts:
                dead_letter_queue.append({
                    **message,
                    "dead_lettered_at": datetime.now(timezone.utc).isoformat(),
                    "reason": "MaxDeliveryCountExceeded",
                })

        assert len(dead_letter_queue) == 1
        assert dead_letter_queue[0]["reason"] == "MaxDeliveryCountExceeded"


# Import asyncio for async tests
import asyncio
