"""
PetInsure360 Rule-Based Claims Processing Engine

This is the RULE-BASED processor that uses deterministic logic.
It calls the same Unified Claims Data API (port 8000) as the AI agents,
but makes decisions using fixed business rules instead of LLM reasoning.

This is used for comparison with the AI agent-driven approach in EIS Dynamics POC.
"""

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# Unified Claims Data API base URL
CLAIMS_API_BASE = "http://localhost:8000/api/v1"


class Decision(Enum):
    """Claim processing decisions."""
    AUTO_APPROVE = "auto_approve"
    STANDARD_REVIEW = "standard_review"
    MANUAL_REVIEW = "manual_review"
    DENY = "deny"


@dataclass
class RulesResult:
    """Result from rule-based processing."""
    decision: Decision
    risk_score: int
    risk_factors: List[str]
    coverage_result: Dict[str, Any]
    reimbursement: float
    reasoning: str
    processing_time_ms: float
    fraud_flags: List[str]


async def _api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make an async API call to the Unified Claims Data API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{CLAIMS_API_BASE}{endpoint}"
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            return {"error": str(e)}


async def process_claim_with_rules(claim_data: Dict[str, Any]) -> RulesResult:
    """
    Process a claim using RULE-BASED logic (no AI).

    This function:
    1. Calls the same Unified API as the AI agents
    2. Applies fixed business rules for decisions
    3. Returns a deterministic result

    Unlike AI agents, this CANNOT:
    - Recognize cross-claim patterns
    - Detect subtle fraud indicators
    - Adjust reasoning based on context
    """
    start_time = datetime.now()

    risk_score = 0
    risk_factors = []
    fraud_flags = []

    customer_id = claim_data.get("customer_id", "")
    pet_id = claim_data.get("pet_id", "")
    policy_id = claim_data.get("policy_id", "")
    provider_id = claim_data.get("provider_id", "")
    claim_amount = float(claim_data.get("claim_amount", 0))
    diagnosis_code = claim_data.get("diagnosis_code", "")
    service_date = claim_data.get("service_date", "")

    # =========================================================================
    # RULE 1: Check policy exists and is active
    # =========================================================================
    policy_result = await _api_call(f"/policies/{policy_id}")
    if "error" in policy_result:
        return RulesResult(
            decision=Decision.DENY,
            risk_score=100,
            risk_factors=["Policy not found"],
            coverage_result={},
            reimbursement=0,
            reasoning=f"Policy {policy_id} not found in system",
            processing_time_ms=0,
            fraud_flags=[]
        )

    policy = policy_result.get("policy", {})
    if policy.get("status") != "active":
        return RulesResult(
            decision=Decision.DENY,
            risk_score=100,
            risk_factors=["Policy not active"],
            coverage_result={},
            reimbursement=0,
            reasoning=f"Policy {policy_id} is not active (status: {policy.get('status')})",
            processing_time_ms=0,
            fraud_flags=[]
        )

    # =========================================================================
    # RULE 2: Check coverage
    # =========================================================================
    coverage_result = await _api_call(f"/policies/{policy_id}/coverage/{diagnosis_code}")
    if not coverage_result.get("is_covered", False):
        return RulesResult(
            decision=Decision.DENY,
            risk_score=0,
            risk_factors=["Diagnosis not covered"],
            coverage_result=coverage_result,
            reimbursement=0,
            reasoning=coverage_result.get("notes", "Diagnosis not covered by policy"),
            processing_time_ms=0,
            fraud_flags=[]
        )

    # =========================================================================
    # RULE 3: Check limits
    # =========================================================================
    limits_result = await _api_call(f"/policies/{policy_id}/limits")
    annual_limit = limits_result.get("annual_limit", 10000)
    remaining = limits_result.get("remaining_this_year", annual_limit)

    if claim_amount > remaining:
        risk_score += 10
        risk_factors.append(f"Claim exceeds remaining annual limit (${remaining:.2f})")

    # =========================================================================
    # RULE 4: Check provider network status
    # =========================================================================
    network_result = await _api_call(f"/providers/{provider_id}/network-status")
    is_in_network = network_result.get("is_in_network", True)
    network_adjustment = network_result.get("reimbursement_adjustment", 1.0)

    if not is_in_network:
        risk_score += 20
        risk_factors.append("Out-of-network provider")

    # =========================================================================
    # RULE 5: Amount-based risk scoring (SIMPLE RULES - what AI beats)
    # =========================================================================
    if claim_amount > 10000:
        risk_score += 30
        risk_factors.append(f"Very high claim amount: ${claim_amount:.2f}")
    elif claim_amount > 5000:
        risk_score += 15
        risk_factors.append(f"High claim amount: ${claim_amount:.2f}")

    # Round amount check (basic rule)
    if claim_amount % 100 == 0 or claim_amount % 500 == 0:
        risk_score += 5
        fraud_flags.append(f"Round dollar amount: ${claim_amount:.0f}")

    # =========================================================================
    # RULE 6: Emergency claim risk
    # =========================================================================
    is_emergency = claim_data.get("is_emergency", False)
    if is_emergency:
        risk_score += 5
        risk_factors.append("Emergency claim")

    # =========================================================================
    # RULE 7: Check deductible and calculate reimbursement
    # =========================================================================
    reimbursement_result = await _api_call("/billing/calculate", "POST", {
        "policy_id": policy_id,
        "claim_amount": claim_amount,
        "diagnosis_code": diagnosis_code,
        "provider_id": provider_id,
        "is_emergency": is_emergency
    })

    final_payout = reimbursement_result.get("final_payout", 0)

    # =========================================================================
    # RULE 8: Basic velocity check (simple rule)
    # =========================================================================
    velocity_result = await _api_call(f"/fraud/velocity/{customer_id}")
    claims_30 = velocity_result.get("claims_last_30_days", 0)
    if claims_30 >= 3:
        risk_score += 10
        fraud_flags.append(f"High claim velocity: {claims_30} claims in 30 days")

    # =========================================================================
    # WHAT RULES MISS (these patterns require AI to detect):
    # - Pre-existing condition gaming (AI checks medical history patterns)
    # - Provider collusion (AI correlates provider-customer relationships)
    # - Staged timing (AI analyzes waiting period statistical anomalies)
    # - Cross-claim pattern recognition
    # =========================================================================

    # Calculate processing time
    end_time = datetime.now()
    processing_time_ms = (end_time - start_time).total_seconds() * 1000

    # Make decision based on risk score
    if risk_score >= 50:
        decision = Decision.MANUAL_REVIEW
        reasoning = f"High risk score ({risk_score}) requires manual review"
    elif risk_score >= 25:
        decision = Decision.STANDARD_REVIEW
        reasoning = f"Moderate risk score ({risk_score}) - standard review required"
    elif claim_amount <= 500 and is_in_network:
        decision = Decision.AUTO_APPROVE
        reasoning = f"Low risk claim (score: {risk_score}), small amount, in-network - auto-approved"
    else:
        decision = Decision.STANDARD_REVIEW
        reasoning = f"Standard processing (risk score: {risk_score})"

    return RulesResult(
        decision=decision,
        risk_score=risk_score,
        risk_factors=risk_factors,
        coverage_result=coverage_result,
        reimbursement=final_payout,
        reasoning=reasoning,
        processing_time_ms=processing_time_ms,
        fraud_flags=fraud_flags
    )


