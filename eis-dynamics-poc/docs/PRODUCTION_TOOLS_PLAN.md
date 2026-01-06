# Production Tools & Unified Data Architecture Plan

## Executive Summary

This document outlines the plan to create a production-grade claims processing system with:
- **Two Separate Applications** for client demo (different UIs, same data)
  - **PetInsure360** → Rule-based claims processing
  - **EIS Dynamics POC** → AI Agent-driven claims processing
- **Unified Data Layer** shared between both applications
- **100 customers** with 1 year of realistic history (150 pets, 500+ claims)
- **3 fraud patterns** designed for AI detection (not rule-based)
- **Single API Gateway** (port 8000) with function-based microservices
- **Datalake/Dataverse** integration for enterprise data management

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND APPLICATIONS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────┐       ┌─────────────────────────┐             │
│   │     PetInsure360        │       │    EIS Dynamics POC     │             │
│   │   (Rule-Based Engine)   │       │   (AI Agent Pipeline)   │             │
│   │    localhost:3001       │       │    localhost:3000       │             │
│   │                         │       │                         │             │
│   │  • Threshold checks     │       │  • LLM-powered agents   │             │
│   │  • Fixed rules          │       │  • Contextual reasoning │             │
│   │  • Fast, deterministic  │       │  • Pattern recognition  │             │
│   └───────────┬─────────────┘       └───────────┬─────────────┘             │
│               │                                 │                            │
│               │         ┌───────────┐           │                            │
│               └─────────┤ COMPARISON├───────────┘                            │
│                         │   VIEW    │                                        │
│                         │ Side-by-  │                                        │
│                         │   side    │                                        │
│                         └───────────┘                                        │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED CLAIMS DATA API (Port 8000)                       │
│                         (Single Gateway + Functions)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      FastAPI Application                             │   │
│   │                                                                      │   │
│   │  /api/v1/                                                            │   │
│   │  ├── policies/      → PolicyService (functions)                     │   │
│   │  ├── customers/     → CustomerService (functions)                   │   │
│   │  ├── pets/          → PetService (functions)                        │   │
│   │  ├── providers/     → ProviderService (functions)                   │   │
│   │  ├── fraud/         → FraudService (functions)                      │   │
│   │  ├── medical/       → MedicalRefService (functions)                 │   │
│   │  ├── billing/       → BillingService (functions)                    │   │
│   │  ├── documents/     → DocumentService (functions)                   │   │
│   │  └── external/      → ExternalDataService (functions)               │   │
│   │                                                                      │   │
│   │  Note: Each "service" is a Python module with functions             │   │
│   │        Called via API endpoints (looks like microservices)          │   │
│   │        Single process, no inter-service network calls               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SHARED DATA STORE                                    │
│               (JSON Files → Production: Azure Datalake/Dataverse)            │
│                                                                              │
│   /src/shared/claims_data/data/                                             │
│   ├── customers.json       (100 customers)                                  │
│   ├── pets.json            (150 pets)                                       │
│   ├── policies.json        (120 policies)                                   │
│   ├── claims_history.json  (500+ claims, 1 year)                            │
│   ├── providers.json       (50 providers)                                   │
│   ├── medical_codes.json   (ICD-10-VET reference)                           │
│   ├── fraud_patterns.json  (ML model features)                              │
│   └── payments.json        (Payment history)                                │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    PRODUCTION DATA FLOW                              │   │
│   │                                                                      │   │
│   │   [Incoming Claims] → Azure Event Hub → Databricks (Bronze/Silver)  │   │
│   │                              ↓                                       │   │
│   │   Azure Datalake Gen2 (Parquet) ←→ Synapse Analytics                │   │
│   │                              ↓                                       │   │
│   │   Dataverse (CDS) ←→ Dynamics 365 ←→ Power Platform                 │   │
│   │                              ↓                                       │   │
│   │   Power BI Dashboards / Agent Portal                                │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Datalake / Dataverse Integration

### Where Data Lives in Production

| Layer | Technology | Data | Purpose |
|-------|------------|------|---------|
| **Raw (Bronze)** | Azure Datalake Gen2 | claims_raw.parquet | Incoming claims, unprocessed |
| **Curated (Silver)** | Azure Datalake Gen2 | claims_validated.parquet | Cleansed, validated claims |
| **Aggregated (Gold)** | Azure Synapse | claims_analytics | Aggregated for reporting |
| **Operational** | Dataverse (CDS) | msdyn_claim, msdyn_policy | Live operational data |
| **Reference** | Dataverse | msdyn_medicalcode, msdyn_provider | Master data |

### Data Flow

```
                    DEMO (Local JSON)              PRODUCTION (Azure)
                    ────────────────               ────────────────────

Claim Submitted     claims_data/data/              Azure Event Hub
        │           claims_history.json            (real-time ingestion)
        ▼                                                  │
                                                           ▼
Bronze Layer        JSON file read                 Datalake Gen2/bronze/
(Raw)               directly                       claims_raw.parquet
        │                                                  │
        ▼                                                  ▼
Silver Layer        In-memory                      Databricks ETL
(Validated)         validation                     → Datalake Gen2/silver/
        │                                                  │
        ▼                                                  ▼
Gold Layer          Python                         Synapse Analytics
(Enriched)          processing                     (aggregations, ML features)
        │                                                  │
        ▼                                                  ▼
Operational         Return to UI                   Dataverse (via API)
                                                   → Dynamics 365 CRM
```

