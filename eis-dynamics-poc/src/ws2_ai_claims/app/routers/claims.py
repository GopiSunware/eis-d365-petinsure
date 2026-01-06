"""Claims API endpoints."""
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from eis_common.models import Claim, ClaimStatus, ClaimSeverity

from ..services.fnol_processor import FNOLProcessor
from ..services.fraud_detector import FraudDetector

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instances
fnol_processor = FNOLProcessor()
fraud_detector = FraudDetector()


# Request/Response Models
class FNOLRequest(BaseModel):
    """First Notice of Loss submission."""
    description: str = Field(..., min_length=10, description="Detailed description of the incident")
    date_of_loss: date = Field(..., description="Date when the incident occurred")
    policy_number: str = Field(..., description="Policy number")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email")


class Party(BaseModel):
    """Party involved in the claim."""
    name: str
    role: str  # claimant, witness, third_party
    contact: Optional[str] = None


class ClaimExtraction(BaseModel):
    """AI-extracted claim data."""
    incident_type: str
    incident_date: Optional[str] = None
    incident_location: Optional[str] = None
    damage_description: str
    estimated_amount: Optional[Decimal] = None
    parties_involved: List[Party] = Field(default_factory=list)
    severity: ClaimSeverity
    confidence_score: float = Field(..., ge=0, le=1)


class FraudIndicator(BaseModel):
    """Fraud indicator from AI analysis."""
    indicator: str
    confidence: float = Field(..., ge=0, le=1)
    description: str


class FraudAnalysis(BaseModel):
    """Fraud analysis result."""
    fraud_score: float = Field(..., ge=0, le=1)
    risk_level: str  # low, medium, high
    indicators: List[FraudIndicator] = Field(default_factory=list)
    recommendation: str


class TriageResult(BaseModel):
    """Claim triage recommendation."""
    severity: ClaimSeverity
    priority: int = Field(..., ge=1, le=5)
    recommended_handler: str
    estimated_reserve: Decimal
    next_steps: List[str]
    auto_approve_eligible: bool


class FNOLResponse(BaseModel):
    """FNOL submission response."""
    claim_number: str
    status: ClaimStatus
    extraction: ClaimExtraction
    fraud_analysis: FraudAnalysis
    triage: TriageResult
    message: str


class ClaimResponse(BaseModel):
    """Claim detail response."""
    claim_number: str
    policy_id: str
    date_of_loss: date
    date_reported: datetime
    status: ClaimStatus
    loss_description: str
    severity: Optional[ClaimSeverity]
    reserve_amount: Decimal
    paid_amount: Decimal
    fraud_score: float
    ai_recommendation: Optional[str]


# In-memory storage for POC
claims_db: dict = {}


@router.post("/fnol", response_model=FNOLResponse)
async def submit_fnol(request: FNOLRequest):
    """
    Submit First Notice of Loss (FNOL).

    AI processes the claim description to:
    - Extract structured incident details
    - Assess severity and priority
    - Detect potential fraud indicators
    - Recommend triage actions
    """
    logger.info(f"Received FNOL for policy {request.policy_number}")

    try:
        # Generate claim number
        claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        # Process FNOL with AI
        extraction = await fnol_processor.extract_claim_data(request.description)

        # Run fraud detection
        fraud_analysis = await fraud_detector.analyze(
            description=request.description,
            extraction=extraction,
        )

        # Determine triage
        triage = await fnol_processor.triage_claim(
            extraction=extraction,
            fraud_score=fraud_analysis["fraud_score"],
        )

        # Create claim record
        claim = Claim(
            claim_number=claim_number,
            policy_id=request.policy_number,  # In real impl, lookup policy ID
            date_of_loss=request.date_of_loss,
            date_reported=datetime.utcnow(),
            status=ClaimStatus.FNOL_RECEIVED,
            loss_description=request.description,
            severity=ClaimSeverity(extraction["severity"]),
            fraud_score=fraud_analysis["fraud_score"],
            ai_recommendation=triage["recommendation"],
            reserve_amount=Decimal(str(triage["estimated_reserve"])),
        )

        # Store in memory (POC)
        claims_db[claim_number] = claim

        logger.info(f"Created claim {claim_number} with severity {extraction['severity']}")

        return FNOLResponse(
            claim_number=claim_number,
            status=ClaimStatus.FNOL_RECEIVED,
            extraction=ClaimExtraction(
                incident_type=extraction["incident_type"],
                incident_date=extraction.get("incident_date"),
                incident_location=extraction.get("incident_location"),
                damage_description=extraction["damage_description"],
                estimated_amount=Decimal(str(extraction["estimated_amount"])) if extraction.get("estimated_amount") else None,
                parties_involved=[Party(**p) for p in extraction.get("parties_involved", [])],
                severity=ClaimSeverity(extraction["severity"]),
                confidence_score=extraction["confidence_score"],
            ),
            fraud_analysis=FraudAnalysis(
                fraud_score=fraud_analysis["fraud_score"],
                risk_level=fraud_analysis["risk_level"],
                indicators=[FraudIndicator(**i) for i in fraud_analysis.get("indicators", [])],
                recommendation=fraud_analysis["recommendation"],
            ),
            triage=TriageResult(
                severity=ClaimSeverity(extraction["severity"]),
                priority=triage["priority"],
                recommended_handler=triage["recommended_handler"],
                estimated_reserve=Decimal(str(triage["estimated_reserve"])),
                next_steps=triage["next_steps"],
                auto_approve_eligible=triage["auto_approve_eligible"],
            ),
            message="FNOL submitted successfully. AI analysis complete.",
        )

    except Exception as e:
        logger.error(f"Error processing FNOL: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing FNOL: {str(e)}")


