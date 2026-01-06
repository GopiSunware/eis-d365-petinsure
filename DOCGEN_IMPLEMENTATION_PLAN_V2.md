# DocGen Feature Implementation Plan v2
## EIS POC - Document Generation & Export System

---

## 1. Executive Summary

**DocGen** enables users to:
1. **Upload** documents/receipts (including ZIP archives) for insurance claims
2. **Process** them through an AI-powered agent pipeline
3. **Auto-populate** all claim fields from extracted data
4. **Export** to PDF, Word, and CSV formats

**Key Principle**: Self-contained module with minimal main application changes.

---

## 2. Folder Structure & Separation

### 2.1 New Service Location

```
eis-dynamics-poc/
├── src/
│   ├── ws7_docgen/                    ← NEW SELF-CONTAINED SERVICE
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # FastAPI app (Port 8007)
│   │   │   ├── config.py              # Service config
│   │   │   │
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── upload.py          # Upload endpoints
│   │   │   │   ├── processing.py      # Processing endpoints
│   │   │   │   └── export.py          # Export endpoints
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── document.py        # Document models
│   │   │   │   ├── extraction.py      # Extraction result models
│   │   │   │   └── export.py          # Export models
│   │   │   │
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_agent.py
│   │   │   │   ├── ingest_agent.py    # File handling + ZIP
│   │   │   │   ├── extract_agent.py   # OCR + AI extraction
│   │   │   │   ├── mapper_agent.py    # Map to claim fields
│   │   │   │   ├── validate_agent.py  # Fraud + billing validation
│   │   │   │   └── export_agent.py    # Generate exports
│   │   │   │
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── storage_service.py # Blob storage
│   │   │   │   ├── ocr_service.py     # Azure Doc Intelligence
│   │   │   │   ├── zip_service.py     # ZIP extraction
│   │   │   │   └── claim_mapper.py    # Map to existing claim models
│   │   │   │
│   │   │   ├── exporters/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_exporter.py
│   │   │   │   ├── pdf_exporter.py    # PDF generation
│   │   │   │   ├── word_exporter.py   # Word generation
│   │   │   │   └── csv_exporter.py    # CSV generation
│   │   │   │
│   │   │   ├── templates/
│   │   │   │   ├── pdf/
│   │   │   │   │   ├── claim_summary.html
│   │   │   │   │   ├── fraud_report.html
│   │   │   │   │   ├── billing_summary.html
│   │   │   │   │   └── styles.css
│   │   │   │   └── word/
│   │   │   │       ├── claim_letter.docx
│   │   │   │       └── adjuster_notes.docx
│   │   │   │
│   │   │   ├── prompts/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── extraction.py      # Document extraction prompts
│   │   │   │   ├── classification.py  # Document type classification
│   │   │   │   └── mapping.py         # Field mapping prompts
│   │   │   │
│   │   │   └── orchestration/
│   │   │       ├── __init__.py
│   │   │       ├── pipeline.py        # Pipeline orchestration
│   │   │       └── event_publisher.py # WebSocket events
│   │   │
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_upload.py
│   │   │   ├── test_extraction.py
│   │   │   ├── test_mapping.py
│   │   │   └── test_export.py
│   │   │
│   │   ├── requirements.txt           # DocGen-specific deps
│   │   └── Dockerfile
│   │
│   ├── shared/                        # EXISTING - minimal changes
│   │   ├── eis_common/                # REUSE - no changes
│   │   └── claims_data_api/           # REUSE - no changes
│   │
│   ├── ws2_ai_claims/                 # EXISTING - no changes
│   ├── ws3_integration/               # EXISTING - no changes
│   ├── ws4_agent_portal/              # EXISTING - minimal changes (see section 3)
│   ├── ws5_rating_engine/             # EXISTING - no changes
│   └── ws6_agent_pipeline/            # EXISTING - no changes
```

---

## 3. Main Application Changes (MINIMAL)

