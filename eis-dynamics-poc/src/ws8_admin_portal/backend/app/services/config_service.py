"""Configuration management service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..config import settings
from ..models.ai_config import AIConfiguration, AIConfigVersion
from ..models.claims_rules import ClaimsRulesConfig
from ..models.rating_config import RatingFactorsConfig
from ..models.policy_config import PolicyPlansConfig
from .cosmos_service import get_cosmos_client

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing configuration data."""

    COLLECTION = "admin_config"
    VERSIONS_COLLECTION = "config_versions"

    # In-memory storage for when Cosmos DB is not configured
    _memory_store: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.cosmos = get_cosmos_client()

    # ==================== AI Configuration ====================

    async def get_ai_config(self) -> AIConfiguration:
        """Get current AI configuration."""
        config = await self._get_config("ai_config", "ai_config")
        if config:
            return AIConfiguration(**config)
        return AIConfiguration()

    async def update_ai_config_direct(
        self,
        update_data: Dict[str, Any],
        approved_by: str,
        approval_id: str,
    ) -> AIConfiguration:
        """Update AI configuration directly (after approval)."""
        current = await self.get_ai_config()
        current_version = current.version

        # Apply updates
        updated_dict = current.model_dump()
        for key, value in update_data.items():
            if key not in ["id", "config_type", "version"]:
                updated_dict[key] = value

        updated_dict["version"] = current_version + 1
        updated_dict["updated_at"] = datetime.utcnow().isoformat()
        updated_dict["updated_by"] = approved_by

        # Save updated config
        await self._save_config("ai_config", "ai_config", updated_dict)

        # Save version history
        await self._save_version(
            config_id="ai_config",
            version=updated_dict["version"],
            value=updated_dict,
            changed_by=approved_by,
            approval_id=approval_id,
            change_summary=f"AI config updated via approval {approval_id}",
        )

        return AIConfiguration(**updated_dict)

    async def get_ai_config_history(self, limit: int = 20) -> List[AIConfigVersion]:
        """Get AI configuration change history."""
        return await self._get_config_history("ai_config", limit)

    # ==================== Claims Rules ====================

    async def get_claims_rules(self) -> ClaimsRulesConfig:
        """Get current claims rules configuration."""
        config = await self._get_config("claims_rules", "claims_rules")
        if config:
            return ClaimsRulesConfig(**config)
        return ClaimsRulesConfig()

    async def update_claims_rules_direct(
        self,
        entity_id: str,
        update_data: Dict[str, Any],
        approved_by: str,
        approval_id: str,
    ) -> ClaimsRulesConfig:
        """Update claims rules directly (after approval)."""
        current = await self.get_claims_rules()
        current_version = current.version

        # Apply updates
        updated_dict = current.model_dump()
        for key, value in update_data.items():
            if key not in ["id", "config_type", "version"]:
                updated_dict[key] = value

        updated_dict["version"] = current_version + 1
        updated_dict["updated_at"] = datetime.utcnow().isoformat()
        updated_dict["updated_by"] = approved_by

        # Save updated config
        await self._save_config("claims_rules", "claims_rules", updated_dict)

        # Save version history
        await self._save_version(
            config_id="claims_rules",
            version=updated_dict["version"],
            value=updated_dict,
            changed_by=approved_by,
            approval_id=approval_id,
            change_summary=f"Claims rules updated via approval {approval_id}",
        )

        return ClaimsRulesConfig(**updated_dict)

    # ==================== Rating Configuration ====================

    async def get_rating_config(self) -> RatingFactorsConfig:
        """Get current rating configuration."""
        config = await self._get_config("rating_config", "rating_config")
        if config:
            return RatingFactorsConfig(**config)
        return RatingFactorsConfig()

    async def update_rating_config_direct(
        self,
        entity_id: str,
        update_data: Dict[str, Any],
        approved_by: str,
        approval_id: str,
    ) -> RatingFactorsConfig:
        """Update rating configuration directly (after approval)."""
        current = await self.get_rating_config()
        current_version = current.version

        # Apply updates
        updated_dict = current.model_dump()
        for key, value in update_data.items():
            if key not in ["id", "config_type", "version"]:
                updated_dict[key] = value

        updated_dict["version"] = current_version + 1
        updated_dict["updated_at"] = datetime.utcnow().isoformat()
        updated_dict["updated_by"] = approved_by

        # Save updated config
        await self._save_config("rating_config", "rating_config", updated_dict)

        # Save version history
        await self._save_version(
            config_id="rating_config",
            version=updated_dict["version"],
            value=updated_dict,
            changed_by=approved_by,
            approval_id=approval_id,
            change_summary=f"Rating config updated via approval {approval_id}",
        )

        return RatingFactorsConfig(**updated_dict)

    # ==================== Policy Configuration ====================

    async def get_policy_config(self) -> PolicyPlansConfig:
        """Get current policy configuration."""
        config = await self._get_config("policy_config", "policy_config")
        if config:
            return PolicyPlansConfig(**config)
        return PolicyPlansConfig()

    async def update_policy_config_direct(
        self,
        entity_id: str,
        update_data: Dict[str, Any],
        approved_by: str,
        approval_id: str,
    ) -> PolicyPlansConfig:
        """Update policy configuration directly (after approval)."""
        current = await self.get_policy_config()
        current_version = current.version

        # Apply updates
        updated_dict = current.model_dump()
        for key, value in update_data.items():
            if key not in ["id", "config_type", "version"]:
                updated_dict[key] = value

        updated_dict["version"] = current_version + 1
        updated_dict["updated_at"] = datetime.utcnow().isoformat()
        updated_dict["updated_by"] = approved_by

        # Save updated config
        await self._save_config("policy_config", "policy_config", updated_dict)

        # Save version history
        await self._save_version(
            config_id="policy_config",
            version=updated_dict["version"],
            value=updated_dict,
            changed_by=approved_by,
            approval_id=approval_id,
            change_summary=f"Policy config updated via approval {approval_id}",
        )

        return PolicyPlansConfig(**updated_dict)

    # ==================== Generic Methods ====================

    async def _get_config(
        self,
        config_id: str,
        config_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Get configuration by ID."""
        # Try Cosmos DB first
        if settings.cosmos_db_configured:
            result = await self.cosmos.get_document(
                collection=self.COLLECTION,
                document_id=config_id,
                partition_key=config_type,
            )
            if result:
                return result

        # Fall back to memory store
        key = f"{config_type}:{config_id}"
        return self._memory_store.get(key)

    async def _save_config(
        self,
        config_id: str,
        config_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save configuration."""
        data["id"] = config_id
        data["config_type"] = config_type

        if settings.cosmos_db_configured:
            return await self.cosmos.update_document(
                collection=self.COLLECTION,
                document_id=config_id,
                document=data,
                partition_key=config_type,
            )

        # Fall back to memory store
        key = f"{config_type}:{config_id}"
        self._memory_store[key] = data
        return data

    async def _save_version(
        self,
        config_id: str,
        version: int,
        value: Dict[str, Any],
        changed_by: str,
        approval_id: Optional[str],
        change_summary: str,
    ):
        """Save configuration version history."""
        version_doc = {
            "id": f"{config_id}_v{version}_{uuid4().hex[:8]}",
            "config_id": config_id,
            "version": version,
            "value": value,
            "changed_by": changed_by,
            "changed_at": datetime.utcnow().isoformat(),
            "approval_id": approval_id,
            "change_summary": change_summary,
        }

        if settings.cosmos_db_configured:
            await self.cosmos.create_document(
                collection=self.VERSIONS_COLLECTION,
                document=version_doc,
                partition_key=config_id,
            )
        else:
            # Memory store for versions
            key = f"versions:{config_id}"
            if key not in self._memory_store:
                self._memory_store[key] = []
            self._memory_store[key].append(version_doc)

    async def _get_config_history(
        self,
        config_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get configuration version history."""
        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.VERSIONS_COLLECTION,
                query="SELECT * FROM c WHERE c.config_id = @config_id ORDER BY c.version DESC",
                parameters=[{"name": "@config_id", "value": config_id}],
            )
            return results[:limit]

        # Memory store fallback
        key = f"versions:{config_id}"
        versions = self._memory_store.get(key, [])
        return sorted(versions, key=lambda x: x.get("version", 0), reverse=True)[:limit]


# Singleton
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """Get config service singleton."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
