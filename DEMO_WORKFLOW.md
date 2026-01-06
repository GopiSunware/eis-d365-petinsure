# Demo Workflow Documentation

## Overview

This document describes the complete demo workflows for both **PetInsure360** and **EIS Dynamics POC** projects, including the integration points and any known issues.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PETINSURE360                                    │
│                          (Rule-Based Processing)                             │
│                                                                              │
│   Customer Portal (3000)  →  Backend API (3002)  →  BI Dashboard (3001)     │
│                                    │                                         │
│                                    ├── Legacy Pipeline (Bronze→Silver→Gold) │
│                                    ├── DocGen Integration (8007)             │
│                                    └── Agent Pipeline Integration (8006)     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EIS DYNAMICS                                    │
│                         (Agent-Driven Processing)                            │
│                                                                              │
│   WS7 DocGen (8007)  →  WS6 Agent Pipeline (8006)  →  Claims Data API (8000)│
│        │                        │                                            │
│        └── AI Document          └── Medallion Architecture                   │
│            Processing               (Router→Bronze→Silver→Gold Agents)       │
│                                                                              │
│   WS4 Agent Portal (8080)        WS8 Admin Portal (8081)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow 1: Claim Submission via Dropdown

### Expected Flow
```
User selects scenario from dropdown → Submits claim form →
Goes to Legacy Pipeline (Bronze layer) + Agent Pipeline →
Manual click to process through layers → User gets results
```

### Current Implementation

**Frontend:** `petinsure360/frontend/src/pages/ClaimPage.jsx`
- Line 159: Comment states "Use the new pipeline submit-claim endpoint for Bronze layer ingestion"
- Line 182: `api.post('/pipeline/submit-claim', submitData)`

**Backend:** `petinsure360/backend/app/api/pipeline.py`
- Endpoint: `POST /pipeline/submit-claim` (lines 139-215)
- Creates claim in Bronze layer (local in-memory + disk persistence)
- Writes to ADLS if configured
- Emits WebSocket event `claim_to_bronze`

### Status: ✅ FULLY WORKING

**All Pipelines Triggered:**
- ✅ Legacy Pipeline - Bronze layer ingestion (rule-based)
- ✅ Agent Pipeline (WS6) - AI-driven medallion architecture
- ✅ DocGen Service (WS7) - AI batch processing for BI Dashboard
- ✅ WebSocket real-time updates
- ✅ State persistence to `/tmp/docgen/pipeline_state.json`

### Implementation Details

**Backend:** `petinsure360/backend/app/api/pipeline.py`
- Endpoint: `POST /pipeline/submit-claim` (lines 234-364)
- Triggers all THREE processing paths in parallel
- Returns detailed status for each pipeline

### Manual Processing Steps (BI Dashboard)