### 3.1 Changes Required

| File | Change Type | Description |
|------|-------------|-------------|
| `ws4_agent_portal/app/docgen/*` | **ADD** | New frontend pages for DocGen UI |
| `ws4_agent_portal/components/docgen/*` | **ADD** | New React components |
| `ws4_agent_portal/lib/docgen-api.ts` | **ADD** | New API client for DocGen |
| `ws4_agent_portal/app/layout.tsx` | **MODIFY** | Add DocGen nav link (1 line) |
| `run.sh` | **MODIFY** | Add WS7 startup command (optional) |
| `pyproject.toml` | **MODIFY** | Add docgen extras (optional) |

### 3.2 Detailed Changes

#### 3.2.1 Frontend Navigation (1 line change)
```tsx
// ws4_agent_portal/app/layout.tsx
// ADD to navigation items array:
{ name: 'DocGen', href: '/docgen', icon: FileText }
```

#### 3.2.2 New Frontend Pages (ADD - no existing code modified)
```
ws4_agent_portal/
├── app/
│   └── docgen/                        ← NEW FOLDER
│       ├── page.tsx                   # DocGen dashboard
│       ├── upload/
│       │   └── page.tsx               # Upload page
│       ├── [batchId]/
│       │   ├── page.tsx               # Batch details
│       │   └── export/
│       │       └── page.tsx           # Export page
│       └── layout.tsx
├── components/
│   └── docgen/                        ← NEW FOLDER
│       ├── DocumentUploader.tsx
│       ├── ProcessingStatus.tsx
│       ├── ExtractionPreview.tsx
│       ├── ClaimFieldMapper.tsx
│       └── ExportSelector.tsx
└── lib/
    └── docgen-api.ts                  ← NEW FILE
```

#### 3.2.3 Run Script (Optional)
```bash
# run.sh - ADD at end:
# Terminal 7: DocGen Service
echo "Starting DocGen Service on port 8007..."
cd src/ws7_docgen && uvicorn app.main:app --reload --port 8007
```

### 3.3 No Changes Required To

| Component | Reason |
|-----------|--------|
| `eis_common/*` | Reuse existing models via import |
| `claims_data_api/*` | Reuse existing services via HTTP calls |
| `ws2_ai_claims/*` | Independent service |
| `ws3_integration/*` | Independent service |
| `ws5_rating_engine/*` | Independent service |
| `ws6_agent_pipeline/*` | Independent service |

---

## 4. Alignment with Existing Use Cases

### 4.1 Claim Field Mapping

DocGen will extract and map to **ALL** existing claim fields:

#### From `eis_common/models/claim.py`:
```python
CLAIM_FIELD_MAPPING = {
    # Core Fields
    "claim_number": "auto_generated",
    "policy_id": "extracted_or_lookup",
    "date_of_loss": "extracted_from_document",
    "date_reported": "current_timestamp",
    "status": "fnol_received",
    "loss_description": "ai_generated_summary",
    "reserve_amount": "calculated_from_line_items",

    # AI-Generated Fields
    "severity": "ai_assessed",           # minor/moderate/severe
    "fraud_score": "fraud_analysis",     # 0.0-1.0
    "fraud_indicators": "fraud_analysis",
    "ai_recommendation": "ai_generated",

    # Documents
    "documents": "uploaded_files",
}
```

