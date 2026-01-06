"""Rating engine configuration endpoints."""

import logging
from decimal import Decimal
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..middleware.auth import require_permission
from ..models.users import User, Permission
from ..models.rating_config import (
    RatingFactorsConfig,
    RatingFactorsUpdate,
    BaseRates,
    BreedMultipliers,
    AgeFactors,
    GeographicFactors,
    Discounts,
    PremiumCalculation,
)
from ..models.approval import ApprovalRequestCreate, ConfigChangeType
from ..services.config_service import get_config_service
from ..services.approval_service import get_approval_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=RatingFactorsConfig)
async def get_rating_config(
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """Get current rating configuration."""
    config_service = get_config_service()
    return await config_service.get_rating_config()


@router.put("")
async def update_rating_config(
    request: Request,
    update: RatingFactorsUpdate,
    change_reason: str = Query(..., min_length=10, description="Reason for change"),
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_WRITE)),
):
    """
    Update rating configuration.
    Changes require approval.
    """
    config_service = get_config_service()
    approval_service = get_approval_service()
    audit_service = get_audit_service()

    current_config = await config_service.get_rating_config()

    proposed = current_config.model_dump()
    update_fields = []
    for key, value in update.model_dump(exclude_none=True).items():
        if value is not None:
            if hasattr(value, 'model_dump'):
                proposed[key] = value.model_dump()
            else:
                proposed[key] = value
            update_fields.append(key)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No changes detected")

    approval_request = ApprovalRequestCreate(
        change_type=ConfigChangeType.RATING_CONFIG,
        entity_id="rating_config",
        proposed_value=proposed,
        change_summary=f"Rating config update: {', '.join(update_fields)}",
        change_reason=change_reason,
    )

    approval = await approval_service.create_approval(
        request=approval_request,
        current_value=current_config.model_dump(),
        requester=current_user,
    )

    await audit_service.log_config_change_request(
        request=request,
        user=current_user,
        change_type="rating_config",
        approval_id=approval.id,
    )

    return {
        "status": "pending_approval",
        "approval_id": approval.id,
        "message": "Rating config change submitted for approval",
        "changes": update_fields,
    }


@router.get("/base-rates", response_model=BaseRates)
async def get_base_rates(
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """Get base premium rates."""
    config_service = get_config_service()
    config = await config_service.get_rating_config()
    return config.base_rates


@router.put("/base-rates")
async def update_base_rates(
    request: Request,
    update: BaseRates,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_WRITE)),
):
    """Update base rates."""
    return await update_rating_config(
        request=request,
        update=RatingFactorsUpdate(base_rates=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/breed-factors", response_model=BreedMultipliers)
async def get_breed_factors(
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """Get breed multipliers."""
    config_service = get_config_service()
    config = await config_service.get_rating_config()
    return config.breed_multipliers


@router.put("/breed-factors")
async def update_breed_factors(
    request: Request,
    update: BreedMultipliers,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_WRITE)),
):
    """Update breed factors."""
    return await update_rating_config(
        request=request,
        update=RatingFactorsUpdate(breed_multipliers=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/age-factors", response_model=AgeFactors)
async def get_age_factors(
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """Get age factors."""
    config_service = get_config_service()
    config = await config_service.get_rating_config()
    return config.age_factors


@router.put("/age-factors")
async def update_age_factors(
    request: Request,
    update: AgeFactors,
    change_reason: str = Query(..., min_length=10),
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_WRITE)),
):
    """Update age factors."""
    return await update_rating_config(
        request=request,
        update=RatingFactorsUpdate(age_factors=update),
        change_reason=change_reason,
        current_user=current_user,
    )


@router.get("/geographic-factors", response_model=GeographicFactors)
async def get_geographic_factors(
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """Get geographic factors."""
    config_service = get_config_service()
    config = await config_service.get_rating_config()
    return config.geographic_factors


@router.get("/discounts", response_model=Discounts)
async def get_discounts(
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """Get discount configuration."""
    config_service = get_config_service()
    config = await config_service.get_rating_config()
    return config.discounts


@router.post("/calculate", response_model=PremiumCalculation)
async def calculate_premium(
    calculation: PremiumCalculation,
    current_user: User = Depends(require_permission(Permission.CONFIG_RATING_READ)),
):
    """
    Calculate premium based on current rating factors.
    Useful for testing/previewing rate changes.
    """
    config_service = get_config_service()
    config = await config_service.get_rating_config()

    # Get base rate
    base_rate = getattr(config.base_rates, calculation.species.lower(), Decimal("45.00"))

    # Get breed factor
    breed_factor = 1.0
    breed_list = getattr(config.breed_multipliers, f"{calculation.species.lower()}s", [])
    for breed in breed_list:
        if breed.breed_name.lower() == calculation.breed.lower():
            breed_factor = breed.multiplier
            break

    # Get age factor
    age_factor = 1.0
    for range_str, factor in config.age_factors.ranges.items():
        if "-" in range_str:
            low, high = range_str.split("-")
            if int(low) <= calculation.age_years <= int(high):
                age_factor = factor
                break
        elif "+" in range_str:
            min_age = int(range_str.replace("+", ""))
            if calculation.age_years >= min_age:
                age_factor = factor
                break

    # Get geographic factor
    geographic_factor = config.geographic_factors.regions.get(
        calculation.region.lower(),
        config.geographic_factors.regions.get("default", 1.0)
    )

    # Get deductible adjustment
    deductible_adjustment = config.deductible_adjustments.get(
        str(calculation.deductible),
        1.0
    )

    # Get reimbursement adjustment
    reimbursement_adjustment = config.reimbursement_adjustments.get(
        str(calculation.reimbursement_percent),
        1.0
    )

    # Calculate premium
    monthly = float(base_rate) * breed_factor * age_factor * geographic_factor
    monthly = monthly * deductible_adjustment * reimbursement_adjustment

    return PremiumCalculation(
        species=calculation.species,
        breed=calculation.breed,
        age_years=calculation.age_years,
        region=calculation.region,
        plan=calculation.plan,
        deductible=calculation.deductible,
        reimbursement_percent=calculation.reimbursement_percent,
        base_rate=base_rate,
        breed_factor=breed_factor,
        age_factor=age_factor,
        geographic_factor=geographic_factor,
        deductible_adjustment=deductible_adjustment,
        reimbursement_adjustment=reimbursement_adjustment,
        monthly_premium=Decimal(str(round(monthly, 2))),
        annual_premium=Decimal(str(round(monthly * 12, 2))),
    )
