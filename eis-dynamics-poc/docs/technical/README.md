# Technical Documentation

## Contents

1. [Getting Started](./getting-started.md) - Setup and development environment
2. [Services Overview](./services.md) - Microservices architecture details
3. [Deployment Guide](./deployment.md) - CI/CD and deployment procedures
4. [Testing Guide](./testing.md) - Test strategy and execution

## Quick Reference

### Service Ports
| Service | Port | Description |
|---------|------|-------------|
| **Unified Claims API** | **8000** | **Core data gateway (54 endpoints, 44 LLM tools)** |
| WS2: AI Claims | 8001 | FNOL extraction, fraud detection |
| WS3: Integration | 8002 | EIS mock APIs, data sync |
| WS5: Rating | 8003 | Premium calculation |
| WS4: Portal | 3000 | Next.js frontend |
| **WS6: Agent Pipeline** | **8006** | **LangGraph agents, scenarios, comparison** |
| PetInsure360 Backend | 8080 | Rule-based claims processor |
| PetInsure360 Frontend | 3001 | Comparison UI |

### Unified Claims API Services

| Service | Endpoints | Description |
|---------|-----------|-------------|
| ClaimService | 11 | CRUD, search, status, history |
| PolicyService | 9 | CRUD, search, coverage |
| PetService | 8 | CRUD, search, breeds |
| ProviderService | 8 | CRUD, search, specialties |
| MedicalCodesService | 9 | Lookup, search, partial match |
| ValidationService | 9 | AI-powered claim validation |

### Validation Endpoints

```
POST /api/v1/validation/diagnosis-treatment    # Check treatment matches diagnosis
POST /api/v1/validation/document-consistency   # Cross-document verification
POST /api/v1/validation/claim-sequence         # Prerequisite/follow-up checks
POST /api/v1/validation/provider-license       # License verification
POST /api/v1/validation/controlled-substances  # DEA/controlled substance compliance
POST /api/v1/validation/comprehensive          # All validations combined
GET  /api/v1/validation/scenarios              # Test scenarios
GET  /api/v1/validation/scenarios/{id}         # Single scenario
POST /api/v1/validation/run-scenario/{id}      # Execute scenario
```

### Key URLs
| Page | URL |
|------|-----|
| **Unified Claims API** | http://localhost:8000/docs |
| Portal Home | http://localhost:3000 |
| Pipeline Dashboard | http://localhost:3000/pipeline |
| **Code vs Agent Compare** | http://localhost:3000/pipeline/compare |
| PetInsure360 | http://localhost:3001 |
| Agent Pipeline API | http://localhost:8006/docs |

### Key Commands
```bash
# Start services (6 terminals)
cd src/shared/claims_data_api && uvicorn app.main:app --port 8000  # REQUIRED FIRST
cd src/ws2_ai_claims && uvicorn app.main:app --reload --port 8001
cd src/ws3_integration && uvicorn app.main:app --reload --port 8002
cd src/ws5_rating_engine && uvicorn app.main:app --reload --port 8003
cd src/ws4_agent_portal && npm run dev
cd src/ws6_agent_pipeline && uvicorn app.main:app --reload --port 8006

# Test Unified API
curl http://localhost:8000/

# Test validation (diagnosis-treatment mismatch)
curl -X POST http://localhost:8000/api/v1/validation/diagnosis-treatment \
  -H "Content-Type: application/json" \
  -d '{"diagnosis_code":"S83.5","procedures":["Dental cleaning"]}'

# Test validation scenario
curl -X POST http://localhost:8000/api/v1/validation/run-scenario/VAL-001

# Test fraud detection
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST-023","pet_id":"PET-034","provider_id":"PROV-011","claim_amount":1600,"diagnosis_code":"S83.5","service_date":"2024-12-15"}'

# Test pipeline
curl -X POST "http://localhost:8006/api/v1/pipeline/demo/claim?complexity=simple"

# Test scenarios
curl http://localhost:8006/api/v1/scenarios/
```

## Agent Pipeline Components

### Backend Services

| Component | File | Description |
|-----------|------|-------------|
| Pipeline Router | `app/routers/pipeline.py` | Pipeline trigger and status APIs |
| Scenarios Router | `app/routers/scenarios.py` | 20 demo claim scenarios |
| Comparison Router | `app/routers/comparison.py` | Code vs Agent comparison |
| Code Processor | `app/services/code_processor.py` | Deterministic claims processor |
| LangGraph Agents | `app/agents/` | Router, Bronze, Silver, Gold agents |
| LLM Tools | `app/tools/unified_api_tools.py` | 44 tools for agents |

### LLM Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| Claim Tools | 7 | CRUD, search, status |
| Policy Tools | 8 | CRUD, coverage lookup |
| Pet Tools | 8 | CRUD, breed info |
| Provider Tools | 7 | CRUD, specialty search |
| Medical Code Tools | 8 | Code lookup, partial match |
| Validation Tools | 6 | AI-powered validation |

### Frontend Pages

| Page | File | Description |
|------|------|-------------|
| Pipeline Dashboard | `app/pipeline/page.tsx` | React Flow visualization |
| Comparison View | `app/pipeline/compare/page.tsx` | Side-by-side comparison |

## Related Documentation

- [PIPELINE_VISUAL_FLOW.md](../PIPELINE_VISUAL_FLOW.md) - Pipeline UI documentation
- [README.md](../README.md) - Project overview
- [howto.md](../../howto.md) - Quick start guide
