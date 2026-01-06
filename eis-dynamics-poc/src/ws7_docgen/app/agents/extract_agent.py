"""Extraction Agent - Extract data from documents using AI."""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from app.config import settings
from app.models.document import (
    DocumentType,
    ExtractedLineItem,
    ExtractionResult,
    UploadedDocument,
)
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


EXTRACTION_SYSTEM_PROMPT = """You are an expert document extraction specialist for pet insurance claims.
Your task is to extract structured data from veterinary invoices, medical receipts, and related documents.

Extract the following information when available:
1. Provider Information: name, address, phone, license number
2. Patient/Pet Information: name, species, breed, age, owner name
3. Service Information: date, invoice number, diagnosis, treatment notes
4. Financial Information: line items with descriptions, quantities, prices; subtotal, tax, total
5. Flags: emergency visit, follow-up visit

Return a JSON object with the extracted data. Use null for fields that cannot be determined.
For confidence scores, use 0.0-1.0 where 1.0 is highest confidence.

Important:
- Extract line items as an array with description, quantity, unit_price, total_amount
- Parse dates in ISO format (YYYY-MM-DD)
- Parse amounts as numbers without currency symbols
- Flag the document type (vet_invoice, medical_receipt, lab_results, police_report, photo_evidence, prescription, other)
"""

EXTRACTION_USER_PROMPT = """Extract structured data from the following document text.
Return a valid JSON object with the extracted information.

Document text:
{document_text}

Return format:
{{
    "document_type": "vet_invoice|medical_receipt|lab_results|police_report|photo_evidence|prescription|other",
    "provider": {{
        "name": "string or null",
        "address": "string or null",
        "phone": "string or null",
        "license": "string or null"
    }},
    "patient": {{
        "name": "string or null",
        "species": "string or null",
        "breed": "string or null",
        "age": "string or null",
        "owner_name": "string or null"
    }},
    "service": {{
        "date": "YYYY-MM-DD or null",
        "invoice_number": "string or null",
        "diagnosis": "string or null",
        "diagnosis_code": "string or null",
        "treatment_notes": "string or null"
    }},
    "line_items": [
        {{
            "description": "string",
            "diagnosis_code": "string or null",
            "procedure_code": "string or null",
            "quantity": 1,
            "unit_price": 0.00,
            "total_amount": 0.00,
            "service_date": "YYYY-MM-DD or null"
        }}
    ],
    "financials": {{
        "subtotal": 0.00,
        "tax": 0.00,
        "total_amount": 0.00,
        "amount_paid": 0.00,
        "balance_due": 0.00,
        "payment_method": "string or null"
    }},
    "flags": {{
        "is_emergency": false,
        "is_follow_up": false
    }},
    "confidence_score": 0.85
}}
"""


