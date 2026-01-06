#!/usr/bin/env python3
"""
PetInsure360 - Synthetic Pet Insurance Data Generator
Generates realistic pet insurance data for medallion lakehouse demo

Data Models:
- Customers (pet owners)
- Pets (dogs, cats, birds, exotic)
- Policies (insurance plans)
- Claims (insurance claims)
- Vet Providers (veterinary clinics)
- Claim Documents (vet invoices metadata)

Author: Gopinath Varadharajan
"""

import json
import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import hashlib

# =============================================================================
# CONFIGURATION
# =============================================================================

NUM_CUSTOMERS = 5000
NUM_PETS = 6500  # Some customers have multiple pets
NUM_POLICIES = 6000
NUM_CLAIMS = 15000
NUM_VET_PROVIDERS = 200

OUTPUT_DIR = Path(__file__).parent / "raw"
OUTPUT_DIR.mkdir(exist_ok=True)

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
    ("San Jose", "CA", "95101"), ("Austin", "TX", "78701"), ("Jacksonville", "FL", "32099"),
    ("Fort Worth", "TX", "76101"), ("Columbus", "OH", "43085"), ("Charlotte", "NC", "28201"),
    ("Seattle", "WA", "98101"), ("Denver", "CO", "80201"), ("Boston", "MA", "02101"),
    ("Detroit", "MI", "48201"), ("Portland", "OR", "97201"), ("Atlanta", "GA", "30301"),
    ("Miami", "FL", "33101"), ("Nashville", "TN", "37201"), ("Las Vegas", "NV", "89101")
]

# Pet breeds by species
DOG_BREEDS = [
    "Labrador Retriever", "German Shepherd", "Golden Retriever", "French Bulldog",
    "Bulldog", "Poodle", "Beagle", "Rottweiler", "Yorkshire Terrier", "Boxer",
    "Dachshund", "Siberian Husky", "Great Dane", "Doberman Pinscher", "Shih Tzu",
    "Boston Terrier", "Bernese Mountain Dog", "Pomeranian", "Havanese", "Cavalier King Charles"
]

CAT_BREEDS = [
    "Domestic Shorthair", "Domestic Longhair", "Maine Coon", "Ragdoll", "British Shorthair",
    "Persian", "Siamese", "Bengal", "Abyssinian", "Scottish Fold", "Sphynx",
    "Russian Blue", "Norwegian Forest Cat", "Birman", "Oriental Shorthair"
]

BIRD_BREEDS = ["Parakeet", "Cockatiel", "Canary", "Finch", "Lovebird", "Conure", "African Grey"]

EXOTIC_BREEDS = ["Rabbit", "Guinea Pig", "Hamster", "Ferret", "Hedgehog", "Chinchilla", "Reptile"]

PET_NAMES = [
    "Max", "Bella", "Charlie", "Luna", "Cooper", "Daisy", "Buddy", "Lucy", "Rocky",
    "Sadie", "Bear", "Molly", "Duke", "Bailey", "Tucker", "Maggie", "Jack", "Sophie",
    "Oliver", "Chloe", "Leo", "Penny", "Milo", "Zoey", "Zeus", "Lily", "Winston",
    "Stella", "Teddy", "Coco", "Murphy", "Rosie", "Finn", "Ruby", "Oscar", "Gracie",
    "Bentley", "Willow", "Louie", "Nala", "Gus", "Ellie", "Shadow", "Pepper", "Simba"
]

# Insurance plan types
PLAN_TYPES = [
    {"name": "Basic", "monthly_premium": 25, "deductible": 500, "coverage_limit": 5000, "coverage_pct": 70},
    {"name": "Standard", "monthly_premium": 45, "deductible": 250, "coverage_limit": 15000, "coverage_pct": 80},
    {"name": "Premium", "monthly_premium": 75, "deductible": 100, "coverage_limit": 30000, "coverage_pct": 90},
    {"name": "Unlimited", "monthly_premium": 120, "deductible": 0, "coverage_limit": 999999, "coverage_pct": 100}
]

