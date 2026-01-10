"""
Cost Monitoring Service - Provides mock cost data for Admin Portal.
In production, this would connect to AWS Cost Explorer and Azure Cost Management APIs.
"""

import logging
from datetime import date, timedelta
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== ENUMS ====================

class CloudProvider(str, Enum):
    AZURE = "azure"
    AWS = "aws"
    ALL = "all"


class TimeGranularity(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ==================== MODELS ====================

class CostSummary(BaseModel):
    """Cost summary for a cloud provider."""
    provider: str
    total_cost: float
    currency: str = "USD"
    period_start: date
    period_end: date
    by_service: dict
    daily_costs: List[dict] = []
    is_mock_data: bool = True


class CostForecast(BaseModel):
    """Cost forecast."""
    provider: str
    forecast_period_start: date
    forecast_period_end: date
    forecasted_cost: float
    confidence_level: float = 0.75
    is_mock_data: bool = True


class CostDashboardData(BaseModel):
    """Complete dashboard data."""
    azure_summary: CostSummary
    aws_summary: CostSummary
    combined_total: float
    currency: str = "USD"
    is_mock_data: bool = True
    mtd_cost: float
    cost_change_vs_last_month: float
    cost_change_percent: float
    top_services: List[dict]
    active_alerts: List[dict] = []
    triggered_alerts: List[dict] = []
    current_month_forecast: CostForecast
    ai_ml_costs: dict
    ai_ml_total: float


class AIUsageSummary(BaseModel):
    """AI/LLM usage summary."""
    period_start: date
    period_end: date
    total_tokens: int
    total_cost: float
    by_provider: dict
    by_model: dict
    daily_usage: List[dict] = []
    is_mock_data: bool = True


class PlatformUsageSummary(BaseModel):
    """Platform usage summary including AI, OCR, DB."""
    period_start: date
    period_end: date
    ai_usage: dict
    ocr_usage: dict
    database_usage: dict
    total_cost: float
    is_mock_data: bool = True


class BudgetAlert(BaseModel):
    """Budget alert."""
    id: str
    name: str
    provider: str
    budget_amount: float
    current_spend: float
    threshold_percent: float
    is_warning: bool = False
    is_critical: bool = False


# ==================== MOCK DATA GENERATORS ====================

def generate_mock_azure_summary(start_date: date, end_date: date) -> CostSummary:
    """Generate mock Azure cost summary."""
    days = (end_date - start_date).days + 1
    base_daily = 45.0  # Base daily cost

    daily_costs = []
    total = 0.0
    for i in range(days):
        day = start_date + timedelta(days=i)
        cost = base_daily + (i % 5) * 3 + (10 if day.weekday() < 5 else -5)
        daily_costs.append({"date": day.isoformat(), "cost": round(cost, 2)})
        total += cost

    return CostSummary(
        provider="azure",
        total_cost=round(total, 2),
        period_start=start_date,
        period_end=end_date,
        by_service={
            "Azure App Service": round(total * 0.35, 2),
            "Azure Databricks": round(total * 0.25, 2),
            "Azure Storage": round(total * 0.15, 2),
            "Azure Cosmos DB": round(total * 0.12, 2),
            "Azure OpenAI": round(total * 0.08, 2),
            "Other": round(total * 0.05, 2),
        },
        daily_costs=daily_costs,
        is_mock_data=True,
    )


def generate_mock_aws_summary(start_date: date, end_date: date) -> CostSummary:
    """Generate mock AWS cost summary."""
    days = (end_date - start_date).days + 1
    base_daily = 38.0  # Base daily cost

    daily_costs = []
    total = 0.0
    for i in range(days):
        day = start_date + timedelta(days=i)
        cost = base_daily + (i % 4) * 2.5 + (8 if day.weekday() < 5 else -3)
        daily_costs.append({"date": day.isoformat(), "cost": round(cost, 2)})
        total += cost

    return CostSummary(
        provider="aws",
        total_cost=round(total, 2),
        period_start=start_date,
        period_end=end_date,
        by_service={
            "AWS App Runner": round(total * 0.30, 2),
            "Amazon S3": round(total * 0.20, 2),
            "Amazon ECR": round(total * 0.15, 2),
            "AWS Bedrock": round(total * 0.18, 2),
            "Amazon CloudWatch": round(total * 0.10, 2),
            "Other": round(total * 0.07, 2),
        },
        daily_costs=daily_costs,
        is_mock_data=True,
    )


def generate_mock_forecast(provider: str, days: int = 30) -> CostForecast:
    """Generate mock cost forecast."""
    today = date.today()
    end_date = today + timedelta(days=days)

    # Base forecast on provider
    if provider == "azure":
        forecasted = 45.0 * days * 1.05  # 5% growth
    elif provider == "aws":
        forecasted = 38.0 * days * 1.03  # 3% growth
    else:
        forecasted = 83.0 * days * 1.04  # Combined

    return CostForecast(
        provider=provider,
        forecast_period_start=today,
        forecast_period_end=end_date,
        forecasted_cost=round(forecasted, 2),
        confidence_level=0.75,
        is_mock_data=True,
    )


# ==================== ENDPOINTS ====================

@router.get("/dashboard", response_model=CostDashboardData)
async def get_cost_dashboard():
    """Get aggregated cost dashboard data."""
    today = date.today()
    month_start = today.replace(day=1)

    # Previous month for comparison
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    # Current month data
    azure_summary = generate_mock_azure_summary(month_start, today)
    aws_summary = generate_mock_aws_summary(month_start, today)

    # Previous month data
    azure_prev = generate_mock_azure_summary(prev_month_start, prev_month_end)
    aws_prev = generate_mock_aws_summary(prev_month_start, prev_month_end)

    # Forecasts
    azure_forecast = generate_mock_forecast("azure")
    aws_forecast = generate_mock_forecast("aws")

    # Calculate totals
    combined_total = azure_summary.total_cost + aws_summary.total_cost
    prev_total = azure_prev.total_cost + aws_prev.total_cost

    cost_change = combined_total - prev_total
    cost_change_percent = (cost_change / prev_total * 100) if prev_total > 0 else 0

    # Top services
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

    # AI/ML costs
    ai_ml_costs = {
        "Azure: Azure OpenAI": azure_summary.by_service.get("Azure OpenAI", 0),
        "AWS: AWS Bedrock": aws_summary.by_service.get("AWS Bedrock", 0),
    }

    return CostDashboardData(
        azure_summary=azure_summary,
        aws_summary=aws_summary,
        combined_total=round(combined_total, 2),
        mtd_cost=round(combined_total, 2),
        cost_change_vs_last_month=round(cost_change, 2),
        cost_change_percent=round(cost_change_percent, 1),
        top_services=top_services,
        current_month_forecast=CostForecast(
            provider="all",
            forecast_period_start=today,
            forecast_period_end=today.replace(day=28) + timedelta(days=4),
            forecasted_cost=round(azure_forecast.forecasted_cost + aws_forecast.forecasted_cost, 2),
            confidence_level=0.75,
            is_mock_data=True,
        ),
        ai_ml_costs=ai_ml_costs,
        ai_ml_total=round(sum(ai_ml_costs.values()), 2),
        is_mock_data=True,
    )


@router.get("/azure/summary", response_model=CostSummary)
async def get_azure_cost_summary(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    granularity: TimeGranularity = TimeGranularity.DAILY,
):
    """Get Azure cost summary."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    return generate_mock_azure_summary(start_date, end_date)


@router.get("/aws/summary", response_model=CostSummary)
async def get_aws_cost_summary(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    granularity: TimeGranularity = TimeGranularity.DAILY,
):
    """Get AWS cost summary."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    return generate_mock_aws_summary(start_date, end_date)


@router.get("/forecast")
async def get_cost_forecast(
    provider: CloudProvider = CloudProvider.ALL,
    days: int = Query(default=30, ge=1, le=90),
):
    """Get cost forecast."""
    result = {"forecasts": []}

    if provider in [CloudProvider.ALL, CloudProvider.AZURE]:
        azure_forecast = generate_mock_forecast("azure", days)
        result["forecasts"].append(azure_forecast)

    if provider in [CloudProvider.ALL, CloudProvider.AWS]:
        aws_forecast = generate_mock_forecast("aws", days)
        result["forecasts"].append(aws_forecast)

    if provider == CloudProvider.ALL:
        total = sum(f.forecasted_cost for f in result["forecasts"])
        result["combined_forecast"] = round(total, 2)

    return result


@router.get("/ai-usage", response_model=AIUsageSummary)
async def get_ai_usage(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    """Get AI/LLM API usage and costs."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    days = (end_date - start_date).days + 1

    # Mock token usage
    daily_tokens_anthropic = 15000
    daily_tokens_openai = 8000

    return AIUsageSummary(
        period_start=start_date,
        period_end=end_date,
        total_tokens=(daily_tokens_anthropic + daily_tokens_openai) * days,
        total_cost=round(days * 2.50, 2),  # ~$2.50/day for AI
        by_provider={
            "anthropic": {
                "tokens": daily_tokens_anthropic * days,
                "cost": round(days * 1.80, 2),
                "models": ["claude-sonnet-4-20250514"],
            },
            "openai": {
                "tokens": daily_tokens_openai * days,
                "cost": round(days * 0.70, 2),
                "models": ["gpt-4o-mini"],
            },
        },
        by_model={
            "claude-sonnet-4-20250514": {
                "tokens": daily_tokens_anthropic * days,
                "cost": round(days * 1.80, 2),
            },
            "gpt-4o-mini": {
                "tokens": daily_tokens_openai * days,
                "cost": round(days * 0.70, 2),
            },
        },
        daily_usage=[
            {
                "date": (start_date + timedelta(days=i)).isoformat(),
                "tokens": daily_tokens_anthropic + daily_tokens_openai,
                "cost": 2.50,
            }
            for i in range(days)
        ],
        is_mock_data=True,
    )


@router.get("/platform-usage", response_model=PlatformUsageSummary)
async def get_platform_usage(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    """Get platform usage including AI, OCR, and database costs."""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()

    days = (end_date - start_date).days + 1

    ai_cost = days * 2.50
    ocr_cost = days * 0.80
    db_cost = days * 1.20

    return PlatformUsageSummary(
        period_start=start_date,
        period_end=end_date,
        ai_usage={
            "total_requests": days * 150,
            "total_tokens": days * 23000,
            "cost": round(ai_cost, 2),
            "by_provider": {
                "anthropic": {"requests": days * 100, "cost": round(ai_cost * 0.72, 2)},
                "openai": {"requests": days * 50, "cost": round(ai_cost * 0.28, 2)},
            },
        },
        ocr_usage={
            "total_pages": days * 45,
            "cost": round(ocr_cost, 2),
            "by_service": {
                "azure_document_intelligence": {"pages": days * 45, "cost": round(ocr_cost, 2)},
            },
        },
        database_usage={
            "total_operations": days * 5000,
            "storage_gb": 2.5,
            "cost": round(db_cost, 2),
            "by_database": {
                "cosmos_db": {"operations": days * 3000, "cost": round(db_cost * 0.6, 2)},
                "blob_storage": {"operations": days * 2000, "cost": round(db_cost * 0.4, 2)},
            },
        },
        total_cost=round(ai_cost + ocr_cost + db_cost, 2),
        is_mock_data=True,
    )


@router.get("/budgets", response_model=List[BudgetAlert])
async def get_budget_alerts():
    """Get budget alerts."""
    # Return sample budget alerts
    return [
        BudgetAlert(
            id="budget-001",
            name="Monthly AI Spend",
            provider="all",
            budget_amount=100.0,
            current_spend=75.0,
            threshold_percent=80,
            is_warning=False,
            is_critical=False,
        ),
        BudgetAlert(
            id="budget-002",
            name="Azure Services",
            provider="azure",
            budget_amount=500.0,
            current_spend=425.0,
            threshold_percent=80,
            is_warning=True,
            is_critical=False,
        ),
        BudgetAlert(
            id="budget-003",
            name="AWS Services",
            provider="aws",
            budget_amount=400.0,
            current_spend=320.0,
            threshold_percent=80,
            is_warning=False,
            is_critical=False,
        ),
    ]


@router.post("/budgets", response_model=BudgetAlert)
async def create_budget_alert(budget: dict):
    """Create a budget alert (mock - returns the input with generated ID)."""
    from uuid import uuid4
    return BudgetAlert(
        id=f"budget-{uuid4().hex[:8]}",
        name=budget.get("name", "New Budget"),
        provider=budget.get("provider", "all"),
        budget_amount=budget.get("budget_amount", 100.0),
        current_spend=0.0,
        threshold_percent=budget.get("threshold_percent", 80),
    )


@router.put("/budgets/{budget_id}", response_model=BudgetAlert)
async def update_budget_alert(budget_id: str, budget: dict):
    """Update a budget alert (mock)."""
    return BudgetAlert(
        id=budget_id,
        name=budget.get("name", "Updated Budget"),
        provider=budget.get("provider", "all"),
        budget_amount=budget.get("budget_amount", 100.0),
        current_spend=budget.get("current_spend", 0.0),
        threshold_percent=budget.get("threshold_percent", 80),
    )


@router.delete("/budgets/{budget_id}")
async def delete_budget_alert(budget_id: str):
    """Delete a budget alert (mock)."""
    return {"message": f"Budget {budget_id} deleted"}
