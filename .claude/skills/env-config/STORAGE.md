# Storage Abstraction Patterns

## Overview

Same code, different storage backends based on environment:
- **Local**: File system (`./data/`)
- **Azure**: Blob Storage / ADLS Gen2
- **AWS**: S3

## Abstract Storage Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional


class StorageBackend(ABC):
    """Abstract storage interface."""

    @abstractmethod
    def read(self, path: str) -> bytes:
        """Read file contents."""
        pass

    @abstractmethod
    def write(self, path: str, data: bytes) -> None:
        """Write file contents."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    def list(self, prefix: str = "") -> list[str]:
        """List files with optional prefix."""
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete a file."""
        pass
```

## Local Storage Implementation

```python
class LocalStorage(StorageBackend):
    """Local file system storage."""

    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, path: str) -> Path:
        return self.base_path / path

    def read(self, path: str) -> bytes:
        return self._full_path(path).read_bytes()

    def write(self, path: str, data: bytes) -> None:
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    def list(self, prefix: str = "") -> list[str]:
        search_path = self._full_path(prefix) if prefix else self.base_path
        if not search_path.exists():
            return []
        return [str(p.relative_to(self.base_path)) for p in search_path.rglob("*") if p.is_file()]

    def delete(self, path: str) -> None:
        self._full_path(path).unlink(missing_ok=True)
```

## Azure Blob Storage Implementation

```python
from azure.storage.blob import BlobServiceClient


class AzureStorage(StorageBackend):
    """Azure Blob Storage backend."""

    def __init__(self, connection_string: str, container: str):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = self.client.get_container_client(container)

    def read(self, path: str) -> bytes:
        blob = self.container.get_blob_client(path)
        return blob.download_blob().readall()

    def write(self, path: str, data: bytes) -> None:
        blob = self.container.get_blob_client(path)
        blob.upload_blob(data, overwrite=True)

    def exists(self, path: str) -> bool:
        blob = self.container.get_blob_client(path)
        return blob.exists()

    def list(self, prefix: str = "") -> list[str]:
        blobs = self.container.list_blobs(name_starts_with=prefix)
        return [blob.name for blob in blobs]

    def delete(self, path: str) -> None:
        blob = self.container.get_blob_client(path)
        blob.delete_blob()
```

## AWS S3 Implementation

```python
import boto3
from botocore.exceptions import ClientError


class S3Storage(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(self, bucket: str, region: str = "us-east-1"):
        self.s3 = boto3.client("s3", region_name=region)
        self.bucket = bucket

    def read(self, path: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=path)
        return response["Body"].read()

    def write(self, path: str, data: bytes) -> None:
        self.s3.put_object(Bucket=self.bucket, Key=path, Body=data)

    def exists(self, path: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False

    def list(self, prefix: str = "") -> list[str]:
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]

    def delete(self, path: str) -> None:
        self.s3.delete_object(Bucket=self.bucket, Key=path)
```

## Storage Factory

```python
from functools import lru_cache


@lru_cache()
def get_storage() -> StorageBackend:
    """Get storage backend based on environment config."""
    from app.config import get_settings

    settings = get_settings()

    if settings.STORAGE_TYPE == "local":
        return LocalStorage(settings.STORAGE_PATH)

    elif settings.STORAGE_TYPE == "azure":
        return AzureStorage(
            connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
            container=settings.AZURE_STORAGE_CONTAINER,
        )

    elif settings.STORAGE_TYPE == "s3":
        return S3Storage(
            bucket=settings.AWS_S3_BUCKET,
            region=settings.AWS_REGION,
        )

    raise ValueError(f"Unknown storage type: {settings.STORAGE_TYPE}")
```

## Usage Example

```python
# Same code works everywhere!
storage = get_storage()

# Write data
storage.write("claims/claim_001.json", json.dumps(claim_data).encode())

# Read data
data = json.loads(storage.read("claims/claim_001.json"))

# List files
files = storage.list("claims/")

# Check existence
if storage.exists("claims/claim_001.json"):
    storage.delete("claims/claim_001.json")
```

## Environment Configuration

### Local Development
```bash
STORAGE_TYPE=local
STORAGE_PATH=./data
```

### Azure Production
```bash
STORAGE_TYPE=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=raw
```

### AWS Production
```bash
STORAGE_TYPE=s3
AWS_S3_BUCKET=my-bucket
AWS_REGION=us-east-1
```

## Medallion Architecture Pattern

```python
class MedallionStorage:
    """Storage with Bronze/Silver/Gold layers."""

    def __init__(self):
        self.storage = get_storage()
        self.settings = get_settings()

    @property
    def bronze_prefix(self) -> str:
        return self.settings.BRONZE_PATH or "bronze/"

    @property
    def silver_prefix(self) -> str:
        return self.settings.SILVER_PATH or "silver/"

    @property
    def gold_prefix(self) -> str:
        return self.settings.GOLD_PATH or "gold/"

    def write_bronze(self, filename: str, data: bytes) -> None:
        self.storage.write(f"{self.bronze_prefix}{filename}", data)

    def read_silver(self, filename: str) -> bytes:
        return self.storage.read(f"{self.silver_prefix}{filename}")

    def list_gold(self) -> list[str]:
        return self.storage.list(self.gold_prefix)
```

## Testing with Local Storage

```python
import pytest
from unittest.mock import patch


@pytest.fixture
def local_storage(tmp_path):
    """Use temporary directory for tests."""
    with patch.dict(os.environ, {"STORAGE_TYPE": "local", "STORAGE_PATH": str(tmp_path)}):
        from app.storage import get_storage
        get_storage.cache_clear()  # Clear cached instance
        yield get_storage()


def test_write_read(local_storage):
    local_storage.write("test.txt", b"hello")
    assert local_storage.read("test.txt") == b"hello"
```
