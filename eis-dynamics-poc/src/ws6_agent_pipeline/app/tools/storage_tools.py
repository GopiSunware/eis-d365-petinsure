"""
Storage tools for Delta Lake and file operations.

These tools handle reading and writing data at each medallion layer
(Bronze, Silver, Gold) with proper metadata and versioning.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Default storage paths (can be overridden by config)
DEFAULT_BRONZE_PATH = "./data/agent_pipeline/bronze"
DEFAULT_SILVER_PATH = "./data/agent_pipeline/silver"
DEFAULT_GOLD_PATH = "./data/agent_pipeline/gold"


class StorageResult(BaseModel):
    """Result of a storage operation."""
    success: bool = True
    path: str = ""
    layer: str = ""
    record_id: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ReadResult(BaseModel):
    """Result of a read operation."""
    success: bool = True
    data: Optional[dict[str, Any]] = None
    layer: str = ""
    record_id: str = ""
    version: int = 0
    error: Optional[str] = None


def _ensure_directory(path: str) -> Path:
    """Ensure directory exists and return Path object."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _get_layer_path(layer: str, base_path: Optional[str] = None) -> Path:
    """Get the path for a specific layer."""
    if base_path:
        return Path(base_path)

    layer_paths = {
        "bronze": DEFAULT_BRONZE_PATH,
        "silver": DEFAULT_SILVER_PATH,
        "gold": DEFAULT_GOLD_PATH,
    }
    return Path(layer_paths.get(layer, DEFAULT_BRONZE_PATH))


@tool
def write_bronze(
    claim_id: str,
    data: dict[str, Any],
    validation_result: dict[str, Any],
    quality_result: dict[str, Any],
    anomaly_result: dict[str, Any],
    agent_reasoning: str,
    decision: str,
    confidence: float,
) -> dict[str, Any]:
    """
    Write validated claim data to the Bronze layer.

    Includes all validation metadata and agent reasoning.

    Args:
        claim_id: Unique claim identifier
        data: Cleaned claim data
        validation_result: Schema validation results
        quality_result: Data quality assessment
        anomaly_result: Anomaly detection results
        agent_reasoning: Agent's reasoning for the decision
        decision: Agent decision (accept/quarantine/reject)
        confidence: Confidence score for the decision

    Returns:
        StorageResult with write status and path
    """
    result = StorageResult(layer="bronze", record_id=claim_id)

    try:
        # Prepare the bronze record
        bronze_record = {
            "claim_id": claim_id,
            "raw_data": data,
            "validation": validation_result,
            "quality": quality_result,
            "anomalies": anomaly_result,
            "agent": {
                "reasoning": agent_reasoning,
                "decision": decision,
                "confidence": confidence,
                "agent_name": "bronze_agent",
                "agent_version": "1.0.0",
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "layer": "bronze",
                "source": "agent_pipeline",
            },
        }

        # Get storage path
        base_path = _get_layer_path("bronze")
        _ensure_directory(str(base_path))

        # Create date-partitioned path
        today = datetime.utcnow().strftime("%Y/%m/%d")
        partition_path = base_path / today
        _ensure_directory(str(partition_path))

        # Write the record
        file_name = f"{claim_id}_{datetime.utcnow().strftime('%H%M%S')}.json"
        file_path = partition_path / file_name

        with open(file_path, "w") as f:
            json.dump(bronze_record, f, indent=2, default=str)

        result.success = True
        result.path = str(file_path)
        result.timestamp = datetime.utcnow().isoformat()
        result.metadata = {
            "decision": decision,
            "confidence": confidence,
            "quality_score": quality_result.get("overall_score", 0),
        }

        logger.info(f"Bronze record written: {file_path}")

    except Exception as e:
        result.success = False
        result.error = str(e)
        logger.error(f"Failed to write bronze record: {e}")

    return result.model_dump()


