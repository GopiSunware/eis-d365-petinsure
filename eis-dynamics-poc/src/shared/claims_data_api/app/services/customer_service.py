"""
CustomerService - Customer 360 functions.
6 endpoints for customer data and analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.data_loader import get_data_store

router = APIRouter()


@router.get("/")
async def list_customers(
    segment: Optional[str] = None,
    risk_tier: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """List all customers with optional filters."""
    store = get_data_store()
    customers = store.get_customers()

    if segment:
        customers = [c for c in customers if c.get("segment") == segment]
    if risk_tier:
        customers = [c for c in customers if c.get("risk_tier") == risk_tier]

    return {
        "count": len(customers[:limit]),
        "total": len(customers),
        "customers": customers[:limit]
    }


@router.get("/{customer_id}")
async def get_customer(customer_id: str) -> Dict[str, Any]:
    """
    Get customer profile with summary info.
    LLM Tool: get_customer(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Get related data
    pets = store.get_pets_by_customer(customer_id)
    policies = store.get_policies_by_customer(customer_id)
    claims = store.get_claims_by_customer(customer_id)

    # Calculate tenure
    customer_since = datetime.fromisoformat(customer.get("customer_since", "2024-01-01"))
    tenure_days = (datetime.now() - customer_since).days

    return {
        "customer": customer,
        "tenure_days": tenure_days,
        "tenure_months": tenure_days // 30,
        "pets_count": len(pets),
        "active_policies": len([p for p in policies if p.get("status") == "active"]),
        "total_claims": len(claims),
        "total_paid": sum(c.get("paid_amount", 0) for c in claims),
        "risk_assessment": {
            "tier": customer.get("risk_tier", "low"),
            "segment": customer.get("segment", "standard"),
            "ltv": customer.get("lifetime_value", 0)
        }
    }


@router.get("/{customer_id}/claims")
async def get_claim_history(customer_id: str) -> Dict[str, Any]:
    """
    Get all claims for a customer.
    LLM Tool: get_claim_history(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    claims = store.get_claims_by_customer(customer_id)

    # Sort by date descending
    claims.sort(key=lambda x: x.get("service_date", ""), reverse=True)

    # Calculate stats
    total_claimed = sum(c.get("claim_amount", 0) for c in claims)
    total_paid = sum(c.get("paid_amount", 0) for c in claims)

    # Group by status
    status_breakdown = {}
    for claim in claims:
        status = claim.get("status", "unknown")
        if status not in status_breakdown:
            status_breakdown[status] = {"count": 0, "amount": 0}
        status_breakdown[status]["count"] += 1
        status_breakdown[status]["amount"] += claim.get("claim_amount", 0)

    # Check for fraud patterns
    fraud_claims = [c for c in claims if c.get("fraud_pattern")]

    return {
        "customer_id": customer_id,
        "customer_name": f"{customer.get('first_name')} {customer.get('last_name')}",
        "total_claims": len(claims),
        "total_claimed": total_claimed,
        "total_paid": total_paid,
        "payout_ratio": total_paid / total_claimed if total_claimed > 0 else 0,
        "status_breakdown": status_breakdown,
        "has_fraud_flags": len(fraud_claims) > 0,
        "fraud_claims_count": len(fraud_claims),
        "claims": claims
    }


@router.get("/{customer_id}/ltv")
async def get_lifetime_value(customer_id: str) -> Dict[str, Any]:
    """
    Calculate customer lifetime value.
    LLM Tool: get_lifetime_value(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    policies = store.get_policies_by_customer(customer_id)
    claims = store.get_claims_by_customer(customer_id)
    payments = store.get_payments_by_customer(customer_id)

    # Calculate revenue (premiums)
    premium_payments = [p for p in payments if p.get("payment_type") == "premium"]
    total_premiums = sum(p.get("amount", 0) for p in premium_payments)

    # Calculate costs (claim payouts)
    total_payouts = sum(c.get("paid_amount", 0) for c in claims)

    # Net value
    net_value = total_premiums - total_payouts

    # Calculate tenure
    customer_since = datetime.fromisoformat(customer.get("customer_since", "2024-01-01"))
    tenure_months = (datetime.now() - customer_since).days / 30

    # Monthly metrics
    avg_monthly_premium = total_premiums / max(1, tenure_months)
    avg_monthly_claims = total_payouts / max(1, tenure_months)

    # Loss ratio
    loss_ratio = total_payouts / total_premiums if total_premiums > 0 else 0

    return {
        "customer_id": customer_id,
        "customer_name": f"{customer.get('first_name')} {customer.get('last_name')}",
        "tenure_months": round(tenure_months, 1),
        "total_premiums_paid": total_premiums,
        "total_claims_paid": total_payouts,
        "net_value": net_value,
        "loss_ratio": round(loss_ratio, 3),
        "avg_monthly_premium": round(avg_monthly_premium, 2),
        "avg_monthly_claims": round(avg_monthly_claims, 2),
        "profitability": "profitable" if net_value > 0 else "unprofitable",
        "stored_ltv": customer.get("lifetime_value", 0)
    }


@router.get("/{customer_id}/risk")
async def get_risk_tier(customer_id: str) -> Dict[str, Any]:
    """
    Get customer risk classification with factors.
    LLM Tool: get_risk_tier(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    claims = store.get_claims_by_customer(customer_id)
    pets = store.get_pets_by_customer(customer_id)

    # Calculate risk factors
    risk_factors = []
    risk_score = 0

    # Claims frequency
    if len(claims) > 10:
        risk_factors.append({
            "factor": "high_claims_frequency",
            "description": f"Customer has {len(claims)} claims",
            "impact": 20
        })
        risk_score += 20
    elif len(claims) > 5:
        risk_factors.append({
            "factor": "moderate_claims_frequency",
            "description": f"Customer has {len(claims)} claims",
            "impact": 10
        })
        risk_score += 10

    # Large claims
    large_claims = [c for c in claims if c.get("claim_amount", 0) > 3000]
    if large_claims:
        risk_factors.append({
            "factor": "large_claims",
            "description": f"{len(large_claims)} claims over $3,000",
            "impact": 15
        })
        risk_score += 15

    # Pre-existing conditions
    for pet in pets:
        conditions = pet.get("pre_existing_conditions", [])
        if conditions:
            risk_factors.append({
                "factor": "pre_existing_conditions",
                "description": f"Pet {pet.get('name')} has {len(conditions)} pre-existing condition(s)",
                "impact": 10
            })
            risk_score += 10

    # Fraud flags
    fraud_claims = [c for c in claims if c.get("fraud_pattern")]
    if fraud_claims:
        risk_factors.append({
            "factor": "fraud_indicators",
            "description": f"{len(fraud_claims)} claims with fraud patterns",
            "impact": 40
        })
        risk_score += 40

    # Determine tier
    if risk_score >= 50:
        tier = "critical"
    elif risk_score >= 30:
        tier = "high"
    elif risk_score >= 15:
        tier = "medium"
    else:
        tier = "low"

    return {
        "customer_id": customer_id,
        "customer_name": f"{customer.get('first_name')} {customer.get('last_name')}",
        "risk_tier": tier,
        "risk_score": risk_score,
        "stored_tier": customer.get("risk_tier", "low"),
        "segment": customer.get("segment"),
        "risk_factors": risk_factors,
        "recommendation": "Review recommended" if tier in ["high", "critical"] else "Standard processing"
    }


@router.get("/{customer_id}/communications")
async def get_communication_history(customer_id: str) -> Dict[str, Any]:
    """
    Get past customer interactions.
    LLM Tool: get_communication_history(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # In a real system, this would query a CRM
    # For demo, we generate based on claims
    claims = store.get_claims_by_customer(customer_id)

    communications = []
    for claim in claims[:10]:  # Last 10
        communications.append({
            "date": claim.get("submitted_date"),
            "type": "claim_submission",
            "channel": customer.get("preferred_contact", "email"),
            "subject": f"Claim {claim.get('claim_number')} submitted",
            "status": claim.get("status")
        })
        if claim.get("status") in ["paid", "approved"]:
            communications.append({
                "date": claim.get("updated_at", claim.get("submitted_date")),
                "type": "claim_resolution",
                "channel": "email",
                "subject": f"Claim {claim.get('claim_number')} {claim.get('status')}",
                "status": "sent"
            })

    # Sort by date
    communications.sort(key=lambda x: x.get("date", ""), reverse=True)

    return {
        "customer_id": customer_id,
        "preferred_contact": customer.get("preferred_contact"),
        "marketing_opt_in": customer.get("marketing_opt_in"),
        "total_communications": len(communications),
        "communications": communications[:20]
    }


@router.get("/{customer_id}/household")
async def get_household(customer_id: str) -> Dict[str, Any]:
    """
    Get all pets and policies for customer.
    LLM Tool: get_household(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    pets = store.get_pets_by_customer(customer_id)
    policies = store.get_policies_by_customer(customer_id)

    # Calculate total monthly premium
    active_policies = [p for p in policies if p.get("status") == "active"]
    total_monthly_premium = sum(p.get("monthly_premium", 0) for p in active_policies)

    # Enrich pets with their policies
    pet_details = []
    for pet in pets:
        pet_policies = [p for p in policies if p.get("pet_id") == pet.get("pet_id")]
        pet_claims = store.get_claims_by_pet(pet.get("pet_id", ""))
        pet_details.append({
            "pet": pet,
            "policies": pet_policies,
            "total_claims": len(pet_claims),
            "has_active_policy": any(p.get("status") == "active" for p in pet_policies)
        })

    return {
        "customer_id": customer_id,
        "customer_name": f"{customer.get('first_name')} {customer.get('last_name')}",
        "total_pets": len(pets),
        "total_policies": len(policies),
        "active_policies": len(active_policies),
        "total_monthly_premium": round(total_monthly_premium, 2),
        "household": pet_details
    }
