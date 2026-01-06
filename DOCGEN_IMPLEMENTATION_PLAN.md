# DocGen Feature Implementation Plan
## EIS POC - Document Generation & Export System

---

## 1. Executive Summary

The DocGen feature enables users to:
1. **Upload** documents/receipts for insurance claims
2. **Process** them through an AI-powered agent pipeline
3. **Export** structured outputs in multiple formats (PDF, Excel, Word, CSV, JSON, HTML)

This integrates with the existing medallion architecture (Router → Bronze → Silver → Gold) and leverages the current AI capabilities (Claude/OpenAI).

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT PORTAL (WS4)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Document   │  │   Upload     │  │  Processing  │  │   Export     │    │
│  │   Library    │  │   Interface  │  │   Status     │  │   Manager    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCGEN SERVICE (WS7) - Port 8007                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Document Ingestion Layer                       │  │
│  │  • Multi-format upload (PDF, Images, DOCX, etc.)                     │  │
│  │  • OCR with Azure Document Intelligence                               │  │
│  │  • Initial validation & classification                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Document Processing Pipeline                     │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │ Ingest  │→ │ Extract │→ │ Enrich  │→ │ Validate│→ │ Generate│   │  │
│  │  │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Export Generation Layer                        │  │
│  │  • PDF Generator (ReportLab/WeasyPrint)                              │  │
│  │  • Excel Generator (openpyxl)                                         │  │
│  │  • Word Generator (python-docx)                                       │  │
│  │  • CSV/JSON/HTML generators                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │Azure Blob   │ │  Cosmos DB  │ │  Dataverse  │
            │Storage      │ │             │ │  D365       │
            └─────────────┘ └─────────────┘ └─────────────┘
```

### 2.2 Service Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE COMMUNICATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WS4 (Portal)  ←→  WS7 (DocGen)  ←→  WS6 (Pipeline)            │
│       │                  │                   │                   │
│       │                  │                   │                   │
│       ▼                  ▼                   ▼                   │
│  WS2 (Claims)      Azure Storage      WS3 (Integration)         │
│                                                                  │
│  Communication:                                                  │
│  • REST APIs for synchronous operations                         │
│  • WebSocket for real-time processing updates                   │
│  • Azure Service Bus for async document processing              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Document Processing Pipeline

### 3.1 Five-Stage Document Agent Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT PROCESSING PIPELINE                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Stage 1: INGEST AGENT                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ • Receive uploaded documents (multi-file support)               │    │
│  │ • Store raw documents in Azure Blob Storage                     │    │
│  │ • Generate document fingerprint/hash for deduplication          │    │
│  │ • Initial file validation (size, type, virus scan)              │    │
│  │ • Create processing job with unique job_id                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                     │                                    │
│                                     ▼                                    │
│  Stage 2: EXTRACT AGENT                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ • OCR processing via Azure Document Intelligence                │    │
│  │ • Document classification (receipt, invoice, report, etc.)      │    │
│  │ • AI-powered field extraction:                                  │    │
│  │   - Vendor/provider name                                        │    │
│  │   - Date of service                                             │    │
│  │   - Line items with amounts                                     │    │
│  │   - Total amount                                                │    │
│  │   - Tax information                                             │    │
│  │   - Payment method                                              │    │
│  │ • Confidence scoring for each extracted field                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                     │                                    │
│                                     ▼                                    │
│  Stage 3: ENRICH AGENT                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ • Cross-reference with claim data                               │    │
│  │ • Match vendor to provider database                             │    │
│  │ • Validate service dates against policy coverage                │    │
│  │ • Flag potential duplicates                                     │    │
│  │ • Calculate reimbursement eligibility                           │    │
│  │ • Enrich with historical claim patterns                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                     │                                    │
│                                     ▼                                    │
│  Stage 4: VALIDATE AGENT                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ • Business rule validation                                      │    │
│  │ • Fraud indicator detection                                     │    │
│  │ • Coverage limit checks                                         │    │
│  │ • Policy compliance verification                                │    │
│  │ • Generate validation report with issues/warnings               │    │
│  │ • Calculate final fraud score                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                     │                                    │
│                                     ▼                                    │
│  Stage 5: GENERATE AGENT                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ • Compile structured claim document                             │    │
│  │ • Generate human-readable summary                               │    │
│  │ • Create exportable data package                                │    │
│  │ • Prepare templates for each export format                      │    │
│  │ • Store processed output in database                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Document Types Supported

| Document Type | Extension | OCR Required | Special Processing |
|---------------|-----------|--------------|-------------------|
| Vet Invoice | PDF, JPG, PNG | Yes | Line item extraction |
| Medical Receipt | PDF, JPG, PNG | Yes | Treatment code extraction |
| Police Report | PDF | Optional | Incident detail extraction |
| Repair Estimate | PDF, DOCX | Optional | Parts/labor breakdown |
| Photo Evidence | JPG, PNG, HEIC | No | Image analysis, damage assessment |
| Lab Results | PDF | Yes | Test result extraction |

---

## 4. Export Formats & Templates

### 4.1 Export Format Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXPORT FORMAT SUPPORT                             │
├───────────────┬─────────────┬───────────────────┬──────────────────────┤
│ Format        │ Library     │ Use Case          │ Template Support     │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ PDF           │ WeasyPrint  │ Formal reports,   │ Yes - Jinja2 + CSS   │
│               │ + Jinja2    │ claim summaries   │                      │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ Excel (.xlsx) │ openpyxl    │ Data analysis,    │ Yes - XLSX templates │
│               │             │ tabular exports   │                      │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ Word (.docx)  │ python-docx │ Editable docs,    │ Yes - DOCX templates │
│               │             │ letters           │                      │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ CSV           │ Built-in    │ Data interchange, │ No (schema-based)    │
│               │             │ imports           │                      │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ JSON          │ Built-in    │ API integration,  │ No (schema-based)    │
│               │             │ programmatic use  │                      │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ HTML          │ Jinja2      │ Web preview,      │ Yes - HTML templates │
│               │             │ email embedding   │                      │
├───────────────┼─────────────┼───────────────────┼──────────────────────┤
│ XML           │ lxml        │ Legacy system     │ Yes - XSD schemas    │
│               │             │ integration       │                      │
└───────────────┴─────────────┴───────────────────┴──────────────────────┘
```

