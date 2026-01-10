"""
Admin Configuration Service - Provides config endpoints for Admin Portal.
Maps /api/v1/config/* to existing services or returns mock data.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .ai_config_service import get_ai_config, get_available_models, AIConfigState

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== MODELS ====================

class AIConfigResponse(BaseModel):
    """AI configuration response matching Admin Portal expectations."""
    provider: str
    model: str
    temperature: float
    max_tokens: int
    vision_enabled: bool = True
    tool_use_enabled: bool = True
    requires_approval: bool = True


class AIConfigHistory(BaseModel):
    """AI config change history entry."""
    id: str
    timestamp: datetime
    changed_by: str
    change_type: str
    previous_value: dict
    new_value: dict
    reason: str


class ClaimsConfig(BaseModel):
    """Claims processing configuration."""
    auto_adjudication_enabled: bool = True
    auto_adjudication_threshold: float = 500.0
    fraud_detection_enabled: bool = True
    fraud_score_threshold: float = 0.7
    pre_existing_check_enabled: bool = True
    duplicate_check_enabled: bool = True
    requires_approval: bool = True


class PolicyConfig(BaseModel):
    """Policy configuration."""
    default_waiting_period_days: int = 14
    max_coverage_amount: float = 15000.0
    renewal_grace_period_days: int = 30
    requires_approval: bool = True


class RatingConfig(BaseModel):
    """Rating configuration."""
    base_rate_dog: float = 45.0
    base_rate_cat: float = 35.0
    base_rate_exotic: float = 65.0
    age_factor_enabled: bool = True
    breed_factor_enabled: bool = True
    location_factor_enabled: bool = True
    requires_approval: bool = True


# ==================== AI CONFIG ENDPOINTS ====================

@router.get("/ai", response_model=AIConfigResponse)
async def get_ai_config_admin():
    """Get current AI configuration for Admin Portal."""
    config = get_ai_config()
    return AIConfigResponse(
        provider=config.provider,
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        vision_enabled=True,
        tool_use_enabled=True,
        requires_approval=True,
    )


@router.put("/ai")
async def update_ai_config_admin(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update AI configuration (mock - returns updated config)."""
    from .ai_config_service import set_ai_config

    updated = set_ai_config(
        provider=data.get("provider"),
        model_id=data.get("model"),
        temperature=data.get("temperature"),
        max_tokens=data.get("max_tokens"),
    )

    return AIConfigResponse(
        provider=updated.provider,
        model=updated.model_id,
        temperature=updated.temperature,
        max_tokens=updated.max_tokens,
        vision_enabled=True,
        tool_use_enabled=True,
        requires_approval=True,
    )


@router.get("/ai/models")
async def get_ai_models_admin():
    """Get available AI models for Admin Portal."""
    models = get_available_models()
    return {
        "models": [
            {
                "provider": m.provider,
                "model_id": m.model_id,
                "display_name": m.display_name,
                "description": m.description,
                "max_tokens": m.max_tokens,
                "supports_vision": m.supports_vision,
                "supports_tools": m.supports_tools,
            }
            for m in models
        ],
        "providers": ["claude", "openai"],
    }


@router.get("/ai/history", response_model=List[AIConfigHistory])
async def get_ai_config_history():
    """Get AI configuration change history (mock data)."""
    now = datetime.utcnow()
    return [
        AIConfigHistory(
            id="hist-001",
            timestamp=now - timedelta(days=7),
            changed_by="admin@example.com",
            change_type="model_change",
            previous_value={"model": "claude-3-5-sonnet-20241022"},
            new_value={"model": "claude-sonnet-4-20250514"},
            reason="Upgraded to latest Claude model",
        ),
        AIConfigHistory(
            id="hist-002",
            timestamp=now - timedelta(days=14),
            changed_by="system",
            change_type="initial_setup",
            previous_value={},
            new_value={"provider": "claude", "model": "claude-3-5-sonnet-20241022"},
            reason="Initial configuration",
        ),
    ]


# ==================== CLAIMS CONFIG ENDPOINTS ====================

@router.get("/claims", response_model=ClaimsConfig)
async def get_claims_config():
    """Get claims processing configuration."""
    return ClaimsConfig()


