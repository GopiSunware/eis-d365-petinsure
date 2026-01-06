"""
Shared pytest fixtures for all test modules.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Import test app instances
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pathlib import Path


# =============================================================================
# Mock Data Fixtures
# =============================================================================

@pytest.fixture
def sample_customer() -> dict:
    """Sample customer data for testing."""
    return {
        "customer_id": "CUST-001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St, Springfield, IL 62701",
        "customer_type": "individual",
        "created_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_policy() -> dict:
    """Sample policy data for testing."""
    return {
        "policy_id": "POL-2024-001",
        "policy_number": "AUTO-IL-2024-00001",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "status": "active",
        "policy_type": "auto",
        "total_premium": 1250.00,
        "insured_name": "John Doe",
        "customer_id": "CUST-001",
        "coverages": [
            {
                "coverage_id": "COV-001",
                "coverage_type": "bodily_injury",
                "limit": 100000,
                "deductible": 0,
                "premium": 450.00,
            },
            {
                "coverage_id": "COV-002",
                "coverage_type": "property_damage",
                "limit": 50000,
                "deductible": 0,
                "premium": 300.00,
            },
            {
                "coverage_id": "COV-003",
                "coverage_type": "collision",
                "limit": 0,
                "deductible": 500,
                "premium": 350.00,
            },
            {
                "coverage_id": "COV-004",
                "coverage_type": "comprehensive",
                "limit": 0,
                "deductible": 250,
                "premium": 150.00,
            },
        ],
    }


@pytest.fixture
def sample_claim() -> dict:
    """Sample claim data for testing."""
    return {
        "claim_id": "CLM-2024-001",
        "claim_number": "CLM-2024-00001",
        "policy_id": "POL-2024-001",
        "date_of_loss": "2024-06-15",
        "date_reported": "2024-06-15T14:30:00Z",
        "status": "fnol_received",
        "loss_description": "Rear-ended at stoplight on Main Street. Other driver at fault. Moderate damage to rear bumper and trunk.",
        "severity": "moderate",
        "reserve_amount": 5000.00,
        "paid_amount": 0.00,
        "fraud_score": 0.15,
        "ai_recommendation": "Proceed with standard claims process. Low fraud risk detected.",
    }


@pytest.fixture
def sample_fnol_request() -> dict:
    """Sample FNOL request for testing."""
    return {
        "description": "I was stopped at a red light on Main Street when another vehicle rear-ended my car. The driver admitted fault. There is significant damage to my rear bumper and trunk. No injuries.",
        "date_of_loss": "2024-06-15",
        "policy_number": "AUTO-IL-2024-00001",
        "contact_phone": "555-123-4567",
        "contact_email": "john.doe@example.com",
    }


@pytest.fixture
def sample_quote_request() -> dict:
    """Sample quote request for testing."""
    return {
        "state": "IL",
        "zip_code": "62701",
        "effective_date": "2024-07-01",
        "drivers": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-03-15",
                "gender": "male",
                "marital_status": "married",
                "license_date": "2003-03-15",
                "violations": 0,
                "at_fault_accidents": 0,
                "is_primary": True,
            }
        ],
        "vehicles": [
            {
                "year": 2022,
                "make": "Toyota",
                "model": "Camry",
                "vin": "1HGBH41JXMN109186",
                "body_type": "sedan",
                "use": "commute",
                "annual_miles": 12000,
                "anti_theft": True,
                "safety_features": ["abs", "airbags", "backup_camera"],
            }
        ],
        "coverages": [
            {"coverage_type": "bodily_injury", "limit": 100000, "deductible": 0},
            {"coverage_type": "property_damage", "limit": 50000, "deductible": 0},
            {"coverage_type": "collision", "limit": 0, "deductible": 500},
            {"coverage_type": "comprehensive", "limit": 0, "deductible": 250},
        ],
        "prior_insurance": True,
        "homeowner": True,
        "multi_policy": False,
    }


@pytest.fixture
def sample_driver() -> dict:
    """Sample driver data for rating calculations."""
    return {
        "age": 39,
        "years_licensed": 21,
        "violations": 0,
        "at_fault_accidents": 0,
        "marital_status": "married",
        "gender": "male",
    }


@pytest.fixture
def sample_vehicle() -> dict:
    """Sample vehicle data for rating calculations."""
    return {
        "year": 2022,
        "make": "Toyota",
        "model": "Camry",
        "body_type": "sedan",
        "safety_rating": 5,
        "anti_theft": True,
        "annual_miles": 12000,
    }


# =============================================================================
# Mock Service Fixtures
# =============================================================================

@pytest.fixture
def mock_openai_response() -> dict:
    """Mock response from Azure OpenAI service."""
    return {
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


@pytest.fixture
def mock_fraud_analysis() -> dict:
    """Mock fraud analysis response."""
    return {
        "fraud_score": 0.15,
        "risk_level": "low",
        "indicators": [],
        "recommendation": "Proceed with standard claims process",
    }


@pytest.fixture
def mock_dataverse_client():
    """Mock Dataverse client for testing."""
    client = AsyncMock()
    client.create_entity = AsyncMock(return_value={"id": "test-guid"})
    client.get_entity = AsyncMock(return_value={"id": "test-guid", "name": "test"})
    client.update_entity = AsyncMock(return_value=True)
    client.delete_entity = AsyncMock(return_value=True)
    client.query_entities = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_service_bus_client():
    """Mock Azure Service Bus client for testing."""
    client = MagicMock()
    sender = MagicMock()
    sender.send_messages = MagicMock()
    client.get_queue_sender = MagicMock(return_value=sender)
    return client


# =============================================================================
# Test Configuration
# =============================================================================

@pytest.fixture
def test_settings() -> dict:
    """Test environment settings."""
    return {
        "ENVIRONMENT": "test",
        "AZURE_SUBSCRIPTION_ID": "test-subscription-id",
        "AZURE_TENANT_ID": "test-tenant-id",
        "DATAVERSE_URL": "https://test.crm.dynamics.com",
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-4o",
        "SERVICE_BUS_CONNECTION_STRING": "Endpoint=sb://test.servicebus.windows.net/",
        "COSMOS_DB_ENDPOINT": "https://test.documents.azure.com:443/",
    }


# =============================================================================
# Async Test Helpers
# =============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
