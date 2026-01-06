"""
Unified API Tools for LLM Agents
These tools call the Unified Claims Data API and are used by Bronze/Silver/Gold agents.

Total: 44 tools across 8 services
- PolicyService: 6 tools
- CustomerService: 6 tools
- PetService: 5 tools
- ProviderService: 5 tools
- FraudService: 6 tools
- MedicalService: 5 tools
- BillingService: 5 tools
- ValidationService: 6 tools (NEW - AI Data Quality)
"""

import httpx
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
import json

from ..config import settings

# Base URL for the Unified Claims Data API - from config
CLAIMS_API_BASE = f"{settings.PETINSURE360_URL}/api/v1"


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


def _sync_api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a sync API call to the Unified Claims Data API."""
    url = f"{CLAIMS_API_BASE}{endpoint}"
    try:
        with httpx.Client(timeout=30.0) as client:
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": str(e), "status_code": e.response.status_code}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# POLICY TOOLS (6 tools)
# =============================================================================

@tool
def get_policy(policy_id: str) -> Dict[str, Any]:
    """
    Get full policy details including coverage, limits, and exclusions.

    Args:
        policy_id: The policy ID (e.g., "POL-034")

    Returns:
        Policy details with customer name, pet info, and claims summary
    """
    return _sync_api_call(f"/policies/{policy_id}")


@tool
def check_coverage(policy_id: str, diagnosis_code: str) -> Dict[str, Any]:
    """
    Check if a diagnosis code is covered under the policy.

    Args:
        policy_id: The policy ID
        diagnosis_code: The ICD-10 diagnosis code (e.g., "S83.5")

    Returns:
        Coverage status including exclusions and waiting period info
    """
    return _sync_api_call(f"/policies/{policy_id}/coverage/{diagnosis_code}")


@tool
def get_policy_exclusions(policy_id: str) -> Dict[str, Any]:
    """
    List all exclusions for a policy including pre-existing conditions.

    Args:
        policy_id: The policy ID

    Returns:
        List of policy exclusions and pre-existing condition exclusions
    """
    return _sync_api_call(f"/policies/{policy_id}/exclusions")


@tool
def check_policy_limits(policy_id: str) -> Dict[str, Any]:
    """
    Get remaining coverage limits for a policy.

    Args:
        policy_id: The policy ID

    Returns:
        Annual limit, used amount, remaining amount, and deductible status
    """
    return _sync_api_call(f"/policies/{policy_id}/limits")


@tool
def get_waiting_periods(policy_id: str) -> Dict[str, Any]:
    """
    Get waiting period status for a policy.

    Args:
        policy_id: The policy ID

    Returns:
        Waiting period details for accident, illness, orthopedic, and cancer
    """
    return _sync_api_call(f"/policies/{policy_id}/waiting-periods")


@tool
def get_policy_history(policy_id: str) -> Dict[str, Any]:
    """
    Get policy changes and renewal history.

    Args:
        policy_id: The policy ID

    Returns:
        Timeline of policy events and claims summary
    """
    return _sync_api_call(f"/policies/{policy_id}/history")


# =============================================================================
# CUSTOMER TOOLS (6 tools)
# =============================================================================

@tool
def get_customer(customer_id: str) -> Dict[str, Any]:
    """
    Get customer profile with summary info.

    Args:
        customer_id: The customer ID (e.g., "CUST-023")

    Returns:
        Customer details, tenure, pets count, and risk assessment
    """
    return _sync_api_call(f"/customers/{customer_id}")


@tool
def get_claim_history(customer_id: str) -> Dict[str, Any]:
    """
    Get all claims for a customer.

    Args:
        customer_id: The customer ID

    Returns:
        List of claims with status breakdown and fraud flags
    """
    return _sync_api_call(f"/customers/{customer_id}/claims")


@tool
def get_customer_ltv(customer_id: str) -> Dict[str, Any]:
    """
    Calculate customer lifetime value.

    Args:
        customer_id: The customer ID

    Returns:
        Premiums paid, claims paid, net value, and profitability
    """
    return _sync_api_call(f"/customers/{customer_id}/ltv")


@tool
def get_customer_risk_tier(customer_id: str) -> Dict[str, Any]:
    """
    Get customer risk classification with factors.

    Args:
        customer_id: The customer ID

    Returns:
        Risk tier, score, factors, and recommendation
    """
    return _sync_api_call(f"/customers/{customer_id}/risk")


@tool
def get_communication_history(customer_id: str) -> Dict[str, Any]:
    """
    Get past customer interactions.

    Args:
        customer_id: The customer ID

    Returns:
        Communication history and preferred contact method
    """
    return _sync_api_call(f"/customers/{customer_id}/communications")


@tool
def get_customer_household(customer_id: str) -> Dict[str, Any]:
    """
    Get all pets and policies for customer.

    Args:
        customer_id: The customer ID

    Returns:
        All pets, policies, and total monthly premium
    """
    return _sync_api_call(f"/customers/{customer_id}/household")


# =============================================================================
# PET TOOLS (5 tools)
# =============================================================================

@tool
def get_pet_profile(pet_id: str) -> Dict[str, Any]:
    """
    Get pet details with enriched data.

    Args:
        pet_id: The pet ID (e.g., "PET-034")

    Returns:
        Pet details, age, owner, policy status, and breed risks
    """
    return _sync_api_call(f"/pets/{pet_id}")


@tool
def get_pet_medical_history(pet_id: str) -> Dict[str, Any]:
    """
    Get all medical records for a pet.

    Args:
        pet_id: The pet ID

    Returns:
        Pre-existing conditions and claim-based medical history
    """
    return _sync_api_call(f"/pets/{pet_id}/medical-history")


@tool
def get_pet_pre_existing_conditions(pet_id: str) -> Dict[str, Any]:
    """
    List pre-existing conditions for a pet.

    Args:
        pet_id: The pet ID

    Returns:
        Conditions and excluded diagnosis codes
    """
    return _sync_api_call(f"/pets/{pet_id}/conditions")


@tool
def get_breed_risks(breed: str) -> Dict[str, Any]:
    """
    Get breed-specific health risks.

    Args:
        breed: The breed name (e.g., "French Bulldog")

    Returns:
        Common conditions, risk multipliers, and average costs
    """
    return _sync_api_call(f"/pets/breed-risks/{breed}")


@tool
def check_vaccination_status(pet_id: str) -> Dict[str, Any]:
    """
    Get vaccination records for a pet.

    Args:
        pet_id: The pet ID

    Returns:
        Vaccination status and records
    """
    return _sync_api_call(f"/pets/{pet_id}/vaccinations")


# =============================================================================
# PROVIDER TOOLS (5 tools)
# =============================================================================

@tool
def verify_provider(provider_name: str) -> Dict[str, Any]:
    """
    Search and verify a provider by name.

    Args:
        provider_name: The provider name to search

    Returns:
        Matching providers with verification status
    """
    return _sync_api_call(f"/providers/search?name={provider_name}")


@tool
def get_provider_network_status(provider_id: str) -> Dict[str, Any]:
    """
    Check if provider is in network.

    Args:
        provider_id: The provider ID (e.g., "PROV-099")

    Returns:
        Network status and reimbursement adjustment
    """
    return _sync_api_call(f"/providers/{provider_id}/network-status")


@tool
def get_provider_stats(provider_id: str) -> Dict[str, Any]:
    """
    Get provider claims statistics.

    Args:
        provider_id: The provider ID

    Returns:
        Total claims, average amount, approval rate, and comparisons
    """
    return _sync_api_call(f"/providers/{provider_id}/statistics")


@tool
def get_provider_fraud_rate(provider_id: str) -> Dict[str, Any]:
    """
    Get provider fraud metrics.

    Args:
        provider_id: The provider ID

    Returns:
        Fraud rate, concentration issues, and flags
    """
    return _sync_api_call(f"/providers/{provider_id}/fraud-metrics")


@tool
def get_provider_peer_comparison(provider_id: str) -> Dict[str, Any]:
    """
    Compare provider to peers.

    Args:
        provider_id: The provider ID

    Returns:
        Comparison with regional peers on claims and ratings
    """
    return _sync_api_call(f"/providers/{provider_id}/peer-comparison")


# =============================================================================
# FRAUD TOOLS (6 tools) - CRITICAL FOR DEMO
# =============================================================================

@tool
def check_fraud_indicators(
    customer_id: str,
    pet_id: str,
    provider_id: str,
    claim_amount: float,
    diagnosis_code: str,
    service_date: str,
    claim_category: str = None,
    treatment_notes: str = None
) -> Dict[str, Any]:
    """
    Perform full fraud analysis on a claim. This is the PRIMARY fraud detection tool.

    Args:
        customer_id: Customer ID
        pet_id: Pet ID
        provider_id: Provider ID
        claim_amount: Total claim amount
        diagnosis_code: Diagnosis code
        service_date: Service date (YYYY-MM-DD)
        claim_category: Optional claim category
        treatment_notes: Optional treatment notes

    Returns:
        Fraud score, risk level, indicators, and recommendation
    """
    data = {
        "customer_id": customer_id,
        "pet_id": pet_id,
        "provider_id": provider_id,
        "claim_amount": claim_amount,
        "diagnosis_code": diagnosis_code,
        "service_date": service_date,
        "claim_category": claim_category,
        "treatment_notes": treatment_notes
    }
    return _sync_api_call("/fraud/check", method="POST", data=data)


@tool
def velocity_check(customer_id: str) -> Dict[str, Any]:
    """
    Check claims frequency for a customer.

    Args:
        customer_id: The customer ID

    Returns:
        Claims counts for 30/90/365 days and unusual flag
    """
    return _sync_api_call(f"/fraud/velocity/{customer_id}")


@tool
def duplicate_check(
    customer_id: str,
    service_date: str,
    claim_amount: float,
    diagnosis_code: str
) -> Dict[str, Any]:
    """
    Find potential duplicate claims.

    Args:
        customer_id: Customer ID
        service_date: Service date (YYYY-MM-DD)
        claim_amount: Claim amount
        diagnosis_code: Diagnosis code

    Returns:
        List of potential duplicates with confidence scores
    """
    data = {
        "customer_id": customer_id,
        "pet_id": "",
        "provider_id": "",
        "claim_amount": claim_amount,
        "diagnosis_code": diagnosis_code,
        "service_date": service_date
    }
    return _sync_api_call("/fraud/duplicate-check", method="POST", data=data)


@tool
def fraud_pattern_match(
    customer_id: str,
    provider_id: str
) -> Dict[str, Any]:
    """
    Match against known fraud patterns.

    Args:
        customer_id: Customer ID
        provider_id: Provider ID

    Returns:
        Matching fraud patterns with indicators
    """
    data = {
        "customer_id": customer_id,
        "pet_id": "",
        "provider_id": provider_id,
        "claim_amount": 0,
        "diagnosis_code": "",
        "service_date": "2024-01-01"
    }
    return _sync_api_call("/fraud/pattern-match", method="POST", data=data)


@tool
def provider_customer_analysis(provider_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Analyze relationship between provider and customer for collusion patterns.

    Args:
        provider_id: Provider ID
        customer_id: Customer ID

    Returns:
        Relationship analysis with concentration metrics
    """
    return _sync_api_call(f"/fraud/provider-customer/{provider_id}/{customer_id}")


