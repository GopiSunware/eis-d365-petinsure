# Claims Decision Logic

This document explains how the pipeline processes claims and makes decisions.

---

## Overview

Claims flow through a **3-layer medallion architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLAIM SUBMITTED                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BRONZE LAYER - Validation & Quality Assessment                 │
│  • Validates required fields                                    │
│  • Checks data types and formats                                │
│  • Calculates QUALITY SCORE (0-100)                             │
│  • Output: ACCEPT / REJECT / QUARANTINE                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                    (if ACCEPT) │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SILVER LAYER - Enrichment & Coverage Calculation               │
│  • Applies deductible ($250)                                    │
│  • Calculates reimbursement (80% rate)                          │
│  • Applies network penalties (20% for out-of-network)           │
│  • Sets processing priority                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GOLD LAYER - Risk Assessment & Final Decision                  │
│  • Calculates RISK SCORE (0-100+)                               │
│  • Determines risk level (LOW/MEDIUM/HIGH)                      │
│  • Makes final decision                                         │
│  • Output: AUTO_APPROVE / STANDARD_REVIEW / MANUAL_REVIEW       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quality Score (Bronze Layer)

**What is it?**
A score from 0-100 that measures the completeness and validity of claim data. Higher score = better quality data.

**How it's calculated:**

```
QUALITY SCORE = Base Score (100) - Penalties + Bonuses

PENALTIES:
┌─────────────────────────────────┬─────────┐
│ Issue Type                      │ Points  │
├─────────────────────────────────┼─────────┤
│ Missing required field          │ -20     │
│ Invalid data type               │ -20     │
│ Warning (e.g., amount mismatch) │ -5      │
└─────────────────────────────────┴─────────┘

BONUSES (for optional fields present):
┌─────────────────────────────────┬─────────┐
│ Optional Field                  │ Points  │
├─────────────────────────────────┼─────────┤
│ provider_name                   │ +5      │
│ treatment_notes                 │ +5      │
│ line_items                      │ +5      │
└─────────────────────────────────┴─────────┘

Final score capped between 0 and 100.
```

**Required Fields:**
- claim_id
- claim_type
- claim_amount
- service_date
- diagnosis_code

**Bronze Decision based on Quality Score:**

| Quality Score | Decision | Meaning |
|---------------|----------|---------|
| Any with issues | REJECT | Missing required fields, invalid data |
| < 60 | QUARANTINE | Poor quality, needs manual data cleanup |
| ≥ 60 | ACCEPT | Passes to Silver layer |

**Example:**
```
Claim with:
- All required fields present: Base = 100
- Amount > $50,000 warning: -5
- Has provider_name: +5
- Has treatment_notes: +5
- Has line_items: +5

Quality Score = 100 - 5 + 5 + 5 + 5 = 110 → capped at 100
Decision: ACCEPT
```

---

## Risk Score (Gold Layer)

**What is it?**
A score that measures fraud/risk indicators. **Higher score = MORE RISK** (bad).

**How it's calculated:**

```
RISK SCORE = Sum of all applicable risk factors

RISK FACTORS (cumulative - all applicable factors add up):
┌─────────────────────────────────┬─────────┬─────────────────────────────┐
│ Condition                       │ Points  │ Reason                      │
├─────────────────────────────────┼─────────┼─────────────────────────────┤
│ Claim amount > $10,000          │ +30     │ High value = higher risk    │
│ Claim amount > $5,000 (≤$10k)   │ +15     │ Elevated amount             │
│ Out-of-network provider         │ +20     │ Less oversight, fraud risk  │
│ Round dollar amount*            │ +10     │ Potential fabrication       │
│ Emergency claim                 │ +5      │ Less documentation typical  │
│ Quality score < 70              │ +15     │ Poor data quality           │
└─────────────────────────────────┴─────────┴─────────────────────────────┘

* Round amounts: $1,000, $2,000, $5,000, $10,000 (suspicious patterns)
```

**Risk Level Determination:**

| Risk Score | Risk Level | Color |
|------------|------------|-------|
| ≥ 50 | HIGH | Red |
| 25 - 49 | MEDIUM | Yellow |
| < 25 | LOW | Green |

**Examples:**

```
Example 1: Low Risk
- Claim: $450, in-network, routine wellness
- Risk factors: None
- Risk Score: 0 → LOW

Example 2: Medium Risk
- Claim: $3,000, in-network, accident
- Risk factors: None (under $5k threshold)
- Risk Score: 0 → LOW
- But claim > $500 → STANDARD_REVIEW (see decision logic)

Example 3: High Risk
- Claim: $8,500, out-of-network, emergency
- Risk factors:
  • > $5,000: +15
  • Out-of-network: +20
  • Emergency: +5
- Risk Score: 40 → MEDIUM

Example 4: Very High Risk
- Claim: $10,000 (round), out-of-network, quality score 65
- Risk factors:
  • = $10,000: +30 (high value)
  • Round amount: +10
  • Out-of-network: +20
  • Quality < 70: +15
- Risk Score: 75 → HIGH → MANUAL_REVIEW
```

