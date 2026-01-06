"""
FraudService - Fraud detection and analysis.
6 endpoints for fraud checking and pattern detection.
Critical for AI vs Rules comparison demo.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.data_loader import get_data_store

router = APIRouter()


class ClaimData(BaseModel):
    """Input for fraud checking."""
    claim_id: Optional[str] = None
    customer_id: str
    pet_id: str
    provider_id: str
    claim_amount: float
    diagnosis_code: str
    service_date: str
    claim_category: Optional[str] = None
    treatment_notes: Optional[str] = None


@router.get("/patterns")
async def get_fraud_patterns() -> Dict[str, Any]:
    """Get configured fraud patterns for demo."""
    store = get_data_store()
    return store.get_fraud_patterns()


@router.post("/check")
async def check_fraud_indicators(claim: ClaimData) -> Dict[str, Any]:
    """
    Full fraud analysis for a claim.
    LLM Tool: check_fraud_indicators(claim_data)

    Returns fraud score, indicators, and recommendation.
    """
    store = get_data_store()

    indicators = []
    fraud_score = 0

    # Get customer history
    customer = store.get_customer(claim.customer_id)
    claims = store.get_claims_by_customer(claim.customer_id)
    pet = store.get_pet(claim.pet_id)
    provider = store.get_provider(claim.provider_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {claim.customer_id} not found")

    # =========================================================================
    # FRAUD PATTERN 1: Chronic Condition Gaming
    # =========================================================================
    if pet and pet.get("pre_existing_conditions"):
        pre_existing_codes = [
            c.get("diagnosis_code") for c in pet.get("pre_existing_conditions", [])
        ]
        # Check if claim is related to pre-existing
        medical_code = store.get_medical_code(claim.diagnosis_code)
        if medical_code:
            related = medical_code.get("related_codes", [])
            for pec in pre_existing_codes:
                if pec == claim.diagnosis_code or pec in related:
                    indicators.append({
                        "indicator_type": "pre_existing_related",
                        "severity": "high",
                        "description": f"Claim diagnosis may be related to pre-existing condition ({pec})",
                        "score_impact": 25
                    })
                    fraud_score += 25

        # Check anatomical pattern (e.g., all hip injuries)
        pet_claims = store.get_claims_by_pet(claim.pet_id)
        anatomy_focus = {}
        for pc in pet_claims:
            code = pc.get("diagnosis_code", "")
            # Simple pattern: first letter indicates body system
            system = code[:1] if code else "X"
            anatomy_focus[system] = anatomy_focus.get(system, 0) + 1

        if len(anatomy_focus) == 1 and len(pet_claims) >= 3:
            indicators.append({
                "indicator_type": "anatomical_concentration",
                "severity": "medium",
                "description": f"All {len(pet_claims)} claims focus on same body system",
                "score_impact": 15
            })
            fraud_score += 15

    # =========================================================================
    # FRAUD PATTERN 2: Provider Collusion
    # =========================================================================
    if provider:
        stats = provider.get("stats", {})

        # Check if customer has unusual concentration with this provider
        customer_claims_at_provider = [
            c for c in claims if c.get("provider_id") == claim.provider_id
        ]
        if len(customer_claims_at_provider) == len(claims) and len(claims) >= 3:
            indicators.append({
                "indicator_type": "exclusive_provider",
                "severity": "medium",
                "description": f"Customer uses only this provider for all {len(claims)} claims",
                "score_impact": 15
            })
            fraud_score += 15

        # Check if provider is out-of-network with high claim amounts
        if not provider.get("is_in_network"):
            avg_claim = sum(c.get("claim_amount", 0) for c in customer_claims_at_provider) / max(1, len(customer_claims_at_provider))
            if avg_claim > 3000:
                indicators.append({
                    "indicator_type": "high_out_of_network",
                    "severity": "medium",
                    "description": f"High average claim (${avg_claim:.0f}) at out-of-network provider",
                    "score_impact": 10
                })
                fraud_score += 10

        # Check provider concentration
        concentration = stats.get("customer_concentration", {})
        if claim.customer_id in concentration and concentration[claim.customer_id] > 0.10:
            indicators.append({
                "indicator_type": "provider_concentration",
                "severity": "high",
                "description": f"Customer represents {concentration[claim.customer_id]*100:.0f}% of provider's claims",
                "score_impact": 20
            })
            fraud_score += 20

        # Check provider fraud rate
        if stats.get("fraud_rate", 0) > 0.025:
            indicators.append({
                "indicator_type": "elevated_provider_fraud_rate",
                "severity": "medium",
                "description": f"Provider fraud rate ({stats.get('fraud_rate', 0)*100:.1f}%) above average",
                "score_impact": 10
            })
            fraud_score += 10

    # =========================================================================
    # FRAUD PATTERN 3: Staged Timing
    # =========================================================================
    policies = store.get_policies_by_pet(claim.pet_id)
    for policy in policies:
        if policy.get("status") != "active":
            continue

        effective = datetime.fromisoformat(policy.get("effective_date", "2024-01-01"))
        service = datetime.fromisoformat(claim.service_date)
        days_since_effective = (service - effective).days

        # Check if claim is suspiciously close to waiting period end
        waiting = policy.get("waiting_period", {})
        illness_wait = waiting.get("illness_days", 14)

        if days_since_effective <= illness_wait + 3 and days_since_effective >= illness_wait:
            # Claim within 3 days of waiting period ending
            indicators.append({
                "indicator_type": "timing_anomaly",
                "severity": "high",
                "description": f"Claim filed {days_since_effective - illness_wait} days after waiting period ended",
                "score_impact": 25
            })
            fraud_score += 25

            # Breed-specific check for French Bulldogs and IVDD
            if pet and pet.get("breed", "").lower() in ["french bulldog", "dachshund", "corgi"]:
                if claim.diagnosis_code in ["G95.89", "M51.9", "S33"]:  # IVDD codes
                    indicators.append({
                        "indicator_type": "breed_specific_timing",
                        "severity": "critical",
                        "description": f"{pet.get('breed')} has 10x higher risk for this condition - suspicious timing",
                        "score_impact": 30
                    })
                    fraud_score += 30

    # =========================================================================
    # ADDITIONAL CHECKS
    # =========================================================================

    # Round amount check
    if claim.claim_amount % 100 == 0 or claim.claim_amount % 500 == 0:
        indicators.append({
            "indicator_type": "round_amount",
            "severity": "low",
            "description": f"Claim amount ${claim.claim_amount:.0f} is a round number",
            "score_impact": 5
        })
        fraud_score += 5

    # High velocity check
    recent_claims = [
        c for c in claims
        if (datetime.fromisoformat(claim.service_date) - datetime.fromisoformat(c.get("service_date", "2020-01-01"))).days <= 90
    ]
    if len(recent_claims) >= 4:
        indicators.append({
            "indicator_type": "high_velocity",
            "severity": "medium",
            "description": f"{len(recent_claims)} claims in last 90 days",
            "score_impact": 10
        })
        fraud_score += 10

    # Determine risk level and recommendation
    if fraud_score >= 50:
        risk_level = "critical"
        recommendation = "manual_review"
        reasoning = "Multiple high-severity fraud indicators detected. Recommend thorough investigation."
    elif fraud_score >= 30:
        risk_level = "high"
        recommendation = "manual_review"
        reasoning = "Significant fraud indicators present. Manual review recommended."
    elif fraud_score >= 15:
        risk_level = "medium"
        recommendation = "enhanced_review"
        reasoning = "Some fraud indicators detected. Enhanced scrutiny recommended."
    else:
        risk_level = "low"
        recommendation = "approve"
        reasoning = "No significant fraud indicators. Standard processing recommended."

    return {
        "claim_id": claim.claim_id,
        "customer_id": claim.customer_id,
        "fraud_score": fraud_score,
        "risk_level": risk_level,
        "indicators": indicators,
        "recommendation": recommendation,
        "reasoning": reasoning,
        "requires_manual_review": fraud_score >= 30
    }


@router.get("/velocity/{customer_id}")
async def velocity_check(customer_id: str) -> Dict[str, Any]:
    """
    Check claims frequency for a customer.
    LLM Tool: velocity_check(customer_id)
    """
    store = get_data_store()
    customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    claims = store.get_claims_by_customer(customer_id)
    now = datetime.now()

    # Calculate claims in different periods
    claims_30 = [c for c in claims if (now - datetime.fromisoformat(c.get("service_date", "2020-01-01"))).days <= 30]
    claims_90 = [c for c in claims if (now - datetime.fromisoformat(c.get("service_date", "2020-01-01"))).days <= 90]
    claims_365 = [c for c in claims if (now - datetime.fromisoformat(c.get("service_date", "2020-01-01"))).days <= 365]

    # Calculate frequency
    if len(claims) >= 2:
        dates = sorted([datetime.fromisoformat(c.get("service_date", "2020-01-01")) for c in claims])
        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_frequency = sum(gaps) / len(gaps) if gaps else 0
    else:
        avg_frequency = 0

    # Determine if unusual
    is_unusual = len(claims_30) >= 3 or len(claims_90) >= 6

    return {
        "customer_id": customer_id,
        "claims_last_30_days": len(claims_30),
        "claims_last_90_days": len(claims_90),
        "claims_last_365_days": len(claims_365),
        "average_claim_frequency_days": round(avg_frequency, 1),
        "is_unusual": is_unusual,
        "reasoning": f"Customer has {len(claims_30)} claims in 30 days, {len(claims_90)} in 90 days" if is_unusual else None
    }


@router.post("/duplicate-check")
async def duplicate_check(claim: ClaimData) -> Dict[str, Any]:
    """
    Find potential duplicate claims.
    LLM Tool: duplicate_check(claim_data)
    """
    store = get_data_store()
    claims = store.get_claims_by_customer(claim.customer_id)

    duplicates = []
    for existing in claims:
        if existing.get("claim_id") == claim.claim_id:
            continue

        # Check for same service date
        if existing.get("service_date") == claim.service_date:
            if existing.get("diagnosis_code") == claim.diagnosis_code:
                duplicates.append({
                    "claim_id": existing.get("claim_id"),
                    "match_type": "exact_duplicate",
                    "confidence": 0.95,
                    "details": "Same date and diagnosis"
                })
            elif existing.get("provider_id") == claim.provider_id:
                duplicates.append({
                    "claim_id": existing.get("claim_id"),
                    "match_type": "same_day_provider",
                    "confidence": 0.70,
                    "details": "Same date and provider"
                })

        # Check for similar amounts within 7 days
        try:
            existing_date = datetime.fromisoformat(existing.get("service_date", "2020-01-01"))
            claim_date = datetime.fromisoformat(claim.service_date)
            days_apart = abs((claim_date - existing_date).days)

            if days_apart <= 7 and abs(existing.get("claim_amount", 0) - claim.claim_amount) < 50:
                duplicates.append({
                    "claim_id": existing.get("claim_id"),
                    "match_type": "similar_amount_close_date",
                    "confidence": 0.50,
                    "details": f"Similar amount (${existing.get('claim_amount')}) within {days_apart} days"
                })
        except ValueError:
            pass

    return {
        "claim_data": {
            "customer_id": claim.customer_id,
            "service_date": claim.service_date,
            "claim_amount": claim.claim_amount,
            "diagnosis_code": claim.diagnosis_code
        },
        "potential_duplicates": duplicates,
        "has_duplicates": len(duplicates) > 0,
        "highest_confidence": max([d["confidence"] for d in duplicates]) if duplicates else 0
    }


@router.post("/pattern-match")
async def pattern_match(claim: ClaimData) -> Dict[str, Any]:
    """
    Match against known fraud patterns.
    LLM Tool: pattern_match(claim_data)
    """
    store = get_data_store()
    fraud_patterns = store.get_fraud_patterns()
    patterns = fraud_patterns.get("patterns", [])

    matches = []
    for pattern in patterns:
        if pattern.get("customer_id") == claim.customer_id:
            matches.append({
                "pattern_id": pattern.get("id"),
                "pattern_name": pattern.get("name"),
                "match_type": "customer_match",
                "description": pattern.get("description"),
                "indicators": pattern.get("indicators", []),
                "why_ai_catches": pattern.get("why_ai_catches")
            })

        if pattern.get("provider_id") == claim.provider_id:
            matches.append({
                "pattern_id": pattern.get("id"),
                "pattern_name": pattern.get("name"),
                "match_type": "provider_match",
                "description": pattern.get("description"),
                "indicators": pattern.get("indicators", []),
                "why_ai_catches": pattern.get("why_ai_catches")
            })

    return {
        "claim_customer_id": claim.customer_id,
        "claim_provider_id": claim.provider_id,
        "pattern_matches": matches,
        "has_matches": len(matches) > 0,
        "requires_investigation": len(matches) > 0
    }


@router.get("/provider-customer/{provider_id}/{customer_id}")
async def provider_customer_analysis(provider_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Analyze relationship between provider and customer.
    LLM Tool: provider_customer_analysis(provider_id, customer_id)
    """
    store = get_data_store()

    provider = store.get_provider(provider_id)
    customer = store.get_customer(customer_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Get claims between this pair
    customer_claims = store.get_claims_by_customer(customer_id)
    pair_claims = [c for c in customer_claims if c.get("provider_id") == provider_id]

    # Get all provider claims for comparison
    provider_claims = store.get_claims_by_provider(provider_id)

    # Calculate metrics
    pair_amount = sum(c.get("claim_amount", 0) for c in pair_claims)
    provider_total = sum(c.get("claim_amount", 0) for c in provider_claims)
    customer_total = sum(c.get("claim_amount", 0) for c in customer_claims)

    pct_of_provider = (pair_amount / provider_total * 100) if provider_total > 0 else 0
    pct_of_customer = (pair_amount / customer_total * 100) if customer_total > 0 else 0

    # Determine if unusual
    is_unusual = pct_of_provider > 10 or (pct_of_customer > 80 and len(pair_claims) >= 3)

    return {
        "provider_id": provider_id,
        "provider_name": provider.get("name"),
        "customer_id": customer_id,
        "customer_name": f"{customer.get('first_name')} {customer.get('last_name')}",
        "total_claims_together": len(pair_claims),
        "total_amount_together": pair_amount,
        "percentage_of_provider_claims": round(pct_of_provider, 1),
        "percentage_of_customer_claims": round(pct_of_customer, 1),
        "is_unusual_concentration": is_unusual,
        "provider_is_in_network": provider.get("is_in_network"),
        "reasoning": f"Customer represents {pct_of_provider:.1f}% of provider's claims" if is_unusual else None
    }


@router.post("/score")
async def calculate_fraud_score(claim: ClaimData) -> Dict[str, Any]:
    """
    Calculate ML-based fraud score.
    LLM Tool: calculate_fraud_score(claim_data)

    This calls the full check_fraud_indicators internally.
    """
    result = await check_fraud_indicators(claim)

    return {
        "claim_id": claim.claim_id,
        "fraud_score": result["fraud_score"],
        "risk_level": result["risk_level"],
        "recommendation": result["recommendation"],
        "indicator_count": len(result["indicators"]),
        "top_indicators": result["indicators"][:3] if result["indicators"] else []
    }
