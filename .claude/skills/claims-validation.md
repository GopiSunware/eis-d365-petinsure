# Claims Validation Intelligence Skill

**Comprehensive validation patterns for AI agents processing pet insurance claims.**

This skill documents ALL validation checks an AI claims processor should perform. Use this as the "brain" for claims processing - the agent should think like an experienced claims adjuster with full customer context.

## Philosophy: Agent as Claims Processor

The AI agent should act like a veteran pet insurance claims processor who:
1. **Knows the customer history** - All past claims, patterns, behaviors
2. **Remembers conversations** - Recent chat interactions, complaints, questions
3. **Spots patterns humans miss** - Cross-claim analysis, timing anomalies
4. **Makes contextual decisions** - Same claim might be valid for one customer, suspicious for another

## When to Apply Validation Checks

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CLAIM ARRIVES                                   │
│                           │                                          │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    BRONZE LAYER                                 │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ IMMEDIATE CHECKS (Block Duplicates Early)               │   │ │
│  │  │ • Exact duplicate claim (same claim_id)                 │   │ │
│  │  │ • Same customer + same pet + same diagnosis < 24 hours  │   │ │
│  │  │ • Same customer + same amount < 1 hour (double submit)  │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ VELOCITY CHECKS                                          │   │ │
│  │  │ • Customer claim frequency (>5/month = flag)             │   │ │
│  │  │ • Pet claim frequency (>3/month = flag)                  │   │ │
│  │  │ • Provider claim frequency (2x average = flag)           │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ DATA QUALITY                                             │   │ │
│  │  │ • Schema validation (required fields present)            │   │ │
│  │  │ • Format validation (dates, amounts, codes)              │   │ │
│  │  │ • Completeness score                                     │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                           │                                          │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    SILVER LAYER                                 │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ POLICY VALIDATION                                        │   │ │
│  │  │ • Policy exists and is active                            │   │ │
│  │  │ • Coverage includes claim type                           │   │ │
│  │  │ • Within policy limits                                   │   │ │
│  │  │ • Waiting period satisfied                               │   │ │
│  │  │ • Pre-existing conditions check                          │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ CLINICAL VALIDATION                                      │   │ │
│  │  │ • Diagnosis-treatment match                              │   │ │
│  │  │ • Treatment sequence logic                               │   │ │
│  │  │ • Cost reasonableness (vs benchmarks)                    │   │ │
│  │  │ • Provider license verification                          │   │ │
│  │  │ • DEA number for controlled substances                   │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                           │                                          │
│                           ▼                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    GOLD LAYER                                   │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ FRAUD DETECTION                                          │   │ │
│  │  │ • Chronic condition gaming pattern                       │   │ │
│  │  │ • Provider collusion indicators                          │   │ │
│  │  │ • Staged timing patterns                                 │   │ │
│  │  │ • Customer-provider relationship analysis                │   │ │
│  │  │ • Cross-claim pattern matching                           │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │ RISK ASSESSMENT                                          │   │ │
│  │  │ • Calculate fraud score (0-100)                          │   │ │
│  │  │ • Determine risk level (low/medium/high/critical)        │   │ │
│  │  │ • Generate alerts and recommendations                    │   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Validation Check Details

### 1. Duplicate Detection (Bronze Layer)

**Why**: Prevent double-payment for same service

| Check | Time Window | Action |
|-------|-------------|--------|
| Same claim_id | Any | REJECT |
| Same customer + pet + diagnosis | 24 hours | FLAG |
| Same customer + exact amount | 1 hour | FLAG |
| Same customer + same provider + same day | Same day | FLAG |

**Implementation**:
```python
# Bronze agent should call:
get_historical_claims(customer_id=claim.customer_id)

# Then check:
recent_claims = [c for c in history if c.submitted_within(hours=24)]
for recent in recent_claims:
    if recent.pet_id == claim.pet_id and recent.diagnosis == claim.diagnosis:
        flag("DUPLICATE: Same pet/diagnosis within 24 hours")
    if recent.claim_amount == claim.claim_amount:
        flag("DUPLICATE: Same amount submitted recently")
```