### 4.2 Template Types

```
templates/
├── pdf/
│   ├── claim_summary.html          # Full claim summary report
│   ├── document_extract.html       # Single document extraction report
│   ├── validation_report.html      # Validation/fraud analysis report
│   └── reimbursement_letter.html   # Customer-facing letter
├── excel/
│   ├── claim_details.xlsx          # Detailed claim workbook
│   ├── line_items.xlsx             # Itemized expenses
│   └── multi_claim_report.xlsx     # Batch claim report
├── word/
│   ├── claim_letter.docx           # Customer correspondence
│   ├── adjuster_notes.docx         # Internal adjuster document
│   └── coverage_explanation.docx   # EOB-style document
└── html/
    ├── preview.html                # Web preview template
    └── email_embed.html            # Email-friendly format
```

---

## 5. Data Models

### 5.1 Core Models

```python
# src/ws7_docgen/models/document.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class DocumentType(str, Enum):
    VET_INVOICE = "vet_invoice"
    MEDICAL_RECEIPT = "medical_receipt"
    POLICE_REPORT = "police_report"
    REPAIR_ESTIMATE = "repair_estimate"
    PHOTO_EVIDENCE = "photo_evidence"
    LAB_RESULTS = "lab_results"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    ENRICHING = "enriching"
    VALIDATING = "validating"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "xlsx"
    WORD = "docx"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    XML = "xml"


class UploadedDocument(BaseModel):
    """Represents an uploaded document before processing."""
    id: UUID = Field(default_factory=uuid4)
    claim_number: str
    filename: str
    content_type: str
    file_size: int
    blob_url: str
    document_type: Optional[DocumentType] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: Optional[str] = None
    file_hash: str  # SHA-256 for deduplication


class ExtractedField(BaseModel):
    """A single extracted field with confidence score."""
    field_name: str
    value: Any
    confidence: float = Field(ge=0, le=1)
    source_location: Optional[str] = None  # Page/region reference
    needs_review: bool = False


class LineItem(BaseModel):
    """Extracted line item from invoice/receipt."""
    description: str
    quantity: float = 1.0
    unit_price: Decimal
    total: Decimal
    category: Optional[str] = None
    service_code: Optional[str] = None
    service_date: Optional[datetime] = None
    is_covered: Optional[bool] = None
    coverage_amount: Optional[Decimal] = None


class ExtractedData(BaseModel):
    """Structured data extracted from a document."""
    document_id: UUID
    document_type: DocumentType

    # Common fields
    vendor_name: Optional[ExtractedField] = None
    vendor_address: Optional[ExtractedField] = None
    vendor_phone: Optional[ExtractedField] = None

    document_date: Optional[ExtractedField] = None
    document_number: Optional[ExtractedField] = None

    # Financial fields
    line_items: List[LineItem] = []
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[ExtractedField] = None
    currency: str = "USD"

    # Payment info
    payment_method: Optional[ExtractedField] = None
    amount_paid: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None

    # Pet-specific (for vet invoices)
    pet_name: Optional[ExtractedField] = None
    diagnosis: Optional[ExtractedField] = None
    treatment: Optional[ExtractedField] = None

    # Raw extracted text
    raw_text: Optional[str] = None

    # Metadata
    extraction_model: str = "claude-sonnet-4"
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_confidence: float = 0.0


class ValidationIssue(BaseModel):
    """A validation issue or warning."""
    severity: str  # error, warning, info
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Results from the validation agent."""
    document_id: UUID
    is_valid: bool
    fraud_score: float = Field(ge=0, le=1)
    fraud_indicators: List[str] = []
    issues: List[ValidationIssue] = []

    # Coverage validation
    is_covered: bool = True
    coverage_issues: List[str] = []
    eligible_amount: Optional[Decimal] = None
    ineligible_amount: Optional[Decimal] = None

    # Duplicate check
    is_duplicate: bool = False
    duplicate_of: Optional[UUID] = None


class ProcessedDocument(BaseModel):
    """Complete processed document with all stages."""
    id: UUID = Field(default_factory=uuid4)
    claim_number: str

    # Original document
    original: UploadedDocument

    # Processing stages
    status: ProcessingStatus = ProcessingStatus.PENDING
    current_stage: Optional[str] = None

    # Stage outputs
    extracted_data: Optional[ExtractedData] = None
    enrichment_data: Optional[Dict[str, Any]] = None
    validation_result: Optional[ValidationResult] = None

    # Generated output
    generated_summary: Optional[str] = None
    export_ready: bool = False

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None

    # Errors
    error: Optional[str] = None
    error_stage: Optional[str] = None


class DocumentBatch(BaseModel):
    """A batch of documents for a single claim."""
    batch_id: UUID = Field(default_factory=uuid4)
    claim_number: str
    documents: List[ProcessedDocument] = []

    # Aggregated data
    total_amount: Optional[Decimal] = None
    total_eligible: Optional[Decimal] = None
    overall_fraud_score: float = 0.0

    # Status
    status: ProcessingStatus = ProcessingStatus.PENDING
    documents_processed: int = 0
    documents_failed: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ExportRequest(BaseModel):
    """Request to export processed documents."""
    batch_id: UUID
    formats: List[ExportFormat]
    template: Optional[str] = None  # Template name override
    include_original: bool = False  # Include original documents
    include_raw_extraction: bool = False

    # PDF options
    pdf_options: Optional[Dict[str, Any]] = None

    # Excel options
    excel_options: Optional[Dict[str, Any]] = None


class ExportResult(BaseModel):
    """Result of an export operation."""
    export_id: UUID = Field(default_factory=uuid4)
    batch_id: UUID
    format: ExportFormat

    blob_url: str
    filename: str
    file_size: int

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # For signed URLs
```

