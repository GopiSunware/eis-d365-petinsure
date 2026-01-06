#!/usr/bin/env python3
"""
Convert PetInsure360 data (CSV/JSONL) to EIS-Dynamics format (JSON)
Maintains same data volume: 5K customers, 6.5K pets, 6K policies, 15K claims, 200 providers
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

# Paths
PETINSURE_DATA = Path("/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/data/raw")
EIS_DATA = Path("/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/shared/claims_data_api/data")

# ID mapping (UUID -> CUST-XXX style)
customer_id_map = {}
pet_id_map = {}
policy_id_map = {}
provider_id_map = {}
claim_id_map = {}


def convert_customers():
    """Convert customers.csv to customers.json"""
    print("Converting customers...")
    customers = []

    with open(PETINSURE_DATA / "customers.csv", "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            old_id = row["customer_id"]
            new_id = f"CUST-{i:05d}"
            customer_id_map[old_id] = new_id

            customers.append({
                "customer_id": new_id,
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "phone": row["phone"],
                "address_line1": row["address_line1"],
                "city": row["city"],
                "state": row["state"],
                "zip_code": row["zip_code"],
                "date_of_birth": row["date_of_birth"],
                "customer_since": row["customer_since"],
                "preferred_contact": row.get("preferred_contact", "email"),
                "marketing_opt_in": row.get("marketing_opt_in", "True") == "True",
                "referral_source": row.get("referral_source", "website"),
                "segment": row.get("customer_segment", "active").lower(),
                "lifetime_value": float(row.get("lifetime_value", 0)),
                "risk_tier": "medium",  # Will be calculated
                "total_claims": 0,  # Will be updated after claims
                "total_paid": 0.0,
                "notes": None,
                "created_at": row.get("created_at", datetime.now().isoformat()),
                "updated_at": row.get("updated_at", datetime.now().isoformat())
            })

    with open(EIS_DATA / "customers.json", "w") as f:
        json.dump(customers, f, indent=2)

    print(f"  Converted {len(customers)} customers")
    return customers


def convert_providers():
    """Convert vet_providers.csv to providers.json"""
    print("Converting providers...")
    providers = []

    with open(PETINSURE_DATA / "vet_providers.csv", "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            old_id = row["provider_id"]
            new_id = f"PROV-{i:04d}"
            provider_id_map[old_id] = new_id

            providers.append({
                "provider_id": new_id,
                "name": row["provider_name"],
                "type": row.get("provider_type", "Veterinary Hospital"),
                "license_number": row.get("license_number", f"VET{i:06d}"),
                "license_state": row.get("state", "CA"),
                "license_expiry": "2026-12-31",
                "dea_number": f"DEA{i:06d}" if i % 3 == 0 else None,  # 1/3 have DEA
                "npi": f"NPI{i:010d}",
                "address": row.get("address", ""),
                "city": row.get("city", ""),
                "state": row.get("state", "CA"),
                "zip_code": row.get("zip_code", ""),
                "phone": row.get("phone", ""),
                "email": row.get("email", f"provider{i}@vetclinic.com"),
                "is_in_network": row.get("is_in_network", "True") == "True",
                "network_tier": row.get("network_tier", "preferred"),
                "specialties": row.get("specialties", "General Practice").split(","),
                "average_rating": float(row.get("average_rating", 4.0)),
                "total_claims": 0,
                "fraud_flag_rate": 0.0,
                "is_active": True,
                "notes": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })

    with open(EIS_DATA / "providers.json", "w") as f:
        json.dump(providers, f, indent=2)

    print(f"  Converted {len(providers)} providers")
    return providers


def convert_pets():
    """Convert pets.csv to pets.json"""
    print("Converting pets...")
    pets = []

    with open(PETINSURE_DATA / "pets.csv", "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            old_id = row["pet_id"]
            new_id = f"PET-{i:05d}"
            pet_id_map[old_id] = new_id

            # Map customer ID
            old_customer_id = row["customer_id"]
            new_customer_id = customer_id_map.get(old_customer_id, f"CUST-{i % 5000 + 1:05d}")

            pets.append({
                "pet_id": new_id,
                "customer_id": new_customer_id,
                "name": row["pet_name"],
                "species": row.get("species", "Dog"),
                "breed": row.get("breed", "Mixed"),
                "gender": row.get("gender", "Male"),
                "date_of_birth": row.get("date_of_birth", "2020-01-01"),
                "weight_lbs": float(row.get("weight_lbs", 30)),
                "microchip_id": row.get("microchip_id"),
                "color": row.get("color", "Brown"),
                "is_neutered": row.get("is_neutered", "True") == "True",
                "vaccination_status": row.get("vaccination_status", "current"),
                "pre_existing_conditions": row.get("pre_existing_conditions", "").split(",") if row.get("pre_existing_conditions") else [],
                "medical_history": [],
                "is_active": row.get("is_active", "True") == "True",
                "notes": row.get("notes"),
                "created_at": row.get("created_at", datetime.now().isoformat()),
                "updated_at": row.get("updated_at", datetime.now().isoformat())
            })

    with open(EIS_DATA / "pets.json", "w") as f:
        json.dump(pets, f, indent=2)

    print(f"  Converted {len(pets)} pets")
    return pets


def convert_policies():
    """Convert policies.csv to policies.json"""
    print("Converting policies...")
    policies = []

    with open(PETINSURE_DATA / "policies.csv", "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            old_id = row["policy_id"]
            new_id = f"POL-{i:05d}"
            policy_id_map[old_id] = new_id

            # Map IDs
            old_customer_id = row["customer_id"]
            old_pet_id = row["pet_id"]
            new_customer_id = customer_id_map.get(old_customer_id, f"CUST-{i % 5000 + 1:05d}")
            new_pet_id = pet_id_map.get(old_pet_id, f"PET-{i % 6500 + 1:05d}")

            policies.append({
                "policy_id": new_id,
                "policy_number": row.get("policy_number", f"POL-2025-{i:06d}"),
                "customer_id": new_customer_id,
                "pet_id": new_pet_id,
                "plan_name": row.get("plan_name", "Premium Care"),
                "plan_type": row.get("plan_type", "comprehensive"),
                "monthly_premium": float(row.get("monthly_premium", 50)),
                "annual_premium": float(row.get("monthly_premium", 50)) * 12,
                "deductible": float(row.get("deductible", 250)),
                "coverage_limit": float(row.get("coverage_limit", 10000)),
                "reimbursement_rate": float(row.get("reimbursement_rate", 80)) / 100 if float(row.get("reimbursement_rate", 80)) > 1 else float(row.get("reimbursement_rate", 0.8)),
                "effective_date": row.get("effective_date", "2024-01-01"),
                "expiration_date": row.get("expiration_date", "2025-12-31"),
                "status": row.get("status", "active"),
                "waiting_period_days": int(row.get("waiting_period_days", 14)),
                "includes_wellness": row.get("includes_wellness", "False") == "True",
                "includes_dental": row.get("includes_dental", "False") == "True",
                "includes_behavioral": row.get("includes_behavioral", "False") == "True",
                "exclusions": row.get("exclusions", "").split(",") if row.get("exclusions") else [],
                "notes": None,
                "created_at": row.get("created_at", datetime.now().isoformat()),
                "updated_at": row.get("updated_at", datetime.now().isoformat())
            })

    with open(EIS_DATA / "policies.json", "w") as f:
        json.dump(policies, f, indent=2)

    print(f"  Converted {len(policies)} policies")
    return policies


def convert_claims():
    """Convert claims.jsonl to claims_history.json"""
    print("Converting claims...")
    claims = []

    with open(PETINSURE_DATA / "claims.jsonl", "r") as f:
        for i, line in enumerate(f, 1):
            row = json.loads(line.strip())
            old_id = row["claim_id"]
            new_id = f"CLM-{i:06d}"
            claim_id_map[old_id] = new_id

            # Map IDs
            old_customer_id = row["customer_id"]
            old_pet_id = row["pet_id"]
            old_policy_id = row["policy_id"]
            old_provider_id = row["provider_id"]

            new_customer_id = customer_id_map.get(old_customer_id, f"CUST-{(i % 5000) + 1:05d}")
            new_pet_id = pet_id_map.get(old_pet_id, f"PET-{(i % 6500) + 1:05d}")
            new_policy_id = policy_id_map.get(old_policy_id, f"POL-{(i % 6000) + 1:05d}")
            new_provider_id = provider_id_map.get(old_provider_id, f"PROV-{(i % 200) + 1:04d}")

            claims.append({
                "claim_id": new_id,
                "claim_number": row.get("claim_number", f"CLM-2025-{i:06d}"),
                "customer_id": new_customer_id,
                "pet_id": new_pet_id,
                "policy_id": new_policy_id,
                "provider_id": new_provider_id,
                "claim_type": row.get("claim_type", "General"),
                "claim_category": row.get("claim_category", "Medical"),
                "service_date": row.get("service_date", "2024-06-01"),
                "submitted_date": row.get("submitted_date", "2024-06-03"),
                "claim_amount": float(row.get("claim_amount", 500)),
                "deductible_applied": float(row.get("deductible_applied", 0)),
                "covered_amount": float(row.get("covered_amount", 0)),
                "paid_amount": float(row.get("paid_amount", 0)),
                "status": row.get("status", "pending"),
                "diagnosis_code": row.get("diagnosis_code", "DX0001"),
                "diagnosis_description": row.get("treatment_notes", "").split(".")[0] if row.get("treatment_notes") else "General diagnosis",
                "treatment_codes": [row.get("diagnosis_code", "TX0001")],
                "treatment_description": row.get("treatment_notes", "Treatment administered"),
                "invoice_number": row.get("invoice_number", f"INV-{i:06d}"),
                "invoice_documents": [],
                "is_emergency": row.get("is_emergency", False),
                "is_recurring": row.get("is_recurring", False),
                "processing_days": int(row.get("processing_days") or 0),
                "denial_reason": row.get("denial_reason"),
                "notes": None,
                "created_at": row.get("created_at", datetime.now().isoformat()),
                "updated_at": row.get("updated_at", datetime.now().isoformat())
            })

    with open(EIS_DATA / "claims_history.json", "w") as f:
        json.dump(claims, f, indent=2)

    print(f"  Converted {len(claims)} claims")
    return claims


def update_customer_stats(customers, claims):
    """Update customer claim statistics"""
    print("Updating customer statistics...")

    customer_claims = {}
    for claim in claims:
        cust_id = claim["customer_id"]
        if cust_id not in customer_claims:
            customer_claims[cust_id] = {"count": 0, "paid": 0.0}
        customer_claims[cust_id]["count"] += 1
        customer_claims[cust_id]["paid"] += claim["paid_amount"]

    for customer in customers:
        cust_id = customer["customer_id"]
        if cust_id in customer_claims:
            customer["total_claims"] = customer_claims[cust_id]["count"]
            customer["total_paid"] = round(customer_claims[cust_id]["paid"], 2)
            # Set risk tier based on claims
            if customer_claims[cust_id]["count"] > 10:
                customer["risk_tier"] = "high"
            elif customer_claims[cust_id]["count"] > 5:
                customer["risk_tier"] = "medium"
            else:
                customer["risk_tier"] = "low"

    with open(EIS_DATA / "customers.json", "w") as f:
        json.dump(customers, f, indent=2)

    print("  Updated customer statistics")


def main():
    print("=" * 60)
    print("PetInsure360 to EIS-Dynamics Data Conversion")
    print("=" * 60)
    print()

    # Ensure output directory exists
    EIS_DATA.mkdir(parents=True, exist_ok=True)

    # Convert in order (dependencies matter)
    customers = convert_customers()
    providers = convert_providers()
    pets = convert_pets()
    policies = convert_policies()
    claims = convert_claims()

    # Update derived statistics
    update_customer_stats(customers, claims)

    print()
    print("=" * 60)
    print("Conversion Complete!")
    print("=" * 60)
    print()
    print("Data Summary:")
    print(f"  Customers: {len(customers):,}")
    print(f"  Pets:      {len(pets):,}")
    print(f"  Policies:  {len(policies):,}")
    print(f"  Providers: {len(providers):,}")
    print(f"  Claims:    {len(claims):,}")
    print()
    print(f"Output directory: {EIS_DATA}")


if __name__ == "__main__":
    main()