### 2. Velocity Checks (Bronze Layer)

**Why**: Abnormal claim frequency indicates fraud or policy abuse

| Pattern | Threshold | Risk Level |
|---------|-----------|------------|
| Customer claims/month | > 5 | HIGH |
| Pet claims/month | > 3 | HIGH |
| Customer claims/week | > 2 | MEDIUM |
| Provider claims (vs avg) | > 2x average | MEDIUM |

**Implementation**:
```python
# Get customer's claim count in last 30 days
customer_claims_30d = get_claim_count(customer_id, days=30)
if customer_claims_30d >= 5:
    flag("VELOCITY: Customer has {n} claims in 30 days")

# Get pet's claim count in last 30 days
pet_claims_30d = get_claim_count(pet_id=pet_id, days=30)
if pet_claims_30d >= 3:
    flag("VELOCITY: Pet has {n} claims in 30 days")
```

### 3. Fraud Patterns (Gold Layer)

#### Pattern 1: Chronic Condition Gaming
**Description**: Customer times policy purchases around known pet conditions

**Indicators**:
- Policy purchased < 30 days before chronic condition claim
- Chronic condition diagnosed within waiting period
- Pattern of policy-claim-cancel cycles

**Example Scenario** (FRAUD-001):
```json
{
  "scenario_id": "FRAUD-001",
  "name": "Chronic Condition Gaming",
  "claim": {
    "diagnosis": "Diabetes mellitus",
    "policy_age_days": 25,
    "is_chronic": true
  },
  "expected_agent": "FLAG for investigation",
  "expected_rule": "APPROVE (rule doesn't see pattern)"
}
```

#### Pattern 2: Provider Collusion
**Description**: Provider and customer conspire to inflate/fabricate claims

**Indicators**:
- Provider's claim amounts consistently 2x+ higher than peers
- Customer always uses same provider
- Unusual procedure combinations
- High frequency of maximum-amount claims

**Example Scenario** (FRAUD-002):
```json
{
  "scenario_id": "FRAUD-002",
  "name": "Provider Collusion",
  "claim": {
    "provider_id": "PROV-SUSPICIOUS",
    "claim_amount": 4500,
    "avg_for_procedure": 2200
  },
  "expected_agent": "FLAG for provider audit",
  "expected_rule": "APPROVE (amount within limits)"
}
```

#### Pattern 3: Staged Timing
**Description**: Claims submitted in suspicious timing patterns

**Indicators**:
- Multiple claims for progressive conditions submitted back-to-back
- Claims submitted just before policy renewal
- Pattern of claims at exact coverage limits

**Example Scenario** (FRAUD-003):
```json
{
  "scenario_id": "FRAUD-003",
  "name": "Staged Timing",
  "claim": {
    "diagnosis": "IVDD Stage 3",
    "days_since_last_stage": 3,
    "normal_progression_days": 30
  },
  "expected_agent": "FLAG for medical review",
  "expected_rule": "APPROVE (valid diagnosis code)"
}
```

### 4. Validation Rules (Silver Layer)

#### VAL-001: Diagnosis-Treatment Mismatch
**Description**: Treatment doesn't match diagnosis

**Check**: Compare diagnosis code with procedure codes
```
Diagnosis: Dental disease (K08.x)
Treatment: Orthopedic surgery
Result: MISMATCH - Flag for review
```

#### VAL-002: Over-Treatment Detection
**Description**: More treatment than diagnosis warrants

**Check**: Compare procedure count/cost with diagnosis severity
```
Diagnosis: Minor ear infection
Treatment: CT scan + MRI + specialist consult
Result: OVER-TREATMENT - Flag for medical review
```

#### VAL-003: Missing Pre-Op Bloodwork
**Description**: Surgery without required pre-operative tests

**Check**: Surgery procedures require bloodwork
```
Procedure: TPLO Surgery
Bloodwork: Not found
Result: INCOMPLETE - Request bloodwork documentation
```

#### VAL-004: Expired Provider License
**Description**: Provider license not valid at service date

