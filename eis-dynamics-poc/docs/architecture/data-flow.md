# Data Flow Architecture - Pet Insurance

## Overview

This document describes how data flows through the EIS-Dynamics POC for pet insurance, including the AI agent pipeline processing, synchronization patterns, and data transformations.

## High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET INSURANCE DATA FLOW                                      │
└──────────────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐                                           ┌─────────────────┐
  │  WS4: Agent     │                                           │  WS8: Admin     │
  │  Portal (:8080) │                                           │  Portal (:8081) │
  └────────┬────────┘                                           └────────┬────────┘
           │                                                              │
           │  HTTP/REST                                          HTTP/REST│
           ▼                                                              ▼
  ┌────────────────────────────────────────────────────────────────────────────────────┐
  │                      CLAIMS DATA API (Port 8000) - Unified Gateway                  │
  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
  │  │Customers│ │  Pets   │ │Policies │ │Providers│ │ Claims  │ │ Fraud   │          │
  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                                               │
  │  │ Medical │ │ Billing │ │Validation│  ◀──── 44 LLM Tools for Agent Processing    │
  │  └─────────┘ └─────────┘ └─────────┘                                               │
  └────────────────────────────────────────────────────────────────────────────────────┘
           │                    │                    │                    │
           ▼                    ▼                    ▼                    ▼
  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
  │ WS2: AI Claims │   │WS3: Integration│   │ WS5: Rating    │   │ WS8: Admin API │
  │ (:8001)        │   │ (:8002)        │   │ (:8003)        │   │ (:8008)        │
  │ • FNOL Process │   │ • Mock EIS API │   │ • Quote Calc   │   │ • Config Mgmt  │
  │ • Fraud Detect │   │ • D365 Sync    │   │ • Rate Factors │   │ • Cost Monitor │
  └────────────────┘   └────────────────┘   └────────────────┘   └────────────────┘
           │                                         │
           └─────────────────┬───────────────────────┘
                             ▼
  ┌────────────────────────────────────────────────────────────────────────────────────┐
  │                            AI PROCESSING LAYER                                      │
  │  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐  │
  │  │  WS6: Agent Pipeline (:8006)        │  │   WS7: DocGen Service (:8007)       │  │
  │  │  LangGraph Medallion Architecture   │  │   AI Document Processing            │  │
  │  │                                     │  │                                     │  │
  │  │  Router → Bronze → Silver → Gold    │  │  Extract → Mapper → Validate        │  │
  │  │   ▲                          │      │  │     │                    │          │  │
  │  │   │ WebSocket (/ws/events)   ▼      │  │     ▼                    ▼          │  │
  │  │  Real-time      Decision/Insights   │  │  PDF/Word/CSV Export               │  │
  │  │  Events                             │  │                                     │  │
  │  └─────────────────────────────────────┘  └─────────────────────────────────────┘  │
  └────────────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────────────────────────────────┐
  │                              DATA LAYER                                             │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
  │  │  Local Storage  │  │  Dataverse      │  │  Azure Storage  │                     │
  │  │  (CSV/JSONL)    │  │  (D365 CRM)     │  │  (Blob/Cosmos)  │                     │
  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                     │
  └────────────────────────────────────────────────────────────────────────────────────┘
