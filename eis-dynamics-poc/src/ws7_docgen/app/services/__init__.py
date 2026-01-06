"""DocGen Services."""

from app.services.storage_service import StorageService, get_storage_service
from app.services.zip_service import ZipService, get_zip_service

__all__ = [
    "StorageService",
    "get_storage_service",
    "ZipService",
    "get_zip_service",
]
