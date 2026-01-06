"""
Claim-related Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """Types of pet insurance claims."""
    ACCIDENT = "accident"
    ILLNESS = "illness"
    WELLNESS = "wellness"
    EMERGENCY = "emergency"
    ROUTINE = "routine"


class ClaimStatus(str, Enum):
    """Claim processing status."""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    VALIDATED = "validated"
    ENRICHED = "enriched"
    ANALYZED = "analyzed"
    COMPLETED = "completed"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    ERROR = "error"


class ClaimComplexity(str, Enum):
    """Claim complexity classification."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class PetInfo(BaseModel):
    """Pet information."""
    pet_id: str
    name: str
    species: str = "dog"
    breed: Optional[str] = None
    age_years: Optional[float] = None
    weight_lbs: Optional[float] = None


class PolicyInfo(BaseModel):
    """Policy information."""
    policy_id: str
    policy_number: str
    coverage_type: str = "comprehensive"
    deductible: float = 0.0
    annual_limit: float = 10000.0
    reimbursement_rate: float = 0.8


class ProviderInfo(BaseModel):
    """Veterinary provider information."""
    provider_id: Optional[str] = None
    provider_name: str
    provider_type: str = "veterinary_clinic"
    is_in_network: bool = True
    address: Optional[str] = None


class ClaimData(BaseModel):
    """Raw claim data as submitted."""
    claim_id: str
    policy_id: str
    customer_id: str
    pet_id: Optional[str] = None

    # Claim details
    claim_type: str = "accident"
    claim_amount: float
    diagnosis_code: Optional[str] = None
    diagnosis_description: Optional[str] = None
    treatment_date: Optional[str] = None
    submission_date: Optional[str] = None

    # Provider info
    provider_name: Optional[str] = None
    provider_id: Optional[str] = None

    # Additional data (flexible)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BronzeClaimRecord(BaseModel):
    """Bronze layer claim record with validation metadata."""
    claim_id: str
    raw_data: ClaimData

    # Validation results
    is_valid: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)

    # Quality metrics
    completeness_score: float = 0.0
    quality_score: float = 0.0

    # Anomaly detection
    anomalies_detected: list[str] = Field(default_factory=list)
    is_anomalous: bool = False

    # Agent decision
    decision: str = "pending"  # accept, quarantine, reject
    decision_reasoning: str = ""
    confidence_score: float = 0.0

    # Metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    agent_version: str = "1.0.0"
    processing_time_ms: float = 0.0


class SilverClaimRecord(BaseModel):
    """Silver layer enriched claim record."""
    claim_id: str
    bronze_record: BronzeClaimRecord

    # Enriched data
    pet_info: Optional[PetInfo] = None
    policy_info: Optional[PolicyInfo] = None
    provider_info: Optional[ProviderInfo] = None

    # Normalized values
    normalized_diagnosis_code: Optional[str] = None
    claim_category: Optional[str] = None
    claim_subcategory: Optional[str] = None

    # Calculated fields
    expected_reimbursement: float = 0.0
    coverage_percentage: float = 0.0
    is_within_limits: bool = True

    # Business rules applied
    rules_applied: list[str] = Field(default_factory=list)
    rules_passed: list[str] = Field(default_factory=list)
    rules_failed: list[str] = Field(default_factory=list)

    # Customer context
    customer_claim_history: list[dict] = Field(default_factory=list)
    customer_lifetime_value: float = 0.0
    customer_risk_score: float = 0.0

    # Quality scores
    enrichment_completeness: float = 0.0
    data_confidence: float = 0.0

    # Agent reasoning
    enrichment_notes: str = ""

    # Metadata
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0


class GoldClaimRecord(BaseModel):
    """Gold layer analytics record."""
    claim_id: str
    silver_record: SilverClaimRecord

    # Risk assessment
    fraud_score: float = 0.0
    fraud_indicators: list[str] = Field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical
    risk_factors: list[str] = Field(default_factory=list)

    # Insights
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    # KPI contributions
    kpi_metrics: dict[str, float] = Field(default_factory=dict)

    # Alerts
    alerts_generated: list[dict] = Field(default_factory=list)
    requires_manual_review: bool = False
    escalation_reason: Optional[str] = None

    # Final decision
    final_decision: str = "auto_approve"  # auto_approve, manual_review, deny
    decision_reasoning: str = ""

    # Customer 360 updates
    customer_360_updates: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    total_pipeline_time_ms: float = 0.0


class ClaimSummary(BaseModel):
    """Summary of claim for API responses."""
    claim_id: str
    status: ClaimStatus
    complexity: ClaimComplexity
    claim_amount: float
    current_stage: str

    # Processing info
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0

    # Results
    decision: Optional[str] = None
    fraud_score: Optional[float] = None
    risk_level: Optional[str] = None

    # Errors
    has_errors: bool = False
    error_message: Optional[str] = None
