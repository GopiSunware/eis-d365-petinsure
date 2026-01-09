"""CSV Exporter for claim documents."""

import csv
import logging
import os
from datetime import datetime, timedelta
from uuid import uuid4

from app.config import DATA_DIR
from app.models.document import ExportFormat, ExportResult, ProcessedBatch

logger = logging.getLogger(__name__)


class CSVExporter:
    """Generate CSV exports for claim documents."""

    async def export(
        self,
        batch: ProcessedBatch,
        template: str = "claim_data",
        include_raw_data: bool = False,
    ) -> ExportResult:
        """Generate CSV export."""
        export_id = uuid4()
        filename = f"claim_{batch.batch_id}_{template}.csv"
        output_dir = str(DATA_DIR / "exports")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)

            if template == "line_items":
                # Export line items
                writer.writerow(['Item', 'Description', 'Amount', 'Category'])
                if batch.mapped_claim and isinstance(batch.mapped_claim, dict):
                    line_items = batch.mapped_claim.get('line_items', [])
                    if isinstance(line_items, list):
                        for item in line_items:
                            if isinstance(item, dict):
                                writer.writerow([
                                    item.get('service_code', ''),
                                    item.get('description', ''),
                                    item.get('amount', 0),
                                    item.get('category', ''),
                                ])
            else:
                # Full claim data export
                writer.writerow(['Field', 'Value'])
                writer.writerow(['Batch ID', str(batch.batch_id)])
                writer.writerow(['Created', batch.created_at.strftime('%Y-%m-%d %H:%M')])
                writer.writerow(['Status', batch.status.value])
                writer.writerow(['', ''])

                # Documents
                writer.writerow(['Documents', ''])
                for doc_item in batch.documents:
                    writer.writerow(['', doc_item.original_filename])
                writer.writerow(['', ''])

                # Claim data
                if batch.mapped_claim:
                    writer.writerow(['Claim Details', ''])
                    if isinstance(batch.mapped_claim, dict):
                        for key, value in batch.mapped_claim.items():
                            if value and not key.startswith('_'):
                                writer.writerow([key, str(value)])
                    writer.writerow(['', ''])

                # Billing
                if batch.billing:
                    writer.writerow(['Billing Summary', ''])
                    writer.writerow(['Claim Amount', f'${batch.billing.claim_amount:.2f}'])
                    writer.writerow(['Deductible Applied', f'${batch.billing.deductible_applied:.2f}'])
                    writer.writerow(['Final Payout', f'${batch.billing.final_payout:.2f}'])
                    writer.writerow(['', ''])

                # AI Decision
                if batch.ai_decision:
                    writer.writerow(['AI Analysis', ''])
                    writer.writerow(['Decision', batch.ai_decision])
                    writer.writerow(['Confidence', f'{(batch.ai_confidence or 0) * 100:.0f}%'])
                    if batch.ai_reasoning:
                        writer.writerow(['Reasoning', batch.ai_reasoning])

        logger.info(f"Generated CSV export: {output_path}")

        return ExportResult(
            export_id=export_id,
            batch_id=batch.batch_id,
            format=ExportFormat.CSV,
            filename=filename,
            local_path=output_path,
            file_size=os.path.getsize(output_path),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
