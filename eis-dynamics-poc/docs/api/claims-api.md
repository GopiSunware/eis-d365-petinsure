# Pet Claims API Reference (WS2)

Base URL: `/api/v1`

## Overview

The Pet Claims API handles veterinary expense claims for pet insurance policies. It provides AI-powered claim processing including vet invoice OCR, pre-existing condition detection, and fraud analysis.

## Endpoints

### Submit Pet Claim (FNOL)

Submit a First Notice of Loss for a pet veterinary expense.

```
POST /claims/fnol
```

#### Request Body

```json
{
  "description": "string (required) - Description of pet's condition/treatment",
  "date_of_service": "string (required) - ISO date (YYYY-MM-DD)",
  "policy_number": "string (required) - Format: PET-XX-XXXX-XXXXX",
  "pet_id": "string (required) - Pet identifier on policy",
  "condition_type": "string (required) - accident|illness|wellness|dental",
  "vet_clinic_name": "string (optional) - Veterinary clinic name",
  "amount_billed": "number (optional) - Total vet bill amount",
  "contact_phone": "string (optional) - Format: XXX-XXX-XXXX",
  "contact_email": "string (optional) - Valid email"
}
```

#### Example Request

```bash
curl -X POST http://localhost:8001/api/v1/claims/fnol \
  -H "Content-Type: application/json" \
  -d '{
    "description": "My golden retriever Max started limping yesterday after playing at the dog park. The vet did x-rays and diagnosed a torn CCL. They recommend TPLO surgery.",
    "date_of_service": "2024-06-15",
    "policy_number": "PET-IL-2024-00001",
    "pet_id": "PET-001",
    "condition_type": "accident",
    "vet_clinic_name": "Happy Paws Veterinary Clinic",
    "amount_billed": 4500.00,
    "contact_phone": "555-123-4567",
    "contact_email": "john.smith@example.com"
  }'
```

#### Response (201 Created)

```json
{
  "claim_number": "CLM-PET-2024-00001",
  "status": "submitted",
  "policy_id": "POL-PET-2024-001",
  "pet_id": "PET-001",
  "pet_name": "Max",
  "pet_breed": "Golden Retriever",
  "date_of_service": "2024-06-15",
  "date_reported": "2024-06-15T14:30:00Z",
  "condition_type": "accident",
  "ai_extraction": {
    "pet_name": "Max",
    "species": "dog",
    "breed": "Golden Retriever",
    "diagnosis": "Torn CCL (Cranial Cruciate Ligament)",
    "affected_body_part": "back left leg",
    "symptoms": ["limping", "non-weight-bearing"],
    "recommended_treatment": "TPLO surgery",
    "severity": "moderate",
    "urgency": "scheduled",
    "confidence_score": 0.94
  },
  "pre_existing_check": {
    "status": "passed",
    "waiting_period_met": true,
    "prior_related_claims": false,
    "hereditary_risk": "elevated",
    "notes": "Golden Retrievers have elevated CCL risk. Verify acute injury vs degenerative.",
    "confidence": 0.87
  },
  "fraud_analysis": {
    "fraud_score": 0.15,
    "risk_level": "low",
    "indicators": [],
    "recommendation": "Proceed with standard processing"
  },
  "coverage_check": {
    "covered": true,
    "coverage_type": "accident",
    "annual_limit": 10000.00,
    "used_ytd": 0.00,
    "remaining": 10000.00,
    "deductible": 250.00,
    "deductible_met": false,
    "reimbursement_rate": 0.80
  },
  "amount_billed": 4500.00,
  "estimated_payout": 3400.00
}
```

---

### Upload Vet Invoice

Upload a vet invoice document for OCR processing.

```
POST /claims/{claim_number}/documents
```

#### Request

```
Content-Type: multipart/form-data

file: <binary> - PDF or image of vet invoice
document_type: string - invoice|medical_record|lab_result
```

#### Example Request

```bash
curl -X POST http://localhost:8001/api/v1/claims/CLM-PET-2024-00001/documents \
  -H "Content-Type: multipart/form-data" \
  -F "file=@vet_invoice.pdf" \
  -F "document_type=invoice"
```

#### Response (201 Created)

