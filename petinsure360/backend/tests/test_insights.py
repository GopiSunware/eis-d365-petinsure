"""
Test Insights API Endpoints
Tests for BI insights and analytics endpoints
"""

import pytest


class TestInsightsEndpoints:
    """Test suite for insights API endpoints."""

    def test_get_summary(self, client):
        """Test getting summary statistics."""
        response = client.get("/api/insights/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_customers" in data
        assert "total_pets" in data
        assert "total_policies" in data
        assert "total_claims" in data
        assert isinstance(data["total_customers"], int)
        assert isinstance(data["total_pets"], int)

    def test_get_kpis(self, client):
        """Test getting KPI metrics."""
        response = client.get("/api/insights/kpis")
        assert response.status_code == 200
        data = response.json()

        assert "kpis" in data
        assert isinstance(data["kpis"], list)

    def test_get_customers_list(self, client):
        """Test getting customers list for insights."""
        response = client.get("/api/insights/customers")
        assert response.status_code == 200
        data = response.json()

        assert "customers" in data
        assert isinstance(data["customers"], list)

    def test_get_customer_360_view(self, client):
        """Test getting customer 360 view."""
        response = client.get("/api/insights/customers/DEMO-001")
        assert response.status_code == 200
        data = response.json()

        assert "customer" in data
        customer = data["customer"]
        assert customer["customer_id"] == "DEMO-001"
        assert "full_name" in customer
        assert "email" in customer
        assert "total_pets" in customer
        assert "total_policies" in customer

    def test_get_claims_analytics(self, client):
        """Test getting claims analytics."""
        response = client.get("/api/insights/claims")
        assert response.status_code == 200
        data = response.json()

        assert "claims" in data
        assert isinstance(data["claims"], list)

    def test_get_provider_performance(self, client):
        """Test getting provider performance metrics."""
        response = client.get("/api/insights/providers")
        assert response.status_code == 200
        data = response.json()

        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_get_risk_scores(self, client):
        """Test getting customer risk scores."""
        response = client.get("/api/insights/risks")
        assert response.status_code == 200
        data = response.json()

        assert "customers" in data
        assert isinstance(data["customers"], list)

    def test_get_cross_sell_opportunities(self, client):
        """Test getting cross-sell opportunities."""
        response = client.get("/api/insights/cross-sell")
        assert response.status_code == 200
        data = response.json()

        assert "opportunities" in data
        assert isinstance(data["opportunities"], list)

    def test_get_customer_segments(self, client):
        """Test getting customer segments."""
        response = client.get("/api/insights/segments")
        assert response.status_code == 200
        data = response.json()

        assert "segments" in data
        assert isinstance(data["segments"], dict)
