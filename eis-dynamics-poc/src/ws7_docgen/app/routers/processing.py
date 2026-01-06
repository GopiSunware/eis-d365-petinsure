"""Processing router for document processing pipeline."""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.document import ProcessedBatch, ProcessingStatus, AgentStep
from app.models.api import ProcessingStatusResponse, ClaimPreviewResponse
from app.routers.upload import get_batch, save_batch


def add_step(batch: ProcessedBatch, step_type: str, message: str, status: str = "pending") -> AgentStep:
    """Add a new agent step to the batch."""
    step = AgentStep(
        step_type=step_type,
        message=message,
        status=status,
        started_at=datetime.utcnow() if status == "running" else None
    )
    batch.agent_steps.append(step)
    return step


def update_step(batch: ProcessedBatch, step_type: str, status: str, result: str = None, details: str = None):
    """Update an existing agent step."""
    for step in batch.agent_steps:
        if step.step_type == step_type:
            step.status = status
            if result:
                step.result = result
            if details:
                step.details = details
            if status == "running" and not step.started_at:
                step.started_at = datetime.utcnow()
            if status in ["completed", "failed"]:
                step.completed_at = datetime.utcnow()
            break

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process/{batch_id}", response_model=ProcessingStatusResponse)
async def start_processing(
    batch_id: str,
    background_tasks: BackgroundTasks,
    sync: bool = False,
):
    """
    Start processing documents in a batch.

    - If sync=False (default), processing runs in background
    - If sync=True, waits for processing to complete
    """
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    if batch.status == ProcessingStatus.COMPLETED:
        return ProcessingStatusResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            progress=100.0,
            current_stage="completed",
            documents_processed=len(batch.documents),
            documents_total=len(batch.documents),
        )

    if batch.status in [ProcessingStatus.EXTRACTING, ProcessingStatus.MAPPING, ProcessingStatus.VALIDATING]:
        return ProcessingStatusResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            progress=batch.progress,
            current_stage=batch.current_stage,
            documents_processed=len(batch.extractions),
            documents_total=len(batch.documents),
        )

    # Start processing
    batch.status = ProcessingStatus.EXTRACTING
    batch.started_at = datetime.utcnow()
    save_batch(batch)

    if sync:
        # Synchronous processing
        await _process_batch(batch_id)
        batch = get_batch(batch_id)
    else:
        # Background processing
        background_tasks.add_task(_process_batch, batch_id)

    return ProcessingStatusResponse(
        batch_id=batch.batch_id,
        status=batch.status,
        progress=batch.progress,
        current_stage=batch.current_stage or "starting",
        documents_processed=len(batch.extractions),
        documents_total=len(batch.documents),
    )