### 5.2 API Models

```python
# src/ws7_docgen/models/api.py

class UploadRequest(BaseModel):
    """Request to upload documents."""
    claim_number: str
    document_type: Optional[DocumentType] = None
    metadata: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    """Response after document upload."""
    batch_id: UUID
    documents: List[UploadedDocument]
    processing_job_id: UUID


class ProcessingStatusResponse(BaseModel):
    """Current processing status."""
    batch_id: UUID
    status: ProcessingStatus
    progress: float  # 0-100
    current_document: Optional[str] = None
    current_stage: Optional[str] = None
    documents_completed: int
    documents_total: int
    estimated_remaining_seconds: Optional[int] = None


class ExportResponse(BaseModel):
    """Response with export download links."""
    batch_id: UUID
    exports: List[ExportResult]
    download_urls: Dict[ExportFormat, str]
```

---

## 6. API Endpoints

### 6.1 Document Upload & Processing

```yaml
# Upload Endpoints
POST   /api/v1/docgen/upload
       - Upload single or multiple documents
       - Body: multipart/form-data with files + metadata
       - Returns: UploadResponse with batch_id

POST   /api/v1/docgen/upload/url
       - Upload from URL (for existing blob storage docs)
       - Body: { claim_number, document_urls: [...] }

# Processing Endpoints
POST   /api/v1/docgen/process/{batch_id}
       - Trigger processing for uploaded batch
       - Optional: { async: true } for background processing

GET    /api/v1/docgen/status/{batch_id}
       - Get current processing status
       - Returns: ProcessingStatusResponse

GET    /api/v1/docgen/result/{batch_id}
       - Get completed processing results
       - Returns: DocumentBatch with all processed documents

# WebSocket for real-time updates
WS     /ws/docgen/{batch_id}
       - Real-time processing status updates
       - Agent reasoning stream
       - Progress events
```

### 6.2 Export Endpoints

```yaml
# Export Generation
POST   /api/v1/docgen/export
       - Generate exports in specified formats
       - Body: ExportRequest
       - Returns: ExportResponse with download URLs

GET    /api/v1/docgen/export/{export_id}
       - Get specific export status/details

GET    /api/v1/docgen/export/{export_id}/download
       - Download exported file
       - Returns: File stream with appropriate content-type

# Bulk Export
POST   /api/v1/docgen/export/bulk
       - Export multiple batches at once
       - Body: { batch_ids: [...], formats: [...] }

# Template Management
GET    /api/v1/docgen/templates
       - List available export templates

GET    /api/v1/docgen/templates/{template_name}/preview
       - Preview template with sample data
```

### 6.3 Management Endpoints

```yaml
# Document Management
GET    /api/v1/docgen/documents/{claim_number}
       - List all documents for a claim

DELETE /api/v1/docgen/documents/{document_id}
       - Delete a document

# Reprocessing
POST   /api/v1/docgen/reprocess/{document_id}
       - Reprocess a single document

POST   /api/v1/docgen/reprocess/batch/{batch_id}
       - Reprocess entire batch
```

