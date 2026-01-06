"""
Analytics tools for the Gold Agent.

These tools handle risk assessment, fraud detection, insight generation,
KPI calculation, and alert creation.
"""

import logging
import random
from datetime import datetime
from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Fraud indicators and weights
FRAUD_INDICATORS = {
    "high_claim_amount": 0.15,
    "new_customer": 0.10,
    "multiple_recent_claims": 0.20,
    "out_of_network_provider": 0.08,
    "round_amount": 0.05,
    "weekend_treatment": 0.03,
    "high_risk_provider": 0.25,
    "unusual_diagnosis": 0.12,
    "amount_exceeds_average": 0.10,
    "missing_documentation": 0.15,
}

# Risk level thresholds
RISK_THRESHOLDS = {
    "low": (0, 0.25),
    "medium": (0.25, 0.50),
    "high": (0.50, 0.75),
    "critical": (0.75, 1.0),
}


class RiskAssessmentResult(BaseModel):
    """Result of risk assessment."""
    fraud_score: float = 0.0
    risk_level: str = "low"
    risk_factors: list[str] = Field(default_factory=list)
    fraud_indicators: list[str] = Field(default_factory=list)
    recommendation: str = ""


class InsightsResult(BaseModel):
    """Result of insight generation."""
    insights: list[str] = Field(default_factory=list)
    patterns_detected: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class KPIMetricsResult(BaseModel):
    """Result of KPI calculation."""
    metrics: dict[str, float] = Field(default_factory=dict)
    comparisons: dict[str, str] = Field(default_factory=dict)
    trends: list[str] = Field(default_factory=list)


class AlertResult(BaseModel):
    """Result of alert creation."""
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    total_alerts: int = 0
    high_priority_count: int = 0


class Customer360Result(BaseModel):
    """Result of customer 360 update."""
    customer_id: str = ""
    updates: dict[str, Any] = Field(default_factory=dict)
    new_metrics: dict[str, float] = Field(default_factory=dict)
    segment_change: Optional[str] = None


