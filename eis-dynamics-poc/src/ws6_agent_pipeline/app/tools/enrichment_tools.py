"""
Enrichment tools for the Silver Agent.

These tools handle data enrichment, normalization, business rule validation,
and score calculation for claims.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Mock data for enrichment (in production, this would come from databases/APIs)
MOCK_POLICIES = {
    "POL-2024-00567": {
        "policy_id": "POL-2024-00567",
        "policy_number": "PET-567-2024",
        "customer_id": "CUST-001",
        "pet_id": "PET-001",
        "coverage_type": "comprehensive",
        "deductible": 250.0,
        "annual_limit": 15000.0,
        "reimbursement_rate": 0.80,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "status": "active",
    },
    "POL-2024-00123": {
        "policy_id": "POL-2024-00123",
        "policy_number": "PET-123-2024",
        "customer_id": "CUST-002",
        "pet_id": "PET-002",
        "coverage_type": "accident_only",
        "deductible": 500.0,
        "annual_limit": 10000.0,
        "reimbursement_rate": 0.70,
        "start_date": "2024-03-01",
        "end_date": "2025-02-28",
        "status": "active",
    },
}

MOCK_CUSTOMERS = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "John Smith",
        "email": "john.smith@email.com",
        "member_since": "2020-05-15",
        "lifetime_value": 4500.0,
        "total_claims": 3,
        "total_paid": 2800.0,
        "risk_tier": "standard",
        "churn_risk": 0.15,
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Jane Doe",
        "email": "jane.doe@email.com",
        "member_since": "2023-01-10",
        "lifetime_value": 1200.0,
        "total_claims": 1,
        "total_paid": 750.0,
        "risk_tier": "low",
        "churn_risk": 0.08,
    },
}

MOCK_PETS = {
    "PET-001": {
        "pet_id": "PET-001",
        "name": "Max",
        "species": "dog",
        "breed": "Golden Retriever",
        "age_years": 5,
        "weight_lbs": 70,
        "known_conditions": ["hip_dysplasia_risk"],
    },
    "PET-002": {
        "pet_id": "PET-002",
        "name": "Luna",
        "species": "cat",
        "breed": "Maine Coon",
        "age_years": 3,
        "weight_lbs": 15,
        "known_conditions": [],
    },
}

MOCK_PROVIDERS = {
    "City Pet Hospital": {
        "provider_id": "PROV-001",
        "name": "City Pet Hospital",
        "type": "veterinary_hospital",
        "is_in_network": True,
        "avg_claim_amount": 850.0,
        "claims_processed": 150,
        "fraud_rate": 0.02,
        "rating": 4.5,
    },
    "Emergency Vet Clinic": {
        "provider_id": "PROV-002",
        "name": "Emergency Vet Clinic",
        "type": "emergency_clinic",
        "is_in_network": True,
        "avg_claim_amount": 1500.0,
        "claims_processed": 80,
        "fraud_rate": 0.01,
        "rating": 4.8,
    },
}

# ICD-10-VET code mappings
DIAGNOSIS_CODE_MAPPINGS = {
    "S83.50": {"category": "injury", "subcategory": "ligament_tear", "description": "ACL/CCL tear"},
    "M16.1": {"category": "orthopedic", "subcategory": "joint_disorder", "description": "Hip dysplasia"},
    "C80.1": {"category": "oncology", "subcategory": "malignant_neoplasm", "description": "Cancer - unspecified"},
    "C85.9": {"category": "oncology", "subcategory": "lymphoma", "description": "Lymphoma"},
    "E11.9": {"category": "endocrine", "subcategory": "diabetes", "description": "Diabetes mellitus"},
    "N18.9": {"category": "renal", "subcategory": "kidney_disease", "description": "Chronic kidney disease"},
}

# Business rules
COVERAGE_RULES = {
    "comprehensive": {
        "covered_categories": ["injury", "illness", "orthopedic", "oncology", "endocrine", "renal", "emergency"],
        "waiting_period_days": 14,
        "annual_limit_applies": True,
    },
    "accident_only": {
        "covered_categories": ["injury", "emergency"],
        "waiting_period_days": 0,
        "annual_limit_applies": True,
    },
    "wellness": {
        "covered_categories": ["wellness", "preventive"],
        "waiting_period_days": 0,
        "annual_limit_applies": False,
    },
}


class EnrichmentResult(BaseModel):
    """Result of data enrichment."""
    policy_info: dict[str, Any] = Field(default_factory=dict)
    customer_info: dict[str, Any] = Field(default_factory=dict)
    pet_info: dict[str, Any] = Field(default_factory=dict)
    provider_info: dict[str, Any] = Field(default_factory=dict)
    enrichment_summary: str = ""


class NormalizationResult(BaseModel):
    """Result of data normalization."""
    normalized_diagnosis: dict[str, Any] = Field(default_factory=dict)
    claim_category: str = ""
    claim_subcategory: str = ""
    derived_values: dict[str, Any] = Field(default_factory=dict)


class BusinessRulesResult(BaseModel):
    """Result of business rules validation."""
    is_covered: bool = True
    passed: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    coverage_percentage: float = 0.0
    expected_reimbursement: float = 0.0


class QualityScoreResult(BaseModel):
    """Result of quality scoring."""
    enrichment_completeness: float = 0.0
    data_confidence: float = 0.0
    overall_silver_score: float = 0.0
    scoring_notes: list[str] = Field(default_factory=list)


@tool
def enrich_claim(
    claim_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Enrich claim data with policy, customer, pet, and provider information.

    Looks up related entities and adds context to the claim.

    Args:
        claim_data: The claim data to enrich

    Returns:
        EnrichmentResult with all enrichment data
    """
    result = EnrichmentResult()
    enrichment_notes = []

    # Enrich with policy info
    policy_id = claim_data.get("policy_id", "")
    if policy_id in MOCK_POLICIES:
        result.policy_info = MOCK_POLICIES[policy_id]
        enrichment_notes.append(f"Found policy: {result.policy_info.get('policy_number')}")
    else:
        # Create synthetic policy for demo
        result.policy_info = {
            "policy_id": policy_id,
            "coverage_type": "comprehensive",
            "deductible": 250.0,
            "annual_limit": 10000.0,
            "reimbursement_rate": 0.80,
            "status": "active",
        }
        enrichment_notes.append(f"Created synthetic policy data for {policy_id}")

    # Enrich with customer info
    customer_id = claim_data.get("customer_id", "")
    if customer_id in MOCK_CUSTOMERS:
        result.customer_info = MOCK_CUSTOMERS[customer_id]
        enrichment_notes.append(f"Found customer: {result.customer_info.get('name')}")
    else:
        # Create synthetic customer for demo
        result.customer_info = {
            "customer_id": customer_id,
            "name": "Demo Customer",
            "member_since": "2023-01-01",
            "lifetime_value": 2000.0,
            "total_claims": random.randint(0, 5),
            "total_paid": random.uniform(0, 3000),
            "risk_tier": "standard",
            "churn_risk": random.uniform(0.05, 0.25),
        }
        enrichment_notes.append(f"Created synthetic customer data for {customer_id}")

    # Enrich with pet info
    pet_id = claim_data.get("pet_id") or result.policy_info.get("pet_id", "")
    if pet_id in MOCK_PETS:
        result.pet_info = MOCK_PETS[pet_id]
        enrichment_notes.append(f"Found pet: {result.pet_info.get('name')} ({result.pet_info.get('breed')})")
    else:
        # Create synthetic pet for demo
        result.pet_info = {
            "pet_id": pet_id or "PET-UNKNOWN",
            "name": "Unknown Pet",
            "species": "dog",
            "breed": "Mixed",
            "age_years": 4,
            "weight_lbs": 45,
            "known_conditions": [],
        }
        enrichment_notes.append("Created synthetic pet data")

    # Enrich with provider info
    provider_name = claim_data.get("provider_name", "")
    if provider_name in MOCK_PROVIDERS:
        result.provider_info = MOCK_PROVIDERS[provider_name]
        enrichment_notes.append(f"Found provider: {provider_name} (in-network: {result.provider_info.get('is_in_network')})")
    else:
        # Create synthetic provider for demo
        result.provider_info = {
            "provider_id": f"PROV-{hash(provider_name) % 10000:04d}" if provider_name else "PROV-UNKNOWN",
            "name": provider_name or "Unknown Provider",
            "type": "veterinary_clinic",
            "is_in_network": random.random() > 0.3,
            "avg_claim_amount": random.uniform(500, 1500),
            "claims_processed": random.randint(10, 100),
            "fraud_rate": random.uniform(0.01, 0.05),
            "rating": random.uniform(3.5, 5.0),
        }
        enrichment_notes.append(f"Created synthetic provider data for {provider_name or 'unknown provider'}")

    result.enrichment_summary = "; ".join(enrichment_notes)

    logger.info(f"Claim enrichment complete: {len(enrichment_notes)} enrichments applied")
    return result.model_dump()