---

## 7. Service Implementation

### 7.1 Directory Structure

```
src/ws7_docgen/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application
│   ├── config.py                   # Service configuration
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py               # Upload endpoints
│   │   ├── processing.py           # Processing endpoints
│   │   ├── export.py               # Export endpoints
│   │   └── templates.py            # Template management
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py             # Core document models
│   │   ├── api.py                  # API request/response models
│   │   └── export.py               # Export-specific models
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Base document agent
│   │   ├── ingest_agent.py         # Document ingestion
│   │   ├── extract_agent.py        # Data extraction
│   │   ├── enrich_agent.py         # Data enrichment
│   │   ├── validate_agent.py       # Validation & fraud check
│   │   └── generate_agent.py       # Output generation
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py     # Document CRUD operations
│   │   ├── processing_service.py   # Pipeline orchestration
│   │   ├── ocr_service.py          # Azure Document Intelligence
│   │   └── storage_service.py      # Blob storage operations
│   │
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── base_exporter.py        # Base exporter class
│   │   ├── pdf_exporter.py         # PDF generation
│   │   ├── excel_exporter.py       # Excel generation
│   │   ├── word_exporter.py        # Word generation
│   │   ├── csv_exporter.py         # CSV generation
│   │   ├── json_exporter.py        # JSON generation
│   │   └── html_exporter.py        # HTML generation
│   │
│   ├── templates/
│   │   ├── pdf/
│   │   ├── excel/
│   │   ├── word/
│   │   └── html/
│   │
│   ├── prompts/
│   │   ├── extraction.py           # Extraction prompts
│   │   ├── classification.py       # Document classification
│   │   ├── validation.py           # Validation prompts
│   │   └── summarization.py        # Summary generation
│   │
│   └── orchestration/
│       ├── __init__.py
│       ├── pipeline.py             # Pipeline orchestration
│       ├── state_manager.py        # Processing state
│       └── event_publisher.py      # WebSocket events
│
├── tests/
│   ├── __init__.py
│   ├── test_upload.py
│   ├── test_processing.py
│   ├── test_export.py
│   └── fixtures/
│       └── sample_documents/
│
├── requirements.txt
└── Dockerfile
```

### 7.2 Key Implementation Files

#### Main Application

```python
# src/ws7_docgen/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.routers import upload, processing, export, templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting DocGen Service...")
    logger.info(f"AI Provider: {settings.AI_PROVIDER}")
    logger.info(f"Storage: {settings.STORAGE_TYPE}")
    yield
    # Shutdown
    logger.info("Shutting down DocGen Service...")


app = FastAPI(
    title="EIS DocGen Service",
    description="Document Generation & Export Service for Claims Processing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1/docgen", tags=["upload"])
app.include_router(processing.router, prefix="/api/v1/docgen", tags=["processing"])
app.include_router(export.router, prefix="/api/v1/docgen", tags=["export"])
app.include_router(templates.router, prefix="/api/v1/docgen", tags=["templates"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "docgen"}
```

#### Extract Agent (Core AI Processing)

