# Architecture Documentation

## Contents

1. [Overview](./overview.md) - High-level system architecture
2. [Infrastructure](./infrastructure.md) - Cloud resources and Terraform
3. [Data Flow](./data-flow.md) - How data moves through the system
4. [Security](./security.md) - Authentication, authorization, secrets

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND APPLICATIONS                               │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐          │
│  │   WS4: Agent Portal (:8080) │    │  WS8: Admin Portal (:8081)  │          │
│  │   Next.js 14 / React 18     │    │  Next.js 14 / React 18      │          │
│  │  ┌─────────┬─────────┐      │    │  ┌─────────┬─────────┐      │          │
│  │  │Dashboard│Pet Owner│      │    │  │AI Config│Cost Mon │      │          │
│  │  │  Page   │   360   │      │    │  │  Mgmt   │ itor    │      │          │
│  │  ├─────────┼─────────┤      │    │  ├─────────┼─────────┤      │          │
│  │  │Claims   │ Quote   │      │    │  │Audit    │ Users   │      │          │
│  │  │Manager  │ Wizard  │      │    │  │Logs     │ & RBAC  │      │          │
│  │  └─────────┴─────────┘      │    │  └─────────┴─────────┘      │          │
│  └─────────────────────────────┘    └─────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────────────┘
                     │                              │
                     ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     UNIFIED DATA GATEWAY (Port 8000)                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │               Claims Data API (FastAPI) - 60+ Endpoints                 │  │
│  │  • Customers  • Pets  • Policies  • Providers  • Claims  • Fraud       │  │
│  │  • Medical    • Billing  • Validation  • Data Lake Operations          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
           │              │              │              │              │
           ▼              ▼              ▼              ▼              ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ WS2: AI Claims │ │ WS3: Integrat. │ │ WS5: Rating    │ │ WS8: Admin API │
│ Port: 8001     │ │ Port: 8002     │ │ Port: 8003     │ │ Port: 8008     │
│ ──────────────││ │ ──────────────││ │ ──────────────││ │ ──────────────││
│ • FNOL Intake  │ │ • Mock EIS API │ │ • Rate Calc    │ │ • Config Mgmt  │
│ • Fraud Detect │ │ • D365 Sync    │ │ • Breed Factor │ │ • Cost Monitor │
│ • Claim Triage │ │ • Webhooks     │ │ • Age Curve    │ │ • Audit Logs   │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
           │              │                    │
           └──────────────┼────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      AI PROCESSING SERVICES                                   │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  WS6: Agent Pipeline (Port 8006) │  │  WS7: DocGen Service (Port 8007) │  │
│  │  LangGraph + Medallion Arch      │  │  AI Document Processing          │  │
│  │  ┌────────┬────────┬────────┐    │  │  ┌────────┬────────┬────────┐    │  │
│  │  │ Router │ Bronze │ Silver │    │  │  │Extract │ Mapper │Validate│    │  │
│  │  │ Agent  │ Agent  │ Agent  │    │  │  │ Agent  │ Agent  │ Agent  │    │  │
│  │  └────────┴────────┴────────┘    │  │  └────────┴────────┴────────┘    │  │
│  │         │                        │  │         │                        │  │
│  │         ▼                        │  │         ▼                        │  │
│  │  ┌────────────────────────┐      │  │  ┌────────────────────────┐      │  │
│  │  │ Gold Agent (Decisions) │      │  │  │ Export: PDF/Word/CSV   │      │  │
│  │  └────────────────────────┘      │  │  └────────────────────────┘      │  │
│  │  WebSocket: /ws/events           │  │                                  │  │
│  └──────────────────────────────────┘  └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Technology | Purpose |
|---------|------|------------|---------|
| **Claims Data API** | **8000** | FastAPI | Unified data gateway (60+ endpoints) |
| AI Claims (WS2) | 8001 | FastAPI | FNOL intake, fraud detection, triage |
| Integration (WS3) | 8002 | FastAPI | Mock EIS APIs, D365 sync |
| Rating Engine (WS5) | 8003 | FastAPI | Premium calculation, breed factors |
| **Agent Pipeline (WS6)** | **8006** | FastAPI + LangGraph | AI agent processing (medallion) |
| **DocGen (WS7)** | **8007** | FastAPI | Document processing & export |
| Admin Backend (WS8) | 8008 | FastAPI | Configuration, cost monitoring |
| **Agent Portal (WS4)** | **8080** | Next.js 14 | Claims processing UI |
| **Admin Portal (WS8)** | **8081** | Next.js 14 | Admin configuration UI |

## Agent Pipeline Architecture (WS6)

