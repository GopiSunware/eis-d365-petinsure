#!/usr/bin/env python3
"""
PetInsure360 - GenAI Claims Processing Agent
Multi-agent pipeline for intelligent claims processing

Agents:
1. Document Extractor - Extract data from vet invoices (PDF/images)
2. Claims Validator - Validate claim against policy terms
3. Fraud Detector - Flag suspicious claims patterns
4. Decision Agent - Recommend approve/deny/review with reasoning

Author: Gopinath Varadharajan
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# For Azure OpenAI / Claude integration
# pip install openai anthropic

# =============================================================================
# DATA MODELS
# =============================================================================

class ClaimStatus(Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    PARTIALLY_APPROVED = "Partially Approved"
    DENIED = "Denied"
    FLAGGED_FRAUD = "Flagged for Fraud Review"


@dataclass
class ClaimDocument:
    """Represents a claim document (vet invoice)"""
    document_id: str
    claim_id: str
    document_type: str  # invoice, lab_report, prescription
    file_path: str
    extracted_data: Optional[Dict] = None


@dataclass
class PolicyTerms:
    """Policy coverage terms"""
    policy_id: str
    plan_name: str
    coverage_limit: float
    deductible: float
    reimbursement_pct: float
    covered_categories: List[str]
    excluded_conditions: List[str]
    waiting_period_days: int
    includes_wellness: bool
    includes_dental: bool


@dataclass
class ClaimDecision:
    """Final claim decision"""
    claim_id: str
    status: ClaimStatus
    approved_amount: float
    reasoning: str
    fraud_score: float
    confidence: float
    recommendations: List[str]


# =============================================================================
# AGENT 1: DOCUMENT EXTRACTOR
# =============================================================================

class DocumentExtractorAgent:
    """
    Extracts structured data from vet invoices and medical documents.
    Uses Azure Document Intelligence or Claude Vision for OCR.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")

    def extract_from_invoice(self, document: ClaimDocument) -> Dict[str, Any]:
        """
        Extract key fields from vet invoice.
        In production: Use Azure Document Intelligence or Claude Vision
        """

        # Simulated extraction for demo
        # In production, this would call Azure Doc Intelligence API

        prompt = f"""
        Extract the following information from this veterinary invoice:

        Required fields:
        - provider_name: Name of the veterinary clinic
        - provider_address: Full address
        - service_date: Date of service (YYYY-MM-DD)
        - patient_name: Pet's name
        - patient_species: Dog, Cat, etc.
        - services: List of services with individual costs
        - total_amount: Total invoice amount
        - diagnosis: Primary diagnosis or reason for visit
        - medications: Any prescribed medications
        - follow_up_required: Yes/No

        Return as JSON format.
        """

        # Simulated response for demo
        extracted = {
            "provider_name": "Happy Paws Veterinary Hospital",
            "provider_address": "123 Pet Care Lane, Chicago, IL 60601",
            "service_date": "2024-11-15",
            "patient_name": "Max",
            "patient_species": "Dog",
            "services": [
                {"name": "Office Visit", "cost": 75.00},
                {"name": "X-Ray (2 views)", "cost": 185.00},
                {"name": "Pain Medication", "cost": 45.00},
                {"name": "Bandaging", "cost": 35.00}
            ],
            "total_amount": 340.00,
            "diagnosis": "Sprained left front leg",
            "medications": ["Carprofen 75mg - 14 tablets"],
            "follow_up_required": "Yes",
            "extraction_confidence": 0.95
        }

        document.extracted_data = extracted
        return extracted

    def validate_extraction(self, extracted_data: Dict) -> Dict[str, Any]:
        """Validate extracted data completeness and quality"""
        required_fields = [
            "provider_name", "service_date", "patient_name",
            "services", "total_amount", "diagnosis"
        ]

        missing = [f for f in required_fields if not extracted_data.get(f)]

        return {
            "is_valid": len(missing) == 0,
            "missing_fields": missing,
            "confidence": extracted_data.get("extraction_confidence", 0),
            "needs_manual_review": len(missing) > 0 or extracted_data.get("extraction_confidence", 0) < 0.8
        }


# =============================================================================
# AGENT 2: CLAIMS VALIDATOR
# =============================================================================

