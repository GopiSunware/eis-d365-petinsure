"""Cosmos DB service for Admin Portal."""

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from ..config import settings

logger = logging.getLogger(__name__)


class CosmosService:
    """Service for Cosmos DB operations."""

    # Collection definitions
    COLLECTIONS = {
        "admin_config": {
            "partition_key": "/config_type",
            "unique_keys": ["/id"]
        },
        "config_pending_approvals": {
            "partition_key": "/change_type",
            "unique_keys": ["/id"]
        },
        "config_versions": {
            "partition_key": "/config_id",
            "unique_keys": []
        },
        "audit_logs": {
            "partition_key": "/partition_key",
            "unique_keys": []
        },
        "users": {
            "partition_key": "/role",
            "unique_keys": ["/email"]
        },
        "budget_alerts": {
            "partition_key": "/provider",
            "unique_keys": ["/id"]
        },
    }

    def __init__(self):
        self.client: Optional[CosmosClient] = None
        self.database = None
        self.containers: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize Cosmos DB client and ensure collections exist."""
        if self._initialized:
            return

        if not settings.cosmos_db_configured:
            logger.warning("Cosmos DB not configured, using in-memory storage")
            self._initialized = True
            return

        try:
            self.client = CosmosClient(
                url=settings.COSMOS_DB_ENDPOINT,
                credential=settings.COSMOS_DB_KEY,
            )

            # Create database if not exists
            self.database = self.client.create_database_if_not_exists(
                id=settings.COSMOS_DB_DATABASE
            )

            # Create containers
            for collection_name, config in self.COLLECTIONS.items():
                container = self.database.create_container_if_not_exists(
                    id=collection_name,
                    partition_key=PartitionKey(path=config["partition_key"]),
                )
                self.containers[collection_name] = container

            self._initialized = True
            logger.info(f"Cosmos DB initialized with database: {settings.COSMOS_DB_DATABASE}")

        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise

    async def close(self):
        """Close Cosmos DB client."""
        if self.client:
            # CosmosClient doesn't have an explicit close method
            self.client = None
            self.database = None
            self.containers = {}
            self._initialized = False

    def _get_container(self, collection: str):
        """Get container by name."""
        if collection not in self.containers:
            raise ValueError(f"Unknown collection: {collection}")
        return self.containers[collection]

    async def create_document(
        self,
        collection: str,
        document: Dict[str, Any],
        partition_key: str,
    ) -> Dict[str, Any]:
        """Create a new document."""
        if not self._initialized or not settings.cosmos_db_configured:
            # In-memory fallback
            if "id" not in document:
                document["id"] = str(uuid4())
            return document

        container = self._get_container(collection)

        if "id" not in document:
            document["id"] = str(uuid4())

        result = container.create_item(body=document)
        return result

    async def get_document(
        self,
        collection: str,
        document_id: str,
        partition_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        if not self._initialized or not settings.cosmos_db_configured:
            return None

        container = self._get_container(collection)

        try:
            result = container.read_item(item=document_id, partition_key=partition_key)
            return result
        except CosmosResourceNotFoundError:
            return None

    async def update_document(
        self,
        collection: str,
        document_id: str,
        document: Dict[str, Any],
        partition_key: str,
    ) -> Dict[str, Any]:
        """Update an existing document."""
        if not self._initialized or not settings.cosmos_db_configured:
            return document

        container = self._get_container(collection)

        document["id"] = document_id
        result = container.upsert_item(body=document)
        return result

    async def delete_document(
        self,
        collection: str,
        document_id: str,
        partition_key: str,
    ) -> bool:
        """Delete a document."""
        if not self._initialized or not settings.cosmos_db_configured:
            return True

        container = self._get_container(collection)

        try:
            container.delete_item(item=document_id, partition_key=partition_key)
            return True
        except CosmosResourceNotFoundError:
            return False

    async def query_documents(
        self,
        collection: str,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query documents using SQL."""
        if not self._initialized or not settings.cosmos_db_configured:
            return []

        container = self._get_container(collection)

        query_options = {}
        if partition_key:
            query_options["partition_key"] = partition_key

        items = container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=partition_key is None,
        )

        return list(items)

    async def query_all(
        self,
        collection: str,
        partition_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all documents from a collection."""
        return await self.query_documents(
            collection=collection,
            query="SELECT * FROM c",
            partition_key=partition_key,
        )

    async def count_documents(
        self,
        collection: str,
        query: str = "SELECT VALUE COUNT(1) FROM c",
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Count documents matching a query."""
        if not self._initialized or not settings.cosmos_db_configured:
            return 0

        container = self._get_container(collection)

        items = container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True,
        )

        result = list(items)
        return result[0] if result else 0


# Singleton instance
cosmos_client = CosmosService()


def get_cosmos_client() -> CosmosService:
    """Get Cosmos DB client singleton."""
    return cosmos_client
