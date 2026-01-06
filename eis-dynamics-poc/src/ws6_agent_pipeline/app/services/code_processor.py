"""
Code-Driven Claims Processor

This module implements the TRADITIONAL code-driven approach to claims
processing. It mirrors the PetInsure360 medallion processing logic
for 1-to-1 comparison with the agent-driven approach.

The code-driven approach uses:
- Deterministic rules and calculations
- Fixed validation logic
- Hardcoded business rules
- No AI reasoning or adaptation
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class CodeDrivenProcessor:
    """
    Traditional code-driven claims processor.

    Implements Bronze -> Silver -> Gold transformation
    using deterministic logic (no AI).
    """

    # Validation rules (hardcoded)
    REQUIRED_FIELDS = [
        "claim_id", "claim_type", "claim_amount",
        "service_date", "diagnosis_code"
    ]

    # Business rules (hardcoded)
    DEDUCTIBLE = 250.0
    REIMBURSEMENT_RATE = 0.80
    OUT_OF_NETWORK_PENALTY = 0.20

    # Fraud detection thresholds (hardcoded)
    HIGH_VALUE_THRESHOLD = 5000.0
    SUSPICIOUS_AMOUNT_PATTERNS = [1000, 2000, 5000, 10000]

    async def process_claim(
        self,
        claim_data: dict[str, Any],
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a claim through Bronze -> Silver -> Gold layers.

        Returns complete processing result with timing and decisions.
        """
        run_id = run_id or f"CODE-{uuid4().hex[:8].upper()}"
        start_time = datetime.utcnow()

        result = {
            "run_id": run_id,
            "processing_type": "code_driven",
            "claim_id": claim_data.get("claim_id", "UNKNOWN"),
            "started_at": start_time.isoformat(),
            "stages": {},
            "reasoning": [],  # Empty - code doesn't explain itself
        }

        try:
            # Bronze Layer
            bronze_start = datetime.utcnow()
            bronze_result = self._process_bronze(claim_data)
            bronze_end = datetime.utcnow()

            result["stages"]["bronze"] = {
                **bronze_result,
                "processing_time_ms": (bronze_end - bronze_start).total_seconds() * 1000,
            }

            # Check if Bronze rejected the claim
            if bronze_result["decision"] == "REJECT":
                result["status"] = "rejected"
                result["final_decision"] = "REJECT"
                result["completed_at"] = datetime.utcnow().isoformat()
                result["total_processing_time_ms"] = (
                    datetime.utcnow() - start_time
                ).total_seconds() * 1000
                return result

            # Silver Layer
            silver_start = datetime.utcnow()
            silver_result = self._process_silver(claim_data, bronze_result)
            silver_end = datetime.utcnow()

            result["stages"]["silver"] = {
                **silver_result,
                "processing_time_ms": (silver_end - silver_start).total_seconds() * 1000,
            }

            # Gold Layer
            gold_start = datetime.utcnow()
            gold_result = self._process_gold(claim_data, bronze_result, silver_result)
            gold_end = datetime.utcnow()

            result["stages"]["gold"] = {
                **gold_result,
                "processing_time_ms": (gold_end - gold_start).total_seconds() * 1000,
            }

            # Final result
            result["status"] = "completed"
            result["final_decision"] = gold_result["decision"]
            result["risk_level"] = gold_result["risk_level"]
            result["estimated_payout"] = gold_result["estimated_payout"]
            result["completed_at"] = datetime.utcnow().isoformat()
            result["total_processing_time_ms"] = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000

        except Exception as e:
            logger.error(f"Code processing error: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            result["completed_at"] = datetime.utcnow().isoformat()
            result["total_processing_time_ms"] = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000

        return result

    def _process_bronze(self, claim_data: dict[str, Any]) -> dict[str, Any]:
        """
        Bronze Layer: Validation & Quality Assessment

        - Checks required fields
        - Validates data types
        - Calculates quality score
        - Detects basic anomalies
        """
        issues = []
        warnings = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in claim_data or claim_data.get(field) is None:
                issues.append(f"Missing required field: {field}")

        # Validate claim amount
        claim_amount = claim_data.get("claim_amount", 0)
        if not isinstance(claim_amount, (int, float)):
            issues.append("claim_amount must be a number")
        elif claim_amount <= 0:
            issues.append("claim_amount must be positive")
        elif claim_amount > 50000:
            warnings.append("Unusually high claim amount")

        # Validate line items if present
        line_items = claim_data.get("line_items", [])
        if line_items:
            line_total = sum(item.get("amount", 0) for item in line_items)
            if abs(line_total - claim_amount) > 1.0:
                warnings.append(
                    f"Line items total (${line_total:.2f}) doesn't match "
                    f"claim amount (${claim_amount:.2f})"
                )

        # Calculate quality score (deterministic formula)
        base_score = 100.0
        base_score -= len(issues) * 20  # -20 per issue
        base_score -= len(warnings) * 5  # -5 per warning

        # Bonus for complete data
        optional_fields = ["provider_name", "treatment_notes", "line_items"]
        completeness_bonus = sum(
            5 for f in optional_fields if claim_data.get(f)
        )
        quality_score = min(100, max(0, base_score + completeness_bonus))

        # Decision
        if issues:
            decision = "REJECT"
        elif quality_score < 60:
            decision = "QUARANTINE"
        else:
            decision = "ACCEPT"

        return {
            "decision": decision,
            "quality_score": quality_score,
            "validation_issues": issues,
            "warnings": warnings,
            "fields_checked": len(self.REQUIRED_FIELDS),
            "completeness": (
                len([f for f in self.REQUIRED_FIELDS if claim_data.get(f)])
                / len(self.REQUIRED_FIELDS) * 100
            ),
        }

    def _process_silver(
        self,
        claim_data: dict[str, Any],
        bronze_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Silver Layer: Enrichment & Normalization

        - Normalizes diagnosis codes
        - Calculates coverage
        - Applies business rules
        """
        claim_amount = claim_data.get("claim_amount", 0)
        is_in_network = claim_data.get("is_in_network", True)
        is_emergency = claim_data.get("is_emergency", False)

        # Calculate deductible (fixed $250)
        after_deductible = max(0, claim_amount - self.DEDUCTIBLE)

        # Calculate reimbursement
        reimbursement_rate = self.REIMBURSEMENT_RATE
        if not is_in_network:
            reimbursement_rate *= (1 - self.OUT_OF_NETWORK_PENALTY)

        estimated_reimbursement = after_deductible * reimbursement_rate

        # Priority (simple rule)
        if is_emergency:
            priority = "HIGH"
        elif claim_amount > self.HIGH_VALUE_THRESHOLD:
            priority = "MEDIUM"
        else:
            priority = "NORMAL"

        # Normalize claim category
        claim_type = claim_data.get("claim_type", "").lower()
        normalized_category = {
            "accident": "ACCIDENT",
            "illness": "ILLNESS",
            "wellness": "WELLNESS",
            "dental": "DENTAL",
            "emergency": "EMERGENCY",
        }.get(claim_type, "OTHER")

        return {
            "normalized_category": normalized_category,
            "deductible_applied": self.DEDUCTIBLE,
            "after_deductible": after_deductible,
            "reimbursement_rate": reimbursement_rate,
            "estimated_reimbursement": round(estimated_reimbursement, 2),
            "processing_priority": priority,
            "is_in_network": is_in_network,
            "network_adjustment": (
                0 if is_in_network
                else round(after_deductible * self.OUT_OF_NETWORK_PENALTY * self.REIMBURSEMENT_RATE, 2)
            ),
            "enrichment_status": "complete",
        }

    def _process_gold(
        self,
        claim_data: dict[str, Any],
        bronze_result: dict[str, Any],
        silver_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Gold Layer: Risk Assessment & Final Decision

        - Calculates risk score
        - Detects fraud indicators
        - Makes final decision
        """
        claim_amount = claim_data.get("claim_amount", 0)
        is_emergency = claim_data.get("is_emergency", False)
        is_in_network = claim_data.get("is_in_network", True)

        # Risk factors (deterministic scoring)
        risk_score = 0.0
        risk_factors = []

        # High value claims
        if claim_amount > 10000:
            risk_score += 30
            risk_factors.append("high_value_claim")
        elif claim_amount > 5000:
            risk_score += 15
            risk_factors.append("elevated_amount")

        # Out of network
        if not is_in_network:
            risk_score += 20
            risk_factors.append("out_of_network")

        # Round number amounts (potential fraud indicator)
        if claim_amount in self.SUSPICIOUS_AMOUNT_PATTERNS:
            risk_score += 10
            risk_factors.append("round_amount")

        # Emergency claims get slight bump
        if is_emergency:
            risk_score += 5
            risk_factors.append("emergency_claim")

        # Quality score impact
        quality_score = bronze_result.get("quality_score", 100)
        if quality_score < 70:
            risk_score += 15
            risk_factors.append("low_quality_score")

        # Risk level
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Final decision (rule-based)
        if risk_level == "HIGH":
            decision = "MANUAL_REVIEW"
        elif risk_level == "MEDIUM":
            decision = "STANDARD_REVIEW"
        elif claim_amount <= 500 and is_in_network:
            decision = "AUTO_APPROVE"
        else:
            decision = "STANDARD_REVIEW"

        return {
            "decision": decision,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 1),
            "risk_factors": risk_factors,
            "estimated_payout": silver_result.get("estimated_reimbursement", 0),
            "confidence": 1.0,  # Code is always 100% confident (no uncertainty)
            "insights": [],  # No insights - code doesn't generate them
            "alerts": (
                [{"type": "HIGH_RISK", "message": "Claim flagged for manual review"}]
                if risk_level == "HIGH" else []
            ),
        }


# Singleton instance
code_processor = CodeDrivenProcessor()
