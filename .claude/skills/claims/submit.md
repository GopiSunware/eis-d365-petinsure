# Claims Submission Skill

Submit pet insurance claims through various methods.

## Submission Methods

### 1. Portal Form (PetInsure360)

**URL**: http://localhost:3000/claim

**Features**:
- Pet/policy selection from customer profile
- Scenario quick-fill (20 pre-built scenarios)
- Line-item entry for detailed charges
- Emergency claim flagging
- Provider selection (in/out of network)

**Required Fields**:
```typescript
{
  pet_id: string;           // Selected pet
  policy_id: string;        // Active policy
  provider_id: string;      // Veterinary provider
  service_date: string;     // YYYY-MM-DD
  diagnosis_code: string;   // ICD-10-VET code
  claim_amount: number;     // Total claim amount
  claim_type: string;       // accident | illness | wellness | emergency
  treatment_notes: string;  // Description of treatment
}
```

### 2. API Direct Submission

**Endpoint**: `POST http://localhost:8000/api/v1/claims/`

```bash
curl -X POST "http://localhost:8000/api/v1/claims/" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2024-001",
    "policy_id": "POL-001",
    "customer_id": "CUST-001",
    "pet_id": "PET-001",
    "provider_id": "PROV-001",
    "claim_amount": 1500.00,
    "diagnosis_code": "K91.1",
    "service_date": "2024-12-15",
    "claim_type": "illness",
    "treatment_notes": "Gastritis treatment - IV fluids, anti-nausea medication"
  }'
```

### 3. Pipeline Trigger (Agent Processing)

**Endpoint**: `POST http://localhost:8006/api/v1/pipeline/trigger`

```bash
curl -X POST "http://localhost:8006/api/v1/pipeline/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_data": {
      "claim_id": "CLM-AGENT-001",
      "policy_id": "POL-001",
      "customer_id": "CUST-001",
      "claim_amount": 2500,
      "diagnosis_code": "S83.5",
      "service_date": "2024-12-15",
      "treatment_notes": "ACL repair surgery"
    }
  }'
```

**Response**:
```json
{
  "run_id": "run_abc123",
  "status": "TRIGGERED",
  "message": "Pipeline started"
}
```

### 4. Scenario-Based Submission

**Quick Test**: Submit a pre-built scenario

```bash
# List available scenarios
curl "http://localhost:8006/api/v1/scenarios/"

# Submit specific scenario for processing
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"
```

### 5. Document Upload Submission

**Endpoint**: `POST http://localhost:8007/api/v1/batches/`

```bash
# Create batch for document processing
curl -X POST "http://localhost:8007/api/v1/batches/" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_name": "Invoice Batch 001",
    "claim_id": "CLM-DOC-001",
    "documents": [
      {"type": "invoice", "filename": "vet_invoice.pdf"},
      {"type": "medical_record", "filename": "medical_notes.pdf"}
    ]
  }'
```

## Claim Types

| Type | Code | Description | Waiting Period |
|------|------|-------------|----------------|
| Accident | `accident` | Injuries from accidents | None |
| Illness | `illness` | Diseases, conditions | 14 days |
| Wellness | `wellness` | Preventive care | None |
| Emergency | `emergency` | Life-threatening | None |
| Dental | `dental` | Dental procedures | 14 days |

## Common Diagnosis Codes

| Code | Description | Typical Amount |
|------|-------------|----------------|
| K91.1 | Gastritis/Vomiting | $500-1,500 |
| S83.5 | ACL/CCL Tear | $3,000-6,000 |
| T65.8 | Toxin Ingestion | $800-2,000 |
| L30.9 | Skin Allergy | $200-800 |
| K29.0 | Foreign Body | $2,000-5,000 |
| C85.9 | Lymphoma | $2,000-5,000 |
| M16.1 | Hip Dysplasia | $1,500-4,000 |
| G40.9 | Seizure Disorder | $1,000-3,500 |

## Validation Before Submission

Before submitting, verify:

1. **Policy Status**: Must be `Active`
2. **Coverage**: Diagnosis covered under plan
3. **Waiting Period**: Past waiting period for claim type
4. **Annual Limit**: Sufficient remaining coverage
5. **Provider**: Preferably in-network

```bash
# Check policy status
curl "http://localhost:8000/api/v1/policies/POL-001"

# Check coverage
curl "http://localhost:8000/api/v1/policies/POL-001/coverage?diagnosis_code=K91.1"
```

## Response Handling

**Success Response**:
```json
{
  "claim_id": "CLM-2024-001",
  "status": "submitted",
  "submitted_at": "2024-12-15T10:30:00Z",
  "estimated_processing": "3-5 business days"
}
```

**Error Response**:
```json
{
  "error": "validation_failed",
  "details": [
    {"field": "policy_id", "message": "Policy not found or inactive"}
  ]
}
```

## WebSocket Updates (PetInsure360)

Subscribe to real-time claim status:

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:3002');

socket.on('claim_submitted', (data) => {
  console.log('Claim submitted:', data.claim_id);
});

socket.on('claim_processing', (data) => {
  console.log('Processing:', data.status);
});

socket.on('claim_completed', (data) => {
  console.log('Decision:', data.decision);
});
```

## Files

```
petinsure360/frontend/src/pages/ClaimPage.jsx      # Submission UI
petinsure360/backend/app/api/claims.py             # Claims API
eis-dynamics-poc/src/ws6_agent_pipeline/app/routers/pipeline.py
```
