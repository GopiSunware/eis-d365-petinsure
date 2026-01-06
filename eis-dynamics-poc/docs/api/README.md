# API Reference

## Overview

The EIS-Dynamics POC exposes RESTful APIs across microservices for claims processing, integration, rating, and AI-powered pipeline processing.

## Base URLs

| Service | Port | Base URL |
|---------|------|----------|
| AI Claims (WS2) | 8001 | `http://localhost:8001/api/v1` |
| Integration (WS3) | 8002 | `http://localhost:8002/api/v1` |
| Rating (WS5) | 8003 | `http://localhost:8003/api/v1` |
| **Agent Pipeline (WS6)** | **8006** | `http://localhost:8006/api/v1` |

## Swagger Documentation

All services have interactive API documentation:

| Service | Swagger URL |
|---------|-------------|
| AI Claims | http://localhost:8001/docs |
| Integration | http://localhost:8002/docs |
| Rating | http://localhost:8003/docs |
| **Agent Pipeline** | **http://localhost:8006/docs** |

## API Documentation

- [Claims API](./claims-api.md) - FNOL submission, claim management
- [EIS Mock API](./eis-api.md) - Policies, customers, claims lookup
- [Rating API](./rating-api.md) - Quote calculation, factors

---

## Agent Pipeline API (WS6)

The Agent Pipeline provides LangGraph-based claims processing with 4 AI agents.

### Pipeline Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pipeline/trigger` | Trigger pipeline (async) |
| POST | `/api/v1/pipeline/trigger/sync` | Trigger pipeline (sync) |
| POST | `/api/v1/pipeline/demo/claim` | Trigger demo claim |
| GET | `/api/v1/pipeline/run/{run_id}` | Get pipeline run status |
| GET | `/api/v1/pipeline/run/{run_id}/bronze` | Get bronze output |
| GET | `/api/v1/pipeline/run/{run_id}/silver` | Get silver output |
| GET | `/api/v1/pipeline/run/{run_id}/gold` | Get gold output |
| GET | `/api/v1/pipeline/recent` | Get recent runs |
| GET | `/api/v1/pipeline/active` | Get active runs |

### Scenarios Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/scenarios/` | List all 20 scenarios |
| GET | `/api/v1/scenarios/{scenario_id}` | Get specific scenario |
| GET | `/api/v1/scenarios/complexity/{level}` | Filter by complexity (simple/medium/complex) |
| GET | `/api/v1/scenarios/category/{category}` | Filter by category |

### Comparison Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/compare/run` | Run comparison with custom claim |
| POST | `/api/v1/compare/scenario/{scenario_id}` | Run comparison with scenario |
| POST | `/api/v1/compare/quick?complexity=` | Quick comparison (simple/medium/complex) |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| GET | `/metrics` | Pipeline metrics |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/events` | Stream all pipeline events |
| `/ws/run/{run_id}` | Stream events for specific run |

---

## Usage Examples

### Scenarios API

```bash
# List all scenarios
curl http://localhost:8006/api/v1/scenarios/

# Get specific scenario
curl http://localhost:8006/api/v1/scenarios/SCN-001

# Get scenarios by complexity
curl http://localhost:8006/api/v1/scenarios/complexity/simple
```

### Comparison API

```bash
# Run quick comparison
curl -X POST "http://localhost:8006/api/v1/compare/quick?complexity=medium"

# Run scenario comparison
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"

# Run custom claim comparison
curl -X POST http://localhost:8006/api/v1/compare/run \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-001",
    "claim_type": "Accident",
    "claim_amount": 1500,
    "service_date": "2024-12-30",
    "diagnosis_code": "T65.8"
  }'
```

### Pipeline API

```bash
# Trigger demo claim
curl -X POST "http://localhost:8006/api/v1/pipeline/demo/claim?complexity=simple"

# Check run status
curl "http://localhost:8006/api/v1/pipeline/run/{run_id}"

# Get metrics
curl http://localhost:8006/metrics
```

---

## Response Formats

### Comparison Response

```json
{
  "comparison_id": "CMP-ABC12345",
  "claim_id": "CLM-001",
  "code_driven": {
    "run_id": "CODE-CMP-ABC12345",
    "processing_time_ms": 0.04,
    "final_decision": "STANDARD_REVIEW",
    "risk_level": "LOW",
    "estimated_payout": 1000.00,
    "bronze": { ... },
    "silver": { ... },
    "gold": { ... }
  },
  "agent_driven": {
    "run_id": "AGENT-CMP-ABC12345",
    "processing_time_ms": 45000,
    "final_decision": "STANDARD_REVIEW",
    "risk_level": "LOW",
    "estimated_payout": 1000.00,
    "bronze": { ... },
    "silver": { ... },
    "gold": { ... },
    "reasoning": ["...", "..."],
    "insights": ["...", "..."]
  },
  "comparison_metrics": {
    "time_comparison": {
      "code_ms": 0.04,
      "agent_ms": 45000,
      "agent_slower_by": "1125000x"
    },
    "decision_match": true,
    "risk_match": true
  }
}
```

### Scenario Response

```json
{
  "id": "SCN-001",
  "name": "Chocolate Toxicity Emergency",
  "description": "Dog ingested dark chocolate - emergency treatment",
  "claim_type": "Accident",
  "claim_category": "Toxicity/Poisoning",
  "claim_amount": 1355.00,
  "diagnosis_code": "T65.8",
  "is_in_network": false,
  "is_emergency": true,
  "line_items": [
    {"description": "Emergency exam fee", "amount": 175.00},
    {"description": "IV fluids", "amount": 245.00}
  ]
}
```

### Error Response

```json
{
  "detail": "Scenario SCN-999 not found"
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |
