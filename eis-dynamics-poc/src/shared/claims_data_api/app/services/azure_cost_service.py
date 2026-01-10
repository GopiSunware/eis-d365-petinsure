"""Azure Cost Management API integration.

Works with:
- Local: `az login` (DefaultAzureCredential picks up CLI credentials)
- Azure: Managed Identity (DefaultAzureCredential auto-detects)
- AWS: Service principal via environment variables
"""

import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import httpx

from ..models.costs import (
    CloudProvider,
    CostDataPoint,
    CostSummary,
    CostForecast,
    TimeGranularity,
)

logger = logging.getLogger(__name__)


class AzureCostService:
    """Service for Azure Cost Management API."""

    COST_MANAGEMENT_API = "https://management.azure.com"
    API_VERSION = "2023-11-01"

    def __init__(self):
        self._credential = None
        self._access_token = None
        self._token_expiry = None

        # Load config from environment
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "")
        self.cost_scope = os.getenv("AZURE_COST_MANAGEMENT_SCOPE", "")
        self.resource_group_filter = os.getenv("AZURE_RESOURCE_GROUP_FILTER", "")

    @property
    def is_configured(self) -> bool:
        """Check if Azure Cost Management is configured."""
        return bool(self.subscription_id)

    @property
    def resource_groups(self) -> List[str]:
        """Parse Azure resource group filter patterns."""
        if not self.resource_group_filter:
            return []
        return [rg.strip() for rg in self.resource_group_filter.split(",") if rg.strip()]

    def _get_credential(self):
        """Get Azure credential (lazy init)."""
        if self._credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                self._credential = DefaultAzureCredential()
                logger.info("Azure DefaultAzureCredential initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure credential: {e}")
                return None
        return self._credential

    async def _get_access_token(self) -> Optional[str]:
        """Get Azure AD access token."""
        if self._access_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._access_token

        credential = self._get_credential()
        if not credential:
            return None

        try:
            token = credential.get_token("https://management.azure.com/.default")
            self._access_token = token.token
            self._token_expiry = datetime.utcnow() + timedelta(minutes=55)
            logger.info("Azure access token obtained successfully")
            return self._access_token
        except Exception as e:
            logger.error(f"Failed to get Azure access token: {e}")
            return None

    def _get_scope(self) -> str:
        """Get the cost management scope."""
        if self.cost_scope:
            return self.cost_scope
        return f"/subscriptions/{self.subscription_id}"

    async def _get_resource_groups(self) -> List[str]:
        """Get resource groups matching the filter patterns."""
        if not self.resource_groups:
            return []

        token = await self._get_access_token()
        if not token:
            return []

        try:
            url = f"{self.COST_MANAGEMENT_API}/subscriptions/{self.subscription_id}/resourcegroups?api-version=2021-04-01"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(f"Failed to get resource groups: {response.status_code}")
                    return []

                data = response.json()
                all_rgs = [rg["name"] for rg in data.get("value", [])]

                # Filter by patterns
                patterns = self.resource_groups
                filtered = []
                for rg in all_rgs:
                    rg_lower = rg.lower()
                    for pattern in patterns:
                        if pattern.lower() in rg_lower:
                            filtered.append(rg)
                            break

                logger.info(f"Found {len(filtered)} resource groups matching filter: {filtered}")
                return filtered

        except Exception as e:
            logger.error(f"Error getting resource groups: {e}")
            return []

    async def get_cost_summary(
        self,
        start_date: date,
        end_date: date,
        granularity: TimeGranularity = TimeGranularity.DAILY,
    ) -> CostSummary:
        """Get cost summary for a period."""
        if not self.is_configured:
            logger.info("Azure Cost not configured, returning mock data")
            return self._get_mock_summary(start_date, end_date, is_mock=True)

        token = await self._get_access_token()
        if not token:
            logger.warning("Could not get Azure token, returning mock data")
            return self._get_mock_summary(start_date, end_date, is_mock=True)

        try:
            # Get filtered resource groups
            resource_groups = await self._get_resource_groups()

            scope = self._get_scope()
            url = f"{self.COST_MANAGEMENT_API}{scope}/providers/Microsoft.CostManagement/query?api-version={self.API_VERSION}"

            # Build query
            query = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat(),
                },
                "dataset": {
                    "granularity": granularity.value.capitalize(),
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {"type": "Dimension", "name": "ServiceName"},
                        {"type": "Dimension", "name": "ResourceGroup"},
                    ]
                }
            }

            # Add resource group filter if configured
            if resource_groups:
                query["dataset"]["filter"] = {
                    "Dimensions": {
                        "Name": "ResourceGroup",
                        "Operator": "In",
                        "Values": resource_groups
                    }
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=query,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    logger.error(f"Azure Cost API error: {response.status_code} - {response.text}")
                    return self._get_mock_summary(start_date, end_date, is_mock=True)

                data = response.json()
                logger.info(f"Azure Cost API returned {len(data.get('properties', {}).get('rows', []))} rows")

            return self._parse_cost_response(data, start_date, end_date)

        except Exception as e:
            logger.error(f"Azure Cost API error: {e}")
            return self._get_mock_summary(start_date, end_date, is_mock=True)

    def _parse_cost_response(
        self,
        data: dict,
        start_date: date,
        end_date: date,
    ) -> CostSummary:
        """Parse Azure Cost Management API response."""
        rows = data.get("properties", {}).get("rows", [])
        columns = data.get("properties", {}).get("columns", [])

        # Build column index map
        col_map = {col["name"]: i for i, col in enumerate(columns)}

        total_cost = 0.0
        by_service: Dict[str, float] = {}
        by_resource_group: Dict[str, float] = {}
        daily_costs: List[CostDataPoint] = []

        for row in rows:
            cost = float(row[col_map.get("Cost", 0)] or 0.0)
            service = row[col_map.get("ServiceName", 1)] if "ServiceName" in col_map else "Unknown"
            rg = row[col_map.get("ResourceGroup", 2)] if "ResourceGroup" in col_map else "Unknown"

            total_cost += cost
            by_service[service] = by_service.get(service, 0) + cost
            by_resource_group[rg] = by_resource_group.get(rg, 0) + cost

        # Sort by cost descending and round values
        by_service = {k: round(v, 2) for k, v in sorted(by_service.items(), key=lambda x: -x[1])}
        by_resource_group = {k: round(v, 2) for k, v in sorted(by_resource_group.items(), key=lambda x: -x[1])}

        return CostSummary(
            provider=CloudProvider.AZURE,
            period_start=start_date,
            period_end=end_date,
            total_cost=round(total_cost, 2),
            currency="USD",
            by_service=by_service,
            by_resource_group=by_resource_group,
            daily_costs=daily_costs,
            is_mock_data=False,
        )

    async def get_forecast(
        self,
        forecast_days: int = 30,
    ) -> CostForecast:
        """Get cost forecast for upcoming period."""
        if not self.is_configured:
            return self._get_mock_forecast(forecast_days, is_mock=True)

        try:
            # Get last 30 days to estimate
            end_date = date.today() - timedelta(days=1)
            start_date = end_date - timedelta(days=30)

            summary = await self.get_cost_summary(start_date, end_date)
            if summary.is_mock_data:
                return self._get_mock_forecast(forecast_days, is_mock=True)

            daily_avg = summary.total_cost / 30

            return CostForecast(
                provider=CloudProvider.AZURE,
                forecast_period_start=date.today(),
                forecast_period_end=date.today() + timedelta(days=forecast_days),
                forecasted_cost=round(daily_avg * forecast_days, 2),
                confidence_level=0.75,
                currency="USD",
                is_mock_data=False,
            )

        except Exception as e:
            logger.error(f"Azure forecast error: {e}")
            return self._get_mock_forecast(forecast_days, is_mock=True)

    def _get_mock_summary(self, start_date: date, end_date: date, is_mock: bool = True) -> CostSummary:
        """Generate mock cost data for development/demo."""
        days = (end_date - start_date).days + 1

        return CostSummary(
            provider=CloudProvider.AZURE,
            period_start=start_date,
            period_end=end_date,
            total_cost=round(47.5 * days, 2),
            currency="USD",
            by_service={
                "Azure OpenAI": round(25.0 * days, 2),
                "Cosmos DB": round(12.0 * days, 2),
                "App Service": round(5.5 * days, 2),
                "Storage": round(3.0 * days, 2),
                "Key Vault": round(1.0 * days, 2),
                "Service Bus": round(1.0 * days, 2),
            },
            by_resource_group={
                "rg-eis-dynamics-dev": round(35.0 * days, 2),
                "rg-eis-shared": round(12.5 * days, 2),
            },
            cost_change_percent=8.5,
            is_mock_data=is_mock,
        )

    def _get_mock_forecast(self, forecast_days: int, is_mock: bool = True) -> CostForecast:
        """Generate mock forecast data."""
        return CostForecast(
            provider=CloudProvider.AZURE,
            forecast_period_start=date.today(),
            forecast_period_end=date.today() + timedelta(days=forecast_days),
            forecasted_cost=round(47.5 * forecast_days, 2),
            confidence_level=0.75,
            currency="USD",
            by_service={
                "Azure OpenAI": round(25.0 * forecast_days, 2),
                "Cosmos DB": round(12.0 * forecast_days, 2),
                "Other": round(10.5 * forecast_days, 2),
            },
            is_mock_data=is_mock,
        )


# Singleton
_azure_cost_service: Optional[AzureCostService] = None


def get_azure_cost_service() -> AzureCostService:
    """Get Azure cost service singleton."""
    global _azure_cost_service
    if _azure_cost_service is None:
        _azure_cost_service = AzureCostService()
    return _azure_cost_service
