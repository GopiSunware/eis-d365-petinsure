"""Pydantic models for cost management APIs."""

from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class CloudProvider(str, Enum):
    """Cloud provider enumeration."""
    AZURE = "azure"
    AWS = "aws"
    ALL = "all"


class TimeGranularity(str, Enum):
    """Time granularity for cost queries."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class CostDataPoint(BaseModel):
    """Single cost data point."""
    date: date
    cost: float
    currency: str = "USD"


class CostSummary(BaseModel):
    """Cost summary for a cloud provider."""
    provider: CloudProvider
    period_start: date
    period_end: date
    total_cost: float
    currency: str = "USD"
    by_service: Dict[str, float] = {}
    by_resource_group: Dict[str, float] = {}
    daily_costs: List[CostDataPoint] = []
    cost_change_percent: Optional[float] = None
    is_mock_data: bool = True


class CostForecast(BaseModel):
    """Cost forecast for upcoming period."""
    provider: CloudProvider
    forecast_period_start: date
    forecast_period_end: date
    forecasted_cost: float
    confidence_level: float = 0.75
    currency: str = "USD"
    by_service: Dict[str, float] = {}
    is_mock_data: bool = True