```

## Agent Pipeline Flow (WS6)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                        LANGGRAPH AGENT PIPELINE DATA FLOW                                 │
└──────────────────────────────────────────────────────────────────────────────────────────┘

  Claim Input (JSON)
       │
       ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │  ROUTER AGENT                                                                        │
  │  ─────────────                                                                       │
  │  Input:  Raw claim data                                                              │
  │  Action: Analyze complexity, determine routing path                                  │
  │  Output: Routing decision (fast_track | standard | enhanced)                        │
  │                                                                                      │
  │  Tools Used:                                                                         │
  │  • claim_analysis - Assess claim complexity                                          │
  │  • policy_lookup - Verify policy exists                                              │
  └─────────────────────────────────────────────────────────────────────────────────────┘
       │
       │  Routing Decision
       ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │  BRONZE AGENT (Data Validation & Cleansing)                                          │
  │  ────────────                                                                        │
  │  Input:  Raw claim + routing decision                                                │
  │  Action: Validate fields, cleanse data, assess quality                               │
  │  Output: Validated claim + quality score                                             │
  │                                                                                      │
  │  Tools Used (via Claims Data API):                                                   │
  │  • validate_claim_data - Schema validation                                           │
  │  • check_required_fields - Completeness check                                        │
  │  • normalize_amounts - Currency/number standardization                               │
  │  • validate_dates - Date range validation                                            │
  │  • check_diagnosis_codes - Medical code validation                                   │
  │                                                                                      │
  │  Data Written: ./data/agent_pipeline/bronze/{run_id}.json                            │
  └─────────────────────────────────────────────────────────────────────────────────────┘
       │
       │  Validated Claim
       ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │  SILVER AGENT (Data Enrichment)                                                      │
  │  ────────────                                                                        │
  │  Input:  Validated claim                                                             │
  │  Action: Enrich with policy, customer, provider context                              │
  │  Output: Enriched claim with full context                                            │
  │                                                                                      │
  │  Tools Used (via Claims Data API):                                                   │
  │  • get_policy_details - Full policy information                                      │
  │  • get_customer_profile - Customer history and risk                                  │
  │  • get_pet_medical_history - Prior conditions and claims                             │
  │  • verify_provider - Vet provider validation                                         │
  │  • check_coverage_eligibility - Coverage verification                                │
  │                                                                                      │
  │  Data Written: ./data/agent_pipeline/silver/{run_id}.json                            │
  └─────────────────────────────────────────────────────────────────────────────────────┘
       │
       │  Enriched Claim
       ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │  GOLD AGENT (Risk Assessment & Decision)                                             │
  │  ──────────                                                                          │
  │  Input:  Enriched claim with full context                                            │
  │  Action: Risk scoring, fraud detection, final recommendation                         │
  │  Output: Decision + reasoning + insights                                             │
  │                                                                                      │
  │  Tools Used (via Claims Data API):                                                   │
  │  • calculate_risk_score - Multi-factor risk assessment                               │
  │  • check_fraud_patterns - Pattern matching against known fraud                       │
  │  • check_pre_existing - Pre-existing condition detection                             │
  │  • calculate_payout - Eligible amount calculation                                    │
  │  • generate_recommendation - Final decision with reasoning                           │
  │  • create_audit_trail - Compliance documentation                                     │
  │                                                                                      │
  │  Data Written: ./data/agent_pipeline/gold/{run_id}.json                              │
  │                                                                                      │
  │  Final Output:                                                                       │
  │  {                                                                                   │
  │    "decision": "APPROVED | DENIED | REVIEW",                                         │
  │    "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",                                   │
  │    "confidence": 0.0 - 1.0,                                                          │
  │    "reasoning": ["...", "..."],                                                      │
  │    "insights": ["...", "..."],                                                       │
  │    "recommended_payout": 0.00,                                                       │
  │    "flags": ["pre_existing", "fraud_risk", ...]                                      │
  │  }                                                                                   │
  └─────────────────────────────────────────────────────────────────────────────────────┘
       │
       │  WebSocket Event Stream
       ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────┐
  │  REAL-TIME EVENTS (WebSocket /ws/events)                                             │
  │  ───────────────────────────────────────                                             │
  │  Events emitted during processing:                                                   │
  │  • pipeline.started - Processing begins                                              │
  │  • router.completed - Routing decision made                                          │
  │  • bronze.started / bronze.completed - Validation layer                              │
  │  • silver.started / silver.completed - Enrichment layer                              │
  │  • gold.started / gold.completed - Decision layer                                    │
  │  • pipeline.completed - Final results ready                                          │
  │  • pipeline.error - Processing failed                                                │
  │                                                                                      │
  │  Heartbeat: 30 seconds                                                               │
  │  Max Connections: 100                                                                │
  └─────────────────────────────────────────────────────────────────────────────────────┘
```