@tool
def normalize_values(
    claim_data: dict[str, Any],
    diagnosis_code: Optional[str] = None,
) -> dict[str, Any]:
    """
    Normalize claim values and map diagnosis codes.

    Standardizes codes, categories, and calculates derived values.

    Args:
        claim_data: The claim data to normalize
        diagnosis_code: Optional diagnosis code to normalize

    Returns:
        NormalizationResult with normalized data
    """
    result = NormalizationResult()

    # Normalize diagnosis code
    code = diagnosis_code or claim_data.get("diagnosis_code", "")
    if code and code in DIAGNOSIS_CODE_MAPPINGS:
        mapping = DIAGNOSIS_CODE_MAPPINGS[code]
        result.normalized_diagnosis = {
            "original_code": code,
            "icd10_code": code,
            "category": mapping["category"],
            "subcategory": mapping["subcategory"],
            "description": mapping["description"],
        }
        result.claim_category = mapping["category"]
        result.claim_subcategory = mapping["subcategory"]
    else:
        # Handle unknown codes
        result.normalized_diagnosis = {
            "original_code": code,
            "icd10_code": code or "UNKNOWN",
            "category": "general",
            "subcategory": "unclassified",
            "description": claim_data.get("diagnosis_description", "Unknown condition"),
        }
        result.claim_category = "general"
        result.claim_subcategory = "unclassified"

    # Calculate derived values
    claim_amount = float(claim_data.get("claim_amount", 0))
    claim_type = str(claim_data.get("claim_type", "accident")).lower()

    result.derived_values = {
        "claim_amount_normalized": claim_amount,
        "claim_type_normalized": claim_type,
        "claim_size": "small" if claim_amount < 500 else "medium" if claim_amount < 2000 else "large",
        "is_emergency": claim_type == "emergency" or result.claim_category == "emergency",
        "is_chronic": result.claim_category in ["endocrine", "renal", "oncology"],
        "processing_priority": 1 if claim_type == "emergency" else 2 if claim_amount > 5000 else 3,
    }

    logger.info(f"Value normalization complete: category={result.claim_category}")
    return result.model_dump()


