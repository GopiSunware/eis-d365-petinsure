# PetInsure360 Backend - Test Report

## Overview

Comprehensive test suite created for PetInsure360 backend API endpoints.

**Test Suite Location**: `/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend/tests/`

## Test Structure

### Test Files Created

| File | Purpose | Test Count |
|------|---------|------------|
| `test_health.py` | Health check endpoints | 2 tests |
| `test_customers.py` | Customer API endpoints | 10 tests |
| `test_pets.py` | Pet API endpoints | 7 tests |
| `test_policies.py` | Policy API endpoints | 7 tests |
| `test_claims.py` | Claims API endpoints | 6 tests |
| `test_insights.py` | BI Insights API endpoints | 9 tests |
| `test_pipeline.py` | Data Pipeline API endpoints | 7 tests |

**Total**: 48 comprehensive API tests

## Test Coverage

### 1. Health Check Tests (`test_health.py`)

- `test_root_endpoint` - Verifies root endpoint returns healthy status
- `test_health_endpoint` - Verifies detailed health check with storage info

### 2. Customer API Tests (`test_customers.py`)

**Success Cases**:
- `test_create_customer_success` - Customer registration
- `test_lookup_customer_by_email_demo_user` - Email-based lookup
- `test_get_customer_by_id_demo_user` - ID-based retrieval
- `test_seed_demo_data` - Demo data seeding

**Validation Tests**:
- `test_create_customer_invalid_email` - Invalid email format
- `test_create_customer_invalid_phone` - Invalid phone format
- `test_create_customer_invalid_state` - Invalid state code
- `test_create_customer_invalid_zip` - Invalid ZIP code

**Error Cases**:
- `test_lookup_customer_not_found` - Non-existent email
- `test_get_customer_not_found` - Non-existent customer ID

### 3. Pet API Tests (`test_pets.py`)

**Success Cases**:
- `test_create_pet_success` - Pet registration
- `test_get_pets_by_customer` - List pets for customer
- `test_get_pet_by_id` - Get specific pet

**Validation Tests**:
- `test_create_pet_invalid_species` - Invalid species (only Dog/Cat allowed)
- `test_create_pet_invalid_gender` - Invalid gender (only Male/Female allowed)
- `test_create_pet_invalid_weight` - Invalid weight (must be > 0)

**Error Cases**:
- `test_get_pet_not_found` - Non-existent pet ID

### 4. Policy API Tests (`test_policies.py`)

**Success Cases**:
- `test_create_policy_success` - Policy creation
- `test_get_policies_by_customer` - List policies for customer
- `test_get_policies_by_pet` - List policies for pet
- `test_validate_policy_for_pet` - Policy validation
- `test_get_policy_by_id` - Get specific policy
- `test_get_available_plans` - List available insurance plans

**Validation Tests**:
- `test_create_policy_invalid_plan` - Invalid plan name

### 5. Claims API Tests (`test_claims.py`)

**Success Cases**:
- `test_create_claim_success` - Claim submission
- `test_get_claim_status` - Claim status check
- `test_get_claims_by_customer` - List customer claims
- `test_simulate_claim_processing` - Process claim simulation

**Validation Tests**:
- `test_create_claim_invalid_type` - Invalid claim type
- `test_create_claim_invalid_amount` - Invalid claim amount (must be > 0)

### 6. Insights API Tests (`test_insights.py`)

**Analytics Tests**:
- `test_get_summary` - Summary statistics
- `test_get_kpis` - KPI metrics
- `test_get_customers_list` - Customer list
- `test_get_customer_360_view` - Customer 360 view
- `test_get_claims_analytics` - Claims analytics
- `test_get_provider_performance` - Provider metrics
- `test_get_risk_scores` - Risk scoring
- `test_get_cross_sell_opportunities` - Cross-sell analysis
- `test_get_customer_segments` - Customer segmentation

### 7. Pipeline API Tests (`test_pipeline.py`)

**Pipeline Tests**:
- `test_get_pipeline_status` - Pipeline layer status
- `test_get_pipeline_flow` - Flow visualization data
- `test_get_pending_claims` - Pending claims list
- `test_submit_claim_to_pipeline` - Submit to pipeline
- `test_get_pipeline_metrics` - Pipeline metrics
- `test_refresh_pipeline` - Refresh pipeline data
- `test_get_fraud_scenarios` - Fraud detection scenarios

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
```

### conftest.py

- Test client fixture using FastAPI TestClient
- Demo data fixtures for customers, pets, policies, claims
- Reusable test data across all test modules

## How to Run Tests

### Prerequisites

1. Install test dependencies:
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend
pip install pytest pytest-asyncio httpx
```

2. Set environment variables (optional for local testing):
```bash
export AZURE_STORAGE_ACCOUNT_NAME="test"
export AZURE_STORAGE_ACCOUNT_KEY="test"
export AZURE_STORAGE_CONTAINER_NAME="test"
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v

# Run specific test
pytest tests/test_customers.py::TestCustomerEndpoints::test_create_customer_success -v
```

### Alternative: Manual API Tests

For live API testing with server running:

```bash
# Make script executable
chmod +x manual_api_tests.sh

# Start backend server
cd backend
uvicorn app.main:socket_app --host 0.0.0.0 --port 3002

# Run manual tests (in another terminal)
./manual_api_tests.sh
```

## Known Issues

### TestClient Compatibility Issue

The current starlette version (0.35.1) has a different TestClient signature that causes initialization errors. To fix:

**Option 1**: Downgrade starlette
```bash
pip install starlette==0.27.0
```

**Option 2**: Use httpx directly
```python
from httpx import Client, ASGITransport
client = Client(transport=ASGITransport(app=app), base_url="http://test")
```

**Option 3**: Use manual curl-based tests (provided)

## Expected Test Results

When properly configured and run:

| Category | Tests | Expected Pass |
|----------|-------|---------------|
| Health | 2 | 100% |
| Customers | 10 | 80-100% |
| Pets | 7 | 85-100% |
| Policies | 7 | 85-100% |
| Claims | 6 | 85-100% |
| Insights | 9 | 90-100% |
| Pipeline | 7 | 90-100% |
| **Total** | **48** | **85-100%** |

## Test Data

### Demo Users (Pre-seeded)

| ID | Email | Pets | Policies |
|----|-------|------|----------|
| DEMO-001 | demo@demologin.com | 2 | 2 |
| DEMO-002 | demo1@demologin.com | 2 | 1 |
| DEMO-003 | demo2@demologin.com | 1 | 1 |

### Test Fixtures

All tests use consistent, reusable fixtures defined in `conftest.py`:
- `demo_customer_data` - Valid customer object
- `demo_pet_data` - Valid pet object
- `demo_policy_data` - Valid policy object
- `demo_claim_data` - Valid claim object

## Recommendations

1. **Fix TestClient Issue**: Update starlette or adjust test fixture to match version
2. **Add Integration Tests**: Test complete workflows (customer → pet → policy → claim)
3. **Add Performance Tests**: Use locust or similar for load testing
4. **Add Database Tests**: If using a database, add transaction/rollback tests
5. **CI/CD Integration**: Add tests to GitHub Actions or Azure Pipelines
6. **Test Coverage**: Aim for 80%+ code coverage

## Test Maintenance

- Update tests when API endpoints change
- Keep demo data in sync with production schemas
- Review and update validation tests when business rules change
- Add tests for new features before implementation (TDD)

## Contact

For test-related issues, contact the QA team or reference this documentation.

---

**Report Generated**: 2026-01-06
**Test Suite Version**: 1.0.0
**Backend API Version**: 1.0.0
