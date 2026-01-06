"""Claim domain models."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    """Claim lifecycle status."""
    FNOL_RECEIVED = "fnol_received"
    UNDER_INVESTIGATION = "under_investigation"
    PENDING_INFO = "pending_info"
    APPROVED = "approved"
    DENIED = "denied"
    IN_PAYMENT = "in_payment"
    CLOSED_PAID = "closed_paid"
    CLOSED_NO_PAYMENT = "closed_no_payment"
    REOPENED = "reopened"
    SUBROGATION = "subrogation"


class ClaimSeverity(str, Enum):
    """AI-assessed claim severity."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


class ClaimDocument(BaseModel):
    """Document attached to a claim."""
    id: Optional[str] = None
    filename: str
    document_type: str  # police_report, photo, invoice, medical_record
    blob_url: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_text: Optional[str] = None


class FraudIndicator(BaseModel):
    """AI-detected fraud indicator."""
    indicator: str
    confidence: float = Field(..., ge=0, le=1)
    description: str


class Claim(BaseModel):
    """Insurance claim."""
    id: Optional[str] = None
    claim_number: str = Field(..., max_length=50)
    policy_id: str
    date_of_loss: date
    date_reported: datetime = Field(default_factory=datetime.utcnow)
    status: ClaimStatus = ClaimStatus.FNOL_RECEIVED
    loss_description: str = ""
    reserve_amount: Decimal = Field(default=Decimal("0"), ge=0)
    paid_amount: Decimal = Field(default=Decimal("0"), ge=0)
    claimant_id: Optional[str] = None
    external_claim_id: Optional[str] = None

    # AI-generated fields
    severity: Optional[ClaimSeverity] = None
    fraud_score: float = Field(default=0.0, ge=0, le=1)
    fraud_indicators: List[FraudIndicator] = Field(default_factory=list)
    ai_recommendation: Optional[str] = None

    # Documents
    documents: List[ClaimDocument] = Field(default_factory=list)

    model_config = {"use_enum_values": True}

    def to_dataverse_record(self) -> dict:
        """Convert to Dataverse entity format."""
        status_map = {
            "fnol_received": 100000000,
            "under_investigation": 100000001,
            "pending_info": 100000002,
            "approved": 100000003,
            "denied": 100000004,
            "in_payment": 100000005,
            "closed_paid": 100000006,
            "closed_no_payment": 100000007,
            "reopened": 100000008,
            "subrogation": 100000009,
        }

        record = {
            "eis_claimnumber": self.claim_number,
            "eis_PolicyId@odata.bind": f"/eis_policies({self.policy_id})",
            "eis_dateofloss": self.date_of_loss.isoformat(),
            "eis_datereported": self.date_reported.isoformat(),
            "eis_status": status_map.get(self.status, 100000000),
            "eis_lossdescription": self.loss_description,
            "eis_reserveamount": float(self.reserve_amount),
            "eis_paidamount": float(self.paid_amount),
            "eis_fraudscore": self.fraud_score,
        }

        if self.claimant_id:
            record["eis_ClaimantId@odata.bind"] = f"/eis_insuredparties({self.claimant_id})"

        if self.ai_recommendation:
            record["eis_airecommendation"] = self.ai_recommendation

        if self.external_claim_id:
            record["eis_externalclaimid"] = self.external_claim_id

        return record

    @classmethod
    def from_dataverse_record(cls, record: dict) -> "Claim":
        """Create from Dataverse entity."""
        status_map = {
            100000000: "fnol_received",
            100000001: "under_investigation",
            100000002: "pending_info",
            100000003: "approved",
            100000004: "denied",
            100000005: "in_payment",
            100000006: "closed_paid",
            100000007: "closed_no_payment",
            100000008: "reopened",
            100000009: "subrogation",
        }

        return cls(
            id=record.get("eis_claimid"),
            claim_number=record["eis_claimnumber"],
            policy_id=record.get("_eis_policyid_value", ""),
            date_of_loss=date.fromisoformat(record["eis_dateofloss"][:10]),
            date_reported=datetime.fromisoformat(record["eis_datereported"].replace("Z", "+00:00")),
            status=status_map.get(record.get("eis_status"), "fnol_received"),
            loss_description=record.get("eis_lossdescription", ""),
            reserve_amount=Decimal(str(record.get("eis_reserveamount", 0))),
            paid_amount=Decimal(str(record.get("eis_paidamount", 0))),
            claimant_id=record.get("_eis_claimantid_value"),
            fraud_score=record.get("eis_fraudscore", 0.0),
            ai_recommendation=record.get("eis_airecommendation"),
            external_claim_id=record.get("eis_externalclaimid"),
        )
