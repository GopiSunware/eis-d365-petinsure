"""
Agent Pipeline Service - Main FastAPI Application

This service provides an agent-driven medallion architecture for
processing pet insurance claims through Bronze, Silver, and Gold layers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .orchestration import event_publisher, state_manager
from .routers import (
    pipeline_router,
    status_router,
    websocket_router,
    scenarios_router,
    comparison_router,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info(f"AI Provider: {settings.AI_PROVIDER} ({settings.ai_model})")

    # Initialize state manager
    await state_manager.initialize()
    logger.info("State manager initialized")

    # Initialize event publisher
    await event_publisher.initialize()
    logger.info("Event publisher initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await event_publisher.close()
    await state_manager.close()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Agent Pipeline Service",
    description="""
## Agent-Driven Medallion Architecture

This service processes pet insurance claims through an intelligent
agent-driven medallion architecture:

### Pipeline Stages

1. **Router Agent** - Determines claim complexity and processing path
2. **Bronze Agent** - Validates, cleans, and assesses data quality
3. **Silver Agent** - Enriches data with policy, customer, and provider context
4. **Gold Agent** - Generates insights, risk scores, and final decisions

### Key Features

- **Real-time Streaming**: WebSocket events for live reasoning display
- **Explainable AI**: Full transparency into agent decision-making
- **Adaptive Processing**: Agents handle schema changes and edge cases
- **Visual Flow**: Designed for n8n-style visual monitoring

### Demo Endpoints

Use `/api/v1/pipeline/demo/claim` to trigger demo claims with different
complexity levels (simple, medium, complex).
    """,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

# Configure CORS - use config or allow all if not configured
# Note: allow_credentials=True is incompatible with allow_origins=["*"]
# When using wildcard, credentials must be False
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
allow_credentials = cors_origins != ["*"]  # Only allow credentials with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(status_router)
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(scenarios_router, prefix="/api/v1")
app.include_router(comparison_router, prefix="/api/v1")
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "description": "Agent-Driven Medallion Architecture for Pet Insurance Claims",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "pipeline_trigger": "/api/v1/pipeline/trigger",
            "demo_claim": "/api/v1/pipeline/demo/claim",
            "scenarios": "/api/v1/scenarios",
            "compare_quick": "/api/v1/compare/quick",
            "compare_scenario": "/api/v1/compare/scenario/{scenario_id}",
            "websocket_events": "/ws/events",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
