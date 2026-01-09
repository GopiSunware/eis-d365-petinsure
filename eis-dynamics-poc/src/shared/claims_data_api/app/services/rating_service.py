"""
RatingService - Pet insurance rating and quote generation.
Provides premium calculations, breed factors, and coverage options.
Ported from ws5_rating_engine for unified API access.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

router = APIRouter()


# ==================== ENUMS ====================

class Species(str, Enum):
    DOG = "dog"
    CAT = "cat"


class CoverageLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ELITE = "elite"


# ==================== REQUEST/RESPONSE MODELS ====================

class QuoteRequest(BaseModel):
    """Request model for quote calculation."""
    species: Species
    breed: str
    age_years: int = Field(..., ge=0, le=25)
    zip_code: str = Field(..., min_length=5, max_length=5)
    coverage_level: CoverageLevel = CoverageLevel.STANDARD
    deductible: int = Field(default=500, ge=0, le=2000)
    annual_limit: int = Field(default=10000, ge=1000, le=100000)
    include_wellness: bool = False
    include_dental: bool = False
    pre_existing_conditions: List[str] = []


class QuoteResponse(BaseModel):
    """Response model for quote."""
    monthly_premium: float
    annual_premium: float
    deductible: int
    annual_limit: int
    coverage_level: str
    coverage_details: Dict[str, Any]
    factors_applied: Dict[str, float]
    discounts_applied: List[Dict[str, Any]]
    total_discount_percent: float
    effective_date: str
    quote_valid_until: str


class CompareRequest(BaseModel):
    """Request model for comparing coverage levels."""
    species: Species
    breed: str
    age_years: int = Field(..., ge=0, le=25)
    zip_code: str = Field(..., min_length=5, max_length=5)


# ==================== RATING FACTORS DATA ====================

# Base rates by state (using zip code prefix)
BASE_RATES = {
    "100": 45.00,  # NY
    "900": 42.00,  # CA - LA
    "941": 48.00,  # CA - SF
    "606": 38.00,  # IL - Chicago
    "770": 35.00,  # TX - Houston
    "331": 40.00,  # FL - Miami
    "981": 36.00,  # WA - Seattle
    "802": 34.00,  # CO - Denver
    "300": 32.00,  # GA - Atlanta
    "021": 44.00,  # MA - Boston
}
DEFAULT_BASE_RATE = 40.00

# Species multipliers
SPECIES_FACTORS = {
    "dog": 1.0,
    "cat": 0.75,  # Cats generally have lower vet costs
}

# Breed risk factors
BREED_FACTORS = {
    # High-risk dog breeds
    "French Bulldog": 1.85,
    "English Bulldog": 1.80,
    "Bulldog": 1.75,
    "Pug": 1.60,
    "Boston Terrier": 1.45,
    "German Shepherd": 1.40,
    "Rottweiler": 1.35,
    "Great Dane": 1.50,
    "Boxer": 1.30,
    "Doberman Pinscher": 1.35,
    "Cavalier King Charles Spaniel": 1.45,
    "Dachshund": 1.30,

    # Medium-risk dog breeds
    "Golden Retriever": 1.20,
    "Labrador Retriever": 1.15,
    "Cocker Spaniel": 1.20,
    "Beagle": 1.10,
    "Poodle": 1.15,
    "Shih Tzu": 1.15,
    "Yorkshire Terrier": 1.10,
    "Chihuahua": 1.05,

    # Low-risk dog breeds
    "Border Collie": 1.00,
    "Australian Shepherd": 1.00,
    "Mixed Breed Dog": 0.95,

    # Cat breeds
    "Persian": 1.30,
    "Exotic Shorthair": 1.25,
    "Maine Coon": 1.20,
    "Ragdoll": 1.15,
    "British Shorthair": 1.10,
    "Siamese": 1.10,
    "Bengal": 1.15,
    "Scottish Fold": 1.25,
    "Sphynx": 1.35,
    "Domestic Shorthair": 0.90,
    "Domestic Longhair": 0.95,
    "Mixed Breed Cat": 0.85,
}
DEFAULT_BREED_FACTOR = 1.0

# Age factors
DOG_AGE_FACTORS = {
    0: 1.20,   # Puppy - higher risk
    1: 1.00,
    2: 1.00,
    3: 1.00,
    4: 1.05,
    5: 1.10,
    6: 1.20,
    7: 1.35,
    8: 1.50,
    9: 1.70,
    10: 1.90,
    11: 2.10,
    12: 2.30,
    13: 2.50,
    14: 2.70,
}

CAT_AGE_FACTORS = {
    0: 1.15,   # Kitten
    1: 1.00,
    2: 1.00,
    3: 1.00,
    4: 1.00,
    5: 1.05,
    6: 1.10,
    7: 1.15,
    8: 1.25,
    9: 1.35,
    10: 1.45,
    11: 1.55,
    12: 1.65,
    13: 1.75,
    14: 1.85,
    15: 1.95,
}

# Coverage level multipliers
COVERAGE_MULTIPLIERS = {
    "basic": 0.70,      # 70% reimbursement
    "standard": 1.00,   # 80% reimbursement
    "premium": 1.35,    # 90% reimbursement
    "elite": 1.80,      # 100% reimbursement + extras
}

# Deductible discounts
DEDUCTIBLE_DISCOUNTS = {
    0: 1.30,     # No deductible = higher premium
    100: 1.15,
    250: 1.05,
    500: 1.00,   # Standard
    750: 0.92,
    1000: 0.85,
    1500: 0.75,
    2000: 0.68,
}

# Annual limit factors
ANNUAL_LIMIT_FACTORS = {
    5000: 0.75,
    7500: 0.85,
    10000: 1.00,   # Standard
    15000: 1.15,
    20000: 1.25,
    30000: 1.40,
    50000: 1.60,
    100000: 1.90,
    -1: 2.20,      # Unlimited
}

# Add-on pricing
ADDON_WELLNESS = 15.00   # Monthly
ADDON_DENTAL = 12.00     # Monthly


# ==================== COVERAGE DETAILS ====================

COVERAGE_DETAILS = {
    "basic": {
        "name": "Basic Coverage",
        "reimbursement_rate": 70,
        "includes": [
            "Accidents",
            "Illnesses",
            "Emergency care",
            "Hospitalization",
        ],
        "excludes": [
            "Wellness exams",
            "Vaccinations",
            "Dental care",
            "Pre-existing conditions",
            "Behavioral therapy",
        ],
        "waiting_period_accident": 3,
        "waiting_period_illness": 14,
    },
    "standard": {
        "name": "Standard Coverage",
        "reimbursement_rate": 80,
        "includes": [
            "Accidents",
            "Illnesses",
            "Emergency care",
            "Hospitalization",
            "Diagnostic tests",
            "Surgery",
            "Medications",
            "Specialist visits",
        ],
        "excludes": [
            "Wellness exams",
            "Vaccinations",
            "Pre-existing conditions",
        ],
        "waiting_period_accident": 2,
        "waiting_period_illness": 14,
    },
    "premium": {
        "name": "Premium Coverage",
        "reimbursement_rate": 90,
        "includes": [
            "All Standard Coverage",
            "Alternative therapies",
            "Rehabilitation",
            "Behavioral therapy",
            "Hereditary conditions",
            "Chronic conditions",
        ],
        "excludes": [
            "Pre-existing conditions",
            "Cosmetic procedures",
        ],
        "waiting_period_accident": 0,
        "waiting_period_illness": 14,
    },
    "elite": {
        "name": "Elite Coverage",
        "reimbursement_rate": 100,
        "includes": [
            "All Premium Coverage",
            "Wellness exams (annual)",
            "Vaccinations",
            "Dental cleaning (annual)",
            "Microchipping",
            "Lost pet advertising",
            "Third-party liability",
        ],
        "excludes": [
            "Pre-existing conditions",
        ],
        "waiting_period_accident": 0,
        "waiting_period_illness": 7,
    },
}


# ==================== BREED DATA ====================

DOG_BREEDS = [
    {"name": "French Bulldog", "risk_level": "high", "common_issues": ["BOAS", "IVDD", "Allergies"]},
    {"name": "English Bulldog", "risk_level": "high", "common_issues": ["BOAS", "Skin infections", "Hip dysplasia"]},
    {"name": "Labrador Retriever", "risk_level": "medium", "common_issues": ["Hip dysplasia", "Obesity", "Ear infections"]},
    {"name": "Golden Retriever", "risk_level": "medium", "common_issues": ["Cancer", "Hip dysplasia", "Heart disease"]},
    {"name": "German Shepherd", "risk_level": "high", "common_issues": ["Hip dysplasia", "Bloat", "Degenerative myelopathy"]},
    {"name": "Poodle", "risk_level": "low", "common_issues": ["Eye problems", "Hip dysplasia", "Skin issues"]},
    {"name": "Beagle", "risk_level": "low", "common_issues": ["Epilepsy", "Hypothyroidism", "Eye problems"]},
    {"name": "Rottweiler", "risk_level": "high", "common_issues": ["Hip dysplasia", "Heart problems", "Cancer"]},
    {"name": "Yorkshire Terrier", "risk_level": "medium", "common_issues": ["Dental disease", "Luxating patella", "Tracheal collapse"]},
    {"name": "Boxer", "risk_level": "high", "common_issues": ["Cancer", "Heart conditions", "Hip dysplasia"]},
    {"name": "Dachshund", "risk_level": "medium", "common_issues": ["IVDD", "Obesity", "Dental disease"]},
    {"name": "Great Dane", "risk_level": "high", "common_issues": ["Bloat", "Heart disease", "Hip dysplasia"]},
    {"name": "Siberian Husky", "risk_level": "medium", "common_issues": ["Eye problems", "Hip dysplasia", "Autoimmune disorders"]},
    {"name": "Cavalier King Charles Spaniel", "risk_level": "high", "common_issues": ["MVD", "Syringomyelia", "Eye problems"]},
    {"name": "Doberman Pinscher", "risk_level": "high", "common_issues": ["DCM", "Hip dysplasia", "Von Willebrand disease"]},
    {"name": "Shih Tzu", "risk_level": "medium", "common_issues": ["Eye problems", "Breathing issues", "Dental disease"]},
    {"name": "Boston Terrier", "risk_level": "high", "common_issues": ["BOAS", "Eye problems", "Luxating patella"]},
    {"name": "Pug", "risk_level": "high", "common_issues": ["BOAS", "Eye problems", "Skin fold infections"]},
    {"name": "Chihuahua", "risk_level": "low", "common_issues": ["Dental disease", "Luxating patella", "Heart problems"]},
    {"name": "Australian Shepherd", "risk_level": "low", "common_issues": ["Hip dysplasia", "Eye problems", "Epilepsy"]},
    {"name": "Border Collie", "risk_level": "low", "common_issues": ["Hip dysplasia", "Eye problems", "Epilepsy"]},
    {"name": "Mixed Breed Dog", "risk_level": "low", "common_issues": ["Varies by genetics"]},
]

CAT_BREEDS = [
    {"name": "Persian", "risk_level": "high", "common_issues": ["PKD", "Breathing problems", "Eye problems"]},
    {"name": "Maine Coon", "risk_level": "medium", "common_issues": ["HCM", "Hip dysplasia", "Spinal muscular atrophy"]},
    {"name": "Ragdoll", "risk_level": "medium", "common_issues": ["HCM", "Bladder stones", "Eye problems"]},
    {"name": "British Shorthair", "risk_level": "medium", "common_issues": ["HCM", "PKD", "Obesity"]},
    {"name": "Siamese", "risk_level": "medium", "common_issues": ["Respiratory issues", "Eye problems", "Dental disease"]},
    {"name": "Bengal", "risk_level": "medium", "common_issues": ["HCM", "PRA", "Luxating patella"]},
    {"name": "Sphynx", "risk_level": "high", "common_issues": ["HCM", "Skin problems", "Dental disease"]},
    {"name": "Scottish Fold", "risk_level": "high", "common_issues": ["Osteochondrodysplasia", "HCM", "PKD"]},
    {"name": "Exotic Shorthair", "risk_level": "high", "common_issues": ["PKD", "Breathing problems", "Eye problems"]},
    {"name": "Abyssinian", "risk_level": "low", "common_issues": ["PRA", "PKD", "Gingivitis"]},
    {"name": "Domestic Shorthair", "risk_level": "low", "common_issues": ["Varies by genetics"]},
    {"name": "Domestic Longhair", "risk_level": "low", "common_issues": ["Varies by genetics"]},
    {"name": "Mixed Breed Cat", "risk_level": "low", "common_issues": ["Varies by genetics"]},
]


# ==================== HELPER FUNCTIONS ====================

def get_base_rate(zip_code: str) -> float:
    """Get base rate for zip code."""
    prefix = zip_code[:3]
    return BASE_RATES.get(prefix, DEFAULT_BASE_RATE)


def get_species_factor(species: str) -> float:
    """Get species factor."""
    return SPECIES_FACTORS.get(species.lower(), 1.0)


def get_breed_factor(breed: str) -> float:
    """Get breed risk factor."""
    return BREED_FACTORS.get(breed, DEFAULT_BREED_FACTOR)


def get_age_factor(species: str, age: int) -> float:
    """Get age-based risk factor."""
    if species.lower() == "dog":
        factors = DOG_AGE_FACTORS
        max_age = 14
    else:
        factors = CAT_AGE_FACTORS
        max_age = 15

    if age > max_age:
        age = max_age
    return factors.get(age, 1.0)


def get_coverage_factor(level: str) -> float:
    """Get coverage level multiplier."""
    return COVERAGE_MULTIPLIERS.get(level.lower(), 1.0)


def get_deductible_factor(deductible: int) -> float:
    """Get deductible discount factor."""
    # Find closest deductible tier
    tiers = sorted(DEDUCTIBLE_DISCOUNTS.keys())
    for i, tier in enumerate(tiers):
        if deductible <= tier:
            return DEDUCTIBLE_DISCOUNTS[tier]
    return DEDUCTIBLE_DISCOUNTS[tiers[-1]]


def get_limit_factor(limit: int) -> float:
    """Get annual limit factor."""
    tiers = sorted([k for k in ANNUAL_LIMIT_FACTORS.keys() if k > 0])
    for tier in tiers:
        if limit <= tier:
            return ANNUAL_LIMIT_FACTORS[tier]
    return ANNUAL_LIMIT_FACTORS[tiers[-1]]


def calculate_discounts(quote_request: QuoteRequest) -> List[Dict[str, Any]]:
    """Calculate applicable discounts."""
    discounts = []

    # Multi-pet discount (would need additional info)
    # For demo, we'll skip this

    # Annual pay discount
    discounts.append({
        "name": "Pay Annually",
        "type": "optional",
        "percent": 5.0,
        "description": "Save 5% when you pay annually"
    })

    # Microchip discount
    discounts.append({
        "name": "Microchip Discount",
        "type": "optional",
        "percent": 5.0,
        "description": "5% off if your pet is microchipped"
    })

    return discounts


def round_premium(amount: float) -> float:
    """Round premium to 2 decimal places."""
    return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# ==================== ENDPOINTS ====================

@router.get("/coverages")
async def get_coverages() -> Dict[str, Any]:
    """
    Get all available coverage levels and their details.
    Used by frontend to display coverage options.
    """
    return {
        "coverages": [
            {
                "level": level,
                **details
            }
            for level, details in COVERAGE_DETAILS.items()
        ]
    }


@router.get("/breeds")
async def get_breeds(species: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all breeds with risk levels and common health issues.
    Optionally filter by species.
    """
    result = {"breeds": []}

    if species is None or species.lower() == "dog":
        result["breeds"].extend([{**b, "species": "dog"} for b in DOG_BREEDS])

    if species is None or species.lower() == "cat":
        result["breeds"].extend([{**b, "species": "cat"} for b in CAT_BREEDS])

    return result


