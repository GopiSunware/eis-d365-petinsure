"""Cost monitoring endpoints."""

import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..middleware.auth import require_permission
from ..models.users import User, Permission
from ..models.costs import (
    CloudProvider,
    CostSummary,
    CostDashboardData,
    BudgetAlert,
    BudgetAlertCreate,
    BudgetAlertUpdate,
    CostForecast,
    TimeGranularity,
)
from ..models.ai_usage import (
    AIUsageSummary,
    PlatformUsageSummary,
)
from ..services.azure_cost_service import get_azure_cost_service
from ..services.aws_cost_service import get_aws_cost_service
from ..services.ai_usage_service import get_ai_usage_service
from ..services.cosmos_service import get_cosmos_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=CostDashboardData)
async def get_cost_dashboard(
    current_user: User = Depends(require_permission(Permission.COST_READ)),
):
    """Get aggregated cost dashboard data."""
    azure_service = get_azure_cost_service()
    aws_service = get_aws_cost_service()

    # Get current month data
    today = date.today()
    month_start = today.replace(day=1)

    # Get previous month for comparison
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    # Fetch data in parallel (in real async implementation)
    azure_summary = await azure_service.get_cost_summary(month_start, today)
    aws_summary = await aws_service.get_cost_summary(month_start, today)

    # Previous month for comparison
    azure_prev = await azure_service.get_cost_summary(prev_month_start, prev_month_end)
    aws_prev = await aws_service.get_cost_summary(prev_month_start, prev_month_end)

    # Forecasts
    azure_forecast = await azure_service.get_forecast()
    aws_forecast = await aws_service.get_forecast()

    # Combine totals
    combined_total = azure_summary.total_cost + aws_summary.total_cost
    prev_total = azure_prev.total_cost + aws_prev.total_cost

    # Calculate change
    cost_change = combined_total - prev_total
    cost_change_percent = (cost_change / prev_total * 100) if prev_total > 0 else 0

    # Top services (combined)
    all_services = {}
    for service, cost in azure_summary.by_service.items():
        all_services[f"Azure: {service}"] = cost
    for service, cost in aws_summary.by_service.items():
        all_services[f"AWS: {service}"] = cost

    top_services = sorted(
        [{"name": k, "cost": v, "provider": k.split(":")[0].strip().lower()}
         for k, v in all_services.items()],
        key=lambda x: x["cost"],
        reverse=True
    )[:10]

    # Get budget alerts
    budgets = await get_budget_alerts(current_user)
    triggered = [b for b in budgets if b.is_warning or b.is_critical]

    # AI/ML costs
    ai_ml_costs = {}
    ai_ml_keywords = ["openai", "bedrock", "cognitive", "ml", "ai"]
    for service, cost in all_services.items():
        if any(kw in service.lower() for kw in ai_ml_keywords):
            ai_ml_costs[service] = cost

    # Determine if any data is mock
    is_mock = azure_summary.is_mock_data or aws_summary.is_mock_data

    return CostDashboardData(
        azure_summary=azure_summary,
        aws_summary=aws_summary,
        combined_total=round(combined_total, 2),
        currency="USD",
        is_mock_data=is_mock,
        mtd_cost=round(combined_total, 2),
        cost_change_vs_last_month=round(cost_change, 2),
        cost_change_percent=round(cost_change_percent, 1),
        top_services=top_services,
        active_alerts=budgets,
        triggered_alerts=triggered,
        current_month_forecast=CostForecast(
            provider=CloudProvider.ALL,
            forecast_period_start=today,
            forecast_period_end=today.replace(day=28) + timedelta(days=4),
            forecasted_cost=round(azure_forecast.forecasted_cost + aws_forecast.forecasted_cost, 2),
            confidence_level=0.75,
            is_mock_data=azure_forecast.is_mock_data or aws_forecast.is_mock_data,
        ),
        ai_ml_costs=ai_ml_costs,
        ai_ml_total=round(sum(ai_ml_costs.values()), 2),
    )


@router.get("/azure/summary", response_model=CostSummary)
async def get_azure_cost_summary(
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    granularity: TimeGranularity = TimeGranularity.DAILY,
    current_user: User = Depends(require_permission(Permission.COST_READ)),
):
    """Get Azure cost summary."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    azure_service = get_azure_cost_service()
    return await azure_service.get_cost_summary(start_date, end_date, granularity)


@router.get("/aws/summary", response_model=CostSummary)
async def get_aws_cost_summary(
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    granularity: TimeGranularity = TimeGranularity.DAILY,
    current_user: User = Depends(require_permission(Permission.COST_READ)),
):
    """Get AWS cost summary."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    aws_service = get_aws_cost_service()
    return await aws_service.get_cost_summary(start_date, end_date, granularity)