```json
{
  "document_id": "doc_abc123",
  "claim_number": "CLM-PET-2024-00001",
  "document_type": "invoice",
  "filename": "vet_invoice.pdf",
  "uploaded_at": "2024-06-15T14:35:00Z",
  "ocr_status": "completed",
  "ocr_result": {
    "clinic_name": "Happy Paws Veterinary Clinic",
    "clinic_address": "123 Pet Street, Chicago, IL 60601",
    "date_of_service": "2024-06-15",
    "patient_name": "Max",
    "patient_species": "Canine",
    "invoice_items": [
      {"code": "OE001", "description": "Office Exam", "amount": 75.00},
      {"code": "RAD01", "description": "X-Ray - 2 Views", "amount": 250.00},
      {"code": "SED01", "description": "Sedation", "amount": 125.00},
      {"code": "DIAG1", "description": "CCL Diagnosis/Consult", "amount": 150.00},
      {"code": "TPLO1", "description": "TPLO Surgery Estimate", "amount": 3900.00}
    ],
    "subtotal": 4500.00,
    "total": 4500.00,
    "confidence_score": 0.96
  }
}
```

---

### Get Pet Claim

Retrieve pet claim details by claim number.

```
GET /claims/{claim_number}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| claim_number | string | Claim identifier (e.g., CLM-PET-2024-00001) |

#### Example Request

```bash
curl http://localhost:8001/api/v1/claims/CLM-PET-2024-00001
```

#### Response (200 OK)

```json
{
  "claim_id": "clm_abc123",
  "claim_number": "CLM-PET-2024-00001",
  "policy_id": "POL-PET-2024-001",
  "pet_id": "PET-001",
  "pet_name": "Max",
  "pet_species": "dog",
  "pet_breed": "Golden Retriever",
  "pet_age_years": 5,
  "date_of_service": "2024-06-15",
  "date_reported": "2024-06-15T14:30:00Z",
  "status": "under_review",
  "condition_type": "accident",
  "diagnosis": "Torn CCL (Cranial Cruciate Ligament)",
  "treatment": "TPLO Surgery",
  "vet_provider": {
    "clinic_name": "Happy Paws Veterinary Clinic",
    "address": "123 Pet Street, Chicago, IL 60601",
    "phone": "312-555-0100"
  },
  "amount_billed": 4500.00,
  "amount_approved": 4500.00,
  "amount_paid": 0.00,
  "estimated_payout": 3400.00,
  "fraud_score": 0.15,
  "pre_existing_flag": false,
  "ai_recommendation": "Approve claim. Surgery estimated reasonable for TPLO."
}
```

---

### List Pet Claims

Retrieve all pet claims with optional filtering.

```
GET /claims/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (submitted, under_review, approved, denied, paid) |
| policy_id | string | Filter by policy |
| pet_id | string | Filter by pet |
| condition_type | string | Filter by type (accident, illness, wellness, dental) |
| limit | integer | Max results (default: 50) |
| offset | integer | Pagination offset |

#### Example Request

```bash
curl "http://localhost:8001/api/v1/claims/?status=under_review&condition_type=accident&limit=10"
```

#### Response (200 OK)

