"""
PolicyService - Policy management functions.
6 endpoints for policy data access and coverage checks.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

from app.data_loader import get_data_store

router = APIRouter()


@router.get("/")
async def list_policies(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    pet_id: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """List all policies with optional filters."""
    store = get_data_store()
    policies = store.get_policies()

    if status:
        policies = [p for p in policies if p.get("status") == status]
    if customer_id:
        policies = [p for p in policies if p.get("customer_id") == customer_id]
    if pet_id:
        policies = [p for p in policies if p.get("pet_id") == pet_id]

    return {
        "count": len(policies[:limit]),
        "total": len(policies),
        "policies": policies[:limit]
    }


@router.get("/{policy_id}")
async def get_policy(policy_id: str) -> Dict[str, Any]:
    """
    Get full policy details.
    LLM Tool: get_policy(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    # Enrich with related data
    customer = store.get_customer(policy.get("customer_id", ""))
    pet = store.get_pet(policy.get("pet_id", ""))
    claims = store.get_claims_by_policy(policy_id)

    return {
        "policy": policy,
        "customer_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}" if customer else None,
        "pet_name": pet.get("name") if pet else None,
        "pet_breed": pet.get("breed") if pet else None,
        "total_claims": len(claims),
        "total_paid": sum(c.get("paid_amount", 0) for c in claims)
    }


@router.get("/{policy_id}/coverage/{diagnosis_code}")
async def check_coverage(policy_id: str, diagnosis_code: str) -> Dict[str, Any]:
    """
    Check if a diagnosis code is covered under the policy.
    LLM Tool: check_coverage(policy_id, diagnosis_code)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    # Check exclusions
    exclusions = policy.get("exclusions", [])
    for exclusion in exclusions:
        if diagnosis_code in exclusion.get("diagnosis_codes", []):
            return {
                "is_covered": False,
                "diagnosis_code": diagnosis_code,
                "coverage_percentage": 0,
                "exclusion_reason": exclusion.get("description"),
                "exclusion_type": exclusion.get("exclusion_type"),
                "waiting_period_satisfied": True,
                "notes": "This diagnosis is excluded from coverage"
            }

    # Check waiting periods
    waiting = policy.get("waiting_period", {})
    effective_date = datetime.fromisoformat(policy.get("effective_date", "2024-01-01"))
    days_since_effective = (datetime.now() - effective_date).days

    # Get diagnosis category
    medical_code = store.get_medical_code(diagnosis_code)
    category = medical_code.get("category", "illness") if medical_code else "illness"

    waiting_satisfied = True
    waiting_reason = None

    if category == "illness" and days_since_effective < waiting.get("illness_days", 14):
        waiting_satisfied = False
        waiting_reason = f"Illness waiting period ({waiting.get('illness_days', 14)} days) not satisfied"
    elif category == "accident" and days_since_effective < waiting.get("accident_days", 14):
        waiting_satisfied = False
        waiting_reason = f"Accident waiting period ({waiting.get('accident_days', 14)} days) not satisfied"
    elif category == "surgery" and days_since_effective < waiting.get("orthopedic_days", 180):
        waiting_satisfied = False
        waiting_reason = f"Orthopedic waiting period ({waiting.get('orthopedic_days', 180)} days) not satisfied"

    return {
        "is_covered": waiting_satisfied,
        "diagnosis_code": diagnosis_code,
        "coverage_percentage": policy.get("reimbursement_percentage", 80) if waiting_satisfied else 0,
        "exclusion_reason": waiting_reason if not waiting_satisfied else None,
        "waiting_period_satisfied": waiting_satisfied,
        "plan_type": policy.get("plan_type"),
        "notes": f"Coverage under {policy.get('plan_name')} plan" if waiting_satisfied else waiting_reason
    }


@router.get("/{policy_id}/exclusions")
async def get_exclusions(policy_id: str) -> Dict[str, Any]:
    """
    List all policy exclusions.
    LLM Tool: get_exclusions(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    exclusions = policy.get("exclusions", [])

    # Also check pet's pre-existing conditions
    pet = store.get_pet(policy.get("pet_id", ""))
    pre_existing = []
    if pet:
        for condition in pet.get("pre_existing_conditions", []):
            if condition.get("is_excluded"):
                pre_existing.append({
                    "exclusion_type": "pre_existing",
                    "description": condition.get("condition_name"),
                    "diagnosis_codes": [condition.get("diagnosis_code")] if condition.get("diagnosis_code") else [],
                    "diagnosis_date": condition.get("diagnosis_date"),
                    "is_permanent": True
                })

    return {
        "policy_id": policy_id,
        "policy_exclusions": exclusions,
        "pre_existing_exclusions": pre_existing,
        "total_exclusions": len(exclusions) + len(pre_existing)
    }


@router.get("/{policy_id}/limits")
async def check_limits(policy_id: str) -> Dict[str, Any]:
    """
    Get remaining coverage limits.
    LLM Tool: check_limits(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    coverage = policy.get("coverage_limit", {})
    claims = store.get_claims_by_policy(policy_id)

    # Calculate actual usage from claims
    current_year = datetime.now().year
    year_claims = [
        c for c in claims
        if c.get("service_date", "").startswith(str(current_year))
        and c.get("status") in ["paid", "approved"]
    ]
    actual_used = sum(c.get("paid_amount", 0) for c in year_claims)

    annual_limit = coverage.get("annual_limit", 10000)

    return {
        "policy_id": policy_id,
        "annual_limit": annual_limit,
        "per_incident_limit": coverage.get("per_incident_limit"),
        "lifetime_limit": coverage.get("lifetime_limit"),
        "used_this_year": actual_used,
        "remaining_this_year": max(0, annual_limit - actual_used),
        "is_within_limits": actual_used < annual_limit,
        "deductible": policy.get("annual_deductible", 0),
        "deductible_met": policy.get("deductible_met", 0),
        "claims_this_year": len(year_claims)
    }


@router.get("/{policy_id}/waiting-periods")
async def get_waiting_periods(policy_id: str) -> Dict[str, Any]:
    """
    Get waiting period status.
    LLM Tool: get_waiting_periods(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    waiting = policy.get("waiting_period", {})
    effective_date = datetime.fromisoformat(policy.get("effective_date", "2024-01-01"))
    days_since_effective = (datetime.now() - effective_date).days

    accident_days = waiting.get("accident_days", 14)
    illness_days = waiting.get("illness_days", 14)
    orthopedic_days = waiting.get("orthopedic_days", 180)
    cancer_days = waiting.get("cancer_days", 30)

    return {
        "policy_id": policy_id,
        "effective_date": policy.get("effective_date"),
        "days_since_effective": days_since_effective,
        "waiting_periods": {
            "accident": {
                "required_days": accident_days,
                "satisfied": days_since_effective >= accident_days,
                "days_remaining": max(0, accident_days - days_since_effective)
            },
            "illness": {
                "required_days": illness_days,
                "satisfied": days_since_effective >= illness_days,
                "days_remaining": max(0, illness_days - days_since_effective)
            },
            "orthopedic": {
                "required_days": orthopedic_days,
                "satisfied": days_since_effective >= orthopedic_days,
                "days_remaining": max(0, orthopedic_days - days_since_effective)
            },
            "cancer": {
                "required_days": cancer_days,
                "satisfied": days_since_effective >= cancer_days,
                "days_remaining": max(0, cancer_days - days_since_effective)
            }
        },
        "all_satisfied": days_since_effective >= max(accident_days, illness_days, orthopedic_days, cancer_days)
    }


@router.get("/{policy_id}/history")
async def get_policy_history(policy_id: str) -> Dict[str, Any]:
    """
    Get policy changes and renewal history.
    LLM Tool: get_policy_history(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    claims = store.get_claims_by_policy(policy_id)

    # Build history events
    events = [
        {
            "date": policy.get("effective_date"),
            "event_type": "policy_created",
            "description": f"Policy created with {policy.get('plan_name')} plan"
        }
    ]

    # Add renewal events
    for i in range(policy.get("renewal_count", 0)):
        effective = datetime.fromisoformat(policy.get("effective_date"))
        renewal_date = (effective + timedelta(days=365 * (i + 1))).date()
        events.append({
            "date": renewal_date.isoformat(),
            "event_type": "renewal",
            "description": f"Policy renewed (renewal #{i + 1})"
        })

    # Add cancellation if applicable
    if policy.get("cancellation_date"):
        events.append({
            "date": policy.get("cancellation_date"),
            "event_type": "cancellation",
            "description": "Policy cancelled"
        })

    # Sort by date
    events.sort(key=lambda x: x["date"], reverse=True)

    return {
        "policy_id": policy_id,
        "policy_number": policy.get("policy_number"),
        "current_status": policy.get("status"),
        "renewal_count": policy.get("renewal_count", 0),
        "events": events,
        "claims_summary": {
            "total_claims": len(claims),
            "total_amount": sum(c.get("claim_amount", 0) for c in claims),
            "total_paid": sum(c.get("paid_amount", 0) for c in claims)
        }
    }
