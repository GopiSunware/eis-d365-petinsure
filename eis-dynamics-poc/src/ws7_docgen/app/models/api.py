"""API request/response models for DocGen service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.document import (
    DocumentType,
    ExportFormat,
    ExportResult,
    ProcessingStatus,
    UploadedDocument,
    ValidationIssue,
)


class UploadResponse(BaseModel):
    """Response after document upload."""
    batch_id: UUID
    documents_count: int
    documents: List[UploadedDocument]
    status: ProcessingStatus
    message: str

    class Config:
        json_encoders = {
            UUID: str,
        }


class ProcessingStatusResponse(BaseModel):
    """Current processing status."""
    batch_id: UUID
    status: ProcessingStatus
    progress: float  # 0-100
    current_stage: Optional[str] = None
    documents_processed: int = 0
    documents_total: int = 0
    estimated_remaining_seconds: Optional[int] = None
    error: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str,
        }


class ExportRequest(BaseModel):
    """Export generation request."""
    batch_id: UUID
    formats: List[ExportFormat]
    template: Optional[str] = None
    include_raw_data: bool = False
    include_documents: bool = False  # Include original documents in export


class ExportResponse(BaseModel):
    """Export generation response."""
    batch_id: UUID
    exports: List[ExportResult]
    download_urls: Dict[str, str]  # format -> url

    class Config:
        json_encoders = {
            UUID: str,
        }


class ClaimPopulateRequest(BaseModel):
    """Request to populate claim with extracted data."""
    batch_id: UUID
    claim_number: Optional[str] = None  # Existing claim to update
    create_new: bool = True  # Create new claim if not exists
    auto_submit: bool = False  # Auto-submit to pipeline


class ClaimPopulateResponse(BaseModel):
    """Response after claim population."""
    claim_number: str
    batch_id: UUID
    fields_populated: List[str]
    fields_requiring_review: List[str]
    validation_warnings: List[ValidationIssue]
    next_steps: List[str]
    claim_data: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            UUID: str,
        }


class ClaimPreviewResponse(BaseModel):
    """Preview of mapped claim data before population."""
    batch_id: UUID
    mapped_claim: Dict[str, Any]
    confidence_scores: Dict[str, float]
    fields_requiring_review: List[str]
    validation_issues: List[ValidationIssue]
    fraud_indicators: List[Dict[str, Any]]
    billing_summary: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            UUID: str,
        }


class BatchListResponse(BaseModel):
    """List of batches."""
    batches: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class TemplateInfo(BaseModel):
    """Information about an export template."""
    name: str
    description: str
    format: ExportFormat
    preview_url: Optional[str] = None


class TemplateListResponse(BaseModel):
    """List of available templates."""
    templates: List[TemplateInfo]
