"""
Pipeline API router for triggering and managing pipeline runs.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..models import (
    PipelineStage,
    PipelineStatus,
    TriggerRequest,
    TriggerResponse,
)
from ..orchestration import medallion_pipeline, state_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.post("/trigger", response_model=TriggerResponse)
async def trigger_pipeline(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger the agent pipeline for a claim.

    This endpoint starts the medallion pipeline processing
    in the background and returns immediately with a run ID.
    """
    # Generate run ID
    run_id = f"RUN-{uuid4().hex[:8].upper()}"

    logger.info(f"Triggering pipeline: run={run_id}, claim={request.claim_id}")

    # Start processing in background
    background_tasks.add_task(
        medallion_pipeline.process_claim,
        run_id=run_id,
        claim_id=request.claim_id,
        claim_data=request.claim_data,
    )

    return TriggerResponse(
        run_id=run_id,
        claim_id=request.claim_id,
        status=PipelineStatus.STARTED,
        current_stage=PipelineStage.TRIGGER,
        started_at=datetime.utcnow(),
        message="Pipeline started successfully",
    )


@router.post("/trigger/sync")
async def trigger_pipeline_sync(request: TriggerRequest):
    """
    Trigger the agent pipeline synchronously.

    Waits for the pipeline to complete before returning results.
    Use for testing or when immediate results are needed.
    """
    # Generate run ID
    run_id = f"RUN-{uuid4().hex[:8].upper()}"

    logger.info(f"Triggering pipeline (sync): run={run_id}, claim={request.claim_id}")

    # Run pipeline synchronously
    result = await medallion_pipeline.process_claim(
        run_id=run_id,
        claim_id=request.claim_id,
        claim_data=request.claim_data,
    )

    return result


@router.get("/run/{run_id}")
async def get_pipeline_run(run_id: str):
    """
    Get the current state of a pipeline run.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    return state.model_dump()


@router.get("/run/{run_id}/bronze")
async def get_bronze_output(run_id: str):
    """
    Get the Bronze layer output for a pipeline run.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    if not state.bronze_output:
        raise HTTPException(status_code=404, detail="Bronze output not yet available")

    return state.bronze_output


@router.get("/run/{run_id}/silver")
async def get_silver_output(run_id: str):
    """
    Get the Silver layer output for a pipeline run.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    if not state.silver_output:
        raise HTTPException(status_code=404, detail="Silver output not yet available")

    return state.silver_output


@router.get("/run/{run_id}/gold")
async def get_gold_output(run_id: str):
    """
    Get the Gold layer output for a pipeline run.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    if not state.gold_output:
        raise HTTPException(status_code=404, detail="Gold output not yet available")

    return state.gold_output


@router.get("/active")
async def get_active_runs():
    """
    Get all currently active pipeline runs.
    """
    runs = await state_manager.get_all_active_runs()
    return {
        "active_runs": [run.model_dump() for run in runs],
        "count": len(runs),
    }


@router.get("/recent")
async def get_recent_runs(limit: int = 50, offset: int = 0):
    """
    Get recent pipeline runs.
    """
    runs = await state_manager.get_recent_runs(limit=limit, offset=offset)
    return {
        "runs": [run.model_dump() for run in runs],
        "count": len(runs),
        "limit": limit,
        "offset": offset,
    }


@router.post("/demo/claim")
async def trigger_demo_claim(
    background_tasks: BackgroundTasks,
    complexity: str = "medium",
):
    """
    Trigger a demo claim for testing.

    Creates a synthetic claim and processes it through the pipeline.
    """
    # Generate demo claim data based on complexity
    claim_id = f"CLM-DEMO-{uuid4().hex[:8].upper()}"

    if complexity == "simple":
        claim_data = {
            "claim_id": claim_id,
            "policy_id": "POL-2024-00567",
            "customer_id": "CUST-001",
            "pet_id": "PET-001",
            "claim_type": "wellness",
            "claim_amount": 150.00,
            "diagnosis_code": "Z00.0",
            "diagnosis_description": "Annual wellness exam",
            "treatment_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "submission_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "provider_name": "City Pet Hospital",
        }
    elif complexity == "complex":
        claim_data = {
            "claim_id": claim_id,
            "policy_id": "POL-2024-00123",
            "customer_id": "CUST-002",
            "pet_id": "PET-002",
            "claim_type": "emergency",
            "claim_amount": 12500.00,
            "diagnosis_code": "S83.50",
            "diagnosis_description": "ACL tear requiring surgery",
            "treatment_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "submission_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "provider_name": "Emergency Vet Clinic",
        }
    else:  # medium
        claim_data = {
            "claim_id": claim_id,
            "policy_id": "POL-2024-00567",
            "customer_id": "CUST-001",
            "pet_id": "PET-001",
            "claim_type": "accident",
            "claim_amount": 4500.00,
            "diagnosis_code": "K9-ACL",
            "diagnosis_description": "Cruciate ligament injury",
            "treatment_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "submission_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "provider_name": "City Pet Hospital",
        }

    # Trigger pipeline
    run_id = f"RUN-{uuid4().hex[:8].upper()}"

    logger.info(f"Triggering demo pipeline: run={run_id}, claim={claim_id}, complexity={complexity}")

    background_tasks.add_task(
        medallion_pipeline.process_claim,
        run_id=run_id,
        claim_id=claim_id,
        claim_data=claim_data,
    )

    return {
        "run_id": run_id,
        "claim_id": claim_id,
        "complexity": complexity,
        "claim_data": claim_data,
        "message": f"Demo {complexity} claim triggered successfully",
    }


