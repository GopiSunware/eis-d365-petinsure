"""Mapper Agent - Map extracted data to claim model fields."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.config import settings
from app.models.document import (
    BillingCalculation,
    ExtractionResult,
    ProcessedBatch,
)

logger = logging.getLogger(__name__)


class MapperAgent:
    """Agent for mapping extracted data to claim model fields."""

    def __init__(self):
        # Billing defaults (should come from policy lookup in production)
        self.default_deductible = Decimal("250.00")
        self.default_reimbursement_pct = 80
        self.default_annual_limit = Decimal("10000.00")
        self.out_of_network_reduction = Decimal("0.30")

    async def map_to_claim(self, batch: ProcessedBatch) -> Dict[str, Any]:
        """Map extracted data from all documents to a unified claim structure."""
        logger.info(f"Mapping batch {batch.batch_id} to claim fields")

        # Aggregate data from all extractions
        aggregated = self._aggregate_extractions(batch)

        # Generate claim number if not provided
        claim_number = batch.claim_number or self._generate_claim_number()

        # Build mapped claim
        mapped_claim = {
            # Core identifiers
            "claim_number": claim_number,
            "policy_id": batch.policy_number or aggregated.get("policy_id"),
            "claim_id": str(uuid4()),

            # Dates
            "date_of_loss": aggregated.get("service_date"),
            "date_reported": datetime.utcnow().isoformat(),
            "submitted_date": datetime.utcnow().date().isoformat(),
            "service_date": aggregated.get("service_date"),

            # Classification
            "claim_type": self._determine_claim_type(aggregated),
            "claim_category": self._determine_category(aggregated),
            "diagnosis_code": aggregated.get("diagnosis_code"),
            "diagnosis_description": aggregated.get("diagnosis"),

            # Pet/Customer (would come from policy lookup)
            "pet_id": aggregated.get("pet_id"),
            "pet_name": aggregated.get("patient_name"),
            "pet_species": aggregated.get("pet_species"),
            "pet_breed": aggregated.get("pet_breed"),
            "customer_id": aggregated.get("customer_id"),
            "customer_name": aggregated.get("owner_name"),

            # Provider
            "provider_id": aggregated.get("provider_id"),
            "provider_name": aggregated.get("provider_name"),
            "provider_address": aggregated.get("provider_address"),
            "provider_phone": aggregated.get("provider_phone"),
            "provider_license": aggregated.get("provider_license"),
            "is_in_network": aggregated.get("is_in_network", True),

            # Treatment
            "treatment_notes": aggregated.get("treatment_notes"),
            "loss_description": self._generate_loss_description(aggregated),

            # Line items
            "line_items": self._map_line_items(aggregated.get("line_items", [])),

            # Financials (raw from documents)
            "claim_amount": float(aggregated.get("total_amount", 0)),
            "subtotal": float(aggregated.get("subtotal", 0)),
            "tax_amount": float(aggregated.get("tax", 0)),

            # Flags
            "is_emergency": aggregated.get("is_emergency", False),
            "is_recurring": False,  # Would check history
            "severity": self._determine_severity(aggregated),

            # Documents
            "documents": self._map_documents(batch),

            # Status
            "status": "fnol_received",

            # Metadata
            "extraction_confidence": aggregated.get("confidence_score", 0.0),
            "source": "docgen",
        }

        # Calculate billing
        billing = self._calculate_billing(
            claim_amount=Decimal(str(aggregated.get("total_amount", 0))),
            is_in_network=aggregated.get("is_in_network", True),
        )

        # Add billing fields
        mapped_claim.update({
            "deductible_applied": float(billing.deductible_applied),
            "covered_amount": float(billing.covered_amount),
            "estimated_payout": float(billing.final_payout),
            "customer_responsibility": float(billing.customer_responsibility),
        })

        # Store billing in batch
        batch.billing = billing
        batch.total_claim_amount = Decimal(str(aggregated.get("total_amount", 0)))
        batch.estimated_payout = billing.final_payout

        logger.info(
            f"Mapped claim {claim_number}: "
            f"amount=${mapped_claim['claim_amount']:.2f}, "
            f"payout=${mapped_claim['estimated_payout']:.2f}"
        )

        return mapped_claim

    def _aggregate_extractions(self, batch: ProcessedBatch) -> Dict[str, Any]:
        """Aggregate data from multiple document extractions."""
        if not batch.extractions:
            return {}

        # Start with empty aggregation
        aggregated = {
            "line_items": [],
            "total_amount": Decimal("0"),
            "subtotal": Decimal("0"),
            "tax": Decimal("0"),
            "confidence_score": 0.0,
        }

        confidence_scores = []

        for doc_id, extraction in batch.extractions.items():
            # Take first non-null values for single-value fields
            for field in [
                "provider_name", "provider_address", "provider_phone",
                "provider_license", "provider_id", "is_in_network",
                "patient_name", "pet_species", "pet_breed", "owner_name",
                "service_date", "diagnosis", "diagnosis_code", "treatment_notes",
                "is_emergency",
            ]:
                value = getattr(extraction, field, None)
                if value and not aggregated.get(field):
                    if field == "service_date" and value:
                        aggregated[field] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                    else:
                        aggregated[field] = value

            # Aggregate line items
            for item in extraction.line_items:
                aggregated["line_items"].append({
                    "description": item.description,
                    "diagnosis_code": item.diagnosis_code,
                    "procedure_code": item.procedure_code,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_amount": item.total_amount,
                    "service_date": item.service_date.isoformat() if item.service_date else None,
                })

            # Sum financials
            if extraction.total_amount:
                aggregated["total_amount"] += extraction.total_amount
            if extraction.subtotal:
                aggregated["subtotal"] += extraction.subtotal
            if extraction.tax:
                aggregated["tax"] += extraction.tax

            confidence_scores.append(extraction.confidence_score)

        # Average confidence
        if confidence_scores:
            aggregated["confidence_score"] = sum(confidence_scores) / len(confidence_scores)

        return aggregated

    def _generate_claim_number(self) -> str:
        """Generate a unique claim number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid4())[:6].upper()
        return f"CLM-{timestamp}-{unique_id}"

    def _determine_claim_type(self, data: Dict[str, Any]) -> str:
        """Determine claim type from extracted data."""
        diagnosis = (data.get("diagnosis") or "").lower()
        is_emergency = data.get("is_emergency", False)

        # Check for accident indicators
        accident_keywords = [
            "injury", "fracture", "broken", "trauma", "accident",
            "hit by car", "fall", "bite", "laceration", "wound",
            "toxicity", "poisoning", "foreign body", "ingestion"
        ]
        if any(kw in diagnosis for kw in accident_keywords):
            return "accident"

        # Check for illness indicators
        illness_keywords = [
            "disease", "infection", "cancer", "tumor", "diabetes",
            "kidney", "liver", "heart", "chronic", "allergy",
            "gastritis", "pancreatitis", "arthritis"
        ]
        if any(kw in diagnosis for kw in illness_keywords):
            return "illness"

        # Check for wellness
        wellness_keywords = ["wellness", "vaccine", "checkup", "annual", "preventive"]
        if any(kw in diagnosis for kw in wellness_keywords):
            return "wellness"

        # Emergency flag
        if is_emergency:
            return "emergency"

        return "illness"  # Default

    def _determine_category(self, data: Dict[str, Any]) -> str:
        """Determine claim category from diagnosis."""
        diagnosis = (data.get("diagnosis") or "").lower()

        categories = {
            "orthopedic": ["fracture", "acl", "ccl", "hip", "joint", "bone", "tplo"],
            "gastrointestinal": ["gastritis", "pancreatitis", "vomiting", "diarrhea", "foreign body"],
            "dermatology": ["skin", "allergy", "rash", "itch", "dermatitis"],
            "oncology": ["cancer", "tumor", "lymphoma", "mass"],
            "dental": ["tooth", "dental", "extraction", "periodontal"],
            "neurology": ["seizure", "neurological", "paralysis", "ivdd"],
            "cardiology": ["heart", "cardiac", "murmur"],
            "ophthalmology": ["eye", "corneal", "cataract", "glaucoma"],
            "emergency": ["emergency", "critical", "trauma", "toxicity"],
            "preventive": ["wellness", "vaccine", "checkup"],
        }

        for category, keywords in categories.items():
            if any(kw in diagnosis for kw in keywords):
                return category

        return "general"

    def _determine_severity(self, data: Dict[str, Any]) -> str:
        """Determine claim severity based on amount and type."""
        amount = float(data.get("total_amount", 0))
        is_emergency = data.get("is_emergency", False)

        if amount > 5000 or is_emergency:
            return "severe"
        elif amount > 1500:
            return "moderate"
        else:
            return "minor"

    def _map_line_items(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """Map line items to claim format."""
        mapped = []
        for i, item in enumerate(items):
            mapped.append({
                "line_id": f"LI-{i+1:03d}",
                "description": item.get("description", ""),
                "diagnosis_code": item.get("diagnosis_code"),
                "procedure_code": item.get("procedure_code"),
                "quantity": item.get("quantity", 1),
                "unit_price": float(item.get("unit_price", 0)),
                "total_amount": float(item.get("total_amount", 0)),
                "service_date": item.get("service_date"),
                "is_covered": True,  # Will be validated
                "denial_reason": None,
            })
        return mapped

    def _map_documents(self, batch: ProcessedBatch) -> List[Dict[str, Any]]:
        """Map uploaded documents to claim format."""
        return [
            {
                "document_id": str(doc.id),
                "document_type": doc.document_type.value if doc.document_type else "other",
                "filename": doc.original_filename,
                "upload_date": doc.uploaded_at.isoformat(),
                "blob_url": doc.blob_url or doc.local_path,
                "verified": True,
            }
            for doc in batch.documents
        ]

    def _generate_loss_description(self, data: Dict[str, Any]) -> str:
        """Generate a loss description from extracted data."""
        parts = []

        if data.get("diagnosis"):
            parts.append(f"Diagnosis: {data['diagnosis']}")

        if data.get("treatment_notes"):
            parts.append(f"Treatment: {data['treatment_notes']}")

        if data.get("is_emergency"):
            parts.append("Emergency visit")

        if data.get("service_date"):
            parts.append(f"Service date: {data['service_date']}")

        return ". ".join(parts) if parts else "Claim submitted via document upload"

    def _calculate_billing(
        self,
        claim_amount: Decimal,
        is_in_network: bool = True,
        deductible_remaining: Optional[Decimal] = None,
        annual_limit_remaining: Optional[Decimal] = None,
    ) -> BillingCalculation:
        """Calculate billing/reimbursement."""
        # Use defaults if not provided
        deductible_remaining = deductible_remaining or self.default_deductible
        annual_limit_remaining = annual_limit_remaining or self.default_annual_limit
        reimbursement_pct = self.default_reimbursement_pct

        # Apply out-of-network reduction
        out_of_network_reduction = Decimal("0")
        if not is_in_network:
            out_of_network_reduction = claim_amount * self.out_of_network_reduction
            claim_amount = claim_amount - out_of_network_reduction

        # Apply deductible
        deductible_applied = min(deductible_remaining, claim_amount)
        amount_after_deductible = claim_amount - deductible_applied

        # Apply reimbursement percentage
        covered_amount = amount_after_deductible * Decimal(str(reimbursement_pct / 100))

        # Apply annual limit
        final_payout = min(covered_amount, annual_limit_remaining)

        # Calculate customer responsibility
        customer_responsibility = claim_amount - final_payout + out_of_network_reduction

        # Generate explanation
        explanation_parts = [
            f"Claim amount: ${claim_amount:.2f}",
        ]
        if out_of_network_reduction > 0:
            explanation_parts.append(
                f"Out-of-network reduction (30%): -${out_of_network_reduction:.2f}"
            )
        explanation_parts.extend([
            f"Deductible applied: -${deductible_applied:.2f}",
            f"Amount after deductible: ${amount_after_deductible:.2f}",
            f"Reimbursement ({reimbursement_pct}%): ${covered_amount:.2f}",
            f"Final payout: ${final_payout:.2f}",
        ])

        return BillingCalculation(
            claim_amount=claim_amount + out_of_network_reduction,
            deductible_remaining=deductible_remaining,
            deductible_applied=deductible_applied,
            amount_after_deductible=amount_after_deductible,
            reimbursement_percentage=reimbursement_pct,
            covered_amount=covered_amount,
            annual_limit_remaining=annual_limit_remaining,
            final_payout=final_payout,
            out_of_network_reduction=out_of_network_reduction,
            customer_responsibility=customer_responsibility,
            explanation="\n".join(explanation_parts),
        )