### Dataverse Entities Used

| Entity | Table Name | Description |
|--------|------------|-------------|
| **Claim** | `msdyn_claim` | Active claims being processed |
| **Policy** | `msdyn_policy` | Insurance policies |
| **Customer** | `contact` | Pet owners (standard Dynamics) |
| **Pet** | `msdyn_pet` | Custom entity for pets |
| **Provider** | `account` | Vet providers (standard Dynamics) |
| **Claim Line Item** | `msdyn_claimlineitem` | Individual claim items |
| **Fraud Alert** | `msdyn_fraudalert` | AI-generated fraud flags |

---

## Part 1: Synthetic Data Design

### 1.1 Data Volume Requirements

| Entity | Count | Notes |
|--------|-------|-------|
| **Customers** | 100 | Mix of individual, family, business |
| **Pets** | 150 | Some customers have multiple pets |
| **Policies** | 120 | Active, cancelled, expired mix |
| **Claims (History)** | 500+ | 1 year history, avg 4-5 per customer |
| **Providers** | 50 | Mix of in-network, out-of-network |
| **Payments** | 600+ | Monthly premiums + claim payouts |

### 1.2 Customer Segments (100 Customers)

| Segment | Count | Characteristics |
|---------|-------|-----------------|
| **New Customers** | 20 | < 3 months tenure, 0-1 claims |
| **Standard Customers** | 50 | 3-18 months, 2-4 claims |
| **Loyal Customers** | 20 | 18+ months, 5-10 claims, high LTV |
| **High-Risk Customers** | 7 | Multiple claims, complex conditions |
| **Fraud Suspects** | 3 | Hidden fraud patterns (see below) |

### 1.3 Pet Distribution (150 Pets)

| Species | Count | Breed Distribution |
|---------|-------|-------------------|
| **Dogs** | 100 | 40% mixed, 30% popular breeds (Lab, Golden, French Bulldog), 30% other |
| **Cats** | 45 | 50% domestic shorthair, 30% popular breeds, 20% other |
| **Exotic** | 5 | Birds, rabbits (for edge cases) |

**Age Distribution:**
- Puppies/Kittens (< 1 year): 15%
- Young (1-3 years): 30%
- Adult (4-7 years): 35%
- Senior (8+ years): 20%

### 1.4 Policy Types

| Plan Type | Count | Coverage |
|-----------|-------|----------|
| **Accident Only** | 25 | Accidents, emergencies |
| **Accident + Illness** | 55 | Accidents, illness, hereditary |
| **Comprehensive** | 30 | Everything + wellness |
| **Wellness Add-on** | 20 | Added to base plans |

---

## Part 2: Fraud Patterns (AI vs Rules)

### Why AI Beats Rules

| Aspect | Rule-Based | AI-Based |
|--------|------------|----------|
| **Detection** | Fixed thresholds | Multi-variable correlation |
| **Context** | Single-variable checks | Contextual reasoning |
| **Adaptability** | Easy to game | Narrative inconsistency detection |
| **Weak Signals** | Misses subtle patterns | Pattern recognition across signals |

### 2.1 Fraud Pattern #1: "Chronic Condition Gaming"

**Customer:** CUST-023 (Jennifer Martinez)
**Pet:** PET-034 (Rocky, German Shepherd, 6 years old)

**Pattern:**
- Pet has documented hip dysplasia (pre-existing)
- Customer files multiple "accident" claims for hip injuries
- Each claim is a "fall" or "jump incident"
- All claims are under $2,000 (below high-value threshold)
- Different providers each time (avoids provider pattern detection)

**Claims History (1 year):**
| Date | Claim | Description | Amount | Provider |
|------|-------|-------------|--------|----------|
| 2024-02 | CLM-023-001 | Hip injury from fall | $1,450 | Provider A |
| 2024-05 | CLM-023-002 | Leg sprain from jumping | $1,200 | Provider B |
| 2024-08 | CLM-023-003 | Hip injury from stairs | $1,800 | Provider C |
| 2024-11 | CLM-023-004 | Back leg injury | $1,650 | Provider D |

**Why Rules Miss It:**
- Each claim is under threshold
- Different providers (no pattern)
- Valid diagnosis codes each time
- No single red flag

**Why AI Catches It:**
```
AI Reasoning:
"Customer CUST-023 has filed 4 claims in 12 months, all involving hip/leg
injuries to Rocky (German Shepherd, 6yr). The pet has documented hip
dysplasia from pre-policy exam. Each claim is filed as 'accident' to
circumvent pre-existing condition exclusion. The consistent anatomical
focus (hip area), despite varying incident descriptions, suggests these
may be manifestations of the pre-existing condition rather than true
accidents. Recommend medical records review to determine if injuries
are genuinely accidental or related to documented hip dysplasia."
```

