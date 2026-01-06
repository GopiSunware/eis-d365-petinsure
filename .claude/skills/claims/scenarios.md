# Claims Test Scenarios Skill

36 pre-built test scenarios for validating claims processing systems.

## Scenario Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    36 TEST SCENARIOS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   STANDARD CLAIMS (20)         │   FRAUD PATTERNS (3)           │
│   SCN-001 to SCN-020           │   FRAUD-001 to FRAUD-003       │
│   ─────────────────            │   ──────────────────           │
│   • Simple approvals           │   • Chronic gaming              │
│   • Coverage denials           │   • Provider collusion          │
│   • Waiting period             │   • Staged timing               │
│   • Limit exceeded             │                                 │
│   • Emergency claims           │   VALIDATION (13)               │
│   • Multi-pet                  │   VAL-001 to VAL-013            │
│                                │   ────────────────              │
│                                │   • Diagnosis mismatch          │
│                                │   • Document inconsistency      │
│                                │   • License issues              │
│                                │   • DEA violations              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## List All Scenarios

**Endpoint**: `GET http://localhost:8006/api/v1/scenarios/`

```bash
curl "http://localhost:8006/api/v1/scenarios/"
```

## Standard Claim Scenarios (SCN-001 to SCN-020)

### Simple Approvals

| ID | Name | Amount | Expected |
|----|------|--------|----------|
| SCN-001 | Simple Gastritis | $1,500 | APPROVED |
| SCN-002 | Routine Dental | $800 | APPROVED |
| SCN-003 | Skin Allergy | $450 | APPROVED |
| SCN-004 | Ear Infection | $350 | APPROVED |
| SCN-005 | Annual Wellness | $250 | APPROVED |

```bash
# Run simple approval scenario
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"
```

**SCN-001 Details**:
```json
{
  "scenario_id": "SCN-001",
  "name": "Simple Gastritis Claim",
  "claim_data": {
    "claim_id": "CLM-SCN-001",
    "policy_id": "POL-001",
    "customer_id": "CUST-001",
    "pet_id": "PET-001",
    "provider_id": "PROV-001",
    "claim_amount": 1500,
    "diagnosis_code": "K91.1",
    "service_date": "2024-12-15",
    "claim_type": "illness",
    "treatment_notes": "Gastritis with vomiting, IV fluids and anti-nausea medication"
  },
  "expected": {
    "decision": "APPROVED",
    "payment_range": [1000, 1200]
  }
}
```

### Coverage Denials

| ID | Name | Reason | Expected |
|----|------|--------|----------|
| SCN-006 | Pre-existing Hip | Pre-existing condition | DENY |
| SCN-007 | Cosmetic Procedure | Not covered | DENY |
| SCN-008 | Breeding Complications | Exclusion | DENY |
| SCN-009 | Experimental Treatment | Not approved | DENY |

**SCN-006 Details**:
```json
{
  "scenario_id": "SCN-006",
  "name": "Pre-existing Hip Dysplasia",
  "claim_data": {
    "diagnosis_code": "M16.1",
    "treatment_notes": "Hip dysplasia surgery - condition noted at enrollment exam"
  },
  "expected": {
    "decision": "DENY",
    "denial_reason": "PRE_EXISTING_CONDITION"
  }
}
```

### Waiting Period Scenarios

| ID | Name | Days | Expected |
|----|------|------|----------|
| SCN-010 | Day 10 Illness | 10 days | DENY (waiting) |
| SCN-011 | Day 15 Illness | 15 days | APPROVED |
| SCN-012 | Day 1 Accident | 1 day | APPROVED |

### Limit Scenarios

| ID | Name | Situation | Expected |
|----|------|-----------|----------|
| SCN-013 | Near Limit | $14,500 of $15,000 used | PARTIAL |
| SCN-014 | Over Limit | Exceeds annual limit | PARTIAL |
| SCN-015 | Incident Limit | Per-incident cap | PARTIAL |