@tool
def calculate_fraud_score(
    customer_id: str,
    pet_id: str,
    provider_id: str,
    claim_amount: float,
    diagnosis_code: str,
    service_date: str
) -> Dict[str, Any]:
    """
    Calculate ML-based fraud score.

    Args:
        customer_id: Customer ID
        pet_id: Pet ID
        provider_id: Provider ID
        claim_amount: Total claim amount
        diagnosis_code: Diagnosis code
        service_date: Service date (YYYY-MM-DD)

    Returns:
        Fraud score, risk level, and top indicators
    """
    data = {
        "customer_id": customer_id,
        "pet_id": pet_id,
        "provider_id": provider_id,
        "claim_amount": claim_amount,
        "diagnosis_code": diagnosis_code,
        "service_date": service_date
    }
    return _sync_api_call("/fraud/score", method="POST", data=data)


# =============================================================================
# MEDICAL REFERENCE TOOLS (5 tools)
# =============================================================================

@tool
def validate_diagnosis_code(code: str) -> Dict[str, Any]:
    """
    Validate a diagnosis code and get details.

    Args:
        code: The ICD-10 diagnosis code

    Returns:
        Validity, description, category, and typical costs
    """
    return _sync_api_call(f"/medical/diagnosis/{code}")


@tool
def get_treatment_benchmarks(diagnosis_code: str) -> Dict[str, Any]:
    """
    Get cost benchmarks for a diagnosis.

    Args:
        diagnosis_code: The diagnosis code

    Returns:
        Median cost, percentiles, and expected line items
    """
    return _sync_api_call(f"/medical/diagnosis/{diagnosis_code}/benchmarks")