---

### 2.2 Fraud Pattern #2: "Provider Collusion"

**Customer:** CUST-067 (David Thompson)
**Pet:** PET-089 (Luna, Labrador, 4 years old)

**Pattern:**
- Always uses same out-of-network provider "Valley Pet Care"
- Claims are always $200-300 below annual limit
- Treatment descriptions are vague but expensive
- Provider has slightly elevated fraud rate (2.8% vs 1.5% average)
- Claim amounts are round numbers

**Claims History:**
| Date | Claim | Description | Amount | Annual Limit |
|------|-------|-------------|--------|--------------|
| 2024-03 | CLM-067-001 | Comprehensive treatment | $4,750 | $5,000 used |
| 2024-04 | CLM-067-002 | Follow-up care | $4,700 | $9,700 used |
| Policy renewed |
| 2024-05 | CLM-067-003 | Specialist consultation | $4,800 | $4,800 used |
| 2024-09 | CLM-067-004 | Advanced diagnostics | $4,900 | $9,700 used |

**Why Rules Miss It:**
- Each claim is below limits
- Provider fraud rate (2.8%) is below alert threshold (5%)
- Out-of-network is allowed
- No duplicate claims

**Why AI Catches It:**
```
AI Reasoning:
"Customer CUST-067 demonstrates unusual provider loyalty to Valley Pet
Care, an out-of-network facility, for all 4 claims despite closer
in-network options. Claims consistently approach but don't exceed
annual limits ($4,700-$4,900 vs $5,000 limit). Valley Pet Care shows
concerning patterns: 15% of their claims come from this single customer,
average claim is 3.5x industry standard, and treatment descriptions
lack specificity. The combination of: (1) exclusive out-of-network
usage, (2) limit-optimization behavior, (3) round claim amounts, and
(4) provider concentration suggests potential collusion. Recommend
provider audit and itemized invoice review."
```

---

### 2.3 Fraud Pattern #3: "Staged Timing"

**Customer:** CUST-089 (Michelle Chen)
**Pet:** PET-112 (Mochi, French Bulldog, 3 years old)

**Pattern:**
- New customer, policy just past 14-day waiting period
- Immediately files expensive claim for IVDD (spinal condition)
- French Bulldogs have 10x higher IVDD risk (AI knows this)
- Claim documentation is suspiciously complete
- Pre-policy vet records are "unavailable"

**Timeline:**
| Date | Event |
|------|-------|
| 2024-10-01 | Policy purchased |
| 2024-10-15 | Waiting period ends (14 days) |
| 2024-10-17 | Emergency claim filed for IVDD ($6,500) |

**Why Rules Miss It:**
- Waiting period was satisfied (16 days)
- Documentation is complete
- Amount is high but not extreme
- No prior claims to compare

**Why AI Catches It:**
```
AI Reasoning:
"Customer CUST-089 filed a $6,500 IVDD claim just 2 days after the
14-day waiting period ended. Key concerns:

1. TIMING: Statistically improbable - IVDD onset exactly at day 16
   of coverage suggests pre-existing awareness

2. BREED RISK: French Bulldogs have 10.4x higher IVDD incidence.
   Combined with timing, suggests informed purchase

3. DOCUMENTATION: Claim has unusually complete documentation for
   an 'emergency' - typically emergency claims have gaps

4. MISSING RECORDS: Pre-policy veterinary records are 'unavailable' -
   a common indicator of concealed pre-existing conditions

5. STATISTICAL ANOMALY: Probability of genuine IVDD onset on days
   15-17 of coverage is <0.3% based on disease progression models

Recommend: Request pre-policy records through alternate channels,
veterinary interview, and policy rescission review."
```

---

## Part 3: Services Design (Single Port 8000)

### 3.1 Architecture: Functions Not Microservices

Instead of separate ports (8010-8018), all services are Python modules called via API endpoints:

```python
# src/shared/claims_data_api/app/main.py
from fastapi import FastAPI
from app.services import (
    policy_service,
    customer_service,
    pet_service,
    provider_service,
    fraud_service,
    medical_service,
    billing_service,
    document_service,
    external_service
)

app = FastAPI(title="Unified Claims Data API", version="1.0.0")

# Each service is a router with functions
app.include_router(policy_service.router, prefix="/api/v1/policies")
app.include_router(customer_service.router, prefix="/api/v1/customers")
# ... etc
```

### 3.2 Service Functions Overview

| Service | Functions | Purpose |
|---------|-----------|---------|
| **PolicyService** | 6 | Policy management, coverage checks |
| **CustomerService** | 6 | Customer 360, claim history |
| **PetService** | 5 | Pet registry, medical history |
| **ProviderService** | 5 | Provider network, fraud rates |
| **FraudService** | 6 | Fraud detection, pattern matching |
| **MedicalRefService** | 5 | Medical codes, benchmarks |
| **BillingService** | 5 | Billing, reimbursement calc |
| **DocumentService** | 4 | Document management |
| **ExternalDataService** | 4 | External data, market rates |