## Pet Insurance Entity Mapping

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET INSURANCE ENTITY MAPPING                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  EIS Pet Policy                            Dataverse eis_policy
  ─────────────────────                     ─────────────────────
  policy_id             ───────────────▶    eis_eissourceid
  policy_number         ───────────────▶    eis_policynumber
  effective_date        ───────────────▶    eis_effectivedate
  expiration_date       ───────────────▶    eis_expirationdate
  status                ───────────────▶    eis_status (OptionSet)
  plan_type             ───────────────▶    eis_plantype (OptionSet)
                                            [accident_only, accident_illness, comprehensive]
  total_premium         ───────────────▶    eis_totalpremium (Currency)
  annual_limit          ───────────────▶    eis_annuallimit (Currency)
  deductible            ───────────────▶    eis_deductible (Currency)
  reimbursement_pct     ───────────────▶    eis_reimbursementpercent (Integer)
  customer_id           ───────────────▶    eis_petownerid (Lookup)


  EIS Pet                                   Dataverse eis_pet
  ─────────────────────                     ─────────────────────
  pet_id                ───────────────▶    eis_eissourceid
  name                  ───────────────▶    eis_petname
  species               ───────────────▶    eis_species (OptionSet)
                                            [dog, cat, bird, rabbit, reptile, other]
  breed                 ───────────────▶    eis_breed
  date_of_birth         ───────────────▶    eis_dateofbirth
  gender                ───────────────▶    eis_gender (OptionSet)
  microchip_id          ───────────────▶    eis_microchipid
  weight                ───────────────▶    eis_weight (Decimal)
  color                 ───────────────▶    eis_color
  spayed_neutered       ───────────────▶    eis_spayedneutered (Boolean)
  pre_existing          ───────────────▶    eis_preexistingconditions
  policy_id             ───────────────▶    eis_policyid (Lookup)


  EIS Pet Claim                             Dataverse eis_claim
  ─────────────────────                     ─────────────────────
  claim_id              ───────────────▶    eis_eissourceid
  claim_number          ───────────────▶    eis_claimnumber
  policy_id             ───────────────▶    eis_policyid (Lookup)
  pet_id                ───────────────▶    eis_petid (Lookup)
  date_of_service       ───────────────▶    eis_dateofservice
  date_reported         ───────────────▶    eis_datereported
  status                ───────────────▶    eis_status (OptionSet)
                                            [submitted, under_review, approved, denied, paid]
  condition_type        ───────────────▶    eis_conditiontype (OptionSet)
                                            [accident, illness, wellness, dental]
  diagnosis             ───────────────▶    eis_diagnosis
  treatment             ───────────────▶    eis_treatment
  vet_provider_id       ───────────────▶    eis_vetproviderid (Lookup)
  amount_billed         ───────────────▶    eis_amountbilled (Currency)
  amount_approved       ───────────────▶    eis_amountapproved (Currency)
  amount_paid           ───────────────▶    eis_amountpaid (Currency)
  fraud_score           ───────────────▶    eis_fraudscore (Decimal)
  pre_existing_flag     ───────────────▶    eis_preexistingflag (Boolean)
  ai_recommendation     ───────────────▶    eis_airecommendation


  EIS Pet Owner                             Dataverse eis_petowner
  ─────────────────────                     ─────────────────────
  customer_id           ───────────────▶    eis_eissourceid
  first_name            ───────────────▶    eis_firstname
  last_name             ───────────────▶    eis_lastname
  first_name+last_name  ───────────────▶    eis_fullname
  email                 ───────────────▶    eis_email
  phone                 ───────────────▶    eis_phone
  address               ───────────────▶    eis_address
  city                  ───────────────▶    eis_city
  state                 ───────────────▶    eis_state
  zip_code              ───────────────▶    eis_zipcode


  EIS Vet Provider                          Dataverse eis_vetprovider
  ─────────────────────                     ─────────────────────
  provider_id           ───────────────▶    eis_eissourceid
  clinic_name           ───────────────▶    eis_clinicname
  address               ───────────────▶    eis_address
  phone                 ───────────────▶    eis_phone
  email                 ───────────────▶    eis_email
  license_number        ───────────────▶    eis_licensenumber
  is_preferred          ───────────────▶    eis_ispreferred (Boolean)
  fraud_flag            ───────────────▶    eis_fraudflag (Boolean)
