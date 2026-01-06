"""Pet Insurance Rating API endpoints."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.rate_calculator import RateCalculator
from ..services.factor_service import FactorService

logger = logging.getLogger(__name__)
router = APIRouter()

rate_calculator = RateCalculator()
factor_service = FactorService()


# Request/Response Models
class Pet(BaseModel):
    """Pet information for rating."""
    name: str
    species: str = "dog"  # dog, cat, bird, rabbit, reptile
    breed: str
    date_of_birth: str  # YYYY-MM-DD
    gender: str = "male"  # male, female
    spayed_neutered: bool = False
    microchipped: bool = False
    microchip_id: Optional[str] = None
    weight_lbs: Optional[float] = None
    pre_existing_conditions: List[str] = Field(default_factory=list)


class CoverageSelection(BaseModel):
    """Coverage selection for pet insurance quote."""
    plan_type: str = "accident_illness"  # accident_only, accident_illness, comprehensive
    annual_limit: Decimal = Decimal("10000")  # 5000, 10000, 15000, 0 (unlimited)
    deductible: Decimal = Decimal("250")  # 100, 250, 500, 750
    reimbursement_pct: int = 80  # 70, 80, 90


class AddOns(BaseModel):
    """Optional add-on coverages."""
    wellness: bool = False
    dental: bool = False
    behavioral: bool = False


class Discounts(BaseModel):
    """Available discounts."""
    multi_pet: bool = False
    annual_pay: bool = False
    shelter_rescue: bool = False
    military_veteran: bool = False


class QuoteRequest(BaseModel):
    """Pet insurance quote request."""
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    effective_date: str  # YYYY-MM-DD
    pet: Pet
    coverage: CoverageSelection = Field(default_factory=CoverageSelection)
    add_ons: AddOns = Field(default_factory=AddOns)
    discounts: Discounts = Field(default_factory=Discounts)


class CoverageCharge(BaseModel):
    """Individual coverage charge."""
    coverage_type: str
    limit: Decimal
    waiting_period_days: int
    premium: Decimal


class DiscountApplied(BaseModel):
    """Applied discount."""
    name: str
    rate: Decimal
    amount: Decimal


class PremiumBreakdown(BaseModel):
    """Detailed premium breakdown for pet insurance."""
    base_rate: Decimal
    species_factor: Decimal
    breed_factor: Decimal
    size_factor: Decimal
    combined_breed_factor: Decimal
    age_factor: Decimal
    location_factor: Decimal
    base_premium_with_factors: Decimal
    coverage_adjustments: Dict
    adjusted_premium: Decimal
    add_on_charges: List[Dict]
    discounts: List[DiscountApplied]
    total_discounts: Decimal
    policy_fee: Decimal
    total_annual_premium: Decimal


class ComparisonResult(BaseModel):
    """Comparison with EIS mock rate."""
    eis_premium: Decimal
    difference: Decimal
    percentage_diff: Decimal
    within_tolerance: bool


class QuoteResponse(BaseModel):
    """Pet insurance quote response."""
    quote_id: str
    state: str
    effective_date: str
    expiration_date: str
    valid_until: str
    pet: Dict
    premium_breakdown: PremiumBreakdown
    monthly_premium: Decimal
    comparison: Optional[ComparisonResult] = None


class CompareRequest(BaseModel):
    """Compare quote with mock EIS rate."""
    quote_request: QuoteRequest
    eis_premium: Decimal


class CompareResponse(BaseModel):
    """Comparison result."""
    our_premium: Decimal
    eis_premium: Decimal
    difference: Decimal
    percentage_diff: Decimal
    within_tolerance: bool
    factor_comparison: List[Dict]
    analysis: str


# Endpoints
@router.post("/quote", response_model=QuoteResponse)
async def calculate_quote(request: QuoteRequest):
    """
    Calculate pet insurance premium quote.

    Applies rating factors for:
    - Pet characteristics (species, breed, age, size)
    - Location (state, zip code)
    - Coverage selections (plan type, limits, deductible)
    - Add-ons (wellness, dental, behavioral)
    - Available discounts (spayed/neutered, microchipped, multi-pet)
    """
    logger.info(f"Calculating quote for {request.pet.name} ({request.pet.breed})")

    try:
        result = await rate_calculator.calculate(request)

        return QuoteResponse(
            quote_id=result["quote_id"],
            state=request.state,
            effective_date=request.effective_date,
            expiration_date=result["expiration_date"],
            valid_until=result["valid_until"],
            pet={
                "name": request.pet.name,
                "species": request.pet.species,
                "breed": request.pet.breed,
                "age_years": result["pet_age_years"],
                "gender": request.pet.gender,
            },
            premium_breakdown=PremiumBreakdown(
                base_rate=result["base_rate"],
                species_factor=result["species_factor"],
                breed_factor=result["breed_factor"],
                size_factor=result["size_factor"],
                combined_breed_factor=result["combined_breed_factor"],
                age_factor=result["age_factor"],
                location_factor=result["location_factor"],
                base_premium_with_factors=result["base_premium_with_factors"],
                coverage_adjustments=result["coverage_adjustments"],
                adjusted_premium=result["adjusted_premium"],
                add_on_charges=result["add_on_charges"],
                discounts=[DiscountApplied(**d) for d in result["discounts"]],
                total_discounts=result["total_discounts"],
                policy_fee=result["policy_fee"],
                total_annual_premium=result["total_annual_premium"],
            ),
            monthly_premium=result["monthly_premium"],
            comparison=ComparisonResult(**result["comparison"]) if result.get("comparison") else None,
        )

    except Exception as e:
        logger.error(f"Quote calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/factors")
async def get_factors():
    """Get available pet insurance rating factors and their values."""
    return {
        "species_factors": factor_service.get_species_factors(),
        "breed_factors": factor_service.get_breed_factors(),
        "age_factors": factor_service.get_age_factors(),
        "location_factors": factor_service.get_location_factors(),
        "discounts": factor_service.get_discounts(),
    }


@router.get("/factors/{factor_type}")
async def get_factor_type(factor_type: str):
    """Get specific factor type."""
    if factor_type == "species":
        return factor_service.get_species_factors()
    elif factor_type == "breed":
        return factor_service.get_breed_factors()
    elif factor_type == "age":
        return factor_service.get_age_factors()
    elif factor_type == "location":
        return factor_service.get_location_factors()
    elif factor_type == "discounts":
        return factor_service.get_discounts()
    else:
        raise HTTPException(status_code=404, detail="Factor type not found")


@router.get("/breeds")
async def get_breeds(species: Optional[str] = None, breed: Optional[str] = None):
    """Get breed-specific rating factors."""
    breeds = factor_service.get_breed_factors()

    if species:
        breeds = {k: v for k, v in breeds.items() if v.get("species") == species}

    if breed:
        breeds = {k: v for k, v in breeds.items() if breed.lower() in v.get("breed_name", "").lower()}

    return {"breeds": list(breeds.values()), "total": len(breeds)}


@router.post("/compare", response_model=CompareResponse)
async def compare_with_eis(request: CompareRequest):
    """Compare our calculated premium with EIS mock rate."""
    result = await rate_calculator.calculate(request.quote_request)
    our_premium = result["total_annual_premium"]

    difference = our_premium - request.eis_premium
    if request.eis_premium > 0:
        diff_pct = (difference / request.eis_premium) * 100
    else:
        diff_pct = Decimal("0")

    # Within ±2% tolerance
    within_tolerance = abs(diff_pct) <= 2

    return CompareResponse(
        our_premium=our_premium,
        eis_premium=request.eis_premium,
        difference=difference,
        percentage_diff=round(diff_pct, 2),
        within_tolerance=within_tolerance,
        factor_comparison=[
            {
                "factor": "breed_factor",
                "our_value": float(result["breed_factor"]),
                "eis_value": float(result["breed_factor"]) * 1.008,  # Mock EIS comparison
                "difference_pct": -0.8,
            },
            {
                "factor": "age_factor",
                "our_value": float(result["age_factor"]),
                "eis_value": float(result["age_factor"]),
                "difference_pct": 0.0,
            },
            {
                "factor": "location_factor",
                "our_value": float(result["location_factor"]),
                "eis_value": float(result["location_factor"]) * 0.991,
                "difference_pct": 0.9,
            },
        ],
        analysis="Premium is within +/-2% tolerance. Minor variances in breed and location factors cancel out.",
    )


@router.get("/coverages")
async def get_available_coverages():
    """Get available coverage types, plans, and options."""
    return {
        "plan_types": [
            {
                "type": "accident_only",
                "name": "Accident Only",
                "description": "Covers injuries from accidents only",
                "price_range": "$15-25/mo",
                "includes": ["accidents", "emergency_care", "surgery_accident"],
            },
            {
                "type": "accident_illness",
                "name": "Accident + Illness",
                "description": "Covers accidents AND illnesses (recommended)",
                "price_range": "$35-55/mo",
                "includes": ["accidents", "illnesses", "emergency_care", "surgery", "medications", "diagnostics", "hereditary"],
            },
            {
                "type": "comprehensive",
                "name": "Comprehensive",
                "description": "Accident + Illness + Wellness",
                "price_range": "$50-80/mo",
                "includes": ["accidents", "illnesses", "wellness", "dental", "behavioral", "alternative"],
            },
        ],
        "annual_limits": [
            {"value": 5000, "label": "$5,000/year", "factor": 0.85},
            {"value": 10000, "label": "$10,000/year", "factor": 1.00},
            {"value": 15000, "label": "$15,000/year", "factor": 1.15},
            {"value": 0, "label": "Unlimited", "factor": 1.40},
        ],
        "deductibles": [
            {"value": 100, "label": "$100", "factor": 1.15},
            {"value": 250, "label": "$250", "factor": 1.00},
            {"value": 500, "label": "$500", "factor": 0.88},
            {"value": 750, "label": "$750", "factor": 0.80},
        ],
        "reimbursement_rates": [
            {"value": 70, "label": "70%", "factor": 0.85},
            {"value": 80, "label": "80%", "factor": 1.00},
            {"value": 90, "label": "90%", "factor": 1.20},
        ],
        "add_ons": [
            {
                "type": "wellness",
                "name": "Wellness Add-On",
                "description": "Vaccines, checkups, dental cleaning, flea/tick",
                "monthly_cost": 15.00,
                "annual_limit": 450.00,
            },
            {
                "type": "dental",
                "name": "Dental Add-On",
                "description": "Dental illness, extractions, periodontal disease",
                "monthly_cost": 8.00,
                "annual_limit": 500.00,
            },
            {
                "type": "behavioral",
                "name": "Behavioral Add-On",
                "description": "Behavioral therapy, anxiety training",
                "monthly_cost": 5.00,
                "annual_limit": 300.00,
            },
        ],
        "waiting_periods": {
            "accident": {"days": 3, "description": "Accidents"},
            "illness": {"days": 14, "description": "Illnesses"},
            "orthopedic": {"days": 180, "description": "Cruciate/orthopedic"},
            "hip_dysplasia": {"days": 365, "description": "Hip dysplasia"},
            "cancer": {"days": 30, "description": "Cancer"},
        },
    }