**Total: 46 functions exposed as API endpoints**

### 3.3 PolicyService Functions

| Function | Endpoint | Description |
|----------|----------|-------------|
| `get_policy` | `GET /policies/{policy_id}` | Get full policy details |
| `check_coverage` | `GET /policies/{policy_id}/coverage/{code}` | Check if diagnosis covered |
| `get_exclusions` | `GET /policies/{policy_id}/exclusions` | List policy exclusions |
| `check_limits` | `GET /policies/{policy_id}/limits` | Get remaining limits |
| `get_waiting_periods` | `GET /policies/{policy_id}/waiting-periods` | Get waiting period status |
| `get_policy_history` | `GET /policies/{policy_id}/history` | Get policy changes |

### 3.4 CustomerService Functions

| Function | Endpoint | Description |
|----------|----------|-------------|
| `get_customer` | `GET /customers/{customer_id}` | Get customer profile |
| `get_claim_history` | `GET /customers/{customer_id}/claims` | Get all claims |
| `get_lifetime_value` | `GET /customers/{customer_id}/ltv` | Calculate LTV |
| `get_risk_tier` | `GET /customers/{customer_id}/risk` | Get risk classification |
| `get_communication_history` | `GET /customers/{customer_id}/communications` | Past interactions |
| `get_household` | `GET /customers/{customer_id}/household` | All pets/policies |

### 3.5 FraudService Functions (Critical for Demo)

| Function | Endpoint | Description |
|----------|----------|-------------|
| `check_fraud_indicators` | `POST /fraud/check` | Full fraud analysis |
| `velocity_check` | `GET /fraud/velocity/{customer_id}` | Claims frequency |
| `duplicate_check` | `POST /fraud/duplicate-check` | Find duplicates |
| `pattern_match` | `POST /fraud/pattern-match` | Known fraud patterns |
| `provider_customer_analysis` | `GET /fraud/provider-customer/{p}/{c}` | Relationship analysis |
| `calculate_fraud_score` | `POST /fraud/score` | ML-based fraud score |

---

## Part 4: Comparison Workflow

### How Both Apps Process Same Claims

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAIM SUBMITTED                                    │
│                    (Same claim data, same scenario)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        │                        ▼
┌─────────────────────┐            │            ┌─────────────────────┐
│    PetInsure360     │            │            │   EIS Dynamics POC  │
│   Rule-Based Flow   │            │            │   Agent-Based Flow  │
├─────────────────────┤            │            ├─────────────────────┤
│                     │            │            │                     │
│ 1. Load claim       │            │            │ 1. Router Agent     │
│ 2. Check thresholds │            │            │    (classify claim) │
│ 3. Validate coverage│            │            │                     │
│ 4. Apply rules:     │            │            │ 2. Bronze Agent     │
│    - amount < $500  │            │            │    (extract, enrich)│
│    - in-network     │            │            │    - Call 46 tools  │
│    - no fraud flags │            │            │    - Get full ctx   │
│ 5. Decision         │            │            │                     │
│                     │            │            │ 3. Silver Agent     │
│ Result:             │            │            │    (validate, score)│
│ - APPROVED/REJECTED │            │            │                     │
│ - Processing: <1ms  │            │            │ 4. Gold Agent       │
│ - No reasoning      │            │            │    (decide, reason) │
│                     │            │            │                     │
└─────────┬───────────┘            │            │ Result:             │
          │                        │            │ - Decision + reason │
          │                        │            │ - Processing: 30-60s│
          │                        │            │ - Full audit trail  │
          │                        │            └─────────┬───────────┘
          │                        │                      │
          │                        ▼                      │
          │            ┌─────────────────────┐            │
          └───────────►│   COMPARISON VIEW   │◄───────────┘
                       │                     │
                       │ Side-by-side:       │
                       │ • Same input claim  │
                       │ • Different outputs │
                       │ • Fraud detection   │
                       │ • Processing time   │
                       │ • Cost analysis     │
                       └─────────────────────┘
