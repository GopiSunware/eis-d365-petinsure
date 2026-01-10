"""
Data Source Service - Toggle between Demo Data and Azure Gold Layer.

This service manages the data source configuration, allowing seamless switching
between local demo data (synthetic) and Azure ADLS Gold layer (production-like).

Features:
- Toggle data source at runtime
- Automatic fallback to demo data if Azure fails
- Health monitoring for both data sources
- API endpoints for status and configuration
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data_loader import get_data_store
from app.services.azure_data_service import (
    get_azure_service,
    GoldLayerData,
    AzureDataService
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

class DataSourceType(str, Enum):
    """Available data sources."""
    DEMO = "demo"           # Local synthetic data
    AZURE = "azure"         # Azure ADLS Gold layer
    HYBRID = "hybrid"       # Try Azure first, fallback to demo


class DataSourceConfig:
    """Global data source configuration."""

    def __init__(self):
        # Default from environment or "demo"
        default_source = os.getenv("USE_AZURE_DATA", "false").lower()
        if default_source in ("true", "1", "yes", "azure"):
            self._source = DataSourceType.AZURE
        elif default_source == "hybrid":
            self._source = DataSourceType.HYBRID
        else:
            self._source = DataSourceType.DEMO

        self._last_toggle = datetime.now(timezone.utc)
        self._toggle_count = 0

    @property
    def source(self) -> DataSourceType:
        return self._source

    @source.setter
    def source(self, value: DataSourceType):
        self._source = value
        self._last_toggle = datetime.now(timezone.utc)
        self._toggle_count += 1
        logger.info(f"Data source changed to: {value}")

    @property
    def use_azure(self) -> bool:
        return self._source in (DataSourceType.AZURE, DataSourceType.HYBRID)

    @property
    def use_demo(self) -> bool:
        return self._source in (DataSourceType.DEMO, DataSourceType.HYBRID)

    def status(self) -> Dict:
        return {
            "current_source": self._source.value,
            "last_toggle": self._last_toggle.isoformat(),
            "toggle_count": self._toggle_count,
            "use_azure": self.use_azure,
            "use_demo": self.use_demo,
        }


# Global config instance
_config = DataSourceConfig()


def get_data_source_config() -> DataSourceConfig:
    """Get the global data source configuration."""
    return _config


# =============================================================================
# DATA PROVIDER - UNIFIED ACCESS
# =============================================================================

class DataProvider:
    """
    Unified data provider that abstracts the data source.
    Uses the configured source (demo, azure, or hybrid) to fetch data.
    """

    def __init__(self):
        self.config = _config
        self.azure_service = get_azure_service()

    def get_customers(self, limit: int = 100) -> Dict:
        """
        Get customer 360 data from the configured source.

        Returns:
            Dict with customers list and metadata
        """
        source_used = "demo"
        azure_data = None  # Initialize to avoid NameError

        if self.config.use_azure:
            # Try Azure first
            azure_data = self.azure_service.read_parquet_table("customer_360")
            if azure_data:
                source_used = "azure"
                # Transform to API format
                customers = [
                    GoldLayerData.transform_customer_360(record)
                    for record in azure_data[:limit]
                ]
                return {
                    "customers": customers,
                    "count": len(customers),
                    "total": len(azure_data),
                    "source": source_used,
                    "description": "Customer 360 from Azure Gold Layer"
                }

        # Fallback to demo data
        if self.config.use_demo or not azure_data:
            source_used = "demo"
            # Import here to avoid circular dependency
            from app.services.insights_service import (
                DEMO_CUSTOMERS,
                calculate_customer_metrics_fast,
                _build_indexes
            )
            _build_indexes()

            store = get_data_store()
            customers = store.get_customers()
            all_customers = DEMO_CUSTOMERS + customers

            customer_360s = [
                calculate_customer_metrics_fast(c)
                for c in all_customers[:limit]
            ]

            return {
                "customers": customer_360s,
                "count": len(customer_360s),
                "total": len(all_customers),
                "source": source_used,
                "description": "Customer 360 from demo synthetic data"
            }

    def get_claims(self, limit: int = 100, status: Optional[str] = None) -> Dict:
        """
        Get claims analytics from the configured source.

        Returns:
            Dict with claims list and metadata
        """
        source_used = "demo"
        azure_data = None  # Initialize to avoid NameError

        if self.config.use_azure:
            azure_data = self.azure_service.read_parquet_table("claims_analytics")
            if azure_data:
                source_used = "azure"
                claims = [
                    GoldLayerData.transform_claims_analytics(record)
                    for record in azure_data
                ]

                # Apply filter if provided
                if status:
                    claims = [c for c in claims if c.get("status") == status]

                return {
                    "claims": claims[:limit],
                    "count": len(claims[:limit]),
                    "total": len(claims),
                    "source": source_used,
                    "description": "Claims analytics from Azure Gold Layer"
                }

        # Fallback to demo data (Azure failed or not configured)
        store = get_data_store()
        claims = store.get_claims()

        if status:
            claims = [c for c in claims if c.get("status") == status]

        return {
            "claims": claims[:limit],
            "count": len(claims[:limit]),
            "total": len(claims),
            "source": "demo",
            "description": "Claims from demo synthetic data"
        }

    def get_kpis(self, limit: int = 12) -> Dict:
        """
        Get monthly KPIs from the configured source.

        Returns:
            Dict with KPIs list and metadata
        """
        source_used = "demo"

        if self.config.use_azure:
            azure_data = self.azure_service.read_parquet_table("monthly_kpis")
            if azure_data:
                source_used = "azure"
                kpis = [
                    GoldLayerData.transform_monthly_kpi(record)
                    for record in azure_data[:limit]
                ]
                return {
                    "kpis": kpis,
                    "source": source_used,
                    "description": "Monthly KPIs from Azure Gold Layer"
                }

        # Fallback to demo data (Azure failed or not configured)
        from app.services.insights_service import generate_monthly_kpis
        store = get_data_store()
        claims = store.get_claims()
        customers = store.get_customers()

        kpis = generate_monthly_kpis(claims, customers, limit=limit)
        return {
            "kpis": kpis,
            "source": "demo",
            "description": "Monthly KPIs from demo synthetic data"
        }

    def get_risk_scores(self, limit: int = 100) -> Dict:
        """
        Get customer risk scores from the configured source.

        Returns:
            Dict with risk scores and metadata
        """
        source_used = "demo"

        if self.config.use_azure:
            azure_data = self.azure_service.read_parquet_table("risk_scoring")
            if azure_data:
                source_used = "azure"
                risks = [
                    GoldLayerData.transform_risk_score(record)
                    for record in azure_data[:limit]
                ]

                # Calculate distribution
                distribution = {}
                for r in risks:
                    cat = r.get("risk_category", "Unknown")
                    distribution[cat] = distribution.get(cat, 0) + 1

                return {
                    "risk_scores": risks,
                    "distribution": distribution,
                    "count": len(risks),
                    "source": source_used,
                    "description": "Risk scores from Azure Gold Layer"
                }

        # Fallback to demo data (Azure failed or not configured)
        from app.services.insights_service import (
            calculate_customer_metrics_fast,
            _build_indexes
        )
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

        distribution = {}
        for r in risks:
            cat = r.get("risk_category", "Unknown")
            distribution[cat] = distribution.get(cat, 0) + 1

        return {
            "risk_scores": risks,
            "distribution": distribution,
            "count": len(risks),
            "source": "demo",
            "description": "Risk scores from demo synthetic data"
        }

    def get_providers(self, limit: int = 50) -> Dict:
        """
        Get provider performance from the configured source.

        Returns:
            Dict with providers and metadata
        """
        source_used = "demo"

        if self.config.use_azure:
            azure_data = self.azure_service.read_parquet_table("provider_performance")
            if azure_data:
                source_used = "azure"
                providers = [
                    GoldLayerData.transform_provider_performance(record)
                    for record in azure_data[:limit]
                ]
                return {
                    "providers": providers,
                    "count": len(providers),
                    "source": source_used,
                    "description": "Provider performance from Azure Gold Layer"
                }

        # Fallback to demo - use existing insights_service function
        # This would normally call insights_service.get_providers()
        return {
            "providers": [],
            "count": 0,
            "source": "demo",
            "description": "Provider performance from demo (not implemented in fallback)"
        }


# Global data provider instance
_data_provider: Optional[DataProvider] = None


def get_data_provider() -> DataProvider:
    """Get the global data provider instance."""
    global _data_provider
    if _data_provider is None:
        _data_provider = DataProvider()
    return _data_provider


# =============================================================================
# API ENDPOINTS
# =============================================================================

class DataSourceToggleRequest(BaseModel):
    """Request model for toggling data source."""
    source: DataSourceType


class CacheInvalidateRequest(BaseModel):
    """Request model for cache invalidation."""
    table: Optional[str] = None  # None means invalidate all


@router.get("/status")
async def get_data_source_status():
    """
    Get current data source status and health.

    Returns configuration, Azure connectivity, and cache statistics.
    """
    config = get_data_source_config()
    azure_service = get_azure_service()
    provider = get_data_provider()

    return {
        "configuration": config.status(),
        "azure": azure_service.health_check(),
        "cache": azure_service.get_cache_stats(),
        "available_tables": azure_service.list_tables(),
        "demo_data": {
            "available": True,
            "description": "Synthetic data always available as fallback"
        }
    }


@router.put("/toggle")
async def toggle_data_source(request: DataSourceToggleRequest):
    """
    Toggle the data source between demo and Azure.

    Args:
        request: Contains the desired data source type

    Returns:
        New configuration status
    """
    config = get_data_source_config()
    azure_service = get_azure_service()

    # If switching to Azure, check if it's available
    if request.source in (DataSourceType.AZURE, DataSourceType.HYBRID):
        health = azure_service.health_check()
        if not health["is_available"]:
            # Allow hybrid (will fallback to demo) but warn for pure Azure
            if request.source == DataSourceType.AZURE:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "message": "Azure is not available. Use 'hybrid' mode for automatic fallback.",
                        "health": health
                    }
                )

    # Update configuration
    config.source = request.source

    return {
        "message": f"Data source changed to {request.source.value}",
        "configuration": config.status(),
        "azure_health": azure_service.health_check()
    }


@router.post("/cache/invalidate")
async def invalidate_cache(request: CacheInvalidateRequest):
    """
    Invalidate cached Azure data.

    Args:
        request: Optional table name to invalidate (None for all)

    Returns:
        Cache invalidation status
    """
    azure_service = get_azure_service()
    result = azure_service.invalidate_cache(request.table)

    return {
        "message": "Cache invalidated",
        "invalidated": result["invalidated"],
        "cache_stats": azure_service.get_cache_stats()
    }


@router.post("/cache/refresh")
async def refresh_cache():
    """
    Force refresh all Azure data cache.

    Invalidates cache and pre-loads data from Azure.

    Returns:
        Refresh status for each table
    """
    azure_service = get_azure_service()

    # Clear cache
    azure_service.invalidate_cache()

    # Pre-load each table
    results = {}
    for table_name in azure_service.list_tables():
        data = azure_service.read_parquet_table(table_name, use_cache=False)
        results[table_name] = {
            "success": data is not None,
            "record_count": len(data) if data else 0
        }

    return {
        "message": "Cache refresh complete",
        "tables": results,
        "cache_stats": azure_service.get_cache_stats()
    }


@router.get("/test")
async def test_data_sources():
    """
    Test both data sources and return sample data.

    Useful for verifying connectivity and data format.
    """
    provider = get_data_provider()
    azure_service = get_azure_service()

    results = {
        "azure": {
            "health": azure_service.health_check(),
            "sample_data": {}
        },
        "demo": {
            "available": True,
            "sample_data": {}
        }
    }

    # Try to get sample from Azure
    if azure_service.is_available:
        for table in ["customer_360", "monthly_kpis"]:
            data = azure_service.read_parquet_table(table)
            if data:
                results["azure"]["sample_data"][table] = {
                    "count": len(data),
                    "sample": data[0] if data else None
                }

    # Get sample from demo
    store = get_data_store()
    results["demo"]["sample_data"]["customers"] = {
        "count": len(store.get_customers()),
        "sample": store.get_customers()[0] if store.get_customers() else None
    }
    results["demo"]["sample_data"]["claims"] = {
        "count": len(store.get_claims()),
        "sample": store.get_claims()[0] if store.get_claims() else None
    }

    return results