@tool
def apply_business_rules(
    claim_data: dict[str, Any],
    policy_info: dict[str, Any],
    normalized_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply business rules to validate claim coverage.

    Checks coverage eligibility, limits, and calculates reimbursement.

    Args:
        claim_data: The claim data
        policy_info: Policy information
        normalized_data: Normalized claim data

    Returns:
        BusinessRulesResult with validation results
    """
    result = BusinessRulesResult()

    coverage_type = policy_info.get("coverage_type", "comprehensive")
    claim_category = normalized_data.get("claim_category", "general")
    claim_amount = float(claim_data.get("claim_amount", 0))

    # Get coverage rules
    rules = COVERAGE_RULES.get(coverage_type, COVERAGE_RULES["comprehensive"])

    # Rule 1: Check if category is covered
    if claim_category in rules["covered_categories"] or "general" in rules["covered_categories"]:
        result.passed.append(f"Category '{claim_category}' is covered under {coverage_type} plan")
    else:
        result.failed.append(f"Category '{claim_category}' is not covered under {coverage_type} plan")
        result.is_covered = False

    # Rule 2: Check waiting period
    policy_start = policy_info.get("start_date", "2024-01-01")
    treatment_date = claim_data.get("treatment_date", datetime.utcnow().strftime("%Y-%m-%d"))
    try:
        start = datetime.strptime(policy_start[:10], "%Y-%m-%d")
        treatment = datetime.strptime(treatment_date[:10], "%Y-%m-%d")
        days_since_start = (treatment - start).days

        if days_since_start >= rules["waiting_period_days"]:
            result.passed.append(f"Waiting period satisfied ({days_since_start} days >= {rules['waiting_period_days']} required)")
        else:
            result.failed.append(f"Waiting period not met ({days_since_start} days < {rules['waiting_period_days']} required)")
            result.is_covered = False
    except Exception:
        result.warnings.append("Could not verify waiting period")

    # Rule 3: Check annual limit
    annual_limit = float(policy_info.get("annual_limit", 10000))
    total_paid = float(policy_info.get("year_to_date_paid", 0))
    remaining_limit = annual_limit - total_paid

    if claim_amount <= remaining_limit:
        result.passed.append(f"Within annual limit (${claim_amount:,.2f} <= ${remaining_limit:,.2f} remaining)")
    else:
        result.warnings.append(f"Claim exceeds remaining annual limit (${claim_amount:,.2f} > ${remaining_limit:,.2f})")
        # Partial coverage
        claim_amount = remaining_limit

    # Rule 4: Apply deductible
    deductible = float(policy_info.get("deductible", 0))
    deductible_met = policy_info.get("deductible_met", False)

    if deductible_met:
        result.passed.append("Deductible already met for this policy period")
        amount_after_deductible = claim_amount
    else:
        amount_after_deductible = max(0, claim_amount - deductible)
        if deductible > 0:
            result.passed.append(f"Applied deductible of ${deductible:,.2f}")

    # Rule 5: Calculate reimbursement
    reimbursement_rate = float(policy_info.get("reimbursement_rate", 0.80))
    result.expected_reimbursement = amount_after_deductible * reimbursement_rate
    result.coverage_percentage = reimbursement_rate * 100

    result.passed.append(f"Calculated reimbursement: ${result.expected_reimbursement:,.2f} ({reimbursement_rate:.0%})")

    # Rule 6: Check provider network
    if claim_data.get("provider_info", {}).get("is_in_network", True):
        result.passed.append("Provider is in-network")
    else:
        result.warnings.append("Provider is out-of-network - reduced coverage may apply")
        result.expected_reimbursement *= 0.7  # 30% reduction for out-of-network

    logger.info(f"Business rules applied: covered={result.is_covered}, reimbursement=${result.expected_reimbursement:,.2f}")
    return result.model_dump()


@tool
def calculate_quality_scores(
    enrichment_result: dict[str, Any],
    normalized_result: dict[str, Any],
    business_rules_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate overall quality scores for the silver layer record.

    Assesses enrichment completeness and data confidence.

    Args:
        enrichment_result: Results from enrichment
        normalized_result: Results from normalization
        business_rules_result: Results from business rules

    Returns:
        QualityScoreResult with scores and notes
    """
    result = QualityScoreResult()
    scoring_notes = []

    # Enrichment completeness score
    enrichment_fields = ["policy_info", "customer_info", "pet_info", "provider_info"]
    present_enrichments = sum(
        1 for field in enrichment_fields
        if enrichment_result.get(field) and len(enrichment_result[field]) > 0
    )
    result.enrichment_completeness = present_enrichments / len(enrichment_fields)
    scoring_notes.append(f"Enrichment completeness: {result.enrichment_completeness:.0%}")

    # Data confidence score
    confidence_factors = []

    # Check if we have real data vs synthetic
    if "synthetic" not in enrichment_result.get("enrichment_summary", "").lower():
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.6)

    # Check if diagnosis was properly normalized
    if normalized_result.get("claim_category") != "general":
        confidence_factors.append(1.0)
    else:
        confidence_factors.append(0.7)

    # Check business rules pass rate
    passed = len(business_rules_result.get("passed", []))
    failed = len(business_rules_result.get("failed", []))
    total_rules = passed + failed
    if total_rules > 0:
        confidence_factors.append(passed / total_rules)
    else:
        confidence_factors.append(0.5)

    result.data_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    scoring_notes.append(f"Data confidence: {result.data_confidence:.0%}")

    # Overall silver score
    result.overall_silver_score = (
        result.enrichment_completeness * 0.4 +
        result.data_confidence * 0.6
    )
    scoring_notes.append(f"Overall silver score: {result.overall_silver_score:.0%}")

    result.scoring_notes = scoring_notes

    logger.info(f"Quality scoring complete: overall={result.overall_silver_score:.0%}")
    return result.model_dump()


