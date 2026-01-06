"""
PetInsure360 - Azure Storage Service
Handles writing data to Azure Data Lake Storage Gen2
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

class StorageService:
    """Service for Azure Data Lake Storage Gen2 operations."""

    def __init__(self):
        """Initialize storage service with Azure credentials."""
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT", "petinsud7i43")
        self.account_key = os.getenv("AZURE_STORAGE_KEY", "")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "raw")

        # Connection string
        if self.account_key:
            self.connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key};"
                f"EndpointSuffix=core.windows.net"
            )
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        else:
            # For demo mode without actual Azure connection
            self.blob_service_client = None
            print("WARNING: Running in demo mode - data will not be persisted to Azure")

    async def write_json(self, entity_type: str, data: Dict[str, Any], entity_id: str) -> str:
        """
        Write JSON data to ADLS Gen2.

        Args:
            entity_type: Type of entity (customers, pets, policies, claims)
            data: Dictionary of data to write
            entity_id: Unique identifier for the entity

        Returns:
            Path to the written file
        """
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{entity_id}_{timestamp}.json"
        blob_path = f"{entity_type}/{filename}"

        # Add metadata
        data["_ingestion_timestamp"] = datetime.utcnow().isoformat()
        data["_source"] = "api"
        data["_entity_id"] = entity_id

        # Convert to JSON
        json_data = json.dumps(data, indent=2, default=str)

        if self.blob_service_client:
            # Write to Azure Blob Storage
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_path
                )
                blob_client.upload_blob(
                    json_data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type='application/json')
                )
                print(f"Written to ADLS: {self.container_name}/{blob_path}")
            except Exception as e:
                print(f"Error writing to ADLS: {e}")
                # Fall back to local storage
                self._write_local(blob_path, json_data)
        else:
            # Write to local storage for demo
            self._write_local(blob_path, json_data)

        return blob_path

    def _write_local(self, path: str, data: str):
        """Write to local storage for demo mode."""
        local_path = os.path.join("data", "local_storage", path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w') as f:
            f.write(data)
        print(f"Written to local: {local_path}")

    async def list_files(self, entity_type: str) -> list:
        """List files for an entity type."""
        if self.blob_service_client:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            blobs = container_client.list_blobs(name_starts_with=f"{entity_type}/")
            return [blob.name for blob in blobs]
        return []

    async def read_json(self, blob_path: str) -> Dict[str, Any]:
        """Read JSON data from ADLS."""
        if self.blob_service_client:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            data = blob_client.download_blob().readall()
            return json.loads(data)
        return {}

    async def write_demo_data(self, entity_type: str, records: list) -> str:
        """
        Persist demo data (customers, pets, claims) to Azure Storage.
        Writes as JSON Lines format for easy loading.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_{entity_type}_{timestamp}.jsonl"
        blob_path = f"demo/{entity_type}/{filename}"

        # Convert to JSON Lines format
        jsonl_data = "\n".join(json.dumps(record, default=str) for record in records)

        if self.blob_service_client:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_path
                )
                blob_client.upload_blob(
                    jsonl_data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type='application/jsonlines')
                )
                print(f"Persisted {len(records)} {entity_type} to ADLS: {blob_path}")
                return blob_path
            except Exception as e:
                print(f"Error persisting demo data: {e}")
        return ""

    async def load_demo_data(self, entity_type: str) -> list:
        """
        Load persisted demo data from Azure Storage.
        Returns list of records or empty list if none found.
        """
        if not self.blob_service_client:
            return []

        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = list(container_client.list_blobs(name_starts_with=f"demo/{entity_type}/"))

            if not blobs:
                return []

            # Get the most recent file
            latest_blob = sorted(blobs, key=lambda b: b.name, reverse=True)[0]
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=latest_blob.name
            )
            data = blob_client.download_blob().readall().decode('utf-8')

            # Parse JSON Lines
            records = []
            for line in data.strip().split("\n"):
                if line:
                    records.append(json.loads(line))

            print(f"Loaded {len(records)} {entity_type} from ADLS: {latest_blob.name}")
            return records
        except Exception as e:
            print(f"Error loading demo data: {e}")
            return []

    async def clear_demo_data(self, entity_type: str = None) -> bool:
        """Clear persisted demo data from Azure Storage."""
        if not self.blob_service_client:
            return False

        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            prefix = f"demo/{entity_type}/" if entity_type else "demo/"
            blobs = list(container_client.list_blobs(name_starts_with=prefix))

            for blob in blobs:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob.name
                )
                blob_client.delete_blob()

            print(f"Cleared {len(blobs)} demo files from ADLS")
            return True
        except Exception as e:
            print(f"Error clearing demo data: {e}")
            return False


class LocalStorageService:
    """Local storage service for demo/development mode."""

    def __init__(self, base_path: str = "data/local_storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def write_json(self, entity_type: str, data: Dict[str, Any], entity_id: str) -> str:
        """Write JSON data to local storage."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{entity_id}_{timestamp}.json"
        file_path = os.path.join(self.base_path, entity_type, filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        data["_ingestion_timestamp"] = datetime.utcnow().isoformat()
        data["_source"] = "api"
        data["_entity_id"] = entity_id

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return file_path