@tool
def write_silver(
    claim_id: str,
    bronze_data: dict[str, Any],
    enrichment_data: dict[str, Any],
    normalized_data: dict[str, Any],
    business_rules_result: dict[str, Any],
    agent_reasoning: str,
) -> dict[str, Any]:
    """
    Write enriched claim data to the Silver layer.

    Includes enrichment data and business rule validations.

    Args:
        claim_id: Unique claim identifier
        bronze_data: Original bronze layer data
        enrichment_data: Enriched data (policy, customer, provider)
        normalized_data: Normalized and derived values
        business_rules_result: Business rules validation results
        agent_reasoning: Agent's enrichment reasoning

    Returns:
        StorageResult with write status and path
    """
    result = StorageResult(layer="silver", record_id=claim_id)

    try:
        # Prepare the silver record
        silver_record = {
            "claim_id": claim_id,
            "bronze_reference": {
                "claim_id": bronze_data.get("claim_id"),
                "decision": bronze_data.get("agent", {}).get("decision"),
            },
            "enrichment": enrichment_data,
            "normalized": normalized_data,
            "business_rules": business_rules_result,
            "agent": {
                "reasoning": agent_reasoning,
                "agent_name": "silver_agent",
                "agent_version": "1.0.0",
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "layer": "silver",
                "source": "agent_pipeline",
            },
        }

        # Get storage path
        base_path = _get_layer_path("silver")
        _ensure_directory(str(base_path))

        # Create date-partitioned path
        today = datetime.utcnow().strftime("%Y/%m/%d")
        partition_path = base_path / today
        _ensure_directory(str(partition_path))

        # Write the record
        file_name = f"{claim_id}_{datetime.utcnow().strftime('%H%M%S')}.json"
        file_path = partition_path / file_name

        with open(file_path, "w") as f:
            json.dump(silver_record, f, indent=2, default=str)

        result.success = True
        result.path = str(file_path)
        result.timestamp = datetime.utcnow().isoformat()
        result.metadata = {
            "enrichment_fields": list(enrichment_data.keys()),
            "rules_passed": len(business_rules_result.get("passed", [])),
            "rules_failed": len(business_rules_result.get("failed", [])),
        }

        logger.info(f"Silver record written: {file_path}")

    except Exception as e:
        result.success = False
        result.error = str(e)
        logger.error(f"Failed to write silver record: {e}")

    return result.model_dump()


@tool
def write_gold(
    claim_id: str,
    silver_data: dict[str, Any],
    risk_assessment: dict[str, Any],
    insights: list[str],
    kpi_metrics: dict[str, float],
    alerts: list[dict[str, Any]],
    final_decision: str,
    agent_reasoning: str,
) -> dict[str, Any]:
    """
    Write analyzed claim data to the Gold layer.

    Includes risk assessment, insights, and KPI contributions.

    Args:
        claim_id: Unique claim identifier
        silver_data: Silver layer reference data
        risk_assessment: Risk and fraud analysis
        insights: Generated insights
        kpi_metrics: KPI metric contributions
        alerts: Generated alerts
        final_decision: Final processing decision
        agent_reasoning: Agent's analysis reasoning

    Returns:
        StorageResult with write status and path
    """
    result = StorageResult(layer="gold", record_id=claim_id)

    try:
        # Prepare the gold record
        gold_record = {
            "claim_id": claim_id,
            "silver_reference": {
                "claim_id": silver_data.get("claim_id"),
            },
            "risk": risk_assessment,
            "insights": insights,
            "kpis": kpi_metrics,
            "alerts": alerts,
            "final_decision": final_decision,
            "agent": {
                "reasoning": agent_reasoning,
                "agent_name": "gold_agent",
                "agent_version": "1.0.0",
            },
            "metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "layer": "gold",
                "source": "agent_pipeline",
            },
        }

        # Get storage path
        base_path = _get_layer_path("gold")
        _ensure_directory(str(base_path))

        # Create date-partitioned path
        today = datetime.utcnow().strftime("%Y/%m/%d")
        partition_path = base_path / today
        _ensure_directory(str(partition_path))

        # Write the record
        file_name = f"{claim_id}_{datetime.utcnow().strftime('%H%M%S')}.json"
        file_path = partition_path / file_name

        with open(file_path, "w") as f:
            json.dump(gold_record, f, indent=2, default=str)

        result.success = True
        result.path = str(file_path)
        result.timestamp = datetime.utcnow().isoformat()
        result.metadata = {
            "final_decision": final_decision,
            "risk_level": risk_assessment.get("risk_level", "unknown"),
            "fraud_score": risk_assessment.get("fraud_score", 0),
            "alerts_count": len(alerts),
            "insights_count": len(insights),
        }

        logger.info(f"Gold record written: {file_path}")

    except Exception as e:
        result.success = False
        result.error = str(e)
        logger.error(f"Failed to write gold record: {e}")

    return result.model_dump()