#### From `claims_data_api/models/schemas.py`:
```python
COMPREHENSIVE_FIELD_MAPPING = {
    # Identifiers
    "claim_id": "auto_generated",
    "pet_id": "policy_lookup",
    "customer_id": "policy_lookup",
    "provider_id": "extracted_from_invoice",

    # Classification
    "claim_type": "ai_classified",       # accident/illness/wellness
    "claim_category": "ai_classified",   # ClaimCategory enum
    "diagnosis_code": "extracted",       # ICD-10-VET
    "diagnosis_description": "extracted",

    # Service Details
    "service_date": "extracted",
    "submitted_date": "current_date",
    "treatment_notes": "extracted",

    # Line Items (from invoice)
    "line_items": [
        {
            "line_id": "auto_generated",
            "description": "extracted",
            "diagnosis_code": "extracted",
            "procedure_code": "extracted",
            "quantity": "extracted",
            "unit_price": "extracted",
            "total_amount": "calculated",
            "is_covered": "coverage_check",
            "denial_reason": "validation",
        }
    ],

    # Financials
    "claim_amount": "sum_of_line_items",
    "deductible_applied": "billing_calculation",
    "covered_amount": "billing_calculation",
    "paid_amount": "initial_zero",

    # Flags
    "is_emergency": "ai_detected",
    "is_recurring": "history_check",

    # AI Analysis
    "ai_decision": "pipeline_result",
    "ai_reasoning": "pipeline_result",
    "ai_risk_score": "fraud_analysis",
    "ai_quality_score": "validation_result",
}
```

### 4.2 Fraud Detection Integration

DocGen will detect fraud patterns from `fraud_service.py`:

| Pattern | Detection Method |
|---------|------------------|
| **Chronic Condition Gaming** | Check if accident claim matches chronic diagnosis patterns |
| **Provider Collusion** | Flag exclusive provider use, out-of-network high claims |
| **Staged Timing** | Compare service date to policy waiting period |
| **Round Amounts** | Flag claims ending in 00/500 |
| **High Velocity** | Check claim frequency (4+ in 90 days) |
| **Duplicates** | Match date + diagnosis + amount patterns |

```python
# Fraud score thresholds (from existing code)
FRAUD_THRESHOLDS = {
    "low": (0, 15),        # Auto-approve eligible
    "medium": (15, 30),    # Enhanced review
    "high": (30, 50),      # Manual review
    "critical": (50, 100), # Investigation
}
```

### 4.3 Billing Validation Integration

DocGen will apply billing rules from `billing_service.py`:

```python
BILLING_CALCULATIONS = {
    "annual_deductible": 250.00,
    "reimbursement_percentage": 0.80,      # 80% standard
    "out_of_network_reduction": 0.30,      # 30% reduction
    "annual_limit": 10000.00,
}

BILLING_OUTPUTS = {
    "deductible_remaining": "calculated",
    "deductible_applied": "calculated",
    "amount_after_deductible": "calculated",
    "reimbursement_percentage": "policy_lookup",
    "covered_amount": "calculated",
    "annual_limit_remaining": "calculated",
    "final_payout": "calculated",
    "explanation": "generated_text",
}
```

### 4.4 Validation Scenarios Supported

DocGen will detect validation issues from `validation_scenarios.json`:

| Category | Issues Detected |
|----------|-----------------|
| **Diagnosis-Treatment Mismatch** | Dental billed for orthopedic, MRI for allergies |
| **Document Consistency** | Pet name mismatch, amount mismatch, date mismatch |
| **Missing Prerequisites** | Surgery without bloodwork, chemo without staging |
| **License Issues** | Expired provider license, missing DEA for controlled substances |

---

## 5. Supported Document Types

### 5.1 Individual Files

| Type | Extensions | OCR | Special Processing |
|------|------------|-----|-------------------|
| Vet Invoice | `.pdf`, `.jpg`, `.png` | Yes | Line item extraction |
| Medical Receipt | `.pdf`, `.jpg`, `.png` | Yes | Treatment code extraction |
| Lab Results | `.pdf` | Yes | Test result extraction |
| Police Report | `.pdf` | Optional | Incident detail extraction |
| Photo Evidence | `.jpg`, `.png`, `.heic` | No | Damage assessment |
| Prescription | `.pdf`, `.jpg` | Yes | Medication extraction |

### 5.2 ZIP Archive Support

