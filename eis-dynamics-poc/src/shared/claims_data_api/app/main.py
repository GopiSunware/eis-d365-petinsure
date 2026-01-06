"""
Unified Claims Data API - Main Application
Serves as the single gateway (port 8000) for all claims data services.
Used by both EIS Dynamics POC (AI agents) and PetInsure360 (rule-based).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.data_loader import get_data_store
from app.services import (
    policy_service,
    customer_service,
    pet_service,
    provider_service,
    fraud_service,
    medical_service,
    billing_service,
    validation_service,
    datalake_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup."""
    print("\n" + "=" * 60)
    print("Starting Unified Claims Data API")
    print("=" * 60)
    get_data_store()  # This loads all data
    print("=" * 60 + "\n")
    yield
    print("Shutting down Unified Claims Data API")


app = FastAPI(
    title="Unified Claims Data API",
    description="""
    Single API gateway providing claims data services for:
    - **EIS Dynamics POC** (AI Agent-driven claims processing)
    - **PetInsure360** (Rule-based claims processing)

    ## Services

    | Service | Prefix | Functions |
    |---------|--------|-----------|
    | PolicyService | /policies | 6 endpoints |
    | CustomerService | /customers | 6 endpoints |
    | PetService | /pets | 5 endpoints |
    | ProviderService | /providers | 5 endpoints |
    | FraudService | /fraud | 6 endpoints |
    | MedicalRefService | /medical | 5 endpoints |
    | BillingService | /billing | 5 endpoints |
    | **ValidationService** | /validation | **7 endpoints** |

    ## AI Validation (NEW)

    ValidationService provides AI-powered data quality checks:
    - Diagnosis-Treatment Mismatch detection
    - Cross-Document Inconsistency
    - Claim Completeness & Sequence validation
    - License Verification (Regulatory)
    - Controlled Substance Compliance (Regulatory)

    ## Data

    - 100 customers
    - 150 pets
    - 51 providers
    - 438 claims (including 9 fraud pattern claims)
    - 3 fraud patterns for AI detection demo
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow both frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # EIS Agent Portal (local)
        "http://localhost:8081",  # EIS Admin Portal (local)
        "http://localhost:3000",  # PetInsure360 Customer Portal (local)
        "http://localhost:3001",  # PetInsure360 BI Dashboard (local)
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://eis-dynamics-frontend-611670815873.s3-website-us-east-1.amazonaws.com",  # AWS S3 Frontend
        "https://eis-dynamics-frontend-611670815873.s3-website-us-east-1.amazonaws.com",
        "*",  # Allow all origins for API access
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register service routers
app.include_router(policy_service.router, prefix="/api/v1/policies", tags=["PolicyService"])
app.include_router(customer_service.router, prefix="/api/v1/customers", tags=["CustomerService"])
app.include_router(pet_service.router, prefix="/api/v1/pets", tags=["PetService"])
app.include_router(provider_service.router, prefix="/api/v1/providers", tags=["ProviderService"])
app.include_router(fraud_service.router, prefix="/api/v1/fraud", tags=["FraudService"])
app.include_router(medical_service.router, prefix="/api/v1/medical", tags=["MedicalRefService"])
app.include_router(billing_service.router, prefix="/api/v1/billing", tags=["BillingService"])
app.include_router(validation_service.router, prefix="/api/v1/validation", tags=["ValidationService"])
app.include_router(datalake_service.router, prefix="/api/v1/datalake", tags=["DataLakeService"])


@app.get("/", tags=["Health"])
async def root():
    """API root - health check and info."""
    store = get_data_store()
    return {
        "name": "Unified Claims Data API",
        "version": "1.0.0",
        "status": "healthy",
        "data_loaded": True,
        "stats": {
            "customers": len(store.get_customers()),
            "pets": len(store.get_pets()),
            "policies": len(store.get_policies()),
            "providers": len(store.get_providers()),
            "claims": len(store.get_claims()),
            "fraud_claims": len(store.get_fraud_claims()),
        },
        "endpoints": {
            "policies": "/api/v1/policies",
            "customers": "/api/v1/customers",
            "pets": "/api/v1/pets",
            "providers": "/api/v1/providers",
            "fraud": "/api/v1/fraud",
            "medical": "/api/v1/medical",
            "billing": "/api/v1/billing",
            "validation": "/api/v1/validation",
            "datalake": "/api/v1/datalake",
        }
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