@router.get("/factors")
async def get_all_factors() -> Dict[str, Any]:
    """
    Get all rating factors for transparency/debugging.
    """
    return {
        "species_factors": SPECIES_FACTORS,
        "coverage_multipliers": COVERAGE_MULTIPLIERS,
        "deductible_discounts": DEDUCTIBLE_DISCOUNTS,
        "annual_limit_factors": ANNUAL_LIMIT_FACTORS,
        "addons": {
            "wellness": {"monthly": ADDON_WELLNESS},
            "dental": {"monthly": ADDON_DENTAL}
        }
    }


@router.get("/factors/{factor_type}")
async def get_factor_by_type(factor_type: str) -> Dict[str, Any]:
    """
    Get specific rating factor type.
    Valid types: species, breed, age, coverage, deductible, limit
    """
    factor_type = factor_type.lower()

    if factor_type == "species":
        return {"factor_type": "species", "factors": SPECIES_FACTORS}
    elif factor_type == "breed":
        return {"factor_type": "breed", "factors": BREED_FACTORS}
    elif factor_type == "age":
        return {
            "factor_type": "age",
            "dog_factors": DOG_AGE_FACTORS,
            "cat_factors": CAT_AGE_FACTORS
        }
    elif factor_type == "coverage":
        return {"factor_type": "coverage", "factors": COVERAGE_MULTIPLIERS}
    elif factor_type == "deductible":
        return {"factor_type": "deductible", "factors": DEDUCTIBLE_DISCOUNTS}
    elif factor_type == "limit":
        return {"factor_type": "limit", "factors": ANNUAL_LIMIT_FACTORS}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown factor type: {factor_type}. Valid types: species, breed, age, coverage, deductible, limit"
        )