```python
# ZIP Processing Flow
ZIP_PROCESSING = {
    "max_size": "50MB",
    "max_files": 20,
    "supported_internal_types": [
        ".pdf", ".jpg", ".jpeg", ".png", ".heic", ".doc", ".docx"
    ],
    "extraction_path": "/tmp/docgen/extract/{batch_id}/",
    "processing": "parallel",  # Process extracted files in parallel
}
```

**ZIP Handling:**
1. Upload ZIP file
2. Extract to temp directory
3. Validate each file (type, size, virus scan)
4. Process each file through pipeline
5. Aggregate results into single batch
6. Clean up temp files

---

## 6. Export Formats

### 6.1 PDF Export

**Use Cases:**
- Formal claim summary reports
- Fraud analysis reports
- Customer-facing claim letters
- Adjuster review documents

**Templates:**
```
templates/pdf/
├── claim_summary.html       # Complete claim overview
├── fraud_report.html        # Fraud analysis with indicators
├── billing_summary.html     # Financial breakdown
├── validation_report.html   # Issues and warnings
└── styles.css               # Shared styling
```

**PDF Content Sections:**
1. **Header**: Company logo, claim number, date
2. **Claim Summary**: Policy holder, pet info, claim type
3. **Document Analysis**: Extracted data from each document
4. **Line Items**: Itemized expenses with coverage status
5. **Financial Summary**: Deductible, coverage, payout
6. **Fraud Assessment**: Risk score, indicators, recommendation
7. **Validation Issues**: Warnings, errors, required actions
8. **AI Recommendation**: Final decision with reasoning

### 6.2 Word Export

**Use Cases:**
- Editable claim letters
- Adjuster notes (internal)
- Customer correspondence
- Appeals documentation

**Templates:**
```
templates/word/
├── claim_letter.docx        # Customer-facing letter
├── adjuster_notes.docx      # Internal review document
├── denial_letter.docx       # Claim denial explanation
└── approval_letter.docx     # Claim approval notification
```

**Word Features:**
- Editable fields for customization
- Mail merge compatible
- Company letterhead integration
- Signature blocks

### 6.3 CSV Export

**Use Cases:**
- Data analysis and reporting
- Import to other systems
- Bulk processing
- Audit trails

**CSV Schemas:**
```python
CSV_EXPORTS = {
    "claim_summary": [
        "claim_number", "policy_id", "customer_name", "pet_name",
        "claim_type", "service_date", "claim_amount", "covered_amount",
        "fraud_score", "status", "ai_decision"
    ],
    "line_items": [
        "claim_number", "line_id", "description", "diagnosis_code",
        "procedure_code", "quantity", "unit_price", "total_amount",
        "is_covered", "denial_reason"
    ],
    "validation_issues": [
        "claim_number", "issue_type", "severity", "field",
        "message", "suggestion"
    ],
    "fraud_indicators": [
        "claim_number", "indicator", "score_impact", "confidence",
        "description"
    ],
}
```

---

## 7. Data Models

### 7.1 Document Models

