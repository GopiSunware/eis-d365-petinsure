"""
PetInsure360 - BI Insights API
Endpoints for querying Gold layer analytics data
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional

router = APIRouter()


def get_insights_service(request: Request):
    """Get insights service from app state."""
    return request.app.state.insights


@router.get("/summary")
async def get_summary(request: Request):
    """Get summary statistics about the data."""
    insights_service = get_insights_service(request)
    return insights_service.get_summary_stats()

@router.get("/kpis")
async def get_kpis(request: Request, limit: int = Query(12, ge=1, le=24)):
    """
    Get monthly KPI metrics.

    Returns:
        List of monthly KPIs including claims, revenue, approval rates, etc.
    """
    insights_service = get_insights_service(request)
    return {
        "kpis": insights_service.get_monthly_kpis(limit=limit),
        "description": "Monthly KPI aggregations from the Gold layer"
    }

@router.get("/customers")
async def get_customers(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[str] = None,
    risk: Optional[str] = None
):
    """
    Get customer 360 views.

    Returns:
        List of customers with unified profile data
    """
    insights_service = get_insights_service(request)
    customers = insights_service.get_customer_360(limit=limit)

    # Apply filters
    if tier:
        customers = [c for c in customers if c.get('customer_value_tier') == tier]
    if risk:
        customers = [c for c in customers if c.get('customer_risk_score') == risk]

    return {
        "customers": customers,
        "count": len(customers),
        "description": "Customer 360 unified profiles from the Gold layer"
    }

@router.get("/customers/{customer_id}")
async def get_customer_360(customer_id: str, request: Request):
    """
    Get detailed customer 360 view for a specific customer.

    Returns:
        Complete customer profile with all metrics
    """
    insights_service = get_insights_service(request)
    customers = insights_service.get_customer_360(customer_id=customer_id)

    if not customers:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return {
        "customer": customers[0],
        "description": "Detailed customer 360 view from the Gold layer"
    }

@router.get("/claims")
async def get_claims(
    request: Request,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get claims analytics with optional filters.

    Returns:
        List of claims with analytics dimensions
    """
    insights_service = get_insights_service(request)
    claims = insights_service.get_claims_analytics(
        status=status,
        category=category,
        limit=limit,
        offset=offset
    )

    return {
        "claims": claims,
        "count": len(claims),
        "filters": {
            "status": status,
            "category": category
        },
        "pagination": {
            "limit": limit,
            "offset": offset
        },
        "description": "Claims analytics from the Gold layer"
    }

@router.get("/providers")
async def get_providers(request: Request, limit: int = Query(50, ge=1, le=200)):
    """
    Get provider performance analytics.

    Returns:
        List of providers with performance metrics
    """
    insights_service = get_insights_service(request)
    providers = insights_service.get_provider_performance(limit=limit)

    return {
        "providers": providers,
        "count": len(providers),
        "description": "Provider performance analytics from the Gold layer"
    }

@router.get("/risks")
async def get_risk_scores(request: Request, limit: int = Query(100, ge=1, le=1000)):
    """
    Get customer risk scores.

    Returns:
        List of customers with risk assessment
    """
    insights_service = get_insights_service(request)
    risks = insights_service.get_risk_scores(limit=limit)

    # Aggregate risk distribution
    risk_distribution = {}
    for r in risks:
        category = r.get('risk_category', 'Unknown')
        risk_distribution[category] = risk_distribution.get(category, 0) + 1

    return {
        "risk_scores": risks,
        "distribution": risk_distribution,
        "count": len(risks),
        "description": "Customer risk assessment from the Gold layer"
    }

@router.get("/cross-sell")
async def get_cross_sell(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[str] = None
):
    """
    Get cross-sell recommendations.

    Returns:
        List of customers with upsell opportunities
    """
    insights_service = get_insights_service(request)
    recommendations = insights_service.get_cross_sell(limit=limit)

    # Apply tier filter
    if tier:
        recommendations = [r for r in recommendations if r.get('customer_value_tier') == tier]

    # Calculate total opportunity
    total_opportunity = sum(r.get('estimated_revenue_opportunity', 0) for r in recommendations)

    return {
        "recommendations": recommendations,
        "count": len(recommendations),
        "total_opportunity": round(total_opportunity, 2),
        "description": "Cross-sell recommendations from the Gold layer"
    }

@router.get("/segments")
async def get_customer_segments(request: Request):
    """
    Get customer segmentation summary.

    Returns:
        Aggregated customer segments
    """
    insights_service = get_insights_service(request)
    customers = insights_service.get_customer_360(limit=10000)

    # Aggregate by tier
    segments = {}
    for c in customers:
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

    return {
        "segments": list(segments.values()),
        "total_customers": len(customers),
        "description": "Customer segmentation summary"
    }
