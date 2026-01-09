"""
Insights Service - BI Analytics endpoints for Claims Data API.
Provides customer 360, claims analytics, KPIs, segmentation, and pipeline data.
Optimized with pre-computed indexes for fast lookups.

Supports hybrid data sources:
- Demo data (synthetic) - always available
- Azure Gold Layer - when configured and available
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict, Any
from enum import Enum
import random

from fastapi import APIRouter, Query, HTTPException

from app.data_loader import get_data_store

# Import data source service for hybrid support
try:
    from app.services.data_source_service import get_data_source_config, get_data_provider
    DATA_SOURCE_AVAILABLE = True
except ImportError:
    DATA_SOURCE_AVAILABLE = False

router = APIRouter()


# ==================== SORTING ENUMS ====================

class CustomerSortField(str, Enum):
    NAME = "name"
    CUSTOMER_SINCE = "customer_since"
    TOTAL_CLAIMS = "total_claims"
    TOTAL_PREMIUM = "total_premium"
    LAST_CLAIM = "last_claim"


class ClaimSortField(str, Enum):
    CLAIM_DATE = "claim_date"
    CLAIM_AMOUNT = "claim_amount"
    STATUS = "status"
    CREATED_AT = "created_at"


# ==================== PRE-COMPUTED INDEXES ====================

# Cache for pre-computed metrics (rebuilt on first access)
_customer_metrics_cache: Dict[str, Dict] = {}
_claims_by_customer: Dict[str, List[Dict]] = {}
_policies_by_customer: Dict[str, List[Dict]] = {}
_cache_built = False


def _build_indexes():
    """Build lookup indexes for fast customer metrics calculation."""
    global _claims_by_customer, _policies_by_customer, _cache_built

    if _cache_built:
        return

    store = get_data_store()
    claims = store.get_claims()
    policies = store.get_policies()

    # Build claims index by customer
    _claims_by_customer.clear()
    for claim in claims:
        cust_id = claim.get("customer_id")
        if cust_id:
            if cust_id not in _claims_by_customer:
                _claims_by_customer[cust_id] = []
            _claims_by_customer[cust_id].append(claim)

    # Build policies index by customer
    _policies_by_customer.clear()
    for policy in policies:
        cust_id = policy.get("customer_id")
        if cust_id:
            if cust_id not in _policies_by_customer:
                _policies_by_customer[cust_id] = []
            _policies_by_customer[cust_id].append(policy)

    _cache_built = True


def _get_customer_claims(customer_id: str) -> List[Dict]:
    """Get claims for a customer using pre-built index."""
    _build_indexes()
    return _claims_by_customer.get(customer_id, [])


def _get_customer_policies(customer_id: str) -> List[Dict]:
    """Get policies for a customer using pre-built index."""
    _build_indexes()
    return _policies_by_customer.get(customer_id, [])


# ==================== DEMO CUSTOMERS ====================

DEMO_CUSTOMERS = [
    {
        "customer_id": "DEMO-001",
        "first_name": "Demo",
        "last_name": "User",
        "email": "demo@demologin.com",
        "phone": "(555) 123-4567",
        "address_line1": "123 Demo Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "customer_since": datetime.now().strftime("%Y-%m-%d"),
        "segment": "active",
    },
    {
        "customer_id": "DEMO-002",
        "first_name": "Demo",
        "last_name": "One",
        "email": "demo1@demologin.com",
        "phone": "(555) 234-5678",
        "address_line1": "456 Test Ave",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201",
        "customer_since": datetime.now().strftime("%Y-%m-%d"),
        "segment": "active",
    },
    {
        "customer_id": "DEMO-003",
        "first_name": "Demo",
        "last_name": "Two",
        "email": "demo2@demologin.com",
        "phone": "(555) 345-6789",
        "address_line1": "789 Sample Blvd",
        "city": "Houston",
        "state": "TX",
        "zip_code": "77001",
        "customer_since": datetime.now().strftime("%Y-%m-%d"),
        "segment": "active",
    },
]


# ==================== HELPER FUNCTIONS ====================

def calculate_customer_metrics_fast(customer: Dict) -> Dict:
    """Calculate customer 360 metrics using indexed lookups (O(1) instead of O(n))."""
    customer_id = customer.get("customer_id")

    # Use indexed lookups
    customer_claims = _get_customer_claims(customer_id)
    customer_policies = _get_customer_policies(customer_id)

    # Calculate metrics
    total_claims = len(customer_claims)
    total_premium = sum(p.get("annual_premium", 0) for p in customer_policies)
    total_claim_amount = sum(c.get("claim_amount", 0) for c in customer_claims)
    approved_claims = [c for c in customer_claims if c.get("status") == "approved"]

    # Loss ratio
    loss_ratio = (total_claim_amount / total_premium * 100) if total_premium > 0 else 0

    # Determine value tier based on premium and loss ratio
    if total_premium > 2000 and loss_ratio < 50:
        tier = "Platinum"
    elif total_premium > 1000 and loss_ratio < 70:
        tier = "Gold"
    elif total_premium > 500:
        tier = "Silver"
    else:
        tier = "Bronze"

    # Risk score based on claims frequency and loss ratio
    if loss_ratio > 100 or total_claims > 10:
        risk = "High"
    elif loss_ratio > 70 or total_claims > 5:
        risk = "Medium"
    else:
        risk = "Low"

    # Build name from first_name and last_name
    first_name = customer.get("first_name", "")
    last_name = customer.get("last_name", "")
    name = f"{first_name} {last_name}".strip() or customer.get("name", "Unknown")

    # Build address from components
    address = customer.get("address_line1", "")
    if customer.get("city"):
        address += f", {customer.get('city')}"
    if customer.get("state"):
        address += f", {customer.get('state')}"
    if customer.get("zip_code"):
        address += f" {customer.get('zip_code')}"

    # Get last claim date (sort by date first)
    last_claim_date = None
    if customer_claims:
        sorted_claims = sorted(
            customer_claims,
            key=lambda x: x.get("claim_date", "") or x.get("service_date", "") or "",
            reverse=True
        )
        last_claim_date = sorted_claims[0].get("claim_date") or sorted_claims[0].get("service_date")

    # Get customer_since date
    customer_since = customer.get("customer_since", "")

    return {
        "customer_id": customer_id,
        "name": name,
        "email": customer.get("email", ""),
        "phone": customer.get("phone", ""),
        "address": address or customer.get("address", ""),
        "segment": customer.get("segment", "Standard"),
        "customer_value_tier": tier,
        "customer_risk_score": risk,
        "total_claims": total_claims,
        "approved_claims": len(approved_claims),
        "total_annual_premium": round(total_premium, 2),
        "total_claim_amount": round(total_claim_amount, 2),
        "loss_ratio": round(loss_ratio, 2),
        "active_policies": len([p for p in customer_policies if p.get("status") == "active"]),
        "customer_since": customer_since,
        "last_claim_date": last_claim_date,
    }


def generate_monthly_kpis(claims: List[Dict], customers: List[Dict], limit: int = 12) -> List[Dict]:
    """Generate monthly KPI aggregations."""
    kpis = []
    today = datetime.now()

    for i in range(limit):
        month_date = today - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")

        # Filter claims for this month (approximate)
        month_claims = [
            c for c in claims
            if (c.get("claim_date", "") or c.get("service_date", ""))[:7] == month_str
        ]

        # If no claims match, generate synthetic metrics
        if not month_claims:
            base_claims = len(claims) // 12
            month_claims_count = base_claims + random.randint(-50, 50)
            approved = int(month_claims_count * 0.72)
            denied = int(month_claims_count * 0.18)
            pending = month_claims_count - approved - denied
            total_amount = month_claims_count * random.uniform(250, 400)
            avg_amount = total_amount / month_claims_count if month_claims_count > 0 else 0
        else:
            month_claims_count = len(month_claims)
            approved = len([c for c in month_claims if c.get("status") == "approved"])
            denied = len([c for c in month_claims if c.get("status") == "denied"])
            pending = len([c for c in month_claims if c.get("status") == "pending"])
            total_amount = sum(c.get("claim_amount", 0) for c in month_claims)
            avg_amount = total_amount / month_claims_count if month_claims_count > 0 else 0

        kpis.append({
            "month": month_str,
            "total_claims": month_claims_count,
            "approved_claims": approved,
            "denied_claims": denied,
            "pending_claims": pending,
            "approval_rate": round(approved / month_claims_count * 100, 1) if month_claims_count > 0 else 0,
            "total_claim_amount": round(total_amount, 2),
            "avg_claim_amount": round(avg_amount, 2),
            "new_customers": random.randint(50, 150),
            "churned_customers": random.randint(10, 40),
            "revenue": round(random.uniform(150000, 250000), 2),
        })

    return list(reversed(kpis))  # Oldest first


# ==================== ENDPOINTS ====================

@router.get("/summary")
async def get_summary():
    """Get summary statistics about the data."""
    store = get_data_store()

    customers = store.get_customers()
    pets = store.get_pets()
    policies = store.get_policies()
    claims = store.get_claims()
    providers = store.get_providers()

    # Calculate totals
    total_premium = sum(p.get("annual_premium", 0) for p in policies)
    total_claims_amount = sum(c.get("claim_amount", 0) for c in claims)
    approved_claims = [c for c in claims if c.get("status") == "approved"]

    # Get data source info
    data_source_info = {
        "source": "demo",
        "description": "Synthetic demo data"
    }
    if DATA_SOURCE_AVAILABLE:
        config = get_data_source_config()
        data_source_info = {
            "source": config.source.value,
            "use_azure": config.use_azure,
            "description": "Hybrid: Azure Gold Layer with demo fallback" if config.use_azure else "Synthetic demo data"
        }

    return {
        "total_customers": len(customers) + len(DEMO_CUSTOMERS),
        "total_pets": len(pets),
        "total_policies": len(policies),
        "active_policies": len([p for p in policies if p.get("status") == "active"]),
        "total_claims": len(claims),
        "approved_claims": len(approved_claims),
        "pending_claims": len([c for c in claims if c.get("status") == "pending"]),
        "denied_claims": len([c for c in claims if c.get("status") == "denied"]),
        "total_providers": len(providers),
        "in_network_providers": len([p for p in providers if p.get("is_in_network")]),
        "total_premium_revenue": round(total_premium, 2),
        "total_claims_paid": round(total_claims_amount, 2),
        "approval_rate": round(len(approved_claims) / len(claims) * 100, 1) if claims else 0,
        "avg_claim_amount": round(total_claims_amount / len(claims), 2) if claims else 0,
        "data_source": data_source_info,
    }


@router.get("/kpis")
async def get_kpis(limit: int = Query(12, ge=1, le=24)):
    """Get monthly KPI metrics."""
    store = get_data_store()
    claims = store.get_claims()
    customers = store.get_customers()

    return {
        "kpis": generate_monthly_kpis(claims, customers, limit=limit),
        "description": "Monthly KPI aggregations from synthetic data"
    }


@router.get("/customers")
async def get_customers(
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[str] = None,
    risk: Optional[str] = None,
    sort_by: CustomerSortField = CustomerSortField.CUSTOMER_SINCE,
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """Get customer 360 views with sorting."""
    _build_indexes()  # Ensure indexes are built

    store = get_data_store()
    customers = store.get_customers()

    # Include demo customers at the top
    all_customers = DEMO_CUSTOMERS + customers

    # Build customer 360 views efficiently
    customer_360s = []
    for customer in all_customers:
        metrics = calculate_customer_metrics_fast(customer)
        customer_360s.append(metrics)

    # Apply filters
    if tier:
        customer_360s = [c for c in customer_360s if c.get('customer_value_tier') == tier]
    if risk:
        customer_360s = [c for c in customer_360s if c.get('customer_risk_score') == risk]

    # Sort customers
    reverse = sort_order == "desc"
    if sort_by == CustomerSortField.NAME:
        customer_360s.sort(key=lambda x: x.get("name", "").lower(), reverse=reverse)
    elif sort_by == CustomerSortField.CUSTOMER_SINCE:
        customer_360s.sort(key=lambda x: x.get("customer_since", "") or "", reverse=reverse)
    elif sort_by == CustomerSortField.TOTAL_CLAIMS:
        customer_360s.sort(key=lambda x: x.get("total_claims", 0), reverse=reverse)
    elif sort_by == CustomerSortField.TOTAL_PREMIUM:
        customer_360s.sort(key=lambda x: x.get("total_annual_premium", 0), reverse=reverse)
    elif sort_by == CustomerSortField.LAST_CLAIM:
        customer_360s.sort(key=lambda x: x.get("last_claim_date", "") or "", reverse=reverse)

    return {
        "customers": customer_360s[:limit],
        "count": len(customer_360s[:limit]),
        "total": len(customer_360s),
        "description": "Customer 360 unified profiles from synthetic data"
    }


@router.get("/customers/{customer_id}")
async def get_customer_360(customer_id: str):
    """Get detailed customer 360 view for a specific customer."""
    _build_indexes()

    store = get_data_store()

    # Check demo customers first
    customer = None
    for demo in DEMO_CUSTOMERS:
        if demo["customer_id"] == customer_id:
            customer = demo
            break

    if not customer:
        customer = store.get_customer(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    pets = store.get_pets_by_customer(customer_id)

    metrics = calculate_customer_metrics_fast(customer)
    metrics["pets"] = pets
    metrics["policies"] = store.get_policies_by_customer(customer_id)
    metrics["recent_claims"] = _get_customer_claims(customer_id)[:10]

    return {
        "customer": metrics,
        "description": "Detailed customer 360 view from synthetic data"
    }


@router.get("/claims")
async def get_claims(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: ClaimSortField = ClaimSortField.CLAIM_DATE,
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """Get claims analytics with optional filters and sorting."""
    store = get_data_store()
    claims = store.get_claims()

    # Apply filters
    if status:
        claims = [c for c in claims if c.get("status") == status]
    if category:
        claims = [c for c in claims if c.get("category") == category or c.get("claim_category") == category]

    # Sort claims
    reverse = sort_order == "desc"
    if sort_by == ClaimSortField.CLAIM_DATE:
        claims.sort(key=lambda x: x.get("claim_date", "") or x.get("service_date", "") or "", reverse=reverse)
    elif sort_by == ClaimSortField.CLAIM_AMOUNT:
        claims.sort(key=lambda x: x.get("claim_amount", 0), reverse=reverse)
    elif sort_by == ClaimSortField.STATUS:
        claims.sort(key=lambda x: x.get("status", ""), reverse=reverse)
    elif sort_by == ClaimSortField.CREATED_AT:
        claims.sort(key=lambda x: x.get("created_at", "") or x.get("claim_date", "") or "", reverse=reverse)

    total = len(claims)

    # Paginate
    paginated = claims[offset:offset + limit]

    # Enhance with analytics dimensions
    enhanced_claims = []
    for claim in paginated:
        enhanced = {
            **claim,
            "processing_time_days": random.randint(1, 14),
            "complexity_score": random.choice(["Low", "Medium", "High"]),
            "auto_adjudicated": random.choice([True, False]),
        }
        enhanced_claims.append(enhanced)

    return {
        "claims": enhanced_claims,
        "count": len(enhanced_claims),
        "total": total,
        "filters": {
            "status": status,
            "category": category
        },
        "pagination": {
            "limit": limit,
            "offset": offset
        },
        "description": "Claims analytics from synthetic data"
    }


@router.get("/providers")
async def get_providers(limit: int = Query(50, ge=1, le=200)):
    """Get provider performance analytics."""
    _build_indexes()

    store = get_data_store()
    providers = store.get_providers()
    claims = store.get_claims()

    # Build provider claims index
    claims_by_provider = defaultdict(list)
    for claim in claims:
        prov_id = claim.get("provider_id")
        if prov_id:
            claims_by_provider[prov_id].append(claim)

    # Build provider performance metrics
    provider_metrics = []
    for provider in providers[:limit]:
        provider_id = provider.get("provider_id")
        provider_claims = claims_by_provider.get(provider_id, [])

        total_claims = len(provider_claims)
        total_amount = sum(c.get("claim_amount", 0) for c in provider_claims)
        approved = len([c for c in provider_claims if c.get("status") == "approved"])

        provider_metrics.append({
            "provider_id": provider_id,
            "name": provider.get("name", "Unknown"),
            "specialty": provider.get("specialty", "General"),
            "is_in_network": provider.get("is_in_network", False),
            "total_claims": total_claims,
            "total_claim_amount": round(total_amount, 2),
            "avg_claim_amount": round(total_amount / total_claims, 2) if total_claims > 0 else 0,
            "approval_rate": round(approved / total_claims * 100, 1) if total_claims > 0 else 0,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "fraud_risk_score": random.choice(["Low", "Medium", "High"]),
        })

    return {
        "providers": provider_metrics,
        "count": len(provider_metrics),
        "description": "Provider performance analytics from synthetic data"
    }


@router.get("/risks")
async def get_risk_scores(limit: int = Query(100, ge=1, le=1000)):
    """Get customer risk scores."""
    _build_indexes()

    store = get_data_store()
    customers = store.get_customers()

    risks = []
    for customer in customers[:limit]:
        metrics = calculate_customer_metrics_fast(customer)
        risks.append({
            "customer_id": customer.get("customer_id"),
            "name": metrics.get("name"),
            "risk_category": metrics.get("customer_risk_score"),
            "loss_ratio": metrics.get("loss_ratio"),
            "total_claims": metrics.get("total_claims"),
            "claim_frequency": round(metrics.get("total_claims", 0) / 12, 2),
            "risk_factors": [],
        })

    # Aggregate risk distribution
    risk_distribution = {}
    for r in risks:
        category = r.get('risk_category', 'Unknown')
        risk_distribution[category] = risk_distribution.get(category, 0) + 1

    return {
        "risk_scores": risks,
        "distribution": risk_distribution,
        "count": len(risks),
        "description": "Customer risk assessment from synthetic data"
    }


@router.get("/cross-sell")
async def get_cross_sell(
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[str] = None
):
    """Get cross-sell recommendations."""
    _build_indexes()

    store = get_data_store()
    customers = store.get_customers()

    recommendations = []
    for customer in customers[:limit * 2]:
        metrics = calculate_customer_metrics_fast(customer)

        # Generate cross-sell opportunity
        opportunity = random.uniform(100, 500) if metrics.get("customer_risk_score") == "Low" else random.uniform(50, 200)

        rec = {
            "customer_id": customer.get("customer_id"),
            "name": metrics.get("name"),
            "customer_value_tier": metrics.get("customer_value_tier"),
            "current_products": metrics.get("active_policies", 1),
            "recommended_product": random.choice(["Wellness Plan", "Dental Coverage", "Premium Upgrade", "Multi-Pet Discount"]),
            "estimated_revenue_opportunity": round(opportunity, 2),
            "probability_score": round(random.uniform(0.3, 0.9), 2),
        }
        recommendations.append(rec)

    # Apply tier filter
    if tier:
        recommendations = [r for r in recommendations if r.get('customer_value_tier') == tier]

    recommendations = recommendations[:limit]

    # Calculate total opportunity
    total_opportunity = sum(r.get('estimated_revenue_opportunity', 0) for r in recommendations)

    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "total_opportunity": round(total_opportunity, 2),
        "description": "Cross-sell recommendations from synthetic data"
    }


@router.get("/segments")
async def get_customer_segments():
    """Get customer segmentation summary."""
    _build_indexes()

    store = get_data_store()
    customers = store.get_customers()

    # Build customer 360 views
    customer_360s = []
    for customer in customers:
        metrics = calculate_customer_metrics_fast(customer)
        customer_360s.append(metrics)

    # Aggregate by tier
    segments = {}
    for c in customer_360s:
        tier = c.get('customer_value_tier', 'Unknown')
        if tier not in segments:
            segments[tier] = {
                'tier': tier,
                'count': 0,
                'total_premium': 0,
                'total_claims': 0,
                'avg_loss_ratio': []
            }
        segments[tier]['count'] += 1
        segments[tier]['total_premium'] += c.get('total_annual_premium', 0)
        segments[tier]['total_claims'] += c.get('total_claims', 0)
        if c.get('loss_ratio'):
            segments[tier]['avg_loss_ratio'].append(c.get('loss_ratio'))

    # Calculate averages
    for tier, data in segments.items():
        if data['avg_loss_ratio']:
            data['avg_loss_ratio'] = round(sum(data['avg_loss_ratio']) / len(data['avg_loss_ratio']), 2)
        else:
            data['avg_loss_ratio'] = 0
        data['total_premium'] = round(data['total_premium'], 2)

    return {
        "segments": list(segments.values()),
        "total_customers": len(customer_360s) + len(DEMO_CUSTOMERS),
        "description": "Customer segmentation summary from synthetic data"
    }
