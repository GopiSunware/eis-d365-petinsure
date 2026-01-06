# Agent Pipeline Skill

LangGraph-based 4-layer agent pipeline for intelligent claims processing.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │   ROUTER     │  Complexity Assessment                        │
│  │   AGENT      │  → LOW: Fast-track to Gold                    │
│  └──────┬───────┘  → MEDIUM: Standard flow                      │
│         │          → HIGH: Full analysis                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   BRONZE     │  Data Validation Layer                        │
│  │   AGENT      │  → Schema validation                          │
│  └──────┬───────┘  → Reference data lookup                      │
│         │          → Initial enrichment                         │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   SILVER     │  Business Logic Layer                         │
│  │   AGENT      │  → Coverage verification                      │
│  └──────┬───────┘  → Treatment benchmarking                     │
│         │          → Provider validation                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   GOLD       │  Decision Layer                               │
│  │   AGENT      │  → Fraud analysis                             │
│  └──────────────┘  → Risk scoring                               │
│                    → Final decision                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Trigger Pipeline

### Start Pipeline Run

**Endpoint**: `POST http://localhost:8006/api/v1/pipeline/trigger`

```bash
curl -X POST "http://localhost:8006/api/v1/pipeline/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_data": {
      "claim_id": "CLM-2024-001",
      "policy_id": "POL-001",
      "customer_id": "CUST-001",
      "pet_id": "PET-001",
      "provider_id": "PROV-001",
      "claim_amount": 1500,
      "diagnosis_code": "K91.1",
      "service_date": "2024-12-15",
      "claim_type": "illness",
      "treatment_notes": "Gastritis treatment with IV fluids"
    }
  }'
```

**Response**:
```json
{
  "run_id": "run_abc123def456",
  "status": "TRIGGERED",
  "message": "Pipeline started successfully",
  "estimated_duration": "30-60 seconds"
}
```

### Check Pipeline Status

```bash
curl "http://localhost:8006/api/v1/pipeline/run/run_abc123def456"
```

**Response**:
```json
{
  "run_id": "run_abc123def456",
  "status": "COMPLETED",
  "current_agent": "GOLD",
  "progress": {
    "router": "completed",
    "bronze": "completed",
    "silver": "completed",
    "gold": "completed"
  },
  "duration_seconds": 45,
  "decision": "APPROVED",
  "payment_amount": 1125
}
```

## Agent Details

### Router Agent

**Purpose**: Assess claim complexity and route appropriately.

**Complexity Factors**:
- Claim amount threshold ($5000+)
- Emergency claim flag
- Prior claim history
- Provider network status
- Diagnosis complexity

```json
{
  "agent": "router",
  "complexity_score": 65,
  "complexity_level": "MEDIUM",
  "routing_decision": "STANDARD_FLOW",
  "reasoning": "Moderate claim amount, known provider, standard diagnosis"
}
```

### Bronze Agent

**Purpose**: Validate and enrich raw claim data.

**Tasks**:
1. Schema validation
2. Policy lookup and verification
3. Customer profile retrieval
4. Pet information validation
5. Provider verification
6. Initial data enrichment

```json
{
  "agent": "bronze",
  "status": "completed",
  "validations": {
    "schema_valid": true,
    "policy_found": true,
    "policy_status": "ACTIVE",
    "customer_verified": true,
    "pet_verified": true,
    "provider_verified": true
  },
  "enriched_data": {
    "policy_type": "Gold Plan",
    "annual_limit": 15000,
    "remaining_limit": 12500,
    "deductible": 250,
    "copay": 0.20
  }
}
```

### Silver Agent

**Purpose**: Apply business logic and benchmarking.

**Tasks**:
1. Coverage determination
2. Treatment cost benchmarking
3. Provider network verification
4. Deductible calculation
5. Pre-authorization check
6. Waiting period validation

```json
{
  "agent": "silver",
  "status": "completed",
  "coverage": {
    "diagnosis_covered": true,
    "coverage_percentage": 80,
    "exclusions_checked": ["pre_existing", "cosmetic"]
  },
  "benchmarking": {
    "claimed_amount": 1500,
    "benchmark_range": {"min": 800, "max": 2000},
    "within_range": true,
    "percentile": 65
  },
  "calculations": {
    "eligible_amount": 1500,
    "deductible_applied": 250,
    "copay_amount": 250,
    "estimated_payment": 1000
  }
}
```

### Gold Agent

**Purpose**: Final risk assessment and decision.