@router.put("/claims")
async def update_claims_config(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update claims configuration (mock)."""
    return ClaimsConfig(**{**ClaimsConfig().model_dump(), **data})


@router.get("/claims/auto-adjudication")
async def get_auto_adjudication_config():
    """Get auto-adjudication settings."""
    return {
        "enabled": True,
        "threshold_amount": 500.0,
        "max_per_day": 100,
        "eligible_claim_types": ["wellness", "routine", "vaccination"],
        "requires_documents": False,
    }


@router.put("/claims/auto-adjudication")
async def update_auto_adjudication_config(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update auto-adjudication settings (mock)."""
    defaults = {
        "enabled": True,
        "threshold_amount": 500.0,
        "max_per_day": 100,
        "eligible_claim_types": ["wellness", "routine", "vaccination"],
        "requires_documents": False,
    }
    return {**defaults, **data}


@router.get("/claims/fraud-detection")
async def get_fraud_detection_config():
    """Get fraud detection settings."""
    return {
        "enabled": True,
        "score_threshold": 0.7,
        "patterns": [
            {"name": "duplicate_claims", "enabled": True, "weight": 0.3},
            {"name": "provider_collusion", "enabled": True, "weight": 0.25},
            {"name": "pre_existing_gaming", "enabled": True, "weight": 0.25},
            {"name": "timing_patterns", "enabled": True, "weight": 0.2},
        ],
        "auto_flag_threshold": 0.8,
        "auto_deny_threshold": 0.95,
    }


@router.put("/claims/fraud-detection")
async def update_fraud_detection_config(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update fraud detection settings (mock)."""
    return data


# ==================== POLICY CONFIG ENDPOINTS ====================

@router.get("/policies", response_model=PolicyConfig)
async def get_policies_config():
    """Get policy configuration."""
    return PolicyConfig()


@router.put("/policies")
async def update_policies_config(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update policy configuration (mock)."""
    return PolicyConfig(**{**PolicyConfig().model_dump(), **data})


@router.get("/policies/plans")
async def get_policy_plans():
    """Get available policy plans."""
    return {
        "plans": [
            {
                "id": "accident_only",
                "name": "Accident Only",
                "description": "Coverage for accidents and injuries",
                "base_premium": 25.0,
                "coverage_limit": 10000,
            },
            {
                "id": "accident_illness",
                "name": "Accident & Illness",
                "description": "Comprehensive coverage for accidents and illnesses",
                "base_premium": 45.0,
                "coverage_limit": 15000,
            },
            {
                "id": "comprehensive",
                "name": "Comprehensive",
                "description": "Full coverage including wellness",
                "base_premium": 65.0,
                "coverage_limit": 20000,
            },
        ]
    }


@router.get("/policies/waiting-periods")
async def get_waiting_periods():
    """Get waiting period configurations."""
    return {
        "waiting_periods": [
            {"type": "accident", "days": 0},
            {"type": "illness", "days": 14},
            {"type": "orthopedic", "days": 180},
            {"type": "cruciate", "days": 180},
        ]
    }


@router.get("/policies/exclusions")
async def get_policy_exclusions():
    """Get policy exclusion list."""
    return {
        "exclusions": [
            "Pre-existing conditions",
            "Cosmetic procedures",
            "Breeding costs",
            "Experimental treatments",
            "Preventable conditions (obesity)",
        ]
    }


# ==================== RATING CONFIG ENDPOINTS ====================

@router.get("/rating", response_model=RatingConfig)
async def get_rating_config():
    """Get rating configuration."""
    return RatingConfig()


@router.put("/rating")
async def update_rating_config(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update rating configuration (mock)."""
    return RatingConfig(**{**RatingConfig().model_dump(), **data})


@router.get("/rating/base-rates")
async def get_base_rates():
    """Get base rate configuration."""
    return {
        "rates": {
            "dog": {"base": 45.0, "min": 30.0, "max": 120.0},
            "cat": {"base": 35.0, "min": 25.0, "max": 80.0},
            "bird": {"base": 20.0, "min": 15.0, "max": 40.0},
            "exotic": {"base": 65.0, "min": 40.0, "max": 200.0},
        }
    }


@router.put("/rating/base-rates")
async def update_base_rates(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update base rates (mock)."""
    return data


@router.get("/rating/breed-factors")
async def get_breed_factors():
    """Get breed factor configuration."""
    return {
        "factors": {
            "high_risk": {
                "breeds": ["Bulldog", "German Shepherd", "Great Dane"],
                "factor": 1.5,
            },
            "medium_risk": {
                "breeds": ["Labrador", "Golden Retriever", "Beagle"],
                "factor": 1.2,
            },
            "low_risk": {
                "breeds": ["Mixed Breed", "Mutt"],
                "factor": 0.9,
            },
        }
    }


@router.put("/rating/breed-factors")
async def update_breed_factors(
    data: dict,
    change_reason: str = Query(default="Admin update"),
):
    """Update breed factors (mock)."""
    return data


@router.get("/rating/age-factors")
async def get_age_factors():
    """Get age factor configuration."""
    return {
        "factors": [
            {"age_range": "0-1", "factor": 1.0},
            {"age_range": "1-4", "factor": 1.1},
            {"age_range": "4-7", "factor": 1.3},
            {"age_range": "7-10", "factor": 1.6},
            {"age_range": "10+", "factor": 2.0},
        ]
    }


@router.post("/rating/calculate")
async def calculate_premium(data: dict):
    """Calculate premium based on provided factors."""
    species = data.get("species", "dog")
    age = data.get("age", 3)
    breed = data.get("breed", "Mixed")

    base_rates = {"dog": 45.0, "cat": 35.0, "bird": 20.0, "exotic": 65.0}
    base = base_rates.get(species, 45.0)

    # Age factor
    if age < 1:
        age_factor = 1.0
    elif age < 4:
        age_factor = 1.1
    elif age < 7:
        age_factor = 1.3
    elif age < 10:
        age_factor = 1.6
    else:
        age_factor = 2.0

    # Simple breed factor
    breed_factor = 1.2 if breed.lower() in ["bulldog", "german shepherd"] else 1.0

    monthly = base * age_factor * breed_factor

    return {
        "monthly_premium": round(monthly, 2),
        "annual_premium": round(monthly * 12, 2),
        "factors": {
            "base_rate": base,
            "age_factor": age_factor,
            "breed_factor": breed_factor,
        }
    }
