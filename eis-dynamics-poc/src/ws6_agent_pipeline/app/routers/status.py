"""
Status API router for health checks and metrics.
"""

import logging
from datetime import datetime

from fastapi import APIRouter

from ..config import settings
from ..orchestration import state_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Status"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Verifies that all dependencies are available.
    """
    checks = {
        "api": True,
        "state_manager": True,
        "ai_provider": False,
    }

    # Check AI provider configuration
    if settings.AI_PROVIDER == "claude":
        checks["ai_provider"] = bool(settings.ANTHROPIC_API_KEY)
    else:
        checks["ai_provider"] = bool(settings.OPENAI_API_KEY)

    is_ready = all(checks.values())

    return {
        "ready": is_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
async def get_metrics():
    """
    Get pipeline metrics summary.
    """
    # Get all runs
    all_runs = await state_manager.get_recent_runs(limit=1000)

    # Calculate metrics
    total_runs = len(all_runs)
    completed_runs = sum(1 for r in all_runs if r.status.value == "completed")
    failed_runs = sum(1 for r in all_runs if r.status.value == "failed")
    running_runs = sum(1 for r in all_runs if r.status.value in ["started", "running"])

    # Processing time stats
    processing_times = [
        r.total_processing_time_ms
        for r in all_runs
        if r.total_processing_time_ms > 0
    ]

    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    min_time = min(processing_times) if processing_times else 0
    max_time = max(processing_times) if processing_times else 0

    # Decision distribution
    decisions = {}
    for run in all_runs:
        if run.final_decision:
            decisions[run.final_decision] = decisions.get(run.final_decision, 0) + 1

    # Risk distribution
    risk_levels = {}
    for run in all_runs:
        if run.risk_level:
            risk_levels[run.risk_level] = risk_levels.get(run.risk_level, 0) + 1

    return {
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "running_runs": running_runs,
        "success_rate": completed_runs / total_runs if total_runs > 0 else 0,
        "processing_time": {
            "average_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
        },
        "decision_distribution": decisions,
        "risk_distribution": risk_levels,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/config")
async def get_config():
    """
    Get current configuration (non-sensitive).
    """
    return {
        "service_name": settings.SERVICE_NAME,
        "service_version": settings.SERVICE_VERSION,
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": settings.ai_model,
        "agent_max_iterations": settings.AGENT_MAX_ITERATIONS,
        "agent_temperature": settings.AGENT_TEMPERATURE,
        "agent_timeout_seconds": settings.AGENT_TIMEOUT_SECONDS,
        "storage_type": settings.AGENT_STORAGE_TYPE,
        "delta_bronze_path": settings.DELTA_BRONZE_PATH,
        "delta_silver_path": settings.DELTA_SILVER_PATH,
        "delta_gold_path": settings.DELTA_GOLD_PATH,
    }