```

### Demo Comparison Scenarios

| Scenario | Rule-Based (PetInsure360) | AI Agent (EIS Dynamics) | Winner |
|----------|---------------------------|-------------------------|--------|
| Normal UTI ($450) | ✅ APPROVE (0.5ms) | ✅ APPROVE (45s) | Rules (speed) |
| Fraud #1: Chronic Gaming | ✅ APPROVE (misses it) | ⚠️ MANUAL_REVIEW (catches) | **AI** |
| Fraud #2: Provider Collusion | ✅ APPROVE (misses it) | ⚠️ MANUAL_REVIEW (catches) | **AI** |
| Fraud #3: Staged Timing | ✅ APPROVE (misses it) | ⚠️ MANUAL_REVIEW (catches) | **AI** |
| Complex surgery ($8,000) | ✅ APPROVE (no context) | ✅ APPROVE (with full reasoning) | AI (transparency) |

---

## Part 5: Implementation Phases

### Phase 1: Data Foundation (Day 1-2)
- [ ] Create data schemas for all entities
- [ ] Build synthetic data generator (scaled down from PetInsure360's 5000 to 100)
- [ ] Generate 100 customers with full history
- [ ] Include 3 fraud patterns with detailed history
- [ ] Create shared data store at `/src/shared/claims_data/data/`

### Phase 2: Core Services (Day 3-5)
- [ ] Create unified API at port 8000
- [ ] Implement PolicyService (6 functions)
- [ ] Implement CustomerService (6 functions)
- [ ] Implement FraudService (6 functions)
- [ ] Add CORS for both frontend apps

### Phase 3: Supporting Services (Day 6-7)
- [ ] Implement PetService (5 functions)
- [ ] Implement ProviderService (5 functions)
- [ ] Implement MedicalRefService (5 functions)
- [ ] Implement BillingService (5 functions)
- [ ] Implement DocumentService (4 functions)
- [ ] Implement ExternalDataService (4 functions)

### Phase 4: LLM Tools (Day 8-9)
- [ ] Create 46 tool wrappers for LLM agents
- [ ] Update Bronze/Silver/Gold agents to use new tools
- [ ] Test fraud detection scenarios
- [ ] Validate AI reasoning quality

### Phase 5: Integration (Day 10)
- [ ] Connect EIS Dynamics POC agents to unified API
- [ ] Add rule-based processing to PetInsure360 (if not exists)
- [ ] Create comparison endpoint
- [ ] End-to-end testing with 3 fraud scenarios
- [ ] Documentation

---

## Part 6: File Structure

```
/src/
├── shared/
│   └── claims_data_api/                # Unified API (Port 8000)
│       ├── app/
│       │   ├── main.py                 # FastAPI app
│       │   ├── services/
│       │   │   ├── policy_service.py   # 6 functions
│       │   │   ├── customer_service.py # 6 functions
│       │   │   ├── pet_service.py      # 5 functions
│       │   │   ├── provider_service.py # 5 functions
│       │   │   ├── fraud_service.py    # 6 functions
│       │   │   ├── medical_service.py  # 5 functions
│       │   │   ├── billing_service.py  # 5 functions
│       │   │   ├── document_service.py # 4 functions
│       │   │   └── external_service.py # 4 functions
│       │   └── models/
│       │       └── schemas.py          # Pydantic models
│       ├── data/                        # Shared data store
│       │   ├── customers.json          # 100 customers
│       │   ├── pets.json               # 150 pets
│       │   ├── policies.json           # 120 policies
│       │   ├── claims_history.json     # 500+ claims
│       │   ├── providers.json          # 50 providers
│       │   ├── medical_codes.json      # ICD-10-VET
│       │   ├── fraud_patterns.json     # ML features
│       │   └── payments.json           # Payment history
│       ├── generators/
│       │   ├── generate_all.py         # Main generator
│       │   └── fraud_scenarios.py      # 3 fraud cases
│       └── requirements.txt
│
├── ws6_agent_pipeline/                  # EIS Dynamics Backend
│   └── app/
│       └── tools/
│           ├── unified_api_tools.py    # 46 tools calling port 8000
│           └── tool_registry.py        # Tool registration
│
└── (petinsure360 is separate repo)
    └── backend/                         # PetInsure360 Backend
        └── app/
            └── services/
                └── rule_engine.py       # Rule-based processing
