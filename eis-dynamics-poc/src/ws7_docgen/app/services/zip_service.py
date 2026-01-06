"""ZIP file extraction service."""

import logging
import os
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

import aiofiles

from app.config import settings

logger = logging.getLogger(__name__)


class ZipExtractionError(Exception):
    """Error during ZIP extraction."""
    pass


class ZipService:
    """Service for handling ZIP file extraction."""

    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.max_zip_size = settings.MAX_ZIP_SIZE_MB * 1024 * 1024  # Convert to bytes
        self.max_files = settings.MAX_FILES_PER_ZIP
        self.allowed_extensions = [
            ext.lower() for ext in settings.ALLOWED_EXTENSIONS
            if ext.lower() != ".zip"  # Don't allow nested ZIPs
        ]

    async def extract_zip(
        self,
        zip_content: bytes,
        batch_id: str,
        original_filename: str,
    ) -> List[Tuple[str, str, bytes]]:
        """
        Extract a ZIP file and return list of extracted files.

        Args:
            zip_content: ZIP file content as bytes
            batch_id: Batch ID for organizing extracted files
            original_filename: Original ZIP filename

        Returns:
            List of tuples: (filename, content_type, file_content)

        Raises:
            ZipExtractionError: If extraction fails or validation fails
        """
        # Validate ZIP size
        if len(zip_content) > self.max_zip_size:
            raise ZipExtractionError(
                f"ZIP file exceeds maximum size of {settings.MAX_ZIP_SIZE_MB}MB"
            )

        # Create temp directory for extraction
        extract_dir = self.temp_dir / batch_id / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Write ZIP to temp file
        temp_zip_path = self.temp_dir / batch_id / f"{uuid4().hex}.zip"
        temp_zip_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(temp_zip_path, "wb") as f:
            await f.write(zip_content)

        try:
            extracted_files = []

            with zipfile.ZipFile(temp_zip_path, "r") as zf:
                # Get list of files (exclude directories)
                file_list = [
                    f for f in zf.namelist()
                    if not f.endswith("/") and not f.startswith("__MACOSX")
                ]

                # Validate file count
                if len(file_list) > self.max_files:
                    raise ZipExtractionError(
                        f"ZIP contains {len(file_list)} files, "
                        f"maximum allowed is {self.max_files}"
                    )

                if len(file_list) == 0:
                    raise ZipExtractionError("ZIP file is empty")

                logger.info(
                    f"Extracting {len(file_list)} files from ZIP: {original_filename}"
                )

                for file_info in zf.infolist():
                    # Skip directories and Mac metadata
                    if file_info.is_dir() or file_info.filename.startswith("__MACOSX"):
                        continue

                    filename = Path(file_info.filename).name
                    extension = Path(filename).suffix.lower()

                    # Skip unsupported file types
                    if extension not in self.allowed_extensions:
                        logger.warning(
                            f"Skipping unsupported file type: {filename} ({extension})"
                        )
                        continue

                    # Extract file content
                    file_content = zf.read(file_info.filename)

                    # Determine content type
                    content_type = self._get_content_type(extension)

                    extracted_files.append((filename, content_type, file_content))

                    logger.debug(f"Extracted: {filename} ({len(file_content)} bytes)")

            if not extracted_files:
                raise ZipExtractionError(
                    "No supported files found in ZIP. "
                    f"Supported formats: {', '.join(self.allowed_extensions)}"
                )

            logger.info(
                f"Successfully extracted {len(extracted_files)} files from ZIP"
            )
            return extracted_files

        except zipfile.BadZipFile:
            raise ZipExtractionError("Invalid or corrupted ZIP file")
        except Exception as e:
            if isinstance(e, ZipExtractionError):
                raise
            logger.error(f"ZIP extraction failed: {e}")
            raise ZipExtractionError(f"Failed to extract ZIP: {str(e)}")
        finally:
            # Clean up temp ZIP file
            if temp_zip_path.exists():
                os.remove(temp_zip_path)

    def _get_content_type(self, extension: str) -> str:
        """Get content type for file extension."""
        content_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".heic": "image/heic",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return content_types.get(extension, "application/octet-stream")

    async def cleanup(self, batch_id: str) -> None:
        """Clean up extracted files for a batch."""
        import shutil
        extract_dir = self.temp_dir / batch_id
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
            logger.info(f"Cleaned up extracted files for batch: {batch_id}")

    def validate_zip(self, zip_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate a ZIP file without extracting.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check size
        if len(zip_content) > self.max_zip_size:
            return False, f"ZIP file exceeds maximum size of {settings.MAX_ZIP_SIZE_MB}MB"

        try:
            import io
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
                # Check for corruption
                bad_file = zf.testzip()
                if bad_file:
                    return False, f"Corrupted file in ZIP: {bad_file}"

                # Count valid files
                valid_files = [
                    f for f in zf.namelist()
                    if not f.endswith("/")
                    and not f.startswith("__MACOSX")
                    and Path(f).suffix.lower() in self.allowed_extensions
                ]

                if len(valid_files) == 0:
                    return False, "No supported files found in ZIP"

                if len(valid_files) > self.max_files:
                    return False, f"ZIP contains too many files ({len(valid_files)} > {self.max_files})"

                return True, None

        except zipfile.BadZipFile:
            return False, "Invalid or corrupted ZIP file"
        except Exception as e:
            return False, f"Failed to validate ZIP: {str(e)}"


# Singleton instance
_zip_service: Optional[ZipService] = None


def get_zip_service() -> ZipService:
    """Get ZIP service singleton."""
    global _zip_service
    if _zip_service is None:
        _zip_service = ZipService()
    return _zip_service