### Special Scenarios

| ID | Name | Type | Expected |
|----|------|------|----------|
| SCN-016 | Emergency Room | Emergency | APPROVED |
| SCN-017 | After Hours | Emergency premium | APPROVED |
| SCN-018 | Multi-Pet Household | 3 pets, 1 claim | APPROVED |
| SCN-019 | Out-of-Network | 70% coverage | APPROVED |
| SCN-020 | Specialist Referral | Oncologist | APPROVED |

## Fraud Scenarios (FRAUD-001 to FRAUD-003)

### FRAUD-001: Chronic Condition Gaming

```bash
curl -X POST "http://localhost:8006/api/v1/compare/scenario/FRAUD-001"
```

```json
{
  "scenario_id": "FRAUD-001",
  "name": "Chronic Condition Gaming - CCL Tear",
  "pattern": "CHRONIC_CONDITION_GAMING",
  "claim_data": {
    "customer_id": "CUST-023",
    "pet_id": "PET-034",
    "diagnosis_code": "S83.5",
    "claim_amount": 4500,
    "service_date": "2024-12-17",
    "treatment_notes": "CCL tear - traumatic injury reported"
  },
  "fraud_indicators": {
    "prior_claims": [
      {"diagnosis": "Hip dysplasia", "date": "2024-03-15"},
      {"diagnosis": "Hip dysplasia", "date": "2024-07-20"},
      {"diagnosis": "Joint pain", "date": "2024-10-05"}
    ],
    "breed": "French Bulldog",
    "breed_risk": "HIGH_ORTHOPEDIC"
  },
  "expected": {
    "decision": "INVESTIGATION",
    "fraud_score_min": 65
  }
}
```

### FRAUD-002: Provider Collusion

```json
{
  "scenario_id": "FRAUD-002",
  "name": "Provider Collusion Pattern",
  "pattern": "PROVIDER_COLLUSION",
  "claim_data": {
    "customer_id": "CUST-045",
    "provider_id": "PROV-099",
    "claim_amount": 2000,
    "service_date": "2024-12-15"
  },
  "fraud_indicators": {
    "provider_concentration": "100%",
    "network_status": "out_of_network",
    "claim_history": [
      {"amount": 2000, "date": "2024-11-01"},
      {"amount": 1500, "date": "2024-10-15"},
      {"amount": 2500, "date": "2024-09-20"},
      {"amount": 2000, "date": "2024-08-10"}
    ],
    "round_amounts": 4
  },
  "expected": {
    "decision": "INVESTIGATION",
    "fraud_score_min": 55
  }
}
```

### FRAUD-003: Staged Timing

```json
{
  "scenario_id": "FRAUD-003",
  "name": "Staged Timing - IVDD Claim",
  "pattern": "STAGED_TIMING",
  "claim_data": {
    "customer_id": "CUST-067",
    "pet_id": "PET-089",
    "diagnosis_code": "G95.2",
    "claim_amount": 8000,
    "service_date": "2024-12-17"
  },
  "fraud_indicators": {
    "policy_start_date": "2024-12-01",
    "waiting_period_days": 14,
    "days_after_waiting": 3,
    "breed": "French Bulldog",
    "condition": "IVDD",
    "breed_risk_for_condition": "VERY_HIGH",
    "pre_policy_records": "MISSING"
  },
  "expected": {
    "decision": "INVESTIGATION",
    "fraud_score_min": 70
  }
}
```

## Validation Scenarios (VAL-001 to VAL-013)

### Diagnosis-Treatment Mismatch

| ID | Issue | Severity |
|----|-------|----------|
| VAL-001 | Dental for orthopedic | HIGH |
| VAL-002 | MRI for allergies | MEDIUM |

```bash
curl -X POST "http://localhost:8000/api/v1/validation/run-scenario/VAL-001"
```

