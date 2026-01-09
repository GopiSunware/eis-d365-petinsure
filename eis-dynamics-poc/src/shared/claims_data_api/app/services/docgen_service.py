"""
DocGenService - Document generation and batch management.
Provides batch management, document upload, and processing status endpoints.
Simplified port from ws7_docgen for unified API access.
"""

import json
import logging
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from enum import Enum

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== ENUMS ====================

class ProcessingStatus(str, Enum):
    UPLOADING = "uploading"
    PENDING = "pending"
    EXTRACTING = "extracting"
    MAPPING = "mapping"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    VET_INVOICE = "vet_invoice"
    MEDICAL_RECORD = "medical_record"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    RECEIPT = "receipt"
    OTHER = "other"


# ==================== MODELS ====================

class UploadedDocument(BaseModel):
    """Represents an uploaded document."""
    id: UUID = Field(default_factory=uuid4)
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    file_hash: str
    document_type: Optional[DocumentType] = None
    local_path: Optional[str] = None
    blob_url: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class AgentStep(BaseModel):
    """Represents a step in agent processing."""
    step_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    step_type: str
    status: str = "pending"  # pending, running, completed, failed
    message: str
    details: Optional[str] = None
    result: Optional[str] = None  # pass, fail, warning, skip
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ValidationIssue(BaseModel):
    """Represents a validation issue."""
    severity: str  # critical, warning, info
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None
    source: Optional[str] = None


class BillingCalculation(BaseModel):
    """Represents billing calculation results."""
    claim_amount: float = 0
    deductible_applied: float = 0
    covered_amount: float = 0
    reimbursement_rate: float = 0.8
    final_payout: float = 0
    customer_responsibility: float = 0


class ProcessedBatch(BaseModel):
    """Represents a batch of documents being processed."""
    batch_id: UUID = Field(default_factory=uuid4)
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None
    customer_id: Optional[str] = None
    pet_id: Optional[str] = None
    pet_name: Optional[str] = None
    policy_id: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress: float = 0.0
    current_stage: Optional[str] = None
    documents: List[UploadedDocument] = []
    agent_steps: List[AgentStep] = []
    extractions: Dict[str, Any] = {}
    mapped_claim: Optional[Dict[str, Any]] = None
    validation_issues: List[ValidationIssue] = []
    fraud_indicators: List[Dict[str, Any]] = []
    fraud_score: float = 0.0
    billing: Optional[BillingCalculation] = None
    ai_decision: Optional[str] = None
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[float] = None
    claim_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_stage: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class UploadResponse(BaseModel):
    """Response for document upload."""
    batch_id: UUID
    documents_count: int
    documents: List[UploadedDocument]
    status: ProcessingStatus
    message: str


class ProcessingStatusResponse(BaseModel):
    """Response for processing status."""
    batch_id: UUID
    status: ProcessingStatus
    progress: float
    current_stage: Optional[str]
    documents_processed: int
    documents_total: int
    estimated_remaining_seconds: Optional[int] = None
    error: Optional[str] = None


# ==================== STORAGE ====================

# Get project-relative data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
BATCHES_FILE = DATA_DIR / "batches" / "batches.json"
UPLOADS_DIR = DATA_DIR / "uploads"

# In-memory batch storage
_batches: Dict[str, ProcessedBatch] = {}


def _ensure_directories():
    """Ensure data directories exist."""
    (DATA_DIR / "batches").mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _load_batches() -> Dict[str, ProcessedBatch]:
    """Load batches from file storage."""
    _ensure_directories()
    if BATCHES_FILE.exists():
        try:
            with open(BATCHES_FILE, "r") as f:
                data = json.load(f)
                batches = {}
                for batch_id, batch_data in data.items():
                    try:
                        batches[batch_id] = ProcessedBatch.model_validate(batch_data)
                    except Exception as e:
                        logger.warning(f"Failed to load batch {batch_id}: {e}")
                logger.info(f"Loaded {len(batches)} batches from storage")
                return batches
        except Exception as e:
            logger.error(f"Failed to load batches file: {e}")
    return {}


