# EIS-Dynamics POC - Showcase Guide

**Version**: 1.0.0 | **Last Updated**: January 2, 2026

---

## Overview

This guide provides step-by-step instructions for demonstrating the EIS-Dynamics AI-powered claims processing system compared to traditional rule-based processing.

**Key Message**: AI catches fraud and data quality issues that rule-based systems miss.

---

## Deployment Options

### Option A: AWS (Production)

| Service | URL |
|---------|-----|
| **Unified Claims API** | https://p7qrmgi9sp.us-east-1.awsapprunner.com |
| **Agent Pipeline API** | https://bn9ymuxtwp.us-east-1.awsapprunner.com |
| **API Documentation** | https://p7qrmgi9sp.us-east-1.awsapprunner.com/docs |

### Option B: Local Development

| Service | Port | Command |
|---------|------|---------|
| Unified Claims API | 8000 | `cd src/shared/claims_data_api && uvicorn app.main:app --port 8000` |
| Agent Pipeline | 8006 | `cd src/ws6_agent_pipeline && uvicorn app.main:app --port 8006` |
| Frontend Portal | 3000 | `cd src/ws4_agent_portal && npm run dev` |

---

## Architecture: UI to Backend Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                     │
│                                                                             │
│  Browser: http://localhost:3000/pipeline/compare                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Scenario Dropdown (grouped by FRAUD/VAL/SCN)                        │   │
│  │  [Run Comparison] button                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ User clicks "Run Comparison"
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js :3000)                             │
│                                                                             │
│  lib/pipeline-api.ts:                                                       │
│  ─────────────────────                                                      │
│  pipelineApi.runScenarioComparison("FRAUD-001")                            │
│  → POST /api/v1/compare/scenario/FRAUD-001                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP POST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT PIPELINE SERVICE (:8006)                           │
│                                                                             │
│  routers/comparison.py → compare_scenario_endpoint()                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  1. Load scenario from data/claim_scenarios.json                            │
│  2. Extract claim data                                                      │
│  3. Fork into TWO parallel processing paths:                                │
│                                                                             │
│  ┌────────────────────────┐        ┌────────────────────────────────────┐  │
│  │   CODE-DRIVEN (Rules)  │        │      AGENT-DRIVEN (AI)             │  │
│  ├────────────────────────┤        ├────────────────────────────────────┤  │
│  │ • 8 fixed business     │        │ • LangGraph Pipeline:              │  │
│  │   rules                │        │   Router → Bronze → Silver → Gold │  │
│  │ • Threshold checks     │        │ • 44 LLM tools                     │  │
│  │ • < 1ms processing     │        │ • 30-120s processing               │  │
│  │                        │        │                                    │  │
│  │ Result: APPROVED       │        │ Result: FLAGGED/MANUAL_REVIEW      │  │
│  └────────────────────────┘        └────────────────────────────────────┘  │
│                │                                │                           │
│                └────────────┬───────────────────┘                           │
│                             │ Both call Unified API                         │
└─────────────────────────────│───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     UNIFIED CLAIMS API (:8000)                              │
│                                                                             │
│  6 Services with 44 LLM Tools:                                              │
│  ─────────────────────────────                                              │
│  • PolicyService (6 tools) - Coverage, limits, exclusions                   │
│  • CustomerService (6 tools) - History, risk tier, LTV                      │
│  • PetService (5 tools) - Medical history, breed risks                      │
│  • ProviderService (5 tools) - Network status, license check                │
│  • FraudService (6 tools) - Pattern detection, velocity                     │
│  • ValidationService (6 tools) - AI-powered validation                      │
│  • MedicalService (5 tools) - Diagnosis validation                          │
│  • BillingService (5 tools) - Reimbursement calculation                     │
│                                                                             │
│  Data Sources: JSON files (claims, policies, customers, pets, providers)    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Merged results
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPARISON RESULT                                   │
│                                                                             │
│  {                                                                          │
│    "code_driven": {                                                         │
│      "final_decision": "auto_approve",                                      │
│      "risk_level": "low",                                                   │
│      "processing_time_ms": 0.5                                              │
│    },                                                                       │
│    "agent_driven": {                                                        │
│      "final_decision": "manual_review",                                     │
│      "risk_level": "high",                                                  │
│      "fraud_indicators": ["pre_existing_related", "anatomical_concentration"],│
│      "reasoning": "Pre-existing hip dysplasia. All claims orthopedic."      │
│    },                                                                       │
│    "comparison_metrics": {                                                  │
│      "decision_match": false,                                               │
│      "agent_advantages": ["Cross-claim pattern recognition"]                │
│    }                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Display in UI
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     UI COMPARISON DISPLAY                                   │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │      TIME           │  │     DECISION        │  │      PAYOUT         │ │
│  │  Code: 0.5ms        │  │  Code: APPROVE      │  │  Code: $1,600       │ │
│  │  Agent: 45s         │  │  Agent: REVIEW      │  │  Agent: $0 (held)   │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LAYER COMPARISON                                                     │   │
│  │ Bronze: Both validate data quality ✓                                 │   │
│  │ Silver: Both check policy coverage ✓                                 │   │
│  │ Gold:   Code says LOW RISK | Agent says HIGH RISK (fraud detected)  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Demo Script: Step-by-Step

### Preparation (5 minutes)

**For Local Demo:**
```bash
# Terminal 1: Start Unified API
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc
cd src/shared/claims_data_api && uvicorn app.main:app --port 8000

# Terminal 2: Start Agent Pipeline
cd src/ws6_agent_pipeline && uvicorn app.main:app --port 8006

# Terminal 3: Start Frontend
cd src/ws4_agent_portal && npm run dev
```

**For AWS Demo:**
- No setup needed - services are already running
- API: https://p7qrmgi9sp.us-east-1.awsapprunner.com
- Pipeline: https://bn9ymuxtwp.us-east-1.awsapprunner.com

---

### Demo 1: Fraud Detection (FRAUD-001 - Chronic Condition Gaming)

**Story to Tell:**
> "A pet owner named Rocky has a dog with documented hip dysplasia. They file multiple 'accident' claims for orthopedic issues, each just under our review threshold. Let's see how rule-based and AI systems handle this."

**Step 1: Open Comparison Page**
```
Local: http://localhost:3000/pipeline/compare
```

**Step 2: Select Scenario**
- Click dropdown → Select "FRAUD DETECTION" group
- Choose: `FRAUD-001: Chronic Condition Gaming`

**Step 3: Run Comparison**
- Click "Run Comparison" button
- Wait 30-60 seconds for AI processing

**Step 4: Explain Results**

| Aspect | Rule-Based | AI Agent |
|--------|------------|----------|
| **Decision** | APPROVED | MANUAL REVIEW |
| **Time** | < 1ms | ~45 seconds |
| **Risk Level** | Low | High |
| **Reasoning** | "Under threshold, valid policy" | "Pre-existing hip dysplasia, anatomical concentration" |

**Key Talking Points:**
1. "Rules see each claim in isolation - $1,600 is under our $2,000 threshold"
2. "AI analyzes the HISTORY - 4 prior orthopedic claims, documented pre-existing condition"
3. "AI detects the PATTERN - all claims focus on same body system"
4. "This would cost us $1,600 in fraud if approved by rules"

---

### Demo 2: Provider Collusion (FRAUD-002)

**Story to Tell:**
> "A customer exclusively uses one out-of-network provider. Every claim is mysteriously just under $5,000 - our automatic approval limit. Let's investigate."

**Select:** `FRAUD-002: Provider Collusion`

**Results:**

| Aspect | Rule-Based | AI Agent |
|--------|------------|----------|
| **Decision** | APPROVED | FLAGGED |
| **Amount** | $4,800 | $4,800 (suspicious) |
| **Provider** | Valid license | 15% revenue from 1 customer |

**Key Talking Points:**
1. "Rules only check: Is provider licensed? Is amount under limit? Yes and yes."
2. "AI asks: Why does this provider get 15% of revenue from ONE customer?"
3. "AI notices: Every claim is $4,800-4,900, just under $5,000 threshold"
4. "This is classic limit optimization - a strong fraud indicator"

---

### Demo 3: Data Quality (VAL-001 - Diagnosis-Treatment Mismatch)

**Story to Tell:**
> "A claim comes in with a CCL tear diagnosis but billing for dental cleaning. Let's see what happens."

**Select:** `VAL-001: Diagnosis-Treatment Mismatch`

**Results:**

| Aspect | Rule-Based | AI Agent |
|--------|------------|----------|
| **Decision** | APPROVED | FAIL |
| **Diagnosis** | S83.5 (valid code) | Orthopedic issue |
| **Treatment** | Dental codes (valid) | Wrong body system |

**Key Talking Points:**
1. "Rules validate: Is the diagnosis code valid? Yes. Are procedure codes valid? Yes."
2. "AI understands SEMANTICS: You don't do dental cleaning for a torn ligament"
3. "This is either data entry error OR intentional fraud"
4. "Either way, we should NOT auto-approve this claim"

---

### Demo 4: Controlled Substance Violation (VAL-005)

**Story to Tell:**
> "A claim includes Hydrocodone (Schedule II controlled substance) prescribed by a provider without DEA registration. This is actually illegal."

**Select:** `VAL-005: Controlled Substance Without DEA`

**Results:**

| Aspect | Rule-Based | AI Agent |
|--------|------------|----------|
| **Decision** | APPROVED | FAIL |
| **Medication** | "Hydrocodone" (text) | Schedule II controlled |
| **Provider DEA** | Not checked | Missing - ILLEGAL |

**Key Talking Points:**
1. "Rules don't parse medication names or understand drug schedules"
2. "AI identifies Hydrocodone as Schedule II - requires DEA registration"
3. "AI checks provider credentials - NO DEA NUMBER"
4. "This prescription is actually illegal - we cannot pay this claim"

---

## Technical Deep Dive

### API Endpoints Used

**Comparison Flow:**
```
POST /api/v1/compare/scenario/{scenarioId}
```

**Internal Calls During Processing:**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/policies/{id}` | Verify policy coverage |
| `GET /api/v1/customers/{id}` | Get customer history |
| `GET /api/v1/pets/{id}` | Get pet medical history |
| `GET /api/v1/providers/{id}` | Check provider credentials |
| `POST /api/v1/fraud/check` | Run fraud analysis |
| `POST /api/v1/validation/diagnosis-treatment` | Check treatment appropriateness |

### LangGraph Agent Pipeline

```
Request → Router Agent (classify complexity)
              ↓
         Bronze Agent (27 tools)
         • Validate data quality
         • Check completeness
         • Flag obvious issues
              ↓
         Silver Agent (13 tools)
         • Enrich with policy data
         • Add customer context
         • Calculate reimbursement
              ↓
         Gold Agent (44 tools - ALL)
         • Full fraud analysis
         • Medical validation
         • Final decision with reasoning
              ↓
         Response with decision + reasoning
```

---

## 28 Demo Scenarios Reference

### Fraud Scenarios (AI catches, Rules miss)

| ID | Name | Rule Result | AI Result | Key Indicator |
|----|------|-------------|-----------|---------------|
| FRAUD-001 | Chronic Condition Gaming | APPROVED | FLAGGED | Pre-existing + anatomical concentration |
| FRAUD-002 | Provider Collusion | APPROVED | FLAGGED | Customer-provider concentration |
| FRAUD-003 | Staged Timing | APPROVED | FLAGGED | Breed risk + timing anomaly |

### Validation Scenarios (AI catches, Rules miss)

| ID | Name | Rule Result | AI Result | Issue Detected |
|----|------|-------------|-----------|----------------|
| VAL-001 | Diagnosis-Treatment Mismatch | APPROVED | FAIL | Dental for orthopedic |
| VAL-002 | Over-Treatment | APPROVED | WARNING | MRI for allergies |
| VAL-003 | Missing Pre-Op | APPROVED | WARNING | Surgery without bloodwork |
| VAL-004 | Expired License | APPROVED | CRITICAL | Provider license expired |
| VAL-005 | DEA Violation | APPROVED | FAIL | Schedule II without DEA |

### Standard Claims (Baseline comparison)

| ID | Name | Amount | Type |
|----|------|--------|------|
| SCN-001 | Chocolate Toxicity | $1,355 | Emergency |
| SCN-002 | ACL Surgery | $5,935 | Orthopedic |
| SCN-003 | Diabetes Management | $1,155 | Chronic |
| SCN-004 | Foreign Body | $5,000 | Surgery |
| SCN-005 | Allergic Reaction | $1,060 | Emergency |
| SCN-006 | Dental Extraction | $2,115 | Dental |
| SCN-007 | Urinary Blockage | $2,665 | Emergency |
| SCN-008 | Skin Allergy | $1,225 | Chronic |
| SCN-009 | Hip Dysplasia | $2,045 | Orthopedic |
| SCN-010 | Lymphoma | $2,365 | Oncology |
| SCN-011 | Fracture (Hit by Car) | $7,020 | Trauma |
| SCN-012 | Seizure Workup | $3,400 | Neurology |
| SCN-013 | Pancreatitis | $2,400 | GI |
| SCN-014 | Corneal Ulcer | $3,075 | Ophthalmology |
| SCN-015 | Heartworm | $2,580 | Parasitic |
| SCN-016 | Broken Leg | $4,635 | Trauma |
| SCN-017 | Kidney Disease | $1,365 | Chronic |
| SCN-018 | Pyometra | $4,495 | Emergency |
| SCN-019 | GDV (Bloat) | $8,500 | Critical |
| SCN-020 | Wellness Exam | $520 | Preventive |

---

## Troubleshooting

### Common Issues

**1. Agent Pipeline timeout**
- AI processing takes 30-120 seconds
- If >2 minutes, check API key in `.env` or Secrets Manager

**2. "Service unavailable" on AWS**
- Check App Runner status in AWS Console
- Services may need 2-3 minutes after deployment

**3. Comparison shows same result**
- For SCN-001 to SCN-020, both systems often agree (legitimate claims)
- Use FRAUD-* or VAL-* scenarios to show differences

**4. Frontend can't connect**
- Verify NEXT_PUBLIC_API_URL in frontend `.env`
- For local: `http://localhost:8006`
- For AWS: Use AppRunner URL

---

## Key Takeaways for Audience

1. **Speed vs Intelligence Trade-off**: Rules are fast (<1ms) but blind to patterns. AI is slower (30-120s) but catches fraud.

2. **ROI**: One prevented $9,200 fraud claim (FRAUD-003) pays for months of AI processing costs.

3. **Compliance**: AI catches regulatory violations (expired licenses, DEA issues) that rules completely miss.

4. **Pattern Recognition**: AI correlates across claims, customers, and providers - rules see only current claim.

5. **Explainability**: AI provides reasoning for every decision, making human review efficient.

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────┐
│           EIS-DYNAMICS DEMO QUICK START            │
├────────────────────────────────────────────────────┤
│                                                    │
│  AWS URLS:                                         │
│  • API: https://p7qrmgi9sp.us-east-1.awsapprunner.com    │
│  • Pipeline: https://bn9ymuxtwp.us-east-1.awsapprunner.com│
│                                                    │
│  BEST DEMO SCENARIOS:                              │
│  • FRAUD-001: Pre-existing condition gaming        │
│  • FRAUD-002: Provider collusion pattern           │
│  • VAL-001: Dental for orthopedic (mismatch)       │
│  • VAL-005: Controlled substance violation         │
│                                                    │
│  KEY COMPARISON:                                   │
│  • Rules: <1ms, misses patterns                    │
│  • AI: 30-120s, catches fraud                      │
│                                                    │
│  EXPECTED RESULTS:                                 │
│  • Rules say: APPROVED                             │
│  • AI says: FLAGGED/MANUAL_REVIEW                  │
│                                                    │
└────────────────────────────────────────────────────┘
```

 1. Azure vs AWS - NO Issue!

  The comparison does NOT cross clouds. Here's why:

  ┌─────────────────────────────────────────────────────────────────┐
  │                    HOW COMPARISON WORKS                          │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  EIS-Dynamics (AWS) - SELF-CONTAINED COMPARISON                 │
  │  ─────────────────────────────────────────────                  │
  │                                                                  │
  │     POST /api/v1/compare/scenario/FRAUD-001                     │
  │                        │                                         │
  │         ┌──────────────┴──────────────┐                         │
  │         │                              │                         │
  │         ▼                              ▼                         │
  │   ┌───────────────┐           ┌───────────────┐                 │
  │   │ CODE PATH     │           │ AGENT PATH    │                 │
  │   │ (simulated    │           │ (LangGraph    │                 │
  │   │  rules)       │           │  AI agents)   │                 │
  │   │               │           │               │                 │
  │   │ 8 fixed rules │           │ 44 LLM tools  │                 │
  │   │ < 1ms         │           │ 30-120s       │                 │
  │   └───────────────┘           └───────────────┘                 │
  │         │                              │                         │
  │         └──────────────┬───────────────┘                         │
  │                        ▼                                         │
  │              Comparison Result                                   │
  │                                                                  │
  │  PetInsure360 (Azure) - SEPARATE DEMO                           │
  │  ────────────────────────────────────                           │
  │  • Used for showing REAL rule-based UI                          │
  │  • Same 28 scenarios synced for demo                            │
  │  • NOT called by EIS comparison endpoint                        │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘

  Bottom line: EIS-Dynamics has its own CodeProcessor that simulates rule-based logic. PetInsure360 is for showing the customer-facing rule-based portal separately.

  ---
  2. PetInsure360 Summary (Updated 2026-01-01)

  Status: FULLY LIVE on Azure

  | Component       | URL                                                  | Status |
  |-----------------|------------------------------------------------------|--------|
  | Customer Portal | https://petinsure360frontend.z5.web.core.windows.net | LIVE   |
  | Backend API     | https://petinsure360-backend.azurewebsites.net       | LIVE   |
  | API Docs        | https://petinsure360-backend.azurewebsites.net/docs  | LIVE   |
  | Databricks      | https://adb-7405619408519767.7.azuredatabricks.net   | LIVE   |

  Infrastructure:
  - Azure Web App (UK West, B1 Basic)
  - ADLS Gen2 (petinsud7i43)
  - Databricks Cluster: PetInsure360-Demo-v2
  - ETL: All notebooks deployed and running

  Data:
  - 5,000 Customers
  - 6,500 Pets
  - 6,000 Policies
  - 15,000 Claims
  - Gold layer: 39 Delta files

  28 Scenarios (synced with EIS-Dynamics):
  - 20 Standard claims (SCN-001 to SCN-020)
  - 3 Fraud scenarios (FRAUD-001 to FRAUD-003)
  - 5 Validation scenarios (VAL-001 to VAL-005)

  Features:
  - Pipeline visualization at /pipeline
  - Real-time WebSocket updates
  - Manual Bronze→Silver→Gold triggers
  - Customer 360 view

  ---
  Demo Strategy

  | Demo Step                           | Platform                | URL                                                             |
  |-------------------------------------|-------------------------|-----------------------------------------------------------------|
  | 1. Show rule-based customer portal  | PetInsure360 (Azure)    | https://petinsure360frontend.z5.web.core.windows.net            |
  | 2. Submit claim via UI              | PetInsure360            | /claim page                                                     |
  | 3. Show rule-based result: APPROVED | PetInsure360            | /pipeline                                                       |
  | 4. Show AI comparison               | EIS-Dynamics (AWS)      | https://bn9ymuxtwp.us-east-1.awsapprunner.com/api/v1/scenarios/ |
  | 5. Same scenario → AI says FLAGGED  | EIS comparison endpoint | POST /api/v1/compare/scenario/FRAUD-001                         |

  