@tool
def get_typical_treatment(diagnosis_code: str) -> Dict[str, Any]:
    """
    Get typical treatments for a diagnosis.

    Args:
        diagnosis_code: The diagnosis code

    Returns:
        Treatment approach, duration, and expected items
    """
    return _sync_api_call(f"/medical/diagnosis/{diagnosis_code}/treatments")


@tool
def check_related_conditions(diagnosis_code: str) -> Dict[str, Any]:
    """
    Get related diagnosis codes.

    Args:
        diagnosis_code: The diagnosis code

    Returns:
        Related codes and same-category diagnoses
    """
    return _sync_api_call(f"/medical/diagnosis/{diagnosis_code}/related")


@tool
def get_breed_condition_risk(breed: str, condition: str) -> Dict[str, Any]:
    """
    Get breed-specific risk for a condition.

    Args:
        breed: The breed name
        condition: The condition name

    Returns:
        Risk multiplier and interpretation
    """
    return _sync_api_call(f"/medical/breed-risk/{breed}/{condition}")


# =============================================================================
# BILLING TOOLS (5 tools)
# =============================================================================

@tool
def calculate_reimbursement(
    policy_id: str,
    claim_amount: float,
    diagnosis_code: str,
    provider_id: str = None,
    is_emergency: bool = False
) -> Dict[str, Any]:
    """
    Calculate reimbursement for a claim.

    Args:
        policy_id: Policy ID
        claim_amount: Total claim amount
        diagnosis_code: Diagnosis code
        provider_id: Optional provider ID for network adjustment
        is_emergency: Whether this is an emergency claim

    Returns:
        Detailed reimbursement calculation with explanation
    """
    data = {
        "policy_id": policy_id,
        "claim_amount": claim_amount,
        "diagnosis_code": diagnosis_code,
        "provider_id": provider_id,
        "is_emergency": is_emergency
    }
    return _sync_api_call("/billing/calculate", method="POST", data=data)


