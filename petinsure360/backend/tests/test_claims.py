"""
Test Claims API Endpoints
Tests for claim submission and processing
"""

import pytest


class TestClaimsEndpoints:
    """Test suite for claims API endpoints."""

    def test_create_claim_success(self, client, demo_claim_data):
        """Test successful claim creation."""
        claim_data = demo_claim_data.copy()
        claim_data["customer_id"] = "DEMO-001"
        claim_data["pet_id"] = "PET-DEMO-001"
        claim_data["policy_id"] = "POL-DEMO-001"
        claim_data["provider_id"] = "PROV-001"

        response = client.post("/api/claims/", json=claim_data)
        assert response.status_code == 200
        data = response.json()

        assert "claim_id" in data
        assert data["claim_id"].startswith("CLM-")
        assert "claim_number" in data
        assert data["policy_id"] == "POL-DEMO-001"
        assert data["pet_id"] == "PET-DEMO-001"
        assert data["customer_id"] == "DEMO-001"
        assert data["claim_type"] == claim_data["claim_type"]
        assert data["claim_amount"] == claim_data["claim_amount"]
        assert "status" in data
        assert "submitted_date" in data
        assert "message" in data

    def test_create_claim_invalid_type(self, client, demo_claim_data):
        """Test claim creation with invalid claim type."""
        invalid_data = demo_claim_data.copy()
        invalid_data["customer_id"] = "DEMO-001"
        invalid_data["pet_id"] = "PET-DEMO-001"
        invalid_data["policy_id"] = "POL-DEMO-001"
        invalid_data["claim_type"] = "InvalidType"

        response = client.post("/api/claims/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_claim_invalid_amount(self, client, demo_claim_data):
        """Test claim creation with invalid amount."""
        invalid_data = demo_claim_data.copy()
        invalid_data["customer_id"] = "DEMO-001"
        invalid_data["pet_id"] = "PET-DEMO-001"
        invalid_data["policy_id"] = "POL-DEMO-001"
        invalid_data["claim_amount"] = -100  # Must be > 0

        response = client.post("/api/claims/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_claim_status(self, client):
        """Test getting claim status."""
        # First create a claim
        claim_data = {
            "customer_id": "DEMO-001",
            "pet_id": "PET-DEMO-001",
            "policy_id": "POL-DEMO-001",
            "provider_id": "PROV-001",
            "claim_type": "Illness",
            "claim_category": "Digestive",
            "service_date": "2024-12-20",
            "claim_amount": 450.00,
            "is_emergency": False
        }

        create_response = client.post("/api/claims/", json=claim_data)
        assert create_response.status_code == 200
        claim_id = create_response.json()["claim_id"]

        # Get claim status
        response = client.get(f"/api/claims/{claim_id}/status")
        assert response.status_code == 200
        data = response.json()

        assert data["claim_id"] == claim_id
        assert "claim_number" in data
        assert "status" in data
        assert "claim_amount" in data
        assert "updated_at" in data

    def test_get_claims_by_customer(self, client):
        """Test getting all claims for a customer."""
        response = client.get("/api/claims/customer/DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "claims" in data
        assert isinstance(data["claims"], list)

    def test_simulate_claim_processing(self, client):
        """Test simulating claim processing."""
        # First create a claim
        claim_data = {
            "customer_id": "DEMO-001",
            "pet_id": "PET-DEMO-001",
            "policy_id": "POL-DEMO-001",
            "claim_type": "Illness",
            "claim_category": "Digestive",
            "service_date": "2024-12-20",
            "claim_amount": 450.00,
            "is_emergency": False
        }

        create_response = client.post("/api/claims/", json=claim_data)
        assert create_response.status_code == 200
        claim_id = create_response.json()["claim_id"]

        # Simulate processing
        response = client.post(f"/api/claims/{claim_id}/simulate-processing")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["Approved", "Denied", "Under Review"]
