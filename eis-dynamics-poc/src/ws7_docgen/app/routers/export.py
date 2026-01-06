"""Export router for document export generation."""

import logging
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse

from app.config import settings
from app.models.document import ExportFormat, ExportResult, ProcessingStatus
from app.models.api import ExportRequest, ExportResponse, TemplateInfo, TemplateListResponse
from app.routers.upload import get_batch
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory export storage (replace with database in production)
_exports: dict[str, ExportResult] = {}


@router.post("/export", response_model=ExportResponse)
async def generate_exports(request: ExportRequest):
    """
    Generate exports in specified formats.

    Supported formats: PDF, Word (DOCX), CSV
    """
    batch = get_batch(str(request.batch_id))
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {request.batch_id} not found",
        )

    if batch.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Processing not complete. Current status: {batch.status.value}",
        )

    storage_service = get_storage_service()
    exports = []
    download_urls = {}

    for fmt in request.formats:
        try:
            logger.info(f"Generating {fmt.value} export for batch {request.batch_id}")

            if fmt == ExportFormat.PDF:
                from app.exporters.pdf_exporter import PDFExporter
                exporter = PDFExporter()
            elif fmt == ExportFormat.WORD:
                from app.exporters.word_exporter import WordExporter
                exporter = WordExporter()
            elif fmt == ExportFormat.CSV:
                from app.exporters.csv_exporter import CSVExporter
                exporter = CSVExporter()
            else:
                logger.warning(f"Unsupported export format: {fmt}")
                continue

            # Generate export
            export_result = await exporter.export(
                batch=batch,
                template=request.template,
                include_raw_data=request.include_raw_data,
            )

            # Store export result
            _exports[str(export_result.export_id)] = export_result
            exports.append(export_result)

            # Get download URL
            storage_url = export_result.local_path or export_result.blob_url
            if storage_url:
                download_url = await storage_service.get_download_url(
                    storage_url,
                    expiry_hours=settings.EXPORT_URL_EXPIRY_HOURS,
                )
                download_urls[fmt.value] = f"/api/v1/docgen/export/{export_result.export_id}/download"

            logger.info(f"Generated {fmt.value} export: {export_result.filename}")

        except Exception as e:
            logger.error(f"Failed to generate {fmt.value} export: {e}")
            # Continue with other formats

    if not exports:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate any exports",
        )

    return ExportResponse(
        batch_id=request.batch_id,
        exports=exports,
        download_urls=download_urls,
    )


@router.get("/export/{export_id}")
async def get_export_info(export_id: str):
    """Get information about an export."""
    export = _exports.get(export_id)
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export {export_id} not found",
        )

    return export


@router.get("/export/{export_id}/download")
async def download_export(export_id: str):
    """Download an exported file."""
    export = _exports.get(export_id)
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export {export_id} not found",
        )

    # Check expiry
    if export.expires_at and datetime.utcnow() > export.expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export has expired",
        )

    storage_url = export.local_path or export.blob_url
    if not storage_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found",
        )

    # Determine content type
    content_types = {
        ExportFormat.PDF: "application/pdf",
        ExportFormat.WORD: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.CSV: "text/csv",
    }
    content_type = content_types.get(export.format, "application/octet-stream")

    # For local storage, return file directly
    if export.local_path:
        return FileResponse(
            path=export.local_path,
            filename=export.filename,
            media_type=content_type,
        )

    # For Azure, stream the content
    storage_service = get_storage_service()
    content = await storage_service.download_file(storage_url)

    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{export.filename}"',
            "Content-Length": str(len(content)),
        },
    )


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates():
    """List available export templates."""
    templates = [
        # PDF Templates
        TemplateInfo(
            name="claim_summary",
            description="Complete claim summary with all details",
            format=ExportFormat.PDF,
        ),
        TemplateInfo(
            name="fraud_report",
            description="Fraud analysis report with indicators",
            format=ExportFormat.PDF,
        ),
        TemplateInfo(
            name="billing_summary",
            description="Financial breakdown and billing details",
            format=ExportFormat.PDF,
        ),

        # Word Templates
        TemplateInfo(
            name="claim_letter",
            description="Customer-facing claim letter",
            format=ExportFormat.WORD,
        ),
        TemplateInfo(
            name="adjuster_notes",
            description="Internal adjuster review document",
            format=ExportFormat.WORD,
        ),

        # CSV Templates
        TemplateInfo(
            name="claim_data",
            description="Full claim data export",
            format=ExportFormat.CSV,
        ),
        TemplateInfo(
            name="line_items",
            description="Itemized line items export",
            format=ExportFormat.CSV,
        ),
    ]

    return TemplateListResponse(templates=templates)


@router.delete("/export/{export_id}")
async def delete_export(export_id: str):
    """Delete an export and its file."""
    export = _exports.get(export_id)
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export {export_id} not found",
        )

    # Delete file
    storage_service = get_storage_service()
    storage_url = export.local_path or export.blob_url
    if storage_url:
        await storage_service.delete_file(storage_url)

    # Remove from storage
    del _exports[export_id]

    return {"message": f"Export {export_id} deleted successfully"}