@tool
def assess_risk(
    claim_data: dict[str, Any],
    enrichment_data: dict[str, Any],
    normalized_data: dict[str, Any],
    business_rules_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Perform comprehensive risk and fraud assessment.

    Analyzes multiple factors to calculate fraud probability.

    Args:
        claim_data: The claim data
        enrichment_data: Enrichment data (customer, policy, provider)
        normalized_data: Normalized claim data
        business_rules_result: Business rules validation result

    Returns:
        RiskAssessmentResult with fraud score and indicators
    """
    result = RiskAssessmentResult()
    fraud_score = 0.0
    indicators = []
    risk_factors = []

    claim_amount = float(claim_data.get("claim_amount", 0))
    customer_info = enrichment_data.get("customer_info", {})
    provider_info = enrichment_data.get("provider_info", {})
    policy_info = enrichment_data.get("policy_info", {})

    # Check high claim amount
    if claim_amount > 5000:
        indicators.append("high_claim_amount")
        fraud_score += FRAUD_INDICATORS["high_claim_amount"]
        risk_factors.append(f"High claim amount: ${claim_amount:,.2f}")

    # Check if new customer
    member_since = customer_info.get("member_since", "")
    if member_since:
        try:
            member_date = datetime.strptime(member_since[:10], "%Y-%m-%d")
            months_as_member = (datetime.utcnow() - member_date).days / 30
            if months_as_member < 3:
                indicators.append("new_customer")
                fraud_score += FRAUD_INDICATORS["new_customer"]
                risk_factors.append(f"New customer: {months_as_member:.1f} months")
        except Exception:
            pass

    # Check multiple recent claims
    total_claims = customer_info.get("total_claims", 0)
    if total_claims >= 5:
        indicators.append("multiple_recent_claims")
        fraud_score += FRAUD_INDICATORS["multiple_recent_claims"]
        risk_factors.append(f"Multiple claims: {total_claims} in history")

    # Check out-of-network provider
    if not provider_info.get("is_in_network", True):
        indicators.append("out_of_network_provider")
        fraud_score += FRAUD_INDICATORS["out_of_network_provider"]
        risk_factors.append("Out-of-network provider")

    # Check round amount
    if claim_amount > 100 and claim_amount % 100 == 0:
        indicators.append("round_amount")
        fraud_score += FRAUD_INDICATORS["round_amount"]
        risk_factors.append(f"Suspiciously round amount: ${claim_amount:,.2f}")

    # Check weekend treatment
    treatment_date = claim_data.get("treatment_date", "")
    if treatment_date:
        try:
            date = datetime.strptime(treatment_date[:10], "%Y-%m-%d")
            if date.weekday() >= 5:  # Saturday or Sunday
                indicators.append("weekend_treatment")
                fraud_score += FRAUD_INDICATORS["weekend_treatment"]
                risk_factors.append("Weekend treatment date")
        except Exception:
            pass

    # Check provider fraud rate
    provider_fraud_rate = provider_info.get("fraud_rate", 0)
    if provider_fraud_rate > 0.05:
        indicators.append("high_risk_provider")
        fraud_score += FRAUD_INDICATORS["high_risk_provider"]
        risk_factors.append(f"High-risk provider (fraud rate: {provider_fraud_rate:.1%})")

    # Check if amount exceeds provider average
    provider_avg = provider_info.get("avg_claim_amount", 0)
    if provider_avg > 0 and claim_amount > provider_avg * 2:
        indicators.append("amount_exceeds_average")
        fraud_score += FRAUD_INDICATORS["amount_exceeds_average"]
        risk_factors.append(f"Amount 2x+ provider average (${provider_avg:,.2f})")

    # Check business rules failures
    failed_rules = business_rules_result.get("failed", [])
    if len(failed_rules) > 0:
        fraud_score += 0.05 * len(failed_rules)
        risk_factors.append(f"{len(failed_rules)} business rule(s) failed")

    # Normalize fraud score to 0-1 range
    result.fraud_score = min(1.0, fraud_score)
    result.fraud_indicators = indicators
    result.risk_factors = risk_factors

    # Determine risk level
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= result.fraud_score < high:
            result.risk_level = level
            break

    # Generate recommendation
    if result.risk_level == "low":
        result.recommendation = "AUTO_APPROVE: Low risk, proceed with standard processing"
    elif result.risk_level == "medium":
        result.recommendation = "STANDARD_REVIEW: Medium risk, apply standard review procedures"
    elif result.risk_level == "high":
        result.recommendation = "MANUAL_REVIEW: High risk, requires senior adjuster review"
    else:
        result.recommendation = "INVESTIGATION: Critical risk, escalate to fraud investigation unit"

    logger.info(f"Risk assessment complete: score={result.fraud_score:.2f}, level={result.risk_level}")
    return result.model_dump()


@tool
def generate_insights(
    claim_data: dict[str, Any],
    enrichment_data: dict[str, Any],
    risk_assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate business insights from claim analysis.

    Identifies patterns, trends, and actionable recommendations.

    Args:
        claim_data: The claim data
        enrichment_data: Enrichment data
        risk_assessment: Risk assessment result

    Returns:
        InsightsResult with insights and recommendations
    """
    result = InsightsResult()
    insights = []
    patterns = []
    recommendations = []

    customer_info = enrichment_data.get("customer_info", {})
    pet_info = enrichment_data.get("pet_info", {})
    provider_info = enrichment_data.get("provider_info", {})
    claim_amount = float(claim_data.get("claim_amount", 0))
    claim_type = claim_data.get("claim_type", "accident")

    # Customer insights
    lifetime_value = customer_info.get("lifetime_value", 0)
    churn_risk = customer_info.get("churn_risk", 0)

    if lifetime_value > 3000:
        insights.append(f"High-value customer (LTV: ${lifetime_value:,.2f}) - prioritize satisfaction")
        patterns.append("high_value_customer")

    if churn_risk > 0.20:
        insights.append(f"Elevated churn risk ({churn_risk:.0%}) - consider retention outreach")
        recommendations.append("Schedule post-claim satisfaction survey")
        patterns.append("high_churn_risk")

    # Pet insights
    pet_age = pet_info.get("age_years", 0)
    known_conditions = pet_info.get("known_conditions", [])

    if pet_age > 8:
        insights.append(f"Senior pet (age {pet_age}) - expect higher claim frequency")
        patterns.append("senior_pet")

    if known_conditions:
        insights.append(f"Pre-existing conditions noted: {', '.join(known_conditions)}")
        patterns.append("pre_existing_conditions")

    # Provider insights
    provider_rating = provider_info.get("rating", 0)
    if provider_rating >= 4.5:
        insights.append(f"High-quality provider (rating: {provider_rating:.1f}/5)")
        patterns.append("quality_provider")

    # Claim pattern insights
    if claim_type == "emergency":
        insights.append("Emergency claim - may indicate coverage gap awareness opportunity")
        recommendations.append("Review customer's emergency preparedness coverage")
        patterns.append("emergency_claim")

    if claim_amount > 10000:
        insights.append(f"High-value claim (${claim_amount:,.2f}) - verify documentation completeness")
        recommendations.append("Request additional documentation if not already provided")
        patterns.append("high_value_claim")

    # Risk-based insights
    fraud_score = risk_assessment.get("fraud_score", 0)
    if fraud_score > 0.5:
        insights.append(f"Elevated fraud indicators detected (score: {fraud_score:.2f})")
        recommendations.append("Review claim with senior adjuster before approval")
        patterns.append("fraud_risk")

    # Calculate insight confidence
    result.confidence = min(1.0, 0.5 + (len(insights) * 0.1))

    result.insights = insights
    result.patterns_detected = patterns
    result.recommendations = recommendations

    logger.info(f"Generated {len(insights)} insights with {result.confidence:.0%} confidence")
    return result.model_dump()


@tool
def calculate_kpi_metrics(
    claim_data: dict[str, Any],
    enrichment_data: dict[str, Any],
    processing_time_ms: float,
) -> dict[str, Any]:
    """
    Calculate KPI metrics for the claim.

    Computes metrics that contribute to business dashboards.

    Args:
        claim_data: The claim data
        enrichment_data: Enrichment data
        processing_time_ms: Time taken to process the claim

    Returns:
        KPIMetricsResult with calculated metrics
    """
    result = KPIMetricsResult()

    claim_amount = float(claim_data.get("claim_amount", 0))
    claim_type = claim_data.get("claim_type", "accident")
    customer_info = enrichment_data.get("customer_info", {})
    policy_info = enrichment_data.get("policy_info", {})

    # Calculate metrics
    metrics = {
        # Claim metrics
        "claim_amount": claim_amount,
        "processing_time_seconds": processing_time_ms / 1000,
        "expected_payout": claim_amount * policy_info.get("reimbursement_rate", 0.8),

        # Customer metrics
        "customer_lifetime_value": customer_info.get("lifetime_value", 0),
        "customer_claim_count": customer_info.get("total_claims", 0) + 1,

        # Efficiency metrics
        "automation_score": 0.85 if processing_time_ms < 15000 else 0.70,
        "straight_through_processing": 1.0 if processing_time_ms < 10000 else 0.0,
    }

    # Add comparisons
    comparisons = {}
    avg_claim_by_type = {
        "accident": 1500,
        "illness": 800,
        "wellness": 150,
        "emergency": 3000,
    }

    if claim_type in avg_claim_by_type:
        avg = avg_claim_by_type[claim_type]
        if claim_amount > avg * 1.5:
            comparisons["claim_vs_average"] = f"Above average (+{((claim_amount/avg)-1)*100:.0f}%)"
        elif claim_amount < avg * 0.5:
            comparisons["claim_vs_average"] = f"Below average ({((claim_amount/avg)-1)*100:.0f}%)"
        else:
            comparisons["claim_vs_average"] = "Within normal range"

    if processing_time_ms < 5000:
        comparisons["processing_speed"] = "Excellent (<5s)"
    elif processing_time_ms < 15000:
        comparisons["processing_speed"] = "Good (5-15s)"
    else:
        comparisons["processing_speed"] = "Needs improvement (>15s)"

    # Add trends
    trends = []
    if customer_info.get("total_claims", 0) > 3:
        trends.append("Increasing claim frequency for this customer")
    if claim_amount > 5000:
        trends.append("High-value claim contributes to quarterly targets")

    result.metrics = metrics
    result.comparisons = comparisons
    result.trends = trends

    logger.info(f"Calculated {len(metrics)} KPI metrics")
    return result.model_dump()


@tool
def create_alerts(
    claim_data: dict[str, Any],
    risk_assessment: dict[str, Any],
    insights_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Create alerts based on claim analysis.

    Generates alerts for fraud, SLA, and business conditions.

    Args:
        claim_data: The claim data
        risk_assessment: Risk assessment result
        insights_result: Generated insights

    Returns:
        AlertResult with created alerts
    """
    result = AlertResult()
    alerts = []

    claim_id = claim_data.get("claim_id", "UNKNOWN")
    claim_amount = float(claim_data.get("claim_amount", 0))
    fraud_score = risk_assessment.get("fraud_score", 0)
    risk_level = risk_assessment.get("risk_level", "low")

    # Fraud alerts
    if fraud_score >= 0.75:
        alerts.append({
            "alert_id": f"ALERT-{claim_id}-FRAUD-CRITICAL",
            "type": "fraud",
            "severity": "critical",
            "title": "Critical Fraud Risk Detected",
            "message": f"Claim {claim_id} has critical fraud indicators (score: {fraud_score:.2f})",
            "action_required": True,
            "recommended_action": "Escalate to fraud investigation unit immediately",
            "created_at": datetime.utcnow().isoformat(),
        })
    elif fraud_score >= 0.50:
        alerts.append({
            "alert_id": f"ALERT-{claim_id}-FRAUD-HIGH",
            "type": "fraud",
            "severity": "high",
            "title": "High Fraud Risk",
            "message": f"Claim {claim_id} requires manual review (score: {fraud_score:.2f})",
            "action_required": True,
            "recommended_action": "Assign to senior adjuster for review",
            "created_at": datetime.utcnow().isoformat(),
        })

    # High value alerts
    if claim_amount >= 10000:
        alerts.append({
            "alert_id": f"ALERT-{claim_id}-HIGHVALUE",
            "type": "high_value",
            "severity": "medium",
            "title": "High Value Claim",
            "message": f"Claim {claim_id} exceeds $10,000 threshold (${claim_amount:,.2f})",
            "action_required": True,
            "recommended_action": "Verify documentation and medical necessity",
            "created_at": datetime.utcnow().isoformat(),
        })

    # Churn risk alerts (from insights)
    patterns = insights_result.get("patterns_detected", [])
    if "high_churn_risk" in patterns:
        alerts.append({
            "alert_id": f"ALERT-{claim_id}-CHURN",
            "type": "retention",
            "severity": "medium",
            "title": "Customer Retention Alert",
            "message": f"Customer for claim {claim_id} has elevated churn risk",
            "action_required": False,
            "recommended_action": "Schedule satisfaction follow-up after claim resolution",
            "created_at": datetime.utcnow().isoformat(),
        })

    result.alerts = alerts
    result.total_alerts = len(alerts)
    result.high_priority_count = sum(1 for a in alerts if a["severity"] in ["critical", "high"])

    logger.info(f"Created {len(alerts)} alerts ({result.high_priority_count} high priority)")
    return result.model_dump()


@tool
def update_customer_360(
    customer_id: str,
    claim_data: dict[str, Any],
    enrichment_data: dict[str, Any],
    risk_assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Update customer 360 profile with claim data.

    Recalculates customer metrics and segment.

    Args:
        customer_id: Customer ID to update
        claim_data: The claim data
        enrichment_data: Enrichment data
        risk_assessment: Risk assessment result

    Returns:
        Customer360Result with profile updates
    """
    result = Customer360Result(customer_id=customer_id)

    customer_info = enrichment_data.get("customer_info", {})
    claim_amount = float(claim_data.get("claim_amount", 0))

    # Current values
    current_ltv = customer_info.get("lifetime_value", 0)
    current_claims = customer_info.get("total_claims", 0)
    current_paid = customer_info.get("total_paid", 0)

    # Calculate new metrics
    new_ltv = current_ltv + (claim_amount * 0.1)  # LTV contribution from claim handling
    new_claims = current_claims + 1
    expected_paid = claim_amount * enrichment_data.get("policy_info", {}).get("reimbursement_rate", 0.8)
    new_total_paid = current_paid + expected_paid

    result.new_metrics = {
        "lifetime_value": new_ltv,
        "total_claims": new_claims,
        "total_paid": new_total_paid,
        "avg_claim_amount": new_total_paid / new_claims if new_claims > 0 else 0,
        "claim_frequency_monthly": new_claims / 12,  # Simplified
        "risk_score": risk_assessment.get("fraud_score", 0),
    }

    # Determine updates to apply
    result.updates = {
        "last_claim_date": datetime.utcnow().isoformat(),
        "last_claim_id": claim_data.get("claim_id"),
        "last_claim_amount": claim_amount,
        "lifetime_value": new_ltv,
        "total_claims": new_claims,
        "total_paid": new_total_paid,
    }

    # Check for segment change
    old_tier = customer_info.get("risk_tier", "standard")
    new_risk_score = risk_assessment.get("fraud_score", 0)

    if new_risk_score > 0.5 and old_tier != "high_risk":
        result.segment_change = f"{old_tier} -> high_risk"
        result.updates["risk_tier"] = "high_risk"
    elif new_risk_score < 0.2 and old_tier == "standard" and new_claims > 3:
        result.segment_change = f"{old_tier} -> preferred"
        result.updates["risk_tier"] = "preferred"

    logger.info(f"Updated customer 360 for {customer_id}: LTV=${new_ltv:,.2f}")
    return result.model_dump()


# Export all analytics tools
GOLD_ANALYTICS_TOOLS = [
    assess_risk,
    generate_insights,
    calculate_kpi_metrics,
    create_alerts,
    update_customer_360,
]
