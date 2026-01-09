"""
Test Policies API Endpoints
Tests for policy creation and management
"""

import pytest


class TestPoliciesEndpoints:
    """Test suite for policies API endpoints."""

    def test_create_policy_success(self, client, demo_policy_data):
        """Test successful policy creation."""
        policy_data = demo_policy_data.copy()
        policy_data["customer_id"] = "DEMO-001"
        policy_data["pet_id"] = "PET-DEMO-001"

        response = client.post("/api/policies/", json=policy_data)
        assert response.status_code == 200
        data = response.json()

        assert "policy_id" in data
        assert data["policy_id"].startswith("POL-")
        assert "policy_number" in data
        assert data["customer_id"] == "DEMO-001"
        assert data["pet_id"] == "PET-DEMO-001"
        assert data["plan_name"] == policy_data["plan_name"]
        assert "monthly_premium" in data
        assert "annual_deductible" in data
        assert "coverage_limit" in data
        assert "effective_date" in data
        assert "expiration_date" in data
        assert "created_at" in data
        assert "message" in data

    def test_create_policy_invalid_plan(self, client, demo_policy_data):
        """Test policy creation with invalid plan name."""
        invalid_data = demo_policy_data.copy()
        invalid_data["customer_id"] = "DEMO-001"
        invalid_data["pet_id"] = "PET-DEMO-001"
        invalid_data["plan_name"] = "InvalidPlan"

        response = client.post("/api/policies/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_policies_by_customer(self, client):
        """Test getting policies for a customer."""
        response = client.get("/api/policies/customer/DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "policies" in data
        assert isinstance(data["policies"], list)

    def test_get_policies_by_pet(self, client):
        """Test getting policies for a pet."""
        response = client.get("/api/policies/pet/PET-DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "policies" in data
        assert isinstance(data["policies"], list)

    def test_validate_policy_for_pet(self, client):
        """Test validating a policy for a pet."""
        response = client.get("/api/policies/validate/POL-DEMO-001/PET-DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "valid" in data
        assert isinstance(data["valid"], bool)

    def test_get_policy_by_id(self, client):
        """Test getting a specific policy by ID."""
        response = client.get("/api/policies/POL-DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "policy" in data
        assert data["policy"]["policy_id"] == "POL-DEMO-001"

    def test_get_available_plans(self, client):
        """Test getting available insurance plans."""
        response = client.get("/api/policies/plans/available")
        assert response.status_code == 200
        data = response.json()

        assert "plans" in data
        assert isinstance(data["plans"], list)
        assert len(data["plans"]) > 0

        # Check plan structure
        plan = data["plans"][0]
        assert "name" in plan
        assert "monthly_premium" in plan
        assert "annual_deductible" in plan
        assert "coverage_limit" in plan
