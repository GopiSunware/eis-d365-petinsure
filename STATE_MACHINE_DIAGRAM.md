# State Machine & Architecture Diagram

Comprehensive visualization of all components, state transitions, and data flows in the PetInsure360 / EIS Dynamics platform.

---

## Table of Contents
1. [High-Level Architecture](#1-high-level-architecture)
2. [Component Communication Matrix](#2-component-communication-matrix)
3. [Claim Processing State Machine](#3-claim-processing-state-machine)
4. [Pipeline State Transitions](#4-pipeline-state-transitions)
5. [LangGraph Agent Pipeline](#5-langgraph-agent-pipeline)
6. [Document Processing Flow](#6-document-processing-flow)
7. [WebSocket Event Flow](#7-websocket-event-flow)
8. [Data Layer Architecture](#8-data-layer-architecture)
9. [Service Endpoints Reference](#9-service-endpoints-reference)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACES                                       │
├────────────────────┬────────────────────┬────────────────────┬────────────────────────────┤
│   Customer Portal  │    BI Dashboard    │   Agent Portal     │     Admin Portal          │
│   (React/Vite)     │    (React/Vite)    │   (Next.js)        │     (Next.js)             │
│   Port 3000 / S3   │    Port 3001 / S3  │   Port 8080 / S3   │     Port 8081 / S3        │
│                    │                    │                    │                            │
│  • Login           │  • Analytics       │  • Claims Flow     │  • AI Configuration       │
│  • View Pets       │  • Pipeline View   │  • React Flow      │  • Approvals Queue        │
│  • Submit Claims   │  • Customer 360    │  • AI Chat         │  • Audit Logs             │
│  • Upload Docs     │  • DocGen Admin    │  • Scenarios       │  • Cost Monitoring        │
└────────┬───────────┴─────────┬──────────┴─────────┬──────────┴──────────┬─────────────────┘
         │                     │                    │                     │
         │ HTTP/WS             │ HTTP/WS            │ HTTP/WS             │ HTTP
         ▼                     ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    BACKEND SERVICES                                      │
├──────────────────────────┬─────────────────────────┬────────────────────────────────────┤
│  PetInsure360 Backend    │    Claims Data API      │     Agent Pipeline                 │
│  (FastAPI + Socket.IO)   │    (FastAPI)            │     (FastAPI + LangGraph)          │
│  Port 3002 / App Runner  │    Port 8000 / AppRunner│     Port 8006 / App Runner         │
│                          │                         │                                    │
│  • /api/customers        │  • /api/chat/*          │  • /api/v1/pipeline/trigger        │
│  • /api/claims           │  • /api/v1/config/*     │  • /api/v1/pipeline/run/{id}       │
│  • /api/pipeline         │  • /api/v1/approvals/*  │  • /ws/events                      │
│  • /api/insights         │  • /api/v1/audit/*      │                                    │
│  • /api/docgen (proxy)   │  • /api/v1/scenarios/*  │  LangGraph Agents:                 │
│  • /ws (WebSocket)       │  • /api/v1/costs/*      │  • Router Agent                    │
│                          │                         │  • Bronze Agent                    │
├──────────────────────────┤                         │  • Silver Agent                    │
│   DocGen Service         │                         │  • Gold Agent                      │
│   Port 8007 / App Runner │                         │                                    │
│                          │                         │                                    │
│  • Document AI           │                         │                                    │
│  • Batch Processing      │                         │                                    │
│  • Extraction            │                         │                                    │
└─────────────┬────────────┴────────────┬────────────┴─────────────────┬──────────────────┘
              │                         │                              │
              │                         │                              │
              ▼                         ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA & AI LAYER                                       │
├────────────────────────────┬────────────────────────────┬────────────────────────────────┤
│     Azure ADLS Gen2        │      In-Memory Cache       │       AI Providers             │
│     (Medallion Lakehouse)  │      (InsightsService)     │                                │
│                            │                            │                                │
│  Bronze: raw/claims/       │  • Customers DataFrame     │  • OpenAI GPT-4o               │
│  Silver: processed/        │  • Pets DataFrame          │  • Anthropic Claude            │
│  Gold: aggregated/         │  • Claims DataFrame        │                                │
│                            │  • Policies DataFrame      │                                │
│  Container: petinsud7i43   │  • Pipeline State          │                                │
└────────────────────────────┴────────────────────────────┴────────────────────────────────┘
```

---

## 2. Component Communication Matrix

```
┌───────────────────┬─────────────────────────────────────────────────────────────────────┐
│    SOURCE         │                        DESTINATION                                   │
│                   ├────────────┬────────────┬────────────┬────────────┬────────────────┤
│                   │ PetIns360  │ Claims API │ Agent Pipe │ DocGen     │ Azure ADLS     │
│                   │ (3002)     │ (8000)     │ (8006)     │ (8007)     │                │
├───────────────────┼────────────┼────────────┼────────────┼────────────┼────────────────┤
│ Customer Portal   │ ●━━━━━━━━━▶│            │            │            │                │
│ (3000)            │  REST+WS   │            │            │            │                │
├───────────────────┼────────────┼────────────┼────────────┼────────────┼────────────────┤
│ BI Dashboard      │ ●━━━━━━━━━▶│            │ ●━━━━━━━━━▶│            │                │
│ (3001)            │  REST+WS   │            │  REST+WS   │            │                │
├───────────────────┼────────────┼────────────┼────────────┼────────────┼────────────────┤
│ Agent Portal      │            │ ●━━━━━━━━━▶│ ●━━━━━━━━━▶│ ●━━━━━━━━━▶│                │
│ (8080)            │            │  REST      │  REST+WS   │  REST      │                │
├───────────────────┼────────────┼────────────┼────────────┼────────────┼────────────────┤
│ Admin Portal      │            │ ●━━━━━━━━━▶│            │            │                │
│ (8081)            │            │  REST      │            │            │                │
├───────────────────┼────────────┼────────────┼────────────┼────────────┼────────────────┤
│ PetIns360 Backend │            │            │ ●━━━━━━━━━▶│ ●━━━━━━━━━▶│ ●━━━━━━━━━━━━▶│
│ (3002)            │            │            │  REST      │  REST      │  SDK           │
├───────────────────┼────────────┼────────────┼────────────┼────────────┼────────────────┤
│ Agent Pipeline    │            │            │            │            │ ●━━━━━━━━━━━━▶│
│ (8006)            │            │            │            │            │  S3/ADLS       │
└───────────────────┴────────────┴────────────┴────────────┴────────────┴────────────────┘

Legend: ●━━━▶ = HTTP/REST Call    ═══▶ = WebSocket    ─ ─ ─▶ = Async/Event
```

---

## 3. Claim Processing State Machine

### Main Claim Lifecycle

```
                                    ┌─────────────────┐
                                    │   USER ACTION   │
                                    │  Submit Claim   │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │     CLAIM CREATED            │
                              │  Status: SUBMITTED           │
                              │  claim_id: CLM-XXXXXXXX      │
                              └──────────────┬───────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
        ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
        │  LEGACY PIPELINE  │   │  AGENT PIPELINE   │   │  DOCGEN SERVICE   │
        │  (Rule-Based)     │   │  (AI/LangGraph)   │   │  (Document AI)    │
        └─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
                  │                       │                       │
                  ▼                       ▼                       ▼
        ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
        │  BRONZE LAYER   │     │  ROUTER AGENT   │     │  DOCUMENT       │
        │  Raw Ingestion  │     │  Complexity     │     │  EXTRACTION     │
        │  quality_score  │     │  Assessment     │     │  OCR + AI       │
        └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
                 │                       │                       │
        [Manual Trigger]          [Automatic]             [Automatic]
                 │                       │                       │
                 ▼                       ▼                       ▼
        ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
        │  SILVER LAYER   │     │  BRONZE AGENT   │     │  CLASSIFICATION │
        │  Validation     │     │  Validation     │     │  Document Type  │
        │  Cleansing      │     │  Data Quality   │     │  Data Extract   │
        └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
                 │                       │                       │
        [Manual Trigger]          [Automatic]             [Automatic]
                 │                       │                       │
                 ▼                       ▼                       ▼
        ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
        │  GOLD LAYER     │     │  SILVER AGENT   │     │  BATCH RESULT   │
        │  Aggregation    │     │  Enrichment     │     │  Linked to      │
        │  KPI Ready      │     │  Context Add    │     │  Claim Record   │
        └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
                 │                       │                       │
                 │                       ▼                       │
                 │              ┌─────────────────┐              │
                 │              │  GOLD AGENT     │              │
                 │              │  Risk Score     │              │
                 │              │  Fraud Detect   │              │
                 │              │  Decision       │              │
                 │              └────────┬────────┘              │
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────────┐
                          │      FINAL DECISION          │
                          │                              │
                          │  ┌─────────┐ ┌──────────┐   │
                          │  │AUTO     │ │NEEDS     │   │
                          │  │APPROVE  │ │REVIEW    │   │
                          │  └────┬────┘ └────┬─────┘   │
                          │       │           │         │
                          │       ▼           ▼         │
                          │  ┌─────────┐ ┌──────────┐   │
                          │  │APPROVED │ │HUMAN     │   │
                          │  │         │ │REVIEW    │   │
                          │  └─────────┘ └────┬─────┘   │
                          │                   │         │
                          │       ┌───────────┴─────┐   │
                          │       ▼                 ▼   │
                          │  ┌─────────┐     ┌────────┐ │
                          │  │APPROVED │     │DENIED  │ │
                          │  └─────────┘     └────────┘ │
                          └──────────────────────────────┘
```

---

## 4. Pipeline State Transitions

### Legacy Pipeline (Rule Engine)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RULE ENGINE PIPELINE                                 │
│                     (Manual Step-by-Step Processing)                         │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌───────────┐         ┌───────────┐         ┌───────────┐         ┌───────────┐
     │  SUBMIT   │         │  BRONZE   │         │  SILVER   │         │   GOLD    │
     │  CLAIM    │────────▶│  LAYER    │────────▶│  LAYER    │────────▶│  LAYER    │
     └───────────┘         └───────────┘         └───────────┘         └───────────┘
           │                     │                     │                     │
           │                     │                     │                     │
           ▼                     ▼                     ▼                     ▼
    ┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
    │ Validation  │       │Transformations│     │Transformations│     │Transformations│
    │ • Pet has   │       │ • Data type  │       │ • Customer   │       │ • Display in │
    │   policy    │       │   standard   │       │   dimension  │       │   BI Dash   │
    │ • Policy    │       │ • Line items │       │   join       │       │ • Include   │
    │   active    │       │   validate   │       │ • Policy     │       │   in KPIs   │
    │ • Amount    │       │ • Complete-  │       │   dimension  │       │ • Update    │
    │   valid     │       │   ness score │       │   join       │       │   Customer  │
    └─────────────┘       │ • Validity   │       │ • Reimburse- │       │   360       │
                          │   score      │       │   ment calc  │       └─────────────┘
                          │ • Quality    │       │ • Network    │
                          │   score      │       │   adjustment │
                          │ • Dedup      │       │ • Priority   │
                          │   check      │       │   assign     │
                          └─────────────┘       └─────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                              STATE STORAGE                                   │
    │                                                                              │
    │   pipeline_state = {                                                         │
    │       "pending_claims": [],        # Bronze → waiting for Silver trigger     │
    │       "silver_claims": [],         # Silver → waiting for Gold trigger       │
    │       "gold_claims": [],           # Gold → ready for analytics              │
    │       "processing_log": [          # Audit trail                             │
    │           {"timestamp": "...", "action": "BRONZE_INGEST", "claim_id": "..."} │
    │       ],                                                                     │
    │       "last_bronze_process": "2026-01-11T...",                               │
    │       "last_silver_process": "2026-01-11T...",                               │
    │       "last_gold_process": "2026-01-11T..."                                  │
    │   }                                                                          │
    │                                                                              │
    │   Persisted to: data/pipeline/pipeline_state.json                            │
    └─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                          PROCESSING PROOF                                    │
    │                                                                              │
    │   Bronze → Silver Response:                                                  │
    │   {                                                                          │
    │     "execution_mode": "python_local",                                        │
    │     "execution_engine": "PetInsure360 Backend (Python/FastAPI)",             │
    │     "notebook_executed": false,                                              │
    │     "transformations_applied": [                                             │
    │       "Data type standardization (claim_amount → decimal)",                  │
    │       "Line items validation (sum check)",                                   │
    │       "Completeness scoring (required fields check)",                        │
    │       "Validity scoring (business rules)",                                   │
    │       "Deduplication check (claim_id uniqueness)"                            │
    │     ],                                                                       │
    │     "processing_proof": [                                                    │
    │       {"claim_id": "...", "completeness_score": 100, "validity_score": 85}   │
    │     ]                                                                        │
    │   }                                                                          │
    └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. LangGraph Agent Pipeline

### Agent State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH AGENT PIPELINE                                │
│                    (Automatic AI-Driven Processing)                          │
└─────────────────────────────────────────────────────────────────────────────┘

                            ┌───────────────────┐
                            │   ENTRY POINT     │
                            │   POST /trigger   │
                            └─────────┬─────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │     ROUTER AGENT       │
                         │                        │
                         │  Determine Complexity: │
                         │  • simple              │
                         │  • medium              │
                         │  • complex             │
                         │  • error               │
                         └───────────┬────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │  complexity:    │   │  complexity:    │   │  complexity:    │
    │  "error"        │   │  "simple"       │   │  "complex"      │
    └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
             │                     │                     │
             ▼                     │                     │
    ┌─────────────────┐            │                     │
    │     REJECT      │            │                     │
    │   (Early Exit)  │            │                     │
    └─────────────────┘            ▼                     ▼
                         ┌─────────────────────────────────────┐
                         │          BRONZE AGENT               │
                         │                                     │
                         │  • Validate claim data              │
                         │  • Clean and standardize            │
                         │  • Assess data quality              │
                         │  • Write bronze_output to S3        │
                         │                                     │
                         │  Output:                            │
                         │  {                                  │
                         │    "validation_status": "pass",     │
                         │    "data_quality_score": 0.95,      │
                         │    "issues_found": []               │
                         │  }                                  │
                         └───────────────┬─────────────────────┘
                                         │
                      ┌──────────────────┴──────────────────┐
                      │                                     │
                      ▼                                     ▼
            ┌─────────────────┐                   ┌─────────────────┐
            │  validation:    │                   │  validation:    │
            │  "reject"       │                   │  "continue"     │
            └────────┬────────┘                   └────────┬────────┘
                     │                                     │
                     ▼                                     ▼
            ┌─────────────────┐             ┌─────────────────────────────────┐
            │     REJECT      │             │          SILVER AGENT           │
            │  (Stop Process) │             │                                 │
            └─────────────────┘             │  • Enrich with customer data    │
                                            │  • Add policy context           │
                                            │  • Historical claim analysis    │
                                            │  • Write silver_output to S3    │
                                            │                                 │
                                            │  Output:                        │
                                            │  {                              │
                                            │    "customer_context": {...},   │
                                            │    "policy_details": {...},     │
                                            │    "historical_claims": [...]   │
                                            │  }                              │
                                            └───────────────┬─────────────────┘
                                                            │
                                                            ▼
                                            ┌─────────────────────────────────┐
                                            │           GOLD AGENT            │
                                            │                                 │
                                            │  • Generate risk score          │
                                            │  • Fraud detection              │
                                            │  • Coverage verification        │
                                            │  • Make final decision          │
                                            │  • Write gold_output to S3      │
                                            │                                 │
                                            │  Output:                        │
                                            │  {                              │
                                            │    "risk_score": 0.25,          │
                                            │    "fraud_indicators": [],      │
                                            │    "coverage_verified": true,   │
                                            │    "decision": "auto_approve",  │
                                            │    "recommended_payout": 3800   │
                                            │  }                              │
                                            └───────────────┬─────────────────┘
                                                            │
                                                            ▼
                                            ┌─────────────────────────────────┐
                                            │         COMPLETED               │
                                            │                                 │
                                            │  Final Status:                  │
                                            │  • auto_approve → Direct pay    │
                                            │  • needs_review → Human queue   │
                                            │  • reject → Deny claim          │
                                            │                                 │
                                            │  Events Published:              │
                                            │  • pipeline_completed           │
                                            │  • claim_decision_made          │
                                            └─────────────────────────────────┘


    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                          PIPELINE STATE OBJECT                               │
    │                                                                              │
    │   class MedallionPipelineState:                                              │
    │       run_id: str                    # Unique run identifier                 │
    │       claim_id: str                  # Claim being processed                 │
    │       claim_data: dict               # Original claim payload                │
    │       current_stage: str             # ROUTER|BRONZE|SILVER|GOLD            │
    │       complexity: str                # simple|medium|complex                 │
    │       processing_path: str           # standard|express|detailed             │
    │       bronze_output: dict            # Bronze agent results                  │
    │       silver_output: dict            # Silver agent results                  │
    │       gold_output: dict              # Gold agent results                    │
    │       final_decision: str            # auto_approve|needs_review|reject      │
    │       status: PipelineStatus         # STARTED|RUNNING|COMPLETED|FAILED     │
    │       error: Optional[str]           # Error message if failed               │
    │       total_processing_time_ms: int  # End-to-end time                       │
    └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Document Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DOCUMENT UPLOAD & PROCESSING                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐                              ┌───────────────────┐
    │   Customer    │  POST /api/docgen/upload     │   PetInsure360    │
    │   Portal      │─────────────────────────────▶│   Backend (3002)  │
    │   (3000)      │                              │                   │
    └───────────────┘                              └─────────┬─────────┘
                                                             │
                                                             │ Store locally
                                                             │ Create upload_record
                                                             │
                                                             ▼
                                            ┌─────────────────────────────┐
                                            │      upload_records         │
                                            │                             │
                                            │  {                          │
                                            │    upload_id: "uuid",       │
                                            │    customer_id: "DEMO-001", │
                                            │    status: "uploaded",      │
                                            │    files: [...],            │
                                            │    created_at: "..."        │
                                            │  }                          │
                                            └──────────────┬──────────────┘
                                                           │
                         ┌─────────────────────────────────┴─────────────────────┐
                         │                                                       │
                         ▼                                                       ▼
            ┌─────────────────────────┐                          ┌─────────────────────────┐
            │    DocGen Service       │                          │    WebSocket Emit       │
            │    POST /api/v1/docgen/ │                          │                         │
            │    batch/from-claim     │                          │    Event: docgen_upload │
            └───────────┬─────────────┘                          │    {                    │
                        │                                        │      upload_id: "...",  │
                        ▼                                        │      status: "uploaded" │
            ┌─────────────────────────┐                          │    }                    │
            │   AI Document Analysis  │                          └─────────────────────────┘
            │                         │
            │   • OCR Text Extract    │
            │   • Document Type       │
            │   • Data Extraction     │
            │   • Validation          │
            └───────────┬─────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐   ┌──────────┐   ┌─────────┐
    │ SUCCESS │   │ NEEDS    │   │ FAILED  │
    │         │   │ REVIEW   │   │         │
    └────┬────┘   └────┬─────┘   └────┬────┘
         │             │              │
         ▼             ▼              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                      UPDATE UPLOAD RECORD                        │
    │                                                                  │
    │   status: "completed" | "failed"                                 │
    │   ai_decision: "auto_approve" | "needs_review" | "reject"        │
    │   extracted_data: {...}                                          │
    │   error_message: "..." (if failed)                               │
    └───────────────────────────────┬─────────────────────────────────┘
                                    │
                                    │ WebSocket Events
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                      BROADCAST TO CLIENTS                        │
    │                                                                  │
    │   • docgen_status     → Processing status update                 │
    │   • docgen_completed  → Success with results                     │
    │   • docgen_failed     → Error with message                       │
    │                                                                  │
    │   Receivers:                                                     │
    │   • Customer Portal (show "In Review" status)                    │
    │   • BI Dashboard (show in DocGen Admin page)                     │
    └─────────────────────────────────────────────────────────────────┘


    ┌─────────────────────────────────────────────────────────────────┐
    │                     UPLOAD STATUS STATES                         │
    │                                                                  │
    │   "uploaded"    → File received, not yet processed               │
    │   "queued"      → In processing queue                            │
    │   "processing"  → AI actively analyzing                          │
    │   "completed"   → Successfully processed                         │
    │   "failed"      → Error during processing                        │
    │                                                                  │
    │   Customer Portal Display:                                       │
    │   • completed → "Processed" (green)                              │
    │   • failed    → "In Review" (amber) - NEVER show "Failed"        │
    │   • others    → "Processing" (blue)                              │
    └─────────────────────────────────────────────────────────────────┘
```

---

## 7. WebSocket Event Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WEBSOCKET EVENT ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                    PetInsure360 Backend (Port 3002)                       │
    │                    Socket.IO / Native WebSocket                           │
    ├──────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    Event Emitters (Backend Actions)                                      │
    │    ════════════════════════════════                                      │
    │                                                                          │
    │    ┌─────────────────┐      ┌─────────────────┐     ┌─────────────────┐ │
    │    │  Claim Submit   │      │  Pipeline Proc  │     │  DocGen Upload  │ │
    │    └────────┬────────┘      └────────┬────────┘     └────────┬────────┘ │
    │             │                        │                       │          │
    │             ▼                        ▼                       ▼          │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │                    WebSocket Manager                            │  │
    │    │                    (Broadcast to all connected clients)         │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                    │                                     │
    │                                    ▼                                     │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │                      EVENT TYPES                                │  │
    │    ├─────────────────────────────────────────────────────────────────┤  │
    │    │                                                                 │  │
    │    │  CLAIM EVENTS:                                                  │  │
    │    │  ├── claim_submitted    → New claim created                     │  │
    │    │  ├── claim_to_bronze    → Moved to Bronze layer                 │  │
    │    │  └── claim_status_update → Status change with message           │  │
    │    │                                                                 │  │
    │    │  CUSTOMER EVENTS:                                               │  │
    │    │  ├── customer_created   → New customer registered               │  │
    │    │  └── pet_added          → New pet added                         │  │
    │    │                                                                 │  │
    │    │  POLICY EVENTS:                                                 │  │
    │    │  ├── policy_created     → New policy created                    │  │
    │    │  └── policy_update      → Policy details updated                │  │
    │    │                                                                 │  │
    │    │  PIPELINE EVENTS:                                               │  │
    │    │  ├── silver_processed   → Claims moved to Silver                │  │
    │    │  └── gold_processed     → Claims moved to Gold                  │  │
    │    │                                                                 │  │
    │    │  DOCGEN EVENTS:                                                 │  │
    │    │  ├── docgen_upload      → Document upload started               │  │
    │    │  ├── docgen_status      → Processing status update              │  │
    │    │  ├── docgen_completed   → Processing complete                   │  │
    │    │  ├── docgen_failed      → Processing failed                     │  │
    │    │  └── docgen_queued      → Job queued                            │  │
    │    │                                                                 │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                                                          │
    └──────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ Broadcast
                                         ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                          CONNECTED CLIENTS                                │
    ├──────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    ┌───────────────────┐    ┌───────────────────┐                       │
    │    │  Customer Portal  │    │   BI Dashboard    │                       │
    │    │  (Port 3000)      │    │   (Port 3001)     │                       │
    │    ├───────────────────┤    ├───────────────────┤                       │
    │    │  Subscribes to:   │    │  Subscribes to:   │                       │
    │    │  • claim_*        │    │  • claim_*        │                       │
    │    │  • docgen_*       │    │  • silver_*       │                       │
    │    │  • policy_*       │    │  • gold_*         │                       │
    │    │                   │    │  • docgen_*       │                       │
    │    │  Updates:         │    │                   │                       │
    │    │  • My Claims list │    │  Updates:         │                       │
    │    │  • Upload status  │    │  • Pipeline view  │                       │
    │    │  • Policy cards   │    │  • Analytics      │                       │
    │    └───────────────────┘    │  • Processing log │                       │
    │                             └───────────────────┘                       │
    │                                                                          │
    └──────────────────────────────────────────────────────────────────────────┘


    ┌──────────────────────────────────────────────────────────────────────────┐
    │                    Agent Pipeline (Port 8006)                             │
    │                    WebSocket Event Stream                                 │
    ├──────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    Endpoint: WS /ws/events?run_id={optional}                             │
    │    Endpoint: WS /ws/run/{run_id}                                         │
    │                                                                          │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │                      EVENT TYPES                                │  │
    │    ├─────────────────────────────────────────────────────────────────┤  │
    │    │  • connected      → Client connected with client_id             │  │
    │    │  • heartbeat      → Keep-alive every 30 seconds                 │  │
    │    │  • event          → Pipeline event with payload:                │  │
    │    │      {                                                          │  │
    │    │        "run_id": "...",                                         │  │
    │    │        "stage": "ROUTER|BRONZE|SILVER|GOLD",                    │  │
    │    │        "status": "started|completed|failed",                    │  │
    │    │        "data": {...}                                            │  │
    │    │      }                                                          │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                                                          │
    │    Subscribers:                                                          │
    │    ┌───────────────────┐                                                │
    │    │   Agent Portal    │  → Real-time React Flow visualization          │
    │    │   (Port 8080)     │  → Agent node status updates                   │
    │    └───────────────────┘  → Decision highlighting                       │
    │                                                                          │
    └──────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Data Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MEDALLION LAKEHOUSE ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────────┐
                    │          DATA SOURCES                    │
                    ├─────────────────────────────────────────┤
                    │  • Customer Portal form submissions      │
                    │  • Document uploads (images, PDFs)       │
                    │  • API integrations                      │
                    │  • Synthetic demo data (CSVs)            │
                    └──────────────────┬──────────────────────┘
                                       │
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           BRONZE LAYER                                   │
    │                         (Raw Data Landing)                               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    Storage: Azure ADLS Gen2 → petinsud7i43/raw/                          │
    │    Format: JSON, CSV, JSONL                                              │
    │                                                                          │
    │    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
    │    │  claims/       │  │  customers/    │  │  documents/    │           │
    │    │  └─ CLM-xxx.json  │  └─ CUST-xxx.json  │  └─ DOC-xxx.json  │           │
    │    └────────────────┘  └────────────────┘  └────────────────┘           │
    │                                                                          │
    │    Transformations: NONE (raw data as-is)                                │
    │    Quality: Unvalidated, may contain nulls/errors                        │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Bronze → Silver Transformation
                                       │ (Manual trigger or Agent Pipeline)
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          SILVER LAYER                                    │
    │                     (Cleaned & Validated Data)                           │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    Storage: Azure ADLS Gen2 → petinsud7i43/processed/                    │
    │    Format: Delta Lake / Parquet                                          │
    │                                                                          │
    │    Transformations Applied:                                              │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │  • Data type standardization (claim_amount → decimal)           │  │
    │    │  • Line items validation (sum check)                            │  │
    │    │  • Completeness scoring (required fields check)                 │  │
    │    │  • Validity scoring (business rules)                            │  │
    │    │  • Deduplication check (claim_id uniqueness)                    │  │
    │    │  • Null handling (default values)                               │  │
    │    │  • Date standardization (ISO 8601)                              │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                                                          │
    │    Quality Metrics Added:                                                │
    │    • completeness_score: 0-100                                           │
    │    • validity_score: 0-100                                               │
    │    • overall_quality_score: weighted average                             │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Silver → Gold Transformation
                                       │ (Manual trigger or Agent Pipeline)
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           GOLD LAYER                                     │
    │                    (Aggregated Business Metrics)                         │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    Storage: Azure ADLS Gen2 → petinsud7i43/gold/                         │
    │    Format: Delta Lake (optimized for analytics)                          │
    │                                                                          │
    │    Transformations Applied:                                              │
    │    ┌─────────────────────────────────────────────────────────────────┐  │
    │    │  • Customer dimension join (customer_id → name, tier, risk)     │  │
    │    │  • Policy dimension join (policy_id → coverage details)         │  │
    │    │  • Provider dimension join (provider_id → network status)       │  │
    │    │  • Reimbursement calculation:                                   │  │
    │    │      after_deductible = max(0, amount - $250)                   │  │
    │    │      reimbursement = after_deductible * 0.80                    │  │
    │    │      if out_of_network: reimbursement *= 0.80                   │  │
    │    │  • Network adjustment (in-network: 100%, out: 80%)              │  │
    │    │  • Priority assignment (emergency → High, else Normal)          │  │
    │    │  • KPI aggregation flags                                        │  │
    │    └─────────────────────────────────────────────────────────────────┘  │
    │                                                                          │
    │    Business-Ready Entities:                                              │
    │    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
    │    │ Claims 360     │  │ Customer 360   │  │ Provider       │           │
    │    │ • Full context │  │ • Value tier   │  │ Performance    │           │
    │    │ • Reimburse $  │  │ • Risk score   │  │ • Network %    │           │
    │    │ • Priority     │  │ • Churn risk   │  │ • Avg claim    │           │
    │    └────────────────┘  └────────────────┘  └────────────────┘           │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Query Layer
                                       ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                       INSIGHTS SERVICE                                   │
    │                    (In-Memory Analytics Cache)                           │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │    DataFrames:                                                           │
    │    ┌────────────────────────────────────────────────────────────────┐   │
    │    │  _customers: pd.DataFrame   # 5,003+ records                   │   │
    │    │  _pets: pd.DataFrame        # 6,504+ records                   │   │
    │    │  _policies: pd.DataFrame    # 6,004+ records                   │   │
    │    │  _claims: pd.DataFrame      # 15,000+ records                  │   │
    │    │  _providers: pd.DataFrame   # 200+ records                     │   │
    │    └────────────────────────────────────────────────────────────────┘   │
    │                                                                          │
    │    API Endpoints:                                                        │
    │    /api/insights/summary     → Aggregate statistics                      │
    │    /api/insights/customers   → Customer 360 views                        │
    │    /api/insights/claims      → Claims analytics                          │
    │    /api/insights/kpis        → Monthly KPIs                              │
    │    /api/insights/risks       → Risk scores                               │
    │    /api/insights/cross-sell  → Recommendations                           │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Service Endpoints Reference

### PetInsure360 Backend (Port 3002)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/customers` | POST | Register customer |
| `/api/customers/lookup` | GET | Login lookup |
| `/api/customers/seed-demo` | POST | Seed demo data |
| `/api/customers/{id}` | GET | Get customer |
| `/api/customers/{id}/pets` | GET | List customer pets |
| `/api/pets` | POST | Add pet |
| `/api/policies` | POST | Create policy |
| `/api/policies/{id}` | PATCH | Update policy |
| `/api/claims` | POST | Submit claim |
| `/api/claims/{id}/status` | GET | Get claim status |
| `/api/pipeline/status` | GET | Pipeline status |
| `/api/pipeline/pending` | GET | Pending claims |
| `/api/pipeline/submit-claim` | POST | Submit to Bronze |
| `/api/pipeline/process/bronze-to-silver` | POST | Process Bronze→Silver |
| `/api/pipeline/process/silver-to-gold` | POST | Process Silver→Gold |
| `/api/insights/summary` | GET | Summary stats |
| `/api/insights/customers` | GET | Customer 360 |
| `/api/insights/claims` | GET | Claims analytics |
| `/api/insights/kpis` | GET | Monthly KPIs |
| `/api/docgen/upload` | POST | Upload documents |
| `/api/docgen/batches` | GET | List all batches |
| `/api/docgen/health` | GET | DocGen connectivity |
| `/ws` | WS | WebSocket connection |

### Agent Pipeline (Port 8006)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/pipeline/trigger` | POST | Async full pipeline |
| `/api/v1/pipeline/trigger/sync` | POST | Sync full pipeline |
| `/api/v1/pipeline/ingest` | POST | Ingest only (manual) |
| `/api/v1/pipeline/run/{id}` | GET | Get pipeline state |
| `/api/v1/pipeline/run/{id}/bronze` | GET | Get Bronze output |
| `/api/v1/pipeline/run/{id}/silver` | GET | Get Silver output |
| `/api/v1/pipeline/run/{id}/gold` | GET | Get Gold output |
| `/api/v1/pipeline/active` | GET | Active runs |
| `/api/v1/pipeline/recent` | GET | Recent runs |
| `/api/v1/pipeline/pending` | GET | Pending runs |
| `/api/v1/scenarios` | GET | Test scenarios |
| `/ws/events` | WS | Event stream |
| `/ws/run/{id}` | WS | Run-specific stream |

### Claims Data API (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/chat/providers` | GET | AI provider status |
| `/api/chat/conversations` | POST | Start conversation |
| `/api/v1/config/ai` | GET/PUT | AI configuration |
| `/api/v1/config/claims` | GET/PUT | Claims config |
| `/api/v1/approvals/stats` | GET | Approval statistics |
| `/api/v1/approvals/pending` | GET | Pending approvals |
| `/api/v1/audit/stats` | GET | Audit statistics |
| `/api/v1/audit/events` | GET | Audit events |
| `/api/v1/costs/summary` | GET | Cost summary |
| `/api/v1/scenarios` | GET | Test scenarios |
| `/api/pipeline/status` | GET | Pipeline status |

---

## Diagram Files

For use with Mermaid or other visualization tools, see the raw diagram code in individual sections above.

**Recommended Tools:**
- [Mermaid Live Editor](https://mermaid.live)
- [Draw.io](https://draw.io)
- [Lucidchart](https://lucidchart.com)

---

**Last Updated:** January 11, 2026