@tool
def check_deductible_status(policy_id: str) -> Dict[str, Any]:
    """
    Check if deductible has been met.

    Args:
        policy_id: Policy ID

    Returns:
        Deductible amount, met status, and remaining
    """
    return _sync_api_call(f"/billing/deductible/{policy_id}")


@tool
def get_payment_history(customer_id: str) -> Dict[str, Any]:
    """
    Get payment history for a customer.

    Args:
        customer_id: Customer ID

    Returns:
        Premium payments, claim payouts, and net position
    """
    return _sync_api_call(f"/billing/payments/{customer_id}")


@tool
def check_payment_status(claim_id: str) -> Dict[str, Any]:
    """
    Check payment status for a claim.

    Args:
        claim_id: Claim ID

    Returns:
        Claim status, amounts, and payment details
    """
    return _sync_api_call(f"/billing/claim-status/{claim_id}")


@tool
def get_annual_summary(policy_id: str) -> Dict[str, Any]:
    """
    Get annual billing summary for a policy.

    Args:
        policy_id: Policy ID

    Returns:
        Year's premiums, claims, and limit usage
    """
    return _sync_api_call(f"/billing/annual-summary/{policy_id}")


# =============================================================================
# TOOL REGISTRY
# =============================================================================

# All tools organized by service
POLICY_TOOLS = [
    get_policy,
    check_coverage,
    get_policy_exclusions,
    check_policy_limits,
    get_waiting_periods,
    get_policy_history,
]

CUSTOMER_TOOLS = [
    get_customer,
    get_claim_history,
    get_customer_ltv,
    get_customer_risk_tier,
    get_communication_history,
    get_customer_household,
]

PET_TOOLS = [
    get_pet_profile,
    get_pet_medical_history,
    get_pet_pre_existing_conditions,
    get_breed_risks,
    check_vaccination_status,
]

PROVIDER_TOOLS = [
    verify_provider,
    get_provider_network_status,
    get_provider_stats,
    get_provider_fraud_rate,
    get_provider_peer_comparison,
]

FRAUD_TOOLS = [
    check_fraud_indicators,
    velocity_check,
    duplicate_check,
    fraud_pattern_match,
    provider_customer_analysis,
    calculate_fraud_score,
]

MEDICAL_TOOLS = [
    validate_diagnosis_code,
    get_treatment_benchmarks,
    get_typical_treatment,
    check_related_conditions,
    get_breed_condition_risk,
]

