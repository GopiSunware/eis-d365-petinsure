"""
Azure Functions wrapper for PetInsure360 FastAPI application.
Uses the ASGI integration to run FastAPI on Azure Functions.
"""

import azure.functions as func

# Import the FastAPI app directly (not socket_app since WebSocket isn't supported)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import customers, pets, policies, claims, insights, recommendations, pipeline
from app.services.storage import StorageService
from app.services.insights import InsightsService

# Initialize services
storage_service = StorageService()
insights_service = InsightsService()

# Create a new FastAPI app for Azure Functions
app = FastAPI(
    title="PetInsure360 API",
    description="Pet Insurance Data Platform - Data Ingestion & BI Insights API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(pets.router, prefix="/api/pets", tags=["Pets"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(claims.router, prefix="/api/claims", tags=["Claims"])
app.include_router(insights.router, prefix="/api/insights", tags=["BI Insights"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Pet Recommendations"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Data Pipeline"])

# Make services available to routes
app.state.storage = storage_service
app.state.insights = insights_service

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PetInsure360 API",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "storage": {
            "account": storage_service.account_name,
            "container": storage_service.container_name
        }
    }

# Create the Azure Functions ASGI app wrapper
app_function = func.AsgiFunctionApp(app=app, http_auth_level=func.AuthLevel.ANONYMOUS)