@tool
def read_layer_data(
    claim_id: str,
    layer: str,
) -> dict[str, Any]:
    """
    Read data from a specific layer for a claim.

    Args:
        claim_id: The claim ID to look up
        layer: The layer to read from (bronze/silver/gold)

    Returns:
        ReadResult with the data if found
    """
    result = ReadResult(layer=layer, record_id=claim_id)

    try:
        base_path = _get_layer_path(layer)

        # Search for the most recent file matching the claim_id
        matching_files = list(base_path.rglob(f"{claim_id}_*.json"))

        if not matching_files:
            result.success = False
            result.error = f"No {layer} record found for claim {claim_id}"
            return result.model_dump()

        # Get the most recent file
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)

        with open(latest_file, "r") as f:
            data = json.load(f)

        result.success = True
        result.data = data
        result.version = 1  # Simple versioning for now

        logger.info(f"Read {layer} record: {latest_file}")

    except Exception as e:
        result.success = False
        result.error = str(e)
        logger.error(f"Failed to read {layer} record: {e}")

    return result.model_dump()


@tool
def get_historical_claims(
    customer_id: Optional[str] = None,
    provider_name: Optional[str] = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Retrieve historical claims for anomaly detection.

    Args:
        customer_id: Optional customer ID to filter by
        provider_name: Optional provider name to filter by
        limit: Maximum number of claims to return

    Returns:
        List of historical claim records
    """
    try:
        base_path = _get_layer_path("bronze")
        all_claims = []

        # Read all bronze records
        for json_file in base_path.rglob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                raw_data = data.get("raw_data", data)

                # Filter by customer_id if specified
                if customer_id and raw_data.get("customer_id") != customer_id:
                    continue

                # Filter by provider_name if specified
                if provider_name and raw_data.get("provider_name") != provider_name:
                    continue

                all_claims.append(raw_data)

                if len(all_claims) >= limit:
                    break

            except Exception:
                continue

        return {
            "success": True,
            "claims": all_claims,
            "count": len(all_claims),
            "filters": {
                "customer_id": customer_id,
                "provider_name": provider_name,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get historical claims: {e}")
        return {
            "success": False,
            "claims": [],
            "count": 0,
            "error": str(e),
        }


@tool
def update_kpi_aggregates(
    claim_id: str,
    kpi_metrics: dict[str, float],
    claim_type: str,
    claim_amount: float,
) -> dict[str, Any]:
    """
    Update KPI aggregate tables with new claim metrics.

    Args:
        claim_id: The claim ID
        kpi_metrics: KPI metrics from the claim
        claim_type: Type of claim
        claim_amount: Claim amount

    Returns:
        Update status
    """
    try:
        # Path for KPI aggregates
        kpi_path = Path(DEFAULT_GOLD_PATH) / "kpis"
        _ensure_directory(str(kpi_path))

        # Load or create daily aggregates
        today = datetime.utcnow().strftime("%Y-%m-%d")
        agg_file = kpi_path / f"daily_agg_{today}.json"

        if agg_file.exists():
            with open(agg_file, "r") as f:
                aggregates = json.load(f)
        else:
            aggregates = {
                "date": today,
                "total_claims": 0,
                "total_amount": 0.0,
                "claims_by_type": {},
                "amount_by_type": {},
                "avg_processing_time_ms": 0.0,
                "claim_ids": [],
            }

        # Update aggregates
        aggregates["total_claims"] += 1
        aggregates["total_amount"] += claim_amount
        aggregates["claims_by_type"][claim_type] = aggregates["claims_by_type"].get(claim_type, 0) + 1
        aggregates["amount_by_type"][claim_type] = aggregates["amount_by_type"].get(claim_type, 0) + claim_amount
        aggregates["claim_ids"].append(claim_id)

        # Add KPI metrics
        for key, value in kpi_metrics.items():
            if key not in aggregates:
                aggregates[key] = 0.0
            aggregates[key] += value

        # Write updated aggregates
        with open(agg_file, "w") as f:
            json.dump(aggregates, f, indent=2, default=str)

        logger.info(f"Updated KPI aggregates: {agg_file}")

        return {
            "success": True,
            "file": str(agg_file),
            "total_claims": aggregates["total_claims"],
            "total_amount": aggregates["total_amount"],
        }

    except Exception as e:
        logger.error(f"Failed to update KPI aggregates: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Export all storage tools
STORAGE_TOOLS = [
    write_bronze,
    write_silver,
    write_gold,
    read_layer_data,
    get_historical_claims,
    update_kpi_aggregates,
]
