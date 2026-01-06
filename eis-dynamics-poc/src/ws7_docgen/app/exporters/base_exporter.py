"""Base exporter class for document exports."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.document import ExportFormat, ExportResult, ProcessedBatch
from app.services.storage_service import get_storage_service


class BaseExporter(ABC):
    """Base class for document exporters."""

    def __init__(self, format: ExportFormat):
        self.format = format
        self.storage_service = get_storage_service()

    @abstractmethod
    async def export(
        self,
        batch: ProcessedBatch,
        template: Optional[str] = None,
        include_raw_data: bool = False,
    ) -> ExportResult:
        """
        Generate export for the given batch.

        Args:
            batch: Processed batch with extraction results
            template: Template name to use
            include_raw_data: Include raw extraction data

        Returns:
            ExportResult with file location
        """
        pass

    def _get_filename(self, batch: ProcessedBatch, extension: str) -> str:
        """Generate filename for export."""
        claim_number = batch.claim_number or str(batch.batch_id)[:8]
        return f"claim_{claim_number}_{self.format.value}.{extension}"
