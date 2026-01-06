"""WS8: Admin Portal Service - FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware.audit_logger import AuditLoggerMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Dev mode (auth disabled): {settings.DEV_MODE}")
    logger.info(f"Cosmos DB configured: {settings.cosmos_db_configured}")
    logger.info(f"Azure Cost configured: {settings.azure_cost_configured}")
    logger.info(f"AWS Cost configured: {settings.aws_cost_configured}")

    # Initialize services
    if settings.cosmos_db_configured:
        from .services.cosmos_service import cosmos_client
        await cosmos_client.initialize()
        logger.info("Cosmos DB client initialized")

    yield

    # Cleanup
    if settings.cosmos_db_configured:
        from .services.cosmos_service import cosmos_client
        await cosmos_client.close()

    logger.info(f"Shutting down {settings.SERVICE_NAME}...")


app = FastAPI(
    title="EIS-D365 Admin Portal",
    description="""
## Admin Portal API

Administrative portal for the EIS-Dynamics 365 Pet Insurance Platform.

### Features:
- **AI Configuration**: Manage AI providers, models, and behavior settings
- **Claims Rules**: Configure auto-adjudication, fraud detection, escalation rules
- **Policy Configuration**: Manage plans, coverage, exclusions, waiting periods
- **Rating Configuration**: Configure base rates, breed factors, age factors, discounts
- **Cost Monitoring**: Track Azure and AWS cloud costs with budgets and alerts
- **Audit Logging**: Complete audit trail of all administrative actions
- **User Management**: RBAC with Admin, Approver, Config Manager, Viewer roles
- **Maker-Checker Workflow**: Configuration changes require approval

### Authentication:
All endpoints require JWT authentication. Use `/api/v1/auth/login` to obtain a token.
    """,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - config driven (no hardcoded URLs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_resolved,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit logging middleware - logs all HTTP requests
app.add_middleware(AuditLoggerMiddleware)

# Import and include routers
from .routers import (
    health,
    ai_config,
    claims_rules,
    policy_config,
    rating_config,
    costs,
    audit,
    users,
    approvals,
    auth,
)

# Health check routes (no auth required)
app.include_router(health.router, tags=["Health"])

# Auth routes (no auth required for login)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Configuration routes
app.include_router(
    ai_config.router,
    prefix="/api/v1/config/ai",
    tags=["AI Configuration"]
)
app.include_router(
    claims_rules.router,
    prefix="/api/v1/config/claims",
    tags=["Claims Rules"]
)
app.include_router(
    policy_config.router,
    prefix="/api/v1/config/policies",
    tags=["Policy Configuration"]
)
app.include_router(
    rating_config.router,
    prefix="/api/v1/config/rating",
    tags=["Rating Configuration"]
)

# Monitoring routes
app.include_router(
    costs.router,
    prefix="/api/v1/costs",
    tags=["Cost Monitoring"]
)

# Admin routes
app.include_router(
    audit.router,
    prefix="/api/v1/audit",
    tags=["Audit Logs"]
)
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["User Management"]
)
app.include_router(
    approvals.router,
    prefix="/api/v1/approvals",
    tags=["Approvals"]
)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "description": "EIS-D365 Admin Portal API",
        "docs": "/docs",
        "health": "/health",
    }
