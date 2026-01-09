"""
Test Health Check Endpoints
Tests for API health and status endpoints
"""

import pytest


def test_root_endpoint(client):
    """Test root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PetInsure360 API"
    assert data["version"] == "1.0.0"


def test_health_endpoint(client):
    """Test detailed health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "storage" in data
    assert "account" in data["storage"]
    assert "container" in data["storage"]
    assert data["websocket"] == "enabled"