```python
# src/ws7_docgen/app/models/document.py

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


class DocumentType(str, Enum):
    VET_INVOICE = "vet_invoice"
    MEDICAL_RECEIPT = "medical_receipt"
    LAB_RESULTS = "lab_results"
    POLICE_REPORT = "police_report"
    PHOTO_EVIDENCE = "photo_evidence"
    PRESCRIPTION = "prescription"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    MAPPING = "mapping"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    PDF = "pdf"
    WORD = "docx"
    CSV = "csv"


class UploadedDocument(BaseModel):
    """Single uploaded document."""
    id: UUID = Field(default_factory=uuid4)
    filename: str
    content_type: str
    file_size: int
    blob_url: str
    document_type: Optional[DocumentType] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_hash: str  # SHA-256 for deduplication
    from_zip: bool = False
    zip_source: Optional[str] = None


class ExtractedLineItem(BaseModel):
    """Line item extracted from invoice/receipt."""
    description: str
    diagnosis_code: Optional[str] = None
    procedure_code: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal
    total_amount: Decimal
    service_date: Optional[datetime] = None
    confidence: float = 0.0


class ExtractionResult(BaseModel):
    """Result of document extraction."""
    document_id: UUID
    document_type: DocumentType

    # Provider Info
    provider_name: Optional[str] = None
    provider_address: Optional[str] = None
    provider_phone: Optional[str] = None
    provider_license: Optional[str] = None
    is_in_network: Optional[bool] = None

    # Patient/Pet Info
    patient_name: Optional[str] = None
    pet_species: Optional[str] = None
    pet_breed: Optional[str] = None

    # Service Info
    service_date: Optional[datetime] = None
    diagnosis: Optional[str] = None
    diagnosis_code: Optional[str] = None
    treatment_notes: Optional[str] = None

    # Financial
    line_items: List[ExtractedLineItem] = []
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None

    # Flags
    is_emergency: bool = False

    # Metadata
    raw_text: Optional[str] = None
    confidence_score: float = 0.0
    extraction_model: str = "claude-sonnet-4"


class ValidationIssue(BaseModel):
    """Validation issue found during processing."""
    severity: str  # critical, error, warning, info
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class FraudIndicator(BaseModel):
    """Fraud indicator detected."""
    indicator: str
    score_impact: float
    confidence: float
    description: str
    pattern_type: str  # chronic_gaming, provider_collusion, staged_timing, etc.


class ProcessedBatch(BaseModel):
    """Complete processed batch with all documents."""
    batch_id: UUID = Field(default_factory=uuid4)
    claim_number: Optional[str] = None  # Generated or linked

    # Documents
    documents: List[UploadedDocument] = []
    extractions: Dict[str, ExtractionResult] = {}  # doc_id -> extraction

    # Aggregated Claim Data (ready to populate claim)
    mapped_claim: Optional[Dict[str, Any]] = None

    # Validation
    validation_issues: List[ValidationIssue] = []
    is_valid: bool = True

    # Fraud Analysis
    fraud_score: float = 0.0
    fraud_indicators: List[FraudIndicator] = []
    risk_level: str = "low"

    # Billing
    total_claim_amount: Optional[Decimal] = None
    deductible_applied: Optional[Decimal] = None
    covered_amount: Optional[Decimal] = None
    estimated_payout: Optional[Decimal] = None

    # AI Decision
    ai_decision: Optional[str] = None  # auto_approve, manual_review, deny
    ai_reasoning: Optional[str] = None

    # Status
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ExportResult(BaseModel):
    """Result of export generation."""
    export_id: UUID = Field(default_factory=uuid4)
    batch_id: UUID
    format: ExportFormat
    filename: str
    blob_url: str
    file_size: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 7.2 API Models

```python
# src/ws7_docgen/app/models/api.py

class UploadRequest(BaseModel):
    """Upload request metadata."""
    claim_number: Optional[str] = None  # Link to existing claim
    policy_number: Optional[str] = None  # For new claims
    document_type: Optional[DocumentType] = None


class UploadResponse(BaseModel):
    """Response after upload."""
    batch_id: UUID
    documents_count: int
    documents: List[UploadedDocument]
    status: str


class ProcessingStatusResponse(BaseModel):
    """Current processing status."""
    batch_id: UUID
    status: ProcessingStatus
    progress: float  # 0-100
    documents_processed: int
    documents_total: int
    current_stage: Optional[str] = None


class ExportRequest(BaseModel):
    """Export generation request."""
    batch_id: UUID
    formats: List[ExportFormat]
    template: Optional[str] = None
    include_raw_data: bool = False


class ExportResponse(BaseModel):
    """Export generation response."""
    batch_id: UUID
    exports: List[ExportResult]
    download_urls: Dict[str, str]


class ClaimPopulateRequest(BaseModel):
    """Request to populate claim with extracted data."""
    batch_id: UUID
    claim_number: Optional[str] = None  # Existing claim to update
    create_new: bool = False  # Create new claim if not exists
    auto_submit: bool = False  # Auto-submit to pipeline


