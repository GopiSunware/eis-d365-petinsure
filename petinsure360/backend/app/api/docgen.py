"""
DocGen API Router - Document Upload and AI Processing
Integrates with the DocGen service (ws7_docgen) for AI-driven claim processing
"""

import os
import uuid
import hashlib
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from pydantic import BaseModel
import httpx

router = APIRouter()

# DocGen service URL (ws7_docgen) - EIS Dynamics DocGen Service
DOCGEN_SERVICE_URL = os.getenv("DOCGEN_SERVICE_URL", "http://localhost:8007")

# Local storage for uploads (before forwarding to DocGen) - Project-relative path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = str(BASE_DIR / "data" / "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory storage for upload tracking (in production, use database)
upload_records = {}


class UploadRecord(BaseModel):
    """Track document uploads for a customer."""
    upload_id: str
    customer_id: str
    policy_id: Optional[str] = None
    pet_id: Optional[str] = None
    pet_name: Optional[str] = None
    policy_number: Optional[str] = None
    filenames: List[str]
    status: str = "uploaded"  # uploaded, processing, completed, failed
    docgen_batch_id: Optional[str] = None
    claim_id: Optional[str] = None
    claim_number: Optional[str] = None
    error_message: Optional[str] = None
    ai_decision: Optional[str] = None
    ai_reasoning: Optional[str] = None
    created_at: str
    updated_at: str


class UploadResponse(BaseModel):
    upload_id: str
    status: str
    message: str
    filenames: List[str]