BILLING_TOOLS = [
    calculate_reimbursement,
    check_deductible_status,
    get_payment_history,
    check_payment_status,
    get_annual_summary,
]


# =============================================================================
# VALIDATION TOOLS (6 tools) - AI Data Quality Detection
# =============================================================================

@tool
def validate_diagnosis_treatment_match(
    claim_id: str,
    policy_id: str,
    pet_id: str,
    provider_id: str,
    diagnosis_code: str,
    procedure_descriptions: List[str],
    claim_amount: float,
    service_date: str
) -> Dict[str, Any]:
    """
    Validate that treatments match the diagnosis - catch mismatches rules miss.

    Args:
        claim_id: The claim ID
        policy_id: The policy ID
        pet_id: The pet ID
        provider_id: The provider ID
        diagnosis_code: The diagnosis code (e.g., "S83.5")
        procedure_descriptions: List of procedure descriptions
        claim_amount: Total claim amount
        service_date: Date of service (YYYY-MM-DD)

    Returns:
        Validation result with score, issues, and recommendations
    """
    return _sync_api_call("/validation/diagnosis-treatment", "POST", {
        "claim_id": claim_id,
        "policy_id": policy_id,
        "pet_id": pet_id,
        "provider_id": provider_id,
        "diagnosis_code": diagnosis_code,
        "procedure_descriptions": procedure_descriptions,
        "medications": [],
        "claim_amount": claim_amount,
        "service_date": service_date
    })


@tool
def validate_document_consistency(
    claim_id: str,
    policy_id: str,
    pet_id: str,
    provider_id: str,
    diagnosis_code: str,
    claim_amount: float,
    service_date: str,
    invoice_pet_name: str = "",
    invoice_amount: float = 0,
    record_amount: float = 0
) -> Dict[str, Any]:
    """
    Compare invoice vs medical records for inconsistencies.

    Args:
        claim_id: The claim ID
        policy_id: The policy ID
        pet_id: The pet ID
        provider_id: The provider ID
        diagnosis_code: The diagnosis code
        claim_amount: Total claim amount
        service_date: Date of service
        invoice_pet_name: Pet name on invoice (optional)
        invoice_amount: Amount on invoice (optional)
        record_amount: Amount in medical records (optional)

    Returns:
        Document consistency check with mismatches identified
    """
    data = {
        "claim_id": claim_id,
        "policy_id": policy_id,
        "pet_id": pet_id,
        "provider_id": provider_id,
        "diagnosis_code": diagnosis_code,
        "procedure_descriptions": [],
        "medications": [],
        "claim_amount": claim_amount,
        "service_date": service_date
    }
    if invoice_pet_name or invoice_amount:
        data["invoice_data"] = {
            "pet_name": invoice_pet_name,
            "amount": invoice_amount or claim_amount,
            "date": service_date
        }
    if record_amount:
        data["medical_record_data"] = {
            "total_charges": record_amount
        }
    return _sync_api_call("/validation/document-consistency", "POST", data)


@tool
def validate_claim_sequence(
    claim_id: str,
    policy_id: str,
    pet_id: str,
    provider_id: str,
    diagnosis_code: str,
    procedure_codes: List[str],
    procedure_descriptions: List[str],
    claim_amount: float,
    service_date: str
) -> Dict[str, Any]:
    """
    Validate clinical workflow completeness and logical sequence.
    Detects missing prerequisites (e.g., surgery without pre-op bloodwork).

    Args:
        claim_id: The claim ID
        policy_id: The policy ID
        pet_id: The pet ID
        provider_id: The provider ID
        diagnosis_code: The diagnosis code
        procedure_codes: List of procedure codes
        procedure_descriptions: List of procedure descriptions
        claim_amount: Total claim amount
        service_date: Date of service

    Returns:
        Sequence validation with missing prerequisites identified
    """
    return _sync_api_call("/validation/completeness-sequence", "POST", {
        "claim_id": claim_id,
        "policy_id": policy_id,
        "pet_id": pet_id,
        "provider_id": provider_id,
        "diagnosis_code": diagnosis_code,
        "procedure_codes": procedure_codes,
        "procedure_descriptions": procedure_descriptions,
        "medications": [],
        "claim_amount": claim_amount,
        "service_date": service_date
    })