async def compare_with_agent_result(claim_data: Dict[str, Any], rules_result: RulesResult) -> Dict[str, Any]:
    """
    Get agent result for comparison.

    This calls the EIS Dynamics agent pipeline and compares with rule-based result.
    """
    # Call fraud check from Unified API (this is what the AI agent uses)
    fraud_result = await _api_call("/fraud/check", "POST", {
        "customer_id": claim_data.get("customer_id"),
        "pet_id": claim_data.get("pet_id"),
        "provider_id": claim_data.get("provider_id"),
        "claim_amount": claim_data.get("claim_amount"),
        "diagnosis_code": claim_data.get("diagnosis_code"),
        "service_date": claim_data.get("service_date", datetime.now().isoformat()[:10])
    })

    # Check pattern match
    pattern_result = await _api_call("/fraud/pattern-match", "POST", {
        "customer_id": claim_data.get("customer_id"),
        "pet_id": claim_data.get("pet_id"),
        "provider_id": claim_data.get("provider_id"),
        "claim_amount": claim_data.get("claim_amount"),
        "diagnosis_code": claim_data.get("diagnosis_code"),
        "service_date": claim_data.get("service_date", datetime.now().isoformat()[:10])
    })

    ai_fraud_score = fraud_result.get("fraud_score", 0)
    ai_recommendation = fraud_result.get("recommendation", "unknown")
    ai_patterns = pattern_result.get("pattern_matches", [])

    # Determine if AI would catch something rules missed
    ai_caught_fraud = ai_fraud_score >= 30 or len(ai_patterns) > 0
    rules_caught_fraud = rules_result.risk_score >= 30 or len(rules_result.fraud_flags) > 0

    return {
        "rules_result": {
            "decision": rules_result.decision.value,
            "risk_score": rules_result.risk_score,
            "fraud_flags": rules_result.fraud_flags,
            "processing_time_ms": rules_result.processing_time_ms,
            "reimbursement": rules_result.reimbursement
        },
        "ai_result": {
            "fraud_score": ai_fraud_score,
            "recommendation": ai_recommendation,
            "patterns_detected": [p.get("pattern_name") for p in ai_patterns],
            "indicators": fraud_result.get("indicators", [])
        },
        "comparison": {
            "rules_caught_fraud": rules_caught_fraud,
            "ai_caught_fraud": ai_caught_fraud,
            "ai_advantage": ai_caught_fraud and not rules_caught_fraud,
            "patterns_missed_by_rules": [p.get("pattern_name") for p in ai_patterns] if not rules_caught_fraud else []
        }
    }