class UploadStatusResponse(BaseModel):
    upload_id: str
    customer_id: str
    policy_id: Optional[str]
    pet_id: Optional[str]
    filenames: List[str]
    status: str
    docgen_batch_id: Optional[str]
    claim_id: Optional[str]
    claim_number: Optional[str]
    error_message: Optional[str]
    ai_decision: Optional[str]
    created_at: str
    updated_at: str


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    customer_id: str = Form(...),
    policy_id: str = Form(None),
    pet_id: str = Form(None),
    pet_name: str = Form(None),
    policy_number: str = Form(None),
):
    """
    Upload documents for AI-driven claim processing.

    This endpoint:
    1. Saves uploaded files locally
    2. Creates an upload record with customer/policy/pet context
    3. Forwards to DocGen service in the background
    4. Returns immediately with upload_id for status tracking
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Generate upload ID
    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(UPLOAD_DIR, upload_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Save files locally
    saved_files = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        saved_files.append({
            "filename": file.filename,
            "path": file_path,
            "size": len(content),
            "content_type": file.content_type
        })

    # Create upload record
    now = datetime.utcnow().isoformat()
    record = UploadRecord(
        upload_id=upload_id,
        customer_id=customer_id,
        policy_id=policy_id,
        pet_id=pet_id,
        pet_name=pet_name,
        policy_number=policy_number,
        filenames=[f["filename"] for f in saved_files],
        status="uploaded",
        created_at=now,
        updated_at=now
    )
    upload_records[upload_id] = record

    # Emit socket event for real-time notification
    sio = request.app.state.sio
    await sio.emit('docgen_upload', {
        'upload_id': upload_id,
        'customer_id': customer_id,
        'status': 'uploaded',
        'message': f'{len(saved_files)} document(s) uploaded successfully'
    }, room=f"customer_{customer_id}")

    # Process in background (forward to DocGen service)
    background_tasks.add_task(
        process_upload_background,
        upload_id=upload_id,
        saved_files=saved_files,
        customer_id=customer_id,
        policy_id=policy_id,
        pet_id=pet_id,
        policy_number=policy_number,
        sio=sio
    )

    return UploadResponse(
        upload_id=upload_id,
        status="uploaded",
        message="Documents uploaded successfully. Processing will begin shortly.",
        filenames=[f["filename"] for f in saved_files]
    )


async def process_upload_background(
    upload_id: str,
    saved_files: List[dict],
    customer_id: str,
    policy_id: Optional[str],
    pet_id: Optional[str],
    policy_number: Optional[str],
    sio
):
    """Background task to process upload through DocGen service."""
    record = upload_records.get(upload_id)
    if not record:
        return

    try:
        # Update status to processing
        record.status = "processing"
        record.updated_at = datetime.utcnow().isoformat()

        # Emit processing status
        await sio.emit('docgen_status', {
            'upload_id': upload_id,
            'customer_id': customer_id,
            'status': 'processing',
            'message': 'AI agent is analyzing your documents...'
        }, room=f"customer_{customer_id}")

        # Forward to DocGen service
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Upload files to DocGen
            files_to_send = []
            for f in saved_files:
                files_to_send.append(
                    ('files', (f['filename'], open(f['path'], 'rb'), f['content_type']))
                )

            # Include context in form data
            data = {
                'customer_id': customer_id,
            }
            if policy_number:
                data['policy_number'] = policy_number
            if policy_id:
                data['policy_id'] = policy_id
            if pet_id:
                data['pet_id'] = pet_id
            if record.pet_name:
                data['pet_name'] = record.pet_name

            # Upload to DocGen
            response = await client.post(
                f"{DOCGEN_SERVICE_URL}/api/v1/docgen/upload",
                files=files_to_send,
                data=data
            )

            # Close file handles
            for _, file_tuple in files_to_send:
                file_tuple[1].close()

            if response.status_code != 200:
                raise Exception(f"DocGen upload failed: {response.text}")

            upload_result = response.json()
            batch_id = upload_result.get('batch_id')
            record.docgen_batch_id = batch_id

            # Start processing
            process_response = await client.post(
                f"{DOCGEN_SERVICE_URL}/api/v1/docgen/process/{batch_id}",
                params={"sync": "true"}  # Wait for completion
            )

            # Get final result
            result_response = await client.get(
                f"{DOCGEN_SERVICE_URL}/api/v1/docgen/result/{batch_id}"
            )

            if result_response.status_code == 200:
                result = result_response.json()

                if result.get('status') == 'completed':
                    record.status = "completed"
                    record.ai_decision = result.get('ai_decision')
                    record.ai_reasoning = result.get('ai_reasoning')

                    # If successful, a claim was created
                    if result.get('ai_decision') in ['auto_approve', 'standard_review', 'proceed']:
                        # Generate claim number
                        record.claim_id = f"CLM-{datetime.utcnow().strftime('%Y%m%d')}-{upload_id[:8].upper()}"
                        record.claim_number = record.claim_id

                        await sio.emit('docgen_completed', {
                            'upload_id': upload_id,
                            'customer_id': customer_id,
                            'status': 'completed',
                            'claim_id': record.claim_id,
                            'claim_number': record.claim_number,
                            'ai_decision': record.ai_decision,
                            'message': f'Claim {record.claim_number} created successfully!'
                        }, room=f"customer_{customer_id}")
                    else:
                        # Needs review or rejected
                        await sio.emit('docgen_completed', {
                            'upload_id': upload_id,
                            'customer_id': customer_id,
                            'status': 'completed',
                            'ai_decision': record.ai_decision,
                            'message': f'Document processed. Decision: {record.ai_decision}'
                        }, room=f"customer_{customer_id}")
                else:
                    # Processing failed
                    record.status = "failed"
                    record.error_message = result.get('error', 'Processing failed')

                    await sio.emit('docgen_failed', {
                        'upload_id': upload_id,
                        'customer_id': customer_id,
                        'status': 'failed',
                        'error': record.error_message,
                        'message': f'Processing failed: {record.error_message}'
                    }, room=f"customer_{customer_id}")
            else:
                raise Exception(f"Failed to get processing result: {result_response.text}")

    except httpx.ConnectError:
        record.status = "failed"
        record.error_message = "DocGen service unavailable. Please try again later."

        await sio.emit('docgen_failed', {
            'upload_id': upload_id,
            'customer_id': customer_id,
            'status': 'failed',
            'error': record.error_message,
            'message': record.error_message
        }, room=f"customer_{customer_id}")

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)

        await sio.emit('docgen_failed', {
            'upload_id': upload_id,
            'customer_id': customer_id,
            'status': 'failed',
            'error': str(e),
            'message': f'Processing failed: {str(e)}'
        }, room=f"customer_{customer_id}")

    finally:
        record.updated_at = datetime.utcnow().isoformat()


@router.get("/uploads/{customer_id}")
async def get_customer_uploads(customer_id: str, limit: int = 20):
    """Get all uploads for a customer."""
    customer_uploads = [
        {
            "upload_id": r.upload_id,
            "customer_id": r.customer_id,
            "policy_id": r.policy_id,
            "pet_id": r.pet_id,
            "pet_name": r.pet_name,
            "filenames": r.filenames,
            "status": r.status,
            "docgen_batch_id": r.docgen_batch_id,
            "claim_id": r.claim_id,
            "claim_number": r.claim_number,
            "error_message": r.error_message,
            "ai_decision": r.ai_decision,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        }
        for r in upload_records.values()
        if r.customer_id == customer_id
    ]

    # Sort by created_at descending
    customer_uploads.sort(key=lambda x: x['created_at'], reverse=True)

    return {
        "customer_id": customer_id,
        "uploads": customer_uploads[:limit],
        "total": len(customer_uploads)
    }


@router.get("/upload/{upload_id}")
async def get_upload_status(upload_id: str):
    """Get status of a specific upload."""
    record = upload_records.get(upload_id)
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")

    return {
        "upload_id": record.upload_id,
        "customer_id": record.customer_id,
        "policy_id": record.policy_id,
        "pet_id": record.pet_id,
        "pet_name": record.pet_name,
        "filenames": record.filenames,
        "status": record.status,
        "docgen_batch_id": record.docgen_batch_id,
        "claim_id": record.claim_id,
        "claim_number": record.claim_number,
        "error_message": record.error_message,
        "ai_decision": record.ai_decision,
        "ai_reasoning": record.ai_reasoning,
        "created_at": record.created_at,
        "updated_at": record.updated_at
    }


@router.post("/process/{upload_id}")
async def trigger_processing(upload_id: str, request: Request, background_tasks: BackgroundTasks):
    """Manually trigger processing for an upload (retry failed uploads)."""
    record = upload_records.get(upload_id)
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")

    if record.status == "processing":
        raise HTTPException(status_code=400, detail="Upload is already being processed")

    # Get saved files
    upload_dir = os.path.join(UPLOAD_DIR, upload_id)
    if not os.path.exists(upload_dir):
        raise HTTPException(status_code=404, detail="Upload files not found")

    saved_files = []
    for filename in record.filenames:
        file_path = os.path.join(upload_dir, filename)
        if os.path.exists(file_path):
            saved_files.append({
                "filename": filename,
                "path": file_path,
                "content_type": "application/octet-stream"
            })

    if not saved_files:
        raise HTTPException(status_code=404, detail="No files found for processing")

    # Reset status
    record.status = "uploaded"
    record.error_message = None
    record.updated_at = datetime.utcnow().isoformat()

    # Process in background
    sio = request.app.state.sio
    background_tasks.add_task(
        process_upload_background,
        upload_id=upload_id,
        saved_files=saved_files,
        customer_id=record.customer_id,
        policy_id=record.policy_id,
        pet_id=record.pet_id,
        policy_number=record.policy_number,
        sio=sio
    )

    return {"status": "processing", "message": "Processing triggered"}


@router.get("/health")
async def docgen_health():
    """Check DocGen service health."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DOCGEN_SERVICE_URL}/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "docgen_service": "connected",
                    "docgen_url": DOCGEN_SERVICE_URL
                }
    except:
        pass

    return {
        "status": "degraded",
        "docgen_service": "unavailable",
        "docgen_url": DOCGEN_SERVICE_URL
    }
