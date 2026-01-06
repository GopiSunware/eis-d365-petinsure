"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from ..config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "cosmos_db": "configured" if settings.cosmos_db_configured else "not_configured",
            "azure_cost": "configured" if settings.azure_cost_configured else "not_configured",
            "aws_cost": "configured" if settings.aws_cost_configured else "not_configured",
        }
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}
