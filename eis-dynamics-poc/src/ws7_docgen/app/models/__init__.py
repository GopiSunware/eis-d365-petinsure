"""DocGen Models."""

from app.models.document import (
    DocumentType,
    ProcessingStatus,
    ExportFormat,
    UploadedDocument,
    ExtractedLineItem,
    ExtractionResult,
    ValidationIssue,
    FraudIndicator,
    ProcessedBatch,
    ExportResult,
)
from app.models.api import (
    UploadResponse,
    ProcessingStatusResponse,
    ExportRequest,
    ExportResponse,
    ClaimPopulateRequest,
    ClaimPopulateResponse,
)

__all__ = [
    # Document models
    "DocumentType",
    "ProcessingStatus",
    "ExportFormat",
    "UploadedDocument",
    "ExtractedLineItem",
    "ExtractionResult",
    "ValidationIssue",
    "FraudIndicator",
    "ProcessedBatch",
    "ExportResult",
    # API models
    "UploadResponse",
    "ProcessingStatusResponse",
    "ExportRequest",
    "ExportResponse",
    "ClaimPopulateRequest",
    "ClaimPopulateResponse",
]
