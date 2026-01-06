"""
MedicalRefService - Medical code reference and benchmarks.
5 endpoints for medical reference data.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.data_loader import get_data_store

router = APIRouter()

# Treatment benchmarks (would come from database in production)
TREATMENT_BENCHMARKS = {
    "Z00.0": {"median": 100, "p25": 75, "p75": 150, "p90": 200, "items": ["Exam fee", "Basic bloodwork"]},
    "Z23": {"median": 125, "p25": 75, "p75": 175, "p90": 250, "items": ["Vaccine administration", "Exam fee"]},
    "K08.3": {"median": 450, "p25": 300, "p75": 650, "p90": 900, "items": ["Dental cleaning", "X-rays", "Anesthesia"]},
    "K59": {"median": 350, "p25": 200, "p75": 500, "p90": 750, "items": ["Exam", "X-rays", "Medications", "Fluids"]},
    "K59.9": {"median": 350, "p25": 200, "p75": 500, "p90": 750, "items": ["Exam", "X-rays", "Medications", "Fluids"]},
    "N39.0": {"median": 275, "p25": 180, "p75": 375, "p90": 500, "items": ["Urinalysis", "Antibiotics", "Exam"]},
    "S83.5": {"median": 4200, "p25": 3200, "p75": 5500, "p90": 6500, "items": ["Surgery", "Anesthesia", "Hospitalization", "X-rays", "Medications"]},
    "G95.89": {"median": 5500, "p25": 4000, "p75": 7500, "p90": 10000, "items": ["MRI", "Surgery", "Hospitalization", "Medications", "Physical therapy"]},
    "T65.8": {"median": 800, "p25": 400, "p75": 1200, "p90": 2500, "items": ["Decontamination", "IV fluids", "Monitoring", "Bloodwork"]},
    "L50.0": {"median": 250, "p25": 150, "p75": 400, "p90": 600, "items": ["Antihistamines", "Exam", "Allergy testing"]},
    "E11.9": {"median": 800, "p25": 500, "p75": 1200, "p90": 2000, "items": ["Glucose testing", "Insulin", "Dietary consult", "Monitoring"]},
}


def _find_medical_code(store, code: str) -> Optional[Dict]:
    """Find medical code with partial matching support (e.g., K59 matches K59.9)."""
    # Try exact match first
    result = store.get_medical_code(code)
    if result:
        return result

    # Try with common suffixes
    for suffix in [".0", ".9", ".89"]:
        result = store.get_medical_code(code + suffix)
        if result:
            return result

    # Try prefix match
    all_codes = store.get_medical_codes()
    for c in all_codes:
        if c.get("code", "").startswith(code):
            return c

    return None


@router.get("/")
async def list_medical_codes(
    category: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """List all medical codes."""
    store = get_data_store()
    codes = store.get_medical_codes()

    if category:
        codes = [c for c in codes if c.get("category", "").lower() == category.lower()]

    return {
        "count": len(codes[:limit]),
        "total": len(codes),
        "codes": codes[:limit]
    }


@router.get("/diagnosis/{code}")
async def validate_diagnosis_code(code: str) -> Dict[str, Any]:
    """
    Validate a diagnosis code and get details.
    LLM Tool: validate_diagnosis_code(code)
    """
    store = get_data_store()
    medical_code = _find_medical_code(store, code)

    if not medical_code:
        return {
            "code": code,
            "valid": False,
            "message": f"Diagnosis code {code} not found in database"
        }

    return {
        "code": code,
        "valid": True,
        "description": medical_code.get("description"),
        "category": medical_code.get("category"),
        "is_chronic": medical_code.get("is_chronic", False),
        "typical_cost_range": {
            "min": medical_code.get("typical_treatment_cost_min"),
            "max": medical_code.get("typical_treatment_cost_max")
        },
        "typical_duration_days": medical_code.get("typical_treatment_duration_days"),
        "related_codes": medical_code.get("related_codes", [])
    }


@router.get("/diagnosis/{code}/benchmarks")
async def get_treatment_benchmarks(code: str) -> Dict[str, Any]:
    """
    Get cost benchmarks for a diagnosis.
    LLM Tool: get_treatment_benchmarks(diagnosis_code)
    """
    store = get_data_store()
    medical_code = _find_medical_code(store, code)

    benchmark = TREATMENT_BENCHMARKS.get(code)

    if not benchmark:
        # Return estimate based on medical code data
        if medical_code:
            min_cost = medical_code.get("typical_treatment_cost_min", 100)
            max_cost = medical_code.get("typical_treatment_cost_max", 500)
            median = (min_cost + max_cost) / 2
            return {
                "diagnosis_code": code,
                "found": False,
                "estimated": True,
                "median_cost": median,
                "percentile_25": min_cost,
                "percentile_75": max_cost,
                "percentile_90": max_cost * 1.5,
                "expected_line_items": ["Exam", "Treatment", "Medications"],
                "note": "Benchmarks estimated from typical cost range"
            }
        return {
            "diagnosis_code": code,
            "found": False,
            "message": "No benchmark data available for this diagnosis code"
        }

    return {
        "diagnosis_code": code,
        "found": True,
        "description": medical_code.get("description") if medical_code else None,
        "median_cost": benchmark["median"],
        "percentile_25": benchmark["p25"],
        "percentile_75": benchmark["p75"],
        "percentile_90": benchmark["p90"],
        "expected_line_items": benchmark["items"]
    }


@router.get("/diagnosis/{code}/treatments")
async def get_typical_treatment(code: str) -> Dict[str, Any]:
    """
    Get typical treatments for a diagnosis.
    LLM Tool: get_typical_treatment(diagnosis_code)
    """
    store = get_data_store()
    medical_code = _find_medical_code(store, code)

    if not medical_code:
        raise HTTPException(status_code=404, detail=f"Diagnosis code {code} not found")

    benchmark = TREATMENT_BENCHMARKS.get(code, {})

    # Map category to treatment approach
    category = medical_code.get("category", "")
    treatment_approach = {
        "preventive": "Routine wellness care - annual exam, vaccinations, preventive screenings",
        "illness": "Diagnosis, medication, follow-up care as needed",
        "emergency": "Immediate stabilization, diagnostic workup, hospitalization if needed",
        "surgery": "Pre-surgical workup, anesthesia, surgical procedure, post-op care",
        "chronic": "Ongoing management with regular monitoring and medication adjustments",
        "dental": "Dental examination, cleaning under anesthesia, extractions if needed",
        "diagnostic": "Testing, imaging, laboratory work to determine diagnosis"
    }.get(category, "Standard veterinary care")

    return {
        "diagnosis_code": code,
        "description": medical_code.get("description"),
        "category": category,
        "is_chronic": medical_code.get("is_chronic", False),
        "typical_treatment_approach": treatment_approach,
        "expected_duration_days": medical_code.get("typical_treatment_duration_days", 1),
        "expected_line_items": benchmark.get("items", ["Exam", "Treatment"]),
        "typical_cost_range": {
            "min": medical_code.get("typical_treatment_cost_min"),
            "max": medical_code.get("typical_treatment_cost_max")
        },
        "follow_up_needed": medical_code.get("is_chronic", False) or category in ["surgery", "chronic"]
    }


@router.get("/diagnosis/{code}/related")
async def check_related_conditions(code: str) -> Dict[str, Any]:
    """
    Get related diagnosis codes.
    LLM Tool: check_related_conditions(diagnosis_code)
    """
    store = get_data_store()
    medical_code = _find_medical_code(store, code)

    if not medical_code:
        raise HTTPException(status_code=404, detail=f"Diagnosis code {code} not found")

    related_codes = medical_code.get("related_codes", [])

    # Get details for related codes
    related_details = []
    for rc in related_codes:
        rc_data = store.get_medical_code(rc)
        if rc_data:
            related_details.append({
                "code": rc,
                "description": rc_data.get("description"),
                "category": rc_data.get("category")
            })

    # Also find codes in same category
    all_codes = store.get_medical_codes()
    same_category = [
        {"code": c.get("code"), "description": c.get("description")}
        for c in all_codes
        if c.get("category") == medical_code.get("category") and c.get("code") != code
    ][:5]

    return {
        "diagnosis_code": code,
        "description": medical_code.get("description"),
        "category": medical_code.get("category"),
        "directly_related": related_details,
        "same_category": same_category,
        "is_pre_existing_risk": medical_code.get("is_chronic", False)
    }


@router.get("/breed-risk/{breed}/{condition}")
async def get_breed_condition_risk(breed: str, condition: str) -> Dict[str, Any]:
    """
    Get breed-specific risk for a condition.
    LLM Tool: get_breed_condition_risk(breed, condition)
    """
    # Breed risk multipliers
    BREED_CONDITION_RISKS = {
        "French Bulldog": {"IVDD": 10.4, "respiratory": 5.0, "allergies": 3.0, "hip_dysplasia": 2.0},
        "German Shepherd": {"hip_dysplasia": 5.0, "bloat": 3.0, "degenerative_myelopathy": 4.0},
        "Labrador Retriever": {"hip_dysplasia": 2.5, "obesity": 2.0, "ear_infections": 2.5},
        "Dachshund": {"IVDD": 8.0, "obesity": 2.0, "dental": 2.0},
        "Bulldog": {"respiratory": 6.0, "skin": 3.0, "hip_dysplasia": 3.0},
        "Golden Retriever": {"cancer": 3.5, "hip_dysplasia": 2.0, "heart": 2.0},
    }

    # Normalize inputs
    breed_lower = breed.lower()
    condition_lower = condition.lower()

    # Find matching breed
    matched_breed = None
    for b in BREED_CONDITION_RISKS.keys():
        if b.lower() == breed_lower or breed_lower in b.lower():
            matched_breed = b
            break

    if not matched_breed:
        return {
            "breed": breed,
            "condition": condition,
            "found": False,
            "risk_multiplier": 1.0,
            "risk_level": "average",
            "note": "Breed not in risk database, using baseline risk"
        }

    risks = BREED_CONDITION_RISKS[matched_breed]

    # Find matching condition
    matched_condition = None
    for c in risks.keys():
        if c.lower() == condition_lower or condition_lower in c.lower():
            matched_condition = c
            break

    if not matched_condition:
        return {
            "breed": matched_breed,
            "condition": condition,
            "found": True,
            "breed_found": True,
            "condition_found": False,
            "risk_multiplier": 1.0,
            "risk_level": "average",
            "note": f"No specific data for {condition} in {matched_breed}"
        }

    multiplier = risks[matched_condition]

    if multiplier >= 5.0:
        risk_level = "very_high"
    elif multiplier >= 3.0:
        risk_level = "high"
    elif multiplier >= 2.0:
        risk_level = "elevated"
    else:
        risk_level = "average"

    return {
        "breed": matched_breed,
        "condition": matched_condition,
        "found": True,
        "risk_multiplier": multiplier,
        "risk_level": risk_level,
        "interpretation": f"{matched_breed} has {multiplier}x the average risk for {matched_condition}",
        "recommendation": "Enhanced scrutiny recommended" if multiplier >= 5.0 else "Standard processing"
    }


@router.get("/search")
async def search_medical_codes(term: str) -> Dict[str, Any]:
    """Search medical codes by term."""
    store = get_data_store()
    results = store.search_medical_codes(term)

    return {
        "query": term,
        "count": len(results),
        "results": results
    }
