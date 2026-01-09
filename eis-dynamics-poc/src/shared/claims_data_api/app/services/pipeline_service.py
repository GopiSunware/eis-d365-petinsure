"""
Pipeline Service - Pipeline status and flow endpoints for Claims Data API.
Provides endpoints for BI Dashboard to display pipeline status and pending claims.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random

from fastapi import APIRouter, Query

from app.data_loader import get_data_store

router = APIRouter()


# ==================== PIPELINE STATE ====================

# In-memory pipeline state (for demo purposes)
_pipeline_state = {
    "pending_claims": [],
    "silver_claims": [],
    "gold_claims": [],
    "processing_log": [],
    "last_bronze_process": None,
    "last_silver_process": None,
    "last_gold_process": None,
}


def _generate_demo_pending_claims() -> Dict[str, List[Dict]]:
    """Generate demo pending claims for visualization."""
    store = get_data_store()
    claims = store.get_claims()

    # Get recent claims for demo
    recent_claims = sorted(
        claims,
        key=lambda x: x.get("claim_date", "") or x.get("service_date", "") or "",
        reverse=True
    )[:20]

    # Distribute claims across layers
    bronze = []
    silver = []
    gold = []

    for i, claim in enumerate(recent_claims):
        layer_claim = {
            "claim_id": claim.get("claim_id"),
            "claim_number": claim.get("claim_id", f"CLM-{i:04d}"),
            "customer_id": claim.get("customer_id"),
            "customer_name": f"Customer {claim.get('customer_id', 'Unknown')[-4:]}",
            "pet_id": claim.get("pet_id"),
            "pet_name": f"Pet {claim.get('pet_id', 'Unknown')[-3:]}",
            "claim_type": claim.get("claim_type", "Medical"),
            "claim_category": claim.get("category", claim.get("claim_category", "Illness")),
            "claim_amount": claim.get("claim_amount", 0),
            "service_date": claim.get("claim_date") or claim.get("service_date"),
            "ingestion_timestamp": datetime.utcnow().isoformat(),
            "status": claim.get("status", "pending"),
        }

        # Distribute across layers
        if i % 3 == 0:
            layer_claim["layer"] = "bronze"
            layer_claim["raw_status"] = "ingested"
            bronze.append(layer_claim)
        elif i % 3 == 1:
            layer_claim["layer"] = "silver"
            layer_claim["silver_status"] = "validated"
            layer_claim["completeness_score"] = round(random.uniform(85, 100), 1)
            layer_claim["validity_score"] = round(random.uniform(80, 100), 1)
            silver.append(layer_claim)
        else:
            layer_claim["layer"] = "gold"
            layer_claim["gold_status"] = "aggregated"
            layer_claim["estimated_reimbursement"] = round(layer_claim["claim_amount"] * 0.8, 2)
            gold.append(layer_claim)

    return {
        "bronze": bronze,
        "silver": silver,
        "gold": gold,
    }


# ==================== ENDPOINTS ====================

@router.get("/pending")
async def get_pending_claims():
    """Get all claims pending in each layer."""
    pending = _generate_demo_pending_claims()

    return {
        "bronze": pending["bronze"],
        "silver": pending["silver"],
        "gold": pending["gold"],
        "counts": {
            "bronze": len(pending["bronze"]),
            "silver": len(pending["silver"]),
            "gold": len(pending["gold"]),
        }
    }


@router.get("/flow")
async def get_pipeline_flow():
    """Get pipeline flow visualization data."""
    store = get_data_store()
    claims = store.get_claims()
    customers = store.get_customers()
    policies = store.get_policies()

    # Calculate layer statistics
    total_claims = len(claims)
    approved = len([c for c in claims if c.get("status") == "approved"])
    denied = len([c for c in claims if c.get("status") == "denied"])
    pending = len([c for c in claims if c.get("status") == "pending"])

    # Get recent processing timestamps
    now = datetime.utcnow()

    return {
        "layers": {
            "bronze": {
                "name": "Bronze Layer",
                "description": "Raw data ingestion",
                "status": "active",
                "record_count": total_claims,
                "last_update": (now - timedelta(minutes=random.randint(5, 30))).isoformat(),
                "transformations": [
                    "JSON validation",
                    "Schema enforcement",
                    "Deduplication check"
                ]
            },
            "silver": {
                "name": "Silver Layer",
                "description": "Cleaned and validated data",
                "status": "active",
                "record_count": total_claims - pending,
                "last_update": (now - timedelta(minutes=random.randint(10, 45))).isoformat(),
                "transformations": [
                    "Data type standardization",
                    "Null handling",
                    "Business rule validation",
                    "Quality scoring"
                ]
            },
            "gold": {
                "name": "Gold Layer",
                "description": "Aggregated business metrics",
                "status": "active",
                "record_count": approved + denied,
                "last_update": (now - timedelta(minutes=random.randint(15, 60))).isoformat(),
                "transformations": [
                    "Customer dimension join",
                    "Policy dimension join",
                    "KPI aggregation",
                    "Fraud scoring"
                ]
            }
        },
        "metrics": {
            "total_records": total_claims,
            "total_customers": len(customers),
            "total_policies": len(policies),
            "processing_rate": f"{random.randint(50, 150)} claims/hour",
            "avg_latency_ms": random.randint(100, 500),
        },
        "data_quality": {
            "completeness": round(random.uniform(92, 99), 1),
            "accuracy": round(random.uniform(95, 99), 1),
            "timeliness": round(random.uniform(88, 98), 1),
            "overall_score": round(random.uniform(90, 98), 1),
        },
        "data_source": "synthetic",
        "last_refresh": now.isoformat(),
    }


@router.get("/status")
async def get_pipeline_status():
    """Get current pipeline status with claim counts at each layer."""
    pending = _generate_demo_pending_claims()
    store = get_data_store()
    claims = store.get_claims()

    now = datetime.utcnow()

    return {
        "status": "healthy",
        "layers": {
            "bronze": {
                "status": "active",
                "record_count": len(claims),
                "pending": len(pending["bronze"]),
                "last_update": (now - timedelta(minutes=5)).isoformat(),
            },
            "silver": {
                "status": "active",
                "record_count": len(claims) - len(pending["bronze"]),
                "pending": len(pending["silver"]),
                "last_update": (now - timedelta(minutes=15)).isoformat(),
            },
            "gold": {
                "status": "active",
                "record_count": len(claims) - len(pending["bronze"]) - len(pending["silver"]),
                "pending": len(pending["gold"]),
                "last_update": (now - timedelta(minutes=30)).isoformat(),
            }
        },
        "pending_claims": {
            "bronze": len(pending["bronze"]),
            "silver": len(pending["silver"]),
            "gold": len(pending["gold"]),
        },
        "processing_log": [
            {
                "timestamp": (now - timedelta(minutes=i * 10)).isoformat(),
                "action": random.choice(["BRONZE_INGEST", "SILVER_PROCESS", "GOLD_AGGREGATE"]),
                "claims_processed": random.randint(1, 10),
                "message": f"Processed batch of claims"
            }
            for i in range(5)
        ],
        "last_processes": {
            "bronze": (now - timedelta(minutes=5)).isoformat(),
            "silver": (now - timedelta(minutes=15)).isoformat(),
            "gold": (now - timedelta(minutes=30)).isoformat(),
        }
    }


@router.delete("/clear")
async def clear_pipeline():
    """Clear all pending claims from pipeline (demo reset)."""
    global _pipeline_state
    _pipeline_state = {
        "pending_claims": [],
        "silver_claims": [],
        "gold_claims": [],
        "processing_log": [],
        "last_bronze_process": None,
        "last_silver_process": None,
        "last_gold_process": None,
    }
    return {
        "message": "Pipeline cleared",
        "status": "success",
        "cleared_at": datetime.utcnow().isoformat()
    }


@router.post("/process/bronze-to-silver")
async def process_bronze_to_silver():
    """Process claims from bronze to silver layer (demo simulation)."""
    now = datetime.utcnow()
    _pipeline_state["last_silver_process"] = now.isoformat()

    # Simulate processing
    processed_count = random.randint(3, 10)

    _pipeline_state["processing_log"].append({
        "timestamp": now.isoformat(),
        "action": "BRONZE_TO_SILVER",
        "claims_processed": processed_count,
        "message": f"Processed {processed_count} claims from Bronze to Silver"
    })

    return {
        "message": f"Processed {processed_count} claims from Bronze to Silver",
        "status": "success",
        "processed_count": processed_count,
        "processed_at": now.isoformat()
    }


@router.post("/process/silver-to-gold")
async def process_silver_to_gold():
    """Process claims from silver to gold layer (demo simulation)."""
    now = datetime.utcnow()
    _pipeline_state["last_gold_process"] = now.isoformat()

    # Simulate processing
    processed_count = random.randint(2, 8)

    _pipeline_state["processing_log"].append({
        "timestamp": now.isoformat(),
        "action": "SILVER_TO_GOLD",
        "claims_processed": processed_count,
        "message": f"Processed {processed_count} claims from Silver to Gold"
    })

    return {
        "message": f"Processed {processed_count} claims from Silver to Gold",
        "status": "success",
        "processed_count": processed_count,
        "processed_at": now.isoformat()
    }


@router.get("/metrics")
async def get_pipeline_metrics():
    """Get detailed pipeline metrics for monitoring."""
    store = get_data_store()
    claims = store.get_claims()
    customers = store.get_customers()
    policies = store.get_policies()

    approved = len([c for c in claims if c.get("status") == "approved"])
    total = len(claims)

    return {
        "data_source": "synthetic",
        "record_counts": {
            "claims": total,
            "customers": len(customers),
            "policies": len(policies),
        },
        "data_quality": {
            "completeness": round(random.uniform(92, 99), 1),
            "accuracy": round(random.uniform(95, 99), 1),
            "timeliness": round(random.uniform(88, 98), 1),
        },
        "processing_stats": {
            "approval_rate": round(approved / total * 100, 1) if total > 0 else 0,
            "avg_processing_time_hours": round(random.uniform(2, 24), 1),
            "claims_per_hour": random.randint(50, 150),
        },
        "pending_counts": {
            "bronze": random.randint(5, 15),
            "silver": random.randint(3, 10),
            "gold": random.randint(2, 8),
        },
        "layers": {
            "bronze": {
                "status": "active",
                "count": total,
                "last_update": datetime.utcnow().isoformat(),
            },
            "silver": {
                "status": "active",
                "count": total - random.randint(10, 50),
                "last_update": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
            },
            "gold": {
                "status": "active",
                "count": approved,
                "last_update": (datetime.utcnow() - timedelta(minutes=20)).isoformat(),
            }
        }
    }