class ClaimPopulateResponse(BaseModel):
    """Response after claim population."""
    claim_number: str
    fields_populated: List[str]
    fields_requiring_review: List[str]
    validation_warnings: List[str]
    next_steps: List[str]
```

---

## 8. API Endpoints

### 8.1 Upload Endpoints

```yaml
POST /api/v1/docgen/upload
  Description: Upload documents (single, multiple, or ZIP)
  Content-Type: multipart/form-data
  Body:
    - files: File[] (required)
    - claim_number: string (optional)
    - policy_number: string (optional)
    - document_type: string (optional)
  Response: UploadResponse

POST /api/v1/docgen/upload/url
  Description: Upload from existing blob URLs
  Body:
    - document_urls: string[]
    - claim_number: string (optional)
  Response: UploadResponse
```

### 8.2 Processing Endpoints

```yaml
POST /api/v1/docgen/process/{batch_id}
  Description: Start processing uploaded documents
  Query:
    - async: boolean (default: true)
  Response: ProcessingStatusResponse

GET /api/v1/docgen/status/{batch_id}
  Description: Get processing status
  Response: ProcessingStatusResponse

GET /api/v1/docgen/result/{batch_id}
  Description: Get complete processing results
  Response: ProcessedBatch

WS /ws/docgen/{batch_id}
  Description: Real-time processing updates
  Events: progress, extraction_complete, validation_complete, error
```

### 8.3 Export Endpoints

```yaml
POST /api/v1/docgen/export
  Description: Generate exports
  Body: ExportRequest
  Response: ExportResponse

GET /api/v1/docgen/export/{export_id}/download
  Description: Download exported file
  Response: File stream

GET /api/v1/docgen/templates
  Description: List available templates
  Response: List of template names and descriptions
```

### 8.4 Claim Integration Endpoints

```yaml
POST /api/v1/docgen/populate-claim
  Description: Populate claim with extracted data
  Body: ClaimPopulateRequest
  Response: ClaimPopulateResponse

GET /api/v1/docgen/preview-claim/{batch_id}
  Description: Preview mapped claim data before population
  Response: Mapped claim object with confidence scores