@router.get("/forecast", response_model=dict)
async def get_cost_forecast(
    provider: CloudProvider = CloudProvider.ALL,
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(require_permission(Permission.COST_READ)),
):
    """Get cost forecast."""
    azure_service = get_azure_cost_service()
    aws_service = get_aws_cost_service()

    result = {"forecasts": []}

    if provider in [CloudProvider.ALL, CloudProvider.AZURE]:
        azure_forecast = await azure_service.get_forecast(days)
        result["forecasts"].append(azure_forecast)

    if provider in [CloudProvider.ALL, CloudProvider.AWS]:
        aws_forecast = await aws_service.get_forecast(days)
        result["forecasts"].append(aws_forecast)

    if provider == CloudProvider.ALL:
        total = sum(f.forecasted_cost for f in result["forecasts"])
        result["combined_forecast"] = round(total, 2)

    return result


# AI Usage endpoints
@router.get("/ai-usage", response_model=AIUsageSummary)
async def get_ai_usage(
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    current_user: User = Depends(require_permission(Permission.COST_READ)),
):
    """Get AI/LLM API usage and token costs."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    ai_service = get_ai_usage_service()
    return await ai_service.get_ai_usage_summary(start_date, end_date)


@router.get("/platform-usage", response_model=PlatformUsageSummary)
async def get_platform_usage(
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    current_user: User = Depends(require_permission(Permission.COST_READ)),
):
    """Get complete platform usage including AI, Document OCR, and Database costs."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    ai_service = get_ai_usage_service()
    return await ai_service.get_platform_usage_summary(start_date, end_date)


# Budget Alert endpoints
_budget_store: List[dict] = []  # In-memory fallback


@router.get("/budgets", response_model=List[BudgetAlert])
async def get_budget_alerts(
    current_user: User = Depends(require_permission(Permission.COST_READ)),
) -> List[BudgetAlert]:
    """Get all budget alerts (user-created only, no mock data)."""
    cosmos = get_cosmos_client()

    if cosmos._initialized:
        results = await cosmos.query_all("budget_alerts")
        return [BudgetAlert(**r) for r in results]

    # Return only user-created budgets from memory store (no mock data)

    return [BudgetAlert(**b) for b in _budget_store]


@router.post("/budgets", response_model=BudgetAlert)
async def create_budget_alert(
    budget: BudgetAlertCreate,
    current_user: User = Depends(require_permission(Permission.COST_BUDGET_WRITE)),
):
    """Create a new budget alert."""
    from uuid import uuid4

    budget_alert = BudgetAlert(
        id=f"budget-{uuid4().hex[:8]}",
        **budget.model_dump(),
    )

    cosmos = get_cosmos_client()
    if cosmos._initialized:
        await cosmos.create_document(
            collection="budget_alerts",
            document=budget_alert.model_dump(),
            partition_key=budget_alert.provider,
        )
    else:
        _budget_store.append(budget_alert.model_dump())

    return budget_alert


@router.put("/budgets/{budget_id}", response_model=BudgetAlert)
async def update_budget_alert(
    budget_id: str,
    update: BudgetAlertUpdate,
    current_user: User = Depends(require_permission(Permission.COST_BUDGET_WRITE)),
):
    """Update a budget alert."""
    budgets = await get_budget_alerts(current_user)

    for i, budget in enumerate(budgets):
        if budget.id == budget_id:
            budget_dict = budget.model_dump()
            for key, value in update.model_dump(exclude_none=True).items():
                budget_dict[key] = value

            cosmos = get_cosmos_client()
            if cosmos._initialized:
                await cosmos.update_document(
                    collection="budget_alerts",
                    document_id=budget_id,
                    document=budget_dict,
                    partition_key=budget_dict.get("provider"),
                )
            else:
                _budget_store[i] = budget_dict

            return BudgetAlert(**budget_dict)

    raise HTTPException(status_code=404, detail=f"Budget {budget_id} not found")


@router.delete("/budgets/{budget_id}")
async def delete_budget_alert(
    budget_id: str,
    current_user: User = Depends(require_permission(Permission.COST_BUDGET_WRITE)),
):
    """Delete a budget alert."""
    cosmos = get_cosmos_client()

    if cosmos._initialized:
        # Find the budget to get partition key
        budgets = await get_budget_alerts(current_user)
        for budget in budgets:
            if budget.id == budget_id:
                await cosmos.delete_document(
                    collection="budget_alerts",
                    document_id=budget_id,
                    partition_key=budget.provider,
                )
                return {"message": f"Budget {budget_id} deleted"}
    else:
        global _budget_store
        _budget_store = [b for b in _budget_store if b.get("id") != budget_id]
        return {"message": f"Budget {budget_id} deleted"}

    raise HTTPException(status_code=404, detail=f"Budget {budget_id} not found")