@tool
def get_customer_claim_history(
    customer_id: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Retrieve customer's claim history for context.

    Args:
        customer_id: The customer ID
        limit: Maximum number of claims to return

    Returns:
        Customer claim history with summary stats
    """
    # In production, this would query a database
    # For demo, generate synthetic history

    history = []
    num_claims = random.randint(1, min(5, limit))

    for i in range(num_claims):
        claim_date = datetime.utcnow() - timedelta(days=random.randint(30, 365))
        history.append({
            "claim_id": f"CLM-HIST-{i+1:04d}",
            "claim_date": claim_date.strftime("%Y-%m-%d"),
            "claim_type": random.choice(["accident", "illness", "wellness"]),
            "claim_amount": round(random.uniform(100, 2000), 2),
            "status": "paid",
            "paid_amount": round(random.uniform(50, 1500), 2),
        })

    total_claims = len(history)
    total_amount = sum(c["claim_amount"] for c in history)
    total_paid = sum(c["paid_amount"] for c in history)

    return {
        "customer_id": customer_id,
        "claims": history,
        "summary": {
            "total_claims": total_claims,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "avg_claim_amount": total_amount / total_claims if total_claims > 0 else 0,
            "claim_frequency": total_claims / 12,  # claims per month
        },
    }


# Export all enrichment tools
SILVER_ENRICHMENT_TOOLS = [
    enrich_claim,
    normalize_values,
    apply_business_rules,
    calculate_quality_scores,
    get_customer_claim_history,
]