@router.post("/quote")
async def calculate_quote(request: QuoteRequest) -> QuoteResponse:
    """
    Calculate insurance quote based on pet details and coverage options.

    The quote calculation applies these factors:
    1. Base rate (by location/zip code)
    2. Species factor (dog vs cat)
    3. Breed risk factor
    4. Age factor
    5. Coverage level multiplier
    6. Deductible discount
    7. Annual limit factor
    8. Add-on pricing (wellness, dental)
    """
    # Get base rate
    base_rate = get_base_rate(request.zip_code)

    # Calculate factors
    species_factor = get_species_factor(request.species.value)
    breed_factor = get_breed_factor(request.breed)
    age_factor = get_age_factor(request.species.value, request.age_years)
    coverage_factor = get_coverage_factor(request.coverage_level.value)
    deductible_factor = get_deductible_factor(request.deductible)
    limit_factor = get_limit_factor(request.annual_limit)

    # Calculate base premium
    monthly_premium = base_rate
    monthly_premium *= species_factor
    monthly_premium *= breed_factor
    monthly_premium *= age_factor
    monthly_premium *= coverage_factor
    monthly_premium *= deductible_factor
    monthly_premium *= limit_factor

    # Add wellness addon
    if request.include_wellness:
        monthly_premium += ADDON_WELLNESS

    # Add dental addon
    if request.include_dental:
        monthly_premium += ADDON_DENTAL

    # Get discounts
    discounts = calculate_discounts(request)
    total_discount = sum(d["percent"] for d in discounts if d["type"] == "applied")

    # Round premium
    monthly_premium = round_premium(monthly_premium)
    annual_premium = round_premium(monthly_premium * 12)

    # Get coverage details
    coverage_info = COVERAGE_DETAILS.get(request.coverage_level.value, COVERAGE_DETAILS["standard"])

    # Calculate dates
    from datetime import datetime, timedelta
    today = datetime.now().date()
    effective_date = today + timedelta(days=1)
    quote_valid = today + timedelta(days=30)

    return QuoteResponse(
        monthly_premium=monthly_premium,
        annual_premium=annual_premium,
        deductible=request.deductible,
        annual_limit=request.annual_limit,
        coverage_level=request.coverage_level.value,
        coverage_details={
            "name": coverage_info["name"],
            "reimbursement_rate": coverage_info["reimbursement_rate"],
            "includes": coverage_info["includes"],
            "excludes": coverage_info["excludes"],
            "waiting_periods": {
                "accident_days": coverage_info["waiting_period_accident"],
                "illness_days": coverage_info["waiting_period_illness"]
            },
            "addons_included": {
                "wellness": request.include_wellness,
                "dental": request.include_dental
            }
        },
        factors_applied={
            "base_rate": base_rate,
            "species": species_factor,
            "breed": breed_factor,
            "age": age_factor,
            "coverage": coverage_factor,
            "deductible": deductible_factor,
            "annual_limit": limit_factor
        },
        discounts_applied=discounts,
        total_discount_percent=total_discount,
        effective_date=effective_date.isoformat(),
        quote_valid_until=quote_valid.isoformat()
    )


