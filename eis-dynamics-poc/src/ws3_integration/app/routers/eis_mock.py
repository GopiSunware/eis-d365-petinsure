"""Mock EIS API endpoints - simulates EIS Suite pet insurance responses."""
import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# Mock data models
class EISPet(BaseModel):
    """Pet in the EIS system."""
    pet_id: str
    name: str
    species: str
    breed: str
    date_of_birth: date
    gender: str
    microchip_id: Optional[str] = None
    spayed_neutered: bool = False
    weight_lbs: Optional[float] = None
    color: Optional[str] = None


class EISCoverage(BaseModel):
    """Coverage in a pet policy."""
    coverage_id: str
    coverage_type: str
    limit: Decimal
    waiting_period_days: int
    premium: Decimal


class EISPolicy(BaseModel):
    """Pet insurance policy in EIS."""
    policy_id: str
    policy_number: str
    customer_id: str
    pet_owner_name: str
    plan_type: str
    status: str
    effective_date: date
    expiration_date: date
    total_premium: Decimal
    annual_limit: Decimal
    deductible: Decimal
    reimbursement_pct: int
    billing_frequency: str = "monthly"
    payment_method: str = "autopay"
    pets: List[EISPet] = Field(default_factory=list)
    coverages: List[EISCoverage] = Field(default_factory=list)
    add_ons: List[dict] = Field(default_factory=list)
    discounts: List[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class EISClaim(BaseModel):
    """Pet insurance claim in EIS."""
    claim_id: str
    claim_number: str
    policy_id: str
    pet_id: str
    pet_name: str
    pet_species: str
    pet_breed: str
    date_of_service: date
    date_reported: datetime
    status: str
    condition_type: str
    diagnosis: str
    treatment: Optional[str] = None
    vet_provider_id: Optional[str] = None
    vet_clinic_name: Optional[str] = None
    amount_billed: Decimal
    amount_approved: Decimal
    amount_paid: Decimal
    deductible_applied: Decimal
    reimbursement_rate: Decimal
    estimated_payout: Decimal
    fraud_score: float = 0.0
    pre_existing_flag: bool = False
    adjuster_id: Optional[str] = None


class EISCustomer(BaseModel):
    """Pet owner in EIS."""
    customer_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    customer_type: str = "individual"
    pets_count: int = 0
    active_policies: int = 0
    created_at: datetime
    updated_at: datetime


class EISVetProvider(BaseModel):
    """Veterinary provider in EIS."""
    provider_id: str
    clinic_name: str
    address: str
    phone: str
    email: Optional[str] = None
    license_number: str
    is_preferred: bool = False
    fraud_flag: bool = False
    claims_processed: int = 0


class WebhookPayload(BaseModel):
    event_type: str
    entity_id: str
    entity_type: str
    timestamp: datetime
    data: dict


# In-memory mock database
_policies: dict = {}
_claims: dict = {}
_customers: dict = {}
_pets: dict = {}
_vet_providers: dict = {}


def _init_mock_data():
    """Initialize mock pet insurance data if empty."""
    if _policies:
        return

    # Create mock pet owners
    customers = [
        EISCustomer(
            customer_id="CUST-001",
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            phone="555-123-4567",
            address="456 Oak Avenue",
            city="Chicago",
            state="IL",
            zip_code="60601",
            customer_type="individual",
            pets_count=1,
            active_policies=1,
            created_at=datetime.utcnow() - timedelta(days=517),
            updated_at=datetime.utcnow(),
        ),
        EISCustomer(
            customer_id="CUST-002",
            first_name="Sarah",
            last_name="Johnson",
            email="sarah.johnson@example.com",
            phone="555-234-5678",
            address="789 Maple Drive",
            city="Los Angeles",
            state="CA",
            zip_code="90210",
            customer_type="individual",
            pets_count=1,
            active_policies=1,
            created_at=datetime.utcnow() - timedelta(days=365),
            updated_at=datetime.utcnow(),
        ),
        EISCustomer(
            customer_id="CUST-003",
            first_name="Michael",
            last_name="Williams",
            email="m.williams@example.com",
            phone="555-345-6789",
            address="321 Pine Street",
            city="New York",
            state="NY",
            zip_code="10001",
            customer_type="individual",
            pets_count=2,
            active_policies=1,
            created_at=datetime.utcnow() - timedelta(days=200),
            updated_at=datetime.utcnow(),
        ),
    ]
    for c in customers:
        _customers[c.customer_id] = c

    # Create mock pets
    pets = [
        EISPet(
            pet_id="PET-001",
            name="Max",
            species="dog",
            breed="Golden Retriever",
            date_of_birth=date(2019, 3, 15),
            gender="male",
            microchip_id="985121012345678",
            spayed_neutered=True,
            weight_lbs=72,
            color="golden",
        ),
        EISPet(
            pet_id="PET-002",
            name="Whiskers",
            species="cat",
            breed="Maine Coon",
            date_of_birth=date(2020, 8, 22),
            gender="female",
            microchip_id="985121098765432",
            spayed_neutered=True,
            weight_lbs=14,
            color="tabby",
        ),
        EISPet(
            pet_id="PET-003",
            name="Bella",
            species="dog",
            breed="French Bulldog",
            date_of_birth=date(2021, 5, 10),
            gender="female",
            microchip_id="985121055555555",
            spayed_neutered=True,
            weight_lbs=24,
            color="fawn",
        ),
        EISPet(
            pet_id="PET-004",
            name="Luna",
            species="dog",
            breed="Labrador Retriever",
            date_of_birth=date(2022, 2, 28),
            gender="female",
            microchip_id="985121066666666",
            spayed_neutered=False,
            weight_lbs=55,
            color="black",
        ),
        EISPet(
            pet_id="PET-005",
            name="Charlie",
            species="cat",
            breed="Domestic Shorthair",
            date_of_birth=date(2018, 11, 5),
            gender="male",
            spayed_neutered=True,
            weight_lbs=11,
            color="orange",
        ),
    ]
    for p in pets:
        _pets[p.pet_id] = p

    # Create mock policies
    policies = [
        EISPolicy(
            policy_id="POL-PET-2024-001",
            policy_number="PET-IL-2024-00001",
            customer_id="CUST-001",
            pet_owner_name="John Smith",
            plan_type="accident_illness",
            status="active",
            effective_date=date.today() - timedelta(days=517),
            expiration_date=date.today() + timedelta(days=213),
            total_premium=Decimal("637.62"),
            annual_limit=Decimal("10000.00"),
            deductible=Decimal("250.00"),
            reimbursement_pct=80,
            pets=[pets[0]],  # Max
            coverages=[
                EISCoverage(
                    coverage_id="COV-001",
                    coverage_type="accident",
                    limit=Decimal("10000.00"),
                    waiting_period_days=3,
                    premium=Decimal("150.00"),
                ),
                EISCoverage(
                    coverage_id="COV-002",
                    coverage_type="illness",
                    limit=Decimal("10000.00"),
                    waiting_period_days=14,
                    premium=Decimal("300.00"),
                ),
                EISCoverage(
                    coverage_id="COV-003",
                    coverage_type="hereditary",
                    limit=Decimal("10000.00"),
                    waiting_period_days=14,
                    premium=Decimal("100.00"),
                ),
            ],
            discounts=[
                {"type": "spayed_neutered", "rate": 0.05, "amount": 33.84},
                {"type": "microchipped", "rate": 0.03, "amount": 20.30},
            ],
            created_at=datetime.utcnow() - timedelta(days=517),
            updated_at=datetime.utcnow(),
        ),
        EISPolicy(
            policy_id="POL-PET-2024-002",
            policy_number="PET-CA-2024-00002",
            customer_id="CUST-002",
            pet_owner_name="Sarah Johnson",
            plan_type="comprehensive",
            status="active",
            effective_date=date.today() - timedelta(days=120),
            expiration_date=date.today() + timedelta(days=245),
            total_premium=Decimal("892.50"),
            annual_limit=Decimal("15000.00"),
            deductible=Decimal("500.00"),
            reimbursement_pct=90,
            pets=[pets[1]],  # Whiskers
            coverages=[
                EISCoverage(
                    coverage_id="COV-004",
                    coverage_type="accident",
                    limit=Decimal("15000.00"),
                    waiting_period_days=3,
                    premium=Decimal("120.00"),
                ),
                EISCoverage(
                    coverage_id="COV-005",
                    coverage_type="illness",
                    limit=Decimal("15000.00"),
                    waiting_period_days=14,
                    premium=Decimal("280.00"),
                ),
                EISCoverage(
                    coverage_id="COV-006",
                    coverage_type="wellness",
                    limit=Decimal("450.00"),
                    waiting_period_days=0,
                    premium=Decimal("180.00"),
                ),
            ],
            add_ons=[{"type": "wellness", "monthly_cost": 15.00}],
            discounts=[
                {"type": "spayed_neutered", "rate": 0.05, "amount": 42.50},
            ],
            created_at=datetime.utcnow() - timedelta(days=120),
            updated_at=datetime.utcnow(),
        ),
        EISPolicy(
            policy_id="POL-PET-2024-003",
            policy_number="PET-NY-2024-00003",
            customer_id="CUST-003",
            pet_owner_name="Michael Williams",
            plan_type="accident_illness",
            status="active",
            effective_date=date.today() - timedelta(days=200),
            expiration_date=date.today() + timedelta(days=165),
            total_premium=Decimal("1150.00"),
            annual_limit=Decimal("10000.00"),
            deductible=Decimal("250.00"),
            reimbursement_pct=80,
            pets=[pets[2], pets[3]],  # Bella and Luna
            coverages=[
                EISCoverage(
                    coverage_id="COV-007",
                    coverage_type="accident",
                    limit=Decimal("10000.00"),
                    waiting_period_days=3,
                    premium=Decimal("300.00"),
                ),
                EISCoverage(
                    coverage_id="COV-008",
                    coverage_type="illness",
                    limit=Decimal("10000.00"),
                    waiting_period_days=14,
                    premium=Decimal("600.00"),
                ),
            ],
            discounts=[
                {"type": "multi_pet", "rate": 0.10, "amount": 115.00},
                {"type": "spayed_neutered", "rate": 0.05, "amount": 57.50},
            ],
            created_at=datetime.utcnow() - timedelta(days=200),
            updated_at=datetime.utcnow(),
        ),
    ]
    for p in policies:
        _policies[p.policy_id] = p

    # Create mock claims
    claims = [
        EISClaim(
            claim_id="CLM-PET-2024-001",
            claim_number="CLM-PET-2024-00001",
            policy_id="POL-PET-2024-001",
            pet_id="PET-001",
            pet_name="Max",
            pet_species="dog",
            pet_breed="Golden Retriever",
            date_of_service=date.today() - timedelta(days=30),
            date_reported=datetime.utcnow() - timedelta(days=28),
            status="under_review",
            condition_type="accident",
            diagnosis="Torn CCL (Cranial Cruciate Ligament)",
            treatment="TPLO Surgery",
            vet_provider_id="VET-001",
            vet_clinic_name="Happy Paws Veterinary Clinic",
            amount_billed=Decimal("4500.00"),
            amount_approved=Decimal("4500.00"),
            amount_paid=Decimal("0"),
            deductible_applied=Decimal("250.00"),
            reimbursement_rate=Decimal("0.80"),
            estimated_payout=Decimal("3400.00"),
            fraud_score=0.15,
            pre_existing_flag=False,
        ),
        EISClaim(
            claim_id="CLM-PET-2024-002",
            claim_number="CLM-PET-2024-00002",
            policy_id="POL-PET-2024-002",
            pet_id="PET-002",
            pet_name="Whiskers",
            pet_species="cat",
            pet_breed="Maine Coon",
            date_of_service=date.today() - timedelta(days=15),
            date_reported=datetime.utcnow() - timedelta(days=14),
            status="approved",
            condition_type="illness",
            diagnosis="Urinary Tract Infection",
            treatment="Antibiotics and prescription diet",
            vet_provider_id="VET-002",
            vet_clinic_name="Feline Care Center",
            amount_billed=Decimal("320.00"),
            amount_approved=Decimal("320.00"),
            amount_paid=Decimal("288.00"),
            deductible_applied=Decimal("0.00"),  # Already met
            reimbursement_rate=Decimal("0.90"),
            estimated_payout=Decimal("288.00"),
            fraud_score=0.05,
            pre_existing_flag=False,
        ),
        EISClaim(
            claim_id="CLM-PET-2024-003",
            claim_number="CLM-PET-2024-00003",
            policy_id="POL-PET-2024-003",
            pet_id="PET-003",
            pet_name="Bella",
            pet_species="dog",
            pet_breed="French Bulldog",
            date_of_service=date.today() - timedelta(days=45),
            date_reported=datetime.utcnow() - timedelta(days=44),
            status="paid",
            condition_type="illness",
            diagnosis="Allergic Dermatitis",
            treatment="Apoquel medication and medicated shampoo",
            vet_provider_id="VET-003",
            vet_clinic_name="City Veterinary Hospital",
            amount_billed=Decimal("450.00"),
            amount_approved=Decimal("450.00"),
            amount_paid=Decimal("160.00"),
            deductible_applied=Decimal("250.00"),
            reimbursement_rate=Decimal("0.80"),
            estimated_payout=Decimal("160.00"),
            fraud_score=0.08,
            pre_existing_flag=False,
        ),
    ]
    for c in claims:
        _claims[c.claim_id] = c

    # Create mock vet providers
    vet_providers = [
        EISVetProvider(
            provider_id="VET-001",
            clinic_name="Happy Paws Veterinary Clinic",
            address="123 Pet Street, Chicago, IL 60601",
            phone="312-555-0100",
            email="info@happypaws.vet",
            license_number="IL-VET-12345",
            is_preferred=True,
            fraud_flag=False,
            claims_processed=45,
        ),
        EISVetProvider(
            provider_id="VET-002",
            clinic_name="Feline Care Center",
            address="456 Cat Lane, Los Angeles, CA 90210",
            phone="310-555-0200",
            email="care@felinecenter.vet",
            license_number="CA-VET-67890",
            is_preferred=True,
            fraud_flag=False,
            claims_processed=32,
        ),
        EISVetProvider(
            provider_id="VET-003",
            clinic_name="City Veterinary Hospital",
            address="789 Animal Ave, New York, NY 10001",
            phone="212-555-0300",
            email="info@cityvet.hospital",
            license_number="NY-VET-11111",
            is_preferred=False,
            fraud_flag=False,
            claims_processed=78,
        ),
    ]
    for v in vet_providers:
        _vet_providers[v.provider_id] = v


# Policies endpoints
@router.get("/policies")
async def list_policies(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    plan_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
):
    """List pet policies from mock EIS system."""
    _init_mock_data()

    policies = list(_policies.values())

    if status:
        policies = [p for p in policies if p.status == status]
    if customer_id:
        policies = [p for p in policies if p.customer_id == customer_id]
    if plan_type:
        policies = [p for p in policies if p.plan_type == plan_type]

    return {
        "policies": [p.model_dump(mode="json") for p in policies[offset : offset + limit]],
        "total": len(policies),
        "limit": limit,
        "offset": offset,
    }


@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get pet policy by ID from mock EIS system."""
    _init_mock_data()

    policy = _policies.get(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return policy.model_dump(mode="json")


@router.post("/policies")
async def create_policy(policy: EISPolicy):
    """Create a new pet policy in mock EIS system."""
    if not policy.policy_id:
        policy.policy_id = f"POL-PET-{datetime.now().year}-{str(uuid.uuid4())[:3].upper()}"

    policy.created_at = datetime.utcnow()
    policy.updated_at = datetime.utcnow()

    _policies[policy.policy_id] = policy
    logger.info(f"Created pet policy {policy.policy_id}")

    return policy.model_dump(mode="json")


# Pets endpoints
@router.get("/pets")
async def list_pets(
    species: Optional[str] = None,
    breed: Optional[str] = None,
    policy_id: Optional[str] = None,
    limit: int = Query(default=50, le=100),
):
    """List pets from mock EIS system."""
    _init_mock_data()

    pets = list(_pets.values())

    if species:
        pets = [p for p in pets if p.species.lower() == species.lower()]
    if breed:
        pets = [p for p in pets if breed.lower() in p.breed.lower()]

    return {
        "pets": [p.model_dump(mode="json") for p in pets[:limit]],
        "total": len(pets),
    }


@router.get("/pets/{pet_id}")
async def get_pet(pet_id: str):
    """Get pet by ID from mock EIS system."""
    _init_mock_data()

    pet = _pets.get(pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    return pet.model_dump(mode="json")


# Claims endpoints
@router.get("/claims")
async def list_claims(
    policy_id: Optional[str] = None,
    pet_id: Optional[str] = None,
    status: Optional[str] = None,
    condition_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
):
    """List pet claims from mock EIS system."""
    _init_mock_data()

    claims = list(_claims.values())

    if policy_id:
        claims = [c for c in claims if c.policy_id == policy_id]
    if pet_id:
        claims = [c for c in claims if c.pet_id == pet_id]
    if status:
        claims = [c for c in claims if c.status == status]
    if condition_type:
        claims = [c for c in claims if c.condition_type == condition_type]

    return {
        "claims": [c.model_dump(mode="json") for c in claims[:limit]],
        "total": len(claims),
    }


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    """Get pet claim by ID from mock EIS system."""
    _init_mock_data()

    claim = _claims.get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return claim.model_dump(mode="json")


# Customers (Pet Owners) endpoints
@router.get("/customers")
async def list_customers(limit: int = Query(default=50, le=100)):
    """List pet owners from mock EIS system."""
    _init_mock_data()

    customers = list(_customers.values())
    return {
        "customers": [c.model_dump(mode="json") for c in customers[:limit]],
        "total": len(customers),
    }


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get pet owner by ID from mock EIS system."""
    _init_mock_data()

    customer = _customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer.model_dump(mode="json")


@router.get("/customers/{customer_id}/pets")
async def get_customer_pets(customer_id: str):
    """Get pets for a customer."""
    _init_mock_data()

    customer = _customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Find policies for this customer and get their pets
    customer_policies = [p for p in _policies.values() if p.customer_id == customer_id]
    pets = []
    for policy in customer_policies:
        for pet in policy.pets:
            pet_data = pet.model_dump(mode="json")
            pet_data["policy_id"] = policy.policy_id
            pet_data["policy_status"] = policy.status
            pets.append(pet_data)

    return {"pets": pets, "total": len(pets)}


@router.get("/customers/{customer_id}/policies")
async def get_customer_policies(customer_id: str):
    """Get policies for a customer."""
    _init_mock_data()

    customer = _customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    policies = [p for p in _policies.values() if p.customer_id == customer_id]
    return {
        "policies": [
            {
                "policy_id": p.policy_id,
                "policy_number": p.policy_number,
                "plan_type": p.plan_type,
                "status": p.status,
                "effective_date": p.effective_date.isoformat(),
                "expiration_date": p.expiration_date.isoformat(),
                "total_premium": float(p.total_premium),
                "pets_covered": len(p.pets),
            }
            for p in policies
        ],
        "total": len(policies),
    }


@router.get("/customers/{customer_id}/claims")
async def get_customer_claims(customer_id: str):
    """Get claims for a customer."""
    _init_mock_data()

    customer = _customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Find policies for this customer
    customer_policy_ids = [p.policy_id for p in _policies.values() if p.customer_id == customer_id]
    claims = [c for c in _claims.values() if c.policy_id in customer_policy_ids]

    return {
        "claims": [c.model_dump(mode="json") for c in claims],
        "total": len(claims),
    }


# Vet Providers endpoints
@router.get("/vet-providers")
async def list_vet_providers(limit: int = Query(default=50, le=100)):
    """List vet providers from mock EIS system."""
    _init_mock_data()

    providers = list(_vet_providers.values())
    return {
        "providers": [p.model_dump(mode="json") for p in providers[:limit]],
        "total": len(providers),
    }


@router.get("/vet-providers/{provider_id}")
async def get_vet_provider(provider_id: str):
    """Get vet provider by ID."""
    _init_mock_data()

    provider = _vet_providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Vet provider not found")

    return provider.model_dump(mode="json")


# Webhook simulation
@router.post("/webhooks/policy")
async def trigger_policy_webhook(event_type: str, policy_id: str, timestamp: Optional[datetime] = None):
    """Simulate an EIS policy webhook event."""
    _init_mock_data()

    policy = _policies.get(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    payload = WebhookPayload(
        event_type=event_type,
        entity_id=policy_id,
        entity_type="pet_policy",
        timestamp=timestamp or datetime.utcnow(),
        data=policy.model_dump(mode="json"),
    )

    logger.info(f"Simulated policy webhook: {event_type} for {policy_id}")

    return {
        "message": "Webhook received",
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "status": "queued",
    }


@router.post("/webhooks/claim")
async def trigger_claim_webhook(
    event_type: str,
    claim_id: str,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
    timestamp: Optional[datetime] = None,
):
    """Simulate an EIS claim webhook event."""
    _init_mock_data()

    claim = _claims.get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    data = claim.model_dump(mode="json")
    if previous_status:
        data["previous_status"] = previous_status
    if new_status:
        data["new_status"] = new_status

    payload = WebhookPayload(
        event_type=event_type,
        entity_id=claim_id,
        entity_type="pet_claim",
        timestamp=timestamp or datetime.utcnow(),
        data=data,
    )

    logger.info(f"Simulated claim webhook: {event_type} for {claim_id}")

    return {
        "message": "Webhook received",
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "status": "queued",
    }


# Admin endpoints
@router.post("/admin/reset")
async def reset_mock_data():
    """Reset mock data to default state (development only)."""
    global _policies, _claims, _customers, _pets, _vet_providers
    _policies = {}
    _claims = {}
    _customers = {}
    _pets = {}
    _vet_providers = {}
    _init_mock_data()

    return {"message": "Mock data reset successfully"}
