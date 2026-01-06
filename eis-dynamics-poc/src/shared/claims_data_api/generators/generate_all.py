#!/usr/bin/env python3
"""
Unified Claims Data Generator
Generates 100 customers, 150 pets, 500+ claims with 3 fraud patterns.
Shared between EIS Dynamics POC and PetInsure360.

Author: Generated for EIS-Dynamics POC
"""

import json
import random
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# CONFIGURATION
# =============================================================================

NUM_CUSTOMERS = 100
NUM_PETS = 150
NUM_PROVIDERS = 50
NUM_CLAIMS_BASE = 500  # Additional claims beyond fraud patterns

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Base date for 1 year of history
BASE_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 30)

# =============================================================================
# REFERENCE DATA
# =============================================================================

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]

CITIES = [
    ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"), ("Chicago", "IL", "60601"),
    ("Houston", "TX", "77001"), ("Phoenix", "AZ", "85001"), ("Philadelphia", "PA", "19101"),
    ("San Antonio", "TX", "78201"), ("San Diego", "CA", "92101"), ("Dallas", "TX", "75201"),
    ("San Jose", "CA", "95101"), ("Austin", "TX", "78701"), ("Seattle", "WA", "98101"),
    ("Denver", "CO", "80201"), ("Boston", "MA", "02101"), ("Portland", "OR", "97201"),
    ("Atlanta", "GA", "30301"), ("Miami", "FL", "33101"), ("Nashville", "TN", "37201")
]

DOG_BREEDS = [
    "Labrador Retriever", "German Shepherd", "Golden Retriever", "French Bulldog",
    "Bulldog", "Poodle", "Beagle", "Rottweiler", "Yorkshire Terrier", "Boxer",
    "Dachshund", "Siberian Husky", "Great Dane", "Doberman Pinscher", "Shih Tzu",
    "Boston Terrier", "Bernese Mountain Dog", "Pomeranian", "Mixed Breed"
]

CAT_BREEDS = [
    "Domestic Shorthair", "Domestic Longhair", "Maine Coon", "Ragdoll",
    "British Shorthair", "Persian", "Siamese", "Bengal", "Abyssinian",
    "Scottish Fold", "Sphynx", "Russian Blue"
]

PET_NAMES = [
    "Max", "Bella", "Charlie", "Luna", "Cooper", "Daisy", "Buddy", "Lucy", "Rocky",
    "Sadie", "Bear", "Molly", "Duke", "Bailey", "Tucker", "Maggie", "Jack", "Sophie",
    "Oliver", "Chloe", "Leo", "Penny", "Milo", "Zoey", "Zeus", "Lily", "Winston",
    "Stella", "Teddy", "Coco", "Murphy", "Rosie", "Finn", "Ruby", "Oscar", "Gracie"
]

PLAN_TYPES = [
    {"type": "accident_only", "name": "Accident Only", "premium": 25, "deductible": 500, "limit": 5000, "pct": 70},
    {"type": "accident_illness", "name": "Accident + Illness", "premium": 45, "deductible": 250, "limit": 10000, "pct": 80},
    {"type": "comprehensive", "name": "Comprehensive", "premium": 75, "deductible": 100, "limit": 20000, "pct": 90},
]

CLAIM_TYPES = [
    {"type": "Wellness Exam", "category": "preventive", "min": 50, "max": 150, "code": "Z00.0"},
    {"type": "Vaccination", "category": "preventive", "min": 75, "max": 200, "code": "Z23"},
    {"type": "Dental Cleaning", "category": "dental", "min": 200, "max": 800, "code": "K08.3"},
    {"type": "Emergency Visit", "category": "emergency", "min": 150, "max": 500, "code": "R68.89"},
    {"type": "X-Ray", "category": "diagnostic", "min": 100, "max": 400, "code": "Z01.89"},
    {"type": "Blood Test", "category": "diagnostic", "min": 80, "max": 250, "code": "Z01.812"},
    {"type": "Allergy Treatment", "category": "illness", "min": 100, "max": 500, "code": "L50.0"},
    {"type": "Skin Condition", "category": "illness", "min": 150, "max": 600, "code": "L30.9"},
    {"type": "Ear Infection", "category": "illness", "min": 100, "max": 300, "code": "H60.9"},
    {"type": "Digestive Issues", "category": "illness", "min": 200, "max": 800, "code": "K59.9"},
    {"type": "UTI Treatment", "category": "illness", "min": 150, "max": 450, "code": "N39.0"},
    {"type": "ACL Surgery", "category": "surgery", "min": 3000, "max": 6000, "code": "S83.5"},
    {"type": "Foreign Body Removal", "category": "emergency", "min": 1500, "max": 5000, "code": "T18.9"},
    {"type": "Fracture Treatment", "category": "emergency", "min": 1000, "max": 4000, "code": "S82.9"},
]

VET_PREFIXES = ["Animal", "Pet", "Companion", "Family", "City", "Valley", "Meadow", "Oak", "Central", "Premier"]
VET_SUFFIXES = ["Veterinary Hospital", "Animal Hospital", "Pet Clinic", "Vet Center", "Animal Care"]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def gen_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12].upper()}"

def gen_date(start: datetime, end: datetime) -> date:
    delta = end - start
    days = random.randint(0, delta.days)
    return (start + timedelta(days=days)).date()

def gen_email(first: str, last: str) -> str:
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com"]
    return f"{first.lower()}.{last.lower()}{random.randint(1, 999)}@{random.choice(domains)}"

def gen_phone() -> str:
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

def now_iso() -> str:
    return datetime.now().isoformat()


# =============================================================================
# DATA GENERATORS
# =============================================================================

