"""PDF Exporter for claim documents."""

import logging
import os
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.document import ExportFormat, ExportResult, ProcessedBatch

logger = logging.getLogger(__name__)


class PDFExporter:
    """Generate PDF exports for claim documents."""

    async def export(
        self,
        batch: ProcessedBatch,
        template: str = "claim_summary",
        include_raw_data: bool = False,
    ) -> ExportResult:
        """Generate PDF export."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
        except ImportError:
            logger.warning("reportlab not installed, using simple text-based PDF")
            return await self._export_simple(batch, template, include_raw_data)

        export_id = uuid4()
        filename = f"claim_{batch.batch_id}_{template}.pdf"
        output_dir = "/tmp/docgen/exports"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
        )
        story.append(Paragraph(f"Claim Processing Report", title_style))
        story.append(Spacer(1, 12))

        # Batch Info
        story.append(Paragraph(f"<b>Batch ID:</b> {batch.batch_id}", styles['Normal']))
        story.append(Paragraph(f"<b>Created:</b> {batch.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"<b>Status:</b> {batch.status.value}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Documents
        story.append(Paragraph("<b>Documents:</b>", styles['Heading2']))
        for doc_item in batch.documents:
            story.append(Paragraph(f"• {doc_item.original_filename}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Claim Data
        if batch.mapped_claim:
            story.append(Paragraph("<b>Claim Details:</b>", styles['Heading2']))
            claim = batch.mapped_claim
            if isinstance(claim, dict):
                for key, value in claim.items():
                    if value and not key.startswith('_'):
                        story.append(Paragraph(f"• <b>{key}:</b> {value}", styles['Normal']))
            story.append(Spacer(1, 12))

        # Billing
        if batch.billing:
            story.append(Paragraph("<b>Billing Summary:</b>", styles['Heading2']))
            story.append(Paragraph(f"• Claim Amount: ${batch.billing.claim_amount:.2f}", styles['Normal']))
            story.append(Paragraph(f"• Deductible Applied: ${batch.billing.deductible_applied:.2f}", styles['Normal']))
            story.append(Paragraph(f"• Final Payout: ${batch.billing.final_payout:.2f}", styles['Normal']))
            story.append(Spacer(1, 12))

        # AI Decision
        if batch.ai_decision:
            story.append(Paragraph("<b>AI Analysis:</b>", styles['Heading2']))
            story.append(Paragraph(f"• Decision: {batch.ai_decision}", styles['Normal']))
            story.append(Paragraph(f"• Confidence: {(batch.ai_confidence or 0) * 100:.0f}%", styles['Normal']))
            if batch.ai_reasoning:
                # Format the reasoning with line breaks
                reasoning = batch.ai_reasoning.replace('\\n', '<br/>')
                story.append(Paragraph(f"<b>Reasoning:</b><br/>{reasoning}", styles['Normal']))

        # Build PDF
        doc.build(story)

        logger.info(f"Generated PDF export: {output_path}")

        return ExportResult(
            export_id=export_id,
            batch_id=batch.batch_id,
            format=ExportFormat.PDF,
            filename=filename,
            local_path=output_path,
            file_size=os.path.getsize(output_path),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

    async def _export_simple(
        self,
        batch: ProcessedBatch,
        template: str,
        include_raw_data: bool,
    ) -> ExportResult:
        """Simple text-based export when reportlab is not available."""
        export_id = uuid4()
        filename = f"claim_{batch.batch_id}_{template}.txt"
        output_dir = "/tmp/docgen/exports"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        content = []
        content.append("=" * 60)
        content.append("CLAIM PROCESSING REPORT")
        content.append("=" * 60)
        content.append("")
        content.append(f"Batch ID: {batch.batch_id}")
        content.append(f"Created: {batch.created_at.strftime('%Y-%m-%d %H:%M')}")
        content.append(f"Status: {batch.status.value}")
        content.append("")

        content.append("Documents:")
        for doc_item in batch.documents:
            content.append(f"  - {doc_item.original_filename}")
        content.append("")

        if batch.mapped_claim:
            content.append("Claim Details:")
            claim = batch.mapped_claim
            if isinstance(claim, dict):
                for key, value in claim.items():
                    if value and not key.startswith('_'):
                        content.append(f"  - {key}: {value}")
            content.append("")

        if batch.billing:
            content.append("Billing Summary:")
            content.append(f"  - Claim Amount: ${batch.billing.claim_amount:.2f}")
            content.append(f"  - Deductible: ${batch.billing.deductible_applied:.2f}")
            content.append(f"  - Final Payout: ${batch.billing.final_payout:.2f}")
            content.append("")

        if batch.ai_decision:
            content.append("AI Analysis:")
            content.append(f"  - Decision: {batch.ai_decision}")
            content.append(f"  - Confidence: {(batch.ai_confidence or 0) * 100:.0f}%")
            if batch.ai_reasoning:
                content.append(f"  - Reasoning: {batch.ai_reasoning}")

        with open(output_path, 'w') as f:
            f.write('\n'.join(content))

        return ExportResult(
            export_id=export_id,
            batch_id=batch.batch_id,
            format=ExportFormat.PDF,
            filename=filename,
            local_path=output_path,
            file_size=os.path.getsize(output_path),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
