"""Cost monitoring models for Azure and AWS."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Cloud provider."""
    AZURE = "azure"
    AWS = "aws"
    ALL = "all"


class TimeGranularity(str, Enum):
    """Time granularity for cost reports."""
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class CostCategory(str, Enum):
    """Cost category."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    AI_ML = "ai_ml"
    NETWORKING = "networking"
    MESSAGING = "messaging"
    SECURITY = "security"
    MONITORING = "monitoring"
    OTHER = "other"


class CostDataPoint(BaseModel):
    """Single cost data point."""
    date: date
    amount: float
    currency: str = "USD"
    provider: CloudProvider
    service_name: Optional[str] = None
    category: Optional[CostCategory] = None
    resource_group: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class CostSummary(BaseModel):
    """Cost summary for a period."""
    provider: CloudProvider
    period_start: date
    period_end: date
    total_cost: float
    currency: str = "USD"

    # Breakdown
    by_service: Dict[str, float] = Field(default_factory=dict)
    by_category: Dict[str, float] = Field(default_factory=dict)
    by_resource_group: Dict[str, float] = Field(default_factory=dict)

    # Trend
    previous_period_cost: Optional[float] = None
    cost_change_percent: Optional[float] = None
    cost_change_amount: Optional[float] = None

    # Daily breakdown
    daily_costs: List[CostDataPoint] = Field(default_factory=list)

    # Mock data indicator
    is_mock_data: bool = Field(default=False, description="True if this is demo/mock data")


class BudgetAlert(BaseModel):
    """Budget alert configuration."""
    id: Optional[str] = None
    name: str
    provider: CloudProvider
    budget_amount: float
    currency: str = "USD"
    period: str = "monthly"  # monthly, quarterly, yearly

    # Thresholds (percentages)
    warning_threshold: int = Field(default=80, ge=0, le=100)
    critical_threshold: int = Field(default=100, ge=0, le=150)

    # Current status
    current_spend: float = 0.0
    percent_used: float = 0.0
    is_warning: bool = False
    is_critical: bool = False

    # Notification
    notification_emails: List[str] = Field(default_factory=list)
    notification_slack_webhook: Optional[str] = None
    last_alert_sent: Optional[datetime] = None
    alert_frequency_hours: int = 24  # Minimum hours between alerts

    # Filters
    resource_groups: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)

    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetAlertCreate(BaseModel):
    """Request to create a budget alert."""
    name: str
    provider: CloudProvider
    budget_amount: float
    currency: str = "USD"
    period: str = "monthly"
    warning_threshold: int = Field(default=80, ge=0, le=100)
    critical_threshold: int = Field(default=100, ge=0, le=150)
    notification_emails: List[str] = Field(default_factory=list)
    notification_slack_webhook: Optional[str] = None
    resource_groups: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


class BudgetAlertUpdate(BaseModel):
    """Request to update a budget alert."""
    name: Optional[str] = None
    budget_amount: Optional[float] = None
    warning_threshold: Optional[int] = Field(default=None, ge=0, le=100)
    critical_threshold: Optional[int] = Field(default=None, ge=0, le=150)
    notification_emails: Optional[List[str]] = None
    notification_slack_webhook: Optional[str] = None
    is_active: Optional[bool] = None


class CostForecast(BaseModel):
    """Cost forecast for upcoming period."""
    provider: CloudProvider
    forecast_period_start: date
    forecast_period_end: date
    forecasted_cost: float
    confidence_level: float = Field(ge=0, le=1)  # 0-1
    currency: str = "USD"

    # Breakdown
    by_service: Dict[str, float] = Field(default_factory=dict)

    # Comparison with budget
    budget_amount: Optional[float] = None
    forecast_vs_budget_percent: Optional[float] = None

    # Mock data indicator
    is_mock_data: bool = Field(default=False, description="True if this is demo/mock data")


class CostQueryRequest(BaseModel):
    """Request for cost data query."""
    provider: CloudProvider = CloudProvider.ALL
    start_date: date
    end_date: date
    granularity: TimeGranularity = TimeGranularity.DAILY
    group_by: List[str] = Field(default_factory=list)  # service, category, resource_group
    resource_groups: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


class CostDashboardData(BaseModel):
    """Aggregated cost data for dashboard."""
    azure_summary: Optional[CostSummary] = None
    aws_summary: Optional[CostSummary] = None
    combined_total: float = 0.0
    currency: str = "USD"

    # Mock data indicator (true if any provider uses mock data)
    is_mock_data: bool = Field(default=False, description="True if using demo/mock data")

    # Month-to-date
    mtd_cost: float = 0.0
    mtd_budget: Optional[float] = None
    mtd_percent_of_budget: Optional[float] = None

    # Comparisons
    cost_change_vs_last_month: Optional[float] = None
    cost_change_percent: Optional[float] = None

    # Top costs
    top_services: List[Dict[str, Any]] = Field(default_factory=list)
    top_resources: List[Dict[str, Any]] = Field(default_factory=list)

    # Trends
    cost_trend_30d: List[CostDataPoint] = Field(default_factory=list)

    # Alerts
    active_alerts: List[BudgetAlert] = Field(default_factory=list)
    triggered_alerts: List[BudgetAlert] = Field(default_factory=list)

    # Forecast
    current_month_forecast: Optional[CostForecast] = None

    # AI/ML specific costs (important for agentic platform)
    ai_ml_costs: Dict[str, float] = Field(default_factory=dict)
    ai_ml_total: float = 0.0


class CostAnomalyAlert(BaseModel):
    """Cost anomaly detection alert."""
    id: str
    provider: CloudProvider
    detected_at: datetime
    service_name: str
    expected_cost: float
    actual_cost: float
    deviation_percent: float
    severity: str  # low, medium, high, critical
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
