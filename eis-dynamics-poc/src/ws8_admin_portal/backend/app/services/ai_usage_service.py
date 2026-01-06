"""AI API usage tracking service.

Fetches AI/LLM usage metrics from:
- Azure OpenAI via Azure Monitor metrics
- AWS Bedrock via CloudWatch metrics
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import httpx

from ..config import settings
from ..models.ai_usage import (
    AIProvider,
    AIModel,
    AIUsageSummary,
    DocumentIntelligenceUsage,
    DatabaseUsage,
    PlatformUsageSummary,
    TOKEN_PRICING,
)

logger = logging.getLogger(__name__)


class AIUsageService:
    """Service for tracking AI API usage across providers."""

    def __init__(self):
        self._azure_token = None
        self._token_expiry = None

    async def _get_azure_token(self) -> Optional[str]:
        """Get Azure AD access token for Azure Monitor."""
        if self._azure_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._azure_token

        if not settings.azure_cost_configured:
            return None

        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            token = credential.get_token("https://management.azure.com/.default")
            self._azure_token = token.token
            self._token_expiry = datetime.utcnow() + timedelta(minutes=55)
            return self._azure_token
        except Exception as e:
            logger.error(f"Failed to get Azure token: {e}")
            return None

    async def get_azure_openai_usage(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """Get Azure OpenAI usage from Azure Monitor metrics."""
        token = await self._get_azure_token()
        if not token:
            return self._get_empty_usage(AIProvider.AZURE_OPENAI)

        try:
            # Azure Monitor Metrics API for Azure OpenAI
            # Metrics: TokensUsed, Requests, etc.
            subscription_id = settings.AZURE_SUBSCRIPTION_ID

            # List Azure OpenAI resources
            url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/accounts?api-version=2023-05-01"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(f"Failed to list Azure OpenAI resources: {response.status_code}")
                    return self._get_empty_usage(AIProvider.AZURE_OPENAI)

                resources = response.json().get("value", [])
                openai_resources = [
                    r for r in resources
                    if r.get("kind", "").lower() in ["openai", "cognitiveservices"]
                ]

                if not openai_resources:
                    logger.info("No Azure OpenAI resources found")
                    return self._get_empty_usage(AIProvider.AZURE_OPENAI)

                # Get metrics for each resource
                total_tokens = 0
                total_requests = 0
                by_model = {}

                for resource in openai_resources:
                    resource_id = resource["id"]
                    metrics = await self._get_resource_metrics(
                        token, resource_id, start_date, end_date
                    )
                    total_tokens += metrics.get("tokens", 0)
                    total_requests += metrics.get("requests", 0)

                    for model, data in metrics.get("by_model", {}).items():
                        if model not in by_model:
                            by_model[model] = {"tokens": 0, "requests": 0}
                        by_model[model]["tokens"] += data.get("tokens", 0)
                        by_model[model]["requests"] += data.get("requests", 0)

                return {
                    "provider": AIProvider.AZURE_OPENAI,
                    "total_tokens": total_tokens,
                    "total_requests": total_requests,
                    "by_model": by_model,
                    "is_mock": False,
                }

        except Exception as e:
            logger.error(f"Error fetching Azure OpenAI usage: {e}")
            return self._get_empty_usage(AIProvider.AZURE_OPENAI)

    async def _get_resource_metrics(
        self,
        token: str,
        resource_id: str,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """Get metrics for a specific Azure resource."""
        try:
            # Azure Monitor metrics endpoint
            timespan = f"{start_date.isoformat()}T00:00:00Z/{end_date.isoformat()}T23:59:59Z"
            url = (
                f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metrics"
                f"?api-version=2023-10-01"
                f"&timespan={timespan}"
                f"&metricnames=TokenTransaction,ProcessedPromptTokens,GeneratedTokens"
                f"&aggregation=Total"
            )

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.warning(f"Failed to get metrics for {resource_id}: {response.status_code}")
                    return {"tokens": 0, "requests": 0, "by_model": {}}

                data = response.json()
                tokens = 0
                requests = 0

                for metric in data.get("value", []):
                    metric_name = metric.get("name", {}).get("value", "")
                    for timeseries in metric.get("timeseries", []):
                        for point in timeseries.get("data", []):
                            if metric_name in ["TokenTransaction", "ProcessedPromptTokens", "GeneratedTokens"]:
                                tokens += point.get("total", 0) or 0

                return {"tokens": int(tokens), "requests": requests, "by_model": {}}

        except Exception as e:
            logger.error(f"Error getting resource metrics: {e}")
            return {"tokens": 0, "requests": 0, "by_model": {}}

    async def get_aws_bedrock_usage(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """Get AWS Bedrock usage from CloudWatch metrics."""
        if not settings.aws_cost_configured:
            return self._get_mock_aws_bedrock_usage(start_date, end_date)

        try:
            import boto3

            cloudwatch = boto3.client(
                "cloudwatch",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            # Get Bedrock metrics
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Bedrock",
                MetricName="InputTokenCount",
                StartTime=datetime.combine(start_date, datetime.min.time()),
                EndTime=datetime.combine(end_date, datetime.max.time()),
                Period=86400,  # Daily
                Statistics=["Sum"],
            )

            input_tokens = sum(dp.get("Sum", 0) for dp in response.get("Datapoints", []))

            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Bedrock",
                MetricName="OutputTokenCount",
                StartTime=datetime.combine(start_date, datetime.min.time()),
                EndTime=datetime.combine(end_date, datetime.max.time()),
                Period=86400,
                Statistics=["Sum"],
            )

            output_tokens = sum(dp.get("Sum", 0) for dp in response.get("Datapoints", []))

            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Bedrock",
                MetricName="Invocations",
                StartTime=datetime.combine(start_date, datetime.min.time()),
                EndTime=datetime.combine(end_date, datetime.max.time()),
                Period=86400,
                Statistics=["Sum"],
            )

            requests = sum(dp.get("Sum", 0) for dp in response.get("Datapoints", []))

            return {
                "provider": AIProvider.AWS_BEDROCK,
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "total_tokens": int(input_tokens + output_tokens),
                "total_requests": int(requests),
                "is_mock": False,
            }

        except Exception as e:
            logger.error(f"Error fetching AWS Bedrock usage: {e}")
            return self._get_empty_usage(AIProvider.AWS_BEDROCK)

    async def get_ai_usage_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> AIUsageSummary:
        """Get combined AI usage summary."""
        azure_usage = await self.get_azure_openai_usage(start_date, end_date)
        aws_usage = await self.get_aws_bedrock_usage(start_date, end_date)

        is_mock = azure_usage.get("is_mock", True) and aws_usage.get("is_mock", True)

        # Calculate totals
        total_input = azure_usage.get("input_tokens", 0) + aws_usage.get("input_tokens", 0)
        total_output = azure_usage.get("output_tokens", 0) + aws_usage.get("output_tokens", 0)

        # For Azure, we might only have total tokens
        if "total_tokens" in azure_usage and "input_tokens" not in azure_usage:
            total_input += azure_usage.get("total_tokens", 0) // 2  # Estimate
            total_output += azure_usage.get("total_tokens", 0) // 2

        total_tokens = total_input + total_output
        total_requests = azure_usage.get("total_requests", 0) + aws_usage.get("total_requests", 0)

        # Estimate cost (using GPT-4o-mini as average)
        avg_input_price = 0.00015  # per 1K tokens
        avg_output_price = 0.0006
        estimated_cost = (total_input / 1000 * avg_input_price) + (total_output / 1000 * avg_output_price)

        # Build breakdown
        by_provider = {}
        if azure_usage.get("total_tokens", 0) > 0 or azure_usage.get("input_tokens", 0) > 0:
            azure_tokens = azure_usage.get("total_tokens", 0) or (azure_usage.get("input_tokens", 0) + azure_usage.get("output_tokens", 0))
            by_provider["Azure OpenAI"] = {
                "tokens": azure_tokens,
                "requests": azure_usage.get("total_requests", 0),
                "cost": round(azure_tokens / 1000 * 0.002, 2),  # Estimate
            }

        if aws_usage.get("total_tokens", 0) > 0:
            by_provider["AWS Bedrock"] = {
                "tokens": aws_usage.get("total_tokens", 0),
                "requests": aws_usage.get("total_requests", 0),
                "cost": round(aws_usage.get("total_tokens", 0) / 1000 * 0.003, 2),  # Estimate
            }

        return AIUsageSummary(
            period_start=start_date,
            period_end=end_date,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_cost=round(estimated_cost, 2),
            total_requests=total_requests,
            by_provider=by_provider,
            by_model=azure_usage.get("by_model", {}),
            avg_tokens_per_request=round(total_tokens / max(total_requests, 1), 1),
            avg_cost_per_request=round(estimated_cost / max(total_requests, 1), 4),
            is_mock_data=is_mock,
        )

    async def get_platform_usage_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> PlatformUsageSummary:
        """Get complete platform usage including all cost centers.

        Note: Only AI usage is currently tracked. Document Intelligence and
        Database usage will be added when those services are integrated.
        """
        ai_usage = await self.get_ai_usage_summary(start_date, end_date)

        # Build cost breakdown with only real data
        # AI usage cost comes from the ai_usage_summary
        cost_breakdown = {}

        if ai_usage.total_cost > 0:
            cost_breakdown["AI/LLM APIs"] = ai_usage.total_cost

        return PlatformUsageSummary(
            period_start=start_date,
            period_end=end_date,
            ai_usage=ai_usage,
            document_usage=None,  # Not tracked yet
            database_usage=None,  # Not tracked yet
            cost_breakdown=cost_breakdown,
            total_platform_cost=ai_usage.total_cost,
            is_mock_data=False,  # No mock data returned
        )

    def _get_empty_usage(self, provider: AIProvider) -> Dict:
        """Return empty usage data when no real data is available."""
        return {
            "provider": provider,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_requests": 0,
            "by_model": {},
            "is_mock": False,
        }


# Singleton
_ai_usage_service: Optional[AIUsageService] = None


def get_ai_usage_service() -> AIUsageService:
    """Get AI usage service singleton."""
    global _ai_usage_service
    if _ai_usage_service is None:
        _ai_usage_service = AIUsageService()
    return _ai_usage_service