class ExtractAgent:
    """Agent for extracting structured data from documents."""

    def __init__(self):
        self.ai_provider = settings.AI_PROVIDER

        if self.ai_provider == "claude":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.CLAUDE_MODEL
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL

    async def extract(self, document: UploadedDocument) -> ExtractionResult:
        """Extract structured data from a document."""
        logger.info(f"Extracting data from: {document.original_filename}")

        # Get document content
        storage_service = get_storage_service()
        storage_url = document.local_path or document.blob_url

        if not storage_url:
            raise ValueError(f"No storage URL for document {document.id}")

        # Download document
        content = await storage_service.download_file(storage_url)

        # Extract text from document
        document_text = await self._extract_text(content, document.content_type)

        if not document_text:
            logger.warning(f"No text extracted from {document.original_filename}")
            return ExtractionResult(
                document_id=document.id,
                document_type=document.document_type or DocumentType.OTHER,
                confidence_score=0.0,
                raw_text="",
            )

        # Use AI to extract structured data
        extraction_data = await self._ai_extract(document_text)

        # Parse into ExtractionResult
        result = self._parse_extraction(document.id, extraction_data, document_text)

        logger.info(
            f"Extraction complete for {document.original_filename}: "
            f"type={result.document_type.value}, confidence={result.confidence_score:.2f}"
        )

        return result

    async def _extract_text(self, content: bytes, content_type: str) -> str:
        """Extract text from document content."""
        # For PDFs, use OCR or PDF text extraction
        if content_type == "application/pdf":
            return await self._extract_pdf_text(content)

        # For images, use OCR
        if content_type.startswith("image/"):
            return await self._extract_image_text(content)

        # For Word documents
        if "wordprocessingml" in content_type or content_type == "application/msword":
            return await self._extract_word_text(content)

        # Default: try to decode as text
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return ""

    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF."""
        try:
            import io
            # Try PyPDF2 first (fast, no OCR)
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    return text
            except Exception:
                pass

            # Fall back to Azure Document Intelligence (OCR)
            return await self._azure_ocr(content)

        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""

    async def _extract_image_text(self, content: bytes) -> str:
        """Extract text from image using OCR."""
        return await self._azure_ocr(content)

    async def _extract_word_text(self, content: bytes) -> str:
        """Extract text from Word document."""
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Word text extraction failed: {e}")
            return ""

    async def _azure_ocr(self, content: bytes) -> str:
        """Use Azure Document Intelligence for OCR."""
        if not settings.AZURE_FORM_RECOGNIZER_ENDPOINT:
            logger.warning("Azure Form Recognizer not configured, using mock OCR")
            return "[OCR not configured - mock text for testing]"

        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential

            client = DocumentAnalysisClient(
                endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY),
            )

            poller = client.begin_analyze_document("prebuilt-document", content)
            result = poller.result()

            text = ""
            for page in result.pages:
                for line in page.lines:
                    text += line.content + "\n"

            return text

        except Exception as e:
            logger.error(f"Azure OCR failed: {e}")
            return ""

    async def _ai_extract(self, document_text: str) -> Dict[str, Any]:
        """Use AI to extract structured data from text."""
        prompt = EXTRACTION_USER_PROMPT.format(document_text=document_text[:10000])

        try:
            if self.ai_provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=EXTRACTION_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )
                response_text = response.choices[0].message.content

            # Parse JSON from response
            # Try to find JSON in response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            return json.loads(json_str.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return {}

    def _parse_extraction(
        self,
        document_id: str,
        data: Dict[str, Any],
        raw_text: str,
    ) -> ExtractionResult:
        """Parse AI extraction response into ExtractionResult."""
        # Parse document type
        doc_type_str = data.get("document_type", "other")
        try:
            doc_type = DocumentType(doc_type_str)
        except ValueError:
            doc_type = DocumentType.OTHER

        # Parse provider info
        provider = data.get("provider", {}) or {}

        # Parse patient info
        patient = data.get("patient", {}) or {}

        # Parse service info
        service = data.get("service", {}) or {}

        # Parse service date
        service_date = None
        if service.get("date"):
            try:
                service_date = datetime.fromisoformat(service["date"])
            except (ValueError, TypeError):
                pass

        # Parse line items
        line_items = []
        for item in data.get("line_items", []) or []:
            try:
                line_item = ExtractedLineItem(
                    description=item.get("description", "Unknown"),
                    diagnosis_code=item.get("diagnosis_code"),
                    procedure_code=item.get("procedure_code"),
                    quantity=int(item.get("quantity", 1)),
                    unit_price=Decimal(str(item.get("unit_price", 0))),
                    total_amount=Decimal(str(item.get("total_amount", 0))),
                    confidence=0.8,
                )
                # Parse service date if present
                if item.get("service_date"):
                    try:
                        line_item.service_date = datetime.fromisoformat(item["service_date"])
                    except (ValueError, TypeError):
                        pass
                line_items.append(line_item)
            except Exception as e:
                logger.warning(f"Failed to parse line item: {e}")

        # Parse financials
        financials = data.get("financials", {}) or {}

        # Parse flags
        flags = data.get("flags", {}) or {}

        return ExtractionResult(
            document_id=document_id,
            document_type=doc_type,
            # Provider
            provider_name=provider.get("name"),
            provider_address=provider.get("address"),
            provider_phone=provider.get("phone"),
            provider_license=provider.get("license"),
            # Patient
            patient_name=patient.get("name"),
            pet_species=patient.get("species"),
            pet_breed=patient.get("breed"),
            pet_age=patient.get("age"),
            owner_name=patient.get("owner_name"),
            # Service
            service_date=service_date,
            invoice_number=service.get("invoice_number"),
            diagnosis=service.get("diagnosis"),
            diagnosis_code=service.get("diagnosis_code"),
            treatment_notes=service.get("treatment_notes"),
            # Line items
            line_items=line_items,
            # Financials
            subtotal=Decimal(str(financials.get("subtotal", 0))) if financials.get("subtotal") else None,
            tax=Decimal(str(financials.get("tax", 0))) if financials.get("tax") else None,
            total_amount=Decimal(str(financials.get("total_amount", 0))) if financials.get("total_amount") else None,
            amount_paid=Decimal(str(financials.get("amount_paid", 0))) if financials.get("amount_paid") else None,
            balance_due=Decimal(str(financials.get("balance_due", 0))) if financials.get("balance_due") else None,
            payment_method=financials.get("payment_method"),
            # Flags
            is_emergency=flags.get("is_emergency", False),
            is_follow_up=flags.get("is_follow_up", False),
            # Metadata
            raw_text=raw_text[:5000],  # Truncate for storage
            confidence_score=data.get("confidence_score", 0.7),
            extraction_model=self.model,
        )
