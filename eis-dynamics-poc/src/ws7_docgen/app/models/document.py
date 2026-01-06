"""Document models for DocGen service."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""
    VET_INVOICE = "vet_invoice"
    MEDICAL_RECEIPT = "medical_receipt"
    LAB_RESULTS = "lab_results"
    POLICE_REPORT = "police_report"
    PHOTO_EVIDENCE = "photo_evidence"
    PRESCRIPTION = "prescription"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Processing status for batches."""
    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    MAPPING = "mapping"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    WORD = "docx"
    CSV = "csv"


class UploadedDocument(BaseModel):
    """Single uploaded document."""
    id: UUID = Field(default_factory=uuid4)
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    blob_url: Optional[str] = None
    local_path: Optional[str] = None
    document_type: Optional[DocumentType] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_hash: str = ""  # SHA-256 for deduplication
    from_zip: bool = False
    zip_source: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class ExtractedLineItem(BaseModel):
    """Line item extracted from invoice/receipt."""
    line_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    description: str
    diagnosis_code: Optional[str] = None
    procedure_code: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    service_date: Optional[datetime] = None
    is_covered: Optional[bool] = None
    denial_reason: Optional[str] = None
    confidence: float = 0.0

    class Config:
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat() if v else None,
        }


class ExtractionResult(BaseModel):
    """Result of document extraction."""
    document_id: UUID
    document_type: DocumentType = DocumentType.OTHER

    # Provider Info
    provider_name: Optional[str] = None
    provider_address: Optional[str] = None
    provider_phone: Optional[str] = None
    provider_license: Optional[str] = None
    provider_id: Optional[str] = None
    is_in_network: Optional[bool] = None

    # Patient/Pet Info
    patient_name: Optional[str] = None
    pet_species: Optional[str] = None
    pet_breed: Optional[str] = None
    pet_age: Optional[str] = None
    owner_name: Optional[str] = None

    # Service Info
    service_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    diagnosis: Optional[str] = None
    diagnosis_code: Optional[str] = None
    treatment_notes: Optional[str] = None

    # Financial
    line_items: List[ExtractedLineItem] = []
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
    payment_method: Optional[str] = None

    # Flags
    is_emergency: bool = False
    is_follow_up: bool = False

    # Metadata
    raw_text: Optional[str] = None
    confidence_score: float = 0.0
    extraction_model: str = "claude-sonnet-4"
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat() if v else None,
        }


class ValidationIssue(BaseModel):
    """Validation issue found during processing."""
    issue_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    severity: str  # critical, error, warning, info
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None
    source: str = "validation"  # validation, fraud, billing


class FraudIndicator(BaseModel):
    """Fraud indicator detected."""
    indicator_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    indicator: str
    score_impact: float
    confidence: float
    description: str
    pattern_type: str  # chronic_gaming, provider_collusion, staged_timing, etc.


class BillingCalculation(BaseModel):
    """Billing calculation results."""
    claim_amount: Decimal = Decimal("0.00")
    deductible_remaining: Decimal = Decimal("0.00")
    deductible_applied: Decimal = Decimal("0.00")
    amount_after_deductible: Decimal = Decimal("0.00")
    reimbursement_percentage: int = 80
    covered_amount: Decimal = Decimal("0.00")
    annual_limit_remaining: Decimal = Decimal("10000.00")
    final_payout: Decimal = Decimal("0.00")
    out_of_network_reduction: Decimal = Decimal("0.00")
    customer_responsibility: Decimal = Decimal("0.00")
    explanation: str = ""

    class Config:
        json_encoders = {
            Decimal: float,
        }


class AgentStep(BaseModel):
    """Single step in agent processing."""
    step_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    step_type: str  # check_policy, check_duplicate, extract_data, validate_fields, calculate_billing, submit
    status: str = "pending"  # pending, running, completed, failed
    message: str
    details: Optional[str] = None
    result: Optional[str] = None  # pass, fail, warning
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessedBatch(BaseModel):
    """Complete processed batch with all documents."""
    batch_id: UUID = Field(default_factory=uuid4)
    claim_number: Optional[str] = None
    policy_number: Optional[str] = None

    # Customer/Pet context (from PetInsure360 upload)
    customer_id: Optional[str] = None
    pet_id: Optional[str] = None
    pet_name: Optional[str] = None
    policy_id: Optional[str] = None

    # Source claim data (from PetInsure360 portal)
    claim_data: Optional[Dict[str, Any]] = None

    # Documents
    documents: List[UploadedDocument] = []
    extractions: Dict[str, ExtractionResult] = {}  # doc_id -> extraction

    # Aggregated Claim Data
    mapped_claim: Optional[Dict[str, Any]] = None

    # Validation
    validation_issues: List[ValidationIssue] = []
    is_valid: bool = True

    # Fraud Analysis
    fraud_score: float = 0.0
    fraud_indicators: List[FraudIndicator] = []
    risk_level: str = "low"  # low, medium, high, critical

    # Billing
    billing: Optional[BillingCalculation] = None
    total_claim_amount: Optional[Decimal] = None
    estimated_payout: Optional[Decimal] = None

    # AI Decision
    ai_decision: Optional[str] = None  # auto_approve, manual_review, deny, investigation
    ai_reasoning: Optional[str] = None
    ai_confidence: float = 0.0

    # Agent Processing Steps - for real-time tracking
    agent_steps: List[AgentStep] = []

    # Status
    status: ProcessingStatus = ProcessingStatus.PENDING
    current_stage: Optional[str] = None
    progress: float = 0.0  # 0-100

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None

    # Errors
    error: Optional[str] = None
    error_stage: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat() if v else None,
        }


class ExportResult(BaseModel):
    """Result of export generation."""
    export_id: UUID = Field(default_factory=uuid4)
    batch_id: UUID
    format: ExportFormat
    template: str = "default"
    filename: str
    blob_url: Optional[str] = None
    local_path: Optional[str] = None
    file_size: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None,
        }
