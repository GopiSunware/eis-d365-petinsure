"""
Validation tools for the Bronze Agent.

These tools handle schema validation, anomaly detection, data cleaning,
and quality assessment for incoming claim data.
"""

import logging
import re
from datetime import datetime
from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Standard diagnosis code patterns
DIAGNOSIS_CODE_PATTERNS = {
    "ICD-10-VET": r"^[A-Z]\d{2}(\.\d{1,2})?$",
    "CUSTOM": r"^[A-Z]{2,4}-[A-Z0-9-]+$",
}

# Expected claim amount ranges by type
CLAIM_AMOUNT_RANGES = {
    "accident": (100, 15000),
    "illness": (50, 10000),
    "wellness": (20, 500),
    "emergency": (500, 25000),
    "routine": (25, 300),
}

# Required fields for a valid claim
REQUIRED_FIELDS = [
    "claim_id",
    "policy_id",
    "customer_id",
    "claim_amount",
]

# Optional but important fields
OPTIONAL_FIELDS = [
    "claim_type",
    "diagnosis_code",
    "diagnosis_description",
    "treatment_date",
    "submission_date",
    "provider_name",
    "pet_id",
]


class ValidationResult(BaseModel):
    """Result of schema validation."""
    is_valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    fields_checked: int = 0
    missing_required: list[str] = Field(default_factory=list)
    missing_optional: list[str] = Field(default_factory=list)


class AnomalyResult(BaseModel):
    """Result of anomaly detection."""
    is_anomalous: bool = False
    anomalies: list[str] = Field(default_factory=list)
    risk_indicators: list[str] = Field(default_factory=list)
    anomaly_score: float = 0.0


class CleaningResult(BaseModel):
    """Result of data cleaning."""
    cleaned_data: dict[str, Any] = Field(default_factory=dict)
    changes_made: list[str] = Field(default_factory=list)
    normalized_fields: list[str] = Field(default_factory=list)


class QualityResult(BaseModel):
    """Result of quality assessment."""
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    consistency_score: float = 0.0
    overall_score: float = 0.0
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