```python
# src/ws7_docgen/app/agents/extract_agent.py

from typing import Optional, Dict, Any
from anthropic import Anthropic
from openai import OpenAI
import json
import logging

from app.config import settings
from app.models.document import (
    UploadedDocument,
    ExtractedData,
    ExtractedField,
    LineItem,
    DocumentType
)
from app.prompts.extraction import get_extraction_prompt

logger = logging.getLogger(__name__)


class ExtractAgent:
    """Agent for extracting structured data from documents."""

    def __init__(self):
        self.ai_provider = settings.AI_PROVIDER
        if self.ai_provider == "claude":
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def extract(
        self,
        document: UploadedDocument,
        ocr_text: str,
        image_data: Optional[bytes] = None
    ) -> ExtractedData:
        """Extract structured data from document text/image."""

        # Classify document type if not provided
        doc_type = document.document_type or await self._classify_document(ocr_text)

        # Get extraction prompt for document type
        prompt = get_extraction_prompt(doc_type, ocr_text)

        # Call AI for extraction
        if self.ai_provider == "claude":
            response = await self._extract_with_claude(prompt, image_data)
        else:
            response = await self._extract_with_openai(prompt)

        # Parse and structure the response
        extracted = self._parse_extraction_response(response, document.id, doc_type)

        # Calculate overall confidence
        extracted.overall_confidence = self._calculate_confidence(extracted)

        return extracted

    async def _extract_with_claude(
        self,
        prompt: str,
        image_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Use Claude for extraction with optional vision."""

        messages = []

        if image_data:
            # Use vision for image-based documents
            import base64
            image_b64 = base64.b64encode(image_data).decode()
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=4096,
            messages=messages,
            system="You are a document extraction specialist. Extract data accurately and provide confidence scores."
        )

        return json.loads(response.content[0].text)

    async def _classify_document(self, text: str) -> DocumentType:
        """Classify document type from content."""

        classification_prompt = f"""Classify this document into one of these categories:
        - vet_invoice: Veterinary bills, pet medical invoices
        - medical_receipt: Human medical receipts
        - police_report: Police reports, incident reports
        - repair_estimate: Repair quotes, estimates
        - lab_results: Laboratory test results
        - other: Other document types

        Document text:
        {text[:2000]}

        Respond with just the category name."""

        if self.ai_provider == "claude":
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Use fast model for classification
                max_tokens=50,
                messages=[{"role": "user", "content": classification_prompt}]
            )
            classification = response.content[0].text.strip().lower()
        else:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=50,
                messages=[{"role": "user", "content": classification_prompt}]
            )
            classification = response.choices[0].message.content.strip().lower()

        try:
            return DocumentType(classification)
        except ValueError:
            return DocumentType.OTHER

    def _parse_extraction_response(
        self,
        response: Dict[str, Any],
        document_id: str,
        doc_type: DocumentType
    ) -> ExtractedData:
        """Parse AI response into structured ExtractedData."""

        # Extract line items
        line_items = []
        for item in response.get("line_items", []):
            line_items.append(LineItem(
                description=item.get("description", ""),
                quantity=float(item.get("quantity", 1)),
                unit_price=item.get("unit_price", 0),
                total=item.get("total", 0),
                category=item.get("category"),
                service_code=item.get("service_code"),
                service_date=item.get("service_date"),
            ))

        return ExtractedData(
            document_id=document_id,
            document_type=doc_type,
            vendor_name=self._make_field(response.get("vendor_name")),
            vendor_address=self._make_field(response.get("vendor_address")),
            document_date=self._make_field(response.get("document_date")),
            document_number=self._make_field(response.get("document_number")),
            line_items=line_items,
            subtotal=response.get("subtotal"),
            tax_amount=response.get("tax_amount"),
            total_amount=self._make_field(response.get("total_amount")),
            pet_name=self._make_field(response.get("pet_name")),
            diagnosis=self._make_field(response.get("diagnosis")),
            treatment=self._make_field(response.get("treatment")),
            extraction_model=settings.CLAUDE_MODEL if self.ai_provider == "claude" else settings.OPENAI_MODEL,
        )

    def _make_field(self, data: Any) -> Optional[ExtractedField]:
        """Create ExtractedField from response data."""
        if data is None:
            return None
        if isinstance(data, dict):
            return ExtractedField(
                field_name=data.get("field", ""),
                value=data.get("value"),
                confidence=data.get("confidence", 0.8),
                needs_review=data.get("confidence", 0.8) < 0.7
            )
        return ExtractedField(
            field_name="",
            value=data,
            confidence=0.8
        )

    def _calculate_confidence(self, extracted: ExtractedData) -> float:
        """Calculate overall extraction confidence."""
        confidences = []

        for field in [extracted.vendor_name, extracted.total_amount,
                      extracted.document_date, extracted.pet_name]:
            if field:
                confidences.append(field.confidence)

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)
```

#### PDF Exporter

```python
# src/ws7_docgen/app/exporters/pdf_exporter.py

from typing import Optional, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
import logging

from app.models.document import DocumentBatch, ExportFormat, ExportResult
from app.exporters.base_exporter import BaseExporter
from app.config import settings

logger = logging.getLogger(__name__)


class PDFExporter(BaseExporter):
    """Export processed documents to PDF format."""

    def __init__(self):
        super().__init__(ExportFormat.PDF)
        self.template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

        # Load CSS
        self.css_path = self.template_dir / "styles.css"

    async def export(
        self,
        batch: DocumentBatch,
        template_name: str = "claim_summary",
        options: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Generate PDF export from document batch."""

        options = options or {}

        # Load template
        template = self.env.get_template(f"{template_name}.html")

        # Prepare template data
        template_data = self._prepare_template_data(batch, options)

        # Render HTML
        html_content = template.render(**template_data)

        # Convert to PDF
        pdf_bytes = self._render_pdf(html_content, options)

        # Upload to storage
        filename = f"claim_{batch.claim_number}_{template_name}.pdf"
        blob_url = await self.storage_service.upload(
            data=pdf_bytes,
            filename=filename,
            content_type="application/pdf"
        )

        return ExportResult(
            batch_id=batch.batch_id,
            format=ExportFormat.PDF,
            blob_url=blob_url,
            filename=filename,
            file_size=len(pdf_bytes)
        )

    def _prepare_template_data(
        self,
        batch: DocumentBatch,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare data for template rendering."""

        # Aggregate line items from all documents
        all_line_items = []
        for doc in batch.documents:
            if doc.extracted_data:
                all_line_items.extend(doc.extracted_data.line_items)

        # Get validation issues
        all_issues = []
        for doc in batch.documents:
            if doc.validation_result:
                all_issues.extend(doc.validation_result.issues)

        return {
            "batch": batch,
            "claim_number": batch.claim_number,
            "documents": batch.documents,
            "line_items": all_line_items,
            "total_amount": batch.total_amount,
            "total_eligible": batch.total_eligible,
            "fraud_score": batch.overall_fraud_score,
            "validation_issues": all_issues,
            "generated_at": datetime.utcnow(),
            "options": options,
            # Company branding
            "company_name": settings.COMPANY_NAME,
            "company_logo": settings.COMPANY_LOGO_URL,
        }

    def _render_pdf(
        self,
        html_content: str,
        options: Dict[str, Any]
    ) -> bytes:
        """Render HTML to PDF bytes."""

        # Load CSS
        css = CSS(filename=str(self.css_path)) if self.css_path.exists() else None

        # PDF options
        pdf_options = {
            "presentational_hints": True,
        }

        # Page size
        if options.get("page_size") == "letter":
            pdf_options["page_size"] = "Letter"
        else:
            pdf_options["page_size"] = "A4"

        # Generate PDF
        html = HTML(string=html_content, base_url=str(self.template_dir))

        if css:
            pdf_bytes = html.write_pdf(stylesheets=[css])
        else:
            pdf_bytes = html.write_pdf()

        return pdf_bytes
```