**Tasks**:
1. Fraud pattern analysis
2. Cross-claim correlation
3. Risk scoring
4. Final decision recommendation
5. Payment calculation
6. Audit trail generation

```json
{
  "agent": "gold",
  "status": "completed",
  "fraud_analysis": {
    "fraud_score": 12,
    "risk_level": "LOW",
    "patterns_checked": ["chronic_gaming", "provider_collusion", "staged_timing"],
    "flags": []
  },
  "decision": {
    "recommendation": "AUTO_APPROVE",
    "confidence": 0.95,
    "reasoning": "Low fraud risk, valid coverage, within benchmarks"
  },
  "payment": {
    "approved_amount": 1000,
    "payment_method": "ACH",
    "estimated_payment_date": "2024-12-18"
  }
}
```

## Pipeline States

| State | Description |
|-------|-------------|
| `TRIGGERED` | Pipeline started, queued for processing |
| `ROUTING` | Router agent assessing complexity |
| `BRONZE_PROCESSING` | Bronze agent validating data |
| `SILVER_PROCESSING` | Silver agent applying business logic |
| `GOLD_PROCESSING` | Gold agent making final decision |
| `COMPLETED` | Pipeline finished successfully |
| `FAILED` | Pipeline encountered error |
| `PENDING_REVIEW` | Requires human intervention |

## Decision Outcomes

| Decision | Fraud Score | Action |
|----------|-------------|--------|
| `AUTO_APPROVE` | 0-14 | Automatic payment |
| `STANDARD_REVIEW` | 15-49 | Quick manual review |
| `MANUAL_REVIEW` | 50-74 | Detailed investigation |
| `INVESTIGATION` | 75+ | Fraud team referral |
| `DENY` | Any | Claim rejected |

## WebSocket Real-time Updates

Subscribe to pipeline progress:

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8006');

socket.on('pipeline_started', (data) => {
  console.log('Pipeline started:', data.run_id);
});

socket.on('agent_progress', (data) => {
  console.log(`${data.agent} agent: ${data.status}`);
});

socket.on('pipeline_completed', (data) => {
  console.log('Decision:', data.decision);
  console.log('Payment:', data.payment_amount);
});
```

## Pipeline Configuration

### Environment Variables

```bash
# Agent Pipeline Configuration
PIPELINE_TIMEOUT=120          # Max processing time (seconds)
ENABLE_ROUTER_AGENT=true      # Enable complexity routing
ENABLE_PARALLEL_CHECKS=true   # Run independent checks in parallel
LLM_MODEL=gpt-4-turbo        # Model for agent reasoning
LLM_TEMPERATURE=0.1          # Low temperature for consistency
```

### Agent Tools Available

Each agent has access to specific tools:

| Agent | Tools |
|-------|-------|
| Router | `assess_complexity`, `check_history`, `route_claim` |
| Bronze | `validate_schema`, `lookup_policy`, `enrich_data` |
| Silver | `check_coverage`, `benchmark_treatment`, `calculate_payment` |
| Gold | `analyze_fraud`, `score_risk`, `make_decision` |

## Error Handling

```json
{
  "run_id": "run_xyz789",
  "status": "FAILED",
  "error": {
    "agent": "silver",
    "code": "POLICY_NOT_FOUND",
    "message": "Policy POL-999 not found in database",
    "recoverable": false
  },
  "partial_results": {
    "router": "completed",
    "bronze": "completed"
  }
}
```

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/pipeline/trigger` | Start pipeline run |
| `GET /api/v1/pipeline/run/{run_id}` | Get run status |
| `GET /api/v1/pipeline/run/{run_id}/details` | Get full details |
| `POST /api/v1/pipeline/run/{run_id}/cancel` | Cancel running pipeline |
| `GET /api/v1/pipeline/stats` | Pipeline statistics |

## Files

```
eis-dynamics-poc/src/ws6_agent_pipeline/
├── app/
│   ├── agents/
│   │   ├── router_agent.py      # Complexity routing
│   │   ├── bronze_agent.py      # Data validation
│   │   ├── silver_agent.py      # Business logic
│   │   └── gold_agent.py        # Decision making
│   ├── graphs/
│   │   └── claims_graph.py      # LangGraph definition
│   ├── services/
│   │   └── code_processor.py    # Rule-based fallback
│   └── routers/
│       └── pipeline.py          # API endpoints
└── data/
    └── claim_scenarios.json     # Test scenarios
```
