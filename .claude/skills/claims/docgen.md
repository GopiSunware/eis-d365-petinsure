# Document Generation & AI Processing Skill

AI-powered document extraction, analysis, and generation for claims processing.

## Document AI Capabilities

### 1. Invoice Extraction

Extract structured data from veterinary invoices.

**Endpoint**: `POST http://localhost:8007/api/v1/extract/invoice`

```bash
curl -X POST "http://localhost:8007/api/v1/extract/invoice" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@vet_invoice.pdf"
```

**Response**:
```json
{
  "extraction_id": "EXT-001",
  "confidence": 0.92,
  "extracted_data": {
    "provider_name": "Happy Paws Veterinary Clinic",
    "provider_id": "PROV-001",
    "patient_name": "Max",
    "service_date": "2024-12-15",
    "line_items": [
      {"description": "Office Visit", "amount": 75.00},
      {"description": "X-Ray - Hip", "amount": 250.00},
      {"description": "Pain Medication", "amount": 45.00}
    ],
    "total_amount": 370.00,
    "diagnosis": "Hip dysplasia evaluation"
  }
}
```

### 2. Medical Record Extraction

Extract clinical data from veterinary medical records.

**Endpoint**: `POST http://localhost:8007/api/v1/extract/medical-record`

```bash
curl -X POST "http://localhost:8007/api/v1/extract/medical-record" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@medical_notes.pdf"
```

**Response**:
```json
{
  "extraction_id": "EXT-002",
  "confidence": 0.88,
  "extracted_data": {
    "patient_name": "Max",
    "species": "Canine",
    "breed": "Golden Retriever",
    "visit_date": "2024-12-15",
    "chief_complaint": "Limping on right hind leg",
    "diagnosis": "Hip dysplasia - moderate",
    "diagnosis_code": "M16.1",
    "treatment_plan": [
      "Pain management with NSAIDs",
      "Weight management",
      "Physical therapy recommendation"
    ],
    "medications_prescribed": [
      {"name": "Carprofen", "dosage": "75mg", "frequency": "twice daily"}
    ],
    "follow_up": "4 weeks"
  }
}
```

### 3. FNOL (First Notice of Loss) Processing

AI extraction from initial claim submissions.

**Endpoint**: `POST http://localhost:8001/api/v1/fnol/extract`

```bash
curl -X POST "http://localhost:8001/api/v1/fnol/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "My dog Max ate chocolate yesterday and started vomiting. Took him to emergency vet at 2am. They gave him IV fluids and medication.",
    "customer_id": "CUST-001"
  }'
```

**Response**:
```json
{
  "fnol_id": "FNOL-001",
  "extracted": {
    "incident_type": "toxin_ingestion",
    "substance": "chocolate",
    "pet_name": "Max",
    "species": "dog",
    "symptoms": ["vomiting"],
    "treatment_location": "emergency_vet",
    "treatments": ["IV fluids", "medication"],
    "urgency": "emergency",
    "estimated_diagnosis_code": "T65.8"
  },
  "suggested_claim_type": "emergency",
  "confidence": 0.91
}
```

## Batch Processing

### Create Document Batch

Process multiple documents for a single claim.

**Endpoint**: `POST http://localhost:8007/api/v1/batches/`

```bash
curl -X POST "http://localhost:8007/api/v1/batches/" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_name": "Claim CLM-2024-001 Documents",
    "claim_id": "CLM-2024-001",
    "documents": [
      {"type": "invoice", "filename": "invoice.pdf"},
      {"type": "medical_record", "filename": "records.pdf"},
      {"type": "lab_results", "filename": "bloodwork.pdf"}
    ]
  }'
```

**Response**:
```json
{
  "batch_id": "BATCH-001",
  "status": "PROCESSING",
  "document_count": 3,
  "estimated_completion": "2024-12-15T10:35:00Z"
}
```

### Check Batch Status

```bash
curl "http://localhost:8007/api/v1/batches/BATCH-001"
```

**Response**:
```json
{
  "batch_id": "BATCH-001",
  "status": "COMPLETED",
  "documents": [
    {"type": "invoice", "status": "extracted", "confidence": 0.94},
    {"type": "medical_record", "status": "extracted", "confidence": 0.89},
    {"type": "lab_results", "status": "extracted", "confidence": 0.92}
  ],
  "cross_validation": {
    "pet_name_match": true,
    "date_consistency": true,
    "amount_verified": true
  }
}
```

## Document Types Supported

| Type | Extension | Extraction Fields |
|------|-----------|-------------------|
| Invoice | PDF, JPG, PNG | Provider, amounts, line items, dates |
| Medical Record | PDF | Diagnosis, treatments, medications |
| Lab Results | PDF | Test values, reference ranges, flags |
| Prescription | PDF, JPG | Medication, dosage, provider, DEA# |
| Referral Letter | PDF | Specialist, reason, urgency |

## Document Validation

### Cross-Document Validation

Compare extracted data across documents for consistency.

```bash
curl -X POST "http://localhost:8007/api/v1/validate/cross-document" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "BATCH-001",
    "validations": ["pet_name", "dates", "amounts", "diagnosis"]
  }'
```

**Response**:
```json
{
  "valid": false,
  "discrepancies": [
    {
      "field": "service_date",
      "invoice": "2024-12-15",
      "medical_record": "2024-12-14",
      "severity": "MEDIUM"
    }
  ],
  "confidence_score": 0.78
}
```

## Document Generation

### Generate EOB (Explanation of Benefits)

```bash
curl -X POST "http://localhost:8007/api/v1/generate/eob" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2024-001",
    "decision": "APPROVED",
    "covered_amount": 1200,
    "deductible_applied": 250,
    "copay_percentage": 20,
    "payment_amount": 760
  }'
```

### Generate Denial Letter

```bash
curl -X POST "http://localhost:8007/api/v1/generate/denial-letter" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2024-002",
    "denial_reason": "PRE_EXISTING_CONDITION",
    "diagnosis_code": "M16.1",
    "policy_reference": "Section 4.2 - Pre-existing Conditions"
  }'
```

## AI Models Used

| Task | Model | Purpose |
|------|-------|---------|
| OCR | Azure Document Intelligence | Text extraction from images |
| Entity Extraction | GPT-4 | Structured data from text |
| Classification | Custom NER | Document type identification |
| Validation | Rule Engine + LLM | Cross-reference checking |

## Integration with Pipeline

DocGen integrates with the agent pipeline:

```
Document Upload → DocGen Service → Bronze Agent
                       ↓
              Extracted Data JSON
                       ↓
              Validation Checks
                       ↓
              Enriched Claim Data
```

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/extract/invoice` | Extract invoice data |
| `POST /api/v1/extract/medical-record` | Extract medical records |
| `POST /api/v1/fnol/extract` | FNOL AI extraction |
| `POST /api/v1/batches/` | Create document batch |
| `GET /api/v1/batches/{id}` | Get batch status |
| `POST /api/v1/validate/cross-document` | Cross-document validation |
| `POST /api/v1/generate/eob` | Generate EOB |
| `POST /api/v1/generate/denial-letter` | Generate denial letter |

## Files

```
eis-dynamics-poc/src/ws7_docgen/
├── app/
│   ├── services/
│   │   ├── extraction_service.py
│   │   ├── ocr_service.py
│   │   └── generation_service.py
│   ├── routers/
│   │   ├── extract.py
│   │   ├── batches.py
│   │   └── generate.py
│   └── models/
│       └── document_models.py
└── templates/
    ├── eob_template.html
    └── denial_letter_template.html
```