```

## Pet Claim Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET CLAIM FNOL PROCESSING                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Agent Portal          AI Claims Service              Azure OpenAI              Dataverse
     │                         │                            │                       │
     │  1. Submit Pet Claim    │                            │                       │
     │     (Vet invoice +      │                            │                       │
     │      description)       │                            │                       │
     │ ───────────────────────▶│                            │                       │
     │                         │                            │                       │
     │                         │  2. OCR Vet Invoice        │                       │
     │                         │     (Doc Intelligence)     │                       │
     │                         │──────────┐                 │                       │
     │                         │          │                 │                       │
     │                         │◀─────────┘                 │                       │
     │                         │                            │                       │
     │                         │  3. Extract Pet Condition  │                       │
     │                         │ ──────────────────────────▶│                       │
     │                         │                            │                       │
     │                         │                            │  4. AI Analyzes       │
     │                         │                            │     • Pet symptoms    │
     │                         │                            │     • Diagnosis       │
     │                         │                            │     • Pre-existing?   │
     │                         │                            │──────────┐            │
     │                         │                            │          │            │
     │                         │                            │◀─────────┘            │
     │                         │                            │                       │
     │                         │        5. Structured Data  │                       │
     │                         │ ◀──────────────────────────│                       │
     │                         │    • Pet: Max (Golden Ret.)│                       │
     │                         │    • Condition: CCL tear   │                       │
     │                         │    • Type: Accident        │                       │
     │                         │    • Est. Cost: $4,500     │                       │
     │                         │    • Pre-existing: No      │                       │
     │                         │                            │                       │
     │                         │  6. Check for Fraud        │                       │
     │                         │     • Waiting period       │                       │
     │                         │     • Duplicate claims     │                       │
     │                         │     • Vet clinic history   │                       │
     │                         │ ──────────────────────────▶│                       │
     │                         │                            │                       │
     │                         │        7. Fraud Score      │                       │
     │                         │ ◀──────────────────────────│                       │
     │                         │                            │                       │
     │                         │  8. Create Pet Claim       │                       │
     │                         │ ─────────────────────────────────────────────────▶│
     │                         │                            │                       │
     │  9. Return Claim        │                            │                       │
     │     with Triage         │                            │                       │
     │ ◀───────────────────────│                            │                       │
     │                         │                            │                       │
     ▼                         ▼                            ▼                       ▼
```

## Pet Quote/Rating Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET INSURANCE QUOTE FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Agent Portal             Rating Engine                 Factor Service            EIS Mock
     │                          │                              │                      │
     │  1. Request Quote        │                              │                      │
     │     (Pet info, Owner)    │                              │                      │
     │ ────────────────────────▶│                              │                      │
     │                          │                              │                      │
     │                          │  2. Validate Pet Data        │                      │
     │                          │     • Species valid?         │                      │
     │                          │     • Breed recognized?      │                      │
     │                          │     • Age eligible?          │                      │
     │                          │──────────┐                   │                      │
     │                          │          │                   │                      │
     │                          │◀─────────┘                   │                      │
     │                          │                              │                      │
     │                          │  3. Get Breed Factors        │                      │
     │                          │ ────────────────────────────▶│                      │
     │                          │                              │                      │
     │                          │        4. Returns:           │                      │
     │                          │           • Base rate/breed  │                      │
     │                          │           • Risk factors     │                      │
     │                          │           • Hereditary cond. │                      │
     │                          │ ◀────────────────────────────│                      │
     │                          │                              │                      │
     │                          │  5. Calculate:               │                      │
     │                          │     • Species factor         │                      │
     │                          │     • Breed factor           │                      │
     │                          │     • Age curve              │                      │
     │                          │     • Location factor        │                      │
     │                          │     • Coverage charges       │                      │
     │                          │     • Discounts              │                      │
     │                          │──────────┐                   │                      │
     │                          │          │                   │                      │
     │                          │◀─────────┘                   │                      │
     │                          │                              │                      │
     │                          │  6. Compare with EIS         │                      │
     │                          │ ─────────────────────────────────────────────────▶ │
     │                          │                              │                      │
     │                          │        7. EIS Premium        │                      │
     │                          │ ◀─────────────────────────────────────────────────  │
     │                          │                              │                      │
     │  8. Return Quote         │                              │                      │
     │     with Breakdown       │                              │                      │
     │ ◀────────────────────────│                              │                      │
     │                          │                              │                      │
     ▼                          ▼                              ▼                      ▼