```

---

## 9. Processing Pipeline

### 9.1 Four-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOCGEN PROCESSING PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Stage 1: INGEST AGENT                                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ • Receive files (single, multiple, ZIP)                        │    │
│  │ • Extract ZIP contents to temp directory                       │    │
│  │ • Validate file types and sizes                                │    │
│  │ • Calculate file hashes (deduplication)                        │    │
│  │ • Upload to Azure Blob Storage                                 │    │
│  │ • Create batch record                                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 2: EXTRACT AGENT                                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ • OCR via Azure Document Intelligence                          │    │
│  │ • AI document classification (vet_invoice, receipt, etc.)      │    │
│  │ • Field extraction with Claude/OpenAI:                         │    │
│  │   - Provider info (name, address, license)                     │    │
│  │   - Pet/patient info                                           │    │
│  │   - Service details (date, diagnosis, treatment)               │    │
│  │   - Line items (description, codes, amounts)                   │    │
│  │   - Totals and payment info                                    │    │
│  │ • Confidence scoring per field                                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 3: MAPPER AGENT                                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ • Map extracted data to claim model fields                     │    │
│  │ • Cross-reference with policy data (customer, pet, coverage)   │    │
│  │ • Lookup provider in network database                          │    │
│  │ • Normalize diagnosis codes (ICD-10-VET)                       │    │
│  │ • Calculate billing:                                           │    │
│  │   - Check deductible status                                    │    │
│  │   - Apply reimbursement percentage                             │    │
│  │   - Check annual limits                                        │    │
│  │   - Calculate estimated payout                                 │    │
│  │ • Aggregate multi-document data                                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    │                                    │
│                                    ▼                                    │
│  Stage 4: VALIDATE AGENT                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ • Fraud detection (5 patterns from fraud_service.py):          │    │
│  │   - Chronic condition gaming                                   │    │
│  │   - Provider collusion                                         │    │
│  │   - Staged timing                                              │    │
│  │   - Claim characteristics                                      │    │
│  │   - Duplicate detection                                        │    │
│  │ • Validation checks (from validation_scenarios.json):          │    │
│  │   - Diagnosis-treatment mismatch                               │    │
│  │   - Document consistency                                       │    │
│  │   - Missing prerequisites                                      │    │
│  │   - License verification                                       │    │
│  │ • Generate AI recommendation                                   │    │
│  │ • Determine risk level and next steps                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Pipeline Output → Claim Field Population

```python
# After pipeline completes, mapped_claim contains:
{
    # From Extraction
    "claim_number": "CLM-2024-XXXXX",  # Auto-generated
    "policy_id": "POL-12345",          # From policy lookup
    "date_of_loss": "2024-01-15",      # Extracted service date
    "loss_description": "AI-generated summary of treatment",

    # Classification
    "claim_type": "illness",           # AI classified
    "claim_category": "gastrointestinal",
    "diagnosis_code": "K29.0",
    "diagnosis_description": "Acute gastritis",

    # Pet/Customer (from policy)
    "pet_id": "PET-67890",
    "customer_id": "CUST-11111",
    "pet_name": "Max",
    "pet_species": "Dog",
    "pet_breed": "Golden Retriever",

    # Provider
    "provider_id": "PROV-22222",
    "provider_name": "Happy Paws Vet Clinic",
    "is_in_network": True,

    # Line Items
    "line_items": [
        {
            "description": "Office Visit - Emergency",
            "procedure_code": "99281",
            "quantity": 1,
            "unit_price": 150.00,
            "total_amount": 150.00,
            "is_covered": True,
        },
        # ... more items
    ],

    # Financials
    "claim_amount": 1250.00,
    "deductible_applied": 125.00,
    "covered_amount": 900.00,
    "estimated_payout": 900.00,

    # Flags
    "is_emergency": True,
    "is_recurring": False,

    # AI Analysis
    "severity": "moderate",
    "fraud_score": 0.12,
    "fraud_indicators": [],
    "ai_decision": "auto_approve",
    "ai_reasoning": "Low fraud risk, valid documentation, within coverage limits",
    "ai_risk_score": 0.12,
    "ai_quality_score": 0.95,

    # Documents
    "documents": [
        {
            "document_id": "DOC-UUID",
            "document_type": "vet_invoice",
            "filename": "invoice_2024_01_15.pdf",
            "blob_url": "https://storage.../",
            "verified": True,
        }
    ],
}
```

---

## 10. Dependencies

### 10.1 WS7 DocGen Requirements

```txt
# src/ws7_docgen/requirements.txt

# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# AI
anthropic>=0.18.0
openai>=1.10.0

# OCR
azure-ai-formrecognizer>=3.3.0

# Storage
azure-storage-blob>=12.19.0
aiofiles>=23.0.0

# PDF Generation
weasyprint>=60.0
jinja2>=3.1.0

# Word Generation
python-docx>=1.1.0

# File Handling
python-magic>=0.4.27
pillow>=10.0.0

# Async HTTP
httpx>=0.26.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

### 10.2 Frontend Dependencies (Add to ws4_agent_portal)

