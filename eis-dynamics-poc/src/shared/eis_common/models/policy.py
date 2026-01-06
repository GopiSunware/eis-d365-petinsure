"""Policy domain models."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PolicyStatus(str, Enum):
    """Policy lifecycle status."""
    DRAFT = "draft"
    QUOTED = "quoted"
    BOUND = "bound"
    ACTIVE = "active"
    PENDING_RENEWAL = "pending_renewal"
    RENEWED = "renewed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NON_RENEWED = "non_renewed"


class PolicyType(str, Enum):
    """Type of insurance policy."""
    PET = "pet"
    HOME = "home"
    COMMERCIAL = "commercial"
    LIFE = "life"
    HEALTH = "health"


class PlanType(str, Enum):
    """Pet insurance plan types."""
    ACCIDENT_ONLY = "accident_only"
    ACCIDENT_ILLNESS = "accident_illness"
    COMPREHENSIVE = "comprehensive"


class CoverageType(str, Enum):
    """Coverage types for pet insurance."""
    ACCIDENT = "accident"
    ILLNESS = "illness"
    WELLNESS = "wellness"
    DENTAL = "dental"
    BEHAVIORAL = "behavioral"
    HEREDITARY = "hereditary"
    ALTERNATIVE = "alternative"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    MEDICATIONS = "medications"
    DIAGNOSTICS = "diagnostics"


class Coverage(BaseModel):
    """Insurance coverage within a pet policy."""
    id: Optional[str] = None
    coverage_type: CoverageType
    limit: Decimal = Field(..., ge=0)
    deductible: Decimal = Field(default=Decimal("0"), ge=0)
    premium: Decimal = Field(default=Decimal("0"), ge=0)
    waiting_period_days: int = Field(default=0, ge=0)
    policy_id: Optional[str] = None
    external_id: Optional[str] = None

    model_config = {"use_enum_values": True}


class Policy(BaseModel):
    """Pet insurance policy."""
    id: Optional[str] = None
    policy_number: str = Field(..., max_length=50)
    effective_date: date
    expiration_date: date
    status: PolicyStatus = PolicyStatus.DRAFT
    policy_type: PolicyType = PolicyType.PET
    plan_type: Optional[PlanType] = PlanType.ACCIDENT_ILLNESS
    total_premium: Decimal = Field(default=Decimal("0"), ge=0)
    annual_limit: Decimal = Field(default=Decimal("10000"), ge=0)
    deductible: Decimal = Field(default=Decimal("250"), ge=0)
    reimbursement_pct: int = Field(default=80, ge=50, le=100)
    billing_frequency: str = "monthly"
    payment_method: str = "autopay"
    pet_owner_id: str
    pet_ids: List[str] = Field(default_factory=list)
    external_policy_id: Optional[str] = None
    last_sync_date: Optional[datetime] = None
    coverages: List[Coverage] = Field(default_factory=list)

    model_config = {"use_enum_values": True}

    def to_dataverse_record(self) -> dict:
        """Convert to Dataverse entity format."""
        status_map = {
            "draft": 100000000,
            "quoted": 100000001,
            "bound": 100000002,
            "active": 100000003,
            "pending_renewal": 100000004,
            "renewed": 100000005,
            "cancelled": 100000006,
            "expired": 100000007,
            "non_renewed": 100000008,
        }

        plan_type_map = {
            "accident_only": 100000000,
            "accident_illness": 100000001,
            "comprehensive": 100000002,
        }

        record = {
            "eis_policynumber": self.policy_number,
            "eis_effectivedate": self.effective_date.isoformat(),
            "eis_expirationdate": self.expiration_date.isoformat(),
            "eis_status": status_map.get(self.status, 100000000),
            "eis_plantype": plan_type_map.get(self.plan_type, 100000001),
            "eis_totalpremium": float(self.total_premium),
            "eis_annuallimit": float(self.annual_limit),
            "eis_deductible": float(self.deductible),
            "eis_reimbursementpct": self.reimbursement_pct,
            "eis_billingfrequency": self.billing_frequency,
            "eis_PetOwnerId@odata.bind": f"/eis_petowners({self.pet_owner_id})",
        }

        if self.external_policy_id:
            record["eis_externalpolicyid"] = self.external_policy_id

        if self.last_sync_date:
            record["eis_lastsyncdate"] = self.last_sync_date.isoformat()

        return record

    @classmethod
    def from_dataverse_record(cls, record: dict) -> "Policy":
        """Create from Dataverse entity."""
        status_map = {
            100000000: "draft",
            100000001: "quoted",
            100000002: "bound",
            100000003: "active",
            100000004: "pending_renewal",
            100000005: "renewed",
            100000006: "cancelled",
            100000007: "expired",
            100000008: "non_renewed",
        }

        plan_type_map = {
            100000000: "accident_only",
            100000001: "accident_illness",
            100000002: "comprehensive",
        }

        return cls(
            id=record.get("eis_policyid"),
            policy_number=record["eis_policynumber"],
            effective_date=date.fromisoformat(record["eis_effectivedate"][:10]),
            expiration_date=date.fromisoformat(record["eis_expirationdate"][:10]),
            status=status_map.get(record.get("eis_status"), "draft"),
            policy_type=PolicyType.PET,
            plan_type=plan_type_map.get(record.get("eis_plantype"), "accident_illness"),
            total_premium=Decimal(str(record.get("eis_totalpremium", 0))),
            annual_limit=Decimal(str(record.get("eis_annuallimit", 10000))),
            deductible=Decimal(str(record.get("eis_deductible", 250))),
            reimbursement_pct=record.get("eis_reimbursementpct", 80),
            billing_frequency=record.get("eis_billingfrequency", "monthly"),
            pet_owner_id=record.get("_eis_petownerid_value", ""),
            external_policy_id=record.get("eis_externalpolicyid"),
        )
