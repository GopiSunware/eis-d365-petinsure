"""
Test Customer API Endpoints
Tests for customer registration, lookup, and management
"""

import pytest


class TestCustomerEndpoints:
    """Test suite for customer API endpoints."""

    def test_create_customer_success(self, client, demo_customer_data):
        """Test successful customer creation."""
        response = client.post("/api/customers/", json=demo_customer_data)
        assert response.status_code == 200
        data = response.json()

        assert "customer_id" in data
        assert data["customer_id"].startswith("CUST-")
        assert data["first_name"] == demo_customer_data["first_name"]
        assert data["last_name"] == demo_customer_data["last_name"]
        assert data["email"] == demo_customer_data["email"]
        assert data["phone"] == demo_customer_data["phone"]
        assert data["city"] == demo_customer_data["city"]
        assert data["state"] == demo_customer_data["state"]
        assert "created_at" in data
        assert "message" in data

    def test_create_customer_invalid_email(self, client, demo_customer_data):
        """Test customer creation with invalid email."""
        invalid_data = demo_customer_data.copy()
        invalid_data["email"] = "invalid-email"

        response = client.post("/api/customers/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_customer_invalid_phone(self, client, demo_customer_data):
        """Test customer creation with invalid phone number."""
        invalid_data = demo_customer_data.copy()
        invalid_data["phone"] = "123"  # Too short

        response = client.post("/api/customers/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_customer_invalid_state(self, client, demo_customer_data):
        """Test customer creation with invalid state code."""
        invalid_data = demo_customer_data.copy()
        invalid_data["state"] = "TEXAS"  # Should be 2 chars

        response = client.post("/api/customers/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_customer_invalid_zip(self, client, demo_customer_data):
        """Test customer creation with invalid ZIP code."""
        invalid_data = demo_customer_data.copy()
        invalid_data["zip_code"] = "123"  # Should be 5 digits

        response = client.post("/api/customers/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_lookup_customer_by_email_demo_user(self, client):
        """Test customer lookup by email for demo users."""
        response = client.get("/api/customers/lookup?email=demo@demologin.com")
        assert response.status_code == 200
        data = response.json()

        assert "customer" in data
        assert data["customer"]["customer_id"] == "DEMO-001"
        assert data["customer"]["email"] == "demo@demologin.com"
        assert "pets" in data["customer"]
        assert "policies" in data["customer"]
        assert data["message"] == "Customer found (demo user)"

    def test_lookup_customer_not_found(self, client):
        """Test customer lookup with non-existent email."""
        response = client.get("/api/customers/lookup?email=nonexistent@example.com")
        assert response.status_code == 404
        assert "No account found" in response.json()["detail"]

    def test_get_customer_by_id_demo_user(self, client):
        """Test get customer by ID for demo users."""
        response = client.get("/api/customers/DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "customer" in data
        assert data["customer"]["customer_id"] == "DEMO-001"

    def test_get_customer_not_found(self, client):
        """Test get customer with non-existent ID."""
        response = client.get("/api/customers/NONEXISTENT-ID")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_seed_demo_data(self, client):
        """Test seeding demo data."""
        response = client.post("/api/customers/seed-demo")
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "created" in data
        assert "demo_users" in data
        assert len(data["demo_users"]) == 3
