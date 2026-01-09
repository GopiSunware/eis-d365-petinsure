"""
Pytest Configuration and Fixtures
Common test setup for PetInsure360 backend tests
"""

import pytest
from fastapi.testclient import TestClient as FastAPITestClient
from app.main import app  # Use the base FastAPI app
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI application."""
    # Use FastAPI's TestClient directly
    with FastAPITestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def demo_customer_data():
    """Demo customer data for testing."""
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "phone": "5551234567",
        "address_line1": "123 Test St",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "date_of_birth": "1990-01-15",
        "preferred_contact": "Email",
        "marketing_opt_in": True,
        "referral_source": "Test"
    }


@pytest.fixture(scope="module")
def demo_pet_data():
    """Demo pet data for testing."""
    return {
        "pet_name": "TestPet",
        "species": "Dog",
        "breed": "Golden Retriever",
        "gender": "Male",
        "date_of_birth": "2020-03-15",
        "weight_lbs": 65.5,
        "color": "Golden",
        "is_neutered": True,
        "vaccination_status": "Up-to-date"
    }


@pytest.fixture(scope="module")
def demo_policy_data():
    """Demo policy data for testing."""
    return {
        "plan_name": "Premium",
        "payment_method": "Credit Card",
        "payment_frequency": "Monthly",
        "includes_wellness": True,
        "includes_dental": True,
        "includes_behavioral": False
    }


@pytest.fixture(scope="module")
def demo_claim_data():
    """Demo claim data for testing."""
    return {
        "claim_type": "Illness",
        "claim_category": "Digestive",
        "service_date": "2024-12-20",
        "claim_amount": 450.00,
        "diagnosis_code": "GI001",
        "treatment_notes": "Treatment for stomach upset",
        "invoice_number": "INV-2024-001",
        "is_emergency": False
    }
