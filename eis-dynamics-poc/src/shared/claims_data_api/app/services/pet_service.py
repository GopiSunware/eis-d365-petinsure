"""
PetService - Pet registry and medical history.
5 endpoints for pet data access.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.data_loader import get_data_store

router = APIRouter()

# Breed risk data
BREED_RISKS = {
    "French Bulldog": {
        "conditions": ["IVDD", "Brachycephalic Syndrome", "Allergies", "Hip Dysplasia"],
        "risk_multipliers": {"IVDD": 10.4, "respiratory": 5.0, "allergies": 3.0},
        "avg_lifespan": 10,
        "avg_annual_cost": 1500
    },
    "German Shepherd": {
        "conditions": ["Hip Dysplasia", "Degenerative Myelopathy", "Bloat"],
        "risk_multipliers": {"hip_dysplasia": 5.0, "bloat": 3.0},
        "avg_lifespan": 11,
        "avg_annual_cost": 1200
    },
    "Labrador Retriever": {
        "conditions": ["Hip Dysplasia", "Obesity", "Ear Infections"],
        "risk_multipliers": {"hip_dysplasia": 2.5, "obesity": 2.0},
        "avg_lifespan": 12,
        "avg_annual_cost": 900
    },
    "Dachshund": {
        "conditions": ["IVDD", "Obesity", "Dental Issues"],
        "risk_multipliers": {"IVDD": 8.0, "dental": 2.0},
        "avg_lifespan": 14,
        "avg_annual_cost": 800
    },
    "Golden Retriever": {
        "conditions": ["Cancer", "Hip Dysplasia", "Heart Disease"],
        "risk_multipliers": {"cancer": 3.5, "hip_dysplasia": 2.0},
        "avg_lifespan": 11,
        "avg_annual_cost": 1100
    },
    "Bulldog": {
        "conditions": ["Brachycephalic Syndrome", "Skin Issues", "Hip Dysplasia"],
        "risk_multipliers": {"respiratory": 6.0, "skin": 3.0},
        "avg_lifespan": 8,
        "avg_annual_cost": 1800
    },
    "Domestic Shorthair": {
        "conditions": ["Dental Disease", "Obesity", "Diabetes"],
        "risk_multipliers": {"dental": 1.5, "diabetes": 1.2},
        "avg_lifespan": 15,
        "avg_annual_cost": 400
    },
    "Maine Coon": {
        "conditions": ["Hypertrophic Cardiomyopathy", "Hip Dysplasia"],
        "risk_multipliers": {"heart": 3.0, "hip_dysplasia": 2.0},
        "avg_lifespan": 13,
        "avg_annual_cost": 600
    },
}


@router.get("/")
async def list_pets(
    species: Optional[str] = None,
    customer_id: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """List all pets with optional filters."""
    store = get_data_store()
    pets = store.get_pets()

    if species:
        pets = [p for p in pets if p.get("species", "").lower() == species.lower()]
    if customer_id:
        pets = store.get_pets_by_customer(customer_id)

    return {
        "count": len(pets[:limit]),
        "total": len(pets),
        "pets": pets[:limit]
    }


@router.get("/{pet_id}")
async def get_pet_profile(pet_id: str) -> Dict[str, Any]:
    """
    Get pet details with enriched data.
    LLM Tool: get_pet_profile(pet_id)
    """
    store = get_data_store()
    pet = store.get_pet(pet_id)

    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet {pet_id} not found")

    # Get related data
    customer = store.get_customer(pet.get("customer_id", ""))
    policies = store.get_policies_by_pet(pet_id)
    claims = store.get_claims_by_pet(pet_id)

    # Calculate age
    dob = datetime.fromisoformat(pet.get("date_of_birth", "2020-01-01"))
    age_years = (datetime.now() - dob).days / 365

    # Get breed risks
    breed = pet.get("breed", "")
    breed_risk = BREED_RISKS.get(breed, {})

    return {
        "pet": pet,
        "age_years": round(age_years, 1),
        "owner_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}" if customer else None,
        "active_policy": any(p.get("status") == "active" for p in policies),
        "total_claims": len(claims),
        "total_claimed": sum(c.get("claim_amount", 0) for c in claims),
        "breed_risk_info": breed_risk if breed_risk else None
    }


@router.get("/{pet_id}/medical-history")
async def get_medical_history(pet_id: str) -> Dict[str, Any]:
    """
    Get all medical records for a pet.
    LLM Tool: get_medical_history(pet_id)
    """
    store = get_data_store()
    pet = store.get_pet(pet_id)

    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet {pet_id} not found")

    claims = store.get_claims_by_pet(pet_id)

    # Sort by date
    claims.sort(key=lambda x: x.get("service_date", ""), reverse=True)

    # Build medical history from claims
    medical_events = []
    for claim in claims:
        medical_events.append({
            "date": claim.get("service_date"),
            "type": claim.get("claim_category"),
            "diagnosis_code": claim.get("diagnosis_code"),
            "diagnosis": claim.get("diagnosis_description"),
            "treatment": claim.get("treatment_notes"),
            "provider_id": claim.get("provider_id"),
            "claim_id": claim.get("claim_id"),
            "amount": claim.get("claim_amount")
        })

    # Add pre-existing conditions
    pre_existing = pet.get("pre_existing_conditions", [])

    return {
        "pet_id": pet_id,
        "pet_name": pet.get("name"),
        "species": pet.get("species"),
        "breed": pet.get("breed"),
        "pre_existing_conditions": pre_existing,
        "vaccination_status": pet.get("vaccination_status"),
        "total_medical_events": len(medical_events),
        "medical_history": medical_events
    }


@router.get("/{pet_id}/conditions")
async def get_pre_existing_conditions(pet_id: str) -> Dict[str, Any]:
    """
    List pre-existing conditions for a pet.
    LLM Tool: get_pre_existing_conditions(pet_id)
    """
    store = get_data_store()
    pet = store.get_pet(pet_id)

    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet {pet_id} not found")

    conditions = pet.get("pre_existing_conditions", [])

    # Check policies for exclusions
    policies = store.get_policies_by_pet(pet_id)
    excluded_codes = []
    for policy in policies:
        for exclusion in policy.get("exclusions", []):
            excluded_codes.extend(exclusion.get("diagnosis_codes", []))

    return {
        "pet_id": pet_id,
        "pet_name": pet.get("name"),
        "conditions": conditions,
        "condition_count": len(conditions),
        "excluded_diagnosis_codes": list(set(excluded_codes)),
        "has_exclusions": len(excluded_codes) > 0
    }


@router.get("/breed-risks/{breed}")
async def get_breed_risks(breed: str) -> Dict[str, Any]:
    """
    Get breed-specific health risks.
    LLM Tool: get_breed_risks(breed)
    """
    # Try exact match first
    risk_info = BREED_RISKS.get(breed)

    if not risk_info:
        # Try case-insensitive match
        for b, info in BREED_RISKS.items():
            if b.lower() == breed.lower():
                risk_info = info
                breed = b
                break

    if not risk_info:
        return {
            "breed": breed,
            "found": False,
            "message": "Breed not in risk database. Using general risk profile.",
            "common_conditions": ["General wellness issues"],
            "risk_multipliers": {},
            "average_lifespan_years": 12,
            "average_annual_vet_cost": 700
        }

    return {
        "breed": breed,
        "found": True,
        "common_conditions": risk_info.get("conditions", []),
        "risk_multipliers": risk_info.get("risk_multipliers", {}),
        "average_lifespan_years": risk_info.get("avg_lifespan", 12),
        "average_annual_vet_cost": risk_info.get("avg_annual_cost", 700)
    }


@router.get("/{pet_id}/vaccinations")
async def check_vaccination_status(pet_id: str) -> Dict[str, Any]:
    """
    Get vaccination records for a pet.
    LLM Tool: check_vaccination_status(pet_id)
    """
    store = get_data_store()
    pet = store.get_pet(pet_id)

    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet {pet_id} not found")

    status = pet.get("vaccination_status", "unknown")

    # In production, would have detailed vaccination records
    # For demo, generate based on status
    vaccinations = []
    if status == "up_to_date":
        if pet.get("species") == "dog":
            vaccinations = [
                {"vaccine": "Rabies", "status": "current", "next_due": "2025-06-01"},
                {"vaccine": "DHPP", "status": "current", "next_due": "2025-03-01"},
                {"vaccine": "Bordetella", "status": "current", "next_due": "2025-01-01"},
            ]
        else:
            vaccinations = [
                {"vaccine": "Rabies", "status": "current", "next_due": "2025-06-01"},
                {"vaccine": "FVRCP", "status": "current", "next_due": "2025-03-01"},
            ]
    elif status == "overdue":
        vaccinations = [
            {"vaccine": "Rabies", "status": "overdue", "next_due": "2024-06-01"},
        ]

    return {
        "pet_id": pet_id,
        "pet_name": pet.get("name"),
        "overall_status": status,
        "is_current": status == "up_to_date",
        "vaccinations": vaccinations
    }
