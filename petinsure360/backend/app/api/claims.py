"""
PetInsure360 - Claims API
Endpoints for claim submission and tracking
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from app.models.schemas import ClaimCreate, ClaimResponse, ClaimStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Agent Pipeline URL (EIS Dynamics Agent Pipeline)
AGENT_PIPELINE_URL = os.getenv("AGENT_PIPELINE_URL", "http://localhost:8006")
# DocGen Service URL (EIS Dynamics DocGen - for AI batch processing)
DOCGEN_SERVICE_URL = os.getenv("DOCGEN_SERVICE_URL", "http://localhost:8007")


async def trigger_agent_pipeline(claim_data: dict) -> dict | None:
    """
    Trigger the EIS Dynamics Agent Pipeline for claim processing.

    This sends the claim to the agent-driven medallion architecture for
    intelligent processing through Bronze, Silver, and Gold layers.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{AGENT_PIPELINE_URL}/api/v1/pipeline/trigger",
                json={
                    "event_type": "claim.submitted",
                    "source": "petinsure360",
                    "claim_id": claim_data["claim_id"],
                    "claim_data": claim_data,
                },
            )
            response.raise_for_status()
            result = response.json()
            logger.info(
                f"Agent pipeline triggered for claim {claim_data['claim_id']}: "
                f"run_id={result.get('run_id')}"
            )
            return result
    except httpx.HTTPError as e:
        logger.warning(
            f"Failed to trigger agent pipeline for claim {claim_data['claim_id']}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Error triggering agent pipeline for claim {claim_data['claim_id']}: {e}"
        )
        return None