async def _process_batch(batch_id: str) -> None:
    """
    Process documents using the AI Agent-Driven approach.

    The DocGen Agent:
    1. Receives full context (existing claims, policy info)
    2. Reads the document
    3. THINKS and DECIDES using tools:
       - check_duplicate
       - extract_document
       - validate_claim
       - calculate_billing
       - submit_claim
    """
    import hashlib
    from app.agents.docgen_agent import DocGenAgent
    from app.services.storage_service import get_storage_service
    from app.agents.validate_agent import _document_fingerprints
    from app.models.document import ValidationIssue, FraudIndicator

    batch = get_batch(batch_id)
    if not batch:
        logger.error(f"Batch {batch_id} not found during processing")
        return

    try:
        total_docs = len(batch.documents)
        storage_service = get_storage_service()

        # ============================================================
        # AGENT-DRIVEN PROCESSING WITH STEP TRACKING
        # ============================================================

        # Initialize all steps upfront so frontend can show full pipeline
        batch.agent_steps = []  # Reset any previous steps
        add_step(batch, "check_policy", "Verify policy is valid and active")
        add_step(batch, "check_duplicate", "Check for duplicate submissions")
        add_step(batch, "extract_data", "Extract document data using AI")
        add_step(batch, "validate_fields", "Validate required fields")
        add_step(batch, "calculate_billing", "Calculate reimbursement")
        add_step(batch, "submit", "Submit for processing")

        batch.current_stage = "agent_processing"
        batch.status = ProcessingStatus.EXTRACTING
        batch.progress = 5
        save_batch(batch)

        logger.info(f"Starting AGENT-DRIVEN processing for batch {batch_id}")

        # ============================================================
        # STEP 1: Check Policy
        # ============================================================
        update_step(batch, "check_policy", "running")
        save_batch(batch)

        # Build context (includes policy info)
        context = await _build_agent_context(batch)
        policy_info = context.get("policy_info", {})

        # Validate policy
        policy_valid = True
        policy_issues = []

        if not batch.policy_number and not policy_info.get("policy_id"):
            policy_issues.append("No policy number provided")
            policy_valid = False

        # Check policy status (mock - in real system would check database)
        if policy_info.get("status") == "expired":
            policy_issues.append("Policy has expired")
            policy_valid = False
        elif policy_info.get("status") == "cancelled":
            policy_issues.append("Policy has been cancelled")
            policy_valid = False

        if policy_valid:
            update_step(batch, "check_policy", "completed", result="pass",
                       details=f"Policy {policy_info.get('policy_id', 'POL-DEFAULT')} is active")
        else:
            update_step(batch, "check_policy", "completed", result="warning",
                       details="; ".join(policy_issues) if policy_issues else "Using default policy")

        batch.progress = 10
        save_batch(batch)

        # Initialize the DocGen Agent
        agent = DocGenAgent()

        # Process each document through the agent
        all_results = []

        # ============================================================
        # CLAIM-ONLY PROCESSING (No Documents)
        # When a claim is submitted without documents, process the claim data with AI
        # ============================================================
        if total_docs == 0 and batch.claim_data:
            logger.info(f"Processing claim-only batch (no documents) with AI: {batch.claim_data.get('claim_number')}")

            # Skip duplicate check for claim-only (no document to check)
            update_step(batch, "check_duplicate", "completed", result="pass",
                       details="N/A - No documents to check")
            batch.progress = 20
            save_batch(batch)

            # Run AI agent on claim data
            update_step(batch, "extract_data", "running")
            batch.progress = 25
            save_batch(batch)

            try:
                # Call AI to analyze claim data
                claim_result = await agent.analyze_claim_data(
                    claim_data=batch.claim_data,
                    context=context
                )
                all_results.append({
                    "source": "claim_data",
                    "result": claim_result
                })
                logger.info(f"AI claim analysis result: decision={claim_result.get('decision')}, confidence={claim_result.get('confidence')}")
            except Exception as e:
                logger.error(f"AI claim analysis failed: {e}")
                all_results.append({
                    "source": "claim_data",
                    "result": {
                        "decision": "standard_review",
                        "confidence": 0.5,
                        "explanation": f"AI analysis unavailable: {str(e)}"
                    }
                })

        for i, doc in enumerate(batch.documents):
            logger.info(f"Agent processing document {i+1}/{total_docs}: {doc.original_filename}")

            # Read document content
            storage_url = doc.local_path or doc.blob_url
            if not storage_url:
                continue

            try:
                content = await storage_service.download_file(storage_url)
                document_content = content.decode('utf-8', errors='replace')
                document_hash = hashlib.sha256(content).hexdigest()

                # ============================================================
                # STEP 2: FAST PRE-CHECK - Detect exact duplicates BEFORE agent
                # ============================================================
                update_step(batch, "check_duplicate", "running")
                batch.progress = 15
                save_batch(batch)

                fingerprints = context.get("fingerprints", {})
                if document_hash in fingerprints:
                    existing = fingerprints[document_hash]
                    logger.warning(f"PRE-CHECK: Duplicate detected! Hash {document_hash[:16]}... matches {existing.get('filename')}")

                    # Update step to failed
                    update_step(batch, "check_duplicate", "completed", result="fail",
                               details=f"Exact match with '{existing.get('filename')}'")

                    # Mark remaining steps as skipped
                    for step_type in ["extract_data", "validate_fields", "calculate_billing", "submit"]:
                        update_step(batch, step_type, "completed", result="skip", details="Skipped - duplicate detected")

                    # Immediately reject - don't call agent
                    batch.status = ProcessingStatus.FAILED
                    batch.current_stage = "duplicate_check"
                    batch.error = (
                        f"🚨 DUPLICATE DOCUMENT REJECTED\n\n"
                        f"• File '{doc.original_filename}' is identical to previously submitted document\n"
                        f"• Original file: '{existing.get('filename')}'\n"
                        f"• Original batch: {existing.get('batch_id', 'unknown')[:8]}...\n"
                        f"• Confidence: 100% (exact content match)\n\n"
                        f"This document has already been processed and cannot be submitted again."
                    )
                    batch.error_stage = "pre_extraction_duplicate_check"
                    batch.validation_issues = [
                        ValidationIssue(
                            severity="critical",
                            code="DUPLICATE_EXACT_MATCH",
                            message="🚨 DUPLICATE: Exact content match with previous submission",
                            field="document",
                            suggestion=f"Previously submitted as '{existing.get('filename')}' in batch {existing.get('batch_id', '')[:8]}",
                            source="pre_check"
                        )
                    ]
                    batch.fraud_score = 75.0
                    batch.ai_decision = "deny"
                    batch.ai_reasoning = f"• Exact duplicate detected via content hash\n• Original: {existing.get('filename')}\n• Submitted: {batch.created_at.isoformat()}"
                    batch.ai_confidence = 1.0
                    batch.completed_at = datetime.utcnow()
                    batch.processing_time_ms = int(
                        (batch.completed_at - batch.started_at).total_seconds() * 1000
                    )
                    save_batch(batch)
                    logger.warning(f"Batch {batch_id} REJECTED: Duplicate document (pre-check)")
                    return  # STOP - don't call agent

                # Duplicate check passed
                update_step(batch, "check_duplicate", "completed", result="pass",
                           details="No duplicate documents found")
                batch.progress = 20
                save_batch(batch)

                # ============================================================
                # STEP 3: Extract Data (Agent Processing)
                # ============================================================
                update_step(batch, "extract_data", "running")
                batch.progress = 25
                save_batch(batch)

                # Let the AGENT process the document
                result = await agent.process_document(
                    document_content=document_content,
                    document_filename=doc.original_filename,
                    document_hash=document_hash,
                    context=context
                )

                all_results.append({
                    "document": doc.original_filename,
                    "result": result
                })

                # Check agent's decision
                decision = result.get("decision", "error")

                if decision == "duplicate_rejected":
                    # Agent detected duplicate - STOP processing
                    update_step(batch, "extract_data", "completed", result="fail",
                               details="Duplicate detected by agent")

                    # Mark remaining steps as skipped
                    for step_type in ["validate_fields", "calculate_billing", "submit"]:
                        update_step(batch, step_type, "completed", result="skip",
                                   details="Skipped - duplicate detected")

                    batch.status = ProcessingStatus.FAILED
                    batch.current_stage = "agent_duplicate_check"
                    batch.error = result.get("explanation", "Duplicate document detected")
                    batch.error_stage = "agent_processing"
                    batch.validation_issues = [
                        ValidationIssue(
                            severity="critical",
                            code="AGENT_DUPLICATE_REJECTED",
                            message=f"🚨 DUPLICATE DETECTED ({result.get('confidence', 0)*100:.0f}% confidence)",
                            field="document",
                            suggestion=result.get("explanation", ""),
                            source="docgen_agent"
                        )
                    ]
                    batch.fraud_score = result.get("fraud_score", 50.0)
                    batch.ai_decision = "deny"
                    batch.ai_reasoning = result.get("thinking", result.get("explanation", ""))
                    batch.ai_confidence = result.get("confidence", 0.95)
                    batch.completed_at = datetime.utcnow()
                    batch.processing_time_ms = int(
                        (batch.completed_at - batch.started_at).total_seconds() * 1000
                    )
                    save_batch(batch)

                    logger.warning(f"Agent REJECTED batch {batch_id}: Duplicate detected")
                    return  # STOP

            except Exception as e:
                logger.error(f"Agent processing failed for {doc.original_filename}: {e}")
                all_results.append({
                    "document": doc.original_filename,
                    "error": str(e)
                })

            batch.progress = 10 + ((i + 1) / total_docs) * 60  # 10-70%
            save_batch(batch)

        # ============================================================
        # Process agent results
        # ============================================================

        # Get the final result (from last document or combined)
        final_result = all_results[-1]["result"] if all_results else {}

        # Update extract_data step based on result
        if final_result.get("extracted_data"):
            update_step(batch, "extract_data", "completed", result="pass",
                       details=f"Extracted data from {total_docs} document(s)")
        else:
            update_step(batch, "extract_data", "completed", result="warning",
                       details="Limited data extracted")
        batch.progress = 50
        save_batch(batch)

        logger.info(f"Agent final_result keys: {list(final_result.keys()) if final_result else 'None'}")

        # Store agent's extracted data - check multiple possible locations
        extracted_data = (
            final_result.get("extracted_data") or
            final_result.get("final_result", {}).get("extracted_data") or
            final_result.get("claim_data") or
            final_result.get("final_result", {}).get("claim_data") or
            {}
        )

        if extracted_data:
            batch.mapped_claim = extracted_data
            logger.info(f"Captured extracted_data: provider={extracted_data.get('provider_name')}, "
                       f"date={extracted_data.get('service_date')}, amount={extracted_data.get('total_amount')}")
        else:
            logger.warning(f"No extracted_data found in agent result. Keys: {list(final_result.keys())}")

        # ============================================================
        # STEP 4: Validate Required Fields
        # ============================================================
        update_step(batch, "validate_fields", "running")
        batch.progress = 60
        save_batch(batch)

        # Check required fields
        required_fields = ["provider_name", "service_date", "total_amount"]
        missing_fields = []
        present_fields = []

        if extracted_data:
            for field in required_fields:
                if extracted_data.get(field):
                    present_fields.append(field)
                else:
                    missing_fields.append(field)

        if missing_fields:
            update_step(batch, "validate_fields", "completed", result="warning",
                       details=f"Missing: {', '.join(missing_fields)}")
        else:
            update_step(batch, "validate_fields", "completed", result="pass",
                       details=f"All required fields present ({len(present_fields)}/{len(required_fields)})")
        batch.progress = 70
        save_batch(batch)

        # ============================================================
        # STEP 5: Calculate Billing
        # ============================================================
        update_step(batch, "calculate_billing", "running")
        batch.progress = 80
        save_batch(batch)

        # Store billing info - check multiple possible locations
        billing_info = (
            final_result.get("billing_info") or
            final_result.get("final_result", {}).get("billing_info") or
            {}
        )

        if billing_info:
            from app.models.document import BillingCalculation
            batch.billing = BillingCalculation(
                claim_amount=Decimal(str(billing_info.get("claim_amount", 0))),
                deductible_applied=Decimal(str(billing_info.get("deductible_applied", 0))),
                covered_amount=Decimal(str(billing_info.get("amount_after_deductible", 0))),
                reimbursement_rate=billing_info.get("reimbursement_rate", 0.8),
                final_payout=Decimal(str(billing_info.get("final_payout", 0))),
                customer_responsibility=Decimal(str(billing_info.get("customer_responsibility", 0))),
            )
            logger.info(f"Captured billing_info: payout=${billing_info.get('final_payout', 0)}")
            update_step(batch, "calculate_billing", "completed", result="pass",
                       details=f"Payout: ${billing_info.get('final_payout', 0):.2f}")
        else:
            update_step(batch, "calculate_billing", "completed", result="warning",
                       details="No billing information calculated")
        batch.progress = 90
        save_batch(batch)

        # Store validation issues
        if final_result.get("validation_issues"):
            batch.validation_issues = [
                ValidationIssue(**issue) if isinstance(issue, dict) else issue
                for issue in final_result["validation_issues"]
            ]

        # Store agent decision
        batch.ai_decision = final_result.get("agent_decision", final_result.get("decision", "standard_review"))
        batch.ai_reasoning = final_result.get("thinking", final_result.get("explanation", ""))
        batch.ai_confidence = final_result.get("confidence", 0.8)

        # ============================================================
        # STEP 6: Submit for Processing - Create claim in PetInsure360
        # ============================================================
        update_step(batch, "submit", "running")
        batch.progress = 95
        save_batch(batch)

        # Determine submit result based on decision
        decision = batch.ai_decision

        # If not rejected, actually submit the claim to PetInsure360
        if decision not in ["deny", "duplicate_rejected", "investigation"]:
            try:
                submit_result = await agent.submit_claim(
                    claim_data=extracted_data or {},
                    billing_info=billing_info,
                    agent_decision=decision,
                    agent_reasoning=batch.ai_reasoning or "",
                    batch=batch  # Pass batch for customer/pet context
                )
                # Store the claim number from submission
                if submit_result.get("claim_number"):
                    batch.claim_number = submit_result.get("claim_number")
                    logger.info(f"Claim created: {batch.claim_number}")
                elif submit_result.get("claim_id"):
                    batch.claim_number = submit_result.get("claim_id")
                    logger.info(f"Claim created (local): {batch.claim_number}")
            except Exception as e:
                logger.warning(f"Failed to submit claim to PetInsure360: {e}")

        if decision in ["auto_approve", "proceed"]:
            update_step(batch, "submit", "completed", result="pass",
                       details=f"Claim {batch.claim_number or 'N/A'} submitted for automatic approval")
        elif decision == "needs_review":
            update_step(batch, "submit", "completed", result="warning",
                       details=f"Claim {batch.claim_number or 'N/A'} submitted for manual review")
        elif decision in ["deny", "duplicate_rejected", "investigation"]:
            update_step(batch, "submit", "completed", result="fail",
                       details=f"Claim rejected: {decision}")
        else:
            update_step(batch, "submit", "completed", result="pass",
                       details=f"Claim {batch.claim_number or 'N/A'} submitted for standard review")

        # Complete
        batch.status = ProcessingStatus.COMPLETED
        batch.current_stage = "completed"
        batch.progress = 100
        batch.completed_at = datetime.utcnow()
        batch.processing_time_ms = int(
            (batch.completed_at - batch.started_at).total_seconds() * 1000
        )

        logger.info(
            f"Agent completed batch {batch_id} in {batch.processing_time_ms}ms - "
            f"Decision: {batch.ai_decision}"
        )

        # ============================================================
        # SAVE FINGERPRINTS for future duplicate detection
        # ============================================================
        from app.agents.validate_agent import _document_fingerprints, _save_fingerprints

        for doc in batch.documents:
            storage_url = doc.local_path or doc.blob_url
            if storage_url:
                try:
                    content = await storage_service.download_file(storage_url)
                    content_hash = hashlib.sha256(content).hexdigest()

                    # Store fingerprint with document details
                    key = f"{batch.batch_id}:{doc.id}"
                    _document_fingerprints[key] = {
                        "batch_id": str(batch.batch_id),
                        "document_id": str(doc.id),
                        "filename": doc.original_filename,
                        "content_hash": content_hash,
                        "timestamp": datetime.utcnow().isoformat(),
                        # Store claim info for semantic duplicate detection
                        "claim_info": {
                            "provider": batch.mapped_claim.get("provider_name") if batch.mapped_claim else None,
                            "service_date": batch.mapped_claim.get("service_date") if batch.mapped_claim else None,
                            "total_amount": batch.mapped_claim.get("total_amount") if batch.mapped_claim else None,
                            "invoice_number": batch.mapped_claim.get("invoice_number") if batch.mapped_claim else None,
                        }
                    }
                    logger.info(f"Saved fingerprint for {doc.original_filename}: {content_hash[:16]}...")
                except Exception as e:
                    logger.warning(f"Failed to save fingerprint for {doc.original_filename}: {e}")

        # Persist fingerprints to disk
        try:
            _save_fingerprints()
            logger.info(f"Persisted {len(_document_fingerprints)} fingerprints to storage")
        except Exception as e:
            logger.error(f"Failed to persist fingerprints: {e}")

    except Exception as e:
        logger.error(f"Agent processing failed for batch {batch_id}: {e}")
        batch.status = ProcessingStatus.FAILED
        batch.error = str(e)
        batch.error_stage = batch.current_stage

    save_batch(batch)


