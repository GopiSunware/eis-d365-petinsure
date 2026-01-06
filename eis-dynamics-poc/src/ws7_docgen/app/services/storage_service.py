"""Storage service for document management."""

import hashlib
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Optional, Tuple
from uuid import uuid4

import aiofiles

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storing and retrieving documents."""

    def __init__(self):
        self.use_local = settings.USE_LOCAL_STORAGE
        self.local_path = Path(settings.LOCAL_STORAGE_PATH)
        self.upload_container = settings.DOCGEN_STORAGE_CONTAINER
        self.export_container = settings.DOCGEN_EXPORT_CONTAINER

        # Ensure local directories exist
        if self.use_local:
            (self.local_path / "uploads").mkdir(parents=True, exist_ok=True)
            (self.local_path / "exports").mkdir(parents=True, exist_ok=True)

        # Azure client (initialized lazily)
        self._blob_service_client = None

    @property
    def blob_service_client(self):
        """Get Azure Blob Service Client (lazy initialization)."""
        if not self.use_local and self._blob_service_client is None:
            try:
                from azure.storage.blob import BlobServiceClient
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION_STRING
                )
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob client: {e}")
                raise
        return self._blob_service_client

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        batch_id: str,
        is_export: bool = False,
    ) -> Tuple[str, str]:
        """
        Upload a file to storage.

        Returns:
            Tuple of (storage_url, file_hash)
        """
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Generate unique storage path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{uuid4().hex[:8]}_{filename}"

        if is_export:
            storage_path = f"exports/{batch_id}/{unique_filename}"
        else:
            storage_path = f"uploads/{batch_id}/{unique_filename}"

        if self.use_local:
            return await self._upload_local(file_content, storage_path), file_hash
        else:
            return await self._upload_azure(
                file_content, storage_path, content_type, is_export
            ), file_hash

    async def _upload_local(self, file_content: bytes, storage_path: str) -> str:
        """Upload file to local storage."""
        full_path = self.local_path / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_content)

        logger.info(f"Uploaded file to local storage: {full_path}")
        return str(full_path)

    async def _upload_azure(
        self,
        file_content: bytes,
        storage_path: str,
        content_type: str,
        is_export: bool = False,
    ) -> str:
        """Upload file to Azure Blob Storage."""
        container = self.export_container if is_export else self.upload_container

        try:
            container_client = self.blob_service_client.get_container_client(container)

            # Create container if not exists
            if not container_client.exists():
                container_client.create_container()

            blob_client = container_client.get_blob_client(storage_path)
            blob_client.upload_blob(
                file_content,
                content_settings={"content_type": content_type},
                overwrite=True,
            )

            logger.info(f"Uploaded file to Azure Blob: {container}/{storage_path}")
            return blob_client.url

        except Exception as e:
            logger.error(f"Azure upload failed: {e}")
            raise

    async def download_file(self, storage_url: str) -> bytes:
        """Download a file from storage."""
        if self.use_local or storage_url.startswith("/"):
            return await self._download_local(storage_url)
        else:
            return await self._download_azure(storage_url)

    async def _download_local(self, file_path: str) -> bytes:
        """Download file from local storage."""
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def _download_azure(self, blob_url: str) -> bytes:
        """Download file from Azure Blob Storage."""
        # Parse container and blob path from URL
        # URL format: https://<account>.blob.core.windows.net/<container>/<path>
        from urllib.parse import urlparse
        parsed = urlparse(blob_url)
        path_parts = parsed.path.lstrip("/").split("/", 1)
        container = path_parts[0]
        blob_path = path_parts[1] if len(path_parts) > 1 else ""

        container_client = self.blob_service_client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_path)

        return blob_client.download_blob().readall()

    async def delete_file(self, storage_url: str) -> bool:
        """Delete a file from storage."""
        try:
            if self.use_local or storage_url.startswith("/"):
                os.remove(storage_url)
            else:
                from urllib.parse import urlparse
                parsed = urlparse(storage_url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                container = path_parts[0]
                blob_path = path_parts[1] if len(path_parts) > 1 else ""

                container_client = self.blob_service_client.get_container_client(container)
                blob_client = container_client.get_blob_client(blob_path)
                blob_client.delete_blob()

            logger.info(f"Deleted file: {storage_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {storage_url}: {e}")
            return False

    async def get_download_url(
        self,
        storage_url: str,
        expiry_hours: int = 24,
    ) -> str:
        """Get a download URL (with SAS token for Azure)."""
        if self.use_local or storage_url.startswith("/"):
            # For local, return the path (frontend should handle download)
            return storage_url
        else:
            # Generate SAS token for Azure
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from urllib.parse import urlparse

            parsed = urlparse(storage_url)
            path_parts = parsed.path.lstrip("/").split("/", 1)
            container = path_parts[0]
            blob_path = path_parts[1] if len(path_parts) > 1 else ""

            # Get account name and key
            account_name = parsed.netloc.split(".")[0]

            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container,
                blob_name=blob_path,
                account_key=self._get_account_key(),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
            )

            return f"{storage_url}?{sas_token}"

    def _get_account_key(self) -> str:
        """Extract account key from connection string."""
        conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
        for part in conn_str.split(";"):
            if part.startswith("AccountKey="):
                return part[11:]
        raise ValueError("AccountKey not found in connection string")

    async def cleanup_temp_files(self, batch_id: str) -> None:
        """Clean up temporary files for a batch."""
        temp_dir = Path(settings.TEMP_DIR) / batch_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp files for batch: {batch_id}")


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
