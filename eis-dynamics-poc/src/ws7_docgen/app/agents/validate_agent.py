"""Validation Agent - Validate claims and detect fraud."""

import hashlib
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings
from app.models.document import (
    BillingCalculation,
    FraudIndicator,
    ProcessedBatch,
    ValidationIssue,
)

logger = logging.getLogger(__name__)

# In-memory store for duplicate detection (would be database in production)
_document_fingerprints: Dict[str, Dict[str, Any]] = {}  # hash -> {batch_id, filename, extracted_data}


class ValidateAgent:
    """Agent for validating claims and detecting fraud."""

    def __init__(self):
        # Fraud detection thresholds
        self.fraud_thresholds = {
            "low": (0, 15),
            "medium": (15, 30),
            "high": (30, 50),
            "critical": (50, 100),
        }

        # AI provider for semantic duplicate detection
        self.ai_provider = settings.AI_PROVIDER
        if self.ai_provider == "claude" and settings.ANTHROPIC_API_KEY:
            from anthropic import Anthropic
            self.ai_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.CLAUDE_MODEL
        elif settings.OPENAI_API_KEY:
            from openai import OpenAI
            self.ai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        else:
            self.ai_client = None
            self.model = None

    async def validate(self, batch: ProcessedBatch) -> Dict[str, Any]:
        """Validate a processed batch and detect fraud indicators."""
        logger.info(f"Validating batch {batch.batch_id}")

        issues: List[ValidationIssue] = []
        fraud_indicators: List[FraudIndicator] = []
        fraud_score = 0.0

        # Get mapped claim data
        claim = batch.mapped_claim or {}

        # 1. Document validation
        doc_issues = self._validate_documents(batch)
        issues.extend(doc_issues)

        # 2. DUPLICATE DETECTION (AI-powered)
        duplicate_result = await self._detect_duplicates(batch)
        issues.extend(duplicate_result["issues"])
        fraud_indicators.extend(duplicate_result["fraud_indicators"])
        fraud_score += duplicate_result["fraud_score_addition"]

        # 3. Claim data validation
        data_issues = self._validate_claim_data(claim)
        issues.extend(data_issues)

        # 4. Fraud detection
        fraud_result = self._detect_fraud(batch, claim)
        fraud_indicators.extend(fraud_result["indicators"])
        fraud_score += fraud_result["score"]

        # 5. Billing validation
        billing_issues = self._validate_billing(batch, claim)
        issues.extend(billing_issues)

        # 6. Diagnosis-treatment validation
        dt_issues = self._validate_diagnosis_treatment(claim)
        issues.extend(dt_issues)

        # Determine risk level
        risk_level = self._calculate_risk_level(fraud_score)

        # Determine AI decision
        ai_decision, ai_reasoning = self._determine_decision(
            issues, fraud_score, risk_level, claim
        )

        # Calculate confidence
        ai_confidence = self._calculate_confidence(batch, issues)

        result = {
            "issues": issues,
            "is_valid": not any(i.severity == "critical" for i in issues),
            "fraud_score": fraud_score,
            "fraud_indicators": fraud_indicators,
            "risk_level": risk_level,
            "ai_decision": ai_decision,
            "ai_reasoning": ai_reasoning,
            "ai_confidence": ai_confidence,
            "billing": batch.billing,
        }

        logger.info(
            f"Validation complete for batch {batch.batch_id}: "
            f"issues={len(issues)}, fraud_score={fraud_score:.2f}, "
            f"decision={ai_decision}"
        )

        return result

    def _validate_documents(self, batch: ProcessedBatch) -> List[ValidationIssue]:
        """Validate uploaded documents."""
        issues = []

        if not batch.documents:
            issues.append(ValidationIssue(
                severity="critical",
                code="NO_DOCUMENTS",
                message="No documents uploaded for claim",
                suggestion="Upload at least one supporting document",
            ))
            return issues

        # Check for invoice/receipt
        has_financial_doc = any(
            d.document_type and d.document_type.value in ["vet_invoice", "medical_receipt"]
            for d in batch.documents
        )
        if not has_financial_doc:
            issues.append(ValidationIssue(
                severity="warning",
                code="NO_INVOICE",
                message="No invoice or receipt document found",
                suggestion="Upload an itemized invoice or receipt for faster processing",
            ))

        # Check extraction quality
        for doc_id, extraction in batch.extractions.items():
            if extraction.confidence_score < 0.5:
                issues.append(ValidationIssue(
                    severity="warning",
                    code="LOW_EXTRACTION_CONFIDENCE",
                    message=f"Low extraction confidence for document",
                    field=str(extraction.document_id),
                    suggestion="Document may require manual review",
                ))

        return issues

    async def _detect_duplicates(self, batch: ProcessedBatch) -> Dict[str, Any]:
        """
        AI-powered duplicate document detection.

        Detects duplicates through multiple strategies:
        1. EXACT MATCH: Content hash comparison (same bytes = definite duplicate)
        2. SEMANTIC MATCH: AI analyzes if documents contain same core information
           - Same invoice number, same amounts, same dates = duplicate even with different formatting
        3. CROSS-BATCH: Checks if document was previously submitted in another claim

        What constitutes a CLEAR DUPLICATE (AI reasoning):
        - Same invoice/receipt number (strongest signal)
        - Same provider + same date + same total amount
        - Same line items with same prices (order doesn't matter)
        - Same patient/pet with same treatment on same date
        - Documents that are reformatted/rescanned versions of same source

        What is NOT a duplicate:
        - Different invoices from same provider on different dates
        - Follow-up visits (different dates, potentially similar treatments)
        - Related documents (e.g., prescription for medication on invoice)
        - Lab results supporting an invoice (complementary, not duplicate)
        """
        issues: List[ValidationIssue] = []
        fraud_indicators: List[FraudIndicator] = []
        fraud_score_addition = 0.0

        if not batch.extractions:
            return {"issues": issues, "fraud_indicators": fraud_indicators, "fraud_score_addition": 0}

        # Step 1: Compute fingerprints for each document in this batch
        batch_fingerprints: List[Dict[str, Any]] = []

        for doc_id, extraction in batch.extractions.items():
            fingerprint = self._compute_document_fingerprint(extraction)
            batch_fingerprints.append({
                "doc_id": doc_id,
                "extraction": extraction,
                "fingerprint": fingerprint,
            })

        # Step 2: Check for duplicates WITHIN this batch
        within_batch_duplicates = self._find_within_batch_duplicates(batch_fingerprints)

        for dup in within_batch_duplicates:
            if dup["match_type"] == "exact":
                # Exact content match - definite duplicate
                fraud_score_addition += 25
                issues.append(ValidationIssue(
                    severity="critical",
                    code="DUPLICATE_DOCUMENT_EXACT",
                    message=f"Exact duplicate detected: '{dup['doc1_name']}' and '{dup['doc2_name']}' are identical",
                    suggestion="Remove the duplicate document before resubmitting",
                ))
                fraud_indicators.append(FraudIndicator(
                    indicator="Exact duplicate document in batch",
                    score_impact=25.0,
                    confidence=1.0,
                    description=f"Documents have identical content despite different filenames",
                    pattern_type="duplicate_submission",
                ))
            elif dup["match_type"] == "semantic":
                # AI detected semantic duplicate
                fraud_score_addition += 20
                issues.append(ValidationIssue(
                    severity="error",
                    code="DUPLICATE_DOCUMENT_SEMANTIC",
                    message=f"Potential duplicate: '{dup['doc1_name']}' and '{dup['doc2_name']}' contain same claim data",
                    field=dup.get("matching_fields", ""),
                    suggestion=f"AI detected same invoice/receipt submitted twice. {dup.get('reason', '')}",
                ))
                fraud_indicators.append(FraudIndicator(
                    indicator="Semantic duplicate document detected",
                    score_impact=20.0,
                    confidence=dup.get("confidence", 0.85),
                    description=dup.get("reason", "Same core claim data with different formatting"),
                    pattern_type="duplicate_submission",
                ))

        # Step 3: Check against previously submitted documents (cross-batch)
        cross_batch_duplicates = await self._find_cross_batch_duplicates(batch, batch_fingerprints)

        for dup in cross_batch_duplicates:
            confidence = dup.get("confidence", 0.95)
            match_type = dup.get("match_type", "exact")

            # Build detailed match explanation
            if match_type == "exact":
                match_reason = "Identical document content (byte-for-byte match)"
                confidence = 1.0
            else:
                match_reason = self._build_semantic_match_reason(dup)

            fraud_score_addition += 30
            issues.append(ValidationIssue(
                severity="critical",
                code="DUPLICATE_PREVIOUSLY_SUBMITTED",
                message=f"🚨 DUPLICATE DETECTED ({confidence*100:.0f}% confidence)",
                field=f"Match type: {match_type.upper()}",
                suggestion=f"{match_reason}. Original submission: Batch {dup['previous_batch'][:8]}... on file '{dup['previous_doc']}'",
                source="duplicate_detection",
            ))
            fraud_indicators.append(FraudIndicator(
                indicator=f"Document resubmission ({match_type})",
                score_impact=30.0,
                confidence=confidence,
                description=f"This document was previously submitted. {match_reason}",
                pattern_type="duplicate_submission",
            ))

        # Step 4: Store fingerprints for future cross-batch detection
        self._store_fingerprints(batch.batch_id, batch_fingerprints)

        logger.info(
            f"Duplicate detection complete: {len(within_batch_duplicates)} within-batch, "
            f"{len(cross_batch_duplicates)} cross-batch duplicates found"
        )

        return {
            "issues": issues,
            "fraud_indicators": fraud_indicators,
            "fraud_score_addition": min(fraud_score_addition, 50),  # Cap contribution
        }

    def _compute_document_fingerprint(self, extraction) -> Dict[str, Any]:
        """
        Compute multiple fingerprints for a document extraction.

        Returns multiple fingerprint types for different matching strategies.
        """
        # Raw text hash (for exact content matching)
        raw_text = extraction.raw_text or ""
        content_hash = hashlib.sha256(raw_text.encode()).hexdigest()

        # Normalized content hash (ignoring whitespace differences)
        normalized_text = " ".join(raw_text.lower().split())
        normalized_hash = hashlib.sha256(normalized_text.encode()).hexdigest()

        # Semantic fingerprint (key extracted data points)
        semantic_key_parts = []

        if extraction.invoice_number:
            semantic_key_parts.append(f"inv:{extraction.invoice_number.lower().strip()}")

        if extraction.provider_name:
            semantic_key_parts.append(f"prov:{extraction.provider_name.lower().strip()}")

        if extraction.service_date:
            semantic_key_parts.append(f"date:{extraction.service_date.strftime('%Y-%m-%d')}")

        if extraction.total_amount:
            semantic_key_parts.append(f"amt:{float(extraction.total_amount):.2f}")

        if extraction.patient_name:
            semantic_key_parts.append(f"pet:{extraction.patient_name.lower().strip()}")

        semantic_fingerprint = "|".join(sorted(semantic_key_parts))
        semantic_hash = hashlib.sha256(semantic_fingerprint.encode()).hexdigest() if semantic_key_parts else None

        return {
            "content_hash": content_hash,
            "normalized_hash": normalized_hash,
            "semantic_hash": semantic_hash,
            "semantic_key": semantic_fingerprint,
            "invoice_number": extraction.invoice_number,
            "provider": extraction.provider_name,
            "date": extraction.service_date,
            "amount": float(extraction.total_amount) if extraction.total_amount else None,
            "patient": extraction.patient_name,
        }

    def _find_within_batch_duplicates(
        self,
        batch_fingerprints: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find duplicate documents within the same batch."""
        duplicates = []
        seen_content_hashes: Dict[str, str] = {}  # hash -> doc_id
        seen_semantic_hashes: Dict[str, str] = {}  # hash -> doc_id

        for fp in batch_fingerprints:
            doc_id = fp["doc_id"]
            fingerprint = fp["fingerprint"]
            extraction = fp["extraction"]

            # Check exact content match
            if fingerprint["content_hash"] in seen_content_hashes:
                other_doc_id = seen_content_hashes[fingerprint["content_hash"]]
                duplicates.append({
                    "match_type": "exact",
                    "doc1_id": other_doc_id,
                    "doc2_id": doc_id,
                    "doc1_name": self._get_doc_filename(batch_fingerprints, other_doc_id),
                    "doc2_name": extraction.document_id,
                    "confidence": 1.0,
                })
            else:
                seen_content_hashes[fingerprint["content_hash"]] = doc_id

            # Check semantic match (same key data points)
            if fingerprint["semantic_hash"] and fingerprint["semantic_hash"] in seen_semantic_hashes:
                other_doc_id = seen_semantic_hashes[fingerprint["semantic_hash"]]
                # Don't double-report if already caught as exact match
                if not any(d["doc2_id"] == doc_id and d["match_type"] == "exact" for d in duplicates):
                    other_fp = next((f for f in batch_fingerprints if f["doc_id"] == other_doc_id), None)
                    duplicates.append({
                        "match_type": "semantic",
                        "doc1_id": other_doc_id,
                        "doc2_id": doc_id,
                        "doc1_name": self._get_doc_filename(batch_fingerprints, other_doc_id),
                        "doc2_name": extraction.document_id,
                        "matching_fields": fingerprint["semantic_key"],
                        "reason": self._explain_semantic_match(fingerprint, other_fp["fingerprint"] if other_fp else None),
                        "confidence": 0.9,
                    })
            elif fingerprint["semantic_hash"]:
                seen_semantic_hashes[fingerprint["semantic_hash"]] = doc_id

        return duplicates

    def _get_doc_filename(self, batch_fingerprints: List[Dict], doc_id: str) -> str:
        """Get filename for a document ID."""
        for fp in batch_fingerprints:
            if fp["doc_id"] == doc_id:
                return fp["extraction"].document_id
        return doc_id

    def _explain_semantic_match(self, fp1: Dict, fp2: Optional[Dict]) -> str:
        """Generate human-readable explanation of why documents match semantically."""
        reasons = []

        if fp1.get("invoice_number"):
            reasons.append(f"Same invoice #{fp1['invoice_number']}")

        if fp1.get("provider") and fp1.get("date") and fp1.get("amount"):
            reasons.append(f"Same provider, date, and amount")
        elif fp1.get("provider") and fp1.get("amount"):
            reasons.append(f"Same provider and total amount")

        if fp1.get("patient") and fp1.get("date"):
            reasons.append(f"Same pet on same date")

        return "; ".join(reasons) if reasons else "Same core claim data detected"

    def _build_semantic_match_reason(self, dup: Dict[str, Any]) -> str:
        """Build detailed explanation for semantic duplicate match."""
        matching_fields = dup.get("matching_fields", "")
        reasons = []

        if "inv:" in matching_fields:
            # Extract invoice number
            inv_match = [p for p in matching_fields.split("|") if p.startswith("inv:")]
            if inv_match:
                inv_num = inv_match[0].replace("inv:", "")
                reasons.append(f"Invoice #{inv_num}")

        if "prov:" in matching_fields:
            prov_match = [p for p in matching_fields.split("|") if p.startswith("prov:")]
            if prov_match:
                prov = prov_match[0].replace("prov:", "")
                reasons.append(f"Provider: {prov}")

        if "date:" in matching_fields:
            date_match = [p for p in matching_fields.split("|") if p.startswith("date:")]
            if date_match:
                date = date_match[0].replace("date:", "")
                reasons.append(f"Service Date: {date}")

        if "amt:" in matching_fields:
            amt_match = [p for p in matching_fields.split("|") if p.startswith("amt:")]
            if amt_match:
                amt = amt_match[0].replace("amt:", "")
                reasons.append(f"Amount: ${amt}")

        if "pet:" in matching_fields:
            pet_match = [p for p in matching_fields.split("|") if p.startswith("pet:")]
            if pet_match:
                pet = pet_match[0].replace("pet:", "")
                reasons.append(f"Pet: {pet}")

        if reasons:
            return "Matching fields: " + ", ".join(reasons)
        return "Same core claim data detected across documents"

    async def _find_cross_batch_duplicates(
        self,
        batch: ProcessedBatch,
        batch_fingerprints: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find documents that were previously submitted in other batches."""
        duplicates = []

        for fp in batch_fingerprints:
            fingerprint = fp["fingerprint"]

            # Check content hash against stored fingerprints
            for stored_hash, stored_data in _document_fingerprints.items():
                if stored_data["batch_id"] == str(batch.batch_id):
                    continue  # Skip same batch

                # Exact match
                if fingerprint["content_hash"] == stored_data.get("content_hash"):
                    duplicates.append({
                        "current_doc": str(fp["extraction"].document_id),
                        "previous_doc": stored_data["filename"],
                        "previous_batch": stored_data["batch_id"],
                        "match_type": "exact",
                        "confidence": 1.0,
                        "matching_fields": fingerprint.get("semantic_key", ""),
                    })
                # Semantic match
                elif (fingerprint["semantic_hash"] and
                      fingerprint["semantic_hash"] == stored_data.get("semantic_hash")):
                    duplicates.append({
                        "current_doc": str(fp["extraction"].document_id),
                        "previous_doc": stored_data["filename"],
                        "previous_batch": stored_data["batch_id"],
                        "match_type": "semantic",
                        "confidence": 0.9,
                        "matching_fields": fingerprint.get("semantic_key", ""),
                    })

        return duplicates

    def _store_fingerprints(
        self,
        batch_id: str,
        batch_fingerprints: List[Dict[str, Any]],
    ) -> None:
        """Store document fingerprints for future cross-batch detection."""
        for fp in batch_fingerprints:
            key = f"{batch_id}:{fp['doc_id']}"
            _document_fingerprints[key] = {
                "batch_id": str(batch_id),
                "filename": str(fp["extraction"].document_id),
                "content_hash": fp["fingerprint"]["content_hash"],
                "normalized_hash": fp["fingerprint"]["normalized_hash"],
                "semantic_hash": fp["fingerprint"]["semantic_hash"],
                "timestamp": datetime.utcnow().isoformat(),
            }

        logger.debug(f"Stored {len(batch_fingerprints)} fingerprints for batch {batch_id}")

        # Persist to disk for cross-batch detection across restarts
        try:
            _save_fingerprints()
        except Exception as e:
            logger.error(f"Failed to save fingerprints: {e}")

    def _validate_claim_data(self, claim: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate claim data completeness and consistency."""
        issues = []

        # Required fields
        required_fields = [
            ("service_date", "Service date"),
            ("diagnosis_description", "Diagnosis"),
            ("claim_amount", "Claim amount"),
        ]

        for field, label in required_fields:
            if not claim.get(field):
                issues.append(ValidationIssue(
                    severity="error",
                    code="MISSING_REQUIRED_FIELD",
                    message=f"Missing required field: {label}",
                    field=field,
                    suggestion=f"Please provide {label.lower()}",
                ))

        # Validate claim amount
        claim_amount = claim.get("claim_amount", 0)
        if claim_amount <= 0:
            issues.append(ValidationIssue(
                severity="error",
                code="INVALID_CLAIM_AMOUNT",
                message="Claim amount must be greater than zero",
                field="claim_amount",
            ))
        elif claim_amount > 50000:
            issues.append(ValidationIssue(
                severity="warning",
                code="HIGH_CLAIM_AMOUNT",
                message=f"Unusually high claim amount: ${claim_amount:,.2f}",
                field="claim_amount",
                suggestion="High-value claims require additional review",
            ))

        # Validate service date
        if claim.get("service_date"):
            try:
                service_date = datetime.fromisoformat(claim["service_date"].replace("Z", "+00:00"))
                if service_date.date() > datetime.utcnow().date():
                    issues.append(ValidationIssue(
                        severity="error",
                        code="FUTURE_SERVICE_DATE",
                        message="Service date cannot be in the future",
                        field="service_date",
                    ))
                elif service_date.date() < (datetime.utcnow() - timedelta(days=365)).date():
                    issues.append(ValidationIssue(
                        severity="warning",
                        code="OLD_SERVICE_DATE",
                        message="Service date is more than 1 year ago",
                        field="service_date",
                        suggestion="Claims should be submitted within policy timeframe",
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_SERVICE_DATE",
                    message="Invalid service date format",
                    field="service_date",
                ))

        # Validate provider
        if not claim.get("provider_name"):
            issues.append(ValidationIssue(
                severity="warning",
                code="MISSING_PROVIDER",
                message="Provider name not found in documents",
                field="provider_name",
            ))

        return issues

    def _detect_fraud(
        self,
        batch: ProcessedBatch,
        claim: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect fraud indicators in the claim."""
        indicators = []
        score = 0.0

        claim_amount = claim.get("claim_amount", 0)

        # Pattern 1: Round amounts (suspicious)
        if claim_amount > 0:
            if claim_amount % 500 == 0:
                score += 5
                indicators.append(FraudIndicator(
                    indicator="Round claim amount",
                    score_impact=5.0,
                    confidence=0.6,
                    description=f"Claim amount ${claim_amount:,.2f} is suspiciously round",
                    pattern_type="claim_characteristics",
                ))
            elif claim_amount % 100 == 0:
                score += 3
                indicators.append(FraudIndicator(
                    indicator="Round claim amount (hundreds)",
                    score_impact=3.0,
                    confidence=0.4,
                    description=f"Claim amount ${claim_amount:,.2f} ends in round hundreds",
                    pattern_type="claim_characteristics",
                ))

        # Pattern 2: Missing line items detail
        line_items = claim.get("line_items", [])
        if claim_amount > 1000 and len(line_items) < 2:
            score += 10
            indicators.append(FraudIndicator(
                indicator="Insufficient line item detail",
                score_impact=10.0,
                confidence=0.7,
                description="High claim amount with few line items may indicate bundling",
                pattern_type="claim_characteristics",
            ))

        # Pattern 3: Emergency without supporting evidence
        if claim.get("is_emergency") and not any(
            "emergency" in (li.get("description", "").lower())
            for li in line_items
        ):
            score += 8
            indicators.append(FraudIndicator(
                indicator="Emergency flag without emergency charges",
                score_impact=8.0,
                confidence=0.6,
                description="Claim marked as emergency but no emergency service charges found",
                pattern_type="staged_timing",
            ))

        # Pattern 4: Out-of-network with high amount
        if not claim.get("is_in_network", True) and claim_amount > 3000:
            score += 10
            indicators.append(FraudIndicator(
                indicator="High out-of-network claim",
                score_impact=10.0,
                confidence=0.5,
                description="Out-of-network claim with amount over $3,000",
                pattern_type="provider_collusion",
            ))

        # Pattern 5: Multiple documents with inconsistent data
        extractions = list(batch.extractions.values())
        if len(extractions) > 1:
            # Check for provider mismatch
            providers = set(e.provider_name for e in extractions if e.provider_name)
            if len(providers) > 1:
                score += 15
                indicators.append(FraudIndicator(
                    indicator="Multiple providers in single claim",
                    score_impact=15.0,
                    confidence=0.8,
                    description=f"Documents show different providers: {', '.join(providers)}",
                    pattern_type="document_consistency",
                ))

            # Check for date mismatch
            dates = set(
                e.service_date.date() if e.service_date else None
                for e in extractions
            )
            dates.discard(None)
            if len(dates) > 1:
                score += 10
                indicators.append(FraudIndicator(
                    indicator="Multiple service dates",
                    score_impact=10.0,
                    confidence=0.7,
                    description="Documents show different service dates",
                    pattern_type="document_consistency",
                ))

        # Pattern 6: Low extraction confidence (potential document manipulation)
        avg_confidence = sum(e.confidence_score for e in extractions) / len(extractions) if extractions else 0
        if avg_confidence < 0.5 and claim_amount > 2000:
            score += 12
            indicators.append(FraudIndicator(
                indicator="Low document quality with high claim",
                score_impact=12.0,
                confidence=0.6,
                description="Poor document quality may indicate altered documents",
                pattern_type="document_authenticity",
            ))

        return {
            "indicators": indicators,
            "score": min(score, 100),  # Cap at 100
        }

    def _validate_billing(
        self,
        batch: ProcessedBatch,
        claim: Dict[str, Any],
    ) -> List[ValidationIssue]:
        """Validate billing calculations."""
        issues = []

        billing = batch.billing
        if not billing:
            return issues

        # Check if claim exceeds annual limit
        if billing.final_payout < billing.covered_amount:
            issues.append(ValidationIssue(
                severity="info",
                code="ANNUAL_LIMIT_APPLIED",
                message="Annual limit cap applied to claim",
                field="annual_limit",
                source="billing",
            ))

        # Check deductible status
        if billing.deductible_applied > 0:
            issues.append(ValidationIssue(
                severity="info",
                code="DEDUCTIBLE_APPLIED",
                message=f"Deductible of ${billing.deductible_applied:.2f} applied",
                field="deductible",
                source="billing",
            ))

        # Check out-of-network reduction
        if billing.out_of_network_reduction > 0:
            issues.append(ValidationIssue(
                severity="warning",
                code="OUT_OF_NETWORK_REDUCTION",
                message=f"Out-of-network reduction of ${billing.out_of_network_reduction:.2f} applied",
                field="network_status",
                source="billing",
                suggestion="Using in-network providers results in higher reimbursement",
            ))

        return issues

    def _validate_diagnosis_treatment(self, claim: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate diagnosis-treatment consistency."""
        issues = []

        diagnosis = (claim.get("diagnosis_description") or "").lower()
        line_items = claim.get("line_items", [])

        # Check for mismatch patterns (simplified version)
        mismatches = [
            {
                "diagnosis_keywords": ["dental", "tooth", "periodontal"],
                "invalid_treatments": ["mri", "ct scan", "ultrasound"],
                "message": "Advanced imaging unusual for dental procedures",
            },
            {
                "diagnosis_keywords": ["allergy", "allergic", "dermatitis"],
                "invalid_treatments": ["surgery", "surgical", "anesthesia"],
                "message": "Surgical procedures unusual for allergy treatment",
            },
            {
                "diagnosis_keywords": ["wellness", "vaccine", "checkup"],
                "invalid_treatments": ["surgery", "emergency", "hospitalization"],
                "message": "Emergency services unusual for wellness visit",
            },
        ]

        for mismatch in mismatches:
            if any(kw in diagnosis for kw in mismatch["diagnosis_keywords"]):
                for item in line_items:
                    item_desc = (item.get("description") or "").lower()
                    if any(t in item_desc for t in mismatch["invalid_treatments"]):
                        issues.append(ValidationIssue(
                            severity="warning",
                            code="DIAGNOSIS_TREATMENT_MISMATCH",
                            message=mismatch["message"],
                            field="line_items",
                            suggestion="Please verify treatment matches diagnosis",
                        ))
                        break

        return issues

    def _calculate_risk_level(self, fraud_score: float) -> str:
        """Calculate risk level from fraud score."""
        for level, (low, high) in self.fraud_thresholds.items():
            if low <= fraud_score < high:
                return level
        return "critical"

    def _determine_decision(
        self,
        issues: List[ValidationIssue],
        fraud_score: float,
        risk_level: str,
        claim: Dict[str, Any],
    ) -> tuple:
        """Determine AI recommendation and reasoning."""
        reasons = []

        # Check for critical issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            reasons.append(f"Critical issues found: {len(critical_issues)}")
            return "deny", ". ".join(reasons)

        # Check fraud score
        if fraud_score >= 50:
            reasons.append(f"High fraud score: {fraud_score:.1f}")
            return "investigation", ". ".join(reasons)

        if fraud_score >= 30:
            reasons.append(f"Elevated fraud score: {fraud_score:.1f}")
            return "manual_review", ". ".join(reasons)

        # Check for errors
        error_issues = [i for i in issues if i.severity == "error"]
        if error_issues:
            reasons.append(f"Validation errors: {len(error_issues)}")
            return "manual_review", ". ".join(reasons)

        # Check claim amount thresholds
        claim_amount = claim.get("claim_amount", 0)
        if claim_amount > 5000:
            reasons.append(f"High claim amount: ${claim_amount:,.2f}")
            return "manual_review", ". ".join(reasons)

        # Low risk - auto approve eligible
        if fraud_score < 15 and not error_issues and claim_amount < 2000:
            reasons.append("Low risk profile")
            reasons.append(f"Fraud score: {fraud_score:.1f}")
            reasons.append(f"Claim amount: ${claim_amount:,.2f}")
            return "auto_approve", ". ".join(reasons)

        # Standard review
        reasons.append("Standard risk profile")
        return "standard_review", ". ".join(reasons)

    def _calculate_confidence(
        self,
        batch: ProcessedBatch,
        issues: List[ValidationIssue],
    ) -> float:
        """Calculate AI confidence in the decision."""
        confidence = 0.9  # Base confidence

        # Reduce for extraction quality issues
        if batch.extractions:
            avg_extraction_conf = sum(
                e.confidence_score for e in batch.extractions.values()
            ) / len(batch.extractions)
            confidence *= avg_extraction_conf

        # Reduce for validation issues
        issue_penalty = len([i for i in issues if i.severity in ["error", "critical"]]) * 0.05
        confidence -= issue_penalty

        return max(0.1, min(1.0, confidence))


# Load fingerprints from file on module load
def _load_fingerprints():
    import json
    import os
    fp_file = "/tmp/docgen/fingerprints.json"
    if os.path.exists(fp_file):
        try:
            with open(fp_file, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_fingerprints():
    import json
    import os
    from uuid import UUID

    def serialize(obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    os.makedirs("/tmp/docgen", exist_ok=True)
    with open("/tmp/docgen/fingerprints.json", "w") as f:
        json.dump(_document_fingerprints, f, default=serialize)

# Initialize from file
_document_fingerprints.update(_load_fingerprints())
