"""
Data Lake Service - Manages S3 raw claim ingestion and layer status
Similar to how PetInsure360 uploads files to ADLS, this uploads claims to S3 raw/
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .s3_service import get_s3_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ClaimSubmission(BaseModel):
    """Claim submission request"""
    claim_id: str = Field(..., description="Unique claim identifier")
    customer_id: str = Field(..., description="Customer ID")
    pet_id: str = Field(..., description="Pet ID")
    policy_id: str = Field(..., description="Policy ID")
    provider_id: str = Field(..., description="Provider ID")
    claim_amount: float = Field(..., description="Total claim amount")
    service_date: str = Field(..., description="Date of service")
    diagnosis_code: str = Field(..., description="Diagnosis code")
    diagnosis_description: Optional[str] = None
    treatment_codes: List[str] = Field(default_factory=list)
    treatment_description: Optional[str] = None
    claim_type: str = "Medical"
    is_emergency: bool = False
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class ClaimSubmissionResponse(BaseModel):
    """Response after claim submission"""
    success: bool
    claim_id: str
    s3_path: Optional[str] = None
    message: str
    submitted_at: str


class DataLakeStatus(BaseModel):
    """Data lake status response"""
    enabled: bool
    bucket: Optional[str] = None
    layers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ClaimPipelineStatus(BaseModel):
    """Pipeline status for a specific claim"""
    claim_id: str
    layers: Dict[str, Dict[str, Any]]


@router.post("/claims/submit", response_model=ClaimSubmissionResponse)
async def submit_claim(claim: ClaimSubmission):
    """
    Submit a new claim to the S3 Data Lake (raw layer).

    This is the entry point for claims - similar to how PetInsure360
    uploads source files to ADLS. The claim is stored in raw/ and can
    then be processed through the medallion pipeline.
    """
    s3_service = get_s3_service()

    # Prepare claim data for storage
    claim_data = {
        "claim_id": claim.claim_id,
        "customer_id": claim.customer_id,
        "pet_id": claim.pet_id,
        "policy_id": claim.policy_id,
        "provider_id": claim.provider_id,
        "claim_amount": claim.claim_amount,
        "service_date": claim.service_date,
        "diagnosis_code": claim.diagnosis_code,
        "diagnosis_description": claim.diagnosis_description,
        "treatment_codes": claim.treatment_codes,
        "treatment_description": claim.treatment_description,
        "claim_type": claim.claim_type,
        "is_emergency": claim.is_emergency,
        "invoice_number": claim.invoice_number,
        "notes": claim.notes,
        "submitted_at": datetime.now().isoformat(),
        "status": "submitted",
        "source": "eis-dynamics-api"
    }

    # Write to S3 raw layer
    s3_path = s3_service.write_raw_claim(claim.claim_id, claim_data)

    if s3_path:
        logger.info(f"Claim {claim.claim_id} submitted to S3: {s3_path}")
        return ClaimSubmissionResponse(
            success=True,
            claim_id=claim.claim_id,
            s3_path=s3_path,
            message="Claim submitted successfully to raw layer",
            submitted_at=claim_data["submitted_at"]
        )
    else:
        # S3 not enabled, but we still accept the claim (local mode)
        logger.info(f"Claim {claim.claim_id} submitted (local mode, S3 disabled)")
        return ClaimSubmissionResponse(
            success=True,
            claim_id=claim.claim_id,
            s3_path=None,
            message="Claim submitted (S3 disabled, running in local mode)",
            submitted_at=claim_data["submitted_at"]
        )


@router.get("/status", response_model=DataLakeStatus)
async def get_datalake_status():
    """
    Get the current status of the S3 Data Lake.

    Returns object counts for each layer (raw, bronze, silver, gold).
    """
    s3_service = get_s3_service()
    status = s3_service.get_pipeline_status()

    return DataLakeStatus(
        enabled=status.get("enabled", False),
        bucket=status.get("bucket"),
        layers=status.get("layers", {})
    )


@router.get("/claims/{claim_id}/status", response_model=ClaimPipelineStatus)
async def get_claim_status(claim_id: str):
    """
    Get the pipeline status for a specific claim.

    Shows which layers have processed the claim.
    """
    s3_service = get_s3_service()
    status = s3_service.get_claim_pipeline_status(claim_id)

    return ClaimPipelineStatus(
        claim_id=claim_id,
        layers=status.get("layers", {})
    )


@router.get("/claims/raw", response_model=List[Dict[str, Any]])
async def list_raw_claims(limit: int = 100):
    """
    List claims in the raw layer.

    Returns metadata about claims that have been submitted.
    """
    s3_service = get_s3_service()
    claims = s3_service.list_raw_claims(limit=limit)
    return claims


@router.get("/claims/{claim_id}/layers/{layer}")
async def get_layer_output(claim_id: str, layer: str):
    """
    Get the output for a specific claim at a specific layer.

    Layers: raw, bronze, silver, gold
    """
    if layer not in ["raw", "bronze", "silver", "gold"]:
        raise HTTPException(status_code=400, detail=f"Invalid layer: {layer}")

    s3_service = get_s3_service()

    if layer == "raw":
        # For raw, we need to find and read the file
        claims = s3_service.list_raw_claims(prefix=f"raw/claims/{claim_id}", limit=1)
        if not claims:
            raise HTTPException(status_code=404, detail=f"No raw data found for claim {claim_id}")
        # Return the metadata, actual content would require additional read
        return {"claim_id": claim_id, "layer": "raw", "files": claims}
    else:
        # For other layers, read directly
        if layer == "bronze":
            output = s3_service.read_bronze_output(claim_id)
        elif layer == "silver":
            output = s3_service.read_silver_output(claim_id)
        else:
            output = s3_service.read_gold_output(claim_id)

        if output is None:
            raise HTTPException(status_code=404, detail=f"No {layer} output found for claim {claim_id}")

        return output