---

## Final Decision Logic (Gold Layer)

The Gold layer makes the final decision based on risk level and claim characteristics:

```
┌─────────────────────────────────────────────────────────────────┐
│                     DECISION FLOWCHART                          │
└─────────────────────────────────────────────────────────────────┘

                         Risk Level?
                             │
            ┌────────────────┼────────────────┐
            │                │                │
           HIGH           MEDIUM             LOW
            │                │                │
            ▼                ▼                ▼
      MANUAL_REVIEW    STANDARD_REVIEW    Amount ≤ $500
                                          AND in-network?
                                               │
                                         ┌─────┴─────┐
                                        YES          NO
                                         │           │
                                         ▼           ▼
                                   AUTO_APPROVE  STANDARD_REVIEW
```

**Decision Definitions:**

| Decision | Description | Next Steps |
|----------|-------------|------------|
| **AUTO_APPROVE** | Automatically approved for payment | Proceeds to payment processing |
| **STANDARD_REVIEW** | Normal review queue | Claims adjuster reviews within SLA |
| **MANUAL_REVIEW** | Flagged for senior review | Requires supervisor/fraud team review |
| **REJECT** | Claim rejected at Bronze | Customer notified, can resubmit with corrections |
| **QUARANTINE** | Data quality issues | Needs data cleanup before processing |

**Decision Rules Summary:**

| Risk Level | Claim Amount | Network | Decision |
|------------|--------------|---------|----------|
| HIGH | Any | Any | MANUAL_REVIEW |
| MEDIUM | Any | Any | STANDARD_REVIEW |
| LOW | ≤ $500 | In-network | AUTO_APPROVE |
| LOW | > $500 | Any | STANDARD_REVIEW |
| LOW | ≤ $500 | Out-of-network | STANDARD_REVIEW |

---

## Reimbursement Calculation (Silver Layer)

```
REIMBURSEMENT = (Claim Amount - Deductible) × Reimbursement Rate × Network Factor

Where:
- Deductible = $250 (fixed)
- Reimbursement Rate = 80%
- Network Factor = 100% (in-network) or 80% (out-of-network)

FORMULA:
In-Network:  (Amount - $250) × 0.80
Out-of-Network: (Amount - $250) × 0.80 × 0.80 = (Amount - $250) × 0.64
```

**Examples:**

```
Example 1: $1,000 in-network claim
Reimbursement = ($1,000 - $250) × 0.80 = $600

Example 2: $1,000 out-of-network claim
Reimbursement = ($1,000 - $250) × 0.80 × 0.80 = $480
Network penalty = $600 - $480 = $120

Example 3: $500 in-network claim
Reimbursement = ($500 - $250) × 0.80 = $200
```

---

## AI Summary Generation

**What it does:**
After a pipeline completes, users can generate an AI-powered executive summary of the claim processing.

**API Endpoint:**
```
POST /api/v1/pipeline/run/{run_id}/summary
```

**What the AI receives:**
The AI (Claude or GPT-4) receives a structured context containing:
- Claim details (amount, type, pet name, provider)
- Treatment notes
- Bronze layer results (quality score, validation issues)
- Silver layer results (reimbursement amount, priority)
- Gold layer results (decision, risk level, confidence, insights)
- Processing time

**What the AI generates:**
A 3-4 sentence executive summary that:
1. Describes what the claim was for
2. Explains the key decision and reasoning
3. Highlights notable risks or insights
4. States recommended next action

**Example AI Summary:**
> "This $1,355 emergency claim for Buddy's chocolate toxicity treatment has been flagged for MANUAL_REVIEW due to elevated risk factors. The out-of-network emergency visit and claim amount contributed to a medium risk score of 40. Estimated reimbursement is $707.20 after the $250 deductible and 80% coverage rate. Recommend verifying the emergency circumstances and provider credentials before approval."

**Configuration:**
- AI Provider: Configured via `AI_PROVIDER` env variable (claude/openai)
- Models: Claude Sonnet 3.5 or GPT-4o
- Max tokens: 300 (keeps summary concise)
- Fallback: If AI fails, returns basic factual summary

---

## Code vs Agent Processing

The system supports two processing modes:

| Aspect | Code-Driven | Agent-Driven |
|--------|-------------|--------------|
| **Speed** | < 1ms | 30-120 seconds |
| **Logic** | Deterministic rules | LLM reasoning |
| **Decisions** | Fixed thresholds | Contextual analysis |
| **Reasoning** | None (just results) | Full explanation |
| **Insights** | None | AI-generated |
| **Cost** | Free | API costs |
| **Consistency** | 100% reproducible | May vary slightly |