def generate_customers() -> List[Dict]:
    """Generate 100 customers with various segments."""
    customers = []

    # Segment distribution
    segments = (
        [("new", 20)] +
        [("standard", 50)] +
        [("loyal", 20)] +
        [("high_risk", 7)] +
        [("fraud_suspect", 3)]
    )

    segment_list = []
    for seg, count in segments:
        segment_list.extend([seg] * count)
    random.shuffle(segment_list)

    for i in range(NUM_CUSTOMERS):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city, state, zip_code = random.choice(CITIES)
        segment = segment_list[i]

        # Tenure based on segment
        if segment == "new":
            tenure_days = random.randint(14, 90)
        elif segment == "loyal":
            tenure_days = random.randint(548, 730)  # 1.5-2 years
        else:
            tenure_days = random.randint(90, 548)

        customer_since = (END_DATE - timedelta(days=tenure_days)).date()

        customers.append({
            "customer_id": f"CUST-{str(i+1).zfill(3)}",
            "first_name": first,
            "last_name": last,
            "email": gen_email(first, last),
            "phone": gen_phone(),
            "address_line1": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "date_of_birth": gen_date(datetime(1960, 1, 1), datetime(2000, 1, 1)).isoformat(),
            "customer_since": customer_since.isoformat(),
            "preferred_contact": random.choice(["email", "phone", "sms"]),
            "marketing_opt_in": random.choice([True, False]),
            "referral_source": random.choice(["google", "facebook", "referral", "vet_recommendation"]),
            "segment": segment,
            "lifetime_value": round(random.uniform(500, 8000), 2),
            "risk_tier": "high" if segment in ["high_risk", "fraud_suspect"] else random.choice(["low", "medium"]),
            "total_claims": 0,  # Will be updated
            "total_paid": 0.0,  # Will be updated
            "notes": None,
            "created_at": now_iso(),
            "updated_at": now_iso()
        })

    return customers


def generate_pets(customers: List[Dict]) -> List[Dict]:
    """Generate 150 pets distributed among customers."""
    pets = []
    customer_ids = [c["customer_id"] for c in customers]

    # Ensure each customer has at least 1 pet, some have 2-3
    pet_assignments = []
    for cid in customer_ids:
        count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        pet_assignments.extend([cid] * count)

    # Trim or extend to exactly 150
    random.shuffle(pet_assignments)
    pet_assignments = pet_assignments[:NUM_PETS]
    while len(pet_assignments) < NUM_PETS:
        pet_assignments.append(random.choice(customer_ids))

    for i, cid in enumerate(pet_assignments):
        species = random.choices(["dog", "cat", "exotic"], weights=[65, 30, 5])[0]

        if species == "dog":
            breed = random.choice(DOG_BREEDS)
            weight = random.randint(15, 90)
        elif species == "cat":
            breed = random.choice(CAT_BREEDS)
            weight = random.randint(6, 18)
        else:
            breed = random.choice(["Rabbit", "Guinea Pig", "Hamster", "Ferret"])
            weight = random.uniform(1, 8)

        # Age distribution
        age_years = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                   weights=[10, 15, 15, 15, 12, 10, 8, 6, 5, 4])[0]
        dob = (END_DATE - timedelta(days=age_years * 365 + random.randint(0, 180))).date()

        # Pre-existing conditions (20% chance)
        pre_existing = []
        if random.random() < 0.2:
            conditions = [
                ("Allergies", "L50.0"),
                ("Hip Dysplasia", "M16.9"),
                ("Diabetes", "E11.9"),
                ("Heart Murmur", "R01.1"),
                ("Arthritis", "M19.90")
            ]
            cond = random.choice(conditions)
            pre_existing.append({
                "condition_name": cond[0],
                "diagnosis_date": gen_date(BASE_DATE - timedelta(days=365), BASE_DATE).isoformat(),
                "diagnosis_code": cond[1],
                "notes": f"Diagnosed prior to policy",
                "is_excluded": True
            })

        pets.append({
            "pet_id": f"PET-{str(i+1).zfill(3)}",
            "customer_id": cid,
            "name": random.choice(PET_NAMES),
            "species": species,
            "breed": breed,
            "gender": random.choice(["male", "female"]),
            "date_of_birth": dob.isoformat(),
            "weight_lbs": round(weight, 1),
            "color": random.choice(["black", "white", "brown", "golden", "gray", "mixed"]),
            "microchip_id": f"MC{random.randint(100000000, 999999999)}" if random.random() > 0.3 else None,
            "is_neutered": random.choice([True, False]),
            "pre_existing_conditions": pre_existing,
            "vaccination_status": random.choice(["up_to_date", "overdue"]),
            "adoption_date": (dob + timedelta(days=random.randint(60, 180))).isoformat(),
            "is_active": True,
            "created_at": now_iso(),
            "updated_at": now_iso()
        })

    return pets


def generate_providers() -> List[Dict]:
    """Generate 50 vet providers."""
    providers = []

    for i in range(NUM_PROVIDERS):
        city, state, zip_code = random.choice(CITIES)
        is_in_network = random.random() < 0.7

        providers.append({
            "provider_id": f"PROV-{str(i+1).zfill(3)}",
            "name": f"{random.choice(VET_PREFIXES)} {random.choice(VET_SUFFIXES)}",
            "provider_type": random.choice(["general", "emergency", "specialty"]),
            "address": f"{random.randint(100, 9999)} Medical Plaza",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "phone": gen_phone(),
            "email": f"contact@vet{i+1}.com",
            "is_in_network": is_in_network,
            "average_rating": round(random.uniform(3.5, 5.0), 1),
            "total_reviews": random.randint(10, 500),
            "accepts_emergency": random.choice([True, False]),
            "operating_hours": random.choice(["8AM-6PM", "7AM-9PM", "24/7", "9AM-5PM"]),
            "specialties": random.sample(["surgery", "oncology", "cardiology", "dermatology", "orthopedics"], k=random.randint(0, 2)),
            "license_number": f"VET{state}{random.randint(10000, 99999)}",
            "stats": {
                "total_claims": 0,
                "total_amount": 0.0,
                "average_claim": 0.0,
                "denial_rate": round(random.uniform(0.02, 0.15), 3),
                "fraud_rate": round(random.uniform(0.005, 0.03), 4),
                "customer_concentration": {}
            },
            "created_at": now_iso()
        })

    return providers