```json
{
  "dependencies": {
    "react-dropzone": "^14.2.3",
    "file-saver": "^2.0.5",
    "jszip": "^3.10.1"
  }
}
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Service Setup)
- [ ] Create `ws7_docgen` folder structure
- [ ] Set up FastAPI application
- [ ] Implement storage service (Azure Blob)
- [ ] Implement ZIP extraction service
- [ ] Create basic upload endpoints
- [ ] Add health check and configuration

### Phase 2: Extraction Pipeline
- [ ] Implement OCR service (Azure Document Intelligence)
- [ ] Create Ingest Agent (file handling, ZIP extraction)
- [ ] Create Extract Agent (AI-powered field extraction)
- [ ] Create Mapper Agent (claim field mapping)
- [ ] Create Validate Agent (fraud + billing checks)
- [ ] Add WebSocket for real-time updates

### Phase 3: Export System
- [ ] Implement PDF exporter with templates
- [ ] Implement Word exporter with templates
- [ ] Implement CSV exporter with schemas
- [ ] Create export endpoints
- [ ] Add download functionality

### Phase 4: Frontend Integration
- [ ] Add navigation link to layout (1 line change)
- [ ] Create DocGen pages (upload, status, export)
- [ ] Create React components
- [ ] Implement docgen-api.ts client
- [ ] Add real-time status updates

### Phase 5: Testing & Integration
- [ ] Unit tests for all agents
- [ ] Integration tests with existing services
- [ ] End-to-end testing
- [ ] Test with 20 demo scenarios
- [ ] Performance optimization

---

## 12. Configuration

### 12.1 Environment Variables

```bash
# DocGen Service
DOCGEN_PORT=8007
DOCGEN_HOST=0.0.0.0

# AI (reuse existing)
AI_PROVIDER=claude
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
CLAUDE_MODEL=claude-sonnet-4-20250514

# OCR
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-instance.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your-key

# Storage (reuse existing)
AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING}
DOCGEN_STORAGE_CONTAINER=docgen-uploads
DOCGEN_EXPORT_CONTAINER=docgen-exports

# ZIP Processing
DOCGEN_MAX_ZIP_SIZE_MB=50
DOCGEN_MAX_FILES_PER_ZIP=20
DOCGEN_TEMP_DIR=/tmp/docgen

# Export
DOCGEN_EXPORT_URL_EXPIRY_HOURS=24

# Internal Service URLs (for cross-service calls)
CLAIMS_DATA_API_URL=http://localhost:8000
WS6_PIPELINE_URL=http://localhost:8006
```

---

## 13. Summary: Main Application Impact

### Changes Made to Main Application

| Location | Change | Impact |
|----------|--------|--------|
| `ws4_agent_portal/app/layout.tsx` | Add nav link | 1 line |
| `ws4_agent_portal/app/docgen/*` | New pages | **ADD** (no existing code modified) |
| `ws4_agent_portal/components/docgen/*` | New components | **ADD** (no existing code modified) |
| `ws4_agent_portal/lib/docgen-api.ts` | New API client | **ADD** (no existing code modified) |
| `run.sh` | Add WS7 startup | 2-3 lines (optional) |

### No Changes Made To

- ✅ `eis_common/*` - Reused via imports
- ✅ `claims_data_api/*` - Reused via HTTP calls
- ✅ `ws2_ai_claims/*` - Independent
- ✅ `ws3_integration/*` - Independent
- ✅ `ws5_rating_engine/*` - Independent
- ✅ `ws6_agent_pipeline/*` - Independent
- ✅ All existing models, services, and business logic

### Integration Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE INTEGRATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WS7 DocGen (NEW)                                               │
│       │                                                          │
│       ├─── HTTP ──→ claims_data_api (read policies, customers)  │
│       │                                                          │
│       ├─── HTTP ──→ ws6_pipeline (submit processed claims)      │
│       │                                                          │
│       └─── Import ─→ eis_common (reuse models)                  │
│                                                                  │
│  WS4 Portal                                                      │
│       │                                                          │
│       └─── HTTP ──→ WS7 DocGen (upload, process, export)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. Next Steps

1. **Review this plan** - Confirm approach and scope
2. **Create folder structure** - Set up ws7_docgen skeleton
3. **Implement Phase 1** - Foundation with upload and storage
4. **Iterate** - Build remaining phases incrementally

Ready to proceed with implementation upon approval.