def _save_batches() -> None:
    """Save batches to file storage."""
    _ensure_directories()
    try:
        data = {}
        for batch_id, batch in _batches.items():
            try:
                data[batch_id] = json.loads(batch.model_dump_json())
            except Exception as e:
                logger.warning(f"Failed to serialize batch {batch_id}: {e}")

        with open(BATCHES_FILE, "w") as f:
            json.dump(data, f, default=str)
    except Exception as e:
        logger.error(f"Failed to save batches: {e}")


def get_batch(batch_id: str) -> Optional[ProcessedBatch]:
    """Get batch by ID."""
    return _batches.get(batch_id)


def save_batch(batch: ProcessedBatch) -> None:
    """Save batch to storage."""
    _batches[str(batch.batch_id)] = batch
    _save_batches()


def list_batches() -> List[ProcessedBatch]:
    """List all batches."""
    return list(_batches.values())


# Load batches on module initialization
_batches = _load_batches()


# ==================== SETTINGS ====================

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".heic", ".doc", ".docx", ".zip"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/heic",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "application/x-zip-compressed",
}
MAX_FILE_SIZE_MB = 50


# ==================== ENDPOINTS ====================

@router.get("/batches")
async def list_all_batches(
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """List all batches with pagination."""
    all_batches = list_batches()
    total = len(all_batches)

    # Sort by created_at descending
    sorted_batches = sorted(all_batches, key=lambda b: b.created_at, reverse=True)

    # Paginate
    paginated = sorted_batches[offset:offset + limit]

    return {
        "batches": [
            {
                "batch_id": str(b.batch_id),
                "claim_number": b.claim_number,
                "documents_count": len(b.documents),
                "status": b.status.value,
                "created_at": b.created_at.isoformat(),
                "error": b.error,
                "error_stage": b.error_stage,
                "agent_steps": [
                    {
                        "step_id": s.step_id,
                        "step_type": s.step_type,
                        "status": s.status,
                        "message": s.message,
                        "details": s.details,
                        "result": s.result,
                    }
                    for s in b.agent_steps
                ] if b.agent_steps else [],
                "ai_decision": b.ai_decision,
                "ai_reasoning": b.ai_reasoning,
                "ai_confidence": b.ai_confidence,
                "claim_amount": b.claim_data.get("claim_amount") if b.claim_data else None,
                "claim_type": b.claim_data.get("claim_type") if b.claim_data else None,
            }
            for b in paginated
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/batch/{batch_id}")
async def get_batch_details(batch_id: str) -> ProcessedBatch:
    """Get detailed information about a batch."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )
    return batch


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Documents to upload"),
    claim_number: Optional[str] = Form(None, description="Existing claim number"),
    policy_number: Optional[str] = Form(None, description="Policy number for new claims"),
    document_type: Optional[str] = Form(None, description="Document type hint"),
    customer_id: Optional[str] = Form(None, description="Customer ID"),
    pet_id: Optional[str] = Form(None, description="Pet ID"),
    pet_name: Optional[str] = Form(None, description="Pet name"),
    policy_id: Optional[str] = Form(None, description="Policy ID"),
):
    """
    Upload one or more documents.

    - Supports PDF, JPG, PNG, HEIC, DOC, DOCX files
    - Returns a batch ID for tracking processing status
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    _ensure_directories()

    # Create new batch
    batch = ProcessedBatch(
        batch_id=uuid4(),
        claim_number=claim_number,
        policy_number=policy_number,
        customer_id=customer_id,
        pet_id=pet_id,
        pet_name=pet_name,
        policy_id=policy_id,
        status=ProcessingStatus.UPLOADING,
    )

    uploaded_docs = []
    errors = []

    for file in files:
        try:
            # Validate file
            if not file.filename:
                errors.append("No filename provided")
                continue

            extension = Path(file.filename).suffix.lower()
            if extension not in ALLOWED_EXTENSIONS:
                errors.append(f"{file.filename}: Unsupported file type: {extension}")
                continue

            # Read file content
            content = await file.read()

            # Check file size
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                errors.append(f"{file.filename}: File exceeds maximum size of {MAX_FILE_SIZE_MB}MB")
                continue

            # Calculate hash
            file_hash = hashlib.sha256(content).hexdigest()

            # Save file locally
            batch_dir = UPLOADS_DIR / str(batch.batch_id)
            batch_dir.mkdir(parents=True, exist_ok=True)
            file_path = batch_dir / file.filename

            with open(file_path, "wb") as f:
                f.write(content)

            # Determine document type
            doc_type = None
            if document_type:
                try:
                    doc_type = DocumentType(document_type)
                except ValueError:
                    pass

            # Create document record
            doc = UploadedDocument(
                filename=f"{batch.batch_id}/{file.filename}",
                original_filename=file.filename,
                content_type=file.content_type or "application/octet-stream",
                file_size=len(content),
                file_hash=file_hash,
                document_type=doc_type,
                local_path=str(file_path),
            )

            uploaded_docs.append(doc)

        except Exception as e:
            logger.error(f"Error uploading {file.filename}: {e}")
            errors.append(f"{file.filename}: Upload failed - {str(e)}")

    if not uploaded_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No files were uploaded successfully. Errors: {'; '.join(errors)}",
        )

    # Update batch
    batch.documents = uploaded_docs
    batch.status = ProcessingStatus.PENDING

    # Save batch
    save_batch(batch)

    message = f"Successfully uploaded {len(uploaded_docs)} document(s)"
    if errors:
        message += f". Warnings: {'; '.join(errors)}"

    logger.info(f"Batch {batch.batch_id}: {message}")

    return UploadResponse(
        batch_id=batch.batch_id,
        documents_count=len(uploaded_docs),
        documents=uploaded_docs,
        status=batch.status,
        message=message,
    )


@router.post("/batch/from-claim")
async def create_batch_from_claim(claim_data: dict):
    """
    Create a batch from claim data (without document uploads).

    This endpoint is called when a claim is submitted,
    allowing batch tracking for AI processing.
    """
    # Create batch ID
    batch_id = uuid4()

    # Create batch
    batch = ProcessedBatch(
        batch_id=batch_id,
        claim_number=claim_data.get("claim_number"),
        policy_number=claim_data.get("policy_id"),
        customer_id=claim_data.get("customer_id"),
        pet_id=claim_data.get("pet_id"),
        pet_name=claim_data.get("pet_name"),
        status=ProcessingStatus.PENDING,
        claim_data=claim_data,
    )

    # Save batch
    save_batch(batch)

    logger.info(f"Created batch {batch_id} from claim {claim_data.get('claim_id')}")

    return {
        "batch_id": str(batch_id),
        "claim_id": claim_data.get("claim_id"),
        "claim_number": claim_data.get("claim_number"),
        "status": batch.status.value,
        "message": "Batch created from claim data. Ready for processing."
    }


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

    # Start processing (simplified - marks as processing)
    batch.status = ProcessingStatus.EXTRACTING
    batch.started_at = datetime.utcnow()
    batch.current_stage = "extraction"
    batch.progress = 10

    # Initialize agent steps for tracking
    batch.agent_steps = [
        AgentStep(step_type="check_policy", message="Verify policy is valid and active", status="pending"),
        AgentStep(step_type="check_duplicate", message="Check for duplicate submissions", status="pending"),
        AgentStep(step_type="extract_data", message="Extract document data", status="pending"),
        AgentStep(step_type="validate_fields", message="Validate required fields", status="pending"),
        AgentStep(step_type="calculate_billing", message="Calculate reimbursement", status="pending"),
        AgentStep(step_type="submit", message="Submit for processing", status="pending"),
    ]

    save_batch(batch)

    if sync:
        # Simple synchronous completion
        await _simple_process_batch(batch_id)
        batch = get_batch(batch_id)
    else:
        # Background processing
        background_tasks.add_task(_simple_process_batch, batch_id)

    return ProcessingStatusResponse(
        batch_id=batch.batch_id,
        status=batch.status,
        progress=batch.progress,
        current_stage=batch.current_stage or "starting",
        documents_processed=len(batch.extractions),
        documents_total=len(batch.documents),
    )


async def _simple_process_batch(batch_id: str) -> None:
    """
    Simple batch processing simulation.
    In production, this would connect to AI agents for full processing.
    """
    import asyncio

    batch = get_batch(batch_id)
    if not batch:
        return

    try:
        # Step 1: Check policy
        _update_step(batch, "check_policy", "running")
        save_batch(batch)
        await asyncio.sleep(0.5)
        _update_step(batch, "check_policy", "completed", result="pass", details="Policy verified")
        batch.progress = 20
        save_batch(batch)

        # Step 2: Check duplicate
        _update_step(batch, "check_duplicate", "running")
        save_batch(batch)
        await asyncio.sleep(0.5)
        _update_step(batch, "check_duplicate", "completed", result="pass", details="No duplicates found")
        batch.progress = 35
        save_batch(batch)

        # Step 3: Extract data
        _update_step(batch, "extract_data", "running")
        batch.status = ProcessingStatus.EXTRACTING
        batch.current_stage = "extraction"
        save_batch(batch)
        await asyncio.sleep(1)

        # Mock extracted data
        batch.mapped_claim = {
            "provider_name": "Sample Veterinary Clinic",
            "service_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total_amount": 250.00,
            "diagnosis": "General wellness check",
        }
        _update_step(batch, "extract_data", "completed", result="pass", details=f"Extracted {len(batch.documents)} document(s)")
        batch.progress = 55
        save_batch(batch)

        # Step 4: Validate fields
        _update_step(batch, "validate_fields", "running")
        batch.status = ProcessingStatus.VALIDATING
        batch.current_stage = "validation"
        save_batch(batch)
        await asyncio.sleep(0.5)
        _update_step(batch, "validate_fields", "completed", result="pass", details="All required fields present")
        batch.progress = 70
        save_batch(batch)

        # Step 5: Calculate billing
        _update_step(batch, "calculate_billing", "running")
        save_batch(batch)
        await asyncio.sleep(0.5)

        claim_amount = batch.mapped_claim.get("total_amount", 0) if batch.mapped_claim else 250.00
        deductible = 50.0
        reimbursement_rate = 0.80
        covered = claim_amount - deductible
        payout = covered * reimbursement_rate

        batch.billing = BillingCalculation(
            claim_amount=claim_amount,
            deductible_applied=deductible,
            covered_amount=covered,
            reimbursement_rate=reimbursement_rate,
            final_payout=payout,
            customer_responsibility=claim_amount - payout,
        )
        _update_step(batch, "calculate_billing", "completed", result="pass", details=f"Payout: ${payout:.2f}")
        batch.progress = 85
        save_batch(batch)

        # Step 6: Submit
        _update_step(batch, "submit", "running")
        save_batch(batch)
        await asyncio.sleep(0.5)

        batch.ai_decision = "standard_review"
        batch.ai_reasoning = "Claim appears valid. Submitted for standard review."
        batch.ai_confidence = 0.85

        _update_step(batch, "submit", "completed", result="pass", details="Submitted for review")
        batch.progress = 100
        batch.status = ProcessingStatus.COMPLETED
        batch.current_stage = "completed"
        batch.completed_at = datetime.utcnow()
        batch.processing_time_ms = int((batch.completed_at - batch.started_at).total_seconds() * 1000)
        save_batch(batch)

        logger.info(f"Batch {batch_id} processing completed in {batch.processing_time_ms}ms")

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        batch.status = ProcessingStatus.FAILED
        batch.error = str(e)
        batch.error_stage = batch.current_stage
        save_batch(batch)


def _update_step(batch: ProcessedBatch, step_type: str, status: str, result: str = None, details: str = None):
    """Update an agent step's status."""
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


@router.delete("/batch/{batch_id}")
async def delete_batch(batch_id: str):
    """Delete a batch and its associated files."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
        )

    # Delete uploaded files
    batch_dir = UPLOADS_DIR / batch_id
    if batch_dir.exists():
        import shutil
        shutil.rmtree(batch_dir)

    # Remove batch from storage
    del _batches[batch_id]
    _save_batches()

    return {"message": f"Batch {batch_id} deleted successfully"}


@router.delete("/clear-all")
async def clear_all_data():
    """
    Clear ALL batches (for testing/reset).

    WARNING: This deletes all data permanently!
    """
    # Clear batches
    batch_count = len(_batches)
    _batches.clear()
    _save_batches()

    # Clear upload files
    import shutil
    if UPLOADS_DIR.exists():
        shutil.rmtree(UPLOADS_DIR)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Cleared {batch_count} batches")

    return {
        "message": "All data cleared successfully",
        "batches_deleted": batch_count,
    }
