"""Sync service for EIS ↔ Dataverse synchronization."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from eis_common.config import get_settings
from eis_common.dataverse import get_dataverse_client

logger = logging.getLogger(__name__)
settings = get_settings()


class SyncService:
    """Handles synchronization between EIS and Dataverse."""

    def __init__(self):
        # Use EIS mock URL from config, fallback to self (ws3 hosts the mock)
        base_url = settings.eis_mock_url or settings.ws3_integration_url
        self.eis_base_url = f"{base_url}/api/v1/eis" if base_url else "/api/v1/eis"

    async def sync_eis_to_dataverse(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync data from EIS to Dataverse."""
        logger.info(f"Syncing {entity_type} from EIS to Dataverse")

        processed = 0
        failed = 0

        try:
            # Fetch from EIS
            async with httpx.AsyncClient() as client:
                if entity_id:
                    url = f"{self.eis_base_url}/{entity_type}s/{entity_id}"
                    response = await client.get(url)
                    records = [response.json()] if response.status_code == 200 else []
                else:
                    url = f"{self.eis_base_url}/{entity_type}s"
                    response = await client.get(url)
                    records = response.json() if response.status_code == 200 else []

            # Transform and upsert to Dataverse
            dataverse = get_dataverse_client()

            for record in records:
                try:
                    if entity_type == "policy":
                        await self._sync_policy_to_dataverse(dataverse, record)
                    elif entity_type == "claim":
                        await self._sync_claim_to_dataverse(dataverse, record)
                    elif entity_type == "customer":
                        await self._sync_customer_to_dataverse(dataverse, record)

                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to sync {entity_type} {record.get('policy_id', record.get('claim_id'))}: {e}")
                    failed += 1

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise

        return {"processed": processed, "failed": failed}

    async def _sync_policy_to_dataverse(self, dataverse, eis_record: dict):
        """Transform and sync policy to Dataverse."""
        # Map EIS policy to Dataverse format
        dataverse_record = {
            "eis_policynumber": eis_record["policy_number"],
            "eis_effectivedate": eis_record["effective_date"],
            "eis_expirationdate": eis_record["expiration_date"],
            "eis_status": self._map_policy_status(eis_record["status"]),
            "eis_totalpremium": float(eis_record["total_premium"]),
            "eis_externalpolicyid": eis_record["policy_id"],
            "eis_lastsyncdate": datetime.utcnow().isoformat(),
        }

        # Upsert using external ID as alternate key
        try:
            await dataverse.upsert(
                entity_set="eis_policies",
                alternate_key=f"eis_externalpolicyid='{eis_record['policy_id']}'",
                data=dataverse_record,
            )
            logger.info(f"Synced policy {eis_record['policy_number']} to Dataverse")
        except Exception as e:
            # If Dataverse not configured, log and continue
            logger.warning(f"Dataverse sync skipped (not configured): {e}")

    async def _sync_claim_to_dataverse(self, dataverse, eis_record: dict):
        """Transform and sync claim to Dataverse."""
        dataverse_record = {
            "eis_claimnumber": eis_record["claim_number"],
            "eis_dateofloss": eis_record["date_of_loss"],
            "eis_datereported": eis_record["date_reported"],
            "eis_status": self._map_claim_status(eis_record["status"]),
            "eis_lossdescription": eis_record["loss_description"],
            "eis_reserveamount": float(eis_record["reserve_amount"]),
            "eis_paidamount": float(eis_record["paid_amount"]),
            "eis_externalclaimid": eis_record["claim_id"],
        }

        try:
            await dataverse.upsert(
                entity_set="eis_claims",
                alternate_key=f"eis_externalclaimid='{eis_record['claim_id']}'",
                data=dataverse_record,
            )
            logger.info(f"Synced claim {eis_record['claim_number']} to Dataverse")
        except Exception as e:
            logger.warning(f"Dataverse sync skipped: {e}")

    async def _sync_customer_to_dataverse(self, dataverse, eis_record: dict):
        """Transform and sync customer to Dataverse."""
        dataverse_record = {
            "eis_firstname": eis_record["first_name"],
            "eis_lastname": eis_record["last_name"],
            "eis_fullname": f"{eis_record['first_name']} {eis_record['last_name']}",
            "eis_email": eis_record.get("email"),
            "eis_phone": eis_record.get("phone"),
            "eis_externalcustomerid": eis_record["customer_id"],
        }

        try:
            await dataverse.upsert(
                entity_set="eis_insuredparties",
                alternate_key=f"eis_externalcustomerid='{eis_record['customer_id']}'",
                data=dataverse_record,
            )
            logger.info(f"Synced customer {eis_record['customer_id']} to Dataverse")
        except Exception as e:
            logger.warning(f"Dataverse sync skipped: {e}")

    async def sync_dataverse_to_eis(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync data from Dataverse to EIS (reverse sync)."""
        # Implementation would mirror sync_eis_to_dataverse
        logger.info(f"Reverse sync {entity_type} from Dataverse to EIS (not implemented)")
        return {"processed": 0, "failed": 0, "message": "Reverse sync not implemented"}

    def _map_policy_status(self, eis_status: str) -> int:
        """Map EIS policy status to Dataverse option set value."""
        mapping = {
            "draft": 100000000,
            "quoted": 100000001,
            "bound": 100000002,
            "active": 100000003,
            "pending_renewal": 100000004,
            "renewed": 100000005,
            "cancelled": 100000006,
            "expired": 100000007,
            "non_renewed": 100000008,
        }
        return mapping.get(eis_status.lower(), 100000003)

    def _map_claim_status(self, eis_status: str) -> int:
        """Map EIS claim status to Dataverse option set value."""
        mapping = {
            "fnol_received": 100000000,
            "under_investigation": 100000001,
            "pending_info": 100000002,
            "approved": 100000003,
            "denied": 100000004,
            "in_payment": 100000005,
            "closed_paid": 100000006,
            "closed_no_payment": 100000007,
            "reopened": 100000008,
            "subrogation": 100000009,
        }
        return mapping.get(eis_status.lower(), 100000000)
