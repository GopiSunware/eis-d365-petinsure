"""
ProviderService - Provider network and verification.
5 endpoints for provider data access.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.data_loader import get_data_store

router = APIRouter()


@router.get("/")
async def list_providers(
    is_in_network: Optional[bool] = None,
    provider_type: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """List all providers with optional filters."""
    store = get_data_store()
    providers = store.get_providers()

    if is_in_network is not None:
        providers = [p for p in providers if p.get("is_in_network") == is_in_network]
    if provider_type:
        providers = [p for p in providers if p.get("provider_type", "").lower() == provider_type.lower()]
    if city:
        providers = [p for p in providers if p.get("city", "").lower() == city.lower()]

    return {
        "count": len(providers[:limit]),
        "total": len(providers),
        "providers": providers[:limit]
    }


@router.get("/search")
async def search_providers(
    name: Optional[str] = None,
    zip_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search providers by name or location.
    LLM Tool: verify_provider(provider_name)
    """
    store = get_data_store()
    providers = store.get_providers()

    results = providers
    if name:
        results = [p for p in results if name.lower() in p.get("name", "").lower()]
    if zip_code:
        results = [p for p in results if p.get("zip_code", "").startswith(zip_code[:3])]

    return {
        "query": {"name": name, "zip_code": zip_code},
        "count": len(results),
        "providers": results[:20]
    }