# Claim types and typical costs
CLAIM_TYPES = [
    {"type": "Wellness Exam", "category": "Preventive", "min_cost": 50, "max_cost": 150},
    {"type": "Vaccination", "category": "Preventive", "min_cost": 75, "max_cost": 200},
    {"type": "Dental Cleaning", "category": "Dental", "min_cost": 200, "max_cost": 800},
    {"type": "Spay/Neuter", "category": "Surgery", "min_cost": 200, "max_cost": 500},
    {"type": "Emergency Visit", "category": "Emergency", "min_cost": 150, "max_cost": 500},
    {"type": "X-Ray", "category": "Diagnostic", "min_cost": 100, "max_cost": 400},
    {"type": "Blood Test", "category": "Diagnostic", "min_cost": 80, "max_cost": 250},
    {"type": "Allergy Treatment", "category": "Illness", "min_cost": 100, "max_cost": 500},
    {"type": "Skin Condition", "category": "Illness", "min_cost": 150, "max_cost": 600},
    {"type": "Ear Infection", "category": "Illness", "min_cost": 100, "max_cost": 300},
    {"type": "Digestive Issues", "category": "Illness", "min_cost": 200, "max_cost": 800},
    {"type": "Orthopedic Surgery", "category": "Surgery", "min_cost": 2000, "max_cost": 8000},
    {"type": "Cancer Treatment", "category": "Chronic", "min_cost": 3000, "max_cost": 15000},
    {"type": "Diabetes Management", "category": "Chronic", "min_cost": 500, "max_cost": 2000},
    {"type": "Heart Condition", "category": "Chronic", "min_cost": 1000, "max_cost": 5000},
    {"type": "ACL Surgery", "category": "Surgery", "min_cost": 3000, "max_cost": 6000},
    {"type": "Foreign Object Removal", "category": "Emergency", "min_cost": 1500, "max_cost": 5000},
    {"type": "Poisoning Treatment", "category": "Emergency", "min_cost": 500, "max_cost": 3000},
    {"type": "Fracture Treatment", "category": "Emergency", "min_cost": 1000, "max_cost": 4000},
    {"type": "Hospitalization", "category": "Emergency", "min_cost": 500, "max_cost": 3000}
]

VET_CLINIC_PREFIXES = [
    "Animal", "Pet", "Companion", "Family", "City", "Valley", "Meadow", "Oak",
    "River", "Mountain", "Sunset", "Sunrise", "Central", "Metro", "Premier"
]

VET_CLINIC_SUFFIXES = [
    "Veterinary Hospital", "Animal Hospital", "Pet Clinic", "Vet Center",
    "Animal Care", "Pet Hospital", "Veterinary Clinic", "Animal Medical Center"
]

CLAIM_STATUSES = ["Submitted", "Under Review", "Approved", "Partially Approved", "Denied", "Paid"]


# =============================================================================
# DATA GENERATORS
# =============================================================================

def generate_uuid() -> str:
    return str(uuid.uuid4())

def generate_email(first_name: str, last_name: str) -> str:
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"]
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(domains)}"

def generate_phone() -> str:
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

def generate_date_in_range(start_date: datetime, end_date: datetime) -> datetime:
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_customers(num: int) -> List[Dict[str, Any]]:
    """Generate customer (pet owner) records."""
    customers = []
    for i in range(num):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        city, state, zip_code = random.choice(CITIES)

        created_date = generate_date_in_range(
            datetime(2019, 1, 1),
            datetime(2024, 12, 1)
        )

        customers.append({
            "customer_id": generate_uuid(),
            "first_name": first_name,
            "last_name": last_name,
            "email": generate_email(first_name, last_name),
            "phone": generate_phone(),
            "address_line1": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine', 'Elm', 'Park', 'Lake', 'River', 'Hill'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr', 'Ln', 'Way', 'Rd'])}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": "USA",
            "date_of_birth": generate_date_in_range(datetime(1950, 1, 1), datetime(2005, 1, 1)).strftime("%Y-%m-%d"),
            "customer_since": created_date.strftime("%Y-%m-%d"),
            "preferred_contact": random.choice(["Email", "Phone", "SMS"]),
            "marketing_opt_in": random.choice([True, False]),
            "referral_source": random.choice(["Google", "Facebook", "Referral", "TV Ad", "Vet Recommendation", "Pet Store", "Direct"]),
            "customer_segment": random.choice(["New", "Active", "Loyal", "At Risk", "Churned"]),
            "lifetime_value": round(random.uniform(500, 10000), 2),
            "created_at": created_date.isoformat(),
            "updated_at": (created_date + timedelta(days=random.randint(0, 365))).isoformat()
        })
    return customers

