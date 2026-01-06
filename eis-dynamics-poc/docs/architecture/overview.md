# Architecture Overview - Pet Insurance Platform

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PRESENTATION LAYER                                      │
│  ┌──────────────────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │     WS4: Agent Portal (Next.js 14)       │  │    WS8: Admin Portal (Next.js 14)    │  │
│  │     Port: 8080                           │  │    Port: 8081                        │  │
│  │  ┌────────┬────────┬────────┬────────┐   │  │  ┌────────┬────────┬────────┐       │  │
│  │  │Dash-   │Pet     │Claims  │Quote   │   │  │  │AI      │Cost    │Audit   │       │  │
│  │  │board   │Owner   │Manager │Wizard  │   │  │  │Config  │Monitor │Logs    │       │  │
│  │  │        │360     │        │        │   │  │  │        │        │        │       │  │
│  │  └────────┴────────┴────────┴────────┘   │  │  └────────┴────────┴────────┘       │  │
│  └──────────────────────────────────────────┘  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              UNIFIED DATA GATEWAY (Port 8000)                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     Claims Data API (FastAPI) - 60+ Endpoints                        │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │  │
│  │  │ /customers  │ │   /pets     │ │ /policies   │ │ /providers  │ │  /claims    │   │  │
│  │  │ (6 routes)  │ │ (5 routes)  │ │ (6 routes)  │ │ (5 routes)  │ │ (8 routes)  │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │  │
│  │  │   /fraud    │ │  /medical   │ │  /billing   │ │/validation  │   44 LLM Tools   │  │
│  │  │ (6 routes)  │ │ (5 routes)  │ │ (5 routes)  │ │ (7 routes)  │   for Agents     │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                   │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
           │                    │                    │                    │
           ▼                    ▼                    ▼                    ▼
┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
│  WS2: AI CLAIMS    │ │  WS3: INTEGRATION  │ │  WS5: RATING       │ │  WS8: ADMIN API    │
│  Port: 8001        │ │  Port: 8002        │ │  Port: 8003        │ │  Port: 8008        │
│ ┌────────────────┐ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │
│ │ FNOL Processor │ │ │ │ Mock EIS APIs  │ │ │ │ Rate Calculator│ │ │ │ Config Mgmt    │ │
│ │ • Vet Invoice  │ │ │ │ • Pet Policies │ │ │ │ • Species Rates│ │ │ │ • AI Provider  │ │
│ │ • Pet Symptoms │ │ │ │ • Pet Claims   │ │ │ │ • Breed Factors│ │ │ │ • Claims Rules │ │
│ │ • Treatment    │ │ │ │ • Pet Owners   │ │ │ │ • Age Curves   │ │ │ │ • Rating Conf  │ │
│ └────────────────┘ │ │ └────────────────┘ │ │ └────────────────┘ │ │ └────────────────┘ │
│ ┌────────────────┐ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │
│ │ Fraud Detector │ │ │ │ Sync Service   │ │ │ │ Coverage Plans │ │ │ │ Cost Monitor   │ │
│ │ • Pre-existing │ │ │ │ • EIS→D365     │ │ │ │ • Accident Only│ │ │ │ • Azure Costs  │ │
│ │ • Duplicate    │ │ │ │ • Webhooks     │ │ │ │ • Acc+Illness  │ │ │ │ • AWS Costs    │ │
│ │ • Wait Period  │ │ │ │ • Retry Logic  │ │ │ │ • Comprehensive│ │ │ │ • Budget Alert │ │
│ └────────────────┘ │ │ └────────────────┘ │ │ └────────────────┘ │ │ └────────────────┘ │
└────────────────────┘ └────────────────────┘ └────────────────────┘ └────────────────────┘
           │                                           │
           └────────────────────┬──────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI PROCESSING SERVICES                                        │