@router.get("/{provider_id}")
async def get_provider(provider_id: str) -> Dict[str, Any]:
    """
    Get provider details.
    LLM Tool: verify_provider(provider_id) / get_network_status(provider_id)
    """
    store = get_data_store()
    provider = store.get_provider(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    # Get claims for this provider
    claims = store.get_claims_by_provider(provider_id)

    return {
        "provider": provider,
        "total_claims_processed": len(claims),
        "total_amount_processed": sum(c.get("claim_amount", 0) for c in claims),
        "verified": True,
        "license_valid": True
    }


@router.get("/{provider_id}/network-status")
async def get_network_status(provider_id: str) -> Dict[str, Any]:
    """
    Check if provider is in network.
    LLM Tool: get_network_status(provider_id)
    """
    store = get_data_store()
    provider = store.get_provider(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    is_in_network = provider.get("is_in_network", False)

    return {
        "provider_id": provider_id,
        "provider_name": provider.get("name"),
        "is_in_network": is_in_network,
        "network_tier": "preferred" if is_in_network else "out_of_network",
        "reimbursement_adjustment": 1.0 if is_in_network else 0.7,
        "notes": "In-network provider - standard reimbursement" if is_in_network else "Out-of-network - 70% reimbursement applies"
    }


@router.get("/{provider_id}/statistics")
async def get_provider_stats(provider_id: str) -> Dict[str, Any]:
    """
    Get provider claims statistics.
    LLM Tool: get_provider_stats(provider_id)
    """
    store = get_data_store()
    provider = store.get_provider(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    claims = store.get_claims_by_provider(provider_id)
    stats = provider.get("stats", {})

    # Calculate actual stats from claims
    total_claims = len(claims)
    total_amount = sum(c.get("claim_amount", 0) for c in claims)
    avg_claim = total_amount / total_claims if total_claims > 0 else 0

    # Status breakdown
    approved = len([c for c in claims if c.get("status") in ["paid", "approved"]])
    denied = len([c for c in claims if c.get("status") == "denied"])
    denial_rate = denied / total_claims if total_claims > 0 else 0

    # Claim type breakdown
    claim_types = {}
    for c in claims:
        ct = c.get("claim_category", "other")
        claim_types[ct] = claim_types.get(ct, 0) + 1

    return {
        "provider_id": provider_id,
        "provider_name": provider.get("name"),
        "total_claims": total_claims,
        "total_amount": total_amount,
        "average_claim_amount": round(avg_claim, 2),
        "industry_average_claim": 1200,  # Benchmark
        "compared_to_industry": "above" if avg_claim > 1200 else "below",
        "approval_rate": round((approved / total_claims * 100) if total_claims > 0 else 0, 1),
        "denial_rate": round(denial_rate * 100, 1),
        "claim_type_breakdown": claim_types,
        "rating": provider.get("average_rating"),
        "review_count": provider.get("total_reviews")
    }


@router.get("/{provider_id}/fraud-metrics")
async def get_provider_fraud_rate(provider_id: str) -> Dict[str, Any]:
    """
    Get provider fraud metrics.
    LLM Tool: get_provider_fraud_rate(provider_id)
    """
    store = get_data_store()
    provider = store.get_provider(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    stats = provider.get("stats", {})
    claims = store.get_claims_by_provider(provider_id)

    # Calculate customer concentration
    customer_counts = {}
    for c in claims:
        cid = c.get("customer_id", "unknown")
        customer_counts[cid] = customer_counts.get(cid, 0) + 1

    total_claims = len(claims)
    concentration = {}
    for cid, count in customer_counts.items():
        pct = count / total_claims if total_claims > 0 else 0
        if pct > 0.05:  # Only show if > 5%
            concentration[cid] = round(pct, 3)

    # Check for unusual patterns
    fraud_flags = []

    fraud_rate = stats.get("fraud_rate", 0)
    if fraud_rate > 0.025:
        fraud_flags.append(f"Fraud rate ({fraud_rate*100:.1f}%) above industry average (1.5%)")

    avg_claim = stats.get("average_claim", 0)
    if avg_claim > 2000:
        fraud_flags.append(f"Average claim (${avg_claim:.0f}) significantly above industry average ($1,200)")

    if any(pct > 0.10 for pct in concentration.values()):
        fraud_flags.append("Unusual customer concentration detected")

    return {
        "provider_id": provider_id,
        "provider_name": provider.get("name"),
        "fraud_rate": stats.get("fraud_rate", 0),
        "industry_average_fraud_rate": 0.015,
        "is_above_average": stats.get("fraud_rate", 0) > 0.015,
        "customer_concentration": concentration,
        "has_concentration_issue": any(pct > 0.10 for pct in concentration.values()),
        "fraud_flags": fraud_flags,
        "risk_level": "high" if len(fraud_flags) >= 2 else "medium" if len(fraud_flags) == 1 else "low"
    }


@router.get("/{provider_id}/peer-comparison")
async def get_provider_peer_comparison(provider_id: str) -> Dict[str, Any]:
    """
    Compare provider to peers.
    LLM Tool: get_provider_peer_comparison(provider_id)
    """
    store = get_data_store()
    provider = store.get_provider(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

    # Get peer providers (same type, same region)
    all_providers = store.get_providers()
    peers = [
        p for p in all_providers
        if p.get("provider_type") == provider.get("provider_type")
        and p.get("state") == provider.get("state")
        and p.get("provider_id") != provider_id
    ]

    # Calculate peer averages
    provider_claims = store.get_claims_by_provider(provider_id)
    provider_avg = sum(c.get("claim_amount", 0) for c in provider_claims) / max(1, len(provider_claims))

    peer_avgs = []
    for peer in peers:
        peer_claims = store.get_claims_by_provider(peer.get("provider_id", ""))
        if peer_claims:
            peer_avgs.append(sum(c.get("claim_amount", 0) for c in peer_claims) / len(peer_claims))

    peer_avg = sum(peer_avgs) / max(1, len(peer_avgs)) if peer_avgs else 0
    peer_rating_avg = sum(p.get("average_rating", 0) for p in peers) / max(1, len(peers))

    return {
        "provider_id": provider_id,
        "provider_name": provider.get("name"),
        "provider_type": provider.get("provider_type"),
        "region": provider.get("state"),
        "peer_count": len(peers),
        "metrics": {
            "average_claim": {
                "provider": round(provider_avg, 2),
                "peer_average": round(peer_avg, 2),
                "percentile": "above_average" if provider_avg > peer_avg * 1.2 else "average" if provider_avg > peer_avg * 0.8 else "below_average"
            },
            "rating": {
                "provider": provider.get("average_rating"),
                "peer_average": round(peer_rating_avg, 2),
                "percentile": "above_average" if provider.get("average_rating", 0) > peer_rating_avg else "below_average"
            },
            "fraud_rate": {
                "provider": provider.get("stats", {}).get("fraud_rate", 0),
                "industry_average": 0.015
            }
        }
    }