```

---

## Part 7: Demo Script

### Setup
1. Start Unified Claims API (port 8000)
2. Start EIS Dynamics POC (port 3000)
3. Start PetInsure360 (port 3001)

### Demo Flow

**Scenario 1: Normal Claim (Baseline)**
1. Open both apps side-by-side
2. Select same customer "Sarah Johnson" with cat "Whiskers"
3. Submit UTI claim ($450)
4. PetInsure360: APPROVED (0.5ms, no reasoning)
5. EIS Dynamics: APPROVED (45s, full reasoning)
6. **Point**: Both work for simple cases, AI adds transparency

**Scenario 2: Fraud Detection #1 (Chronic Condition Gaming)**
1. Select "Jennifer Martinez" with dog "Rocky"
2. Submit new hip injury claim ($1,600)
3. PetInsure360: **APPROVED** (passes all rules)
4. EIS Dynamics: **MANUAL_REVIEW** (detects pre-existing pattern)
5. **Point**: AI catches fraud that rules miss

**Scenario 3: Fraud Detection #2 (Provider Collusion)**
1. Select "David Thompson" with dog "Luna"
2. Submit claim for $4,850 from "Valley Pet Care"
3. PetInsure360: **APPROVED** (below limits, valid provider)
4. EIS Dynamics: **MANUAL_REVIEW** (detects collusion pattern)
5. **Point**: AI correlates multiple weak signals

**Scenario 4: Fraud Detection #3 (Staged Timing)**
1. Select "Michelle Chen" with dog "Mochi"
2. Submit IVDD claim ($6,500) on day 17
3. PetInsure360: **APPROVED** (waiting period satisfied)
4. EIS Dynamics: **MANUAL_REVIEW** (statistical anomaly + breed risk)
5. **Point**: AI uses contextual knowledge

### Key Messages for Client

| Message | Supporting Evidence |
|---------|---------------------|
| "AI catches fraud that rules miss" | 3 fraud scenarios detected only by AI |
| "Same data, different intelligence" | Both apps use identical data |
| "Transparent decision-making" | AI shows full reasoning trail |
| "Production-ready architecture" | Datalake/Dataverse integration ready |
| "Speed where needed, depth where needed" | Rules for simple, AI for complex |

---

## Approval Checklist

- [ ] Architecture approved (single port 8000)
- [ ] Data volume approved (100 customers)
- [ ] Fraud scenarios approved (3 patterns)
- [ ] Two-app approach approved (PetInsure360 + EIS Dynamics)
- [ ] Datalake/Dataverse integration documented


Top 3 Additional Real-World Scenarios for Pet Insurance -- not implemented yet..

  Here are the most impactful scenarios where AI beats rules:

  | Scenario                                 | What Happens                                                                                  | Why Rules Fail                                  | How AI Catches It                                                                                          |
  |------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------|------------------------------------------------------------------------------------------------------------|
  | 1. Claim Stacking/Unbundling             | One treatment split into multiple claims to stay under per-incident limits                    | Each claim individually passes threshold checks | Recognizes related treatments within short timeframes, same body part, semantic similarity in descriptions |
  | 2. Medical Necessity/Overtreatment       | Excessive diagnostics or treatments for minor conditions (e.g., MRI for simple ear infection) | Rules can't assess clinical appropriateness     | Compares treatment complexity vs diagnosis severity, breed norms, age-appropriate care                     |
  | 3. Wellness-to-Illness Misclassification | Routine wellness (teeth cleaning, vaccines) submitted as "illness" to get coverage            | Rules trust submitted category                  | Analyzes procedure codes, timing patterns, diagnosis descriptions to determine true category               |

  Business Impact

  | Scenario          | Industry Loss Rate | Typical Claim Amount |
  |-------------------|--------------------|----------------------|
  | Claim Stacking    | 3-5% of claims     | $2,000-8,000         |
  | Overtreatment     | 8-12% of claims    | $500-3,000           |
  | Misclassification | 5-7% of claims     | $200-800             |


Other non-fraud, mis classifications:

1. Chronic Condition Gaming - Pre-existing conditions claimed as accidents
  2. Provider Collusion - Coordinated billing patterns
  3. Staged Timing - Claims suspiciously close to waiting period end

  Top 3 Additional Real-World Scenarios for Pet Insurance

  Here are the most impactful scenarios where AI beats rules:

  | Scenario                                 | What Happens                                                                                  | Why Rules Fail                                  | How AI Catches It                                                                                          |
  |------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------|------------------------------------------------------------------------------------------------------------|
  | 1. Claim Stacking/Unbundling             | One treatment split into multiple claims to stay under per-incident limits                    | Each claim individually passes threshold checks | Recognizes related treatments within short timeframes, same body part, semantic similarity in descriptions |
  | 2. Medical Necessity/Overtreatment       | Excessive diagnostics or treatments for minor conditions (e.g., MRI for simple ear infection) | Rules can't assess clinical appropriateness     | Compares treatment complexity vs diagnosis severity, breed norms, age-appropriate care                     |
  | 3. Wellness-to-Illness Misclassification | Routine wellness (teeth cleaning, vaccines) submitted as "illness" to get coverage            | Rules trust submitted category                  | Analyzes procedure codes, timing patterns, diagnosis descriptions to determine true category               |

  Business Impact

  | Scenario          | Industry Loss Rate | Typical Claim Amount |
  |-------------------|--------------------|----------------------|
  | Claim Stacking    | 3-5% of claims     | $2,000-8,000         |
  | Overtreatment     | 8-12% of claims    | $500-3,000           |
  | Misclassification | 5-7% of claims     | $200-800             |

  Want me to implement these 3 additional patterns in the fraud detection system? I can:
  1. Add detection logic to the Unified API
  2. Create sample data demonstrating each pattern
  3. Update the Gold agent prompts to catch them

> apart from fraud claims, what other regular data issues (typical and advanced) that ai can catch, starting from wrong treatment category(patient error, dr error etc) , ultrathink

● This is an excellent question. Beyond fraud, there's a massive category of data quality and clinical accuracy issues that AI excels at catching. Let me break this down comprehensively:

  ---
  CATEGORY 1: SUBMISSION ERRORS (Pet Parent Side)

  | Issue Type           | Example                                                                   | Rules Can Catch  | AI Can Catch                                |
  |----------------------|---------------------------------------------------------------------------|------------------|---------------------------------------------|
  | Wrong Pet Selected   | Multi-pet household submits claim for "Max" but invoice shows "Bella"     | ❌               | ✅ Name mismatch, breed/species correlation |
  | Wrong Condition Type | Owner selects "Accident" but description says "noticed limping for weeks" | ❌               | ✅ Temporal language analysis               |
  | Timeline Confusion   | Chronic condition onset mixed with current episode date                   | ❌               | ✅ Semantic understanding of progression    |
  | Duplicate Submission | Same claim submitted twice with slight wording changes                    | Only exact match | ✅ Semantic similarity detection            |
  | Amount Transcription | Invoice shows $1,450 but owner types $1,540                               | ❌               | ✅ OCR cross-validation                     |

  ---
  CATEGORY 2: VETERINARY CODING ERRORS

  | Issue Type                   | Example                                                | Rules Can Catch       | AI Can Catch                    |
  |------------------------------|--------------------------------------------------------|-----------------------|---------------------------------|
  | Wrong Diagnosis Code         | Codes K59 (constipation) but notes describe vomiting   | ❌                    | ✅ Symptom-code correlation     |
  | Procedure-Diagnosis Mismatch | Dental cleaning code with "ear infection" diagnosis    | ❌                    | ✅ Clinical logic validation    |
  | Missing Codes                | Surgery billed without anesthesia code                 | Partial (if required) | ✅ Procedure completeness check |
  | Laterality Errors            | "Left CCL repair" but X-ray report says "right stifle" | ❌                    | ✅ Cross-document consistency   |
  | Modifier Omissions           | Bilateral procedure billed as unilateral               | ❌                    | ✅ Clinical notes analysis      |

  ---
  CATEGORY 3: CLINICAL APPROPRIATENESS

  | Issue Type                | Example                                             | Rules Can Catch | AI Can Catch                             |
  |---------------------------|-----------------------------------------------------|-----------------|------------------------------------------|
  | Over-Diagnostics          | MRI ordered for simple ear infection                | ❌              | ✅ Diagnosis severity vs test complexity |
  | Under-Treatment           | Major surgery without post-op medications           | ❌              | ✅ Standard of care comparison           |
  | Drug-Weight Mismatch      | 50lb dog prescribed dose for 100lb dog              | ❌              | ✅ Dosage calculation from weight        |
  | Contraindicated Treatment | NSAID prescribed to pet with kidney disease history | ❌              | ✅ Medical history correlation           |
  | Age-Inappropriate Care    | Aggressive chemo for 16-year-old cat                | ❌              | ✅ Age + prognosis + treatment analysis  |
  | Breed-Specific Risks      | Certain anesthetics for brachycephalic breeds       | ❌              | ✅ Breed risk database correlation       |

  ---
  CATEGORY 4: DOCUMENT INCONSISTENCIES

  | Issue Type                | Example                                                      | Rules Can Catch  | AI Can Catch                        |
  |---------------------------|--------------------------------------------------------------|------------------|-------------------------------------|
  | Invoice vs Medical Record | Invoice: "dental cleaning" / Records: "mass removal"         | ❌               | ✅ Cross-document semantic matching |
  | Date Discrepancies        | Invoice dated 12/15, medical notes dated 12/18               | Exact match only | ✅ Logical sequence validation      |
  | Provider Name Mismatch    | Invoice from "ABC Vet" but records say "XYZ Animal Hospital" | ❌               | ✅ Entity resolution                |
  | Pet Name Variations       | "Maximus" on policy, "Max" on invoice, "Maxi" in notes       | ❌               | ✅ Fuzzy name matching              |
  | OCR Errors                | "$1,0O0" extracted as "$1,000" or "$10,000"                  | ❌               | ✅ Contextual amount validation     |

  ---
  CATEGORY 5: TEMPORAL/SEQUENCE LOGIC

  | Issue Type                 | Example                                             | Rules Can Catch | AI Can Catch                     |
  |----------------------------|-----------------------------------------------------|-----------------|----------------------------------|
  | Illogical Sequence         | Follow-up visit billed before initial consultation  | Date order only | ✅ Clinical workflow logic       |
  | Treatment Before Diagnosis | Surgery date before diagnostic workup date          | ❌              | ✅ Procedure prerequisite chain  |
  | Impossible Recovery        | "Full recovery" 2 days after major spinal surgery   | ❌              | ✅ Expected recovery timeline    |
  | Missing Gaps               | Chronic medication with 6-month gap, no explanation | ❌              | ✅ Treatment continuity analysis |
  | Future Dating              | Service date is tomorrow (data entry error)         | ✅ Simple       | ✅ + Context awareness           |

  ---
  CATEGORY 6: FINANCIAL ANOMALIES (Non-Fraud)

  | Issue Type              | Example                                                          | Rules Can Catch  | AI Can Catch                       |
  |-------------------------|------------------------------------------------------------------|------------------|------------------------------------|
  | Regional Price Variance | NYC prices submitted for Iowa clinic                             | ❌               | ✅ Geographic pricing intelligence |
  | Math Errors             | Line items: $150+$200+$175 = $525, but total shows $575          | ✅ If structured | ✅ Even from unstructured invoices |
  | Missing Discounts       | Multi-pet discount not applied                                   | ❌               | ✅ Policy benefit correlation      |
  | Tax Inconsistency       | Tax charged on non-taxable veterinary services (varies by state) | ❌               | ✅ State tax rule awareness        |
  | Duplicate Line Items    | "Office visit" charged twice on same invoice                     | Pattern only     | ✅ Semantic duplicate detection    |

  ---
  CATEGORY 7: COVERAGE INTELLIGENCE

  | Issue Type                        | Example                                                                 | Rules Can Catch   | AI Can Catch                         |
  |-----------------------------------|-------------------------------------------------------------------------|-------------------|--------------------------------------|
  | Wellness Misclassified as Illness | Annual vaccines submitted as "illness prevention"                       | ❌                | ✅ Procedure type classification     |
  | Cosmetic vs Medical               | Ear cropping claimed as "ear infection treatment"                       | ❌                | ✅ Procedure intent analysis         |
  | Experimental Treatment            | Stem cell therapy claimed as standard treatment                         | ❌                | ✅ Treatment classification database |
  | Excluded Breed Condition          | Hip dysplasia claim for breed with exclusion rider                      | ✅ If coded right | ✅ Even if miscoded                  |
  | Pre-Existing Symptom Link         | "New" allergy claim, but previous notes mention "occasional scratching" | ❌                | ✅ Symptom progression analysis      |

  ---
  CATEGORY 8: CROSS-CLAIM INTELLIGENCE

  | Issue Type              | Example                                                                            | Rules Can Catch | AI Can Catch                          |
  |-------------------------|------------------------------------------------------------------------------------|-----------------|---------------------------------------|
  | Related Condition Split | Diabetes + diabetic ketoacidosis filed as separate conditions                      | ❌              | ✅ Clinical relationship mapping      |
  | Household Pattern       | All 3 pets in household have "accidents" within same month                         | Count only      | ✅ Statistical anomaly + plausibility |
  | Contradictory Claims    | Previous claim: "pet recovered fully" / New claim: "ongoing issue since last year" | ❌              | ✅ Historical narrative consistency   |
  | Treatment Effectiveness | Same treatment repeated 5 times with no improvement documented                     | ❌              | ✅ Outcome tracking                   |
  | Provider Consistency    | Same diagnosis, wildly different treatment approaches across claims                | ❌              | ✅ Standard of care comparison        |

  ---
  CATEGORY 9: SEMANTIC UNDERSTANDING

  | Issue Type             | Example                                                            | Rules Can Catch | AI Can Catch                         |
  |------------------------|--------------------------------------------------------------------|-----------------|--------------------------------------|
  | Negation Detection     | "No evidence of hip dysplasia" interpreted as having hip dysplasia | ❌              | ✅ NLP negation handling             |
  | Uncertainty Language   | "Possibly lymphoma" vs "Confirmed lymphoma"                        | ❌              | ✅ Diagnostic certainty scoring      |
  | Severity Extraction    | "Mild" vs "Severe" vs "Life-threatening" allergic reaction         | ❌              | ✅ Severity classification           |
  | Body Part Resolution   | "Left rear leg" = "Left hind limb" = "LHL" = "Left pelvic limb"    | ❌              | ✅ Medical terminology normalization |
  | Abbreviation Expansion | "Hx of CHF" → "History of Congestive Heart Failure"                | ❌              | ✅ Medical abbreviation database     |

  ---
  CATEGORY 10: REGULATORY/COMPLIANCE

  | Issue Type                  | Example                                                | Rules Can Catch | AI Can Catch                   |
  |-----------------------------|--------------------------------------------------------|-----------------|--------------------------------|
  | License Verification        | Veterinarian license expired or from wrong state       | External lookup | ✅ + Contextual validation     |
  | Controlled Substance Issues | Pain medication prescribed without DEA documentation   | ❌              | ✅ Drug schedule awareness     |
  | State-Specific Requirements | Missing required disclosures for certain states        | If coded        | ✅ Natural language extraction |
  | HIPAA-Adjacent Issues       | Other client's pet info visible on submitted documents | ❌              | ✅ PII detection in documents  |

  ---
  IMPACT MATRIX

  | Category                   | Frequency        | $ Impact per Claim   | Total Industry Impact |
  |----------------------------|------------------|----------------------|-----------------------|
  | Coding Errors              | 15-20% of claims | $50-500 overpayment  | High                  |
  | Clinical Appropriateness   | 8-12% of claims  | $200-2,000           | Very High             |
  | Document Inconsistency     | 10-15% of claims | Delays + rework cost | Medium                |
  | Coverage Misclassification | 5-8% of claims   | $100-800             | High                  |
  | Cross-Claim Logic          | 3-5% of claims   | $500-5,000           | Very High             |

  ---
  TOP 3 TO IMPLEMENT (Recommended)

  Based on business impact and demo value:

  | Priority | Scenario                      | Why It's Valuable                                               |
  |----------|-------------------------------|-----------------------------------------------------------------|
  | 1        | Diagnosis-Treatment Mismatch  | Clear visual demo - "This surgery doesn't match this diagnosis" |
  | 2        | Cross-Document Inconsistency  | Shows AI reading multiple docs - invoice vs medical records     |
  | 3        | Claim Completeness & Sequence | Shows AI understanding clinical workflows                       |

