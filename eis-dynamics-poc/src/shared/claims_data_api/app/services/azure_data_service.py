"""
Azure Data Service - Connect to Azure ADLS Gen2 Gold Layer.

This service provides access to the Azure medallion architecture Gold layer,
allowing the AWS-hosted Claims Data API to read production data from Azure.

Features:
- Read Parquet/Delta files from ADLS Gen2
- Caching with configurable TTL
- Graceful fallback to demo data on errors
- Connection health monitoring
"""

import os
import io
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from functools import lru_cache
import json

logger = logging.getLogger(__name__)

# Try to import Azure SDK - graceful fallback if not available
try:
    from azure.storage.filedatalake import DataLakeServiceClient
    from azure.core.exceptions import AzureError
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    logger.warning("Azure SDK not installed. Install with: pip install azure-storage-file-datalake")

# Try to import pyarrow for Parquet reading
try:
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    logger.warning("PyArrow not installed. Install with: pip install pyarrow")


# =============================================================================
# CONFIGURATION
# =============================================================================

class AzureConfig:
    """Azure ADLS Gen2 configuration."""

    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "petinsud7i43")
        self.sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")  # None if not set
        self.gold_container = os.getenv("AZURE_GOLD_CONTAINER", "gold")
        self.cache_ttl = int(os.getenv("DATA_CACHE_TTL", "300"))  # 5 minutes default

        # Export paths within Gold container
        self.export_paths = {
            "customer_360": "exports/customer_360",
            "claims_analytics": "exports/claims_analytics",
            "monthly_kpis": "exports/monthly_kpis",
            "risk_scoring": "exports/risk_scoring",
            "provider_performance": "exports/provider_performance",
            "cross_sell": "exports/cross_sell_recommendations",
        }

    @property
    def account_url(self) -> str:
        return f"https://{self.storage_account}.dfs.core.windows.net"

    @property
    def is_configured(self) -> bool:
        """Check if Azure is properly configured."""
        return bool(self.storage_account and self.sas_token)


# Global config instance
_config = AzureConfig()


# =============================================================================
# CACHE IMPLEMENTATION
# =============================================================================

class DataCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict] = {}
        self._default_ttl = default_ttl
        self._lock = threading.RLock()  # Thread-safe reentrant lock

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if datetime.now(timezone.utc) > entry["expires_at"]:
                del self._cache[key]
                return None

            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl or self._default_ttl)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }

    def invalidate(self, key: str) -> None:
        """Remove item from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            now = datetime.now(timezone.utc)
            valid_entries = {k: v for k, v in self._cache.items() if now < v["expires_at"]}
            return {
                "total_entries": len(self._cache),
                "valid_entries": len(valid_entries),
                "keys": list(valid_entries.keys())
            }


# Global cache instance
_cache = DataCache(default_ttl=_config.cache_ttl)


# =============================================================================
# AZURE ADLS CLIENT
# =============================================================================

class AzureDataService:
    """Service for reading data from Azure ADLS Gen2 Gold layer."""

    def __init__(self, config: Optional[AzureConfig] = None):
        self.config = config or _config
        self._client: Optional[DataLakeServiceClient] = None
        self._last_error: Optional[str] = None
        self._last_successful_read: Optional[datetime] = None
        self._connection_failures = 0
        self._max_failures_before_circuit_break = 3
        self._circuit_break_until: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Check if Azure service is available."""
        if not AZURE_SDK_AVAILABLE:
            return False
        if not self.config.is_configured:
            return False
        if self._circuit_break_until and datetime.now(timezone.utc) < self._circuit_break_until:
            return False
        return True

    def _get_client(self) -> Optional[DataLakeServiceClient]:
        """Get or create ADLS client."""
        if not self.is_available:
            return None

        if self._client is None:
            try:
                self._client = DataLakeServiceClient(
                    account_url=self.config.account_url,
                    credential=self.config.sas_token
                )
            except Exception as e:
                logger.error(f"Failed to create Azure client: {e}")
                self._record_failure(str(e))
                return None

        return self._client

    def _record_failure(self, error: str) -> None:
        """Record a connection failure."""
        self._last_error = error
        self._connection_failures += 1

        if self._connection_failures >= self._max_failures_before_circuit_break:
            # Circuit breaker: stop trying for 5 minutes
            self._circuit_break_until = datetime.now(timezone.utc) + timedelta(minutes=5)
            logger.warning(f"Azure circuit breaker activated until {self._circuit_break_until}")

    def _record_success(self) -> None:
        """Record a successful read."""
        self._last_successful_read = datetime.now(timezone.utc)
        self._connection_failures = 0
        self._circuit_break_until = None
        self._last_error = None

    def health_check(self) -> Dict:
        """Check Azure connectivity health."""
        return {
            "is_available": self.is_available,
            "sdk_installed": AZURE_SDK_AVAILABLE,
            "pyarrow_installed": PYARROW_AVAILABLE,
            "is_configured": self.config.is_configured,
            "storage_account": self.config.storage_account,
            "last_successful_read": self._last_successful_read.isoformat() if self._last_successful_read else None,
            "last_error": self._last_error,
            "connection_failures": self._connection_failures,
            "circuit_breaker_active": self._circuit_break_until is not None and datetime.now(timezone.utc) < self._circuit_break_until,
            "circuit_breaker_until": self._circuit_break_until.isoformat() if self._circuit_break_until else None,
        }

    def read_parquet_table(self, table_name: str, use_cache: bool = True) -> Optional[List[Dict]]:
        """
        Read a Parquet table from Azure ADLS Gold layer.

        Args:
            table_name: Name of the table (e.g., "customer_360")
            use_cache: Whether to use cached data if available

        Returns:
            List of records as dictionaries, or None on error
        """
        # Check cache first
        cache_key = f"azure_{table_name}"
        if use_cache:
            cached = _cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {table_name}")
                return cached

        if not self.is_available:
            logger.warning(f"Azure not available, cannot read {table_name}")
            return None

        if not PYARROW_AVAILABLE:
            logger.warning("PyArrow not available for Parquet reading")
            return None

        # Get path for this table
        export_path = self.config.export_paths.get(table_name)
        if not export_path:
            logger.error(f"Unknown table: {table_name}")
            return None

        try:
            client = self._get_client()
            if not client:
                return None

            # Get file system client for Gold container
            fs_client = client.get_file_system_client(self.config.gold_container)

            # List Parquet files in the export path
            paths = list(fs_client.get_paths(path=export_path))
            parquet_files = [p for p in paths if p.name.endswith(".parquet")]

            if not parquet_files:
                logger.warning(f"No Parquet files found at {export_path}")
                return None

            # Read all Parquet files and combine
            all_records = []
            for file_path in parquet_files:
                file_client = fs_client.get_file_client(file_path.name)
                download = file_client.download_file()
                data = download.readall()

                # Read Parquet with PyArrow
                buffer = io.BytesIO(data)
                table = pq.read_table(buffer)
                records = table.to_pydict()

                # Convert to list of dicts
                # Safe check: records must have at least one column with values
                if records and len(records) > 0:
                    first_col = next(iter(records.values()), [])
                    num_rows = len(first_col) if first_col else 0
                    for i in range(num_rows):
                        record = {k: v[i] for k, v in records.items()}
                        all_records.append(record)

            # Cache the results
            _cache.set(cache_key, all_records)
            self._record_success()

            logger.info(f"Successfully read {len(all_records)} records from {table_name}")
            return all_records

        except Exception as e:
            error_msg = f"Error reading {table_name} from Azure: {str(e)}"
            logger.error(error_msg)
            self._record_failure(error_msg)
            return None

    def read_json_file(self, path: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Read a JSON file from Azure ADLS.

        Args:
            path: Path to JSON file within Gold container
            use_cache: Whether to use cached data

        Returns:
            JSON data as dictionary, or None on error
        """
        cache_key = f"azure_json_{path}"
        if use_cache:
            cached = _cache.get(cache_key)
            if cached is not None:
                return cached

        if not self.is_available:
            return None

        try:
            client = self._get_client()
            if not client:
                return None

            fs_client = client.get_file_system_client(self.config.gold_container)
            file_client = fs_client.get_file_client(path)

            download = file_client.download_file()
            data = json.loads(download.readall().decode("utf-8"))

            _cache.set(cache_key, data)
            self._record_success()
            return data

        except Exception as e:
            logger.error(f"Error reading JSON {path}: {e}")
            self._record_failure(str(e))
            return None

    def list_tables(self) -> List[str]:
        """List available Gold layer tables."""
        return list(self.config.export_paths.keys())

    def invalidate_cache(self, table_name: Optional[str] = None) -> Dict:
        """
        Invalidate cache for a specific table or all tables.

        Args:
            table_name: Table to invalidate, or None for all

        Returns:
            Status of cache invalidation
        """
        if table_name:
            cache_key = f"azure_{table_name}"
            _cache.invalidate(cache_key)
            return {"invalidated": [table_name]}
        else:
            _cache.clear()
            return {"invalidated": "all"}

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return _cache.stats()


# =============================================================================
# GOLD LAYER DATA MODELS
# =============================================================================

class GoldLayerData:
    """Helper class to work with Gold layer data structures."""

    @staticmethod
    def transform_customer_360(azure_record: Dict) -> Dict:
        """
        Transform Azure customer_360 record to API format.
        Maps Databricks column names to API response format.
        """
        return {
            "customer_id": azure_record.get("customer_id"),
            "name": f"{azure_record.get('first_name', '')} {azure_record.get('last_name', '')}".strip(),
            "email": azure_record.get("email"),
            "phone": azure_record.get("phone"),
            "address": azure_record.get("full_address", ""),
            "segment": azure_record.get("customer_segment", "Standard"),
            "customer_value_tier": azure_record.get("value_tier", "Bronze"),
            "customer_risk_score": azure_record.get("risk_category", "Low"),
            "total_claims": azure_record.get("total_claims", 0),
            "approved_claims": azure_record.get("approved_claims", 0),
            "total_annual_premium": azure_record.get("total_annual_premium", 0),
            "total_claim_amount": azure_record.get("total_claim_amount", 0),
            "loss_ratio": azure_record.get("loss_ratio", 0),
            "active_policies": azure_record.get("active_policies", 0),
            "customer_since": azure_record.get("customer_since"),
            "last_claim_date": azure_record.get("last_claim_date"),
            "total_pets": azure_record.get("total_pets", 0),
            "lifetime_value": azure_record.get("lifetime_value", 0),
            "churn_risk": azure_record.get("churn_risk", "Low"),
        }

    @staticmethod
    def transform_claims_analytics(azure_record: Dict) -> Dict:
        """Transform Azure claims_analytics record to API format."""
        return {
            "claim_id": azure_record.get("claim_id"),
            "customer_id": azure_record.get("customer_id"),
            "pet_id": azure_record.get("pet_id"),
            "claim_date": azure_record.get("claim_date") or azure_record.get("service_date"),
            "claim_amount": azure_record.get("claim_amount", 0),
            "status": azure_record.get("status", "pending"),
            "category": azure_record.get("claim_category", "General"),
            "processing_time_days": azure_record.get("processing_days", 0),
            "complexity_score": azure_record.get("complexity", "Medium"),
            "auto_adjudicated": azure_record.get("auto_adjudicated", False),
            "fraud_score": azure_record.get("fraud_score", 0),
            "provider_id": azure_record.get("provider_id"),
        }

    @staticmethod
    def transform_monthly_kpi(azure_record: Dict) -> Dict:
        """Transform Azure monthly_kpis record to API format."""
        return {
            "month": azure_record.get("month"),
            "total_claims": azure_record.get("total_claims", 0),
            "approved_claims": azure_record.get("approved_claims", 0),
            "denied_claims": azure_record.get("denied_claims", 0),
            "pending_claims": azure_record.get("pending_claims", 0),
            "approval_rate": azure_record.get("approval_rate", 0),
            "total_claim_amount": azure_record.get("total_claim_amount", 0),
            "avg_claim_amount": azure_record.get("avg_claim_amount", 0),
            "new_customers": azure_record.get("new_customers", 0),
            "churned_customers": azure_record.get("churned_customers", 0),
            "revenue": azure_record.get("total_premium", 0),
            "loss_ratio": azure_record.get("loss_ratio", 0),
        }

    @staticmethod
    def transform_risk_score(azure_record: Dict) -> Dict:
        """Transform Azure risk_scoring record to API format."""
        return {
            "customer_id": azure_record.get("customer_id"),
            "name": f"{azure_record.get('first_name', '')} {azure_record.get('last_name', '')}".strip(),
            "risk_category": azure_record.get("risk_category", "Low"),
            "risk_score": azure_record.get("risk_score", 0),
            "loss_ratio": azure_record.get("loss_ratio", 0),
            "total_claims": azure_record.get("total_claims", 0),
            "claim_frequency": azure_record.get("claim_frequency", 0),
            "risk_factors": azure_record.get("risk_factors", []),
        }

    @staticmethod
    def transform_provider_performance(azure_record: Dict) -> Dict:
        """Transform Azure provider_performance record to API format."""
        return {
            "provider_id": azure_record.get("provider_id"),
            "name": azure_record.get("provider_name", "Unknown"),
            "specialty": azure_record.get("specialty", "General"),
            "is_in_network": azure_record.get("is_in_network", False),
            "total_claims": azure_record.get("total_claims", 0),
            "total_claim_amount": azure_record.get("total_claim_amount", 0),
            "avg_claim_amount": azure_record.get("avg_claim_amount", 0),
            "approval_rate": azure_record.get("approval_rate", 0),
            "rating": azure_record.get("provider_rating", 4.0),
            "fraud_risk_score": azure_record.get("fraud_risk", "Low"),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

@lru_cache(maxsize=1)
def get_azure_service() -> AzureDataService:
    """Get the global Azure data service instance (thread-safe via lru_cache)."""
    return AzureDataService()


def reset_azure_service() -> None:
    """Reset the Azure service (for testing)."""
    get_azure_service.cache_clear()
    _cache.clear()
