"""Claims rules configuration models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class AutoApproveCondition(BaseModel):
    """Condition for auto-approval."""
    name: str
    description: str
    enabled: bool = True
    value: Optional[float] = None


class AutoDenyCondition(BaseModel):
    """Condition for auto-denial."""
    name: str
    description: str
    enabled: bool = True
    value: Optional[float] = None


class AutoAdjudicationConfig(BaseModel):
    """Auto-adjudication configuration."""
    enabled: bool = True
    max_auto_approve_amount: Decimal = Field(default=Decimal("500.00"))
    require_human_review_above: Decimal = Field(default=Decimal("2500.00"))

    # Auto-approve conditions
    auto_approve_conditions: List[AutoApproveCondition] = Field(default_factory=lambda: [
        AutoApproveCondition(
            name="fraud_score_below",
            description="Fraud score must be below this threshold",
            value=0.3
        ),
        AutoApproveCondition(
            name="document_confidence_above",
            description="OCR document confidence must be above this threshold",
            value=0.85
        ),
        AutoApproveCondition(
            name="within_coverage_limits",
            description="Claim must be within policy coverage limits",
            enabled=True
        ),
        AutoApproveCondition(
            name="no_waiting_period_violation",
            description="No waiting period violations",
            enabled=True
        ),
    ])

    # Auto-deny conditions
    auto_deny_conditions: List[AutoDenyCondition] = Field(default_factory=lambda: [
        AutoDenyCondition(
            name="fraud_score_above",
            description="Auto-deny if fraud score exceeds this threshold",
            value=0.85
        ),
        AutoDenyCondition(
            name="pre_existing_match",
            description="Auto-deny if pre-existing condition detected",
            enabled=True
        ),
        AutoDenyCondition(
            name="policy_lapsed",
            description="Auto-deny if policy has lapsed",
            enabled=True
        ),
        AutoDenyCondition(
            name="excluded_condition",
            description="Auto-deny if condition is excluded from coverage",
            enabled=True
        ),
    ])


class VelocityCheck(BaseModel):
    """Velocity check configuration for fraud detection."""
    max_claims_per_month: int = 3
    max_claims_per_year: int = 12
    same_condition_cooldown_days: int = 30


class SuspiciousPattern(BaseModel):
    """Suspicious pattern for fraud detection."""
    name: str
    description: str
    enabled: bool = True
    threshold_days: Optional[int] = None


class FraudDetectionConfig(BaseModel):
    """Fraud detection configuration."""
    enabled: bool = True
    flag_threshold: float = Field(default=0.5, ge=0, le=1)
    deny_threshold: float = Field(default=0.85, ge=0, le=1)
    escalate_threshold: float = Field(default=0.7, ge=0, le=1)

    # Velocity checks
    velocity_check: VelocityCheck = Field(default_factory=VelocityCheck)

    # Duplicate detection
    duplicate_detection_enabled: bool = True
    same_provider_same_day_action: str = "flag"  # flag, deny, escalate
    similar_amount_threshold_percent: float = 5.0

    # Suspicious patterns
    suspicious_patterns: List[SuspiciousPattern] = Field(default_factory=lambda: [
        SuspiciousPattern(
            name="claim_filed_within_days_of_enrollment",
            description="Flag claims filed shortly after enrollment",
            threshold_days=30
        ),
        SuspiciousPattern(
            name="multiple_pets_same_condition",
            description="Multiple pets with same condition at same time",
            enabled=True
        ),
        SuspiciousPattern(
            name="weekend_emergency_frequency",
            description="High frequency of weekend emergency visits",
            enabled=True
        ),
        SuspiciousPattern(
            name="claim_amount_near_limit",
            description="Claim amount suspiciously close to coverage limit",
            enabled=True
        ),
    ])


class EscalationRule(BaseModel):
    """Escalation rule."""
    name: str
    description: str
    enabled: bool = True
    escalate_to: str  # senior_adjuster, veterinary_review, fraud_team
    threshold: Optional[float] = None


class EscalationRules(BaseModel):
    """Escalation rules configuration."""
    rules: List[EscalationRule] = Field(default_factory=lambda: [
        EscalationRule(
            name="claim_amount_above",
            description="Escalate claims above this amount",
            escalate_to="senior_adjuster",
            threshold=5000.0
        ),
        EscalationRule(
            name="fraud_score_between",
            description="Escalate claims with fraud score in suspicious range",
            escalate_to="fraud_team",
            threshold=0.5
        ),
        EscalationRule(
            name="repeat_claim_same_condition",
            description="Escalate repeat claims for same condition",
            escalate_to="senior_adjuster"
        ),
        EscalationRule(
            name="experimental_treatment",
            description="Escalate claims for experimental treatments",
            escalate_to="veterinary_review"
        ),
        EscalationRule(
            name="disputed_diagnosis",
            description="Escalate claims with disputed diagnosis",
            escalate_to="veterinary_review"
        ),
        EscalationRule(
            name="high_value_claim",
            description="Escalate very high value claims",
            escalate_to="senior_adjuster",
            threshold=10000.0
        ),
    ])


class ClaimsRulesConfig(BaseModel):
    """Complete claims rules configuration."""
    id: str = "claims_rules"
    config_type: str = "claims_rules"  # Partition key
    version: int = 1

    auto_adjudication: AutoAdjudicationConfig = Field(default_factory=AutoAdjudicationConfig)
    fraud_detection: FraudDetectionConfig = Field(default_factory=FraudDetectionConfig)
    escalation_rules: EscalationRules = Field(default_factory=EscalationRules)

    # Processing settings
    require_vet_invoice: bool = True
    require_diagnosis: bool = True
    allow_partial_payment: bool = True
    max_processing_days: int = 5

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


class ClaimsRulesUpdate(BaseModel):
    """Request to update claims rules."""
    auto_adjudication: Optional[AutoAdjudicationConfig] = None
    fraud_detection: Optional[FraudDetectionConfig] = None
    escalation_rules: Optional[EscalationRules] = None
    require_vet_invoice: Optional[bool] = None
    require_diagnosis: Optional[bool] = None
    allow_partial_payment: Optional[bool] = None
    max_processing_days: Optional[int] = None