def generate_pets(num: int, customers: List[Dict]) -> List[Dict[str, Any]]:
    """Generate pet records linked to customers."""
    pets = []
    customer_ids = [c["customer_id"] for c in customers]

    for i in range(num):
        species = random.choices(
            ["Dog", "Cat", "Bird", "Exotic"],
            weights=[55, 35, 5, 5]
        )[0]

        if species == "Dog":
            breed = random.choice(DOG_BREEDS)
            avg_weight = random.randint(10, 100)
        elif species == "Cat":
            breed = random.choice(CAT_BREEDS)
            avg_weight = random.randint(5, 20)
        elif species == "Bird":
            breed = random.choice(BIRD_BREEDS)
            avg_weight = random.uniform(0.1, 2)
        else:
            breed = random.choice(EXOTIC_BREEDS)
            avg_weight = random.uniform(0.5, 10)

        birth_date = generate_date_in_range(datetime(2015, 1, 1), datetime(2024, 6, 1))

        pets.append({
            "pet_id": generate_uuid(),
            "customer_id": random.choice(customer_ids),
            "pet_name": random.choice(PET_NAMES),
            "species": species,
            "breed": breed,
            "gender": random.choice(["Male", "Female"]),
            "date_of_birth": birth_date.strftime("%Y-%m-%d"),
            "weight_lbs": round(avg_weight + random.uniform(-5, 5), 1),
            "color": random.choice(["Black", "White", "Brown", "Golden", "Gray", "Orange", "Mixed", "Spotted", "Brindle"]),
            "microchip_id": f"MC{random.randint(100000000, 999999999)}" if random.random() > 0.3 else None,
            "is_neutered": random.choice([True, False]),
            "pre_existing_conditions": random.choice([None, "Allergies", "Hip Dysplasia", "Diabetes", "Heart Murmur", "Arthritis"]),
            "vaccination_status": random.choice(["Up to Date", "Overdue", "Unknown"]),
            "adoption_date": (birth_date + timedelta(days=random.randint(60, 365))).strftime("%Y-%m-%d"),
            "is_active": random.choices([True, False], weights=[95, 5])[0],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
    return pets

def generate_vet_providers(num: int) -> List[Dict[str, Any]]:
    """Generate veterinary provider records."""
    providers = []
    for i in range(num):
        city, state, zip_code = random.choice(CITIES)

        providers.append({
            "provider_id": generate_uuid(),
            "provider_name": f"{random.choice(VET_CLINIC_PREFIXES)} {random.choice(VET_CLINIC_SUFFIXES)}",
            "provider_type": random.choice(["General Practice", "Emergency Hospital", "Specialty Clinic", "Mobile Vet"]),
            "address": f"{random.randint(100, 9999)} {random.choice(['Medical', 'Healthcare', 'Veterinary', 'Animal'])} {random.choice(['Plaza', 'Center', 'Park', 'Drive'])}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "phone": generate_phone(),
            "email": f"contact@{random.choice(VET_CLINIC_PREFIXES).lower()}vet{random.randint(1, 100)}.com",
            "is_in_network": random.choices([True, False], weights=[70, 30])[0],
            "average_rating": round(random.uniform(3.5, 5.0), 1),
            "total_reviews": random.randint(10, 500),
            "accepts_emergency": random.choice([True, False]),
            "operating_hours": random.choice(["8AM-6PM", "7AM-9PM", "24/7", "9AM-5PM"]),
            "specialties": random.choice([None, "Surgery", "Oncology", "Cardiology", "Dermatology", "Orthopedics"]),
            "license_number": f"VET{state}{random.randint(10000, 99999)}",
            "created_at": datetime.now().isoformat()
        })
    return providers

def generate_policies(num: int, pets: List[Dict], customers: List[Dict]) -> List[Dict[str, Any]]:
    """Generate insurance policy records."""
    policies = []
    pet_ids = [p["pet_id"] for p in pets]
    pet_to_customer = {p["pet_id"]: p["customer_id"] for p in pets}

    for i in range(num):
        pet_id = random.choice(pet_ids)
        plan = random.choice(PLAN_TYPES)

        effective_date = generate_date_in_range(datetime(2020, 1, 1), datetime(2024, 10, 1))

        # Policy might be active, cancelled, or expired
        status = random.choices(
            ["Active", "Cancelled", "Expired", "Pending"],
            weights=[70, 10, 15, 5]
        )[0]

        policies.append({
            "policy_id": generate_uuid(),
            "policy_number": f"PI{datetime.now().year}-{random.randint(100000, 999999)}",
            "customer_id": pet_to_customer.get(pet_id, random.choice(list(pet_to_customer.values()))),
            "pet_id": pet_id,
            "plan_name": plan["name"],
            "monthly_premium": plan["monthly_premium"] + random.uniform(-5, 15),
            "annual_deductible": plan["deductible"],
            "coverage_limit": plan["coverage_limit"],
            "reimbursement_percentage": plan["coverage_pct"],
            "effective_date": effective_date.strftime("%Y-%m-%d"),
            "expiration_date": (effective_date + timedelta(days=365)).strftime("%Y-%m-%d"),
            "status": status,
            "payment_method": random.choice(["Credit Card", "Debit Card", "Bank Transfer", "PayPal"]),
            "payment_frequency": random.choice(["Monthly", "Annual"]),
            "waiting_period_days": random.choice([14, 30]),
            "includes_wellness": random.choice([True, False]),
            "includes_dental": random.choice([True, False]),
            "includes_behavioral": random.choice([True, False]),
            "cancellation_date": (effective_date + timedelta(days=random.randint(30, 300))).strftime("%Y-%m-%d") if status == "Cancelled" else None,
            "renewal_count": random.randint(0, 5),
            "created_at": effective_date.isoformat(),
            "updated_at": datetime.now().isoformat()
        })
    return policies

def generate_claims(num: int, policies: List[Dict], providers: List[Dict]) -> List[Dict[str, Any]]:
    """Generate insurance claim records."""
    claims = []
    active_policies = [p for p in policies if p["status"] in ["Active", "Expired"]]
    provider_ids = [p["provider_id"] for p in providers]

    for i in range(num):
        policy = random.choice(active_policies)
        claim_type = random.choice(CLAIM_TYPES)
        provider_id = random.choice(provider_ids)

        service_date = generate_date_in_range(
            datetime.strptime(policy["effective_date"], "%Y-%m-%d"),
            datetime.now()
        )

        # Calculate claim amounts
        claim_amount = round(random.uniform(claim_type["min_cost"], claim_type["max_cost"]), 2)
        deductible_applied = min(policy["annual_deductible"], claim_amount) if random.random() > 0.5 else 0
        covered_amount = (claim_amount - deductible_applied) * (policy["reimbursement_percentage"] / 100)

        status = random.choice(CLAIM_STATUSES)

        # Determine paid amount based on status
        if status == "Paid":
            paid_amount = covered_amount
        elif status == "Partially Approved":
            paid_amount = covered_amount * random.uniform(0.5, 0.9)
        elif status in ["Denied", "Submitted", "Under Review"]:
            paid_amount = 0
        else:
            paid_amount = covered_amount

        submitted_date = service_date + timedelta(days=random.randint(1, 14))

        claims.append({
            "claim_id": generate_uuid(),
            "claim_number": f"CLM{datetime.now().year}{random.randint(100000, 999999)}",
            "policy_id": policy["policy_id"],
            "pet_id": policy["pet_id"],
            "customer_id": policy["customer_id"],
            "provider_id": provider_id,
            "claim_type": claim_type["type"],
            "claim_category": claim_type["category"],
            "service_date": service_date.strftime("%Y-%m-%d"),
            "submitted_date": submitted_date.strftime("%Y-%m-%d"),
            "claim_amount": claim_amount,
            "deductible_applied": round(deductible_applied, 2),
            "covered_amount": round(covered_amount, 2),
            "paid_amount": round(paid_amount, 2),
            "status": status,
            "denial_reason": random.choice(["Pre-existing condition", "Waiting period", "Not covered", "Documentation missing", None]) if status == "Denied" else None,
            "processing_days": random.randint(1, 30) if status in ["Approved", "Paid", "Partially Approved", "Denied"] else None,
            "diagnosis_code": f"DX{random.randint(1000, 9999)}",
            "treatment_notes": f"Treatment for {claim_type['type'].lower()}. Pet responded well to treatment.",
            "invoice_number": f"INV{random.randint(100000, 999999)}",
            "is_emergency": claim_type["category"] == "Emergency",
            "is_recurring": claim_type["category"] == "Chronic",
            "created_at": submitted_date.isoformat(),
            "updated_at": (submitted_date + timedelta(days=random.randint(1, 30))).isoformat()
        })
    return claims


# =============================================================================
# FILE WRITERS
# =============================================================================

def write_csv(data: List[Dict], filename: str):
    """Write data to CSV file."""
    if not data:
        return
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  Written: {filepath} ({len(data)} records)")

def write_json(data: List[Dict], filename: str):
    """Write data to JSON file (newline delimited for streaming)."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    print(f"  Written: {filepath} ({len(data)} records)")

def write_json_array(data: List[Dict], filename: str):
    """Write data as JSON array."""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"  Written: {filepath} ({len(data)} records)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("PetInsure360 - Synthetic Data Generator")
    print("=" * 70)

    print(f"\nGenerating {NUM_CUSTOMERS:,} customers...")
    customers = generate_customers(NUM_CUSTOMERS)

    print(f"Generating {NUM_PETS:,} pets...")
    pets = generate_pets(NUM_PETS, customers)

    print(f"Generating {NUM_VET_PROVIDERS:,} vet providers...")
    providers = generate_vet_providers(NUM_VET_PROVIDERS)

    print(f"Generating {NUM_POLICIES:,} policies...")
    policies = generate_policies(NUM_POLICIES, pets, customers)

    print(f"Generating {NUM_CLAIMS:,} claims...")
    claims = generate_claims(NUM_CLAIMS, policies, providers)

    print("\nWriting files...")

    # CSV files (typical for structured data ingestion)
    write_csv(customers, "customers.csv")
    write_csv(pets, "pets.csv")
    write_csv(policies, "policies.csv")
    write_csv(providers, "vet_providers.csv")

    # JSON files (typical for semi-structured/streaming data)
    write_json(claims, "claims.jsonl")  # Newline delimited for streaming
    write_json_array(claims[:100], "claims_sample.json")  # Sample for testing

    # Summary statistics
    print("\n" + "=" * 70)
    print("DATA GENERATION COMPLETE")
    print("=" * 70)

    total_claim_amount = sum(c["claim_amount"] for c in claims)
    total_paid = sum(c["paid_amount"] for c in claims)

    print(f"""
Summary Statistics:
-------------------
Customers:     {len(customers):,}
Pets:          {len(pets):,}
Policies:      {len(policies):,}
Claims:        {len(claims):,}
Vet Providers: {len(providers):,}

Claims Analysis:
----------------
Total Claim Amount:  ${total_claim_amount:,.2f}
Total Paid:          ${total_paid:,.2f}
Loss Ratio:          {(total_paid/total_claim_amount)*100:.1f}%

Status Distribution:
""")

    status_counts = {}
    for c in claims:
        status_counts[c["status"]] = status_counts.get(c["status"], 0) + 1
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count:,} ({count/len(claims)*100:.1f}%)")

    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print("\nNext steps:")
    print("  1. Upload to Azure Storage (raw container)")
    print("  2. Run Databricks ETL notebooks")
    print("  3. Query with Synapse Serverless")
    print("  4. Connect Power BI")


if __name__ == "__main__":
    main()