**When to use each:**
- **Code-Driven**: High volume, simple claims, cost-sensitive
- **Agent-Driven**: Complex claims, edge cases, audit requirements

---

## Agent-Driven LLM API Calls

Yes, agent-driven processing calls LLM APIs (Claude or GPT-4) for each agent. Here's what each agent sends/receives:

### Router Agent (NO LLM Call)

The Router Agent does **NOT** call an LLM. It uses deterministic rules to assess complexity.

```
INPUT: Raw claim data
LOGIC: Rule-based complexity assessment
OUTPUT: { complexity, processing_path, factors, reasoning }
```

**Complexity Factors (rule-based):**
- Claim amount: <$1k (simple), $1k-$10k (medium), >$10k (complex)
- Claim type: wellness/routine (simple), accident (medium), emergency/surgery (complex)
- Diagnosis code: standard (simple), oncology codes (complex)
- Data completeness: all fields (simple), missing fields (complex)

---

### Bronze Agent (LLM Call)

**LLM Used:** Claude Sonnet 3.5 or GPT-4o (configurable)

**System Prompt:**
```
You are a Bronze Layer Data Agent for pet insurance claims processing.

Your role is to validate, clean, and assess incoming claim data.

Responsibilities:
1. VALIDATE: Check required fields and data types
2. DETECT ANOMALIES: Look for suspicious patterns
3. CLEAN: Normalize and fix data issues
4. ASSESS QUALITY: Rate overall data quality (0-100)
5. DECIDE: ACCEPT / QUARANTINE / REJECT
```

**Input Message to LLM:**
```
Please process the following pet insurance claim:

Claim ID: CLM-SCN-001-ABC123
Claim Data:
{
  "claim_id": "CLM-SCN-001-ABC123",
  "policy_id": "POL-DEMO-001",
  "claim_amount": 1355.00,
  "claim_type": "Accident",
  "diagnosis_code": "T65.8",
  "diagnosis_description": "Chocolate toxicity emergency",
  "treatment_notes": "Emergency induced vomiting, activated charcoal...",
  "provider_name": "Emergency Vet Clinic",
  "is_emergency": true,
  "line_items": [...]
}

Steps:
1. validate_schema
2. detect_anomalies
3. clean_data
4. assess_quality
5. write_bronze with your decision
```

**Tools Available:**
- `validate_schema` - Check required fields
- `detect_anomalies` - Find suspicious patterns
- `clean_data` - Normalize values
- `assess_quality` - Calculate quality score
- `write_bronze` - Save results
- `get_historical_claims` - Check claim history

**Output (extracted from LLM response):**
```json
{
  "decision": "ACCEPT",
  "confidence": 0.9,
  "quality_score": 85,
  "validation_issues": [],
  "warnings": ["Emergency claim - expedited processing"],
  "reasoning": "All required fields present, data quality is good...",
  "cleaned_data": { ... }
}
```

---

### Silver Agent (LLM Call)

**LLM Used:** Claude Sonnet 3.5 or GPT-4o

**System Prompt:**
```
You are a Silver Layer Enrichment Agent for pet insurance claims.

Your role is to enrich, normalize, and transform validated Bronze data.

Responsibilities:
1. ENRICH: Pull policy, customer, pet, provider data
2. NORMALIZE: Standardize codes and values
3. VALIDATE BUSINESS RULES: Check coverage, waiting periods, limits
4. CALCULATE SCORES: Assess enriched data quality

Context to Consider:
- Is this a repeat customer?
- Is the provider in-network?
- Does amount match typical costs for this diagnosis?
- Any coverage exclusions?
```

**Input Message to LLM:**
```
Please enrich and validate the following Bronze layer claim data:

Claim ID: CLM-SCN-001-ABC123
Bronze Data:
{
  "decision": "ACCEPT",
  "quality_score": 85,
  "cleaned_data": { ... }
}

Steps:
1. enrich_claim - Get policy, customer, pet, provider data
2. get_customer_claim_history - Check past claims
3. normalize_values - Standardize diagnosis codes
4. apply_business_rules - Validate coverage
5. calculate_quality_scores - Assess enrichment quality
6. write_silver - Save enriched record
```

**Tools Available:**
- `enrich_claim` - Fetch related data
- `get_customer_claim_history` - Past claims lookup
- `normalize_values` - Standardize codes
- `apply_business_rules` - Coverage validation
- `calculate_quality_scores` - Quality metrics
- `write_silver` - Save results

