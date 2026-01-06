"""
Comparison API router for running both code-driven and agent-driven processing.

This enables 1-to-1 comparison between traditional deterministic processing
and AI agent-driven processing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..orchestration import medallion_pipeline, state_manager
from ..services.code_processor import code_processor
from ..services.s3_service import get_s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.post("/run")
async def run_comparison(claim_data: dict[str, Any]):
    """
    Run both code-driven and agent-driven processing on the same claim.

    Returns side-by-side results for comparison including:
    - Processing times
    - Decisions made
    - Quality scores
    - Risk assessments
    - Reasoning (agent only)
    """
    comparison_id = f"CMP-{uuid4().hex[:8].upper()}"
    claim_id = claim_data.get("claim_id", f"CLM-{uuid4().hex[:8].upper()}")
    claim_data["claim_id"] = claim_id

    logger.info(f"Running comparison: {comparison_id} for claim {claim_id}")

    start_time = datetime.utcnow()

    # Run both processors in parallel
    code_task = asyncio.create_task(
        code_processor.process_claim(claim_data, run_id=f"CODE-{comparison_id}")
    )

    agent_run_id = f"AGENT-{comparison_id}"
    agent_task = asyncio.create_task(
        medallion_pipeline.process_claim(
            run_id=agent_run_id,
            claim_id=claim_id,
            claim_data=claim_data,
        )
    )

    # Wait for both to complete
    code_result, agent_result = await asyncio.gather(code_task, agent_task)

    # Get agent state for full details
    agent_state = await state_manager.get_pipeline_state(agent_run_id)

    end_time = datetime.utcnow()

    # Build comparison result
    comparison = {
        "comparison_id": comparison_id,
        "claim_id": claim_id,
        "claim_data": claim_data,
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "total_time_ms": (end_time - start_time).total_seconds() * 1000,

        # Code-driven results
        "code_driven": {
            "run_id": code_result.get("run_id"),
            "processing_time_ms": code_result.get("total_processing_time_ms"),
            "final_decision": code_result.get("final_decision"),
            "risk_level": code_result.get("risk_level"),
            "estimated_payout": code_result.get("estimated_payout"),
            "bronze": code_result.get("stages", {}).get("bronze", {}),
            "silver": code_result.get("stages", {}).get("silver", {}),
            "gold": code_result.get("stages", {}).get("gold", {}),
            "reasoning": [],  # Code doesn't explain
            "insights": [],  # Code doesn't generate insights
        },

        # Agent-driven results
        "agent_driven": {
            "run_id": agent_run_id,
            "processing_time_ms": (
                agent_state.total_processing_time_ms if agent_state else 0
            ),
            "final_decision": (
                agent_state.gold_output.get("decision") if agent_state and agent_state.gold_output else None
            ),
            "risk_level": (
                agent_state.gold_output.get("risk_level") if agent_state and agent_state.gold_output else None
            ),
            "estimated_payout": (
                agent_state.silver_output.get("estimated_reimbursement")
                if agent_state and agent_state.silver_output else None
            ),
            "bronze": agent_state.bronze_output if agent_state else None,
            "silver": agent_state.silver_output if agent_state else None,
            "gold": agent_state.gold_output if agent_state else None,
            "reasoning": agent_state.gold_state.reasoning_log if agent_state and agent_state.gold_state else [],
            "insights": (
                agent_state.gold_output.get("insights", [])
                if agent_state and agent_state.gold_output else []
            ),
        },

        # Comparison metrics
        "comparison_metrics": _calculate_comparison_metrics(
            code_result,
            agent_state.model_dump() if agent_state else {},
        ),
    }

    return comparison


@router.post("/scenario/{scenario_id}")
async def run_scenario_comparison(scenario_id: str):
    """
    Run comparison using a pre-defined scenario.
    """
    from .scenarios import load_scenarios

    scenarios = load_scenarios()
    scenario = next((s for s in scenarios if s.get("id") == scenario_id), None)

    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    # Convert scenario to claim data format
    claim_data = {
        "claim_id": f"CLM-{scenario_id}-{uuid4().hex[:4].upper()}",
        "policy_id": "POL-DEMO-001",
        "customer_id": "CUST-DEMO-001",
        "pet_id": scenario.get("pet_id", "PET-DEMO-001"),
        "pet_name": scenario.get("pet_name"),
        "claim_type": scenario.get("claim_type"),
        "claim_category": scenario.get("claim_category"),
        "claim_amount": scenario.get("claim_amount"),
        "diagnosis_code": scenario.get("diagnosis_code"),
        "diagnosis_description": scenario.get("diagnosis"),
        "treatment_notes": scenario.get("treatment_notes"),
        "service_date": scenario.get("service_date"),
        "provider_id": scenario.get("provider_id"),
        "provider_name": scenario.get("provider_name"),
        "is_in_network": scenario.get("is_in_network", True),
        "is_emergency": scenario.get("is_emergency", False),
        "line_items": scenario.get("line_items", []),
    }

    return await run_comparison(claim_data)


@router.post("/quick")
async def run_quick_comparison(complexity: str = "medium"):
    """
    Run a quick comparison with synthetic demo data.

    Complexity levels:
    - simple: Low value wellness claim (~$500)
    - medium: Moderate accident claim (~$3000)
    - complex: High value emergency (~$8000)
    """
    claim_id = f"CLM-QUICK-{uuid4().hex[:6].upper()}"

    if complexity == "simple":
        claim_data = {
            "claim_id": claim_id,
            "policy_id": "POL-DEMO-001",
            "customer_id": "CUST-DEMO-001",
            "pet_id": "PET-DEMO-001",
            "pet_name": "Buddy",
            "claim_type": "Wellness",
            "claim_category": "Preventive Care",
            "claim_amount": 520.00,
            "diagnosis_code": "Z00.0",
            "diagnosis_description": "Annual wellness exam with vaccinations",
            "treatment_notes": "Routine checkup, all vaccines updated, heartworm negative",
            "service_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "provider_name": "Companion Animal Hospital",
            "is_in_network": True,
            "is_emergency": False,
            "line_items": [
                {"description": "Wellness exam", "amount": 65.00},
                {"description": "DHPP vaccine", "amount": 35.00},
                {"description": "Rabies vaccine", "amount": 25.00},
                {"description": "Heartworm test", "amount": 55.00},
                {"description": "Flea/tick prevention (6mo)", "amount": 145.00},
                {"description": "Heartworm prevention (6mo)", "amount": 95.00},
                {"description": "Fecal exam", "amount": 35.00},
                {"description": "Bordetella vaccine", "amount": 30.00},
                {"description": "Leptospirosis vaccine", "amount": 35.00},
            ],
        }
    elif complexity == "complex":
        claim_data = {
            "claim_id": claim_id,
            "policy_id": "POL-DEMO-002",
            "customer_id": "CUST-DEMO-002",
            "pet_id": "PET-DEMO-002",
            "pet_name": "Max",
            "claim_type": "Accident",
            "claim_category": "Emergency/Critical",
            "claim_amount": 8500.00,
            "diagnosis_code": "K56.2",
            "diagnosis_description": "Gastric dilatation-volvulus (GDV) with splenic torsion",
            "treatment_notes": "Emergency decompression and surgery. Gastropexy performed. Partial splenectomy required.",
            "service_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "provider_name": "24/7 Emergency Animal Hospital",
            "is_in_network": False,
            "is_emergency": True,
            "line_items": [
                {"description": "Emergency triage (critical)", "amount": 285.00},
                {"description": "Emergency decompression", "amount": 245.00},
                {"description": "Abdominal radiographs", "amount": 265.00},
                {"description": "Emergency bloodwork", "amount": 195.00},
                {"description": "IV fluid resuscitation", "amount": 385.00},
                {"description": "General anesthesia (high-risk)", "amount": 485.00},
                {"description": "Exploratory laparotomy", "amount": 1250.00},
                {"description": "Gastropexy", "amount": 485.00},
                {"description": "Partial splenectomy", "amount": 865.00},
                {"description": "Blood transfusion", "amount": 485.00},
                {"description": "ICU hospitalization (4 nights)", "amount": 2450.00},
                {"description": "Post-op medications", "amount": 185.00},
                {"description": "ECG monitoring", "amount": 145.00},
                {"description": "Blood gas analysis", "amount": 125.00},
                {"description": "Gastric derotation", "amount": 650.00},
            ],
        }
    else:  # medium
        claim_data = {
            "claim_id": claim_id,
            "policy_id": "POL-DEMO-001",
            "customer_id": "CUST-DEMO-001",
            "pet_id": "PET-DEMO-001",
            "pet_name": "Buddy",
            "claim_type": "Accident",
            "claim_category": "Gastrointestinal",
            "claim_amount": 3000.00,
            "diagnosis_code": "T18.9",
            "diagnosis_description": "Gastric foreign body (fabric material)",
            "treatment_notes": "Radiographs confirmed foreign body. Exploratory laparotomy performed. Foreign body removed successfully.",
            "service_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "provider_name": "City Veterinary Hospital",
            "is_in_network": True,
            "is_emergency": False,
            "line_items": [
                {"description": "Emergency examination", "amount": 145.00},
                {"description": "Abdominal radiographs", "amount": 265.00},
                {"description": "Pre-surgical bloodwork", "amount": 165.00},
                {"description": "IV fluid therapy", "amount": 195.00},
                {"description": "General anesthesia", "amount": 345.00},
                {"description": "Exploratory laparotomy", "amount": 1100.00},
                {"description": "Gastrotomy procedure", "amount": 450.00},
                {"description": "Hospitalization (2 nights)", "amount": 285.00},
                {"description": "Post-op medications", "amount": 50.00},
            ],
        }

    return await run_comparison(claim_data)


def _calculate_comparison_metrics(
    code_result: dict[str, Any],
    agent_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate comparison metrics between code and agent results.
    """
    code_time = code_result.get("total_processing_time_ms", 0)
    agent_time = agent_result.get("total_processing_time_ms", 0)

    code_decision = code_result.get("final_decision", "")
    agent_gold = agent_result.get("gold_output", {}) or {}
    agent_decision = agent_gold.get("decision", "")

    code_risk = code_result.get("risk_level", "")
    agent_risk = agent_gold.get("risk_level", "")

    # Calculate slower by percentage safely
    if code_time > 0 and agent_time > 0:
        ratio = agent_time / code_time
        if ratio >= 1000:
            agent_slower_by = f"{ratio:.0f}x"
        else:
            agent_slower_by = f"{((ratio - 1) * 100):.0f}%"
    else:
        agent_slower_by = "N/A"

    return {
        "time_comparison": {
            "code_ms": round(code_time, 2),
            "agent_ms": round(agent_time, 2),
            "difference_ms": round(agent_time - code_time, 2),
            "agent_slower_by": agent_slower_by,
        },
        "decision_match": code_decision == agent_decision,
        "risk_match": code_risk == agent_risk,
        "decisions": {
            "code": code_decision,
            "agent": agent_decision,
        },
        "risk_levels": {
            "code": code_risk,
            "agent": agent_risk,
        },
        "agent_advantages": [
            "Provides reasoning for decisions",
            "Generates business insights",
            "Adapts to edge cases",
            "Explains risk factors in detail",
        ] if agent_result.get("reasoning_log") else [],
        "code_advantages": [
            "Faster processing",
            "Deterministic results",
            "No API costs",
            "Predictable behavior",
        ],
    }