**VAL-001 Details**:
```json
{
  "scenario_id": "VAL-001",
  "name": "Dental Procedure for ACL Diagnosis",
  "validation_type": "DIAGNOSIS_TREATMENT_MISMATCH",
  "input": {
    "diagnosis_code": "S83.5",
    "diagnosis_name": "ACL/CCL Tear",
    "procedures": ["Dental cleaning", "Tooth extraction"]
  },
  "expected": {
    "valid": false,
    "severity": "HIGH",
    "issue": "Dental procedures not appropriate for orthopedic diagnosis"
  }
}
```

### Document Inconsistency

| ID | Issue | Severity |
|----|-------|----------|
| VAL-003 | Pet name mismatch | MEDIUM |
| VAL-004 | Date mismatch | HIGH |
| VAL-005 | Amount mismatch | HIGH |
| VAL-011 | Procedure list mismatch | MEDIUM |

### Clinical Sequence

| ID | Issue | Severity |
|----|-------|----------|
| VAL-006 | Surgery without bloodwork | HIGH |
| VAL-009 | Chemo without staging | CRITICAL |

### License/Compliance

| ID | Issue | Severity |
|----|-------|----------|
| VAL-007 | Expired license | CRITICAL |
| VAL-008 | Missing DEA | CRITICAL |
| VAL-012 | Out-of-state license | HIGH |
| VAL-013 | Schedule II docs | CRITICAL |

## Run Scenarios

### Run Single Scenario

```bash
# Standard scenario
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"

# Fraud scenario
curl -X POST "http://localhost:8006/api/v1/compare/scenario/FRAUD-001"

# Validation scenario
curl -X POST "http://localhost:8000/api/v1/validation/run-scenario/VAL-001"
```

### Run All Standard Scenarios

```bash
curl -X POST "http://localhost:8006/api/v1/compare/all"
```

### Run All Fraud Scenarios

```bash
curl -X POST "http://localhost:8006/api/v1/compare/fraud-all"
```

### Run All Validation Scenarios

```bash
curl -X POST "http://localhost:8000/api/v1/validation/run-all-scenarios"
```

## Scenario Results Summary

### Expected Outcomes by Category

| Category | Approve | Deny | Review | Investigate |
|----------|---------|------|--------|-------------|
| Standard (20) | 12 | 4 | 3 | 1 |
| Fraud (3) | 0 | 0 | 0 | 3 |
| Validation (13) | 0 | 0 | 8 | 5 |

### Pass Rate Targets

| System | Target | Description |
|--------|--------|-------------|
| Rule-Based | 100% | All scenarios deterministic |
| Agent-Driven | 95%+ | Allow for LLM variance |
| Validation | 100% | All issues detected |
| Fraud | 100% | All patterns flagged |

## Custom Scenario Creation

Create custom scenarios for testing:

```bash
curl -X POST "http://localhost:8006/api/v1/scenarios/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom Test Scenario",
    "category": "CUSTOM",
    "claim_data": {
      "policy_id": "POL-001",
      "customer_id": "CUST-001",
      "claim_amount": 2000,
      "diagnosis_code": "K91.1",
      "service_date": "2024-12-20"
    },
    "expected": {
      "decision": "APPROVED"
    }
  }'
```

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/scenarios/` | List all scenarios |
| `GET /api/v1/scenarios/{id}` | Get scenario details |
| `POST /api/v1/compare/scenario/{id}` | Run scenario comparison |
| `POST /api/v1/compare/all` | Run all comparisons |
| `POST /api/v1/validation/run-scenario/{id}` | Run validation scenario |
| `POST /api/v1/scenarios/` | Create custom scenario |

## Files

```
eis-dynamics-poc/src/
├── ws6_agent_pipeline/data/
│   └── claim_scenarios.json       # 20 standard + 3 fraud scenarios
└── shared/claims_data_api/data/
    ├── validation_scenarios.json  # 13 validation scenarios
    └── fraud_patterns.json        # Fraud pattern definitions
```