The Agent Pipeline uses LangGraph for true agent-driven claims processing with a medallion architecture:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH AGENT PIPELINE                              │
│                                                                               │
│   Claim Input                                                                 │
│       │                                                                       │
│       ▼                                                                       │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐ │
│  │   ROUTER    │────▶│   BRONZE    │────▶│   SILVER    │────▶│    GOLD     │ │
│  │   AGENT     │     │   AGENT     │     │   AGENT     │     │   AGENT     │ │
│  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘ │
│       │                   │                   │                   │          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐ │
│  │ • Analyze   │     │ • Validate  │     │ • Policy    │     │ • Risk      │ │
│  │   Complexity│     │ • Cleanse   │     │   Lookup    │     │   Scoring   │ │
│  │ • Route:    │     │ • Quality   │     │ • Customer  │     │ • Decision  │ │
│  │   fast_track│     │   Check     │     │   Enrich    │     │   Making    │ │
│  │   standard  │     │ • Schema    │     │ • Provider  │     │ • Insights  │ │
│  │   enhanced  │     │   Adapt     │     │   Verify    │     │ • Reasoning │ │
│  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘ │
│                                                                               │
│   WebSocket Events (/ws/events) ──────────────────────────────────▶ Real-time│
└──────────────────────────────────────────────────────────────────────────────┘
```

### Agent Configuration

| Agent | Role | AI Model | Timeout |
|-------|------|----------|---------|
| Router | Classify complexity, route claims | Claude claude-sonnet-4-20250514 | 30s |
| Bronze | Data validation & cleansing | Claude claude-sonnet-4-20250514 | 60s |
| Silver | Data enrichment & context | Claude claude-sonnet-4-20250514 | 60s |
| Gold | Risk assessment & decisions | Claude claude-sonnet-4-20250514 | 60s |

### Routing Paths

| Path | Criteria | Processing |
|------|----------|------------|
| `fast_track` | Low amount, simple claim | Bronze only |
| `standard` | Normal complexity | Bronze → Silver → Gold |
| `enhanced` | High value, complex | Full pipeline + extra validation |

## Code vs Agent Comparison

The system supports 1-to-1 comparison between two processing approaches:

### Code-Driven Processing
- **Speed**: < 1ms
- **Approach**: Deterministic rules
- **Pros**: Fast, predictable, no API costs
- **Cons**: No reasoning, rigid rules

### Agent-Driven Processing
- **Speed**: 30-120 seconds
- **Approach**: LLM-powered reasoning
- **Pros**: Adaptive, explains decisions, handles edge cases
- **Cons**: Slower, API costs, non-deterministic

### Comparison Flow

```
                    +----------------+
                    |  Claim Data    |
                    +-------+--------+
                            |
            +---------------+---------------+
            |                               |
            v                               v
    +---------------+               +---------------+
    | Code-Driven   |               | Agent-Driven  |
    | Processor     |               | Pipeline      |
    | (< 1ms)       |               | (30-120s)     |
    +-------+-------+               +-------+-------+
            |                               |
            +---------------+---------------+
                            |
                            v
                    +---------------+
                    | Comparison    |
                    | Metrics       |
                    +---------------+
```

## Data Model

### Claim Scenario

```json
{
  "id": "SCN-001",
  "name": "Chocolate Toxicity Emergency",
  "claim_type": "Accident",
  "claim_category": "Toxicity/Poisoning",
  "claim_amount": 1355.00,
  "diagnosis_code": "T65.8",
  "is_in_network": false,
  "is_emergency": true,
  "line_items": [...]
}
```

### Comparison Result

```json
{
  "comparison_id": "CMP-ABC123",
  "code_driven": {
    "processing_time_ms": 0.04,
    "final_decision": "STANDARD_REVIEW",
    "risk_level": "MEDIUM"
  },
  "agent_driven": {
    "processing_time_ms": 45000,
    "final_decision": "STANDARD_REVIEW",
    "risk_level": "MEDIUM",
    "reasoning": ["...", "..."],
    "insights": ["...", "..."]
  },
  "comparison_metrics": {
    "decision_match": true,
    "risk_match": true
  }
}
```

## DocGen Service Architecture (WS7)

AI-powered document processing with multi-agent pipeline:

```
┌──────────────────────────────────────────────────────────────────┐
│                    DOCGEN AGENT PIPELINE                          │
│                                                                   │
│  Upload (PDF/Image/ZIP)                                          │
│       │                                                           │
│       ▼                                                           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ EXTRACT  │───▶│  MAPPER  │───▶│ VALIDATE │───▶│  DOCGEN  │   │
│  │  AGENT   │    │  AGENT   │    │  AGENT   │    │  AGENT   │   │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │
│       │              │              │              │             │
│   OCR/Text      Schema Map     Completeness    Generate         │
│   Extract       to Claims      Check           Output           │
│                                                                   │
│  Export Formats: PDF | Word | CSV                                │
└──────────────────────────────────────────────────────────────────┘
```

### DocGen Constraints

| Parameter | Limit |
|-----------|-------|
| Max ZIP size | 50 MB |
| Max files per ZIP | 20 |
| Max file size | 10 MB |
| Supported formats | PDF, JPG, PNG, HEIC, DOC, DOCX, TXT, ZIP |

## Architecture Principles

1. **Cloud-Native** - Multi-cloud (Azure primary, AWS for agent pipeline)
2. **Event-Driven** - Loosely coupled services via Redis/WebSocket
3. **AI-Augmented** - LangGraph agents with Claude/OpenAI
4. **API-First** - All functionality exposed via RESTful APIs
5. **Real-Time** - WebSocket streaming for live pipeline updates
6. **Comparable** - Side-by-side rule-based vs agent-driven analysis
7. **Medallion Architecture** - Bronze/Silver/Gold data processing layers

## Live Deployments

| Environment | URL |
|-------------|-----|
| Claims Data API | https://p7qrmgi9sp.us-east-1.awsapprunner.com |
| Agent Pipeline | https://bn9ymuxtwp.us-east-1.awsapprunner.com |
| API Documentation | https://p7qrmgi9sp.us-east-1.awsapprunner.com/docs |

## Related Documentation

- [PIPELINE_VISUAL_FLOW.md](../PIPELINE_VISUAL_FLOW.md) - Pipeline UI documentation
- [howto.md](../../howto.md) - Quick start guide
- [api/README.md](../api/README.md) - API reference
- [RULE_VS_AI_COMPARISON.md](../RULE_VS_AI_COMPARISON.md) - Processing comparison
- [SHOWCASE_GUIDE.md](../SHOWCASE_GUIDE.md) - Demo walkthrough