@router.get("/layers/{claim_id}")
async def get_layer_comparison(claim_id: str):
    """
    Get layer-by-layer comparison from S3 Data Lake.

    Returns the stored outputs for each layer (bronze, silver, gold)
    allowing side-by-side comparison of how the claim was processed.
    """
    s3_service = get_s3_service()

    if not s3_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="S3 Data Lake not available"
        )

    # Get pipeline status for the claim
    status = s3_service.get_claim_pipeline_status(claim_id)

    # Read outputs from each layer
    bronze_output = s3_service.read_layer_output("bronze", claim_id)
    silver_output = s3_service.read_layer_output("silver", claim_id)
    gold_output = s3_service.read_layer_output("gold", claim_id)

    return {
        "claim_id": claim_id,
        "pipeline_status": status,
        "layers": {
            "bronze": {
                "available": bronze_output is not None,
                "output": bronze_output
            },
            "silver": {
                "available": silver_output is not None,
                "output": silver_output
            },
            "gold": {
                "available": gold_output is not None,
                "output": gold_output
            }
        },
        "summary": {
            "layers_completed": sum([
                bronze_output is not None,
                silver_output is not None,
                gold_output is not None
            ]),
            "final_decision": (
                gold_output.get("decision", {}).get("final_decision")
                if gold_output else None
            ),
            "fraud_score": (
                gold_output.get("decision", {}).get("fraud_score")
                if gold_output else None
            ),
            "risk_level": (
                gold_output.get("decision", {}).get("risk_level")
                if gold_output else None
            )
        }
    }


@router.get("/datalake/status")
async def get_datalake_status():
    """
    Get the current status of the S3 Data Lake.

    Returns counts for each layer (raw, bronze, silver, gold).
    """
    s3_service = get_s3_service()

    if not s3_service.is_enabled():
        return {
            "enabled": False,
            "message": "S3 Data Lake not configured. Running in local mode."
        }

    # Get layer counts
    status = {
        "enabled": True,
        "bucket": s3_service.bucket_name,
        "layers": {}
    }

    for layer in ["raw", "bronze", "silver", "gold"]:
        try:
            from botocore.exceptions import ClientError
            response = s3_service.s3_client.list_objects_v2(
                Bucket=s3_service.bucket_name,
                Prefix=f"{layer}/",
                MaxKeys=1000
            )
            count = response.get("KeyCount", 0)
            # Don't count folder placeholders
            if count > 0:
                count = len([obj for obj in response.get("Contents", []) if not obj["Key"].endswith("/")])

            status["layers"][layer] = {
                "object_count": count,
                "status": "active" if count > 0 else "empty"
            }
        except Exception as e:
            status["layers"][layer] = {
                "object_count": 0,
                "status": "error",
                "error": str(e)
            }

    return status
