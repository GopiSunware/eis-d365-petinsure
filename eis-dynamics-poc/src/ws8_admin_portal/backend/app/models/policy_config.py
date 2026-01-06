"""Policy configuration models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class CoverageLimits(BaseModel):
    """Coverage limits for a plan."""
    annual_limit: Optional[Decimal] = None  # None = unlimited
    per_incident_limit: Optional[Decimal] = None
    lifetime_limit: Optional[Decimal] = None


class PlanDefinition(BaseModel):
    """Insurance plan definition."""
    plan_id: str
    name: str
    description: str
    is_active: bool = True

    # Coverage
    limits: CoverageLimits
    reimbursement_options: List[int] = Field(default_factory=lambda: [70, 80, 90])
    deductible_options: List[int] = Field(default_factory=lambda: [100, 250, 500])
    deductible_type: str = "annual"  # annual, per_incident

    # What's covered
    covers_accidents: bool = True
    covers_illnesses: bool = True
    covers_wellness: bool = False
    covers_dental: bool = False
    covers_behavioral: bool = False
    covers_alternative_therapy: bool = False
    covers_prescription_food: bool = False
    covers_hereditary: bool = True
    covers_chronic: bool = True

    # Sublimits
    sublimits: Dict[str, Decimal] = Field(default_factory=dict)

    # Premium factor
    premium_factor: float = 1.0


class WaitingPeriods(BaseModel):
    """Waiting periods configuration."""
    accidents_days: int = 0
    illnesses_days: int = 14
    orthopedic_days: int = 180  # Hip dysplasia, cruciate ligament
    dental_days: int = 30
    behavioral_days: int = 90
    cancer_days: int = 30
    chronic_conditions_days: int = 14


class ExclusionCategory(BaseModel):
    """Exclusion category."""
    category: str
    description: str
    conditions: List[str] = Field(default_factory=list)
    is_active: bool = True


class Exclusions(BaseModel):
    """Policy exclusions configuration."""
    global_exclusions: List[str] = Field(default_factory=lambda: [
        "Cosmetic procedures (ear cropping, tail docking, declawing)",
        "Breeding costs and pregnancy-related conditions",
        "Pre-existing conditions",
        "Experimental treatments not approved by veterinary boards",
        "Elective procedures",
        "Grooming and routine bathing",
        "Food and dietary supplements (unless prescription)",
        "Training and behavioral classes",
        "Boarding and pet sitting",
        "Parasite prevention (unless included in wellness)",
    ])

    # Breed-specific exclusions
    breed_exclusions: Dict[str, List[str]] = Field(default_factory=lambda: {
        "french_bulldog": ["Stenotic nares correction", "Soft palate resection"],
        "english_bulldog": ["Stenotic nares correction", "Soft palate resection"],
        "cavalier_king_charles": ["Syringomyelia"],
    })

    # Condition-specific exclusions
    condition_exclusions: List[ExclusionCategory] = Field(default_factory=list)


class CoverageRules(BaseModel):
    """Coverage rules and requirements."""
    # Pre-existing conditions
    pre_existing_lookback_months: int = 18
    curable_condition_clear_months: int = 12
    bilateral_exclusion: bool = True  # If left knee injured, right knee excluded

    # Age requirements
    min_enrollment_age_weeks: int = 8
    max_enrollment_age_dogs_years: int = 14
    max_enrollment_age_cats_years: int = 16
    max_renewal_age: Optional[int] = None  # None = no max

    # Documentation requirements
    require_vet_exam_days: int = 30  # Exam within X days of enrollment
    require_vaccination_records: bool = True

    # Claims requirements
    require_itemized_invoice: bool = True
    require_diagnosis_code: bool = True
    allow_direct_vet_pay: bool = True


class PolicyPlansConfig(BaseModel):
    """Complete policy plans configuration."""
    id: str = "policy_config"
    config_type: str = "policy_config"  # Partition key
    version: int = 1

    # Plan definitions
    plans: List[PlanDefinition] = Field(default_factory=lambda: [
        PlanDefinition(
            plan_id="basic",
            name="Basic",
            description="Accident-only coverage for essential protection",
            limits=CoverageLimits(annual_limit=Decimal("5000")),
            reimbursement_options=[70, 80],
            deductible_options=[250, 500, 750],
            covers_illnesses=False,
            premium_factor=0.6,
        ),
        PlanDefinition(
            plan_id="standard",
            name="Standard",
            description="Comprehensive accident and illness coverage",
            limits=CoverageLimits(annual_limit=Decimal("15000")),
            reimbursement_options=[70, 80, 90],
            deductible_options=[100, 250, 500],
            premium_factor=1.0,
        ),
        PlanDefinition(
            plan_id="premium",
            name="Premium",
            description="Complete coverage including dental and behavioral",
            limits=CoverageLimits(annual_limit=Decimal("30000")),
            reimbursement_options=[80, 90],
            deductible_options=[0, 100, 250],
            covers_dental=True,
            covers_behavioral=True,
            covers_alternative_therapy=True,
            sublimits={
                "dental_cleaning": Decimal("300"),
                "behavioral_therapy": Decimal("500"),
                "alternative_therapy": Decimal("1000"),
            },
            premium_factor=1.5,
        ),
        PlanDefinition(
            plan_id="unlimited",
            name="Unlimited",
            description="Maximum protection with no annual limits",
            limits=CoverageLimits(annual_limit=None),  # Unlimited
            reimbursement_options=[90],
            deductible_options=[0, 100],
            covers_wellness=True,
            covers_dental=True,
            covers_behavioral=True,
            covers_alternative_therapy=True,
            covers_prescription_food=True,
            sublimits={
                "wellness": Decimal("500"),
                "dental_cleaning": Decimal("500"),
                "behavioral_therapy": Decimal("1000"),
                "alternative_therapy": Decimal("2000"),
                "prescription_food": Decimal("500"),
            },
            premium_factor=2.0,
        ),
    ])

    waiting_periods: WaitingPeriods = Field(default_factory=WaitingPeriods)
    exclusions: Exclusions = Field(default_factory=Exclusions)
    coverage_rules: CoverageRules = Field(default_factory=CoverageRules)

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


class PolicyConfigUpdate(BaseModel):
    """Request to update policy configuration."""
    plans: Optional[List[PlanDefinition]] = None
    waiting_periods: Optional[WaitingPeriods] = None
    exclusions: Optional[Exclusions] = None
    coverage_rules: Optional[CoverageRules] = None