class ClaimsValidatorAgent:
    """
    Validates claim against policy terms and coverage rules.
    """

    def __init__(self):
        pass

    def validate_claim(
        self,
        extracted_data: Dict,
        policy: PolicyTerms,
        claim_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate claim against policy terms.
        Returns validation results with detailed reasoning.
        """

        validation_results = {
            "is_valid": True,
            "issues": [],
            "covered_amount": 0,
            "deductible_remaining": policy.deductible,
            "reasoning": []
        }

        total_amount = extracted_data.get("total_amount", 0)

        # Check 1: Coverage limit
        if total_amount > policy.coverage_limit:
            validation_results["issues"].append("Exceeds coverage limit")
            validation_results["reasoning"].append(
                f"Claim amount ${total_amount} exceeds policy limit ${policy.coverage_limit}"
            )

        # Check 2: Service categories
        services = extracted_data.get("services", [])
        for service in services:
            service_name = service.get("name", "").lower()

            # Check dental coverage
            if "dental" in service_name and not policy.includes_dental:
                validation_results["issues"].append("Dental not covered")
                validation_results["reasoning"].append(
                    f"Service '{service['name']}' requires dental coverage (not included in policy)"
                )

            # Check wellness coverage
            if any(w in service_name for w in ["wellness", "routine", "vaccination"]):
                if not policy.includes_wellness:
                    validation_results["issues"].append("Wellness not covered")
                    validation_results["reasoning"].append(
                        f"Service '{service['name']}' requires wellness coverage (not included)"
                    )

        # Check 3: Pre-existing conditions (simplified)
        diagnosis = extracted_data.get("diagnosis", "").lower()
        for excluded in policy.excluded_conditions:
            if excluded.lower() in diagnosis:
                validation_results["issues"].append("Pre-existing condition")
                validation_results["reasoning"].append(
                    f"Diagnosis '{diagnosis}' matches excluded condition: {excluded}"
                )

        # Calculate covered amount
        if len(validation_results["issues"]) == 0:
            # Apply deductible and reimbursement
            after_deductible = max(0, total_amount - policy.deductible)
            covered = after_deductible * (policy.reimbursement_pct / 100)
            validation_results["covered_amount"] = round(min(covered, policy.coverage_limit), 2)
            validation_results["reasoning"].append(
                f"Calculated coverage: (${total_amount} - ${policy.deductible} deductible) "
                f"x {policy.reimbursement_pct}% = ${validation_results['covered_amount']}"
            )
        else:
            validation_results["is_valid"] = False

        return validation_results


# =============================================================================
# AGENT 3: FRAUD DETECTOR
# =============================================================================

class FraudDetectorAgent:
    """
    Analyzes claims for potential fraud patterns.
    Uses rule-based + ML-based detection.
    """

    def __init__(self):
        # Fraud detection thresholds
        self.high_amount_threshold = 5000
        self.frequent_claims_threshold = 5  # claims per month
        self.duplicate_window_days = 7

    def analyze_claim(
        self,
        extracted_data: Dict,
        customer_history: List[Dict] = None,
        provider_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze claim for fraud indicators.
        Returns fraud score (0-100) and detailed flags.
        """

        fraud_flags = []
        fraud_score = 0

        total_amount = extracted_data.get("total_amount", 0)
        service_date = extracted_data.get("service_date", "")

        # Rule 1: Unusually high claim amount
        if total_amount > self.high_amount_threshold:
            fraud_flags.append({
                "type": "HIGH_AMOUNT",
                "severity": "medium",
                "detail": f"Claim amount ${total_amount} exceeds typical threshold"
            })
            fraud_score += 20

        # Rule 2: Duplicate claims (check history)
        if customer_history:
            recent_claims = [
                c for c in customer_history
                if c.get("service_date") == service_date
            ]
            if len(recent_claims) > 0:
                fraud_flags.append({
                    "type": "POTENTIAL_DUPLICATE",
                    "severity": "high",
                    "detail": f"Found {len(recent_claims)} claims on same date"
                })
                fraud_score += 40

        # Rule 3: Frequent claims pattern
        if customer_history:
            # Count claims in last 30 days
            recent_count = len([c for c in customer_history])  # Simplified
            if recent_count > self.frequent_claims_threshold:
                fraud_flags.append({
                    "type": "HIGH_FREQUENCY",
                    "severity": "medium",
                    "detail": f"Customer has {recent_count} recent claims"
                })
                fraud_score += 15

        # Rule 4: Provider red flags
        if provider_history:
            provider_denial_rate = provider_history.get("denial_rate", 0)
            if provider_denial_rate > 30:
                fraud_flags.append({
                    "type": "HIGH_RISK_PROVIDER",
                    "severity": "low",
                    "detail": f"Provider has {provider_denial_rate}% denial rate"
                })
                fraud_score += 10

        # Rule 5: Weekend/holiday claims (for emergency visits)
        # Simplified check

        return {
            "fraud_score": min(fraud_score, 100),
            "risk_level": (
                "HIGH" if fraud_score >= 50 else
                "MEDIUM" if fraud_score >= 25 else
                "LOW"
            ),
            "flags": fraud_flags,
            "requires_manual_review": fraud_score >= 40,
            "analysis_timestamp": datetime.now().isoformat()
        }


# =============================================================================
# AGENT 4: DECISION AGENT
# =============================================================================

class DecisionAgent:
    """
    Makes final claim decision based on all agent inputs.
    Uses LLM for complex reasoning when needed.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")

    def make_decision(
        self,
        claim_id: str,
        extracted_data: Dict,
        validation_result: Dict,
        fraud_analysis: Dict,
        policy: PolicyTerms
    ) -> ClaimDecision:
        """
        Make final claim decision based on all inputs.
        """

        # Decision logic
        if fraud_analysis["risk_level"] == "HIGH":
            return ClaimDecision(
                claim_id=claim_id,
                status=ClaimStatus.FLAGGED_FRAUD,
                approved_amount=0,
                reasoning=f"Claim flagged for fraud review. Fraud score: {fraud_analysis['fraud_score']}. "
                          f"Flags: {[f['type'] for f in fraud_analysis['flags']]}",
                fraud_score=fraud_analysis["fraud_score"],
                confidence=0.85,
                recommendations=["Manual review required", "Contact customer for verification"]
            )

        if not validation_result["is_valid"]:
            return ClaimDecision(
                claim_id=claim_id,
                status=ClaimStatus.DENIED,
                approved_amount=0,
                reasoning=f"Claim denied due to: {', '.join(validation_result['issues'])}. "
                          f"Details: {' '.join(validation_result['reasoning'])}",
                fraud_score=fraud_analysis["fraud_score"],
                confidence=0.9,
                recommendations=["Notify customer of denial reason", "Offer policy upgrade if applicable"]
            )

        # Approved
        approved_amount = validation_result["covered_amount"]

        # Check for partial approval
        total_claimed = extracted_data.get("total_amount", 0)
        if approved_amount < total_claimed * 0.5:
            status = ClaimStatus.PARTIALLY_APPROVED
        else:
            status = ClaimStatus.APPROVED

        return ClaimDecision(
            claim_id=claim_id,
            status=status,
            approved_amount=approved_amount,
            reasoning=f"Claim {status.value.lower()}. " + " ".join(validation_result["reasoning"]),
            fraud_score=fraud_analysis["fraud_score"],
            confidence=0.95 if fraud_analysis["risk_level"] == "LOW" else 0.75,
            recommendations=self._generate_recommendations(extracted_data, policy, validation_result)
        )

    def _generate_recommendations(
        self,
        extracted_data: Dict,
        policy: PolicyTerms,
        validation_result: Dict
    ) -> List[str]:
        """Generate follow-up recommendations"""
        recommendations = []

        # Recommend wellness if not covered
        if not policy.includes_wellness:
            recommendations.append("Customer may benefit from wellness coverage add-on")

        # Follow-up reminder
        if extracted_data.get("follow_up_required") == "Yes":
            recommendations.append("Schedule follow-up claim reminder")

        # High claim amount
        if extracted_data.get("total_amount", 0) > 1000:
            recommendations.append("High-value claim - ensure customer satisfaction follow-up")

        return recommendations


# =============================================================================
# CLAIMS PROCESSING PIPELINE
# =============================================================================

class ClaimsProcessingPipeline:
    """
    Orchestrates the multi-agent claims processing pipeline.
    """

    def __init__(self, api_key: str = None):
        self.extractor = DocumentExtractorAgent(api_key)
        self.validator = ClaimsValidatorAgent()
        self.fraud_detector = FraudDetectorAgent()
        self.decision_maker = DecisionAgent(api_key)

    def process_claim(
        self,
        document: ClaimDocument,
        policy: PolicyTerms,
        customer_history: List[Dict] = None,
        provider_history: Dict = None
    ) -> Dict[str, Any]:
        """
        Process a claim through the full pipeline.
        """
        pipeline_result = {
            "claim_id": document.claim_id,
            "started_at": datetime.now().isoformat(),
            "stages": {}
        }

        # Stage 1: Document Extraction
        print(f"[1/4] Extracting data from document...")
        extracted_data = self.extractor.extract_from_invoice(document)
        extraction_validation = self.extractor.validate_extraction(extracted_data)
        pipeline_result["stages"]["extraction"] = {
            "data": extracted_data,
            "validation": extraction_validation
        }

        if not extraction_validation["is_valid"]:
            pipeline_result["status"] = "EXTRACTION_FAILED"
            pipeline_result["error"] = f"Missing fields: {extraction_validation['missing_fields']}"
            return pipeline_result

        # Stage 2: Policy Validation
        print(f"[2/4] Validating against policy terms...")
        validation_result = self.validator.validate_claim(
            extracted_data, policy, customer_history
        )
        pipeline_result["stages"]["validation"] = validation_result

        # Stage 3: Fraud Detection
        print(f"[3/4] Analyzing for fraud patterns...")
        fraud_analysis = self.fraud_detector.analyze_claim(
            extracted_data, customer_history, provider_history
        )
        pipeline_result["stages"]["fraud_detection"] = fraud_analysis

        # Stage 4: Final Decision
        print(f"[4/4] Making final decision...")
        decision = self.decision_maker.make_decision(
            document.claim_id,
            extracted_data,
            validation_result,
            fraud_analysis,
            policy
        )
        pipeline_result["stages"]["decision"] = {
            "status": decision.status.value,
            "approved_amount": decision.approved_amount,
            "reasoning": decision.reasoning,
            "fraud_score": decision.fraud_score,
            "confidence": decision.confidence,
            "recommendations": decision.recommendations
        }

        pipeline_result["completed_at"] = datetime.now().isoformat()
        pipeline_result["final_status"] = decision.status.value
        pipeline_result["final_amount"] = decision.approved_amount

        return pipeline_result


# =============================================================================
# DEMO / TEST
# =============================================================================

def demo():
    """Run a demo of the claims processing pipeline"""

    print("=" * 70)
    print("PetInsure360 - GenAI Claims Processing Agent Demo")
    print("=" * 70)

    # Create sample claim document
    document = ClaimDocument(
        document_id="DOC-001",
        claim_id="CLM-2024-123456",
        document_type="invoice",
        file_path="/claims/invoices/inv_123456.pdf"
    )

    # Create sample policy
    policy = PolicyTerms(
        policy_id="POL-001",
        plan_name="Premium",
        coverage_limit=30000,
        deductible=100,
        reimbursement_pct=90,
        covered_categories=["Illness", "Accident", "Emergency", "Surgery"],
        excluded_conditions=["Hip Dysplasia", "Cherry Eye"],
        waiting_period_days=14,
        includes_wellness=True,
        includes_dental=True
    )

    # Sample customer history
    customer_history = [
        {"claim_id": "CLM-001", "service_date": "2024-10-15", "amount": 250},
        {"claim_id": "CLM-002", "service_date": "2024-09-20", "amount": 180}
    ]

    # Initialize pipeline
    pipeline = ClaimsProcessingPipeline()

    # Process claim
    print("\nProcessing claim...")
    print("-" * 70)

    result = pipeline.process_claim(
        document=document,
        policy=policy,
        customer_history=customer_history,
        provider_history={"denial_rate": 8}
    )

    # Display results
    print("\n" + "=" * 70)
    print("PROCESSING RESULTS")
    print("=" * 70)

    print(f"\nClaim ID: {result['claim_id']}")
    print(f"Final Status: {result['final_status']}")
    print(f"Approved Amount: ${result['final_amount']:.2f}")

    print("\n--- Extraction ---")
    print(f"Provider: {result['stages']['extraction']['data']['provider_name']}")
    print(f"Service Date: {result['stages']['extraction']['data']['service_date']}")
    print(f"Total Claimed: ${result['stages']['extraction']['data']['total_amount']:.2f}")
    print(f"Diagnosis: {result['stages']['extraction']['data']['diagnosis']}")

    print("\n--- Validation ---")
    print(f"Valid: {result['stages']['validation']['is_valid']}")
    if result['stages']['validation']['reasoning']:
        for r in result['stages']['validation']['reasoning']:
            print(f"  - {r}")

    print("\n--- Fraud Analysis ---")
    print(f"Risk Level: {result['stages']['fraud_detection']['risk_level']}")
    print(f"Fraud Score: {result['stages']['fraud_detection']['fraud_score']}")
    if result['stages']['fraud_detection']['flags']:
        print("Flags:")
        for f in result['stages']['fraud_detection']['flags']:
            print(f"  - [{f['severity'].upper()}] {f['type']}: {f['detail']}")

    print("\n--- Decision ---")
    print(f"Status: {result['stages']['decision']['status']}")
    print(f"Reasoning: {result['stages']['decision']['reasoning']}")
    print(f"Confidence: {result['stages']['decision']['confidence']*100:.0f}%")
    print("\nRecommendations:")
    for rec in result['stages']['decision']['recommendations']:
        print(f"  - {rec}")

    print("\n" + "=" * 70)
    print("Full JSON output saved to: claims_result.json")
    print("=" * 70)

    # Save full result
    with open("claims_result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)


if __name__ == "__main__":
    demo()
