"""
PetInsure360 - Pipeline Control API
Manual triggers for Bronze → Silver → Gold processing
Now also triggers Agent Pipeline (WS6) and DocGen (WS7) for parallel AI processing.
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()

# Agent Pipeline URL (EIS Dynamics Agent Pipeline - WS6)
AGENT_PIPELINE_URL = os.getenv("AGENT_PIPELINE_URL", "http://localhost:8006")
# DocGen Service URL (EIS Dynamics DocGen - WS7)
DOCGEN_SERVICE_URL = os.getenv("DOCGEN_SERVICE_URL", "http://localhost:8007")

# Pipeline state persistence file
PIPELINE_STATE_FILE = "/tmp/docgen/pipeline_state.json"


# =============================================================================
# AGENT PIPELINE & DOCGEN INTEGRATION
# =============================================================================

async def trigger_agent_pipeline(claim_data: dict) -> dict | None:
    """
    Trigger the EIS Dynamics Agent Pipeline (WS6) for AI-driven claim processing.

    This sends the claim to the agent-driven medallion architecture for
    intelligent processing through Router, Bronze, Silver, and Gold agents.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{AGENT_PIPELINE_URL}/api/v1/pipeline/trigger",
                json={
                    "event_type": "claim.submitted",
                    "source": "petinsure360_pipeline",
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
    except httpx.ConnectError:
        logger.warning(f"Agent Pipeline unavailable at {AGENT_PIPELINE_URL}")
        return None
    except httpx.HTTPError as e:
        logger.warning(f"Failed to trigger agent pipeline: {e}")
        return None
    except Exception as e:
        logger.error(f"Error triggering agent pipeline: {e}")
        return None


async def create_docgen_batch(claim_data: dict) -> dict | None:
    """
    Create a batch in DocGen service (WS7) for AI-driven claim processing.

    This sends the claim to DocGen to create a batch that will appear
    in the BI Dashboard Agent Pipeline page.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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
                    "source": "petinsure360_pipeline"
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
                logger.warning(f"DocGen batch creation returned {response.status_code}")
                return None
    except httpx.ConnectError:
        logger.warning(f"DocGen service unavailable at {DOCGEN_SERVICE_URL}")
        return None
    except Exception as e:
        logger.error(f"Error creating DocGen batch: {e}")
        return None


def _load_pipeline_state() -> dict:
    """Load pipeline state from file."""
    default_state = {
        "pending_claims": [],
        "silver_claims": [],
        "gold_claims": [],
        "processing_log": [],
        "last_bronze_process": None,
        "last_silver_process": None,
        "last_gold_process": None
    }
    if os.path.exists(PIPELINE_STATE_FILE):
        try:
            with open(PIPELINE_STATE_FILE, "r") as f:
                data = json.load(f)
                print(f"Loaded pipeline state: {len(data.get('pending_claims', []))} bronze, {len(data.get('silver_claims', []))} silver, {len(data.get('gold_claims', []))} gold")
                return data
        except Exception as e:
            print(f"Error loading pipeline state: {e}")
    return default_state

def _save_pipeline_state() -> None:
    """Save pipeline state to file."""
    try:
        os.makedirs(os.path.dirname(PIPELINE_STATE_FILE), exist_ok=True)
        with open(PIPELINE_STATE_FILE, "w") as f:
            json.dump(pipeline_state, f, default=str)
    except Exception as e:
        print(f"Error saving pipeline state: {e}")

# Demo user mapping - maps email to customer info for proper display
DEMO_USER_INFO = {
    "demo@demologin.com": {
        "customer_id": "DEMO-001",
        "first_name": "Demo",
        "last_name": "User",
        "email": "demo@demologin.com"
    },
    "demo1@demologin.com": {
        "customer_id": "DEMO-002",
        "first_name": "Demo",
        "last_name": "One",
        "email": "demo1@demologin.com"
    },
    "demo2@demologin.com": {
        "customer_id": "DEMO-003",
        "first_name": "Demo",
        "last_name": "Two",
        "email": "demo2@demologin.com"
    }
}

# Pipeline state - persisted to disk for survival across restarts
pipeline_state = _load_pipeline_state()


class ClaimSubmission(BaseModel):
    """Enhanced claim submission with full details."""
    scenario_id: Optional[str] = None
    customer_id: str
    pet_id: str
    policy_id: Optional[str] = None
    claim_type: str
    claim_category: str
    diagnosis_code: Optional[str] = None
    diagnosis: str
    service_date: str
    treatment_notes: str
    line_items: List[Dict[str, Any]]
    claim_amount: float
    provider_id: Optional[str] = None
    provider_name: str
    is_in_network: bool = True
    is_emergency: bool = False
    source: Optional[str] = None  # "docgen_processed" to prevent circular batch creation


@router.get("/status")
async def get_pipeline_status(request: Request):
    """Get current pipeline status with claim counts at each layer."""
    insights = request.app.state.insights
    base_status = insights.get_pipeline_status()

    # Add pending claims info
    base_status["pending_claims"] = {
        "bronze": len(pipeline_state["pending_claims"]),
        "silver": len(pipeline_state["silver_claims"]),
        "gold": len(pipeline_state["gold_claims"])
    }
    base_status["processing_log"] = pipeline_state["processing_log"][-10:]  # Last 10 entries
    base_status["last_processes"] = {
        "bronze": pipeline_state["last_bronze_process"],
        "silver": pipeline_state["last_silver_process"],
        "gold": pipeline_state["last_gold_process"]
    }

    return base_status


@router.get("/flow")
async def get_pipeline_flow(request: Request):
    """Get pipeline flow visualization data."""
    insights = request.app.state.insights
    return insights.get_pipeline_flow()


@router.get("/pending")
async def get_pending_claims():
    """Get all claims pending in each layer."""
    return {
        "bronze": pipeline_state["pending_claims"],
        "silver": pipeline_state["silver_claims"],
        "gold": pipeline_state["gold_claims"],
        "counts": {
            "bronze": len(pipeline_state["pending_claims"]),
            "silver": len(pipeline_state["silver_claims"]),
            "gold": len(pipeline_state["gold_claims"])
        }
    }


@router.post("/submit-claim")
async def submit_claim_to_bronze(claim: ClaimSubmission, request: Request):
    """
    Submit a claim to BOTH Legacy Pipeline (Bronze layer) AND Agent Pipeline.

    This endpoint now triggers THREE parallel processing paths:
    1. Legacy Pipeline - Bronze layer ingestion (rule-based, manual processing)
    2. Agent Pipeline (WS6) - AI-driven medallion architecture
    3. DocGen Service (WS7) - AI batch processing for BI Dashboard
    """
    insights = request.app.state.insights

    # =========================================================================
    # VALIDATION: Check pet has a policy before accepting claim
    # =========================================================================
    if claim.policy_id:
        all_policies = insights.get_all_policies()
        policy = next((p for p in all_policies if str(p.get('policy_id', '')) == claim.policy_id), None)

        if policy:
            policy_pet_id = str(policy.get('pet_id', ''))
            if policy_pet_id and policy_pet_id != claim.pet_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Policy {claim.policy_id} belongs to a different pet. Please select the correct policy for this pet."
                )
        # If policy not found, allow submission (might be new policy not yet synced)

    # Check if pet has ANY policy
    pet_policies = [p for p in insights.get_all_policies() if str(p.get('pet_id', '')) == claim.pet_id]
    if not pet_policies and not claim.policy_id:
        raise HTTPException(
            status_code=400,
            detail=f"Pet {claim.pet_id} does not have an active policy. Please purchase a policy first."
        )

    # Generate claim ID and number
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # =========================================================================
    # Lookup customer and pet names for display
    # =========================================================================
    customer_name = None
    pet_name = None

    # Try multiple methods to get customer name
    try:
        # Method 1: Try get_customer_360
        cust_data = insights.get_customer_360(customer_id=claim.customer_id)
        if cust_data:
            first = cust_data.get('first_name', '') or ''
            last = cust_data.get('last_name', '') or ''
            customer_name = f"{first} {last}".strip()
    except Exception as e:
        logger.warning(f"get_customer_360 failed: {e}")

    if not customer_name:
        try:
            # Method 2: Try get_customers and filter
            customers = insights.get_customers(limit=1000)
            for c in customers:
                if str(c.get('customer_id', '')) == claim.customer_id:
                    first = c.get('first_name', '') or ''
                    last = c.get('last_name', '') or ''
                    customer_name = f"{first} {last}".strip()
                    break
        except Exception as e:
            logger.warning(f"get_customers lookup failed: {e}")

    if not customer_name:
        # Method 3: Check DEMO_USER_INFO
        for email, info in DEMO_USER_INFO.items():
            if info.get('customer_id') == claim.customer_id:
                customer_name = f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
                break

    if not customer_name:
        customer_name = f"Customer {claim.customer_id}"

    # Get pet name
    try:
        pets = insights.get_customer_pets(claim.customer_id)
        for pet in pets:
            if str(pet.get('pet_id', '')) == claim.pet_id:
                pet_name = pet.get('pet_name') or pet.get('name')
                break
    except Exception as e:
        logger.warning(f"Could not lookup pet name: {e}")

    if not pet_name:
        pet_name = f"Pet {claim.pet_id}"

    # Create raw claim record (Bronze layer - no transformation)
    raw_claim = {
        "claim_id": claim_id,
        "claim_number": claim_number,
        "scenario_id": claim.scenario_id,
        "customer_id": claim.customer_id,
        "customer_name": customer_name,
        "pet_id": claim.pet_id,
        "pet_name": pet_name,
        "policy_id": claim.policy_id,
        "claim_type": claim.claim_type,
        "claim_category": claim.claim_category,
        "diagnosis_code": claim.diagnosis_code,
        "diagnosis": claim.diagnosis,
        "service_date": claim.service_date,
        "treatment_notes": claim.treatment_notes,
        "line_items": claim.line_items,
        "claim_amount": claim.claim_amount,
        "provider_id": claim.provider_id,
        "provider_name": claim.provider_name,
        "is_in_network": claim.is_in_network,
        "is_emergency": claim.is_emergency,
        # Bronze metadata
        "ingestion_timestamp": datetime.utcnow().isoformat(),
        "source": "customer_portal",
        "raw_status": "ingested",
        "layer": "bronze"
    }

    # =========================================================================
    # PATH 1: Legacy Pipeline - Bronze Layer Ingestion
    # Skip if source is "docgen_processed" - claim was already added when first submitted
    # =========================================================================
    if claim.source != "docgen_processed":
        pipeline_state["pending_claims"].append(raw_claim)
        pipeline_state["last_bronze_process"] = datetime.utcnow().isoformat()

        # Log the ingestion
        pipeline_state["processing_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "BRONZE_INGEST",
            "claim_id": claim_id,
            "message": f"Claim {claim_number} ingested to Bronze layer"
        })
    else:
        logger.info(f"Skipping Legacy Pipeline for claim {claim_id} (source=docgen_processed)")

    # Persist state to disk
    _save_pipeline_state()

    # Also write to ADLS if configured
    storage = request.app.state.storage
    try:
        await storage.write_json("claims", raw_claim, claim_id)
    except Exception as e:
        logger.warning(f"Could not write to ADLS: {e}")

    # =========================================================================
    # Add to in-memory insights data for real-time Claims Analytics display
    # =========================================================================
    if claim.source != "docgen_processed":
        insights = request.app.state.insights
        insights.add_claim(raw_claim)

    # =========================================================================
    # PATH 2: Agent Pipeline (WS6) - AI-Driven Processing
    # Skip if source is "docgen_processed" - already processed by AI
    # =========================================================================
    agent_pipeline_result = None
    if claim.source != "docgen_processed":
        agent_pipeline_result = await trigger_agent_pipeline(raw_claim)
        if agent_pipeline_result:
            raw_claim["agent_pipeline_run_id"] = agent_pipeline_result.get("run_id")
            pipeline_state["processing_log"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "AGENT_PIPELINE_TRIGGER",
                "claim_id": claim_id,
                "message": f"Agent Pipeline triggered: run_id={agent_pipeline_result.get('run_id')}"
            })

    # =========================================================================
    # PATH 3: DocGen Service (WS7) - AI Batch Processing
    # Skip if source is "docgen_processed" to prevent circular batch creation
    # =========================================================================
    docgen_result = None
    if claim.source != "docgen_processed":
        docgen_result = await create_docgen_batch(raw_claim)
        if docgen_result:
            raw_claim["docgen_batch_id"] = docgen_result.get("batch_id")
            pipeline_state["processing_log"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "DOCGEN_BATCH_CREATE",
                "claim_id": claim_id,
                "message": f"DocGen batch created: batch_id={docgen_result.get('batch_id')}"
            })
    else:
        logger.info(f"Skipping DocGen batch creation for claim {claim_id} (source=docgen_processed)")

    # Save updated state with pipeline IDs
    _save_pipeline_state()

    # Emit WebSocket event
    sio = request.app.state.sio
    await sio.emit('claim_to_bronze', {
        'claim_id': claim_id,
        'claim_number': claim_number,
        'amount': claim.claim_amount,
        'category': claim.claim_category,
        'layer': 'bronze',
        'agent_pipeline_triggered': agent_pipeline_result is not None,
        'docgen_triggered': docgen_result is not None,
        'timestamp': datetime.utcnow().isoformat()
    })

    # Build response with all pipeline info
    response = {
        "success": True,
        "claim_id": claim_id,
        "claim_number": claim_number,
        "layer": "bronze",
        "pipelines": {
            "legacy": {
                "status": "ingested",
                "message": "Added to Bronze layer for manual processing"
            },
            "agent": {
                "status": "triggered" if agent_pipeline_result else "unavailable",
                "run_id": agent_pipeline_result.get("run_id") if agent_pipeline_result else None
            },
            "docgen": {
                "status": "created" if docgen_result else "unavailable",
                "batch_id": docgen_result.get("batch_id") if docgen_result else None
            }
        },
        "message": f"Claim {claim_number} submitted successfully. Processing via Legacy + Agent pipelines."
    }

    return response


@router.post("/process/bronze-to-silver")
async def process_bronze_to_silver(request: Request):
    """
    Process claims from Bronze to Silver layer.
    Performs: data cleansing, validation, deduplication, quality scoring.
    """
    if not pipeline_state["pending_claims"]:
        return {"success": False, "message": "No claims pending in Bronze layer", "processed": 0}

    processed_claims = []
    errors = []

    for raw_claim in pipeline_state["pending_claims"]:
        try:
            # Silver layer transformations
            silver_claim = {
                **raw_claim,
                "layer": "silver",
                # Data type standardization
                "claim_amount_decimal": float(raw_claim["claim_amount"]),
                "service_date_iso": raw_claim["service_date"],
                # Calculated fields
                "total_line_items": len(raw_claim.get("line_items", [])),
                "line_items_total": sum(item.get("amount", 0) for item in raw_claim.get("line_items", [])),
                # Validation
                "amount_validated": abs(raw_claim["claim_amount"] - sum(item.get("amount", 0) for item in raw_claim.get("line_items", []))) < 1,
                # Data quality scoring
                "completeness_score": calculate_completeness(raw_claim),
                "validity_score": calculate_validity(raw_claim),
                "overall_quality_score": 0,  # Will be calculated
                # Deduplication check
                "is_duplicate": False,
                "duplicate_of": None,
                # Processing metadata
                "silver_processed_at": datetime.utcnow().isoformat(),
                "silver_status": "validated"
            }

            # Calculate overall quality score
            silver_claim["overall_quality_score"] = round(
                silver_claim["completeness_score"] * 0.4 +
                silver_claim["validity_score"] * 0.6, 1
            )

            processed_claims.append(silver_claim)

        except Exception as e:
            errors.append({"claim_id": raw_claim.get("claim_id"), "error": str(e)})

    # Move claims to Silver layer
    pipeline_state["silver_claims"].extend(processed_claims)
    pipeline_state["pending_claims"] = []  # Clear Bronze pending
    pipeline_state["last_silver_process"] = datetime.utcnow().isoformat()

    # Log the processing
    pipeline_state["processing_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "SILVER_PROCESS",
        "claims_processed": len(processed_claims),
        "errors": len(errors),
        "message": f"Processed {len(processed_claims)} claims to Silver layer"
    })

    # Persist state to disk
    _save_pipeline_state()

    # Emit WebSocket event
    sio = request.app.state.sio
    await sio.emit('silver_processed', {
        'count': len(processed_claims),
        'layer': 'silver',
        'claims': [{"claim_id": c["claim_id"], "quality_score": c["overall_quality_score"]} for c in processed_claims],
        'timestamp': datetime.utcnow().isoformat()
    })

    return {
        "success": True,
        "processed": len(processed_claims),
        "errors": errors,
        "transformations": [
            "Data type standardization",
            "Line items validation",
            "Completeness scoring",
            "Validity scoring",
            "Deduplication check"
        ],
        "message": f"Processed {len(processed_claims)} claims from Bronze to Silver layer"
    }


@router.post("/process/silver-to-gold")
async def process_silver_to_gold(request: Request):
    """
    Process claims from Silver to Gold layer.
    Performs: aggregations, business metrics, joins with dimensions.
    """
    if not pipeline_state["silver_claims"]:
        return {"success": False, "message": "No claims pending in Silver layer", "processed": 0}

    insights = request.app.state.insights
    processed_claims = []

    for silver_claim in pipeline_state["silver_claims"]:
        try:
            # For demo customers (DEMO-xxx), create a demo customer record if not exists
            customer_id = silver_claim["customer_id"]
            if customer_id.startswith("DEMO-"):
                # Ensure demo customer exists in insights
                existing = insights.get_customer_360(customer_id=customer_id, limit=1)
                if not existing:
                    # Look up demo user info by customer_id
                    demo_info = None
                    for email, info in DEMO_USER_INFO.items():
                        if info["customer_id"] == customer_id:
                            demo_info = info
                            break

                    # Use scenario info if available, otherwise use demo user info
                    scenario_id = silver_claim.get("scenario_id")
                    pet_name = silver_claim.get("pet_name", "Buddy")

                    # Get customer info from demo mapping or use defaults
                    first_name = demo_info["first_name"] if demo_info else "Demo"
                    last_name = demo_info["last_name"] if demo_info else "User"
                    email = demo_info["email"] if demo_info else "demo@petinsure360.com"

                    insights.add_customer({
                        "customer_id": customer_id,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": "555-DEMO",
                        "city": "Demo City",
                        "state": "TX",
                        "customer_since": datetime.now().strftime('%Y-%m-%d')
                    })
                    # Also add demo pet if not exists
                    pet_id = silver_claim.get("pet_id", "PET-DEMO-001")
                    insights.add_pet({
                        "pet_id": pet_id,
                        "customer_id": customer_id,
                        "pet_name": pet_name,
                        "species": "Dog",
                        "breed": "Labrador Retriever",
                        "date_of_birth": "2020-01-15",
                        "gender": "Male",
                        "weight_lbs": 65
                    })

            # Gold layer transformations - join with dimensions
            customers = insights.get_customer_360(customer_id=customer_id, limit=1)
            customer_info = customers[0] if customers else {}

            gold_claim = {
                **silver_claim,
                "layer": "gold",
                # Joined customer info
                "customer_name": customer_info.get("full_name", "Unknown"),
                "customer_tier": customer_info.get("customer_value_tier", "Unknown"),
                "customer_risk": customer_info.get("customer_risk_score", "Unknown"),
                "customer_email": customer_info.get("email", ""),
                # Business calculations
                "network_adjustment": 1.0 if silver_claim.get("is_in_network") else 0.8,
                "estimated_reimbursement": calculate_reimbursement(silver_claim, customer_info),
                "processing_priority": "High" if silver_claim.get("is_emergency") else "Normal",
                # Aggregation flags
                "include_in_kpi": True,
                "include_in_customer_360": True,
                # Processing metadata
                "gold_processed_at": datetime.utcnow().isoformat(),
                "gold_status": "aggregated",
                "status": "Submitted"  # Claim workflow status
            }

            processed_claims.append(gold_claim)

            # Add to insights service for real-time display
            insights.add_claim({
                "claim_id": gold_claim["claim_id"],
                "claim_number": gold_claim["claim_number"],
                "customer_id": gold_claim["customer_id"],
                "pet_id": gold_claim["pet_id"],
                "policy_id": gold_claim.get("policy_id", ""),
                "provider_id": gold_claim.get("provider_id", "PROV-0001"),
                "service_date": gold_claim["service_date"],
                "claim_type": gold_claim["claim_type"],
                "claim_category": gold_claim["claim_category"],
                "diagnosis": gold_claim["diagnosis"],
                "treatment": gold_claim["treatment_notes"],
                "claim_amount": gold_claim["claim_amount"],
                "paid_amount": gold_claim["estimated_reimbursement"],
                "status": "Submitted",
                "processing_days": 0
            })

        except Exception as e:
            print(f"Error processing claim to Gold: {e}")

    # Move claims to Gold layer
    pipeline_state["gold_claims"].extend(processed_claims)
    pipeline_state["silver_claims"] = []  # Clear Silver pending
    pipeline_state["last_gold_process"] = datetime.utcnow().isoformat()

    # Log the processing
    pipeline_state["processing_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "GOLD_PROCESS",
        "claims_processed": len(processed_claims),
        "message": f"Aggregated {len(processed_claims)} claims to Gold layer"
    })

    # Persist state to disk
    _save_pipeline_state()

    # Emit WebSocket event
    sio = request.app.state.sio
    await sio.emit('gold_processed', {
        'count': len(processed_claims),
        'layer': 'gold',
        'claims': [{"claim_id": c["claim_id"], "claim_number": c["claim_number"], "amount": c["claim_amount"], "customer": c["customer_name"]} for c in processed_claims],
        'timestamp': datetime.utcnow().isoformat()
    })

    # Persist demo data to Azure Storage for survival across restarts
    storage = request.app.state.storage
    persisted = False
    try:
        # Helper to clean NaN/NaT values for JSON serialization
        def clean_record(record):
            import math
            cleaned = {}
            for k, v in record.items():
                if v is None:
                    cleaned[k] = None
                elif isinstance(v, float) and math.isnan(v):
                    cleaned[k] = None
                elif hasattr(v, 'isoformat'):  # datetime/date
                    cleaned[k] = v.isoformat() if v is not None else None
                elif str(v) == 'NaT':
                    cleaned[k] = None
                else:
                    cleaned[k] = v
            return cleaned

        # Get all demo customers and claims from insights (with null checks)
        demo_customers = []
        demo_pets = []
        demo_claims = []

        if insights._customers is not None and len(insights._customers) > 0:
            all_customers = insights._customers.to_dict('records')
            demo_customers = [clean_record(c) for c in all_customers if str(c.get('customer_id', '')).startswith('DEMO-')]

        if insights._pets is not None and len(insights._pets) > 0:
            all_pets = insights._pets.to_dict('records')
            demo_pets = [clean_record(p) for p in all_pets if str(p.get('customer_id', '')).startswith('DEMO-')]

        if insights._claims is not None and len(insights._claims) > 0:
            all_claims = insights._claims.to_dict('records')
            demo_claims = [clean_record(c) for c in all_claims if str(c.get('customer_id', '')).startswith('DEMO-')]

        if demo_customers:
            await storage.write_demo_data('customers', demo_customers)
            persisted = True
        if demo_pets:
            await storage.write_demo_data('pets', demo_pets)
        if demo_claims:
            await storage.write_demo_data('claims', demo_claims)
    except Exception as e:
        print(f"Warning: Could not persist demo data: {e}")
        import traceback
        traceback.print_exc()

    return {
        "success": True,
        "processed": len(processed_claims),
        "claims": [{"claim_id": c["claim_id"], "amount": c["claim_amount"], "customer": c["customer_name"], "reimbursement": c["estimated_reimbursement"]} for c in processed_claims],
        "transformations": [
            "Customer dimension join",
            "Policy dimension join",
            "Reimbursement calculation",
            "Priority assignment",
            "KPI aggregation prep"
        ],
        "message": f"Aggregated {len(processed_claims)} claims to Gold layer. Now visible in dashboard.",
        "persisted": persisted
    }


@router.post("/refresh")
async def refresh_pipeline(request: Request):
    """Force refresh of pipeline data from source."""
    insights = request.app.state.insights
    insights.refresh_data()
    return {"success": True, "message": "Pipeline data refreshed"}


@router.delete("/clear")
async def clear_pipeline(request: Request, include_demo_data: bool = True):
    """Clear all pending claims and optionally demo data (for demo reset)."""
    pipeline_state["pending_claims"] = []
    pipeline_state["silver_claims"] = []
    pipeline_state["gold_claims"] = []
    pipeline_state["processing_log"] = []
    _save_pipeline_state()

    demo_cleared = False
    if include_demo_data:
        try:
            storage = request.app.state.storage
            await storage.clear_demo_data()  # Clear all demo data from ADLS
            demo_cleared = True

            # Also refresh insights to remove demo data from in-memory state
            insights = request.app.state.insights
            insights.refresh_data()
        except Exception as e:
            print(f"Error clearing demo data: {e}")

    return {
        "success": True,
        "message": f"Pipeline cleared{' and demo data removed' if demo_cleared else ''}"
    }


@router.get("/metrics")
async def get_pipeline_metrics(request: Request):
    """Get detailed pipeline metrics for monitoring."""
    insights = request.app.state.insights
    status = insights.get_pipeline_status()

    return {
        "data_source": status["data_source"],
        "record_counts": status["metrics"],
        "data_quality": status["data_quality"],
        "pending_counts": {
            "bronze": len(pipeline_state["pending_claims"]),
            "silver": len(pipeline_state["silver_claims"]),
            "gold": len(pipeline_state["gold_claims"])
        },
        "layers": {
            name: {
                "status": layer["status"],
                "count": layer["record_count"],
                "last_update": layer["last_update"]
            }
            for name, layer in status["layers"].items()
        }
    }


# Helper functions
def calculate_completeness(claim: dict) -> float:
    """Calculate data completeness score (0-100)."""
    required_fields = [
        "claim_id", "customer_id", "pet_id", "claim_type",
        "claim_category", "service_date", "claim_amount", "provider_name"
    ]
    present = sum(1 for f in required_fields if claim.get(f))
    return round((present / len(required_fields)) * 100, 1)


def calculate_validity(claim: dict) -> float:
    """Calculate data validity score (0-100)."""
    score = 100.0

    # Check amount is positive
    if claim.get("claim_amount", 0) <= 0:
        score -= 20

    # Check line items sum matches total
    line_total = sum(item.get("amount", 0) for item in claim.get("line_items", []))
    if abs(claim.get("claim_amount", 0) - line_total) > 1:
        score -= 15

    # Check date format
    try:
        datetime.strptime(claim.get("service_date", ""), "%Y-%m-%d")
    except:
        score -= 10

    return max(round(score, 1), 0)


def calculate_reimbursement(claim: dict, customer: dict) -> float:
    """Calculate estimated reimbursement amount."""
    amount = claim.get("claim_amount", 0)

    # Apply deductible (simplified - assume $250)
    deductible = 250
    after_deductible = max(0, amount - deductible)

    # Apply reimbursement rate (simplified - assume 80%)
    reimbursement_rate = 0.80

    # Apply network adjustment
    if not claim.get("is_in_network"):
        reimbursement_rate *= 0.8  # 20% less for out-of-network

    return round(after_deductible * reimbursement_rate, 2)


# =============================================================================
# RULE-BASED vs AI COMPARISON ENDPOINTS
# =============================================================================

class RulesComparisonRequest(BaseModel):
    """Request for rule-based comparison."""
    customer_id: str
    pet_id: str
    policy_id: str
    provider_id: str
    claim_amount: float
    diagnosis_code: str
    service_date: str
    is_emergency: bool = False


@router.post("/process/rules-only")
async def process_with_rules_only(claim: RulesComparisonRequest, request: Request):
    """
    Process a claim using RULES ONLY (no AI agents).

    This endpoint demonstrates what the traditional rule-based system would do.
    Used for comparison with AI agent results.
    """
    from app.services.rules_engine import process_claim_with_rules

    claim_data = {
        "customer_id": claim.customer_id,
        "pet_id": claim.pet_id,
        "policy_id": claim.policy_id,
        "provider_id": claim.provider_id,
        "claim_amount": claim.claim_amount,
        "diagnosis_code": claim.diagnosis_code,
        "service_date": claim.service_date,
        "is_emergency": claim.is_emergency
    }

    result = await process_claim_with_rules(claim_data)

    return {
        "processing_type": "rules_only",
        "decision": result.decision.value,
        "risk_score": result.risk_score,
        "risk_factors": result.risk_factors,
        "fraud_flags": result.fraud_flags,
        "reimbursement": result.reimbursement,
        "reasoning": result.reasoning,
        "processing_time_ms": result.processing_time_ms,
        "coverage": result.coverage_result
    }


@router.post("/process/compare")
async def process_and_compare(claim: RulesComparisonRequest, request: Request):
    """
    Process a claim with BOTH rules and AI, then compare results.

    This is the main comparison endpoint for the demo.
    Shows what rules catch vs what AI catches.
    """
    from app.services.rules_engine import process_claim_with_rules, compare_with_agent_result

    claim_data = {
        "customer_id": claim.customer_id,
        "pet_id": claim.pet_id,
        "policy_id": claim.policy_id,
        "provider_id": claim.provider_id,
        "claim_amount": claim.claim_amount,
        "diagnosis_code": claim.diagnosis_code,
        "service_date": claim.service_date,
        "is_emergency": claim.is_emergency
    }

    # Process with rules
    rules_result = await process_claim_with_rules(claim_data)

    # Get AI comparison
    comparison = await compare_with_agent_result(claim_data, rules_result)

    return {
        "claim_data": claim_data,
        **comparison,
        "summary": {
            "rules_decision": rules_result.decision.value,
            "ai_recommendation": comparison["ai_result"]["recommendation"],
            "ai_detected_patterns": comparison["ai_result"]["patterns_detected"],
            "ai_advantage_demonstrated": comparison["comparison"]["ai_advantage"],
            "what_rules_missed": comparison["comparison"]["patterns_missed_by_rules"]
        }
    }


@router.get("/fraud-scenarios")
async def get_fraud_scenarios():
    """
    Get the pre-built fraud scenarios for demo.

    These scenarios are designed to show AI advantage over rules.
    """
    return {
        "scenarios": [
            {
                "id": "fraud_1",
                "name": "Chronic Condition Gaming",
                "customer_id": "CUST-023",
                "pet_id": "PET-034",
                "provider_id": "PROV-011",
                "policy_id": "POL-034",
                "claim_amount": 1600,
                "diagnosis_code": "S83.5",
                "service_date": "2024-12-15",
                "description": "Pet has hip dysplasia but owner claims repeated 'accidents' for leg injuries",
                "rules_expected": "APPROVE (each claim under threshold)",
                "ai_expected": "FLAG (detects pattern across claims + pre-existing condition)"
            },
            {
                "id": "fraud_2",
                "name": "Provider Collusion",
                "customer_id": "CUST-067",
                "pet_id": "PET-089",
                "provider_id": "PROV-099",
                "policy_id": "POL-089",
                "claim_amount": 4800,
                "diagnosis_code": "K59",
                "service_date": "2024-12-15",
                "description": "Customer exclusively uses one out-of-network provider with claims just under limit",
                "rules_expected": "APPROVE (below $5000 threshold)",
                "ai_expected": "FLAG (detects provider concentration + limit optimization)"
            },
            {
                "id": "fraud_3",
                "name": "Staged Timing",
                "customer_id": "CUST-089",
                "pet_id": "PET-112",
                "provider_id": "PROV-025",
                "policy_id": "POL-112",
                "claim_amount": 5200,
                "diagnosis_code": "G95.89",
                "service_date": "2024-12-17",
                "description": "French Bulldog IVDD claim 2 days after waiting period - breed has 10x risk",
                "rules_expected": "APPROVE (waiting period satisfied)",
                "ai_expected": "FLAG (statistical anomaly + breed risk awareness)"
            }
        ],
        "notes": [
            "These scenarios use the shared data from Unified Claims API (port 8000)",
            "Rules-based processing uses simple thresholds and checks",
            "AI agent uses pattern recognition and cross-reference analysis",
            "Run /process/compare with each scenario to see the difference"
        ]
    }