│  ┌────────────────────────────────────────┐  ┌────────────────────────────────────────┐  │
│  │   WS6: Agent Pipeline (Port 8006)      │  │    WS7: DocGen Service (Port 8007)     │  │
│  │   LangGraph + Medallion Architecture   │  │    AI Document Processing              │  │
│  │  ┌────────────────────────────────┐    │  │  ┌────────────────────────────────┐    │  │
│  │  │ Router → Bronze → Silver → Gold│    │  │  │ Extract → Mapper → Validate   │    │  │
│  │  │  Agent    Agent    Agent  Agent│    │  │  │  Agent    Agent    Agent       │    │  │
│  │  └────────────────────────────────┘    │  │  └────────────────────────────────┘    │  │
│  │  • WebSocket: /ws/events               │  │  • Export: PDF, Word, CSV              │  │
│  │  • 44 LLM Tools via Claims Data API    │  │  • Upload: PDF, Image, ZIP             │  │
│  │  • AI: Claude claude-sonnet-4-20250514 / GPT-4o           │  │  • AI: Claude claude-sonnet-4-20250514 / GPT-4o          │  │
│  └────────────────────────────────────────┘  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AI PROVIDERS                                            │
│  ┌─────────────────────────────────┐     ┌─────────────────────────────────┐             │
│  │      Anthropic Claude API       │     │       OpenAI API                │             │
│  │  ┌───────────────────────────┐  │     │  ┌───────────────────────────┐  │             │
│  │  │  claude-sonnet-4-20250514 (Default)     │  │     │  │  gpt-4o (Fallback)        │  │             │
│  │  │  • Agent Processing       │  │     │  │  • Agent Processing       │  │             │
│  │  │  • Document Analysis      │  │     │  │  • Document Analysis      │  │             │
│  │  │  • Fraud Detection        │  │     │  │  • Fraud Detection        │  │             │
│  │  └───────────────────────────┘  │     │  └───────────────────────────┘  │             │
│  └─────────────────────────────────┘     └─────────────────────────────────┘             │
│                                                                                           │
│  ┌─────────────────────────────────┐                                                     │
│  │   Azure Document Intelligence   │   (Optional - for enhanced OCR)                     │
│  │  • Vet Invoice OCR              │                                                     │
│  │  • Form Recognition             │                                                     │
│  └─────────────────────────────────┘                                                     │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              MESSAGING & EVENTS LAYER                                      │
│  ┌────────────────────────────────────────┐  ┌────────────────────────────────────────┐  │
│  │           Redis (WS6 Events)           │  │        Azure Service Bus (Optional)    │  │
│  │  • Pipeline event streaming            │  │  • pet-policy-sync (Queue)             │  │
│  │  • Real-time WebSocket broadcasts      │  │  • pet-claim-sync (Queue)              │  │
│  │  • Heartbeat: 30s                      │  │  • claim-events (Topic)                │  │
│  │  • Max connections: 100                │  │    └─▶ dataverse-sync subscription    │  │
│  └────────────────────────────────────────┘  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA LAYER                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │   Local File Storage │  │  Dataverse (D365)    │  │  Azure Blob Storage  │            │
│  │  ┌────────────────┐  │  │  ┌────────────────┐  │  │  ┌────────────────┐  │            │
│  │  │ data/          │  │  │  │  eis_policy    │  │  │  │  vet-invoices  │  │            │
│  │  │  customers.csv │  │  │  │  eis_pet       │  │  │  │  Container     │  │            │
│  │  │  pets.csv      │  │  │  │  eis_claim     │  │  │  │  • Invoices    │  │            │
│  │  │  policies.csv  │  │  │  │  eis_petowner  │  │  │  │  • Med Records │  │            │
│  │  │  claims.jsonl  │  │  │  │  eis_coverage  │  │  │  │  • Lab Results │  │            │
│  │  │  providers.csv │  │  │  │  eis_vetprovdr │  │  │  └────────────────┘  │            │
│  │  └────────────────┘  │  │  └────────────────┘  │  │                      │            │
│  │  100 customers       │  │  Power Platform      │  │  Hot/Cool Tiers      │            │
│  │  150 pets            │  └──────────────────────┘  └──────────────────────┘            │
│  │  438 claims          │                                                                │
│  │  51 providers        │  ┌──────────────────────┐                                      │
│  └──────────────────────┘  │    Azure Cosmos DB   │  (Optional for WS8)                  │
│                            │  • sync_state        │                                      │
│                            │  • audit_logs        │                                      │
│                            │  • config_state      │                                      │
│                            └──────────────────────┘                                      │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Pet Insurance Domain Model

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET INSURANCE DOMAIN MODEL                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐           │
│  │   PET OWNER     │ 1    n  │    POLICY       │ 1    n  │    PET          │           │
│  │   (Customer)    │─────────│                 │─────────│                 │           │
│  ├─────────────────┤         ├─────────────────┤         ├─────────────────┤           │
│  │ customer_id     │         │ policy_id       │         │ pet_id          │           │
│  │ first_name      │         │ policy_number   │         │ name            │           │
│  │ last_name       │         │ effective_date  │         │ species         │           │
│  │ email           │         │ expiration_date │         │ breed           │           │
│  │ phone           │         │ status          │         │ date_of_birth   │           │
│  │ address         │         │ plan_type       │         │ gender          │           │
│  │ customer_type   │         │ total_premium   │         │ microchip_id    │           │
│  └─────────────────┘         │ deductible      │         │ weight          │           │
│                              │ annual_limit    │         │ color           │           │
│                              │ reimbursement_%│         │ spayed_neutered │           │
│                              └────────┬────────┘         │ pre_existing    │           │
│                                       │                  └─────────────────┘           │
│                                       │ 1                                               │
│                                       │ n                                               │
│                              ┌────────┴────────┐                                        │
│                              │    COVERAGE     │                                        │
│                              ├─────────────────┤                                        │
│                              │ coverage_id     │                                        │
│                              │ coverage_type   │ (accident, illness, wellness, dental) │
│                              │ limit           │                                        │
│                              │ waiting_period  │ (0-14 days)                           │
│                              │ premium         │                                        │
│                              └─────────────────┘                                        │
│                                                                                          │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐           │
│  │    CLAIM        │ 1    n  │  CLAIM LINE     │ n    1  │  VET PROVIDER   │           │
│  │                 │─────────│  ITEM           │─────────│                 │           │
│  ├─────────────────┤         ├─────────────────┤         ├─────────────────┤           │
│  │ claim_id        │         │ line_id         │         │ provider_id     │           │
│  │ claim_number    │         │ service_date    │         │ clinic_name     │           │
│  │ policy_id       │         │ service_type    │ (exam,  │ address         │           │
│  │ pet_id          │         │                 │  surgery│ phone           │           │
│  │ date_of_service │         │                 │  lab,   │ license_number  │           │
│  │ date_reported   │         │                 │  meds)  │ email           │           │
│  │ status          │         │ diagnosis_code  │         └─────────────────┘           │
│  │ condition_type  │ (illness│ treatment_desc  │                                        │
│  │                 │  accident│ amount_billed   │                                        │
│  │                 │  wellness│ amount_approved │                                        │
│  │ total_billed    │         │ amount_paid     │                                        │
│  │ total_approved  │         │ denial_reason   │                                        │
│  │ fraud_score     │         └─────────────────┘                                        │
│  │ pre_existing_flg│                                                                    │
│  └─────────────────┘                                                                    │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Coverage Types - Pet Insurance

| Coverage Type | Description | Typical Limits | Waiting Period |
|---------------|-------------|----------------|----------------|
| `accident` | Injuries (broken bones, lacerations, ingestion) | $5,000 - $30,000/year | 0-3 days |
| `illness` | Sickness, infections, diseases, cancer | $5,000 - $30,000/year | 14 days |
| `wellness` | Routine care (vaccines, checkups, flea/tick) | $200 - $600/year | None |
| `dental` | Dental illness and periodontal disease | $500 - $1,500/year | 14 days |
| `hereditary` | Breed-specific conditions (hip dysplasia, etc.) | Included or excluded | 14 days |
| `behavioral` | Behavioral therapy and training | $500 - $1,000/year | 14 days |
| `alternative` | Acupuncture, chiropractic, hydrotherapy | $500 - $2,000/year | 14 days |

## Claim Types & Examples

| Claim Type | Examples |
|------------|----------|
| **Accident** | Broken leg, laceration, foreign body ingestion (sock, toy), hit by car, bee sting |
| **Illness** | Ear infection, UTI, diabetes, cancer, allergies, vomiting/diarrhea, kennel cough |
| **Wellness** | Annual checkup, vaccinations, heartworm test, flea/tick prevention, microchipping |
| **Surgery** | ACL/CCL repair, tumor removal, gastropexy, eye surgery, dental extraction |
| **Hospitalization** | Overnight stay, ICU, IV fluids, oxygen therapy |
| **Diagnostic** | X-ray, bloodwork, ultrasound, MRI, urinalysis, biopsy |
| **Medication** | Antibiotics, pain medication, insulin, allergy meds, anxiety medication |

## AI Claims Processing - Pet Insurance Example

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  INPUT (Free Text from Pet Owner)                                                        │
│  ─────────────────────────────────────────────────────────────────────────────────────  │
│  "My golden retriever Max started limping yesterday after playing at the dog park.      │
│   He won't put weight on his back left leg. The vet did x-rays and said it's a torn    │
│   CCL (cruciate ligament). They're recommending TPLO surgery which costs $4,500.       │
│   Max is 5 years old and has been healthy until now."                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                         GPT-4o
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  OUTPUT (Structured Extraction)                                                          │
│  ─────────────────────────────────────────────────────────────────────────────────────  │
│  {                                                                                       │
│    "pet_name": "Max",                                                                   │
│    "species": "dog",                                                                    │
│    "breed": "Golden Retriever",                                                         │
│    "pet_age_years": 5,                                                                  │
│    "condition_type": "accident",                                                        │
│    "diagnosis": "Torn CCL (Cranial Cruciate Ligament)",                                │
│    "affected_body_part": "back left leg",                                               │
│    "symptoms": ["limping", "non-weight-bearing"],                                       │
│    "recommended_treatment": "TPLO surgery",                                             │
│    "diagnostic_performed": ["x-ray"],                                                   │
│    "estimated_cost": 4500.00,                                                           │
│    "date_of_onset": "2024-06-14",                                                       │
│    "pre_existing_indicators": [],                                                       │
│    "severity": "moderate",                                                              │
│    "urgency": "scheduled",                                                              │
│    "fraud_indicators": [],                                                              │
│    "confidence_score": 0.94                                                             │
│  }                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  TRIAGE RECOMMENDATION                                                                   │
│  ─────────────────────────────────────────────────────────────────────────────────────  │
│  {                                                                                       │
│    "claim_category": "orthopedic_surgery",                                              │
│    "auto_approve": false,                                                               │
│    "requires_review": true,                                                             │
│    "review_reasons": [                                                                  │
│      "Surgery claim over $3,000 threshold",                                            │
│      "CCL is hereditary/congenital in some breeds"                                     │
│    ],                                                                                   │
│    "coverage_check": {                                                                  │
│      "covered": true,                                                                   │
│      "coverage_type": "accident",                                                       │
│      "annual_limit_remaining": 8500.00,                                                 │
│      "deductible_remaining": 0.00,                                                      │
│      "reimbursement_rate": 0.80                                                         │
│    },                                                                                   │
│    "estimated_payout": 3600.00,                                                         │
│    "notes": "Golden Retrievers prone to CCL issues. Verify this is acute injury,       │
│              not chronic/pre-existing condition. Request full medical history."         │
│  }                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Pet Insurance Fraud Detection

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRAUD DETECTION INDICATORS                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Common Pet Insurance Fraud Patterns:                                                   │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│  │  1. PRE-EXISTING CONDITIONS                                                        │ │
│  │     • Claim submitted within waiting period                                        │ │
│  │     • Condition matches breed-specific hereditary issues                          │ │
│  │     • Symptoms described suggest chronic condition                                │ │
│  │     • Prior vet records show earlier treatment                                    │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│  │  2. DUPLICATE/INFLATED CLAIMS                                                      │ │
│  │     • Same treatment claimed to multiple insurers                                 │ │
│  │     • Invoice totals don't match itemized charges                                │ │
│  │     • Unusually high charges for standard procedures                              │ │
│  │     • Multiple claims for same condition in short period                          │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│  │  3. PHANTOM PET / IDENTITY FRAUD                                                   │ │
│  │     • No microchip verification available                                         │ │
│  │     • Pet age/breed doesn't match policy records                                  │ │
│  │     • Different pets treated under same policy                                    │ │
│  │     • Vet records show inconsistent pet descriptions                              │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│  │  4. VET COLLUSION                                                                  │ │
│  │     • Clinic flagged for suspicious billing patterns                              │ │
│  │     • Unbundled services to maximize claims                                       │ │
│  │     • Unnecessary procedures recommended                                          │ │
│  │     • Invoice alterations detected                                                │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
│  Fraud Score Calculation:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                                    │ │
│  │  Score 0.0 - 0.3  →  LOW RISK      →  Auto-process eligible                      │ │
│  │  Score 0.3 - 0.6  →  MEDIUM RISK   →  Standard review queue                      │ │
│  │  Score 0.6 - 0.8  →  HIGH RISK     →  Senior adjuster review                     │ │
│  │  Score 0.8 - 1.0  →  CRITICAL      →  SIU (Special Investigations Unit)          │ │
│  │                                                                                    │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Overview

### Presentation Layer

#### WS4: Agent Portal (Port 8080)
- **Technology**: Next.js 14 with App Router, React 18, TypeScript
- **Purpose**: Agent-facing dashboard for pet insurance operations
- **Key Pages**:
  - Dashboard with pet/claim statistics
  - Pet Owner 360 view (owner, pets, policies, claims)
  - Pet Claim Manager with AI triage
  - Pet Quote Wizard (species, breed, age, coverage)
  - Pipeline visualization with XYFlow

#### WS8: Admin Portal (Port 8081)
- **Technology**: Next.js 14, React 18, Zustand, Recharts
- **Purpose**: Administrative configuration and monitoring
- **Key Features**:
  - AI provider/model configuration
  - Cost monitoring (Azure/AWS)
  - Audit log viewing
  - User/role management
  - Maker-checker approval workflow

### Unified Data Gateway

#### Claims Data API (Port 8000)
- **Framework**: FastAPI (Python 3.11+)
- **Purpose**: Single gateway for all claims data services
- **Endpoints**: 60+ endpoints across 10 route groups
- **Features**:
  - Customer, Pet, Policy, Provider, Claims management
  - Fraud pattern detection
  - Medical reference data
  - Billing & financial data
  - AI validation services
  - 44 LLM tools for agent processing

### Microservices

#### WS2: AI Claims Service (Port 8001)
- **Framework**: FastAPI (Python 3.11+)
- **Responsibilities**:
  - Pet FNOL intake and processing
  - AI-powered extraction from documents
  - Claim severity and priority triage
  - Fraud analysis and detection
  - Pre-existing condition detection

#### WS3: Integration Layer (Port 8002)
- **Framework**: FastAPI (Python 3.11+)
- **Responsibilities**:
  - Mock EIS Suite APIs for pets, policies, claims
  - D365 Dataverse synchronization
  - Webhook processing
  - Vet provider management
  - Entity mapping (EIS → Dataverse)

#### WS5: Rating Engine (Port 8003)
- **Framework**: FastAPI (Python 3.11+)
- **Responsibilities**:
  - Pet premium calculation
  - Species/breed rating factors
  - Age-based pricing curves
  - Multi-pet, annual pay, shelter/rescue, military discounts
  - Coverage plans: Accident Only, Accident+Illness, Comprehensive

#### WS8: Admin Backend (Port 8008)
- **Framework**: FastAPI (Python 3.11+)
- **Responsibilities**:
  - AI provider/model configuration
  - Claims processing rules
  - Rating factor configuration
  - Cost monitoring (Azure Cost Management, AWS Cost Explorer)
  - Audit logging and retrieval
  - User/role management with RBAC
  - Maker-checker workflow for config changes

### AI Processing Services

#### WS6: Agent Pipeline (Port 8006)
- **Framework**: FastAPI + LangGraph
- **AI Models**: Claude claude-sonnet-4-20250514 (default), GPT-4o (fallback)
- **Architecture**: Medallion (Bronze → Silver → Gold)
- **Features**:
  - Router agent for complexity classification
  - Bronze agent for data validation/cleansing
  - Silver agent for data enrichment
  - Gold agent for risk assessment and decisions
  - WebSocket real-time events (/ws/events)
  - Async and sync pipeline triggers
  - Demo scenarios and comparison endpoints

#### WS7: DocGen Service (Port 8007)
- **Framework**: FastAPI + LangChain
- **AI Models**: Claude claude-sonnet-4-20250514 (default), GPT-4o (fallback)
- **Features**:
  - Document upload (PDF, Image, ZIP)
  - OCR and text extraction
  - Schema mapping to claims
  - Data validation and completeness check
  - Export: PDF, Word, CSV formats
  - Batch processing support

### Data Stores
- **Local CSV/JSONL**: 100 customers, 150 pets, 438 claims, 51 providers
- **Cosmos DB** (Optional): Sync state, audit logs, config state
- **Dataverse**: Pet owners, pets, policies, claims, vet providers
- **Blob Storage**: Vet invoices, lab results, medical records
- **Redis**: Pipeline event streaming

## Network Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              MULTI-CLOUD DEPLOYMENT                                        │
│                                                                                            │
│  ┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐       │
│  │         AWS (US-EAST-1)             │    │         AZURE (EAST US)              │       │
│  │  ┌───────────────────────────────┐  │    │  ┌───────────────────────────────┐  │       │
│  │  │        AWS AppRunner          │  │    │  │      Azure Services           │  │       │
│  │  │  ┌─────────────┬────────────┐ │  │    │  │  ┌─────────────┬───────────┐  │  │       │
│  │  │  │Claims Data  │Agent       │ │  │    │  │  │ Cosmos DB   │ Blob      │  │  │       │
│  │  │  │API :8000    │Pipeline    │ │  │    │  │  │ (Optional)  │ Storage   │  │  │       │
│  │  │  │             │:8006       │ │  │    │  │  └─────────────┴───────────┘  │  │       │
│  │  │  └─────────────┴────────────┘ │  │    │  │  ┌─────────────┬───────────┐  │  │       │
│  │  └───────────────────────────────┘  │    │  │  │ Service Bus │ Key Vault │  │  │       │
│  │                                     │    │  │  │ (Optional)  │           │  │  │       │
│  │  Live URLs:                         │    │  │  └─────────────┴───────────┘  │  │       │
│  │  • p7qrmgi9sp.us-east-1.awsapprunner│    │  │                               │  │       │
│  │  • bn9ymuxtwp.us-east-1.awsapprunner│    │  │  Dataverse (D365 CRM)         │  │       │
│  └─────────────────────────────────────┘    └──────────────────────────────────────┘       │
│                                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           LOCAL DEVELOPMENT                                          │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │  │
│  │  │ WS4 UI  │ │Claims   │ │ WS2 AI  │ │ WS3 Int │ │WS5 Rate │ │WS6 Pipe │           │  │
│  │  │ :8080   │ │API:8000 │ │ :8001   │ │ :8002   │ │ :8003   │ │ :8006   │           │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                                               │  │
│  │  │WS7 Doc  │ │WS8 Admin│ │WS8 Admin│                                               │  │
│  │  │ :8007   │ │API:8008 │ │UI:8081  │                                               │  │
│  │  └─────────┘ └─────────┘ └─────────┘                                               │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Service Port Summary

| Service | Local Port | Production URL |
|---------|------------|----------------|
| Claims Data API | 8000 | https://p7qrmgi9sp.us-east-1.awsapprunner.com |
| WS2: AI Claims | 8001 | - |
| WS3: Integration | 8002 | - |
| WS5: Rating Engine | 8003 | - |
| WS6: Agent Pipeline | 8006 | https://bn9ymuxtwp.us-east-1.awsapprunner.com |
| WS7: DocGen | 8007 | - |
| WS8: Admin Backend | 8008 | - |
| WS4: Agent Portal | 8080 | - |
| WS8: Admin Portal | 8081 | - |

## Key Design Decisions

1. **Pet-Centric Data Model**: Pets are first-class entities, not just attributes of policies
2. **Breed-Based Rating**: Extensive breed database for accurate risk assessment
3. **AI-Powered Processing**: Claude/GPT-4o for claims analysis, fraud detection, document processing
4. **Medallion Architecture**: Bronze → Silver → Gold data processing layers in agent pipeline
5. **Multi-Pet Policies**: Support for households with multiple pets on single policy
6. **Species-Specific Rules**: Different coverage rules for dogs, cats, exotic pets
7. **Multi-Cloud**: AWS AppRunner for production, Azure for optional enterprise services
8. **44 LLM Tools**: Rich tool ecosystem for AI agent processing via Claims Data API
