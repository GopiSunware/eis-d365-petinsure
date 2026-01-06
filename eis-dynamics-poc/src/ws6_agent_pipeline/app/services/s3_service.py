"""
S3 Data Lake Service for Agent Pipeline
Handles write operations to S3 medallion layers (bronze/silver/gold)
"""

import os
import json
import boto3
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class S3DataLakeService:
    """Service for writing agent outputs to S3 Data Lake"""

    def __init__(self):
        self.bucket_name = os.getenv("S3_DATALAKE_BUCKET", "eis-dynamics-datalake-611670815873")
        self.region = os.getenv("AWS_REGION", "us-east-1")

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                "s3",
                region_name=self.region
            )
            self.enabled = True
            logger.info(f"S3 DataLake initialized: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"S3 not available, running in local mode: {e}")
            self.s3_client = None
            self.enabled = False

    def is_enabled(self) -> bool:
        """Check if S3 is enabled"""
        return self.enabled and self.s3_client is not None

    def write_bronze_output(self, claim_id: str, run_id: str, bronze_data: Dict[str, Any]) -> Optional[str]:
        """Write Bronze agent output to S3"""
        if not self.is_enabled():
            logger.debug("S3 not enabled, skipping bronze output write")
            return None

        key = f"bronze/{claim_id}/output.json"

        bronze_output = {
            "claim_id": claim_id,
            "run_id": run_id,
            "layer": "bronze",
            "processed_at": datetime.now().isoformat(),
            "agent": "BronzeAgent",
            "processing_engine": "AI-LangGraph",
            "data": bronze_data,
            "metadata": {
                "quality_score": bronze_data.get("quality_score", 0),
                "validation_passed": bronze_data.get("validation_passed", False),
                "issues_found": bronze_data.get("issues", []),
                "decision": bronze_data.get("decision", "pending")
            }
        }

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(bronze_output, indent=2, default=str),
                ContentType="application/json"
            )
            logger.info(f"Written bronze output to S3: {key}")
            return f"s3://{self.bucket_name}/{key}"
        except ClientError as e:
            logger.error(f"Failed to write bronze output: {e}")
            return None

    def write_silver_output(self, claim_id: str, run_id: str, silver_data: Dict[str, Any]) -> Optional[str]:
        """Write Silver agent output to S3"""
        if not self.is_enabled():
            logger.debug("S3 not enabled, skipping silver output write")
            return None

        key = f"silver/{claim_id}/output.json"

        silver_output = {
            "claim_id": claim_id,
            "run_id": run_id,
            "layer": "silver",
            "processed_at": datetime.now().isoformat(),
            "agent": "SilverAgent",
            "processing_engine": "AI-LangGraph",
            "data": silver_data,
            "enrichment": {
                "policy_info": silver_data.get("policy", {}),
                "customer_info": silver_data.get("customer", {}),
                "pet_info": silver_data.get("pet", {}),
                "provider_info": silver_data.get("provider", {}),
                "reimbursement_calculation": silver_data.get("reimbursement", {})
            }
        }

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(silver_output, indent=2, default=str),
                ContentType="application/json"
            )
            logger.info(f"Written silver output to S3: {key}")
            return f"s3://{self.bucket_name}/{key}"
        except ClientError as e:
            logger.error(f"Failed to write silver output: {e}")
            return None

    def write_gold_output(self, claim_id: str, run_id: str, gold_data: Dict[str, Any]) -> Optional[str]:
        """Write Gold agent output to S3"""
        if not self.is_enabled():
            logger.debug("S3 not enabled, skipping gold output write")
            return None

        key = f"gold/{claim_id}/output.json"

        gold_output = {
            "claim_id": claim_id,
            "run_id": run_id,
            "layer": "gold",
            "processed_at": datetime.now().isoformat(),
            "agent": "GoldAgent",
            "processing_engine": "AI-LangGraph",
            "data": gold_data,
            "decision": {
                "final_decision": gold_data.get("final_decision", "pending"),
                "risk_level": gold_data.get("risk_level", "unknown"),
                "fraud_score": gold_data.get("fraud_score", 0),
                "fraud_indicators": gold_data.get("fraud_indicators", []),
                "validation_issues": gold_data.get("validation_issues", []),
                "recommended_action": gold_data.get("recommended_action", "manual_review"),
                "reasoning": gold_data.get("reasoning", "")
            }
        }

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(gold_output, indent=2, default=str),
                ContentType="application/json"
            )
            logger.info(f"Written gold output to S3: {key}")
            return f"s3://{self.bucket_name}/{key}"
        except ClientError as e:
            logger.error(f"Failed to write gold output: {e}")
            return None

    def read_layer_output(self, layer: str, claim_id: str) -> Optional[Dict[str, Any]]:
        """Read layer output from S3"""
        if not self.is_enabled():
            return None

        key = f"{layer}/{claim_id}/output.json"

        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            logger.error(f"Failed to read {layer} output: {e}")
            return None

    def get_claim_pipeline_status(self, claim_id: str) -> Dict[str, Any]:
        """Get pipeline status for a specific claim"""
        if not self.is_enabled():
            return {"enabled": False}

        status = {
            "claim_id": claim_id,
            "layers": {}
        }

        for layer in ["raw", "bronze", "silver", "gold"]:
            try:
                if layer == "raw":
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=f"raw/claims/{claim_id}",
                        MaxKeys=1
                    )
                    exists = response.get("KeyCount", 0) > 0
                else:
                    response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=f"{layer}/{claim_id}/output.json"
                    )
                    exists = True

                status["layers"][layer] = {
                    "processed": exists,
                    "status": "complete" if exists else "pending"
                }
            except ClientError:
                status["layers"][layer] = {
                    "processed": False,
                    "status": "pending"
                }

        return status


# Singleton instance
_s3_service = None


def get_s3_service() -> S3DataLakeService:
    """Get singleton S3 service instance"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3DataLakeService()
    return _s3_service