#### Excel Exporter

```python
# src/ws7_docgen/app/exporters/excel_exporter.py

from typing import Optional, Dict, Any, List
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import logging

from app.models.document import DocumentBatch, ExportFormat, ExportResult, LineItem
from app.exporters.base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class ExcelExporter(BaseExporter):
    """Export processed documents to Excel format."""

    def __init__(self):
        super().__init__(ExportFormat.EXCEL)

        # Styles
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
        self.money_format = '"$"#,##0.00'
        self.date_format = 'YYYY-MM-DD'

    async def export(
        self,
        batch: DocumentBatch,
        template_name: str = "claim_details",
        options: Optional[Dict[str, Any]] = None
    ) -> ExportResult:
        """Generate Excel export from document batch."""

        options = options or {}

        wb = Workbook()

        # Summary sheet
        self._create_summary_sheet(wb.active, batch)

        # Line items sheet
        items_sheet = wb.create_sheet("Line Items")
        self._create_line_items_sheet(items_sheet, batch)

        # Documents sheet
        docs_sheet = wb.create_sheet("Documents")
        self._create_documents_sheet(docs_sheet, batch)

        # Validation sheet
        if any(doc.validation_result for doc in batch.documents):
            val_sheet = wb.create_sheet("Validation")
            self._create_validation_sheet(val_sheet, batch)

        # Save to bytes
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        excel_bytes = buffer.getvalue()

        # Upload
        filename = f"claim_{batch.claim_number}_details.xlsx"
        blob_url = await self.storage_service.upload(
            data=excel_bytes,
            filename=filename,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        return ExportResult(
            batch_id=batch.batch_id,
            format=ExportFormat.EXCEL,
            blob_url=blob_url,
            filename=filename,
            file_size=len(excel_bytes)
        )

    def _create_summary_sheet(self, ws, batch: DocumentBatch):
        """Create summary sheet."""
        ws.title = "Summary"

        # Title
        ws["A1"] = f"Claim Summary - {batch.claim_number}"
        ws["A1"].font = Font(bold=True, size=16)
        ws.merge_cells("A1:D1")

        # Summary data
        summary_data = [
            ("Claim Number", batch.claim_number),
            ("Documents Processed", len(batch.documents)),
            ("Total Amount", batch.total_amount),
            ("Eligible Amount", batch.total_eligible),
            ("Fraud Score", f"{batch.overall_fraud_score:.2%}"),
            ("Status", batch.status.value),
            ("Processed At", batch.completed_at),
        ]

        row = 3
        for label, value in summary_data:
            ws[f"A{row}"] = label
            ws[f"A{row}"].font = Font(bold=True)
            ws[f"B{row}"] = value
            row += 1

        # Auto-size columns
        self._auto_size_columns(ws)

    def _create_line_items_sheet(self, ws, batch: DocumentBatch):
        """Create line items sheet."""

        # Headers
        headers = ["Document", "Description", "Quantity", "Unit Price",
                   "Total", "Category", "Service Date", "Covered"]
        self._write_header_row(ws, headers)

        # Data
        row = 2
        for doc in batch.documents:
            if doc.extracted_data:
                for item in doc.extracted_data.line_items:
                    ws[f"A{row}"] = doc.original.filename
                    ws[f"B{row}"] = item.description
                    ws[f"C{row}"] = item.quantity
                    ws[f"D{row}"] = float(item.unit_price)
                    ws[f"D{row}"].number_format = self.money_format
                    ws[f"E{row}"] = float(item.total)
                    ws[f"E{row}"].number_format = self.money_format
                    ws[f"F{row}"] = item.category or ""
                    ws[f"G{row}"] = item.service_date
                    ws[f"H{row}"] = "Yes" if item.is_covered else "No"
                    row += 1

        self._auto_size_columns(ws)

    def _write_header_row(self, ws, headers: List[str]):
        """Write styled header row."""
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal="center")

    def _auto_size_columns(self, ws):
        """Auto-size all columns."""
        for column_cells in ws.columns:
            length = max(len(str(cell.value or "")) for cell in column_cells)
            ws.column_dimensions[get_column_letter(column_cells[0].column)].width = min(length + 2, 50)
```