1. Navigate to BI Dashboard → Pipeline page (http://localhost:3001/pipeline)
2. Click "Process Bronze → Silver" button
3. Click "Process Silver → Gold" button
4. Claims appear in Claims Analytics page

---

## Workflow 2: Document Upload → DocGen → Claim Creation

### Expected Flow
```
User uploads document(s) → Creates claim in system →
DocGen service processes → AI Agent analyzes → User gets result
```

### Current Implementation

**Frontend:** `petinsure360/frontend/src/pages/UploadDocsPage.jsx`
- Drag & drop file upload interface
- Submits to `/docgen/upload` endpoint
- Real-time status updates via WebSocket

**Backend:** `petinsure360/backend/app/api/docgen.py`
- Endpoint: `POST /docgen/upload` (lines 72-156)
- Saves files to `/tmp/petinsure360_uploads/{upload_id}/`
- Background processing forwards to WS7 DocGen (8007)

**DocGen Agent:** `eis-dynamics-poc/src/ws7_docgen/app/agents/docgen_agent.py`
- Uses Claude AI for document processing
- 5 tools: check_duplicate, extract_document, validate_claim, calculate_billing, submit_claim
- Strict fraud detection rules

### Status: ✅ WORKING

**Complete Flow:**
1. User uploads documents via Customer Portal
2. PetInsure360 Backend saves files locally
3. Background task forwards to WS7 DocGen (8007)
4. DocGen AI Agent processes documents
5. Claim created if AI decision is `auto_approve`, `standard_review`, or `proceed`
6. WebSocket events notify user: `docgen_completed` or `docgen_failed`

---

## Workflow 3: Legacy (Azure) Medallion Processing

### Expected Flow
```
Claims in Azure → Processed via Bronze → Silver → Gold medallion layers
```

### Current Implementation

**Backend:** `petinsure360/backend/app/api/pipeline.py`

**Bronze Layer** (Raw Ingestion):
- Endpoint: `POST /pipeline/submit-claim`
- No transformation, raw data storage
- Metadata: `ingestion_timestamp`, `source`, `layer: "bronze"`

**Silver Layer** (Validation & Cleaning):
- Endpoint: `POST /pipeline/process/bronze-to-silver`
- Data type standardization
- Line items validation
- Completeness scoring (0-100)
- Validity scoring (0-100)
- Deduplication check

**Gold Layer** (Aggregation & Enrichment):
- Endpoint: `POST /pipeline/process/silver-to-gold`
- Customer dimension join
- Policy dimension join
- Reimbursement calculation
- Processing priority assignment
- Persists to Azure Storage

### Status: ✅ WORKING

**Manual Processing via BI Dashboard:**
1. Claims submitted → Bronze layer
2. Click "Process Bronze → Silver" → Silver layer
3. Click "Process Silver → Gold" → Gold layer + Dashboard display

---

## Workflow 4: Agent (Local/AWS) AI Processing

### Expected Flow
```
Agent Pipeline processes claims → AI analyzes → Returns decision with reasoning
```

### Current Implementation

**EIS Dynamics WS6:** `eis-dynamics-poc/src/ws6_agent_pipeline/`

**Pipeline Architecture:**
1. **Router Agent** - Determines claim complexity (simple/medium/complex)
2. **Bronze Agent** - Data validation, anomaly detection, quality scoring
3. **Silver Agent** - Data enrichment, normalization, coverage validation
4. **Gold Agent** - Risk assessment, fraud detection, final decisions

**AI Integration:**
- Uses Claude (Anthropic) or OpenAI based on config
- Event streaming via WebSocket at `/ws/run/{run_id}`

**Fraud Detection (Gold Agent):**
- 3 fraud patterns: Chronic Condition Gaming, Provider Collusion, Staged Timing
- Tools: `calculate_fraud_score`, `velocity_check`, `duplicate_check`, `fraud_pattern_match`
- Decisions: AUTO_APPROVE, STANDARD_REVIEW, MANUAL_REVIEW, INVESTIGATION

### Status: ✅ WORKING (but not auto-triggered from PetInsure360)

**Trigger Methods:**
1. Direct API: `POST http://localhost:8006/api/v1/pipeline/trigger`
2. WS4 Agent Portal: Select scenario → Click "Run Pipeline"
3. Demo endpoint: `POST /api/v1/pipeline/demo/claim?complexity=simple|medium|complex`

---

## Workflow 5: Claims Analytics Shows New Claims

### Expected Flow
```
New claims submitted → Claims Analytics dashboard shows them
```

### Current Implementation

**BI Dashboard:** `petinsure360/bi-dashboard/src/pages/ClaimsPage.jsx`

**Data Sources (3):**
1. Gold Layer Claims: `/api/insights/claims`
2. Pipeline Pending Claims: `/api/pipeline/pending`
3. Agent Pipeline Batches: `http://localhost:8007/api/v1/docgen/batches`

### Status: ✅ WORKING

**Note:** Claims appear AFTER processing, not immediately after submission.

**For Legacy Pipeline:**
- Claims visible after `Silver → Gold` processing

**For DocGen:**
- Claims visible after AI processing completes

---

## Workflow 6: Customer Dashboard Shows New Users

### Expected Flow
```
New user registers → Customer Dashboard shows them
```

### Current Implementation

**Frontend:** `petinsure360/frontend/src/pages/RegisterPage.jsx`
- POST to `/customers/` creates new customer
- Emits WebSocket `customer_created` event

**BI Dashboard:** `petinsure360/bi-dashboard/src/pages/CustomersPage.jsx`
- Fetches from `/api/insights/customers`
- Search, filter by tier/risk
- Customer detail card with metrics

### Status: ✅ WORKING

**Demo Users:**
- DEMO-001 (demo@demologin.com)
- DEMO-002 (demo1@demologin.com)
- DEMO-003 (demo2@demologin.com)

---

## Summary Table

| Workflow | Status | Notes |
|----------|--------|-------|
| Claim Dropdown → Legacy + Agent | ✅ WORKING | Triggers all 3 pipelines |
| Document Upload → DocGen → Claim | ✅ WORKING | Full AI agent processing |
| Legacy Medallion (B→S→G) | ✅ WORKING | Manual trigger buttons |
| Agent AI Processing (WS6) | ✅ WORKING | Auto-triggered from PetInsure360 |
| Claims Analytics Display | ✅ WORKING | Shows after processing |
| Customer Dashboard | ✅ WORKING | Shows registered users |

---

## Resolved Issues

### Issue #1: Claim Submission Now Triggers All Pipelines ✅ FIXED

**Fixed On:** 2025-01-05

**Location:**
- `petinsure360/backend/app/api/pipeline.py:234-364`

**Solution:**
Modified `submit_claim_to_bronze()` to trigger THREE parallel processing paths:
1. **Legacy Pipeline** - Bronze layer ingestion (rule-based, manual processing)
2. **Agent Pipeline (WS6)** - AI-driven medallion architecture
3. **DocGen Service (WS7)** - AI batch processing for BI Dashboard

**New Response Format:**
```json
{
  "success": true,
  "claim_id": "CLM-XXXXXXXX",
  "claim_number": "CLM-20250105-XXXXXX",
  "layer": "bronze",
  "pipelines": {
    "legacy": {"status": "ingested", "message": "..."},
    "agent": {"status": "triggered", "run_id": "RUN-XXXXX"},
    "docgen": {"status": "created", "batch_id": "BATCH-XXXXX"}
  }
}
```

---

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Customer Portal | 3000 | User-facing UI |
| BI Dashboard | 3001 | Analytics UI |
| PetInsure360 Backend | 3002 | API Gateway |
| Claims Data API | 8000 | Unified Data Store |
| WS6 Agent Pipeline | 8006 | AI Claims Processing |
| WS7 DocGen | 8007 | Document Processing |
| WS4 Agent Portal | 8080 | Agent UI |
| WS8 Admin Portal | 8081 | Admin UI |

---

## Quick Start Demo

### 1. Start All Services

```bash
# PetInsure360
cd petinsure360/backend && uvicorn app.main:socket_app --port 3002 --reload
cd petinsure360/frontend && npm run dev
cd petinsure360/bi-dashboard && npm run dev

# EIS Dynamics (optional for Agent Pipeline)
cd eis-dynamics-poc/src/ws6_agent_pipeline && uvicorn app.main:app --port 8006 --reload
cd eis-dynamics-poc/src/ws7_docgen && uvicorn app.main:app --port 8007 --reload
```

### 2. Demo Flow A: Legacy Pipeline

1. Open Customer Portal: http://localhost:3000
2. Login with demo@demologin.com
3. Submit Claim → Select scenario → Submit
4. Open BI Dashboard: http://localhost:3001/pipeline
5. Click "Process Bronze → Silver"
6. Click "Process Silver → Gold"
7. View in Claims Analytics

### 3. Demo Flow B: Document Upload (AI)

1. Open Customer Portal: http://localhost:3000
2. Login with demo@demologin.com
3. Go to "Upload Documents"
4. Drop vet invoice/receipt files
5. Wait for AI processing (real-time updates)
6. View created claim

### 4. Demo Flow C: Agent Pipeline (Direct)

1. Open WS4 Agent Portal: http://localhost:8080
2. Select scenario from dropdown
3. Click "Run Pipeline"
4. Watch real-time agent reasoning
5. View final decision

---

## Last Updated

2025-01-05 - Initial documentation based on code review