async def _build_agent_context(batch) -> dict:
    """Build context for the agent including existing claims and policy info."""
    from app.agents.validate_agent import _document_fingerprints
    from app.routers.upload import list_batches

    # Build existing claims from processed batches (excluding current batch)
    existing_claims = []
    for prev_batch in list_batches():
        if str(prev_batch.batch_id) == str(batch.batch_id):
            continue  # Skip current batch
        if prev_batch.status.value != "completed":
            continue  # Only completed batches
        if prev_batch.mapped_claim:
            claim_data = prev_batch.mapped_claim if isinstance(prev_batch.mapped_claim, dict) else {}
            existing_claims.append({
                "batch_id": str(prev_batch.batch_id),
                "invoice_number": claim_data.get("invoice_number"),
                "provider_name": claim_data.get("provider_name"),
                "service_date": claim_data.get("service_date"),
                "total_amount": claim_data.get("total_amount"),
                "submission_date": prev_batch.created_at.isoformat(),
                "documents": [doc.original_filename for doc in prev_batch.documents],
            })

    logger.info(f"Agent context: {len(existing_claims)} existing claims, {len(_document_fingerprints)} fingerprints")

    # Get policy info - use batch's customer/pet data if available
    policy_info = {
        "policy_id": batch.policy_id or batch.policy_number or "POL-DEFAULT",
        "customer_id": batch.customer_id or (batch.claim_data.get("customer_id") if batch.claim_data else None) or "CUST-UNKNOWN",
        "customer_name": "Policy Holder",
        "pet_id": batch.pet_id or (batch.claim_data.get("pet_id") if batch.claim_data else None) or "PET-UNKNOWN",
        "pet_name": batch.pet_name or (batch.claim_data.get("pet_name") if batch.claim_data else None) or "Pet",
        "deductible": 500,
        "reimbursement_rate": 80,
        "annual_limit": 10000,
        "deductible_met": 0,
        "used_limit": 0
    }

    return {
        "existing_claims": existing_claims,
        "policy_info": policy_info,
        "fingerprints": {v.get("content_hash"): v for v in _document_fingerprints.values()},
        "batch_id": str(batch.batch_id)
    }


