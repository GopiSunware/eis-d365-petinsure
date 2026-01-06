"""
Pydantic schemas for the Unified Claims Data API.
These models define the data structures for all entities in the system.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class CustomerSegment(str, Enum):
    NEW = "new"
    STANDARD = "standard"
    LOYAL = "loyal"
    HIGH_RISK = "high_risk"
    FRAUD_SUSPECT = "fraud_suspect"


class Species(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    EXOTIC = "exotic"


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class PlanType(str, Enum):
    ACCIDENT_ONLY = "accident_only"
    ACCIDENT_ILLNESS = "accident_illness"
    COMPREHENSIVE = "comprehensive"
    WELLNESS_ADDON = "wellness_addon"


class ClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    PAID = "paid"
    MANUAL_REVIEW = "manual_review"


class ClaimCategory(str, Enum):
    PREVENTIVE = "preventive"
    ILLNESS = "illness"
    ACCIDENT = "accident"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    CHRONIC = "chronic"
    DENTAL = "dental"
    DIAGNOSTIC = "diagnostic"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# CUSTOMER MODELS
# =============================================================================

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address_line1: str
    city: str
    state: str
    zip_code: str


class Customer(CustomerBase):
    customer_id: str
    date_of_birth: date
    customer_since: date
    preferred_contact: str = "email"
    marketing_opt_in: bool = True
    referral_source: Optional[str] = None
    segment: CustomerSegment = CustomerSegment.STANDARD
    lifetime_value: float = 0.0
    risk_tier: RiskTier = RiskTier.LOW
    total_claims: int = 0
    total_paid: float = 0.0
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class CustomerHousehold(BaseModel):
    customer: Customer
    pets: List["Pet"] = []
    policies: List["Policy"] = []
    total_premium_monthly: float = 0.0


# =============================================================================
# PET MODELS
# =============================================================================

class PreExistingCondition(BaseModel):
    condition_name: str
    diagnosis_date: date
    diagnosis_code: Optional[str] = None
    notes: Optional[str] = None
    is_excluded: bool = True


class Pet(BaseModel):
    pet_id: str
    customer_id: str
    name: str
    species: Species
    breed: str
    gender: str
    date_of_birth: date
    weight_lbs: float
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    is_neutered: bool = False
    pre_existing_conditions: List[PreExistingCondition] = []
    vaccination_status: str = "up_to_date"
    adoption_date: Optional[date] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class BreedRisk(BaseModel):
    breed: str
    species: Species
    common_conditions: List[str] = []
    risk_multipliers: Dict[str, float] = {}
    average_lifespan_years: float = 0.0
    average_annual_vet_cost: float = 0.0


# =============================================================================
# POLICY MODELS
# =============================================================================

class CoverageLimit(BaseModel):
    annual_limit: float
    per_incident_limit: Optional[float] = None
    lifetime_limit: Optional[float] = None
    used_this_year: float = 0.0
    remaining: float = 0.0


class WaitingPeriod(BaseModel):
    accident_days: int = 14
    illness_days: int = 14
    orthopedic_days: int = 180
    cancer_days: int = 30
    policy_effective_date: date
    all_satisfied: bool = False


class PolicyExclusion(BaseModel):
    exclusion_type: str  # "pre_existing", "breed_specific", "age_related", "general"
    description: str
    diagnosis_codes: List[str] = []
    is_permanent: bool = True


class Policy(BaseModel):
    policy_id: str
    policy_number: str
    customer_id: str
    pet_id: str
    plan_type: PlanType
    plan_name: str
    monthly_premium: float
    annual_deductible: float
    deductible_met: float = 0.0
    reimbursement_percentage: int = 80
    coverage_limit: CoverageLimit
    waiting_period: WaitingPeriod
    exclusions: List[PolicyExclusion] = []
    effective_date: date
    expiration_date: date
    status: PolicyStatus = PolicyStatus.ACTIVE
    payment_method: str = "credit_card"
    payment_frequency: str = "monthly"
    includes_wellness: bool = False
    includes_dental: bool = False
    includes_behavioral: bool = False
    renewal_count: int = 0
    cancellation_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


class PolicyHistory(BaseModel):
    policy_id: str
    events: List[Dict[str, Any]] = []


# =============================================================================
# PROVIDER MODELS
# =============================================================================

class ProviderStats(BaseModel):
    total_claims: int = 0
    total_amount: float = 0.0
    average_claim: float = 0.0
    denial_rate: float = 0.0
    fraud_rate: float = 0.0
    customer_concentration: Dict[str, float] = {}  # customer_id -> % of claims


class Provider(BaseModel):
    provider_id: str
    name: str
    provider_type: str  # "general", "emergency", "specialty", "mobile"
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: Optional[str] = None
    is_in_network: bool = True
    average_rating: float = 4.0
    total_reviews: int = 0
    accepts_emergency: bool = False
    operating_hours: str = "9AM-5PM"
    specialties: List[str] = []
    license_number: str
    stats: ProviderStats = ProviderStats()
    created_at: datetime

    class Config:
        use_enum_values = True


# =============================================================================
# CLAIM MODELS
# =============================================================================

class ClaimLineItem(BaseModel):
    line_id: str
    description: str
    diagnosis_code: Optional[str] = None
    procedure_code: Optional[str] = None
    quantity: int = 1
    unit_price: float
    total_amount: float
    is_covered: bool = True
    denial_reason: Optional[str] = None


class ClaimDocument(BaseModel):
    document_id: str
    document_type: str  # "invoice", "medical_record", "receipt", "other"
    filename: str
    upload_date: datetime
    verified: bool = False


class Claim(BaseModel):
    claim_id: str
    claim_number: str
    policy_id: str
    pet_id: str
    customer_id: str
    provider_id: str
    claim_type: str  # "accident", "illness", "wellness", "dental", etc.
    claim_category: ClaimCategory
    diagnosis_code: str
    diagnosis_description: str
    service_date: date
    submitted_date: date
    treatment_notes: str
    line_items: List[ClaimLineItem] = []
    claim_amount: float
    deductible_applied: float = 0.0
    covered_amount: float = 0.0
    paid_amount: float = 0.0
    status: ClaimStatus = ClaimStatus.SUBMITTED
    denial_reason: Optional[str] = None
    processing_days: Optional[int] = None
    is_emergency: bool = False
    is_recurring: bool = False
    documents: List[ClaimDocument] = []
    ai_decision: Optional[str] = None
    ai_reasoning: Optional[str] = None
    ai_risk_score: Optional[float] = None
    ai_quality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


# =============================================================================
# FRAUD MODELS
# =============================================================================

class FraudIndicator(BaseModel):
    indicator_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    score_impact: float = 0.0


class FraudCheckResult(BaseModel):
    claim_id: str
    fraud_score: float = 0.0  # 0-100
    risk_level: RiskTier = RiskTier.LOW
    indicators: List[FraudIndicator] = []
    recommendation: str = "approve"
    reasoning: str = ""
    requires_manual_review: bool = False

    class Config:
        use_enum_values = True


class VelocityCheck(BaseModel):
    customer_id: str
    claims_last_30_days: int = 0
    claims_last_90_days: int = 0
    claims_last_365_days: int = 0
    average_claim_frequency_days: float = 0.0
    is_unusual: bool = False
    reasoning: Optional[str] = None


class ProviderCustomerRelationship(BaseModel):
    provider_id: str
    customer_id: str
    total_claims: int = 0
    total_amount: float = 0.0
    percentage_of_provider_claims: float = 0.0
    percentage_of_customer_claims: float = 0.0
    is_unusual_concentration: bool = False


# =============================================================================
# MEDICAL REFERENCE MODELS
# =============================================================================

class DiagnosisCode(BaseModel):
    code: str
    description: str
    category: str
    is_chronic: bool = False
    typical_treatment_cost_min: float = 0.0
    typical_treatment_cost_max: float = 0.0
    typical_treatment_duration_days: int = 1
    related_codes: List[str] = []


class TreatmentBenchmark(BaseModel):
    diagnosis_code: str
    median_cost: float = 0.0
    percentile_25: float = 0.0
    percentile_75: float = 0.0
    percentile_90: float = 0.0
    expected_line_items: List[str] = []


# =============================================================================
# BILLING MODELS
# =============================================================================

class Payment(BaseModel):
    payment_id: str
    customer_id: str
    policy_id: Optional[str] = None
    claim_id: Optional[str] = None
    payment_type: str  # "premium", "claim_payout", "refund"
    amount: float
    payment_date: date
    payment_method: str
    status: str = "completed"
    reference_number: Optional[str] = None


class ReimbursementCalculation(BaseModel):
    claim_amount: float
    deductible_remaining: float
    deductible_applied: float
    amount_after_deductible: float
    reimbursement_percentage: int
    covered_amount: float
    annual_limit_remaining: float
    final_payout: float
    explanation: str


class AnnualSummary(BaseModel):
    policy_id: str
    year: int
    total_premiums_paid: float = 0.0
    total_claims_submitted: int = 0
    total_claims_approved: int = 0
    total_claimed_amount: float = 0.0
    total_paid_amount: float = 0.0
    deductible_met: bool = False
    annual_limit_used: float = 0.0
    annual_limit_remaining: float = 0.0


# =============================================================================
# API RESPONSE MODELS
# =============================================================================

class CoverageCheckResult(BaseModel):
    is_covered: bool
    diagnosis_code: str
    coverage_percentage: int = 0
    exclusion_reason: Optional[str] = None
    waiting_period_satisfied: bool = True
    notes: Optional[str] = None


class LimitCheckResult(BaseModel):
    annual_limit: float
    used_this_year: float
    remaining: float
    per_incident_limit: Optional[float] = None
    is_within_limits: bool = True


# Forward reference updates
CustomerHousehold.model_rebuild()
