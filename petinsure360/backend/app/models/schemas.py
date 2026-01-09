"""
PetInsure360 - Pydantic Models
Data validation schemas for API requests and responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Enums
class Species(str, Enum):
    DOG = "Dog"
    CAT = "Cat"

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

class PlanName(str, Enum):
    BASIC = "Basic"
    STANDARD = "Standard"
    PREMIUM = "Premium"
    UNLIMITED = "Unlimited"

class ClaimType(str, Enum):
    ACCIDENT = "Accident"
    ILLNESS = "Illness"
    WELLNESS = "Wellness"
    DENTAL = "Dental"
    BEHAVIORAL = "Behavioral"

class ClaimStatus(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    DENIED = "Denied"
    PAID = "Paid"

# Customer Models
class CustomerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)  # Flexible phone format
    address_line1: Optional[str] = Field(None, alias="address")  # Accept 'address' or 'address_line1'
    address: Optional[str] = None  # Alternative field name
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)  # Support ZIP+4
    country: str = "USA"
    date_of_birth: Optional[date] = None  # Made optional for simple registration
    preferred_contact: str = "Email"
    marketing_opt_in: bool = False
    referral_source: Optional[str] = None

    def get_address(self) -> Optional[str]:
        """Get address from either field."""
        return self.address_line1 or self.address

    class Config:
        populate_by_name = True  # Allow both field name and alias
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
                "phone": "5551234567",
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "date_of_birth": "1985-06-15",
                "preferred_contact": "Email",
                "marketing_opt_in": True,
                "referral_source": "Google"
            }
        }

class CustomerResponse(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    state: str
    created_at: datetime
    message: str

# Pet Models
class PetCreate(BaseModel):
    customer_id: str
    pet_name: str = Field(..., min_length=1, max_length=50)
    species: Species
    breed: str
    gender: Gender
    date_of_birth: date
    weight_lbs: float = Field(..., gt=0, lt=500)
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    is_neutered: bool = False
    pre_existing_conditions: Optional[str] = None
    vaccination_status: str = "Up-to-date"

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST-12345",
                "pet_name": "Buddy",
                "species": "Dog",
                "breed": "Golden Retriever",
                "gender": "Male",
                "date_of_birth": "2020-03-15",
                "weight_lbs": 65.5,
                "color": "Golden",
                "is_neutered": True,
                "vaccination_status": "Up-to-date"
            }
        }

class PetResponse(BaseModel):
    pet_id: str
    customer_id: str
    pet_name: str
    species: str
    breed: str
    created_at: datetime
    message: str

# Policy Models
class PolicyCreate(BaseModel):
    customer_id: str
    pet_id: str
    plan_name: PlanName
    payment_method: str = "Credit Card"
    payment_frequency: str = "Monthly"
    includes_wellness: bool = False
    includes_dental: bool = False
    includes_behavioral: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST-12345",
                "pet_id": "PET-67890",
                "plan_name": "Premium",
                "payment_method": "Credit Card",
                "payment_frequency": "Monthly",
                "includes_wellness": True,
                "includes_dental": True
            }
        }

class PolicyResponse(BaseModel):
    policy_id: str
    policy_number: str
    customer_id: str
    pet_id: str
    plan_name: str
    monthly_premium: float
    annual_deductible: float
    coverage_limit: float
    effective_date: date
    expiration_date: date
    created_at: datetime
    message: str

# Claim Models
class ClaimCreate(BaseModel):
    policy_id: str
    pet_id: str
    customer_id: str
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None  # Allow provider name instead of ID
    claim_type: ClaimType
    claim_category: str = "General"  # Default category
    service_date: date
    claim_amount: float = Field(None, gt=0)  # Made optional, can use 'amount' alias
    amount: Optional[float] = Field(None, gt=0)  # Alternative field name
    diagnosis: Optional[str] = None  # Friendly alias for diagnosis_code
    diagnosis_code: Optional[str] = None
    description: Optional[str] = None  # Alias for treatment_notes
    treatment_notes: Optional[str] = None
    invoice_number: Optional[str] = None
    is_emergency: bool = False

    def get_claim_amount(self) -> float:
        """Get claim amount from either field."""
        return self.claim_amount or self.amount or 0.0

    def get_diagnosis(self) -> Optional[str]:
        """Get diagnosis from either field."""
        return self.diagnosis or self.diagnosis_code

    def get_notes(self) -> Optional[str]:
        """Get notes from either field."""
        return self.treatment_notes or self.description

    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "POL-12345",
                "pet_id": "PET-67890",
                "customer_id": "CUST-12345",
                "provider_name": "City Vet Clinic",
                "claim_type": "Illness",
                "claim_category": "Digestive",
                "service_date": "2024-12-20",
                "claim_amount": 450.00,
                "diagnosis": "Stomach upset",
                "description": "Treatment for stomach upset",
                "is_emergency": False
            }
        }

class ClaimResponse(BaseModel):
    claim_id: str
    claim_number: str
    policy_id: str
    pet_id: str
    customer_id: str
    claim_type: str
    claim_amount: float
    status: str
    submitted_date: datetime
    message: str

class ClaimStatusResponse(BaseModel):
    claim_id: str
    claim_number: str
    status: str
    claim_amount: float
    covered_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    processing_days: Optional[int] = None
    denial_reason: Optional[str] = None
    updated_at: datetime

# BI Insights Models
class KPIResponse(BaseModel):
    year_month: str
    total_claims: int
    unique_customers: int
    total_claim_amount: float
    total_paid_amount: float
    approval_rate: float
    denial_rate: float
    avg_processing_days: float
    loss_ratio: float
    claims_growth_pct: Optional[float] = None

class Customer360Response(BaseModel):
    customer_id: str
    full_name: str
    email: str
    phone: str
    city: str
    state: str
    customer_since: date
    tenure_months: int
    total_pets: int
    total_policies: int
    active_policies: int
    total_annual_premium: float
    total_claims: int
    total_claim_amount: float
    total_paid_amount: float
    loss_ratio: float
    customer_value_tier: str
    customer_risk_score: str
    churn_risk: str
    cross_sell_opportunity: Optional[str] = None
    estimated_revenue_opportunity: Optional[float] = None

class ClaimAnalyticsResponse(BaseModel):
    claim_id: str
    claim_number: str
    customer_name: str
    pet_name: str
    species: str
    claim_type: str
    claim_category: str
    service_date: date
    claim_amount: float
    paid_amount: float
    status: str
    processing_days: int
    provider_name: Optional[str] = None
    is_in_network: Optional[bool] = None

class ProviderPerformanceResponse(BaseModel):
    provider_id: str
    provider_name: str
    provider_type: str
    city: str
    state: str
    is_in_network: bool
    average_rating: float
    total_claims: int
    total_claim_amount: float
    avg_claim_amount: float
    avg_processing_days: float

class RiskScoreResponse(BaseModel):
    customer_id: str
    full_name: str
    total_risk_score: float
    risk_category: str
    pet_age_risk: float
    claims_frequency_risk: float
    loss_ratio_risk: float
    breed_risk: float
    recommendation: str

class CrossSellResponse(BaseModel):
    customer_id: str
    full_name: str
    email: str
    customer_value_tier: str
    current_plans: List[str]
    recommendation: str
    recommendation_reason: str
    estimated_revenue_opportunity: float
    priority_score: float