async def _check_duplicates_before_extraction(batch) -> Optional[dict]:
    """
    Check for duplicate documents BEFORE extraction.

    This is a fast check using file content hash to detect if the same
    document was previously submitted. Runs BEFORE expensive AI extraction.

    Returns:
        None if no duplicates found
        Dict with error details if duplicate detected
    """
    import hashlib
    from app.services.storage_service import get_storage_service
    from app.agents.validate_agent import _document_fingerprints, _save_fingerprints
    from app.models.document import ValidationIssue, FraudIndicator

    storage_service = get_storage_service()
    duplicates_found = []

    for doc in batch.documents:
        storage_url = doc.local_path or doc.blob_url
        if not storage_url:
            continue

        try:
            # Read file content
            content = await storage_service.download_file(storage_url)

            # Compute content hash
            content_hash = hashlib.sha256(content).hexdigest()

            # Check against stored fingerprints
            for stored_key, stored_data in _document_fingerprints.items():
                if stored_data.get("batch_id") == str(batch.batch_id):
                    continue  # Skip same batch

                if stored_data.get("content_hash") == content_hash:
                    duplicates_found.append({
                        "current_file": doc.original_filename,
                        "previous_file": stored_data.get("filename", "unknown"),
                        "previous_batch": stored_data.get("batch_id", "unknown"),
                        "match_type": "exact",
                        "confidence": 1.0,
                    })
                    break  # Found duplicate, no need to check more

        except Exception as e:
            logger.warning(f"Error checking duplicate for {doc.original_filename}: {e}")

    if duplicates_found:
        dup = duplicates_found[0]  # Report first duplicate
        error_msg = (
            f"🚨 DUPLICATE DOCUMENT REJECTED\n\n"
            f"File '{dup['current_file']}' is identical to a previously submitted document.\n\n"
            f"Match Details:\n"
            f"• Confidence: 100% (byte-for-byte match)\n"
            f"• Original File: '{dup['previous_file']}'\n"
            f"• Original Batch: {dup['previous_batch'][:8]}...\n\n"
            f"This document cannot be processed again. If this is a legitimate resubmission, "
            f"please contact support."
        )

        return {
            "error": error_msg,
            "issues": [
                ValidationIssue(
                    severity="critical",
                    code="DUPLICATE_REJECTED",
                    message="🚨 DUPLICATE DOCUMENT - Processing blocked",
                    field="document",
                    suggestion=f"This exact document was previously submitted in batch {dup['previous_batch'][:8]}...",
                    source="pre_extraction_check",
                )
            ],
            "fraud_indicators": [
                FraudIndicator(
                    indicator="Duplicate document submission blocked",
                    score_impact=50.0,
                    confidence=1.0,
                    description=f"Exact match with '{dup['previous_file']}' from batch {dup['previous_batch'][:8]}",
                    pattern_type="duplicate_submission",
                )
            ],
            "fraud_score": 50.0,
            "duplicate_details": dup,
        }

    # No duplicates found - store fingerprints for this batch's documents
    for doc in batch.documents:
        storage_url = doc.local_path or doc.blob_url
        if not storage_url:
            continue

        try:
            content = await storage_service.download_file(storage_url)
            content_hash = hashlib.sha256(content).hexdigest()

            key = f"{batch.batch_id}:{doc.id}"
            _document_fingerprints[key] = {
                "batch_id": str(batch.batch_id),
                "filename": doc.original_filename,
                "content_hash": content_hash,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Error storing fingerprint for {doc.original_filename}: {e}")

    # Save updated fingerprints
    try:
        _save_fingerprints()
    except Exception as e:
        logger.error(f"Failed to save fingerprints: {e}")

    logger.info(f"Duplicate check passed for batch {batch.batch_id} - no duplicates found")
    return None  # No duplicates


@router.get("/status/{batch_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(batch_id: str):
    """Get the current processing status of a batch."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    # Estimate remaining time
    estimated_remaining = None
    if batch.started_at and batch.progress > 0 and batch.progress < 100:
        elapsed = (datetime.utcnow() - batch.started_at).total_seconds()
        total_estimated = elapsed / (batch.progress / 100)
        estimated_remaining = int(total_estimated - elapsed)

    return ProcessingStatusResponse(
        batch_id=batch.batch_id,
        status=batch.status,
        progress=batch.progress,
        current_stage=batch.current_stage,
        documents_processed=len(batch.extractions),
        documents_total=len(batch.documents),
        estimated_remaining_seconds=estimated_remaining,
        error=batch.error,
    )


@router.get("/result/{batch_id}")
async def get_processing_result(batch_id: str):
    """Get complete processing results for a batch."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    if batch.status not in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Processing not complete. Current status: {batch.status.value}",
        )

    return batch


@router.get("/preview-claim/{batch_id}", response_model=ClaimPreviewResponse)
async def preview_claim_mapping(batch_id: str):
    """Preview how extracted data will map to claim fields."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    if not batch.mapped_claim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim mapping not yet complete",
        )

    # Calculate confidence scores for each field
    confidence_scores = {}
    fields_requiring_review = []

    for field, value in batch.mapped_claim.items():
        if isinstance(value, dict) and "confidence" in value:
            confidence_scores[field] = value["confidence"]
            if value["confidence"] < 0.7:
                fields_requiring_review.append(field)
        elif value is not None:
            confidence_scores[field] = 0.9  # Default high confidence for derived fields

    return ClaimPreviewResponse(
        batch_id=batch.batch_id,
        mapped_claim=batch.mapped_claim,
        confidence_scores=confidence_scores,
        fields_requiring_review=fields_requiring_review,
        validation_issues=batch.validation_issues,
        fraud_indicators=[
            {
                "indicator": fi.indicator,
                "score_impact": fi.score_impact,
                "confidence": fi.confidence,
                "description": fi.description,
                "pattern_type": fi.pattern_type,
            }
            for fi in batch.fraud_indicators
        ],
        billing_summary=batch.billing.dict() if batch.billing else None,
    )


@router.post("/reprocess/{batch_id}")
async def reprocess_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
):
    """Reprocess a batch (reset and start fresh)."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    # Reset batch state
    batch.status = ProcessingStatus.PENDING
    batch.current_stage = None
    batch.progress = 0
    batch.extractions = {}
    batch.mapped_claim = None
    batch.validation_issues = []
    batch.fraud_indicators = []
    batch.fraud_score = 0.0
    batch.ai_decision = None
    batch.ai_reasoning = None
    batch.error = None
    batch.error_stage = None
    batch.started_at = None
    batch.completed_at = None

    save_batch(batch)

    # Start processing
    return await start_processing(batch_id, background_tasks, sync=False)
