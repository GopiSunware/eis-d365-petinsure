# Claims Processing Skill (Parent)

Master skill for pet insurance claims processing workflows. Orchestrates both rule-based and AI agent-driven approaches.

## Skill Hierarchy

```
/claims-processing (this file)
├── /claims/submit      - Claim submission methods
├── /claims/validate    - 5 validation types
├── /claims/fraud       - Fraud detection & patterns
├── /claims/docgen      - Document AI processing
├── /claims/pipeline    - Agent pipeline (Bronze/Silver/Gold)
├── /claims/compare     - Rule vs Agent comparison
└── /claims/scenarios   - 36 pre-built test scenarios
```

## Quick Reference

### Processing Approaches

| Approach | Project | Description |
|----------|---------|-------------|
| **Rule-Based** | PetInsure360 | Fixed business rules, deterministic decisions |
| **Agent-Driven** | EIS-Dynamics | 4-layer LangGraph agents with LLM reasoning |

### Service Endpoints

| Service | Port | Purpose |
|---------|------|---------|
| Claims Data API | 8000 | Unified claims API (54 endpoints) |
| AI Claims | 8001 | FNOL extraction, basic fraud |
| Agent Pipeline | 8006 | LangGraph orchestration |
| DocGen Service | 8007 | Document AI processing |
| PetInsure Backend | 3002 | Portal API + WebSocket |

## Usage

### Run a Claim Through Agent Pipeline

```bash
# Submit claim to agent pipeline
curl -X POST "http://localhost:8006/api/v1/pipeline/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-TEST-001",
    "policy_id": "POL-001",
    "customer_id": "CUST-001",
    "claim_amount": 1500,
    "diagnosis_code": "K91.1",
    "service_date": "2024-12-15"
  }'

# Check pipeline status
curl "http://localhost:8006/api/v1/pipeline/run/{run_id}"
```

### Run a Pre-built Scenario

```bash
# List all scenarios
curl "http://localhost:8006/api/v1/scenarios/"

# Run specific scenario
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"

# Run fraud scenario
curl -X POST "http://localhost:8006/api/v1/compare/scenario/FRAUD-001"
```

### Check Fraud Indicators

```bash
curl -X POST "http://localhost:8000/api/v1/fraud/check" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-023",
    "claim_amount": 1600,
    "diagnosis_code": "S83.5",
    "service_date": "2024-12-15"
  }'
```

### Run Validation Check

```bash
# Diagnosis-treatment mismatch
curl -X POST "http://localhost:8000/api/v1/validation/diagnosis-treatment" \
  -H "Content-Type: application/json" \
  -d '{"diagnosis_code": "S83.5", "procedures": ["Dental cleaning"]}'

# Run validation scenario
curl -X POST "http://localhost:8000/api/v1/validation/run-scenario/VAL-001"
```

## Claims Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLAIM SUBMISSION                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Portal Form  │  │  API Direct  │  │  Doc Upload  │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         └────────────────┬────────────────────┘                         │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    RULE-BASED PATH      │   │   AGENT-DRIVEN PATH     │
│    (PetInsure360)       │   │   (EIS-Dynamics)        │
├─────────────────────────┤   ├─────────────────────────┤
│ • Fixed business rules  │   │ ┌─────────────────────┐ │
│ • Policy validation     │   │ │   ROUTER AGENT      │ │
│ • Coverage check        │   │ │ Complexity routing  │ │
│ • Limit verification    │   │ └──────────┬──────────┘ │
│ • Basic fraud check     │   │            ▼            │
│ • Risk scoring          │   │ ┌─────────────────────┐ │
│                         │   │ │   BRONZE AGENT      │ │
│ Decision: APPROVE/DENY  │   │ │ Data validation     │ │
│                         │   │ └──────────┬──────────┘ │
│                         │   │            ▼            │
│                         │   │ ┌─────────────────────┐ │
│                         │   │ │   SILVER AGENT      │ │
│                         │   │ │ Enrichment          │ │
│                         │   │ └──────────┬──────────┘ │
│                         │   │            ▼            │
│                         │   │ ┌─────────────────────┐ │
│                         │   │ │   GOLD AGENT        │ │
│                         │   │ │ Risk & decision     │ │
│                         │   │ └─────────────────────┘ │
└─────────────────────────┘   └─────────────────────────┘
           │                               │
           └───────────────┬───────────────┘
                           ▼
                    ┌─────────────┐
                    │  DECISION   │
                    │ AUTO_APPROVE│
                    │ REVIEW      │
                    │ INVESTIGATE │
                    │ DENY        │
                    └─────────────┘
```

## Child Skills

Use specific child skills for detailed guidance:

| Need | Use Skill |
|------|-----------|
| Submit a new claim | `/claims/submit` |
| Validate claim data | `/claims/validate` |
| Detect fraud patterns | `/claims/fraud` |
| Process documents | `/claims/docgen` |
| Run agent pipeline | `/claims/pipeline` |
| Compare rule vs agent | `/claims/compare` |
| Run test scenarios | `/claims/scenarios` |

## Key Files

```
eis-dynamics-poc/
├── src/
│   ├── ws6_agent_pipeline/
│   │   ├── app/agents/          # LangGraph agents
│   │   ├── app/services/        # Code processor (rule-based)
│   │   └── data/claim_scenarios.json  # 20 scenarios
│   ├── ws7_docgen/              # Document processing
│   └── shared/claims_data_api/
│       ├── app/services/
│       │   ├── claim_service.py
│       │   ├── validation_service.py
│       │   └── fraud_service.py
│       └── data/
│           ├── validation_scenarios.json  # 13 scenarios
│           └── fraud_patterns.json        # 3 patterns

petinsure360/
├── backend/app/
│   ├── api/claims.py            # Claims API
│   └── services/pipeline_service.py
└── frontend/src/pages/
    └── ClaimPage.jsx            # Claim submission UI
```

## Metrics & Monitoring

Track these metrics when processing claims:

| Metric | Rule-Based | Agent-Driven |
|--------|------------|--------------|
| Processing Time | < 100ms | 30-120 seconds |
| Decision Match | Baseline | 85-95% match |
| Fraud Detection | Basic patterns | Cross-claim analysis |
| Reasoning | None | Full audit trail |