---

## 8. Frontend Implementation

### 8.1 New Pages & Components

```
src/ws4_agent_portal/
├── app/
│   └── docgen/
│       ├── page.tsx                 # Main DocGen dashboard
│       ├── upload/
│       │   └── page.tsx             # Document upload page
│       ├── [batchId]/
│       │   ├── page.tsx             # Batch details & status
│       │   └── export/
│       │       └── page.tsx         # Export selection & download
│       └── layout.tsx               # DocGen layout
├── components/
│   └── docgen/
│       ├── DocumentUploader.tsx     # Drag & drop upload
│       ├── ProcessingStatus.tsx     # Real-time progress
│       ├── DocumentPreview.tsx      # Document viewer
│       ├── ExtractionResults.tsx    # Show extracted data
│       ├── ValidationReport.tsx     # Show validation issues
│       ├── ExportSelector.tsx       # Format selection
│       └── ExportDownload.tsx       # Download buttons
└── lib/
    └── docgen-api.ts                # DocGen API client
```

### 8.2 Document Upload Component

```tsx
// src/ws4_agent_portal/components/docgen/DocumentUploader.tsx

'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, Loader2 } from 'lucide-react';
import { uploadDocuments } from '@/lib/docgen-api';

interface UploadedFile {
  file: File;
  preview: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface DocumentUploaderProps {
  claimNumber: string;
  onUploadComplete: (batchId: string) => void;
}

export default function DocumentUploader({
  claimNumber,
  onUploadComplete
}: DocumentUploaderProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      status: 'pending' as const,
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.heic'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('claim_number', claimNumber);
      files.forEach(({ file }) => {
        formData.append('files', file);
      });

      const response = await uploadDocuments(formData);
      onUploadComplete(response.batch_id);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-blue-500 font-medium">Drop files here...</p>
        ) : (
          <>
            <p className="text-gray-600 font-medium">
              Drag & drop documents here
            </p>
            <p className="text-gray-400 text-sm mt-1">
              or click to browse (PDF, Images, Word docs up to 10MB)
            </p>
          </>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700">
            Selected Files ({files.length})
          </h4>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <File className="w-5 h-5 text-gray-400" />
                  <span className="text-sm text-gray-700">{file.file.name}</span>
                  <span className="text-xs text-gray-400">
                    ({(file.file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-gray-400 hover:text-red-500"
                >
                  <X className="w-4 h-4" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Upload Button */}
      {files.length > 0 && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className={`
            w-full py-3 px-4 rounded-lg font-medium text-white
            ${isUploading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
            }
          `}
        >
          {isUploading ? (
            <span className="flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Uploading...
            </span>
          ) : (
            `Upload ${files.length} Document${files.length > 1 ? 's' : ''}`
          )}
        </button>
      )}
    </div>
  );
}
```

### 8.3 Export Selector Component

```tsx
// src/ws4_agent_portal/components/docgen/ExportSelector.tsx

'use client';

import { useState } from 'react';
import { FileText, FileSpreadsheet, FileType, Download, Loader2 } from 'lucide-react';
import { generateExport, ExportFormat } from '@/lib/docgen-api';

interface ExportOption {
  format: ExportFormat;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const EXPORT_OPTIONS: ExportOption[] = [
  {
    format: 'pdf',
    label: 'PDF Report',
    description: 'Professional claim summary document',
    icon: FileText,
  },
  {
    format: 'xlsx',
    label: 'Excel Spreadsheet',
    description: 'Detailed data with line items',
    icon: FileSpreadsheet,
  },
  {
    format: 'docx',
    label: 'Word Document',
    description: 'Editable claim letter',
    icon: FileType,
  },
  {
    format: 'csv',
    label: 'CSV Data',
    description: 'Raw data for analysis',
    icon: FileText,
  },
  {
    format: 'json',
    label: 'JSON',
    description: 'Structured data for integration',
    icon: FileText,
  },
];

interface ExportSelectorProps {
  batchId: string;
  onExportComplete: (downloads: Record<ExportFormat, string>) => void;
}

export default function ExportSelector({
  batchId,
  onExportComplete
}: ExportSelectorProps) {
  const [selectedFormats, setSelectedFormats] = useState<ExportFormat[]>(['pdf']);
  const [isExporting, setIsExporting] = useState(false);

  const toggleFormat = (format: ExportFormat) => {
    setSelectedFormats(prev =>
      prev.includes(format)
        ? prev.filter(f => f !== format)
        : [...prev, format]
    );
  };

  const handleExport = async () => {
    if (selectedFormats.length === 0) return;

    setIsExporting(true);

    try {
      const response = await generateExport(batchId, selectedFormats);
      onExportComplete(response.download_urls);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Select Export Formats
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {EXPORT_OPTIONS.map(({ format, label, description, icon: Icon }) => (
            <button
              key={format}
              onClick={() => toggleFormat(format)}
              className={`
                p-4 rounded-lg border-2 text-left transition-all
                ${selectedFormats.includes(format)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <div className="flex items-start space-x-3">
                <Icon className={`w-6 h-6 ${
                  selectedFormats.includes(format)
                    ? 'text-blue-500'
                    : 'text-gray-400'
                }`} />
                <div>
                  <p className="font-medium text-gray-800">{label}</p>
                  <p className="text-sm text-gray-500">{description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleExport}
        disabled={selectedFormats.length === 0 || isExporting}
        className={`
          flex items-center justify-center w-full py-3 px-4 rounded-lg
          font-medium text-white
          ${selectedFormats.length === 0 || isExporting
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-green-600 hover:bg-green-700'
          }
        `}
      >
        {isExporting ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Generating Exports...
          </>
        ) : (
          <>
            <Download className="w-5 h-5 mr-2" />
            Export {selectedFormats.length} Format{selectedFormats.length > 1 ? 's' : ''}
          </>
        )}
      </button>
    </div>
  );
}
```

---

## 9. Dependencies

### 9.1 New Python Dependencies

```toml
# Add to pyproject.toml