**Output (extracted from LLM response):**
```json
{
  "is_covered": true,
  "expected_reimbursement": 884.00,
  "coverage_percentage": 80,
  "deductible_applied": 250,
  "processing_priority": "HIGH",
  "enrichment_data": {
    "policy": { "type": "Comprehensive", "annual_limit": 15000 },
    "customer": { "tenure_months": 24, "claims_ytd": 2 },
    "provider": { "in_network": false, "fraud_rate": 0.02 }
  },
  "quality_score": 0.88,
  "enrichment_notes": "Customer is in good standing..."
}
```

---

### Gold Agent (LLM Call)

**LLM Used:** Claude Sonnet 3.5 or GPT-4o

**System Prompt:**
```
You are a Gold Layer Analytics Agent for pet insurance claims.

Your role is to generate insights, assess risk, and make final decisions.

Responsibilities:
1. ASSESS RISK: Calculate fraud probability, identify risk indicators
2. GENERATE INSIGHTS: Extract business intelligence
3. CALCULATE KPIs: Compute business metrics
4. CREATE ALERTS: Flag important items
5. UPDATE CUSTOMER 360: Maintain customer profiles
6. MAKE FINAL DECISION:
   - AUTO_APPROVE: Low risk, proceed automatically
   - STANDARD_REVIEW: Normal review process
   - MANUAL_REVIEW: Requires adjuster attention
   - INVESTIGATION: Escalate to fraud unit

Think like a business analyst:
- What does this claim tell us about the customer?
- Are there concerning patterns?
- What actions should the business take?
```

**Input Message to LLM:**
```
Please analyze the following Silver layer claim data:

Claim ID: CLM-SCN-001-ABC123
Silver Data:
{
  "is_covered": true,
  "expected_reimbursement": 884.00,
  "enrichment_data": { ... },
  "bronze_reference": { ... }
}

Total Processing Time So Far: 45000ms

Steps:
1. assess_risk - Calculate fraud probability
2. generate_insights - Extract business intelligence
3. calculate_kpi_metrics - Compute metrics
4. create_alerts - Flag important items
5. update_customer_360 - Update customer profile
6. write_gold - Save with final decision
```

**Tools Available:**
- `assess_risk` - Fraud/risk scoring
- `generate_insights` - Business intelligence
- `calculate_kpi_metrics` - KPI computation
- `create_alerts` - Alert generation
- `update_customer_360` - Profile updates
- `write_gold` - Save final results
- `update_kpi_aggregates` - Update dashboards

**Output (extracted from LLM response):**
```json
{
  "final_decision": "STANDARD_REVIEW",
  "confidence": 0.85,
  "fraud_score": 0.25,
  "risk_level": "MEDIUM",
  "insights": [
    "Customer has 2 claims this year, within normal range",
    "Out-of-network emergency - verify provider credentials",
    "Chocolate toxicity is common in dogs - legitimate diagnosis"
  ],
  "alerts": [
    {
      "type": "OUT_OF_NETWORK",
      "message": "Emergency claim at non-network provider",
      "action_required": false
    }
  ],
  "kpi_metrics": {
    "claim_complexity": "medium",
    "processing_efficiency": 0.92
  },
  "reasoning": "This emergency claim for chocolate toxicity appears legitimate. The customer is in good standing with 24 months tenure. However, the out-of-network provider and emergency nature warrant standard review before approval. Estimated payout of $884 after $250 deductible and 80% coverage..."
}
```

---

## LLM API Call Summary

| Agent | LLM Call? | Model | Max Tokens | Temperature |
|-------|-----------|-------|------------|-------------|
| Router | **No** | N/A | N/A | N/A |
| Bronze | **Yes** | Claude Sonnet / GPT-4o | 4096 | 0.1 |
| Silver | **Yes** | Claude Sonnet / GPT-4o | 4096 | 0.1 |
| Gold | **Yes** | Claude Sonnet / GPT-4o | 4096 | 0.1 |
| Summary | **Yes** | Claude Sonnet / GPT-4o | 300 | default |

**Total LLM Calls per Pipeline Run:** 3-4 (Bronze, Silver, Gold, + optional Summary)

**Estimated API Cost per Run:**
- Claude: ~$0.03-0.10 depending on claim complexity
- GPT-4o: ~$0.05-0.15 depending on claim complexity

---

## File References

| Component | File |
|-----------|------|
| Code Processor | `src/ws6_agent_pipeline/app/services/code_processor.py` |
| Pipeline Router | `src/ws6_agent_pipeline/app/routers/pipeline.py` |
| Bronze Agent | `src/ws6_agent_pipeline/app/agents/bronze_agent.py` |
| Silver Agent | `src/ws6_agent_pipeline/app/agents/silver_agent.py` |
| Gold Agent | `src/ws6_agent_pipeline/app/agents/gold_agent.py` |

---

*Last updated: December 30, 2024*
