# EIS-Dynamics POC

**AI-Powered Pet Insurance Claims Processing**

**Version**: 1.0.0 | **Status**: Deployed to AWS

---

## What This Demonstrates

AI-powered claims processing that catches fraud and data quality issues that rule-based systems miss.

| System | Processing | Strength |
|--------|------------|----------|
| **Rule-Based** | < 1ms | Fast, deterministic |
| **AI Agent** | 30-120s | Pattern recognition, fraud detection |

**Result**: AI catches fraud patterns worth $15,000+ that rules approve.

---

## Live Deployment (AWS)

| Service | URL |
|---------|-----|
| **Unified Claims API** | https://p7qrmgi9sp.us-east-1.awsapprunner.com |
| **Agent Pipeline** | https://bn9ymuxtwp.us-east-1.awsapprunner.com |
| **API Documentation** | https://p7qrmgi9sp.us-east-1.awsapprunner.com/docs |

---

## Quick Start (Local)

```bash
# Terminal 1: Unified API (required)
cd src/shared/claims_data_api && uvicorn app.main:app --port 8000

# Terminal 2: Agent Pipeline (required)
cd src/ws6_agent_pipeline && uvicorn app.main:app --port 8006

# Terminal 3: Frontend
cd src/ws4_agent_portal && npm run dev

# Open: http://localhost:3000/pipeline/compare
```

---

## Demo Scenarios (28 Total)

### Fraud Detection (AI catches, Rules miss)

| ID | Scenario | Rule Result | AI Result |
|----|----------|-------------|-----------|
| FRAUD-001 | Chronic Condition Gaming | APPROVED | FLAGGED |
| FRAUD-002 | Provider Collusion | APPROVED | FLAGGED |
| FRAUD-003 | Staged Timing | APPROVED | FLAGGED |

### Data Validation (AI catches, Rules miss)

| ID | Scenario | Rule Result | AI Result |
|----|----------|-------------|-----------|
| VAL-001 | Diagnosis-Treatment Mismatch | APPROVED | FAIL |
| VAL-002 | Over-Treatment Detection | APPROVED | WARNING |
| VAL-003 | Missing Pre-Op Bloodwork | APPROVED | WARNING |
| VAL-004 | Expired Provider License | APPROVED | CRITICAL |
| VAL-005 | Controlled Substance Violation | APPROVED | FAIL |

### Standard Claims (20 scenarios: SCN-001 to SCN-020)

Baseline comparison scenarios covering emergency, surgery, chronic conditions.

---

## Architecture

```
┌──────────────────┐     ┌──────────────────┐
│  Rule-Based      │     │  AI Agent        │
│  (PetInsure360)  │     │  (EIS-Dynamics)  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         └──────────┬─────────────┘
                    │
         ┌──────────▼──────────┐
         │  Unified Claims API │
         │  (60 endpoints)     │
         │  (44 LLM tools)     │
         └─────────────────────┘
```

### Agent Pipeline (LangGraph)

```
Request → Router → Bronze → Silver → Gold → Decision
              │        │        │        │
              └────────┴────────┴────────┘
                    44 LLM Tools
```

---

## Services

| Port | Service | Purpose |
|------|---------|---------|
| **8000** | Unified Claims API | Core data gateway (60 endpoints) |
| **8006** | Agent Pipeline | LangGraph agents + comparison |
| 3000 | Frontend Portal | Next.js UI |
| 8001 | AI Claims | FNOL extraction |
| 8002 | Integration | EIS mock APIs |
| 8003 | Rating Engine | Premium calculation |

---

## Key Features

- **44 LLM Tools**: Policy, customer, pet, provider, fraud, validation
- **4 Agent Tiers**: Router, Bronze, Silver, Gold (medallion architecture)
- **Real-time Comparison**: Side-by-side code vs agent processing
- **28 Demo Scenarios**: Pre-built fraud, validation, standard claims

---

## Documentation

| Document | Purpose |
|----------|---------|
| [SHOWCASE_GUIDE.md](./SHOWCASE_GUIDE.md) | Step-by-step demo instructions |
| [RULE_VS_AI_COMPARISON.md](./RULE_VS_AI_COMPARISON.md) | All 28 scenarios documented |
| [SESSION_SUMMARY.md](./SESSION_SUMMARY.md) | Build history |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Backend | FastAPI, Python 3.11, Pydantic |
| AI | Claude AI, LangGraph |
| Infrastructure | AWS App Runner, ECR, Terraform |

---

## Version History

### v1.0.0 (January 2, 2026)
- Deployed to AWS (App Runner)
- Complete showcase documentation
- 28 demo scenarios validated

### v0.9.2 (January 1, 2025)
- Code vs Agent comparison
- 3 fraud + 5 validation scenarios

### v0.9.1 (December 31, 2024)
- AI Demo page
- ValidationService with 5 types
- 44 LLM tools