async def create_docgen_batch(claim_data: dict) -> dict | None:
    """
    Create a batch in DocGen service for AI-driven claim processing.

    This sends the claim to DocGen (8007) to create a batch that will
    appear in the Agent Pipeline page of the BI Dashboard.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Create a batch from claim data (no documents)
            response = await client.post(
                f"{DOCGEN_SERVICE_URL}/api/v1/docgen/batch/from-claim",
                json={
                    "claim_id": claim_data["claim_id"],
                    "claim_number": claim_data["claim_number"],
                    "customer_id": claim_data["customer_id"],
                    "pet_id": claim_data["pet_id"],
                    "policy_id": claim_data.get("policy_id"),
                    "claim_type": claim_data["claim_type"],
                    "claim_category": claim_data.get("claim_category"),
                    "claim_amount": claim_data["claim_amount"],
                    "diagnosis_code": claim_data.get("diagnosis_code"),
                    "treatment_notes": claim_data.get("treatment_notes"),
                    "is_emergency": claim_data.get("is_emergency", False),
                    "service_date": claim_data.get("service_date"),
                    "source": "petinsure360_portal"
                },
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"DocGen batch created for claim {claim_data['claim_id']}: "
                    f"batch_id={result.get('batch_id')}"
                )
                return result
            else:
                logger.warning(f"DocGen batch creation returned {response.status_code}: {response.text}")
                return None
    except httpx.ConnectError:
        logger.warning(f"DocGen service unavailable at {DOCGEN_SERVICE_URL}")
        return None
    except Exception as e:
        logger.error(f"Error creating DocGen batch for claim {claim_data['claim_id']}: {e}")
        return None

# In-memory claim status tracking (for demo)
claim_status_cache = {}

@router.post("/", response_model=ClaimResponse)
async def submit_claim(claim: ClaimCreate, request: Request):
    """
    Submit a new insurance claim.

    Writes claim data to Azure Data Lake Storage for ETL processing.
    Emits real-time status updates via WebSocket.
    """
    # Generate claim ID and number
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    claim_number = f"CLM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Get values from helper methods (supports multiple field names)
    actual_claim_amount = claim.get_claim_amount()
    actual_diagnosis = claim.get_diagnosis()
    actual_notes = claim.get_notes()

    # Prepare data for storage
    claim_data = {
        "claim_id": claim_id,
        "claim_number": claim_number,
        "policy_id": claim.policy_id,
        "pet_id": claim.pet_id,
        "customer_id": claim.customer_id,
        "provider_id": claim.provider_id,
        "provider_name": claim.provider_name,
        "claim_type": claim.claim_type.value,
        "claim_category": claim.claim_category,
        "service_date": claim.service_date.isoformat(),
        "submitted_date": datetime.utcnow().date().isoformat(),
        "claim_amount": actual_claim_amount,
        "deductible_applied": 0.0,  # Calculated during processing
        "covered_amount": 0.0,
        "paid_amount": 0.0,
        "status": "Submitted",
        "denial_reason": None,
        "processing_days": 0,
        "diagnosis_code": actual_diagnosis,
        "treatment_notes": actual_notes,
        "invoice_number": claim.invoice_number,
        "is_emergency": claim.is_emergency,
        "is_recurring": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Write to ADLS
    storage = request.app.state.storage
    await storage.write_json("claims", claim_data, claim_id)

    # Trigger BOTH pipelines for comparison:
    # 1. EIS Dynamics Agent Pipeline (8006) - agent-driven medallion architecture
    pipeline_result = await trigger_agent_pipeline(claim_data)
    if pipeline_result:
        claim_data["agent_pipeline_run_id"] = pipeline_result.get("run_id")

    # 2. DocGen Service (8007) - AI batch processing (appears in BI Dashboard)
    docgen_result = await create_docgen_batch(claim_data)
    if docgen_result:
        claim_data["docgen_batch_id"] = docgen_result.get("batch_id")

    # Add to in-memory insights data for real-time BI display
    insights = request.app.state.insights
    insights.add_claim(claim_data)

    # Add to Legacy Pipeline Bronze layer for rule-based processing
    from app.api.pipeline import pipeline_state, _save_pipeline_state
    bronze_claim = {
        **claim_data,
        "ingestion_timestamp": datetime.utcnow().isoformat(),
        "source": "customer_portal",
        "raw_status": "ingested",
        "layer": "bronze",
        "line_items": [],  # Will be populated from documents if any
        "diagnosis": claim.diagnosis_code or "",
        "provider_name": claim.provider_id or "Unknown Provider",
        "is_in_network": True,
    }
    pipeline_state["pending_claims"].append(bronze_claim)
    pipeline_state["processing_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "BRONZE_INGEST",
        "claim_id": claim_id,
        "message": f"Claim {claim_number} migrated to Bronze layer"
    })
    _save_pipeline_state()  # Persist to disk

    # Emit WebSocket event for Legacy Pipeline Bronze layer
    sio = request.app.state.sio
    await sio.emit('claim_to_bronze', {
        'claim_id': claim_id,
        'claim_number': claim_number,
        'amount': claim.claim_amount,
        'category': claim.claim_category,
        'layer': 'bronze',
        'timestamp': datetime.utcnow().isoformat()
    })

    # Cache status for real-time tracking
    claim_status_cache[claim_id] = {
        "claim_id": claim_id,
        "claim_number": claim_number,
        "status": "Submitted",
        "claim_amount": claim.claim_amount,
        "covered_amount": None,
        "paid_amount": None,
        "processing_days": None,
        "denial_reason": None,
        "updated_at": datetime.utcnow()
    }

    # Emit WebSocket events
    sio = request.app.state.sio

    # Broadcast to all
    await sio.emit('claim_submitted', {
        'claim_id': claim_id,
        'claim_number': claim_number,
        'customer_id': claim.customer_id,
        'claim_type': claim.claim_type.value,
        'claim_amount': claim.claim_amount,
        'status': 'Submitted',
        'timestamp': datetime.utcnow().isoformat()
    })

    # Notify customer room
    await sio.emit('claim_status_update', {
        'claim_id': claim_id,
        'claim_number': claim_number,
        'status': 'Submitted',
        'message': 'Your claim has been received and is being processed'
    }, room=f"customer_{claim.customer_id}")

    return ClaimResponse(
        claim_id=claim_id,
        claim_number=claim_number,
        policy_id=claim.policy_id,
        pet_id=claim.pet_id,
        customer_id=claim.customer_id,
        claim_type=claim.claim_type.value,
        claim_amount=claim.claim_amount,
        status="Submitted",
        submitted_date=datetime.utcnow(),
        message=f"Claim {claim_number} submitted successfully. You will receive updates on its status."
    )

@router.get("/{claim_id}/status", response_model=ClaimStatusResponse)
async def get_claim_status(claim_id: str, request: Request):
    """Get current claim status."""
    # Check cache first
    if claim_id in claim_status_cache:
        status = claim_status_cache[claim_id]
        return ClaimStatusResponse(
            claim_id=status["claim_id"],
            claim_number=status["claim_number"],
            status=status["status"],
            claim_amount=status["claim_amount"],
            covered_amount=status.get("covered_amount"),
            paid_amount=status.get("paid_amount"),
            processing_days=status.get("processing_days"),
            denial_reason=status.get("denial_reason"),
            updated_at=status["updated_at"]
        )

    # In production, query from Gold layer
    raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

@router.get("/customer/{customer_id}")
async def get_customer_claims(customer_id: str, request: Request):
    """Get all claims for a customer."""
    insights = request.app.state.insights
    claims_list = insights.get_customer_claims(customer_id)

    # Also include any cached claims (newly submitted) that match this customer
    for claim in claim_status_cache.values():
        # Check if claim belongs to this customer and not already in list
        claim_id = claim.get('claim_id')
        if claim_id and not any(c.get('claim_id') == claim_id for c in claims_list):
            claims_list.append(claim)

    return {
        "customer_id": customer_id,
        "claims": claims_list,
        "count": len(claims_list)
    }

@router.post("/{claim_id}/simulate-processing")
async def simulate_claim_processing(claim_id: str, request: Request):
    """
    Simulate claim processing for demo purposes.
    Updates the claim status through the processing workflow.
    """
    import asyncio
    import random

    if claim_id not in claim_status_cache:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    sio = request.app.state.sio
    claim = claim_status_cache[claim_id]

    # Simulate processing stages
    stages = [
        ("Under Review", "Your claim is being reviewed by our team"),
        ("Approved", "Your claim has been approved!"),
        ("Paid", "Payment has been processed")
    ]

    for status, message in stages:
        await asyncio.sleep(2)  # Simulate processing time

        # Update status
        claim["status"] = status
        claim["updated_at"] = datetime.utcnow()

        if status == "Approved":
            claim["covered_amount"] = claim["claim_amount"] * 0.8
            claim["paid_amount"] = claim["covered_amount"]
            claim["processing_days"] = random.randint(2, 5)

        # Emit status update
        await sio.emit('claim_status_update', {
            'claim_id': claim_id,
            'claim_number': claim["claim_number"],
            'status': status,
            'message': message,
            'covered_amount': claim.get("covered_amount"),
            'paid_amount': claim.get("paid_amount"),
            'timestamp': datetime.utcnow().isoformat()
        })

    return {
        "claim_id": claim_id,
        "final_status": claim["status"],
        "message": "Claim processing simulation completed"
    }


# ============================================================================
# CONVENIENCE ENDPOINTS (aliases for common query patterns)
# ============================================================================

async def _list_claims_impl(
    request: Request,
    customer_id: Optional[str] = None,
    limit: int = 100
):
    """Implementation for listing claims."""
    insights = request.app.state.insights

    if customer_id:
        claims = insights.get_customer_claims(customer_id)
    else:
        claims = insights.get_recent_claims(limit=limit)

    return {
        "claims": claims[:limit],
        "count": len(claims[:limit]),
        "filter": {"customer_id": customer_id} if customer_id else None
    }


@router.get("/")
@router.get("")  # Also handle without trailing slash
async def list_claims(
    request: Request,
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(100, description="Max results")
):
    """
    List claims with optional filtering.

    Query params:
    - customer_id: Filter by customer
    - limit: Max results (default 100)
    """
    return await _list_claims_impl(request, customer_id, limit)
