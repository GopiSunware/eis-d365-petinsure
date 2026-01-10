"""AWS Cost Explorer API integration.

Works with:
- Local: AWS credentials from environment or ~/.aws/credentials
- AWS: IAM Role with Cost Explorer permissions
"""

import logging
import os
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..models.costs import (
    CloudProvider,
    CostDataPoint,
    CostSummary,
    CostForecast,
    TimeGranularity,
)

logger = logging.getLogger(__name__)


class AWSCostService:
    """Service for AWS Cost Explorer API."""

    def __init__(self):
        self._client = None

        # Load config from environment
        self.access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.service_filter = os.getenv("AWS_SERVICE_FILTER", "")

    @property
    def is_configured(self) -> bool:
        """Check if AWS Cost Explorer is configured."""
        return bool(self.access_key_id and self.secret_access_key)

    @property
    def services(self) -> List[str]:
        """Parse AWS service filter."""
        if not self.service_filter:
            return []
        return [svc.strip() for svc in self.service_filter.split(",") if svc.strip()]

    def _get_client(self):
        """Get boto3 Cost Explorer client."""
        if self._client:
            return self._client

        if not self.is_configured:
            logger.info("AWS Cost not configured")
            return None

        try:
            import boto3
            self._client = boto3.client(
                "ce",
                region_name=self.region,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
            )
            logger.info("AWS Cost Explorer client initialized")
            return self._client
        except Exception as e:
            logger.error(f"Failed to create AWS Cost Explorer client: {e}")
            return None

    def _expand_service_names(self, short_names: List[str]) -> List[str]:
        """Expand short service names to full AWS service names."""
        service_map = {
            "bedrock": "Amazon Bedrock",
            "s3": "Amazon Simple Storage Service",
            "lambda": "AWS Lambda",
            "api gateway": "Amazon API Gateway",
            "cloudwatch": "AmazonCloudWatch",
            "dynamodb": "Amazon DynamoDB",
            "sagemaker": "Amazon SageMaker",
            "ec2": "Amazon Elastic Compute Cloud - Compute",
            "rds": "Amazon Relational Database Service",
            "ecs": "Amazon Elastic Container Service",
            "ecr": "Amazon EC2 Container Registry (ECR)",
            "sns": "Amazon Simple Notification Service",
            "sqs": "Amazon Simple Queue Service",
            "kinesis": "Amazon Kinesis",
            "athena": "Amazon Athena",
            "glue": "AWS Glue",
            "app runner": "AWS App Runner",
        }

        expanded = []
        for name in short_names:
            name_lower = name.lower().strip()
            if name_lower in service_map:
                expanded.append(service_map[name_lower])
            else:
                # Use as-is if not in map
                expanded.append(name)

        logger.info(f"AWS service filter expanded: {short_names} -> {expanded}")
        return expanded

    async def get_cost_summary(
        self,
        start_date: date,
        end_date: date,
        granularity: TimeGranularity = TimeGranularity.DAILY,
    ) -> CostSummary:
        """Get cost summary for a period."""
        client = self._get_client()
        if not client:
            return self._get_mock_summary(start_date, end_date, is_mock=True)

        try:
            # Build request
            request = {
                "TimePeriod": {
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                "Granularity": granularity.value.upper(),
                "Metrics": ["UnblendedCost"],
                "GroupBy": [
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                ],
            }

            # Add service filter if configured
            if self.services:
                request["Filter"] = {
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": self._expand_service_names(self.services),
                    }
                }

            response = client.get_cost_and_usage(**request)
            logger.info(f"AWS Cost Explorer returned {len(response.get('ResultsByTime', []))} time periods")
            return self._parse_cost_response(response, start_date, end_date)

        except Exception as e:
            logger.error(f"AWS Cost Explorer error: {e}")
            return self._get_mock_summary(start_date, end_date, is_mock=True)

    def _parse_cost_response(
        self,
        response: dict,
        start_date: date,
        end_date: date,
    ) -> CostSummary:
        """Parse AWS Cost Explorer API response."""
        total_cost = 0.0
        by_service: Dict[str, float] = {}
        daily_costs: List[CostDataPoint] = []

        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                service_name = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])

                total_cost += amount
                by_service[service_name] = by_service.get(service_name, 0) + amount

        # Sort by cost descending and round values
        by_service = {k: round(v, 2) for k, v in sorted(by_service.items(), key=lambda x: -x[1])}

        return CostSummary(
            provider=CloudProvider.AWS,
            period_start=start_date,
            period_end=end_date,
            total_cost=round(total_cost, 2),
            currency="USD",
            by_service=by_service,
            daily_costs=daily_costs,
            is_mock_data=False,
        )

    async def get_forecast(
        self,
        forecast_days: int = 30,
    ) -> CostForecast:
        """Get cost forecast for upcoming period."""
        client = self._get_client()
        if not client:
            return self._get_mock_forecast(forecast_days, is_mock=True)

        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=forecast_days)

            request = {
                "TimePeriod": {
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                "Metric": "UNBLENDED_COST",
                "Granularity": "MONTHLY",
            }

            # Add service filter if configured
            if self.services:
                request["Filter"] = {
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": self._expand_service_names(self.services),
                    }
                }

            response = client.get_cost_forecast(**request)
            forecasted_cost = float(response.get("Total", {}).get("Amount", 0))

            return CostForecast(
                provider=CloudProvider.AWS,
                forecast_period_start=start_date,
                forecast_period_end=end_date,
                forecasted_cost=round(forecasted_cost, 2),
                confidence_level=0.80,
                currency="USD",
                is_mock_data=False,
            )

        except Exception as e:
            logger.error(f"AWS forecast error: {e}")
            return self._get_mock_forecast(forecast_days, is_mock=True)

    def _get_mock_summary(self, start_date: date, end_date: date, is_mock: bool = True) -> CostSummary:
        """Generate mock cost data for development/demo."""
        days = (end_date - start_date).days + 1

        return CostSummary(
            provider=CloudProvider.AWS,
            period_start=start_date,
            period_end=end_date,
            total_cost=round(23.5 * days, 2),
            currency="USD",
            by_service={
                "Amazon Bedrock": round(12.0 * days, 2),
                "Amazon S3": round(4.0 * days, 2),
                "AWS Lambda": round(3.5 * days, 2),
                "Amazon API Gateway": round(2.0 * days, 2),
                "Amazon CloudWatch": round(1.5 * days, 2),
                "AWS App Runner": round(0.5 * days, 2),
            },
            cost_change_percent=5.2,
            is_mock_data=is_mock,
        )

    def _get_mock_forecast(self, forecast_days: int, is_mock: bool = True) -> CostForecast:
        """Generate mock forecast data."""
        return CostForecast(
            provider=CloudProvider.AWS,
            forecast_period_start=date.today(),
            forecast_period_end=date.today() + timedelta(days=forecast_days),
            forecasted_cost=round(23.5 * forecast_days, 2),
            confidence_level=0.80,
            currency="USD",
            by_service={
                "Amazon Bedrock": round(12.0 * forecast_days, 2),
                "Amazon S3": round(4.0 * forecast_days, 2),
                "Other": round(7.5 * forecast_days, 2),
            },
            is_mock_data=is_mock,
        )


# Singleton
_aws_cost_service: Optional[AWSCostService] = None


def get_aws_cost_service() -> AWSCostService:
    """Get AWS cost service singleton."""
    global _aws_cost_service
    if _aws_cost_service is None:
        _aws_cost_service = AWSCostService()
    return _aws_cost_service
