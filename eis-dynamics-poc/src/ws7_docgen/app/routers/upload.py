"""Upload router for document uploads."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.models.document import (
    DocumentType,
    ProcessedBatch,
    ProcessingStatus,
    UploadedDocument,
)
from app.models.api import UploadResponse
from app.services.storage_service import get_storage_service
from app.services.zip_service import ZipExtractionError, get_zip_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Batch storage with file persistence
BATCHES_FILE = "/tmp/docgen/batches.json"
_batches: dict[str, ProcessedBatch] = {}


def _load_batches() -> dict[str, ProcessedBatch]:
    """Load batches from file storage."""
    if os.path.exists(BATCHES_FILE):
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
    try:
        os.makedirs(os.path.dirname(BATCHES_FILE), exist_ok=True)

        # Convert batches to JSON-serializable format
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
    _save_batches()  # Persist to disk


def list_batches() -> List[ProcessedBatch]:
    """List all batches."""
    return list(_batches.values())


def clear_all_batches() -> int:
    """Clear all batches (for testing/reset)."""
    count = len(_batches)
    _batches.clear()
    _save_batches()
    return count


# Load batches on module initialization
_batches = _load_batches()


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Documents to upload"),
    claim_number: Optional[str] = Form(None, description="Existing claim number"),
    policy_number: Optional[str] = Form(None, description="Policy number for new claims"),
    document_type: Optional[str] = Form(None, description="Document type hint"),
    customer_id: Optional[str] = Form(None, description="Customer ID from PetInsure360"),
    pet_id: Optional[str] = Form(None, description="Pet ID from PetInsure360"),
    pet_name: Optional[str] = Form(None, description="Pet name from PetInsure360"),
    policy_id: Optional[str] = Form(None, description="Policy ID from PetInsure360"),
):
    """
    Upload one or more documents (including ZIP files).

    - Supports PDF, JPG, PNG, HEIC, DOC, DOCX, and ZIP files
    - ZIP files are automatically extracted (max 50MB, 20 files)
    - Returns a batch ID for tracking processing status
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

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

    storage_service = get_storage_service()
    zip_service = get_zip_service()

    uploaded_docs = []
    errors = []

    for file in files:
        try:
            # Validate file
            validation_error = await _validate_file(file)
            if validation_error:
                errors.append(f"{file.filename}: {validation_error}")
                continue

            # Read file content
            content = await file.read()

            # Check if ZIP file
            if file.content_type in ["application/zip", "application/x-zip-compressed"] or \
               file.filename.lower().endswith(".zip"):
                # Extract ZIP and process each file
                try:
                    extracted_files = await zip_service.extract_zip(
                        content,
                        str(batch.batch_id),
                        file.filename,
                    )

                    for extracted_name, extracted_type, extracted_content in extracted_files:
                        doc = await _upload_single_file(
                            storage_service=storage_service,
                            batch_id=str(batch.batch_id),
                            filename=extracted_name,
                            content=extracted_content,
                            content_type=extracted_type,
                            document_type=document_type,
                            from_zip=True,
                            zip_source=file.filename,
                        )
                        uploaded_docs.append(doc)

                except ZipExtractionError as e:
                    errors.append(f"{file.filename}: {str(e)}")
                    continue
            else:
                # Single file upload
                doc = await _upload_single_file(
                    storage_service=storage_service,
                    batch_id=str(batch.batch_id),
                    filename=file.filename,
                    content=content,
                    content_type=file.content_type,
                    document_type=document_type,
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


async def _validate_file(file: UploadFile) -> Optional[str]:
    """Validate uploaded file. Returns error message if invalid."""
    # Check filename
    if not file.filename:
        return "No filename provided"

    # Check extension
    extension = Path(file.filename).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        return f"Unsupported file type: {extension}"

    # Check content type
    if file.content_type and file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        # Allow if extension is valid (content_type can be unreliable)
        logger.warning(f"Unexpected content type {file.content_type} for {file.filename}")

    # Check file size (approximate - actual check after read)
    if file.size and file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        return f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB"

    return None


async def _upload_single_file(
    storage_service,
    batch_id: str,
    filename: str,
    content: bytes,
    content_type: str,
    document_type: Optional[str] = None,
    from_zip: bool = False,
    zip_source: Optional[str] = None,
) -> UploadedDocument:
    """Upload a single file to storage."""
    # Upload to storage
    storage_url, file_hash = await storage_service.upload_file(
        file_content=content,
        filename=filename,
        content_type=content_type,
        batch_id=batch_id,
    )

    # Determine document type
    doc_type = None
    if document_type:
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            pass

    # Create document record
    doc = UploadedDocument(
        filename=f"{batch_id}/{filename}",
        original_filename=filename,
        content_type=content_type,
        file_size=len(content),
        file_hash=file_hash,
        document_type=doc_type,
        from_zip=from_zip,
        zip_source=zip_source,
    )

    # Set storage location
    if settings.USE_LOCAL_STORAGE:
        doc.local_path = storage_url
    else:
        doc.blob_url = storage_url

    return doc


@router.post("/batch/from-claim")
async def create_batch_from_claim(claim_data: dict):
    """
    Create a batch from claim data (without document uploads).

    This endpoint is called by PetInsure360 when a claim is submitted,
    allowing the Agent Pipeline to process the claim with AI.
    """
    from pydantic import BaseModel

    # Create batch ID
    batch_id = uuid4()

    # Create batch
    batch = ProcessedBatch(
        batch_id=batch_id,
        claim_number=claim_data.get("claim_number"),
        policy_number=claim_data.get("policy_id"),
        status=ProcessingStatus.PENDING,
        claim_data=claim_data,  # Store claim data for processing
    )

    # Save batch
    save_batch(batch)

    logger.info(f"Created batch {batch_id} from claim {claim_data.get('claim_id')}")

    return {
        "batch_id": str(batch_id),
        "claim_id": claim_data.get("claim_id"),
        "claim_number": claim_data.get("claim_number"),
        "status": batch.status.value,
        "message": "Batch created from claim data. Ready for AI processing."
    }


@router.get("/batches")
async def list_all_batches(
    limit: int = 20,
    offset: int = 0,
):
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
                # Include error info for inline display
                "error": b.error,
                "error_stage": b.error_stage,
                # Include agent steps for inline expandable view
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
                # Include AI decision info
                "ai_decision": b.ai_decision,
                "ai_reasoning": b.ai_reasoning,
                "ai_confidence": b.ai_confidence,
                # Include claim data summary
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
async def get_batch_details(batch_id: str):
    """Get detailed information about a batch."""
    batch = get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found",
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

    storage_service = get_storage_service()
    zip_service = get_zip_service()

    # Delete files from storage
    for doc in batch.documents:
        storage_url = doc.local_path or doc.blob_url
        if storage_url:
            await storage_service.delete_file(storage_url)

    # Clean up temp files
    await zip_service.cleanup(batch_id)
    await storage_service.cleanup_temp_files(batch_id)

    # Remove batch
    del _batches[batch_id]
    _save_batches()  # Persist deletion

    return {"message": f"Batch {batch_id} deleted successfully"}


@router.delete("/clear-all")
async def clear_all_data():
    """
    Clear ALL batches and fingerprints (for testing/reset).

    WARNING: This deletes all data permanently!
    """
    from app.agents.validate_agent import _document_fingerprints, _save_fingerprints

    # Clear batches
    batch_count = len(_batches)
    _batches.clear()
    _save_batches()

    # Clear fingerprints
    fingerprint_count = len(_document_fingerprints)
    _document_fingerprints.clear()
    _save_fingerprints()

    # Clear upload files
    import shutil
    upload_dir = "/tmp/docgen/storage/uploads"
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
        os.makedirs(upload_dir, exist_ok=True)

    logger.info(f"Cleared {batch_count} batches and {fingerprint_count} fingerprints")

    return {
        "message": "All data cleared successfully",
        "batches_deleted": batch_count,
        "fingerprints_deleted": fingerprint_count,
    }
