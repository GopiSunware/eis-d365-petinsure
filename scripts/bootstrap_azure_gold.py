#!/usr/bin/env python3
"""
Bootstrap Azure Gold Layer - Export demo data to Azure ADLS Gen2.

This script exports the synthetic demo data from Claims Data API to Azure
Gold layer in Parquet format, enabling the hybrid architecture to work
without requiring Databricks notebook execution.

Usage:
    python scripts/bootstrap_azure_gold.py

Requirements:
    pip install azure-storage-file-datalake pyarrow pandas
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add the claims_data_api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "eis-dynamics-poc" / "src" / "shared" / "claims_data_api"))

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    from azure.storage.filedatalake import DataLakeServiceClient
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install azure-storage-file-datalake pyarrow pandas")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "petinsud7i43")
SAS_TOKEN = os.getenv("AZURE_STORAGE_SAS_TOKEN")  # Required - no default for security
GOLD_CONTAINER = "gold"
EXPORT_PATH = "exports"


# =============================================================================
# DATA GENERATION (mirrors Claims Data API synthetic data)
# =============================================================================

def generate_customers(count: int = 500) -> pd.DataFrame:
    """Generate synthetic customer data for Gold layer."""
    customers = []
    segments = ["Premium", "Standard", "Basic"]
    tiers = ["Platinum", "Gold", "Silver", "Bronze"]
    risks = ["Low", "Medium", "High"]
    states = ["TX", "CA", "FL", "NY", "WA", "CO", "AZ", "NC", "GA", "PA"]
    cities = {
        "TX": ["Austin", "Dallas", "Houston", "San Antonio"],
        "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
        "FL": ["Miami", "Orlando", "Tampa", "Jacksonville"],
        "NY": ["New York", "Buffalo", "Albany", "Syracuse"],
        "WA": ["Seattle", "Tacoma", "Spokane", "Bellevue"],
        "CO": ["Denver", "Colorado Springs", "Boulder", "Fort Collins"],
        "AZ": ["Phoenix", "Tucson", "Scottsdale", "Mesa"],
        "NC": ["Charlotte", "Raleigh", "Durham", "Greensboro"],
        "GA": ["Atlanta", "Savannah", "Augusta", "Athens"],
        "PA": ["Philadelphia", "Pittsburgh", "Harrisburg", "Allentown"],
    }

    for i in range(count):
        state = random.choice(states)
        city = random.choice(cities[state])
        tier = random.choice(tiers)
        risk = random.choice(risks)

        # Correlate values
        premium = random.uniform(500, 3000) if tier in ["Platinum", "Gold"] else random.uniform(200, 1000)
        claims = random.randint(0, 5) if risk == "Low" else random.randint(3, 15)
        claim_amount = claims * random.uniform(200, 500)
        loss_ratio = (claim_amount / premium * 100) if premium > 0 else 0

        customer_since = datetime.now() - timedelta(days=random.randint(30, 1500))
        last_claim = datetime.now() - timedelta(days=random.randint(1, 365)) if claims > 0 else None

        customers.append({
            "customer_id": f"CUST-{i+1:05d}",
            "first_name": f"Customer{i+1}",
            "last_name": f"Test{random.randint(1, 100)}",
            "email": f"customer{i+1}@example.com",
            "phone": f"(555) {random.randint(100,999)}-{random.randint(1000,9999)}",
            "full_address": f"{random.randint(100, 9999)} Main St, {city}, {state}",
            "customer_segment": random.choice(segments),
            "value_tier": tier,
            "risk_category": risk,
            "total_claims": claims,
            "approved_claims": int(claims * 0.7),
            "total_annual_premium": round(premium, 2),
            "total_claim_amount": round(claim_amount, 2),
            "loss_ratio": round(loss_ratio, 2),
            "active_policies": random.randint(1, 3),
            "customer_since": customer_since.strftime("%Y-%m-%d"),
            "last_claim_date": last_claim.strftime("%Y-%m-%d") if last_claim else None,
            "total_pets": random.randint(1, 4),
            "lifetime_value": round(premium * random.uniform(2, 5), 2),
            "churn_risk": random.choice(["Low", "Medium", "High"]),
        })

    return pd.DataFrame(customers)


def generate_claims(count: int = 2000) -> pd.DataFrame:
    """Generate synthetic claims data for Gold layer."""
    claims = []
    statuses = ["approved", "denied", "pending", "under_review"]
    categories = ["Illness", "Injury", "Wellness", "Emergency", "Surgery", "Dental"]
    complexities = ["Low", "Medium", "High"]

    for i in range(count):
        status = random.choices(statuses, weights=[0.65, 0.15, 0.15, 0.05])[0]
        category = random.choice(categories)
        claim_date = datetime.now() - timedelta(days=random.randint(1, 365))

        claims.append({
            "claim_id": f"CLM-{i+1:06d}",
            "customer_id": f"CUST-{random.randint(1, 500):05d}",
            "pet_id": f"PET-{random.randint(1, 700):05d}",
            "claim_date": claim_date.strftime("%Y-%m-%d"),
            "service_date": (claim_date - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
            "claim_amount": round(random.uniform(50, 2000), 2),
            "status": status,
            "claim_category": category,
            "processing_days": random.randint(1, 14),
            "complexity": random.choice(complexities),
            "auto_adjudicated": random.choice([True, False]),
            "fraud_score": round(random.uniform(0, 100), 2),
            "provider_id": f"PROV-{random.randint(1, 200):04d}",
        })

    return pd.DataFrame(claims)


def generate_monthly_kpis(months: int = 12) -> pd.DataFrame:
    """Generate monthly KPI data for Gold layer."""
    kpis = []
    base_date = datetime.now()

    for i in range(months):
        month_date = base_date - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")

        total_claims = random.randint(1500, 2500)
        approved = int(total_claims * random.uniform(0.65, 0.75))
        denied = int(total_claims * random.uniform(0.12, 0.18))
        pending = total_claims - approved - denied

        total_amount = total_claims * random.uniform(300, 450)
        premium = total_amount * random.uniform(1.2, 1.5)

        kpis.append({
            "month": month_str,
            "total_claims": total_claims,
            "approved_claims": approved,
            "denied_claims": denied,
            "pending_claims": pending,
            "approval_rate": round(approved / total_claims * 100, 1),
            "total_claim_amount": round(total_amount, 2),
            "avg_claim_amount": round(total_amount / total_claims, 2),
            "new_customers": random.randint(80, 200),
            "churned_customers": random.randint(15, 50),
            "total_premium": round(premium, 2),
            "loss_ratio": round(total_amount / premium * 100, 2),
        })

    return pd.DataFrame(list(reversed(kpis)))


def generate_risk_scores(count: int = 500) -> pd.DataFrame:
    """Generate risk scoring data for Gold layer."""
    risks = []
    categories = ["Low", "Medium", "High"]

    for i in range(count):
        category = random.choices(categories, weights=[0.6, 0.3, 0.1])[0]

        if category == "Low":
            score = random.uniform(0, 30)
            loss_ratio = random.uniform(20, 50)
            claims = random.randint(0, 3)
        elif category == "Medium":
            score = random.uniform(30, 70)
            loss_ratio = random.uniform(50, 80)
            claims = random.randint(3, 8)
        else:
            score = random.uniform(70, 100)
            loss_ratio = random.uniform(80, 150)
            claims = random.randint(8, 20)

        risks.append({
            "customer_id": f"CUST-{i+1:05d}",
            "first_name": f"Customer{i+1}",
            "last_name": f"Test{random.randint(1, 100)}",
            "risk_category": category,
            "risk_score": round(score, 2),
            "loss_ratio": round(loss_ratio, 2),
            "total_claims": claims,
            "claim_frequency": round(claims / 12, 2),
            "risk_factors": [],
        })

    return pd.DataFrame(risks)


def generate_provider_performance(count: int = 200) -> pd.DataFrame:
    """Generate provider performance data for Gold layer."""
    providers = []
    specialties = ["General Practice", "Emergency", "Surgery", "Dermatology", "Orthopedics", "Dental", "Cardiology"]

    for i in range(count):
        total_claims = random.randint(10, 500)
        total_amount = total_claims * random.uniform(200, 600)
        approval_rate = random.uniform(60, 95)

        providers.append({
            "provider_id": f"PROV-{i+1:04d}",
            "provider_name": f"Pet Clinic {i+1}",
            "specialty": random.choice(specialties),
            "is_in_network": random.choice([True, True, True, False]),  # 75% in-network
            "total_claims": total_claims,
            "total_claim_amount": round(total_amount, 2),
            "avg_claim_amount": round(total_amount / total_claims, 2),
            "approval_rate": round(approval_rate, 1),
            "provider_rating": round(random.uniform(3.5, 5.0), 1),
            "fraud_risk": random.choices(["Low", "Medium", "High"], weights=[0.8, 0.15, 0.05])[0],
        })

    return pd.DataFrame(providers)


# =============================================================================
# AZURE UPLOAD
# =============================================================================

def upload_parquet_to_azure(df: pd.DataFrame, table_name: str, service_client: DataLakeServiceClient) -> bool:
    """Upload DataFrame as Parquet to Azure ADLS Gen2."""
    try:
        # Get file system client
        fs_client = service_client.get_file_system_client(GOLD_CONTAINER)

        # Convert to Parquet bytes
        table = pa.Table.from_pandas(df)
        buffer = pa.BufferOutputStream()
        pq.write_table(table, buffer)
        parquet_bytes = buffer.getvalue().to_pybytes()

        # Create directory if needed
        dir_path = f"{EXPORT_PATH}/{table_name}"
        try:
            fs_client.create_directory(dir_path)
        except Exception as e:
            # Directory likely already exists, log for debugging
            if "already exists" not in str(e).lower() and "PathAlreadyExists" not in str(e):
                print(f"  Note: Could not create directory {dir_path}: {e}")

        # Upload file
        file_path = f"{dir_path}/data.parquet"
        file_client = fs_client.get_file_client(file_path)
        file_client.upload_data(parquet_bytes, overwrite=True)

        print(f"  ✓ Uploaded {table_name}: {len(df)} records ({len(parquet_bytes):,} bytes)")
        return True

    except Exception as e:
        print(f"  ✗ Failed to upload {table_name}: {e}")
        return False


def main():
    """Main function to bootstrap Azure Gold layer."""
    print("=" * 60)
    print("Bootstrap Azure Gold Layer")
    print("=" * 60)
    print(f"\nStorage Account: {STORAGE_ACCOUNT}")
    print(f"Container: {GOLD_CONTAINER}")
    print(f"Export Path: {EXPORT_PATH}/")
    print()

    # Check SAS token
    if not SAS_TOKEN:
        print("ERROR: AZURE_STORAGE_SAS_TOKEN not set")
        print("Generate with:")
        print("  az storage container generate-sas --account-name petinsud7i43 --name gold --permissions rwl --expiry 2026-12-31")
        sys.exit(1)

    # Connect to Azure
    print("Connecting to Azure ADLS Gen2...")
    try:
        account_url = f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net"
        service_client = DataLakeServiceClient(account_url, credential=SAS_TOKEN)

        # Test connection
        fs_client = service_client.get_file_system_client(GOLD_CONTAINER)
        list(fs_client.get_paths(max_results=1))
        print("  ✓ Connected successfully\n")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        sys.exit(1)

    # Generate and upload data
    print("Generating and uploading Gold layer data...\n")

    tables = [
        ("customer_360", generate_customers, {"count": 500}),
        ("claims_analytics", generate_claims, {"count": 2000}),
        ("monthly_kpis", generate_monthly_kpis, {"months": 12}),
        ("risk_scoring", generate_risk_scores, {"count": 500}),
        ("provider_performance", generate_provider_performance, {"count": 200}),
    ]

    success_count = 0
    for table_name, generator, kwargs in tables:
        print(f"Processing {table_name}...")
        df = generator(**kwargs)
        if upload_parquet_to_azure(df, table_name, service_client):
            success_count += 1

    print()
    print("=" * 60)
    print(f"Bootstrap Complete: {success_count}/{len(tables)} tables uploaded")
    print("=" * 60)

    if success_count == len(tables):
        print("\n✓ Azure Gold layer is ready for hybrid architecture!")
        print("\nNext steps:")
        print("1. Update Claims Data API with AZURE_STORAGE_SAS_TOKEN")
        print("2. Set USE_AZURE_DATA=hybrid")
        print("3. Test: curl https://your-api/api/data-source/status")
    else:
        print("\n⚠ Some tables failed to upload. Check errors above.")


if __name__ == "__main__":
    main()
