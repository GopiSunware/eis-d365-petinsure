"""
BillingService - Billing and reimbursement calculations.
5 endpoints for billing operations.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.data_loader import get_data_store

router = APIRouter()


class ReimbursementRequest(BaseModel):
    """Request for reimbursement calculation."""
    policy_id: str
    claim_amount: float
    diagnosis_code: str
    provider_id: Optional[str] = None
    is_emergency: bool = False


@router.post("/calculate")
async def calculate_reimbursement(request: ReimbursementRequest) -> Dict[str, Any]:
    """
    Calculate reimbursement for a claim.
    LLM Tool: calculate_reimbursement(claim_data, policy_data)
    """
    store = get_data_store()
    policy = store.get_policy(request.policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {request.policy_id} not found")

    # Get policy details
    annual_deductible = policy.get("annual_deductible", 250)
    deductible_met = policy.get("deductible_met", 0)
    reimbursement_pct = policy.get("reimbursement_percentage", 80)
    coverage_limit = policy.get("coverage_limit", {})
    annual_limit = coverage_limit.get("annual_limit", 10000)
    used_this_year = coverage_limit.get("used_this_year", 0)
    remaining_limit = annual_limit - used_this_year

    # Check network status
    network_adjustment = 1.0
    if request.provider_id:
        provider = store.get_provider(request.provider_id)
        if provider and not provider.get("is_in_network"):
            network_adjustment = 0.7  # 30% reduction for out-of-network

    # Calculate deductible
    deductible_remaining = max(0, annual_deductible - deductible_met)
    deductible_applied = min(deductible_remaining, request.claim_amount)
    amount_after_deductible = request.claim_amount - deductible_applied

    # Calculate reimbursement
    covered_amount = amount_after_deductible * (reimbursement_pct / 100) * network_adjustment

    # Apply limit
    final_payout = min(covered_amount, remaining_limit)

    # Build explanation
    explanation_parts = [
        f"Claim amount: ${request.claim_amount:.2f}"
    ]
    if deductible_applied > 0:
        explanation_parts.append(f"Deductible applied: ${deductible_applied:.2f}")
    if network_adjustment < 1.0:
        explanation_parts.append(f"Out-of-network adjustment: {network_adjustment * 100:.0f}%")
    explanation_parts.append(f"Reimbursement rate: {reimbursement_pct}%")
    if final_payout < covered_amount:
        explanation_parts.append(f"Annual limit cap applied")
    explanation_parts.append(f"Final payout: ${final_payout:.2f}")

    return {
        "policy_id": request.policy_id,
        "claim_amount": request.claim_amount,
        "deductible_remaining_before": deductible_remaining,
        "deductible_applied": deductible_applied,
        "amount_after_deductible": amount_after_deductible,
        "reimbursement_percentage": reimbursement_pct,
        "network_adjustment": network_adjustment,
        "covered_amount": covered_amount,
        "annual_limit_remaining": remaining_limit,
        "final_payout": round(final_payout, 2),
        "customer_responsibility": round(request.claim_amount - final_payout, 2),
        "explanation": " | ".join(explanation_parts)
    }


@router.get("/deductible/{policy_id}")
async def check_deductible_status(policy_id: str) -> Dict[str, Any]:
    """
    Check if deductible has been met.
    LLM Tool: check_deductible_status(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    annual_deductible = policy.get("annual_deductible", 250)
    deductible_met = policy.get("deductible_met", 0)

    # Calculate from actual claims this year
    claims = store.get_claims_by_policy(policy_id)
    current_year = datetime.now().year
    year_claims = [
        c for c in claims
        if c.get("service_date", "").startswith(str(current_year))
        and c.get("status") in ["paid", "approved"]
    ]
    actual_deductible_paid = sum(c.get("deductible_applied", 0) for c in year_claims)

    remaining = max(0, annual_deductible - actual_deductible_paid)

    return {
        "policy_id": policy_id,
        "annual_deductible": annual_deductible,
        "amount_met": actual_deductible_paid,
        "remaining": remaining,
        "is_met": remaining == 0,
        "claims_contributing": len(year_claims),
        "next_claim_deductible": remaining
    }


@router.get("/payments/{customer_id}")
async def get_payment_history(customer_id: str) -> Dict[str, Any]:
    """
    Get payment history for a customer.
    LLM Tool: get_payment_history(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    payments = store.get_payments_by_customer(customer_id)

    # Sort by date
    payments.sort(key=lambda x: x.get("payment_date", ""), reverse=True)

    # Separate by type
    premiums = [p for p in payments if p.get("payment_type") == "premium"]
    payouts = [p for p in payments if p.get("payment_type") == "claim_payout"]

    total_premiums = sum(p.get("amount", 0) for p in premiums)
    total_payouts = sum(p.get("amount", 0) for p in payouts)

    return {
        "customer_id": customer_id,
        "customer_name": f"{customer.get('first_name')} {customer.get('last_name')}",
        "total_payments": len(payments),
        "total_premiums_paid": total_premiums,
        "total_claims_received": total_payouts,
        "net_position": total_premiums - total_payouts,
        "recent_payments": payments[:20]
    }


@router.get("/claim-status/{claim_id}")
async def check_payment_status(claim_id: str) -> Dict[str, Any]:
    """
    Check payment status for a claim.
    LLM Tool: check_payment_status(claim_id)
    """
    store = get_data_store()
    claim = store.get_claim(claim_id)

    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    payments = store.get_payments_by_claim(claim_id)

    total_paid = sum(p.get("amount", 0) for p in payments)
    expected_payment = claim.get("paid_amount", 0)

    if claim.get("status") == "denied":
        payment_status = "no_payment_due"
    elif total_paid >= expected_payment and expected_payment > 0:
        payment_status = "paid_in_full"
    elif total_paid > 0:
        payment_status = "partially_paid"
    elif claim.get("status") in ["approved", "paid"]:
        payment_status = "pending_payment"
    else:
        payment_status = "processing"

    return {
        "claim_id": claim_id,
        "claim_number": claim.get("claim_number"),
        "claim_status": claim.get("status"),
        "claim_amount": claim.get("claim_amount"),
        "approved_amount": claim.get("covered_amount"),
        "expected_payment": expected_payment,
        "total_paid": total_paid,
        "payment_status": payment_status,
        "payments": payments
    }


@router.get("/annual-summary/{policy_id}")
async def get_annual_summary(policy_id: str) -> Dict[str, Any]:
    """
    Get annual billing summary for a policy.
    LLM Tool: get_annual_summary(policy_id)
    """
    store = get_data_store()
    policy = store.get_policy(policy_id)

    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    customer_id = policy.get("customer_id")
    current_year = datetime.now().year

    # Get claims for this year
    claims = store.get_claims_by_policy(policy_id)
    year_claims = [
        c for c in claims
        if c.get("service_date", "").startswith(str(current_year))
    ]

    approved_claims = [c for c in year_claims if c.get("status") in ["paid", "approved"]]

    # Get payments
    payments = store.get_payments_by_customer(customer_id)
    year_premiums = [
        p for p in payments
        if p.get("payment_type") == "premium"
        and p.get("payment_date", "").startswith(str(current_year))
        and p.get("policy_id") == policy_id
    ]

    total_premiums = sum(p.get("amount", 0) for p in year_premiums)
    total_claimed = sum(c.get("claim_amount", 0) for c in year_claims)
    total_paid = sum(c.get("paid_amount", 0) for c in approved_claims)

    coverage = policy.get("coverage_limit", {})
    annual_limit = coverage.get("annual_limit", 10000)

    return {
        "policy_id": policy_id,
        "policy_number": policy.get("policy_number"),
        "year": current_year,
        "total_premiums_paid": total_premiums,
        "total_claims_submitted": len(year_claims),
        "total_claims_approved": len(approved_claims),
        "total_claimed_amount": total_claimed,
        "total_paid_amount": total_paid,
        "deductible": policy.get("annual_deductible"),
        "deductible_met": policy.get("deductible_met", 0) >= policy.get("annual_deductible", 250),
        "annual_limit": annual_limit,
        "annual_limit_used": total_paid,
        "annual_limit_remaining": max(0, annual_limit - total_paid),
        "loss_ratio": total_paid / total_premiums if total_premiums > 0 else 0
    }