[project.optional-dependencies]
docgen = [
    # PDF Generation
    "weasyprint>=60.0",
    "jinja2>=3.1.0",

    # Excel Generation
    "openpyxl>=3.1.0",

    # Word Generation
    "python-docx>=1.1.0",

    # CSV/XML
    "lxml>=5.0.0",

    # OCR (Azure Document Intelligence)
    "azure-ai-formrecognizer>=3.3.0",

    # Image Processing
    "pillow>=10.0.0",

    # File Handling
    "python-magic>=0.4.27",
    "aiofiles>=23.0.0",
]
```

### 9.2 New Frontend Dependencies

```json
// Add to package.json

{
  "dependencies": {
    "react-dropzone": "^14.2.3",
    "@tanstack/react-table": "^8.11.0",
    "file-saver": "^2.0.5"
  },
  "devDependencies": {
    "@types/file-saver": "^2.0.7"
  }
}
```

---

## 10. Configuration

### 10.1 Environment Variables

```bash
# DocGen Service Configuration

# Service
DOCGEN_PORT=8007
DOCGEN_HOST=0.0.0.0

# AI Provider (same as other services)
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your-key
CLAUDE_MODEL=claude-sonnet-4-20250514

# Azure Document Intelligence (OCR)
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-instance.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your-key

# Storage
STORAGE_TYPE=azure  # azure | local
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_STORAGE_CONTAINER=docgen-documents

# Export Settings
EXPORT_TEMP_DIR=/tmp/docgen-exports
EXPORT_URL_EXPIRY_HOURS=24

# Company Branding
COMPANY_NAME=Pet Insurance Co.
COMPANY_LOGO_URL=https://your-cdn.com/logo.png
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create WS7 service skeleton
- [ ] Implement document upload endpoints
- [ ] Set up Azure Blob Storage integration
- [ ] Create basic data models

### Phase 2: Processing Pipeline (Week 2-3)
- [ ] Implement Ingest Agent
- [ ] Implement Extract Agent with OCR
- [ ] Implement Enrich Agent
- [ ] Implement Validate Agent
- [ ] Set up WebSocket streaming

### Phase 3: Export System (Week 3-4)
- [ ] Implement PDF exporter with templates
- [ ] Implement Excel exporter
- [ ] Implement Word exporter
- [ ] Implement CSV/JSON exporters
- [ ] Create template system

### Phase 4: Frontend Integration (Week 4-5)
- [ ] Build document upload UI
- [ ] Build processing status UI
- [ ] Build export selection UI
- [ ] Integrate with existing portal

### Phase 5: Testing & Polish (Week 5-6)
- [ ] Unit tests for all agents
- [ ] Integration tests
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Document Processing Time | < 30 seconds per document |
| OCR Accuracy | > 95% for standard documents |
| Extraction Accuracy | > 90% field accuracy |
| Export Generation Time | < 5 seconds per format |
| Supported File Types | 8+ formats |
| Export Formats | 6 formats (PDF, Excel, Word, CSV, JSON, HTML) |

---

## 13. Security Considerations

1. **File Validation**: Validate file types, sizes, and scan for malware
2. **Access Control**: Ensure users can only access their own claims
3. **Data Encryption**: Encrypt documents at rest and in transit
4. **Audit Logging**: Log all document operations
5. **PII Handling**: Mask sensitive data in exports as needed
6. **Signed URLs**: Use time-limited signed URLs for downloads

---

## 14. Future Enhancements

1. **Batch Processing**: Process multiple claims in parallel
2. **Template Editor**: UI for customizing export templates
3. **OCR Training**: Custom models for specific document types
4. **Multi-language**: Support for documents in multiple languages
5. **E-signature**: Integration with DocuSign/Adobe Sign
6. **Archive**: Long-term document archival with compliance