**Check**: Verify license expiration vs service date
```
Provider: Dr. Smith
License Expiry: 2024-01-15
Service Date: 2024-12-15
Result: INVALID - Provider license expired
```

#### VAL-005: Controlled Substance Without DEA
**Description**: Controlled medications prescribed without DEA number

**Check**: Verify DEA registration for controlled substances
```
Medication: Gabapentin (Schedule V)
Provider DEA: Not registered
Result: INVALID - DEA required for controlled substances
```

## Customer Context the Agent Should Have

### Historical Claims Data
```python
# Agent should retrieve:
{
  "customer_id": "CUST-123",
  "total_claims_lifetime": 12,
  "total_claims_30d": 3,
  "total_claims_7d": 1,
  "total_amount_lifetime": 15000,
  "claims_by_pet": {
    "PET-001": 8,
    "PET-002": 4
  },
  "claims_by_diagnosis": {
    "skin_allergy": 4,
    "dental": 3,
    "injury": 5
  },
  "favorite_provider": "PROV-456",
  "avg_claim_amount": 1250,
  "fraud_flags_history": []
}
```

### Chat History (if available)
```python
# Agent should consider recent conversations:
{
  "recent_chats": [
    {
      "date": "2024-01-10",
      "topic": "Coverage question about dental",
      "sentiment": "neutral"
    },
    {
      "date": "2024-01-09",
      "topic": "Complaint about claim denial",
      "sentiment": "negative"
    }
  ]
}
```

### Behavioral Patterns
```python
# Agent should identify:
{
  "claim_timing_pattern": "end_of_month",  # Always files at month end
  "document_quality": "always_complete",
  "response_to_requests": "quick",
  "dispute_rate": 0.1  # 10% of claims disputed
}
```

## Decision Thresholds

| Fraud Score | Risk Level | Decision |
|-------------|------------|----------|
| 0-24% | LOW | AUTO_APPROVE (if amount ≤ $500, in-network) |
| 25-49% | MEDIUM | STANDARD_REVIEW |
| 50-74% | HIGH | MANUAL_REVIEW |
| 75-100% | CRITICAL | INVESTIGATION |

## Test Scenarios Summary

### Valid Scenarios (23)
SCN-001 to SCN-023: Legitimate claims covering all categories
- Toxicity, Surgery, Chronic illness, Emergency, Wellness, etc.

### Fraud Scenarios (3)
- FRAUD-001: Chronic Condition Gaming
- FRAUD-002: Provider Collusion  
- FRAUD-003: Staged Timing

### Validation Scenarios (5)
- VAL-001: Diagnosis-Treatment Mismatch
- VAL-002: Over-Treatment Detection
- VAL-003: Missing Pre-Op Bloodwork
- VAL-004: Expired Provider License
- VAL-005: Controlled Substance Without DEA

## Implementation Checklist

### Bronze Agent Enhancements
- [ ] Fetch customer claim history before validation
- [ ] Check for duplicates in last 24 hours
- [ ] Check velocity (claims per month)
- [ ] Flag suspicious patterns early

### Silver Agent Enhancements
- [ ] Verify policy coverage and limits
- [ ] Check diagnosis-treatment consistency
- [ ] Verify provider credentials
- [ ] Check for pre-existing conditions

### Gold Agent Enhancements
- [ ] Run all 3 fraud pattern checks
- [ ] Calculate comprehensive fraud score
- [ ] Include customer context in reasoning
- [ ] Generate detailed audit trail

## API Endpoints for Context

```bash
# Get customer claim history
GET /api/v1/claims/customer/{customer_id}/history

# Get customer chat history (if integrated)
GET /api/v1/chat/customer/{customer_id}/recent

# Check velocity
GET /api/v1/fraud/velocity/{customer_id}

# Check duplicates
POST /api/v1/fraud/duplicate-check
{
  "customer_id": "CUST-123",
  "pet_id": "PET-001",
  "diagnosis": "K91.1",
  "claim_amount": 1500
}

# Run fraud pattern match
POST /api/v1/fraud/pattern-match
{
  "claim_data": {...},
  "customer_history": {...}
}
```