@router.post("/compare")
async def compare_coverage_levels(request: CompareRequest) -> Dict[str, Any]:
    """
    Compare quotes across all coverage levels for the same pet.
    Helps customers choose the right coverage.
    """
    comparisons = []

    for level in CoverageLevel:
        quote_request = QuoteRequest(
            species=request.species,
            breed=request.breed,
            age_years=request.age_years,
            zip_code=request.zip_code,
            coverage_level=level,
            deductible=500,  # Standard deductible for comparison
            annual_limit=10000,  # Standard limit for comparison
        )

        quote = await calculate_quote(quote_request)

        coverage_info = COVERAGE_DETAILS[level.value]
        comparisons.append({
            "level": level.value,
            "name": coverage_info["name"],
            "monthly_premium": quote.monthly_premium,
            "annual_premium": quote.annual_premium,
            "reimbursement_rate": coverage_info["reimbursement_rate"],
            "key_features": coverage_info["includes"][:4],  # Top 4 features
            "waiting_periods": {
                "accident": coverage_info["waiting_period_accident"],
                "illness": coverage_info["waiting_period_illness"]
            }
        })

    return {
        "pet_info": {
            "species": request.species.value,
            "breed": request.breed,
            "age_years": request.age_years,
            "zip_code": request.zip_code
        },
        "comparison_basis": {
            "deductible": 500,
            "annual_limit": 10000
        },
        "quotes": comparisons,
        "recommendation": _get_recommendation(request.age_years, request.breed)
    }


def _get_recommendation(age: int, breed: str) -> Dict[str, str]:
    """Generate coverage recommendation based on pet profile."""
    breed_factor = get_breed_factor(breed)

    if age >= 8 or breed_factor >= 1.5:
        return {
            "level": "premium",
            "reason": "Based on your pet's age and breed, we recommend Premium coverage for comprehensive protection against higher-risk conditions."
        }
    elif age >= 5 or breed_factor >= 1.2:
        return {
            "level": "standard",
            "reason": "Standard coverage provides excellent protection for your pet's current life stage and breed profile."
        }
    else:
        return {
            "level": "basic",
            "reason": "Basic coverage is a cost-effective option for younger, healthy pets with lower breed-specific risks."
        }