@router.get("/{claim_number}", response_model=ClaimResponse)
async def get_claim(claim_number: str):
    """Get claim details by claim number."""
    claim = claims_db.get(claim_number)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return ClaimResponse(
        claim_number=claim.claim_number,
        policy_id=claim.policy_id,
        date_of_loss=claim.date_of_loss,
        date_reported=claim.date_reported,
        status=claim.status,
        loss_description=claim.loss_description,
        severity=claim.severity,
        reserve_amount=claim.reserve_amount,
        paid_amount=claim.paid_amount,
        fraud_score=claim.fraud_score,
        ai_recommendation=claim.ai_recommendation,
    )


@router.get("/{claim_number}/triage", response_model=TriageResult)
async def get_triage(claim_number: str):
    """Get AI triage recommendation for a claim."""
    claim = claims_db.get(claim_number)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Re-run triage (could be cached in real impl)
    extraction = await fnol_processor.extract_claim_data(claim.loss_description)
    triage = await fnol_processor.triage_claim(
        extraction=extraction,
        fraud_score=claim.fraud_score,
    )

    return TriageResult(
        severity=ClaimSeverity(extraction["severity"]),
        priority=triage["priority"],
        recommended_handler=triage["recommended_handler"],
        estimated_reserve=Decimal(str(triage["estimated_reserve"])),
        next_steps=triage["next_steps"],
        auto_approve_eligible=triage["auto_approve_eligible"],
    )


@router.post("/{claim_number}/fraud", response_model=FraudAnalysis)
async def analyze_fraud(claim_number: str):
    """Run fraud analysis on a claim."""
    claim = claims_db.get(claim_number)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    extraction = await fnol_processor.extract_claim_data(claim.loss_description)
    fraud_analysis = await fraud_detector.analyze(
        description=claim.loss_description,
        extraction=extraction,
    )

    # Update claim
    claim.fraud_score = fraud_analysis["fraud_score"]
    claims_db[claim_number] = claim

    return FraudAnalysis(
        fraud_score=fraud_analysis["fraud_score"],
        risk_level=fraud_analysis["risk_level"],
        indicators=[FraudIndicator(**i) for i in fraud_analysis.get("indicators", [])],
        recommendation=fraud_analysis["recommendation"],
    )


@router.post("/{claim_number}/documents")
async def upload_document(
    claim_number: str,
    file: UploadFile = File(...),
    document_type: str = "other",
):
    """Upload a document to a claim."""
    claim = claims_db.get(claim_number)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # In real impl: upload to Azure Blob Storage, run Document Intelligence
    logger.info(f"Received document {file.filename} for claim {claim_number}")

    return {
        "message": "Document uploaded successfully",
        "claim_number": claim_number,
        "filename": file.filename,
        "document_type": document_type,
    }


@router.get("/", response_model=List[ClaimResponse])
async def list_claims(
    status: Optional[ClaimStatus] = None,
    limit: int = 50,
):
    """List claims with optional filtering."""
    claims = list(claims_db.values())

    if status:
        claims = [c for c in claims if c.status == status]

    claims = claims[:limit]

    return [
        ClaimResponse(
            claim_number=c.claim_number,
            policy_id=c.policy_id,
            date_of_loss=c.date_of_loss,
            date_reported=c.date_reported,
            status=c.status,
            loss_description=c.loss_description,
            severity=c.severity,
            reserve_amount=c.reserve_amount,
            paid_amount=c.paid_amount,
            fraud_score=c.fraud_score,
            ai_recommendation=c.ai_recommendation,
        )
        for c in claims
    ]