```json
{
  "claims": [
    {
      "claim_number": "CLM-PET-2024-00001",
      "pet_name": "Max",
      "pet_breed": "Golden Retriever",
      "status": "under_review",
      "condition_type": "accident",
      "diagnosis": "Torn CCL",
      "date_of_service": "2024-06-15",
      "amount_billed": 4500.00,
      "estimated_payout": 3400.00,
      "fraud_score": 0.15
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### Check Pre-Existing Condition

Analyze claim for pre-existing conditions.

```
POST /claims/{claim_number}/pre-existing
```

#### Example Request

```bash
curl -X POST http://localhost:8001/api/v1/claims/CLM-PET-2024-00001/pre-existing
```

#### Response (200 OK)

```json
{
  "claim_number": "CLM-PET-2024-00001",
  "pet_name": "Max",
  "diagnosis": "Torn CCL",
  "pre_existing_analysis": {
    "determination": "likely_not_pre_existing",
    "confidence": 0.87,
    "waiting_period_check": {
      "accident": {"required_days": 0, "elapsed_days": 517, "passed": true},
      "illness": {"required_days": 14, "elapsed_days": 517, "passed": true},
      "orthopedic": {"required_days": 180, "elapsed_days": 517, "passed": true}
    },
    "prior_claims_check": {
      "related_claims": 0,
      "similar_conditions": [],
      "passed": true
    },
    "breed_risk_assessment": {
      "breed": "Golden Retriever",
      "condition": "CCL tear",
      "hereditary_risk": "elevated",
      "notes": "CCL injuries common in large breed dogs. Recommend verifying acute injury vs progressive degenerative condition."
    }
  },
  "recommendation": "Approve with standard review",
  "analyzed_at": "2024-06-15T14:40:00Z"
}
```

---

### Run Fraud Analysis

Trigger fraud analysis on an existing pet claim.

```
POST /claims/{claim_number}/fraud
```

#### Example Request

```bash
curl -X POST http://localhost:8001/api/v1/claims/CLM-PET-2024-00001/fraud
```

#### Response (200 OK)

```json
{
  "claim_number": "CLM-PET-2024-00001",
  "fraud_score": 0.15,
  "risk_level": "low",
  "indicators_checked": {
    "policy_age": {"status": "normal", "details": "Policy active for 517 days"},
    "claim_frequency": {"status": "normal", "details": "0 claims in past year"},
    "report_timing": {"status": "normal", "details": "Reported same day as vet visit"},
    "invoice_authenticity": {"status": "verified", "details": "Clinic license verified"},
    "amount_pattern": {"status": "normal", "details": "Reasonable for TPLO surgery"},
    "vet_clinic": {"status": "clear", "details": "No fraud flags on provider"},
    "pet_identity": {"status": "verified", "details": "Microchip matches policy records"}
  },
  "indicators_triggered": [],
  "recommendation": "Proceed with standard processing",
  "analyzed_at": "2024-06-15T14:45:00Z"
}
```

---

### Get Claim Triage

Get AI triage recommendation for a pet claim.

```
GET /claims/{claim_number}/triage
```

#### Response (200 OK)

```json
{
  "claim_number": "CLM-PET-2024-00001",
  "pet_name": "Max",
  "diagnosis": "Torn CCL",
  "triage_result": {
    "category": "orthopedic_surgery",
    "severity": "moderate",
    "priority": "normal",
    "auto_approve_eligible": false,
    "requires_review": true,
    "review_reasons": [
      "Surgery claim over $3,000 threshold",
      "CCL has hereditary component in some breeds"
    ],
    "recommended_actions": [
      "Verify surgery completion before payment",
      "Request post-operative x-rays for file",
      "Confirm acute injury vs degenerative"
    ],
    "estimated_processing_days": 5,
    "assignment_queue": "orthopedic_claims"
  },
  "coverage_summary": {
    "eligible_amount": 4500.00,
    "deductible_applied": 250.00,
    "reimbursable_amount": 4250.00,
    "estimated_payout": 3400.00
  }
}
```

---

## Webhooks

### Pet Claim Status Updated

Sent when pet claim status changes.

```json
{
  "event_type": "pet_claim.status_changed",
  "timestamp": "2024-06-15T15:00:00Z",
  "data": {
    "claim_number": "CLM-PET-2024-00001",
    "pet_name": "Max",
    "previous_status": "submitted",
    "new_status": "under_review",
    "changed_by": "system"
  }
}
```

### Pet Claim Approved

Sent when pet claim is approved for payment.

```json
{
  "event_type": "pet_claim.approved",
  "timestamp": "2024-06-20T10:00:00Z",
  "data": {
    "claim_number": "CLM-PET-2024-00001",
    "pet_name": "Max",
    "amount_approved": 4500.00,
    "payout_amount": 3400.00,
    "approved_by": "adjuster_001"
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| CLAIM_NOT_FOUND | Claim number does not exist |
| PET_NOT_FOUND | Pet ID not found on policy |
| INVALID_POLICY | Policy number not found or inactive |
| WAITING_PERIOD_NOT_MET | Claim submitted before waiting period expired |
| PRE_EXISTING_CONDITION | Condition determined to be pre-existing |
| COVERAGE_LIMIT_EXCEEDED | Claim exceeds annual limit |
| INVALID_CONDITION_TYPE | Condition type not covered by plan |
| VALIDATION_ERROR | Request body validation failed |
| AI_SERVICE_UNAVAILABLE | AI processing temporarily unavailable |
| DOCUMENT_PROCESSING_FAILED | OCR or document analysis failed |