def generate_policies(customers: List[Dict], pets: List[Dict]) -> List[Dict]:
    """Generate policies - one per pet, some pets have multiple."""
    policies = []

    pet_to_customer = {p["pet_id"]: p["customer_id"] for p in pets}

    for pet in pets:
        plan = random.choice(PLAN_TYPES)
        customer = next(c for c in customers if c["customer_id"] == pet["customer_id"])

        # Policy effective date based on customer tenure
        customer_since = datetime.fromisoformat(customer["customer_since"])
        effective = customer_since + timedelta(days=random.randint(0, 30))
        expiration = effective + timedelta(days=365)

        # Waiting period calculation
        waiting = {
            "accident_days": 14,
            "illness_days": 14,
            "orthopedic_days": 180,
            "cancer_days": 30,
            "policy_effective_date": effective.date().isoformat(),
            "all_satisfied": (END_DATE.date() - effective.date()).days > 180
        }

        # Calculate used limits based on segment
        limit_pct_used = 0.0
        if customer["segment"] == "high_risk":
            limit_pct_used = random.uniform(0.5, 0.9)
        elif customer["segment"] == "loyal":
            limit_pct_used = random.uniform(0.2, 0.5)
        else:
            limit_pct_used = random.uniform(0.0, 0.3)

        used_this_year = round(plan["limit"] * limit_pct_used, 2)

        policies.append({
            "policy_id": f"POL-{pet['pet_id'][4:]}",  # Match pet ID
            "policy_number": f"PI{datetime.now().year}-{random.randint(100000, 999999)}",
            "customer_id": pet["customer_id"],
            "pet_id": pet["pet_id"],
            "plan_type": plan["type"],
            "plan_name": plan["name"],
            "monthly_premium": plan["premium"] + random.uniform(-5, 10),
            "annual_deductible": plan["deductible"],
            "deductible_met": plan["deductible"] * random.uniform(0, 1),
            "reimbursement_percentage": plan["pct"],
            "coverage_limit": {
                "annual_limit": plan["limit"],
                "per_incident_limit": plan["limit"] / 2,
                "lifetime_limit": plan["limit"] * 10,
                "used_this_year": used_this_year,
                "remaining": plan["limit"] - used_this_year
            },
            "waiting_period": waiting,
            "exclusions": [],
            "effective_date": effective.date().isoformat(),
            "expiration_date": expiration.date().isoformat(),
            "status": "active",
            "payment_method": random.choice(["credit_card", "debit_card", "bank_transfer"]),
            "payment_frequency": random.choice(["monthly", "annual"]),
            "includes_wellness": random.choice([True, False]),
            "includes_dental": random.choice([True, False]),
            "includes_behavioral": False,
            "renewal_count": random.randint(0, 3),
            "cancellation_date": None,
            "created_at": now_iso(),
            "updated_at": now_iso()
        })

    return policies