@tool
def validate_schema(claim_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate claim data against the expected schema.

    Checks for required fields, data types, and basic constraints.

    Args:
        claim_data: The raw claim data to validate

    Returns:
        ValidationResult with validation status and any errors/warnings
    """
    result = ValidationResult()
    result.fields_checked = len(claim_data)

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in claim_data or claim_data[field] is None:
            result.errors.append(f"Missing required field: {field}")
            result.missing_required.append(field)
            result.is_valid = False
        elif field == "claim_id" and not claim_data[field]:
            result.errors.append("claim_id cannot be empty")
            result.is_valid = False

    # Check optional fields
    for field in OPTIONAL_FIELDS:
        if field not in claim_data or claim_data[field] is None:
            result.missing_optional.append(field)
            result.warnings.append(f"Optional field missing: {field}")

    # Validate claim_amount
    if "claim_amount" in claim_data and claim_data["claim_amount"] is not None:
        try:
            amount = float(claim_data["claim_amount"])
            if amount <= 0:
                result.errors.append("claim_amount must be positive")
                result.is_valid = False
            elif amount > 100000:
                result.warnings.append(f"Unusually high claim amount: ${amount:,.2f}")
        except (ValueError, TypeError):
            result.errors.append("claim_amount must be a number")
            result.is_valid = False

    # Validate claim_type if present
    if "claim_type" in claim_data and claim_data["claim_type"]:
        valid_types = ["accident", "illness", "wellness", "emergency", "routine"]
        claim_type = str(claim_data["claim_type"]).lower()
        if claim_type not in valid_types:
            result.warnings.append(f"Non-standard claim_type: {claim_type}")

    # Validate diagnosis_code format if present
    if "diagnosis_code" in claim_data and claim_data["diagnosis_code"]:
        code = str(claim_data["diagnosis_code"])
        is_valid_format = False
        for pattern_name, pattern in DIAGNOSIS_CODE_PATTERNS.items():
            if re.match(pattern, code):
                is_valid_format = True
                break
        if not is_valid_format:
            result.warnings.append(f"Non-standard diagnosis_code format: {code}")

    # Validate dates if present
    for date_field in ["treatment_date", "submission_date"]:
        if date_field in claim_data and claim_data[date_field]:
            try:
                date_str = str(claim_data[date_field])
                # Try common date formats
                parsed = None
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        parsed = datetime.strptime(date_str[:10], fmt[:10])
                        break
                    except ValueError:
                        continue
                if not parsed:
                    result.warnings.append(f"Could not parse {date_field}: {date_str}")
                elif parsed > datetime.utcnow():
                    result.warnings.append(f"{date_field} is in the future")
            except Exception as e:
                result.warnings.append(f"Error validating {date_field}: {str(e)}")

    logger.info(f"Schema validation complete: valid={result.is_valid}, errors={len(result.errors)}")
    return result.model_dump()


@tool
def detect_anomalies(
    claim_data: dict[str, Any],
    historical_claims: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """
    Detect anomalies and suspicious patterns in claim data.

    Checks for duplicate claims, unusual amounts, and other red flags.

    Args:
        claim_data: The claim data to analyze
        historical_claims: Optional list of previous claims for comparison

    Returns:
        AnomalyResult with detected anomalies and risk indicators
    """
    result = AnomalyResult()
    historical_claims = historical_claims or []

    claim_type = str(claim_data.get("claim_type", "accident")).lower()
    claim_amount = float(claim_data.get("claim_amount", 0))
    claim_id = claim_data.get("claim_id", "")
    customer_id = claim_data.get("customer_id", "")

    # Check for duplicate claim IDs
    for hist_claim in historical_claims:
        if hist_claim.get("claim_id") == claim_id:
            result.anomalies.append(f"Duplicate claim ID detected: {claim_id}")
            result.is_anomalous = True
            result.anomaly_score += 0.5

    # Check claim amount against expected range
    if claim_type in CLAIM_AMOUNT_RANGES:
        min_amount, max_amount = CLAIM_AMOUNT_RANGES[claim_type]
        if claim_amount < min_amount:
            result.risk_indicators.append(
                f"Claim amount ${claim_amount:,.2f} is below typical range for {claim_type}"
            )
            result.anomaly_score += 0.1
        elif claim_amount > max_amount:
            result.anomalies.append(
                f"Claim amount ${claim_amount:,.2f} exceeds typical range for {claim_type} "
                f"(expected ${min_amount:,.2f} - ${max_amount:,.2f})"
            )
            result.is_anomalous = True
            result.anomaly_score += 0.3

    # Check for multiple claims in short period
    customer_claims = [c for c in historical_claims if c.get("customer_id") == customer_id]
    if len(customer_claims) >= 5:
        result.risk_indicators.append(
            f"Customer has {len(customer_claims)} recent claims"
        )
        result.anomaly_score += 0.2

    # Check for round number amounts (potential fabrication indicator)
    if claim_amount > 100 and claim_amount % 100 == 0:
        result.risk_indicators.append(
            f"Suspiciously round claim amount: ${claim_amount:,.2f}"
        )
        result.anomaly_score += 0.1

    # Check provider patterns
    provider_name = claim_data.get("provider_name", "")
    if provider_name:
        provider_claims = [c for c in historical_claims if c.get("provider_name") == provider_name]
        if len(provider_claims) >= 10:
            avg_amount = sum(c.get("claim_amount", 0) for c in provider_claims) / len(provider_claims)
            if claim_amount > avg_amount * 2:
                result.risk_indicators.append(
                    f"Claim amount is 2x higher than provider average"
                )
                result.anomaly_score += 0.15

    # Normalize anomaly score to 0-1 range
    result.anomaly_score = min(1.0, result.anomaly_score)

    # Set anomalous flag if score exceeds threshold
    if result.anomaly_score >= 0.4:
        result.is_anomalous = True

    logger.info(f"Anomaly detection complete: anomalous={result.is_anomalous}, score={result.anomaly_score:.2f}")
    return result.model_dump()


@tool
def clean_data(claim_data: dict[str, Any]) -> dict[str, Any]:
    """
    Clean and normalize claim data.

    Fixes formatting issues, standardizes values, and handles missing data.

    Args:
        claim_data: The raw claim data to clean

    Returns:
        CleaningResult with cleaned data and list of changes made
    """
    result = CleaningResult()
    cleaned = claim_data.copy()

    # Normalize claim_type
    if "claim_type" in cleaned and cleaned["claim_type"]:
        original = cleaned["claim_type"]
        cleaned["claim_type"] = str(original).lower().strip()
        if cleaned["claim_type"] != original:
            result.changes_made.append(f"Normalized claim_type: '{original}' -> '{cleaned['claim_type']}'")
            result.normalized_fields.append("claim_type")

    # Normalize diagnosis_code
    if "diagnosis_code" in cleaned and cleaned["diagnosis_code"]:
        original = cleaned["diagnosis_code"]
        code = str(original).upper().strip()

        # Map common pet diagnosis codes to ICD-10-VET format
        code_mappings = {
            "K9-ACL": "S83.50",
            "K9-ACL-TEAR": "S83.50",
            "ACL-TEAR": "S83.50",
            "K9-HIP": "M16.1",
            "HIP-DYSPLASIA": "M16.1",
            "K9-CANCER": "C80.1",
            "LYMPHOMA": "C85.9",
            "DIABETES": "E11.9",
            "K9-DIABETES": "E11.9",
            "KIDNEY-DISEASE": "N18.9",
            "CKD": "N18.9",
        }

        if code in code_mappings:
            cleaned["diagnosis_code"] = code_mappings[code]
            cleaned["original_diagnosis_code"] = original
            result.changes_made.append(
                f"Normalized diagnosis_code: '{original}' -> '{cleaned['diagnosis_code']}'"
            )
            result.normalized_fields.append("diagnosis_code")
        elif code != original:
            cleaned["diagnosis_code"] = code
            result.changes_made.append(f"Uppercased diagnosis_code: '{original}' -> '{code}'")

    # Normalize provider_name
    if "provider_name" in cleaned and cleaned["provider_name"]:
        original = cleaned["provider_name"]
        normalized = " ".join(str(original).strip().split())  # Remove extra whitespace
        normalized = normalized.title()
        if normalized != original:
            cleaned["provider_name"] = normalized
            result.changes_made.append(f"Normalized provider_name: '{original}' -> '{normalized}'")
            result.normalized_fields.append("provider_name")

    # Ensure claim_amount is a float
    if "claim_amount" in cleaned:
        original = cleaned["claim_amount"]
        try:
            cleaned["claim_amount"] = float(original)
            if str(original) != str(cleaned["claim_amount"]):
                result.changes_made.append(f"Converted claim_amount to float: {original} -> {cleaned['claim_amount']}")
        except (ValueError, TypeError):
            pass

    # Normalize dates to ISO format
    for date_field in ["treatment_date", "submission_date"]:
        if date_field in cleaned and cleaned[date_field]:
            original = cleaned[date_field]
            try:
                date_str = str(original)
                parsed = None
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        parsed = datetime.strptime(date_str[:10], fmt[:len(fmt.split("T")[0])])
                        break
                    except ValueError:
                        continue
                if parsed:
                    iso_date = parsed.strftime("%Y-%m-%d")
                    if iso_date != date_str:
                        cleaned[date_field] = iso_date
                        result.changes_made.append(f"Normalized {date_field}: '{original}' -> '{iso_date}'")
                        result.normalized_fields.append(date_field)
            except Exception:
                pass

    # Add processing metadata
    cleaned["_cleaned_at"] = datetime.utcnow().isoformat()
    cleaned["_changes_count"] = len(result.changes_made)

    result.cleaned_data = cleaned

    logger.info(f"Data cleaning complete: {len(result.changes_made)} changes made")
    return result.model_dump()


@tool
def assess_quality(claim_data: dict[str, Any]) -> dict[str, Any]:
    """
    Assess the overall quality of claim data.

    Calculates completeness, accuracy, and consistency scores.

    Args:
        claim_data: The claim data to assess

    Returns:
        QualityResult with quality scores and recommendations
    """
    result = QualityResult()

    all_fields = REQUIRED_FIELDS + OPTIONAL_FIELDS
    total_fields = len(all_fields)

    # Completeness score: percentage of fields that have values
    present_fields = sum(
        1 for field in all_fields
        if field in claim_data and claim_data[field] is not None and claim_data[field] != ""
    )
    result.completeness_score = present_fields / total_fields if total_fields > 0 else 0

    # Accuracy score: based on format validation
    accuracy_checks = 0
    accuracy_passed = 0

    # Check claim_id format
    if "claim_id" in claim_data and claim_data["claim_id"]:
        accuracy_checks += 1
        claim_id = str(claim_data["claim_id"])
        if re.match(r"^CLM-\d{8}-\d+$", claim_id) or re.match(r"^[A-Z0-9-]+$", claim_id):
            accuracy_passed += 1
        else:
            result.issues.append("claim_id has non-standard format")

    # Check policy_id format
    if "policy_id" in claim_data and claim_data["policy_id"]:
        accuracy_checks += 1
        policy_id = str(claim_data["policy_id"])
        if re.match(r"^POL-\d{4}-\d+$", policy_id) or re.match(r"^[A-Z0-9-]+$", policy_id):
            accuracy_passed += 1
        else:
            result.issues.append("policy_id has non-standard format")

    # Check diagnosis_code format
    if "diagnosis_code" in claim_data and claim_data["diagnosis_code"]:
        accuracy_checks += 1
        code = str(claim_data["diagnosis_code"])
        is_valid_format = any(
            re.match(pattern, code)
            for pattern in DIAGNOSIS_CODE_PATTERNS.values()
        )
        if is_valid_format:
            accuracy_passed += 1
        else:
            result.issues.append("diagnosis_code has non-standard format")

    result.accuracy_score = accuracy_passed / accuracy_checks if accuracy_checks > 0 else 1.0

    # Consistency score: check for logical consistency
    consistency_checks = 0
    consistency_passed = 0

    # Check that claim_amount is reasonable for claim_type
    if "claim_amount" in claim_data and "claim_type" in claim_data:
        claim_type = str(claim_data.get("claim_type", "")).lower()
        claim_amount = float(claim_data.get("claim_amount", 0))

        if claim_type in CLAIM_AMOUNT_RANGES:
            consistency_checks += 1
            min_amt, max_amt = CLAIM_AMOUNT_RANGES[claim_type]
            if min_amt <= claim_amount <= max_amt:
                consistency_passed += 1
            else:
                result.issues.append(
                    f"claim_amount ${claim_amount:,.2f} is outside expected range for {claim_type}"
                )

    # Check that treatment_date is not after submission_date
    if "treatment_date" in claim_data and "submission_date" in claim_data:
        if claim_data["treatment_date"] and claim_data["submission_date"]:
            consistency_checks += 1
            try:
                treatment = datetime.fromisoformat(str(claim_data["treatment_date"])[:10])
                submission = datetime.fromisoformat(str(claim_data["submission_date"])[:10])
                if treatment <= submission:
                    consistency_passed += 1
                else:
                    result.issues.append("treatment_date is after submission_date")
            except Exception:
                pass

    result.consistency_score = consistency_passed / consistency_checks if consistency_checks > 0 else 1.0

    # Calculate overall score (weighted average)
    result.overall_score = (
        result.completeness_score * 0.4 +
        result.accuracy_score * 0.3 +
        result.consistency_score * 0.3
    )

    # Generate recommendations
    if result.completeness_score < 0.8:
        result.recommendations.append("Improve data completeness by adding missing optional fields")
    if result.accuracy_score < 0.8:
        result.recommendations.append("Review and fix data format issues")
    if result.consistency_score < 0.8:
        result.recommendations.append("Check for logical inconsistencies in claim data")
    if result.overall_score >= 0.9:
        result.recommendations.append("Data quality is excellent")
    elif result.overall_score >= 0.7:
        result.recommendations.append("Data quality is acceptable for processing")
    else:
        result.recommendations.append("Data quality is below threshold, manual review recommended")

    logger.info(f"Quality assessment complete: overall_score={result.overall_score:.2f}")
    return result.model_dump()


# Export all tools
BRONZE_VALIDATION_TOOLS = [
    validate_schema,
    detect_anomalies,
    clean_data,
    assess_quality,
]
