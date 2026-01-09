"""
Test Pipeline API Endpoints
Tests for data pipeline and processing endpoints
"""

import pytest


class TestPipelineEndpoints:
    """Test suite for pipeline API endpoints."""

    def test_get_pipeline_status(self, client):
        """Test getting pipeline status."""
        response = client.get("/api/pipeline/status")
        assert response.status_code == 200
        data = response.json()

        assert "bronze_layer" in data
        assert "silver_layer" in data
        assert "gold_layer" in data
        assert isinstance(data["bronze_layer"]["count"], int)

    def test_get_pipeline_flow(self, client):
        """Test getting pipeline flow visualization data."""
        response = client.get("/api/pipeline/flow")
        assert response.status_code == 200
        data = response.json()

        assert "nodes" in data or "message" in data

    def test_get_pending_claims(self, client):
        """Test getting pending claims in pipeline."""
        response = client.get("/api/pipeline/pending")
        assert response.status_code == 200
        data = response.json()

        assert "pending_claims" in data
        assert isinstance(data["pending_claims"], list)

    def test_submit_claim_to_pipeline(self, client):
        """Test submitting a claim to the pipeline."""
        claim_data = {
            "customer_id": "DEMO-001",
            "pet_id": "PET-DEMO-001",
            "policy_id": "POL-DEMO-001",
            "claim_type": "Illness",
            "claim_category": "Digestive",
            "service_date": "2024-12-20",
            "claim_amount": 450.00,
            "diagnosis_code": "GI001",
            "is_emergency": False
        }

        response = client.post("/api/pipeline/submit-claim", json=claim_data)
        assert response.status_code == 200
        data = response.json()

        assert "claim_id" in data
        assert "layer" in data
        assert data["layer"] == "bronze"

    def test_get_pipeline_metrics(self, client):
        """Test getting pipeline metrics."""
        response = client.get("/api/pipeline/metrics")
        assert response.status_code == 200
        data = response.json()

        assert "total_claims_processed" in data
        assert isinstance(data["total_claims_processed"], int)

    def test_refresh_pipeline(self, client):
        """Test refreshing pipeline data."""
        response = client.post("/api/pipeline/refresh")
        assert response.status_code == 200
        data = response.json()

        assert "message" in data

    def test_get_fraud_scenarios(self, client):
        """Test getting fraud detection scenarios."""
        response = client.get("/api/pipeline/fraud-scenarios")
        assert response.status_code == 200
        data = response.json()

        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)