```

## Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET INSURANCE EVENT TOPOLOGY                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                              Azure Service Bus
  ┌──────────────────────────────────────────────────────────────────────────────────────┐
  │                                                                                       │
  │    QUEUES (Point-to-Point)                                                           │
  │    ┌─────────────────────────────────────────────────────────────────┐              │
  │    │                                                                  │              │
  │    │   pet-policy-sync-queue              pet-claim-sync-queue       │              │
  │    │   ┌───┬───┬───┬───┐                 ┌───┬───┬───┬───┐          │              │
  │    │   │ M │ M │ M │ M │ ────▶ Consumer  │ M │ M │ M │ M │ ────▶    │              │
  │    │   └───┴───┴───┴───┘                 └───┴───┴───┴───┘          │              │
  │    │                                                                  │              │
  │    └─────────────────────────────────────────────────────────────────┘              │
  │                                                                                       │
  │    TOPICS (Pub/Sub)                                                                  │
  │    ┌─────────────────────────────────────────────────────────────────┐              │
  │    │                                                                  │              │
  │    │   pet-claim-events (Topic)                                      │              │
  │    │   ┌─────────────────────┐                                       │              │
  │    │   │  claim.submitted    │  (new pet claim)                      │              │
  │    │   │  claim.approved     │  (claim approved)                     │              │
  │    │   │  claim.paid         │  (reimbursement sent)                 │              │
  │    │   │  claim.denied       │  (claim rejected)                     │              │
  │    │   └──────────┬──────────┘                                       │              │
  │    │              │                                                   │              │
  │    │              ├──────────▶ dataverse-sync (Subscription)         │              │
  │    │              │            └──▶ Sync to D365                     │              │
  │    │              │                                                   │              │
  │    │              ├──────────▶ fraud-analysis (Subscription)         │              │
  │    │              │            └──▶ AI fraud check                   │              │
  │    │              │                                                   │              │
  │    │              └──────────▶ pet-owner-notify (Subscription)       │              │
  │    │                           └──▶ Send email/SMS                   │              │
  │    │                                                                  │              │
  │    └─────────────────────────────────────────────────────────────────┘              │
  │                                                                                       │
  │    DEAD LETTER QUEUES                                                                │
  │    ┌─────────────────────────────────────────────────────────────────┐              │
  │    │   pet-policy-sync-queue/$deadletterqueue                        │              │
  │    │   pet-claim-sync-queue/$deadletterqueue                         │              │
  │    │   ▲                                                              │              │
  │    │   │ Messages after 5 failed attempts                            │              │
  │    └───┼─────────────────────────────────────────────────────────────┘              │
  │        │                                                                             │
  └────────┼─────────────────────────────────────────────────────────────────────────────┘
           │
           └──────▶ Alert triggered for manual review
```

## Sync State Tracking

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              SYNC STATE (Cosmos DB)                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Pet Policy Sync Document:
  {
    "id": "sync-POL-PET-2024-001",
    "entity_type": "pet_policy",
    "eis_source_id": "POL-PET-2024-001",
    "d365_entity_id": "a1b2c3d4-e5f6-...",
    "pet_ids": ["PET-001", "PET-002"],
    "last_sync_time": "2024-06-15T14:30:00Z",
    "sync_status": "synced",
    "version": 5,
    "sync_direction": "eis_to_d365",
    "error_count": 0
  }

  Pet Claim Sync Document:
  {
    "id": "sync-CLM-PET-2024-001",
    "entity_type": "pet_claim",
    "eis_source_id": "CLM-PET-2024-001",
    "d365_entity_id": "b2c3d4e5-f6g7-...",
    "pet_id": "PET-001",
    "pet_name": "Max",
    "condition_type": "accident",
    "diagnosis": "CCL tear",
    "amount_billed": 4500.00,
    "fraud_score": 0.12,
    "pre_existing_check": "passed",
    "last_sync_time": "2024-06-15T14:30:00Z",
    "sync_status": "synced"
  }

  Status Values:
  ├── synced          # Successfully synchronized
  ├── pending         # Awaiting sync
  ├── in_progress     # Currently syncing
  ├── error           # Sync failed
  ├── fraud_review    # Flagged for fraud investigation
  ├── pre_existing    # Flagged for pre-existing condition review
  └── stale           # Needs re-sync
```

## Breed Data Reference (Cosmos DB)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              BREED DATABASE                                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  Example Breed Document:
  {
    "id": "breed-golden-retriever",
    "species": "dog",
    "breed_name": "Golden Retriever",
    "breed_group": "Sporting",
    "size_category": "large",
    "avg_weight_lbs": 65,
    "avg_lifespan_years": 11,
    "risk_factor": 1.15,
    "base_rate": 420.00,
    "hereditary_conditions": [
      "hip_dysplasia",
      "elbow_dysplasia",
      "heart_disease",
      "cancer",
      "eye_conditions"
    ],
    "common_claims": [
      "ear_infections",
      "skin_allergies",
      "ccl_tears",
      "hypothyroidism"
    ],
    "exclusion_breeds": false,
    "age_rating_curve": {
      "0-1": 0.85,
      "1-4": 1.00,
      "4-7": 1.20,
      "7-10": 1.50,
      "10+": 2.00
    }
  }
```
