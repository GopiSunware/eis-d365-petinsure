# Claims Validation Skill

5 types of AI-powered claim validation that detect issues rules cannot catch.

## Validation Types

### 1. Diagnosis-Treatment Mismatch

Validates that treatments match the diagnosis code.

**Detects**:
- Dental procedures for orthopedic diagnosis
- Surgical procedures for minor conditions
- Contraindicated treatments
- Excessive/unnecessary procedures

**Endpoint**: `POST /api/v1/validation/diagnosis-treatment`

```bash
curl -X POST "http://localhost:8000/api/v1/validation/diagnosis-treatment" \
  -H "Content-Type: application/json" \
  -d '{
    "diagnosis_code": "S83.5",
    "procedures": ["Dental cleaning", "Tooth extraction"]
  }'
```

**Response**:
```json
{
  "valid": false,
  "issues": [
    {
      "type": "MISMATCH",
      "severity": "HIGH",
      "message": "Dental procedures not appropriate for orthopedic diagnosis S83.5 (ACL tear)"
    }
  ],
  "expected_procedures": ["Surgery", "Physical therapy", "Pain management"]
}
```

### 2. Document Inconsistency

Compares invoice against medical records for discrepancies.

**Detects**:
- Pet name mismatches
- Date inconsistencies
- Amount discrepancies
- Procedure list differences
- Provider information conflicts

**Endpoint**: `POST /api/v1/validation/document-consistency`

```bash
curl -X POST "http://localhost:8000/api/v1/validation/document-consistency" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice": {
      "pet_name": "Max",
      "service_date": "2024-12-15",
      "total_amount": 1500,
      "procedures": ["Surgery", "Anesthesia", "Medications"]
    },
    "medical_record": {
      "pet_name": "Maxie",
      "service_date": "2024-12-14",
      "procedures": ["Surgery", "Anesthesia"]
    }
  }'
```

**Response**:
```json
{
  "valid": false,
  "issues": [
    {"field": "pet_name", "invoice": "Max", "record": "Maxie", "severity": "MEDIUM"},
    {"field": "service_date", "invoice": "2024-12-15", "record": "2024-12-14", "severity": "HIGH"},
    {"field": "procedures", "missing_in_record": ["Medications"], "severity": "MEDIUM"}
  ]
}
```

### 3. Claim Completeness & Sequence

Validates clinical workflow prerequisites.

**Checks**:
- Pre-op bloodwork before surgery
- Staging workup before chemotherapy
- MRI before surgical decisions
- Post-operative care documented
- Diagnostic test sequencing

**Endpoint**: `POST /api/v1/validation/completeness`

```bash
curl -X POST "http://localhost:8000/api/v1/validation/completeness" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_type": "surgery",
    "diagnosis_code": "S83.5",
    "procedures": ["TPLO Surgery", "Anesthesia"],
    "supporting_docs": []
  }'
```

**Response**:
```json
{
  "valid": false,
  "missing_prerequisites": [
    {
      "required": "Pre-operative bloodwork",
      "reason": "Required before any surgical procedure",
      "severity": "HIGH"
    },
    {
      "required": "X-rays or imaging",
      "reason": "Required for ACL surgery planning",
      "severity": "HIGH"
    }
  ]
}
```

### 4. License Verification

Validates provider licensing and credentials.

**Checks**:
- Provider license status (active/expired)
- License expiry date vs service date
- State-specific requirements
- Facility licensing

**Endpoint**: `POST /api/v1/validation/license`

```bash
curl -X POST "http://localhost:8000/api/v1/validation/license" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "PROV-011",
    "service_date": "2024-12-15",
    "service_state": "TX"
  }'
```

**Response**:
```json
{
  "valid": false,
  "issues": [
    {
      "type": "LICENSE_EXPIRED",
      "license_number": "TX-VET-2020-4567",
      "expiry_date": "2024-06-30",
      "service_date": "2024-12-15",
      "message": "Provider license expired 168 days before service date"
    }
  ]
}
```

### 5. Controlled Substance Compliance

Validates DEA requirements for scheduled medications.

**Checks**:
- Schedule II-IV medication identification
- DEA registration verification
- Appropriate diagnosis for controlled substance
- Maximum supply limits
- Documentation requirements

**Endpoint**: `POST /api/v1/validation/controlled-substance`

```bash
curl -X POST "http://localhost:8000/api/v1/validation/controlled-substance" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "PROV-015",
    "medications": ["Tramadol", "Gabapentin"],
    "diagnosis_code": "G89.4",
    "service_state": "CA"
  }'
```

**Response**:
```json
{
  "valid": false,
  "issues": [
    {
      "medication": "Tramadol",
      "schedule": "IV",
      "issue": "MISSING_DEA",
      "message": "Provider lacks DEA registration required for Schedule IV controlled substance in CA"
    }
  ]
}
```

## Run Validation Scenarios

13 pre-built validation test scenarios:

```bash
# List validation scenarios
curl "http://localhost:8000/api/v1/validation/scenarios"

# Run specific scenario
curl -X POST "http://localhost:8000/api/v1/validation/run-scenario/VAL-001"
```

### Available Scenarios

| ID | Type | Description |
|----|------|-------------|
| VAL-001 | Mismatch | Dental procedure for ACL diagnosis |
| VAL-002 | Over-treatment | MRI for simple allergic reaction |
| VAL-003 | Document | Pet name mismatch (Max vs Maxie) |
| VAL-004 | Document | Date mismatch (1 day difference) |
| VAL-005 | Document | Amount mismatch ($200 difference) |
| VAL-006 | Sequence | Surgery without pre-op bloodwork |
| VAL-007 | License | Expired veterinary license |
| VAL-008 | DEA | Controlled substance without DEA |
| VAL-009 | Sequence | Chemo without staging workup |
| VAL-010 | Multiple | Combined mismatch + document issues |
| VAL-011 | Document | Procedure list inconsistency |
| VAL-012 | License | Out-of-state license |
| VAL-013 | Compliance | Schedule II without proper docs |

## Validation in Agent Pipeline

The Silver and Gold agents perform these validations automatically:

```
Silver Agent:
├── Coverage validation
├── Treatment benchmarking
├── Provider verification
└── Deductible calculation

Gold Agent:
├── Final validation summary
├── Risk assessment
└── Compliance check
```

## Severity Levels

| Level | Action | Examples |
|-------|--------|----------|
| LOW | Flag for review | Minor date formatting |
| MEDIUM | Enhanced review | Pet name spelling |
| HIGH | Manual review | Amount mismatch, missing docs |
| CRITICAL | Investigation | License expired, DEA violation |

## Files

```
eis-dynamics-poc/src/shared/claims_data_api/
├── app/services/validation_service.py
└── data/validation_scenarios.json
```