# =============================================================================
# MANUAL STEP-BY-STEP PROCESSING ENDPOINTS
# =============================================================================

@router.post("/ingest")
async def ingest_claim(request: TriggerRequest):
    """
    Ingest a claim into the pipeline without processing.

    The claim will be placed in 'pending' status, waiting for manual
    trigger to start Bronze processing. This allows step-by-step
    processing similar to the Rule Engine Pipeline.
    """
    run_id = f"RUN-{uuid4().hex[:8].upper()}"

    logger.info(f"Ingesting claim for manual processing: run={run_id}, claim={request.claim_id}")

    # Initialize pipeline state without starting processing
    await state_manager.initialize_pending_run(
        run_id=run_id,
        claim_id=request.claim_id,
        claim_data=request.claim_data,
    )

    return {
        "run_id": run_id,
        "claim_id": request.claim_id,
        "status": "pending",
        "current_stage": "ingested",
        "message": "Claim ingested. Click 'Process Bronze' to start validation.",
        "next_action": "process_bronze",
    }


@router.post("/run/{run_id}/process/bronze")
async def process_bronze(run_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger Bronze layer processing for a pending claim.

    Runs the Router and Bronze agents, then pauses for user action.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    # Check if already processed Bronze
    if state.bronze_output and state.bronze_state and state.bronze_state.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Bronze already processed. Use process_silver next.")

    logger.info(f"Manually triggering Bronze for run {run_id}")

    # Process Router + Bronze in background
    background_tasks.add_task(
        medallion_pipeline.process_through_bronze,
        run_id=run_id,
    )

    return {
        "run_id": run_id,
        "status": "processing",
        "current_stage": "bronze",
        "message": "Bronze processing started. Poll /run/{run_id} for status.",
    }


@router.post("/run/{run_id}/process/silver")
async def process_silver(run_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger Silver layer processing.

    Requires Bronze to be completed first.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    # Check if Bronze is completed
    if not state.bronze_output or not state.bronze_state or state.bronze_state.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Bronze not yet completed. Process Bronze first.")

    # Check if Silver already processed
    if state.silver_output and state.silver_state and state.silver_state.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Silver already processed. Use process_gold next.")

    logger.info(f"Manually triggering Silver for run {run_id}")

    # Process Silver in background
    background_tasks.add_task(
        medallion_pipeline.process_silver_only,
        run_id=run_id,
    )

    return {
        "run_id": run_id,
        "status": "processing",
        "current_stage": "silver",
        "message": "Silver processing started. Poll /run/{run_id} for status.",
    }


@router.post("/run/{run_id}/process/gold")
async def process_gold(run_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger Gold layer processing.

    Requires Silver to be completed first.
    """
    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    # Check if Silver is completed
    if not state.silver_output or not state.silver_state or state.silver_state.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Silver not yet completed. Process Silver first.")

    # Check if Gold already processed
    if state.gold_output and state.gold_state and state.gold_state.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Gold already processed. Pipeline complete.")

    logger.info(f"Manually triggering Gold for run {run_id}")

    # Process Gold in background
    background_tasks.add_task(
        medallion_pipeline.process_gold_only,
        run_id=run_id,
    )

    return {
        "run_id": run_id,
        "status": "processing",
        "current_stage": "gold",
        "message": "Gold processing started. Poll /run/{run_id} for status.",
    }


@router.get("/pending")
async def get_pending_runs():
    """
    Get all pipeline runs waiting for manual processing.
    """
    runs = await state_manager.get_pending_runs()
    return {
        "pending_runs": [run.model_dump() for run in runs],
        "count": len(runs),
    }


@router.post("/run/{run_id}/summary")
async def generate_run_summary(run_id: str):
    """
    Generate an LLM-powered summary of a pipeline run.

    Returns a high-level overview of the claim processing,
    key decisions made, and recommendations.
    """
    from ..config import settings

    state = await state_manager.get_pipeline_state(run_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    if state.status.value not in ("completed", "failed"):
        raise HTTPException(status_code=400, detail="Pipeline not yet completed")

    # Build context for LLM
    claim_data = state.claim_data or {}
    bronze = state.bronze_output or {}
    silver = state.silver_output or {}
    gold = state.gold_output or {}

    # Determine final decision from available outputs
    final_decision = gold.get('decision') or gold.get('final_decision') or bronze.get('decision') or 'PENDING_REVIEW'
    risk_level = gold.get('risk_level') or silver.get('risk_level') or 'UNKNOWN'
    estimated_payout = silver.get('estimated_reimbursement') or silver.get('reimbursement_amount') or 0

    # Handle failed pipeline
    if state.status.value == "failed":
        error_msg = state.error or "Unknown error"
        summary = f"Claim {state.claim_id} for ${claim_data.get('claim_amount', 0):,.2f} encountered a processing error and requires manual review. Error: {error_msg}. Recommended action: Review claim manually and reprocess if needed."
        return {
            "run_id": run_id,
            "claim_id": state.claim_id,
            "summary": summary,
            "final_decision": "MANUAL_REVIEW",
            "risk_level": "HIGH",
            "estimated_payout": 0,
            "processing_time_ms": state.total_processing_time_ms,
        }

    context = f"""
Claim ID: {state.claim_id}
Claim Amount: ${claim_data.get('claim_amount', 0):,.2f}
Claim Type: {claim_data.get('claim_type', 'Unknown')}
Pet Name: {claim_data.get('pet_name', claim_data.get('pet_id', 'Unknown'))}
Provider: {claim_data.get('provider_name', 'Unknown')}
Diagnosis: {claim_data.get('diagnosis_description', claim_data.get('diagnosis_code', 'N/A'))}
Treatment Notes: {claim_data.get('treatment_notes', 'N/A')}

Bronze Layer (Validation):
- Decision: {bronze.get('decision', 'PASSED')}
- Quality Score: {bronze.get('quality_score', bronze.get('data_quality_score', 'N/A'))}
- Issues: {bronze.get('validation_issues', bronze.get('issues', []))}

Silver Layer (Enrichment):
- Estimated Reimbursement: ${estimated_payout:,.2f}
- Processing Priority: {silver.get('processing_priority', silver.get('priority', 'NORMAL'))}
- In-Network: {silver.get('is_in_network', 'N/A')}

Gold Layer (Decision):
- Final Decision: {final_decision}
- Risk Level: {risk_level}
- Risk Score: {gold.get('risk_score', gold.get('fraud_risk_score', 'N/A'))}
- Confidence: {gold.get('confidence', 'N/A')}
- Insights: {gold.get('insights', gold.get('ai_insights', []))}

Processing Time: {state.total_processing_time_ms:.0f}ms
Pipeline Status: {state.status.value}
"""

    prompt = f"""You are a claims processing analyst. Analyze this pet insurance claim that was just processed through our AI pipeline.

Provide a concise 3-4 sentence executive summary that:
1. Describes what the claim was for (pet type, condition, amount)
2. Explains the key decision and why it was made
3. Highlights any notable risks or insights
4. States the recommended next action

Claim Processing Results:
{context}

Write the summary in a professional but friendly tone. Be specific about amounts and decisions. Start with "This claim..." or "The claim..."."""

    # Use configured AI provider
    summary = ""
    try:
        if settings.AI_PROVIDER == "claude":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.content[0].text
        else:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        # Fallback to descriptive summary
        claim_amount = claim_data.get('claim_amount', 0)
        claim_type = claim_data.get('claim_type', 'Unknown')
        diagnosis = claim_data.get('diagnosis_description', claim_data.get('diagnosis_code', 'Unknown condition'))
        summary = f"This {claim_type} claim for ${claim_amount:,.2f} ({diagnosis}) was processed with decision: {final_decision}. Risk level: {risk_level}. Processing completed in {state.total_processing_time_ms/1000:.1f} seconds."

    return {
        "run_id": run_id,
        "claim_id": state.claim_id,
        "summary": summary,
        "final_decision": final_decision,
        "risk_level": risk_level,
        "estimated_payout": estimated_payout,
        "processing_time_ms": state.total_processing_time_ms,
    }
