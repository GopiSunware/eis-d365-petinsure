"""
Test Pets API Endpoints
Tests for pet registration and management
"""

import pytest


class TestPetsEndpoints:
    """Test suite for pets API endpoints."""

    def test_create_pet_success(self, client, demo_pet_data):
        """Test successful pet creation."""
        pet_data = demo_pet_data.copy()
        pet_data["customer_id"] = "DEMO-001"  # Use existing demo customer

        response = client.post("/api/pets/", json=pet_data)
        assert response.status_code == 200
        data = response.json()

        assert "pet_id" in data
        assert data["pet_id"].startswith("PET-")
        assert data["customer_id"] == "DEMO-001"
        assert data["pet_name"] == pet_data["pet_name"]
        assert data["species"] == pet_data["species"]
        assert data["breed"] == pet_data["breed"]
        assert "created_at" in data
        assert "message" in data

    def test_create_pet_invalid_species(self, client, demo_pet_data):
        """Test pet creation with invalid species."""
        invalid_data = demo_pet_data.copy()
        invalid_data["customer_id"] = "DEMO-001"
        invalid_data["species"] = "Bird"  # Only Dog/Cat allowed

        response = client.post("/api/pets/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_pet_invalid_gender(self, client, demo_pet_data):
        """Test pet creation with invalid gender."""
        invalid_data = demo_pet_data.copy()
        invalid_data["customer_id"] = "DEMO-001"
        invalid_data["gender"] = "Unknown"  # Only Male/Female allowed

        response = client.post("/api/pets/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_pet_invalid_weight(self, client, demo_pet_data):
        """Test pet creation with invalid weight."""
        invalid_data = demo_pet_data.copy()
        invalid_data["customer_id"] = "DEMO-001"
        invalid_data["weight_lbs"] = 0  # Must be > 0

        response = client.post("/api/pets/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_get_pets_by_customer(self, client):
        """Test getting pets for a customer."""
        response = client.get("/api/pets/customer/DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "pets" in data
        assert isinstance(data["pets"], list)
        # Demo user should have at least the seeded pets
        if len(data["pets"]) > 0:
            assert "pet_id" in data["pets"][0]
            assert "customer_id" in data["pets"][0]

    def test_get_pet_by_id(self, client):
        """Test getting a specific pet by ID."""
        response = client.get("/api/pets/PET-DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "pet" in data
        assert data["pet"]["pet_id"] == "PET-DEMO-001"

    def test_get_pet_not_found(self, client):
        """Test getting non-existent pet."""
        response = client.get("/api/pets/NONEXISTENT-PET-ID")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