def generate_fraud_pattern_1(customers: List[Dict], pets: List[Dict], policies: List[Dict], providers: List[Dict]) -> tuple:
    """
    Fraud Pattern #1: Chronic Condition Gaming
    Customer: Jennifer Martinez with German Shepherd "Rocky" who has hip dysplasia
    Files multiple "accident" claims for hip injuries at different providers
    """
    # Create the fraud customer
    fraud_customer = {
        "customer_id": "CUST-023",
        "first_name": "Jennifer",
        "last_name": "Martinez",
        "email": "jennifer.martinez123@gmail.com",
        "phone": "(555) 123-4567",
        "address_line1": "1234 Oak Street",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90001",
        "date_of_birth": "1985-03-15",
        "customer_since": "2023-06-01",
        "preferred_contact": "email",
        "marketing_opt_in": True,
        "referral_source": "google",
        "segment": "fraud_suspect",
        "lifetime_value": 5200.00,
        "risk_tier": "high",
        "total_claims": 4,
        "total_paid": 6100.00,
        "notes": "Multiple hip-related claims - pattern detected",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    # Create the pet with pre-existing hip dysplasia
    fraud_pet = {
        "pet_id": "PET-034",
        "customer_id": "CUST-023",
        "name": "Rocky",
        "species": "dog",
        "breed": "German Shepherd",
        "gender": "male",
        "date_of_birth": "2018-05-20",
        "weight_lbs": 85.0,
        "color": "black and tan",
        "microchip_id": "MC987654321",
        "is_neutered": True,
        "pre_existing_conditions": [
            {
                "condition_name": "Hip Dysplasia",
                "diagnosis_date": "2023-02-15",
                "diagnosis_code": "M16.9",
                "notes": "Documented in pre-policy exam. Moderate bilateral hip dysplasia.",
                "is_excluded": True
            }
        ],
        "vaccination_status": "up_to_date",
        "adoption_date": "2018-08-01",
        "is_active": True,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    # Create policy
    fraud_policy = {
        "policy_id": "POL-034",
        "policy_number": "PI2024-FRAUD01",
        "customer_id": "CUST-023",
        "pet_id": "PET-034",
        "plan_type": "accident_illness",
        "plan_name": "Accident + Illness",
        "monthly_premium": 48.00,
        "annual_deductible": 250,
        "deductible_met": 250.0,
        "reimbursement_percentage": 80,
        "coverage_limit": {
            "annual_limit": 10000,
            "per_incident_limit": 5000,
            "lifetime_limit": 100000,
            "used_this_year": 6100.00,
            "remaining": 3900.00
        },
        "waiting_period": {
            "accident_days": 14,
            "illness_days": 14,
            "orthopedic_days": 180,
            "cancer_days": 30,
            "policy_effective_date": "2023-06-15",
            "all_satisfied": True
        },
        "exclusions": [
            {
                "exclusion_type": "pre_existing",
                "description": "Hip Dysplasia - documented prior to policy",
                "diagnosis_codes": ["M16.9"],
                "is_permanent": True
            }
        ],
        "effective_date": "2023-06-15",
        "expiration_date": "2025-06-15",
        "status": "active",
        "payment_method": "credit_card",
        "payment_frequency": "monthly",
        "includes_wellness": False,
        "includes_dental": True,
        "includes_behavioral": False,
        "renewal_count": 1,
        "cancellation_date": None,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    # Create 4 claims - all hip/leg injuries filed as "accidents"
    fraud_claims = []
    claim_data = [
        ("2024-02-10", "Hip injury from fall off deck", 1450.00, "PROV-011"),
        ("2024-05-22", "Leg sprain from jumping out of car", 1200.00, "PROV-018"),
        ("2024-08-15", "Hip injury from falling down stairs", 1800.00, "PROV-025"),
        ("2024-11-08", "Back leg injury from slipping on ice", 1650.00, "PROV-033"),
    ]

    for i, (service_date, desc, amount, provider_id) in enumerate(claim_data):
        fraud_claims.append({
            "claim_id": f"CLM-023-{str(i+1).zfill(3)}",
            "claim_number": f"CLM2024-FRAUD1-{i+1}",
            "policy_id": "POL-034",
            "pet_id": "PET-034",
            "customer_id": "CUST-023",
            "provider_id": provider_id,
            "claim_type": "accident",
            "claim_category": "accident",
            "diagnosis_code": "S83.5" if "hip" in desc.lower() else "S86.9",
            "diagnosis_description": desc,
            "service_date": service_date,
            "submitted_date": (datetime.fromisoformat(service_date) + timedelta(days=random.randint(1, 5))).date().isoformat(),
            "treatment_notes": f"{desc}. X-rays taken. Pain management prescribed. Physical therapy recommended.",
            "line_items": [
                {"line_id": f"LI-{i}-1", "description": "Emergency exam", "amount": 150.00, "is_covered": True},
                {"line_id": f"LI-{i}-2", "description": "Digital X-rays (4 views)", "amount": 320.00, "is_covered": True},
                {"line_id": f"LI-{i}-3", "description": "Pain medication", "amount": 85.00, "is_covered": True},
                {"line_id": f"LI-{i}-4", "description": "Treatment and bandaging", "amount": amount - 555, "is_covered": True},
            ],
            "claim_amount": amount,
            "deductible_applied": 0.0 if i > 0 else 250.0,
            "covered_amount": amount * 0.8 if i > 0 else (amount - 250) * 0.8,
            "paid_amount": amount * 0.8 if i > 0 else (amount - 250) * 0.8,
            "status": "paid",
            "denial_reason": None,
            "processing_days": random.randint(3, 10),
            "is_emergency": True,
            "is_recurring": False,
            "documents": [],
            "ai_decision": None,
            "ai_reasoning": None,
            "ai_risk_score": None,
            "ai_quality_score": None,
            "fraud_pattern": "chronic_condition_gaming",
            "created_at": now_iso(),
            "updated_at": now_iso()
        })

    return fraud_customer, fraud_pet, fraud_policy, fraud_claims


def generate_fraud_pattern_2(customers: List[Dict], pets: List[Dict], policies: List[Dict], providers: List[Dict]) -> tuple:
    """
    Fraud Pattern #2: Provider Collusion
    Customer: David Thompson with Labrador "Luna"
    Always uses same out-of-network provider, claims near annual limit
    """
    # Create special provider for collusion
    fraud_provider = {
        "provider_id": "PROV-099",
        "name": "Valley Pet Care",
        "provider_type": "general",
        "address": "999 Suspicious Lane",
        "city": "San Diego",
        "state": "CA",
        "zip_code": "92101",
        "phone": "(555) 999-8888",
        "email": "contact@valleypetcare.com",
        "is_in_network": False,  # Out of network
        "average_rating": 4.2,
        "total_reviews": 45,
        "accepts_emergency": True,
        "operating_hours": "8AM-8PM",
        "specialties": [],
        "license_number": "VETCA99999",
        "stats": {
            "total_claims": 26,
            "total_amount": 78500.00,
            "average_claim": 3019.23,  # 3.5x industry average
            "denial_rate": 0.04,
            "fraud_rate": 0.028,  # Slightly elevated but below 5% threshold
            "customer_concentration": {"CUST-067": 0.15}  # 15% from one customer!
        },
        "created_at": now_iso()
    }

    fraud_customer = {
        "customer_id": "CUST-067",
        "first_name": "David",
        "last_name": "Thompson",
        "email": "david.thompson456@yahoo.com",
        "phone": "(555) 456-7890",
        "address_line1": "5678 Maple Drive",
        "city": "San Diego",
        "state": "CA",
        "zip_code": "92101",
        "date_of_birth": "1978-11-22",
        "customer_since": "2023-01-15",
        "preferred_contact": "phone",
        "marketing_opt_in": False,
        "referral_source": "referral",
        "segment": "fraud_suspect",
        "lifetime_value": 19200.00,
        "risk_tier": "high",
        "total_claims": 4,
        "total_paid": 19200.00,
        "notes": "Exclusive use of out-of-network Valley Pet Care - unusual pattern",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    fraud_pet = {
        "pet_id": "PET-089",
        "customer_id": "CUST-067",
        "name": "Luna",
        "species": "dog",
        "breed": "Labrador Retriever",
        "gender": "female",
        "date_of_birth": "2020-07-10",
        "weight_lbs": 65.0,
        "color": "yellow",
        "microchip_id": "MC555666777",
        "is_neutered": True,
        "pre_existing_conditions": [],
        "vaccination_status": "up_to_date",
        "adoption_date": "2020-09-15",
        "is_active": True,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    fraud_policy = {
        "policy_id": "POL-089",
        "policy_number": "PI2024-FRAUD02",
        "customer_id": "CUST-067",
        "pet_id": "PET-089",
        "plan_type": "accident_illness",
        "plan_name": "Accident + Illness",
        "monthly_premium": 52.00,
        "annual_deductible": 250,
        "deductible_met": 250.0,
        "reimbursement_percentage": 80,
        "coverage_limit": {
            "annual_limit": 10000,
            "per_incident_limit": 5000,
            "lifetime_limit": 100000,
            "used_this_year": 9700.00,  # Near limit
            "remaining": 300.00
        },
        "waiting_period": {
            "accident_days": 14,
            "illness_days": 14,
            "orthopedic_days": 180,
            "cancer_days": 30,
            "policy_effective_date": "2023-02-01",
            "all_satisfied": True
        },
        "exclusions": [],
        "effective_date": "2023-02-01",
        "expiration_date": "2025-02-01",
        "status": "active",
        "payment_method": "credit_card",
        "payment_frequency": "monthly",
        "includes_wellness": False,
        "includes_dental": False,
        "includes_behavioral": False,
        "renewal_count": 1,
        "cancellation_date": None,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    # Claims - all from same provider, vague descriptions, near limits
    fraud_claims = []
    claim_data = [
        ("2024-03-15", "Comprehensive treatment package", 4750.00),  # Round-ish
        ("2024-04-28", "Follow-up care and diagnostics", 4700.00),
        # Policy renewed here
        ("2024-05-20", "Specialist consultation and treatment", 4800.00),
        ("2024-09-10", "Advanced diagnostic workup", 4900.00),  # Just under $5k
    ]

    for i, (service_date, desc, amount) in enumerate(claim_data):
        fraud_claims.append({
            "claim_id": f"CLM-067-{str(i+1).zfill(3)}",
            "claim_number": f"CLM2024-FRAUD2-{i+1}",
            "policy_id": "POL-089",
            "pet_id": "PET-089",
            "customer_id": "CUST-067",
            "provider_id": "PROV-099",  # Always same provider
            "claim_type": "illness",
            "claim_category": "illness",
            "diagnosis_code": "R68.89",  # Vague "other general symptoms"
            "diagnosis_description": desc,
            "service_date": service_date,
            "submitted_date": (datetime.fromisoformat(service_date) + timedelta(days=2)).date().isoformat(),
            "treatment_notes": f"{desc}. Multiple procedures performed. Continued monitoring recommended.",
            "line_items": [
                {"line_id": f"LI-{i}-1", "description": "Comprehensive examination", "amount": 500.00, "is_covered": True},
                {"line_id": f"LI-{i}-2", "description": "Diagnostic procedures", "amount": 1500.00, "is_covered": True},
                {"line_id": f"LI-{i}-3", "description": "Treatment protocol", "amount": amount - 2000, "is_covered": True},
            ],
            "claim_amount": amount,
            "deductible_applied": 250.0 if i == 0 else 0.0,
            "covered_amount": (amount - 250) * 0.8 if i == 0 else amount * 0.8,
            "paid_amount": (amount - 250) * 0.8 if i == 0 else amount * 0.8,
            "status": "paid",
            "denial_reason": None,
            "processing_days": random.randint(5, 12),
            "is_emergency": False,
            "is_recurring": False,
            "documents": [],
            "ai_decision": None,
            "ai_reasoning": None,
            "ai_risk_score": None,
            "ai_quality_score": None,
            "fraud_pattern": "provider_collusion",
            "created_at": now_iso(),
            "updated_at": now_iso()
        })

    return fraud_customer, fraud_pet, fraud_policy, fraud_claims, fraud_provider


def generate_fraud_pattern_3(customers: List[Dict], pets: List[Dict], policies: List[Dict], providers: List[Dict]) -> tuple:
    """
    Fraud Pattern #3: Staged Timing
    Customer: Michelle Chen with French Bulldog "Mochi"
    New policy, IVDD claim filed 2 days after waiting period
    """
    fraud_customer = {
        "customer_id": "CUST-089",
        "first_name": "Michelle",
        "last_name": "Chen",
        "email": "michelle.chen789@outlook.com",
        "phone": "(555) 789-0123",
        "address_line1": "9012 Pine Lane",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "date_of_birth": "1990-08-05",
        "customer_since": "2024-10-01",  # Very new
        "preferred_contact": "email",
        "marketing_opt_in": True,
        "referral_source": "google",
        "segment": "fraud_suspect",
        "lifetime_value": 0.0,  # New customer
        "risk_tier": "high",
        "total_claims": 1,
        "total_paid": 0.0,  # Pending
        "notes": "IVDD claim filed 2 days after waiting period - statistical anomaly",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    # French Bulldog - 10x higher IVDD risk
    fraud_pet = {
        "pet_id": "PET-112",
        "customer_id": "CUST-089",
        "name": "Mochi",
        "species": "dog",
        "breed": "French Bulldog",  # High IVDD risk breed
        "gender": "male",
        "date_of_birth": "2021-12-15",
        "weight_lbs": 28.0,
        "color": "fawn",
        "microchip_id": "MC111222333",
        "is_neutered": True,
        "pre_existing_conditions": [],  # None documented - suspicious
        "vaccination_status": "up_to_date",
        "adoption_date": "2022-02-20",
        "is_active": True,
        "notes": "Pre-policy vet records unavailable - clinic 'closed'",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    fraud_policy = {
        "policy_id": "POL-112",
        "policy_number": "PI2024-FRAUD03",
        "customer_id": "CUST-089",
        "pet_id": "PET-112",
        "plan_type": "comprehensive",
        "plan_name": "Comprehensive",
        "monthly_premium": 85.00,
        "annual_deductible": 100,
        "deductible_met": 0.0,
        "reimbursement_percentage": 90,
        "coverage_limit": {
            "annual_limit": 20000,
            "per_incident_limit": 10000,
            "lifetime_limit": 200000,
            "used_this_year": 0.00,
            "remaining": 20000.00
        },
        "waiting_period": {
            "accident_days": 14,
            "illness_days": 14,
            "orthopedic_days": 180,
            "cancer_days": 30,
            "policy_effective_date": "2024-10-01",
            "all_satisfied": False  # Just barely past illness waiting
        },
        "exclusions": [],
        "effective_date": "2024-10-01",
        "expiration_date": "2025-10-01",
        "status": "active",
        "payment_method": "credit_card",
        "payment_frequency": "monthly",
        "includes_wellness": True,
        "includes_dental": True,
        "includes_behavioral": True,
        "renewal_count": 0,
        "cancellation_date": None,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }

    # IVDD claim - 2 days after waiting period
    fraud_claims = [{
        "claim_id": "CLM-089-001",
        "claim_number": "CLM2024-FRAUD3-1",
        "policy_id": "POL-112",
        "pet_id": "PET-112",
        "customer_id": "CUST-089",
        "provider_id": "PROV-015",
        "claim_type": "illness",
        "claim_category": "emergency",
        "diagnosis_code": "G95.89",  # IVDD
        "diagnosis_description": "Intervertebral Disc Disease (IVDD) - acute onset, surgical intervention required",
        "service_date": "2024-10-17",  # Day 17 - just 2 days after 14-day waiting
        "submitted_date": "2024-10-18",
        "treatment_notes": "Emergency presentation for acute hind limb paralysis. MRI confirmed IVDD at T12-L1. Emergency hemilaminectomy performed. Post-surgical hospitalization 3 days.",
        "line_items": [
            {"line_id": "LI-IVDD-1", "description": "Emergency examination", "amount": 250.00, "is_covered": True},
            {"line_id": "LI-IVDD-2", "description": "MRI spine", "amount": 1800.00, "is_covered": True},
            {"line_id": "LI-IVDD-3", "description": "Pre-surgical bloodwork", "amount": 185.00, "is_covered": True},
            {"line_id": "LI-IVDD-4", "description": "General anesthesia", "amount": 450.00, "is_covered": True},
            {"line_id": "LI-IVDD-5", "description": "Hemilaminectomy surgery", "amount": 2800.00, "is_covered": True},
            {"line_id": "LI-IVDD-6", "description": "Post-op hospitalization (3 nights)", "amount": 750.00, "is_covered": True},
            {"line_id": "LI-IVDD-7", "description": "Pain management protocol", "amount": 165.00, "is_covered": True},
            {"line_id": "LI-IVDD-8", "description": "Physical therapy consultation", "amount": 100.00, "is_covered": True},
        ],
        "claim_amount": 6500.00,
        "deductible_applied": 100.0,
        "covered_amount": 5760.00,  # (6500-100) * 0.9
        "paid_amount": 0.0,  # Pending review
        "status": "under_review",
        "denial_reason": None,
        "processing_days": None,
        "is_emergency": True,
        "is_recurring": False,
        "documents": [
            {"document_id": "DOC-001", "document_type": "invoice", "filename": "invoice_oct17.pdf", "upload_date": now_iso(), "verified": True},
            {"document_id": "DOC-002", "document_type": "medical_record", "filename": "mri_report.pdf", "upload_date": now_iso(), "verified": True},
            {"document_id": "DOC-003", "document_type": "medical_record", "filename": "surgery_notes.pdf", "upload_date": now_iso(), "verified": True},
        ],
        "ai_decision": None,
        "ai_reasoning": None,
        "ai_risk_score": None,
        "ai_quality_score": None,
        "fraud_pattern": "staged_timing",
        "notes": "Pre-policy vet records requested - customer states clinic closed. Documentation unusually complete for emergency.",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }]

    return fraud_customer, fraud_pet, fraud_policy, fraud_claims


def generate_normal_claims(customers: List[Dict], pets: List[Dict], policies: List[Dict], providers: List[Dict]) -> List[Dict]:
    """Generate ~500 normal claims for non-fraud customers."""
    claims = []

    # Get non-fraud customers
    normal_customers = [c for c in customers if c["segment"] != "fraud_suspect"]
    normal_pets = [p for p in pets if p["customer_id"] in [c["customer_id"] for c in normal_customers]]

    pet_to_policy = {}
    for pol in policies:
        pet_to_policy[pol["pet_id"]] = pol

    claim_count = 0
    for pet in normal_pets:
        if pet["pet_id"] not in pet_to_policy:
            continue

        policy = pet_to_policy[pet["pet_id"]]
        customer = next((c for c in customers if c["customer_id"] == pet["customer_id"]), None)
        if not customer:
            continue

        # Number of claims based on segment
        if customer["segment"] == "new":
            num_claims = random.randint(0, 1)
        elif customer["segment"] == "loyal":
            num_claims = random.randint(3, 8)
        elif customer["segment"] == "high_risk":
            num_claims = random.randint(4, 10)
        else:
            num_claims = random.randint(1, 4)

        for _ in range(num_claims):
            claim_type = random.choice(CLAIM_TYPES)
            provider = random.choice(providers)

            service_date = gen_date(
                datetime.fromisoformat(policy["effective_date"]),
                END_DATE
            )

            amount = round(random.uniform(claim_type["min"], claim_type["max"]), 2)

            claim_count += 1
            claims.append({
                "claim_id": f"CLM-{str(claim_count).zfill(5)}",
                "claim_number": f"CLM2024-{random.randint(100000, 999999)}",
                "policy_id": policy["policy_id"],
                "pet_id": pet["pet_id"],
                "customer_id": customer["customer_id"],
                "provider_id": provider["provider_id"],
                "claim_type": claim_type["type"].lower().replace(" ", "_"),
                "claim_category": claim_type["category"],
                "diagnosis_code": claim_type["code"],
                "diagnosis_description": claim_type["type"],
                "service_date": service_date.isoformat(),
                "submitted_date": (service_date + timedelta(days=random.randint(1, 7))).isoformat(),
                "treatment_notes": f"Treatment for {claim_type['type'].lower()}. Pet responded well.",
                "line_items": [
                    {
                        "line_id": f"LI-{claim_count}-1",
                        "description": claim_type["type"],
                        "amount": amount,
                        "is_covered": True
                    }
                ],
                "claim_amount": amount,
                "deductible_applied": min(policy["annual_deductible"], amount) if random.random() < 0.3 else 0.0,
                "covered_amount": amount * (policy["reimbursement_percentage"] / 100),
                "paid_amount": amount * (policy["reimbursement_percentage"] / 100),
                "status": random.choices(
                    ["paid", "approved", "under_review", "denied"],
                    weights=[60, 20, 15, 5]
                )[0],
                "denial_reason": random.choice(["pre_existing", "waiting_period", "not_covered"]) if random.random() < 0.05 else None,
                "processing_days": random.randint(1, 15),
                "is_emergency": claim_type["category"] == "emergency",
                "is_recurring": claim_type["category"] == "chronic",
                "documents": [],
                "ai_decision": None,
                "ai_reasoning": None,
                "ai_risk_score": None,
                "ai_quality_score": None,
                "fraud_pattern": None,
                "created_at": now_iso(),
                "updated_at": now_iso()
            })

    return claims


def generate_medical_codes() -> List[Dict]:
    """Generate medical reference codes."""
    codes = []

    code_data = [
        ("Z00.0", "General health exam", "preventive", False, 50, 150),
        ("Z23", "Vaccination encounter", "preventive", False, 75, 200),
        ("K08.3", "Dental disorder", "dental", False, 200, 800),
        ("R68.89", "Other general symptoms", "diagnostic", False, 100, 500),
        ("Z01.89", "Diagnostic exam", "diagnostic", False, 80, 400),
        ("Z01.812", "Laboratory examination", "diagnostic", False, 50, 250),
        ("L50.0", "Allergic urticaria", "illness", True, 100, 500),
        ("L30.9", "Dermatitis unspecified", "illness", True, 150, 600),
        ("H60.9", "Otitis externa", "illness", False, 100, 300),
        ("K59.9", "Functional intestinal disorder", "illness", False, 200, 800),
        ("N39.0", "Urinary tract infection", "illness", False, 150, 450),
        ("S83.5", "Cruciate ligament injury", "surgery", False, 3000, 6000),
        ("T18.9", "Foreign body", "emergency", False, 1500, 5000),
        ("S82.9", "Fracture", "emergency", False, 1000, 4000),
        ("T65.8", "Toxic effect", "emergency", False, 500, 3000),
        ("E11.9", "Type 2 diabetes", "chronic", True, 500, 2000),
        ("M16.9", "Hip osteoarthritis", "chronic", True, 800, 3000),
        ("G95.89", "IVDD - Intervertebral Disc Disease", "emergency", True, 4000, 10000),
        ("R01.1", "Heart murmur", "chronic", True, 200, 1000),
        ("M19.90", "Osteoarthritis", "chronic", True, 300, 1500),
    ]

    for code, desc, category, chronic, min_cost, max_cost in code_data:
        codes.append({
            "code": code,
            "description": desc,
            "category": category,
            "is_chronic": chronic,
            "typical_treatment_cost_min": min_cost,
            "typical_treatment_cost_max": max_cost,
            "typical_treatment_duration_days": random.randint(1, 30),
            "related_codes": []
        })

    return codes


def generate_payments(customers: List[Dict], policies: List[Dict], claims: List[Dict]) -> List[Dict]:
    """Generate payment history."""
    payments = []
    payment_id = 0

    # Premium payments
    for policy in policies:
        effective = datetime.fromisoformat(policy["effective_date"])
        months = min(12, (END_DATE - effective).days // 30)

        for month in range(months):
            payment_id += 1
            payment_date = (effective + timedelta(days=month * 30)).date()
            payments.append({
                "payment_id": f"PAY-{str(payment_id).zfill(6)}",
                "customer_id": policy["customer_id"],
                "policy_id": policy["policy_id"],
                "claim_id": None,
                "payment_type": "premium",
                "amount": policy["monthly_premium"],
                "payment_date": payment_date.isoformat(),
                "payment_method": policy["payment_method"],
                "status": "completed",
                "reference_number": f"REF{random.randint(100000, 999999)}"
            })

    # Claim payouts
    for claim in claims:
        if claim["status"] in ["paid", "approved"] and claim["paid_amount"] > 0:
            payment_id += 1
            service_date = datetime.fromisoformat(claim["service_date"])
            payment_date = (service_date + timedelta(days=random.randint(5, 20))).date()
            payments.append({
                "payment_id": f"PAY-{str(payment_id).zfill(6)}",
                "customer_id": claim["customer_id"],
                "policy_id": claim["policy_id"],
                "claim_id": claim["claim_id"],
                "payment_type": "claim_payout",
                "amount": claim["paid_amount"],
                "payment_date": payment_date.isoformat(),
                "payment_method": "direct_deposit",
                "status": "completed",
                "reference_number": f"REF{random.randint(100000, 999999)}"
            })

    return payments


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("Unified Claims Data Generator")
    print("=" * 70)

    print("\n1. Generating base data...")
    customers = generate_customers()
    print(f"   Generated {len(customers)} customers")

    pets = generate_pets(customers)
    print(f"   Generated {len(pets)} pets")

    providers = generate_providers()
    print(f"   Generated {len(providers)} providers")

    policies = generate_policies(customers, pets)
    print(f"   Generated {len(policies)} policies")

    print("\n2. Generating fraud patterns...")

    # Fraud Pattern 1: Chronic Condition Gaming
    f1_cust, f1_pet, f1_pol, f1_claims = generate_fraud_pattern_1(customers, pets, policies, providers)
    print(f"   Pattern 1 (Chronic Gaming): {len(f1_claims)} claims")

    # Fraud Pattern 2: Provider Collusion
    f2_cust, f2_pet, f2_pol, f2_claims, f2_provider = generate_fraud_pattern_2(customers, pets, policies, providers)
    print(f"   Pattern 2 (Provider Collusion): {len(f2_claims)} claims")

    # Fraud Pattern 3: Staged Timing
    f3_cust, f3_pet, f3_pol, f3_claims = generate_fraud_pattern_3(customers, pets, policies, providers)
    print(f"   Pattern 3 (Staged Timing): {len(f3_claims)} claims")

    # Add fraud data to main lists
    # Replace existing entries with matching IDs
    customers = [c for c in customers if c["customer_id"] not in ["CUST-023", "CUST-067", "CUST-089"]]
    customers.extend([f1_cust, f2_cust, f3_cust])

    pets = [p for p in pets if p["pet_id"] not in ["PET-034", "PET-089", "PET-112"]]
    pets.extend([f1_pet, f2_pet, f3_pet])

    policies = [p for p in policies if p["policy_id"] not in ["POL-034", "POL-089", "POL-112"]]
    policies.extend([f1_pol, f2_pol, f3_pol])

    providers.append(f2_provider)

    print("\n3. Generating normal claims...")
    normal_claims = generate_normal_claims(customers, pets, policies, providers)
    print(f"   Generated {len(normal_claims)} normal claims")

    # Combine all claims
    all_claims = f1_claims + f2_claims + f3_claims + normal_claims
    print(f"   Total claims: {len(all_claims)}")

    print("\n4. Generating medical codes...")
    medical_codes = generate_medical_codes()
    print(f"   Generated {len(medical_codes)} medical codes")

    print("\n5. Generating payments...")
    payments = generate_payments(customers, policies, all_claims)
    print(f"   Generated {len(payments)} payments")

    print("\n6. Writing files...")

    # Write all data files
    def write_json(data, filename):
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"   Written: {filepath}")

    write_json(customers, "customers.json")
    write_json(pets, "pets.json")
    write_json(providers, "providers.json")
    write_json(policies, "policies.json")
    write_json(all_claims, "claims_history.json")
    write_json(medical_codes, "medical_codes.json")
    write_json(payments, "payments.json")

    # Create fraud patterns summary
    fraud_patterns = {
        "patterns": [
            {
                "id": "chronic_condition_gaming",
                "name": "Chronic Condition Gaming",
                "customer_id": "CUST-023",
                "pet_id": "PET-034",
                "description": "Customer files multiple 'accident' claims for a pet with documented pre-existing hip dysplasia",
                "indicators": [
                    "Anatomical focus (hip/leg) across all claims",
                    "Different providers for each claim",
                    "All claims under $2000 threshold",
                    "Pre-existing condition documented"
                ],
                "why_rules_miss": "Each claim passes individual thresholds",
                "why_ai_catches": "Pattern recognition across claim history + pre-existing condition awareness"
            },
            {
                "id": "provider_collusion",
                "name": "Provider Collusion",
                "customer_id": "CUST-067",
                "pet_id": "PET-089",
                "provider_id": "PROV-099",
                "description": "Customer exclusively uses one out-of-network provider with claims near annual limits",
                "indicators": [
                    "100% claims with same out-of-network provider",
                    "Claims consistently $200-300 below annual limit",
                    "Vague treatment descriptions",
                    "Provider has 15% customer concentration",
                    "Round claim amounts"
                ],
                "why_rules_miss": "Each claim is below limits, provider fraud rate below threshold",
                "why_ai_catches": "Multi-variable correlation: provider loyalty + limit optimization + concentration"
            },
            {
                "id": "staged_timing",
                "name": "Staged Timing",
                "customer_id": "CUST-089",
                "pet_id": "PET-112",
                "description": "New customer files expensive IVDD claim 2 days after waiting period for high-risk breed",
                "indicators": [
                    "Claim filed day 17 (2 days after 14-day waiting period)",
                    "French Bulldog has 10x higher IVDD risk",
                    "Pre-policy vet records 'unavailable'",
                    "Documentation suspiciously complete for emergency",
                    "Statistical anomaly: <0.3% probability"
                ],
                "why_rules_miss": "Waiting period technically satisfied, documentation complete",
                "why_ai_catches": "Statistical anomaly + breed risk + missing records pattern"
            }
        ],
        "summary": {
            "total_fraud_claims": len(f1_claims) + len(f2_claims) + len(f3_claims),
            "total_fraud_amount": sum(c["claim_amount"] for c in f1_claims + f2_claims + f3_claims),
            "fraud_customers": 3,
            "detection_method": "AI-based contextual analysis"
        }
    }
    write_json(fraud_patterns, "fraud_patterns.json")

    print("\n" + "=" * 70)
    print("DATA GENERATION COMPLETE")
    print("=" * 70)

    print(f"""
Summary:
--------
Customers:     {len(customers)}
Pets:          {len(pets)}
Providers:     {len(providers)}
Policies:      {len(policies)}
Claims:        {len(all_claims)}
  - Normal:    {len(normal_claims)}
  - Fraud:     {len(f1_claims) + len(f2_claims) + len(f3_claims)}
Payments:      {len(payments)}
Medical Codes: {len(medical_codes)}

Fraud Patterns:
--------------
1. Chronic Condition Gaming (CUST-023): {len(f1_claims)} claims
2. Provider Collusion (CUST-067): {len(f2_claims)} claims
3. Staged Timing (CUST-089): {len(f3_claims)} claims

Output: {OUTPUT_DIR.absolute()}
""")


if __name__ == "__main__":
    main()