@tool
def verify_provider_license(provider_id: str, service_date: str) -> Dict[str, Any]:
    """
    Verify provider licensing is valid and compliant.
    Checks license status, expiry, DEA registration, and state requirements.

    Args:
        provider_id: The provider ID
        service_date: Date of service (YYYY-MM-DD)

    Returns:
        License verification result including compliance issues
    """
    return _sync_api_call("/validation/license-verification", "POST", {
        "claim_id": "license-check",
        "policy_id": "N/A",
        "pet_id": "N/A",
        "provider_id": provider_id,
        "diagnosis_code": "Z00.0",
        "procedure_descriptions": [],
        "medications": [],
        "claim_amount": 0,
        "service_date": service_date
    })


@tool
def validate_controlled_substances(
    claim_id: str,
    provider_id: str,
    diagnosis_code: str,
    medications: List[str],
    service_date: str
) -> Dict[str, Any]:
    """
    Validate controlled substance prescriptions for regulatory compliance.
    Checks DEA requirements, diagnosis appropriateness, and documentation.

    Args:
        claim_id: The claim ID
        provider_id: The provider ID
        diagnosis_code: The diagnosis code
        medications: List of medications prescribed
        service_date: Date of service

    Returns:
        Controlled substance compliance check with violations identified
    """
    return _sync_api_call("/validation/controlled-substance", "POST", {
        "claim_id": claim_id,
        "policy_id": "N/A",
        "pet_id": "N/A",
        "provider_id": provider_id,
        "diagnosis_code": diagnosis_code,
        "procedure_descriptions": [],
        "medications": medications,
        "claim_amount": 0,
        "service_date": service_date
    })


@tool
def validate_claim_comprehensive(
    claim_id: str,
    policy_id: str,
    pet_id: str,
    provider_id: str,
    diagnosis_code: str,
    procedure_codes: List[str],
    procedure_descriptions: List[str],
    medications: List[str],
    claim_amount: float,
    service_date: str
) -> Dict[str, Any]:
    """
    Run ALL 5 validation checks and return comprehensive data quality score.
    This is the main validation tool - use for complete claim validation.

    Checks:
    1. Diagnosis-Treatment Mismatch
    2. Document Consistency
    3. Claim Completeness & Sequence
    4. License Verification
    5. Controlled Substance Compliance

    Args:
        claim_id: The claim ID
        policy_id: The policy ID
        pet_id: The pet ID
        provider_id: The provider ID
        diagnosis_code: The diagnosis code
        procedure_codes: List of procedure codes
        procedure_descriptions: List of procedure descriptions
        medications: List of medications
        claim_amount: Total claim amount
        service_date: Date of service

    Returns:
        Comprehensive validation with overall score, all issues, and recommendation
    """
    return _sync_api_call("/validation/comprehensive", "POST", {
        "claim_id": claim_id,
        "policy_id": policy_id,
        "pet_id": pet_id,
        "provider_id": provider_id,
        "diagnosis_code": diagnosis_code,
        "procedure_codes": procedure_codes,
        "procedure_descriptions": procedure_descriptions,
        "medications": medications,
        "claim_amount": claim_amount,
        "service_date": service_date
    })


VALIDATION_TOOLS = [
    validate_diagnosis_treatment_match,
    validate_document_consistency,
    validate_claim_sequence,
    verify_provider_license,
    validate_controlled_substances,
    validate_claim_comprehensive,
]


# All tools combined
ALL_TOOLS = (
    POLICY_TOOLS +
    CUSTOMER_TOOLS +
    PET_TOOLS +
    PROVIDER_TOOLS +
    FRAUD_TOOLS +
    MEDICAL_TOOLS +
    BILLING_TOOLS +
    VALIDATION_TOOLS
)

# Tools by agent tier
BRONZE_TOOLS = POLICY_TOOLS + CUSTOMER_TOOLS + PET_TOOLS + PROVIDER_TOOLS + MEDICAL_TOOLS
SILVER_TOOLS = FRAUD_TOOLS + BILLING_TOOLS + [get_claim_history, get_customer_risk_tier]
GOLD_TOOLS = ALL_TOOLS  # Gold agent has access to everything including VALIDATION_TOOLS


def get_tools_for_agent(agent_tier: str) -> List:
    """Get appropriate tools for an agent tier."""
    if agent_tier.lower() == "bronze":
        return BRONZE_TOOLS
    elif agent_tier.lower() == "silver":
        return SILVER_TOOLS
    elif agent_tier.lower() == "gold":
        return GOLD_TOOLS
    else:
        return ALL_TOOLS
