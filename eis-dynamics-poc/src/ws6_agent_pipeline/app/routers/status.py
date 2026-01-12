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


@router.delete("/clear")
async def clear_all_runs():
    """
    Clear all pipeline runs (for demo reset).
    """
    count = await state_manager.clear_all_runs()
    return {
        "success": True,
        "message": f"Cleared {count} pipeline runs",
        "runs_cleared": count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/ai/test")
async def test_ai_connection(provider: str = None, model: str = None):
    """
    Test AI provider connection by making a real API call.
    This validates that API key is valid and has credits.
    
    Args:
        provider: Optional provider override ('claude' or 'openai'). Defaults to configured provider.
        model: Optional model override. Defaults to configured model for the provider.
    """
    import httpx
    
    # Use provided values or fall back to settings
    provider = provider or settings.AI_PROVIDER
    
    # Default models by provider
    default_models = {
        "claude": "claude-sonnet-4-20250514",
        "openai": "gpt-4o"
    }
    model = model or (settings.ai_model if provider == settings.AI_PROVIDER else default_models.get(provider, "gpt-4o"))
    
    # Test message - simple and cheap
    test_message = "Say 'Hello' in one word."
    
    if provider == "claude":
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "message": "Claude API key not configured (ANTHROPIC_API_KEY)",
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": test_message}]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("content", [{}])[0].get("text", "")
                    return {
                        "status": "success",
                        "provider": provider,
                        "model": model,
                        "message": f"Connection successful! AI says: '{ai_response}'",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                elif response.status_code == 401:
                    return {
                        "status": "error",
                        "provider": provider,
                        "model": model,
                        "message": "Invalid API key - authentication failed",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                elif response.status_code == 400:
                    error_data = response.json()
                    error_type = error_data.get("error", {}).get("type", "")
                    error_msg = error_data.get("error", {}).get("message", "")
                    if "credit" in error_msg.lower() or "billing" in error_msg.lower():
                        return {
                            "status": "error",
                            "provider": provider,
                            "model": model,
                            "message": "API credits exhausted - please add credits to your Anthropic account",
                            "error_detail": error_msg,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    return {
                        "status": "error",
                        "provider": provider,
                        "model": model,
                        "message": f"API error: {error_msg}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                elif response.status_code == 429:
                    return {
                        "status": "warning",
                        "provider": provider,
                        "model": model,
                        "message": "Rate limited - API key is valid but too many requests",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    error_detail = response.text[:500]
                    return {
                        "status": "error",
                        "provider": provider,
                        "model": model,
                        "message": f"API error ({response.status_code}): {error_detail}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "message": "Connection timeout - API server did not respond",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "message": f"Connection error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    else:  # openai
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "message": "OpenAI API key not configured (OPENAI_API_KEY)",
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": test_message}]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "status": "success",
                        "provider": provider,
                        "model": model,
                        "message": f"Connection successful! AI says: '{ai_response}'",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                elif response.status_code == 401:
                    return {
                        "status": "error",
                        "provider": provider,
                        "model": model,
                        "message": "Invalid API key - authentication failed",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                elif response.status_code == 429:
                    error_msg = response.json().get("error", {}).get("message", "")
                    if "quota" in error_msg.lower() or "billing" in error_msg.lower():
                        return {
                            "status": "error",
                            "provider": provider,
                            "model": model,
                            "message": "API quota exceeded - check OpenAI billing",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    return {
                        "status": "warning",
                        "provider": provider,
                        "model": model,
                        "message": "Rate limited - too many requests",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    error_detail = response.text[:500]
                    return {
                        "status": "error",
                        "provider": provider,
                        "model": model,
                        "message": f"API error ({response.status_code}): {error_detail}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "message": "Connection timeout - API server did not respond",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": provider,
                "model": model,
                "message": f"Connection error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
