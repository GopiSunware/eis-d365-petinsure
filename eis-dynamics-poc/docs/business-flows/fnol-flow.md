# Pet Insurance FNOL (First Notice of Loss) Business Flow

## Overview

The Pet Insurance FNOL process captures initial claim information when a pet owner reports a veterinary expense for reimbursement. This POC demonstrates AI-augmented FNOL processing with automated vet invoice extraction, pre-existing condition detection, and intelligent triage.

## Process Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           PET CLAIM FNOL BUSINESS PROCESS                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  PET OWNER              AGENT                 AI SYSTEM               CLAIMS TEAM
     │                     │                       │                        │
     │  1. Report Vet      │                       │                        │
     │     Expense         │                       │                        │
     │ ───────────────────▶│                       │                        │
     │                     │                       │                        │
     │                     │  2. Enter Pet/Claim   │                        │
     │                     │     Details           │                        │
     │                     │ ─────────────────────▶│                        │
     │                     │                       │                        │
     │                     │                       │  3. AI Processing      │
     │                     │                       │  ┌─────────────────┐   │
     │                     │                       │  │ • OCR Invoice   │   │
     │                     │                       │  │ • Extract Diag. │   │
     │                     │                       │  │ • Check Pre-ex  │   │
     │                     │                       │  │ • Fraud Score   │   │
     │                     │                       │  │ • Coverage Chk  │   │
     │                     │                       │  └─────────────────┘   │
     │                     │                       │                        │
     │                     │  4. Review Results    │                        │
     │                     │ ◀─────────────────────│                        │
     │                     │                       │                        │
     │                     │  5. Confirm/Adjust    │                        │
     │                     │ ─────────────────────▶│                        │
     │                     │                       │                        │
     │                     │                       │  6. Create Claim       │
     │                     │                       │ ───────────────────────▶
     │                     │                       │                        │
     │  7. Confirmation    │                       │                        │
     │ ◀───────────────────│                       │                        │
     │    (Claim # + Est)  │                       │                        │
     │                     │                       │                        │
     ▼                     ▼                       ▼                        ▼
```

## Detailed Steps

### Step 1: Pet Owner Reports Claim
**Actor:** Pet Owner
**Channel:** Phone, Web Portal, Mobile App

The pet owner contacts their insurance company to file a claim for a recent vet visit. They typically provide:
- Pet name and policy number
- Date of vet visit
- Reason for visit (illness, accident, wellness)
- Vet clinic information
- Vet invoice/receipt

### Step 2: Agent Portal Entry
**Actor:** Insurance Agent
**System:** WS4 Agent Portal

Agent accesses the Pet Claim FNOL form and enters:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PET CLAIM FNOL FORM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Policy Number:    [PET-IL-2024-00001         ] ← Validated     │
│  Pet:              [Max - Golden Retriever ▼  ]                 │
│                                                                  │
│  Date of Service:  [2024-06-15                ]                 │
│  Vet Clinic:       [Happy Paws Veterinary ▼   ]                │
│                                                                  │
│  Condition Type:   ● Accident  ○ Illness  ○ Wellness  ○ Dental │
│                                                                  │
│  Description:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Max started limping yesterday after playing at the dog     ││
│  │ park. He won't put weight on his back left leg. The vet    ││
│  │ did x-rays and diagnosed a torn CCL (cruciate ligament).   ││
│  │ They're recommending TPLO surgery. Max is 5 years old     ││
│  │ and has been healthy until now.                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Vet Invoice:      [📎 Upload Invoice       ] invoice_max.pdf  │
│                                                                  │
│  Amount Billed:    [$4,500.00                ]                  │
│                                                                  │
│                              [ Submit Claim ]                    │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: AI Processing
**System:** WS2 AI Claims Service

The AI system automatically:

#### 3a. Vet Invoice OCR (Azure Document Intelligence)
```json
{
  "clinic_name": "Happy Paws Veterinary Clinic",
  "clinic_address": "123 Pet Street, Chicago, IL 60601",
  "clinic_phone": "312-555-0100",
  "date_of_service": "2024-06-15",
  "patient_name": "Max",
  "patient_species": "Canine",
  "invoice_items": [
    {"code": "OE001", "description": "Office Exam", "amount": 75.00},
    {"code": "RAD01", "description": "X-Ray - 2 Views", "amount": 250.00},
    {"code": "SED01", "description": "Sedation", "amount": 125.00},
    {"code": "DIAG1", "description": "CCL Diagnosis/Consult", "amount": 150.00},
    {"code": "TPLO1", "description": "TPLO Surgery Estimate", "amount": 3,900.00}
  ],
  "subtotal": 4500.00,
  "tax": 0.00,
  "total": 4500.00
}
```

#### 3b. AI Condition Extraction (GPT-4o)
```json
{
  "pet_name": "Max",
  "species": "dog",
  "breed": "Golden Retriever",
  "pet_age_years": 5,
  "condition_type": "accident",
  "diagnosis": "Torn CCL (Cranial Cruciate Ligament)",
  "diagnosis_code": "ORTH-CCL-001",
  "affected_body_part": "back left leg",
  "symptoms": ["limping", "non-weight-bearing", "pain"],
  "cause": "Acute injury during play",
  "recommended_treatment": "TPLO surgery",
  "diagnostics_performed": ["x-ray"],
  "urgency": "scheduled_surgery",
  "severity": "moderate",
  "confidence_score": 0.94
}
```

#### 3c. Pre-Existing Condition Check
```
Pre-Existing Condition Analysis:
─────────────────────────────────
Policy Effective Date:    2023-01-15
Claim Date of Service:    2024-06-15
Days Since Policy Start:  517 days

Waiting Period Check:
✓ Accident waiting period (0 days):     PASSED
✓ Illness waiting period (14 days):      PASSED
✓ Orthopedic waiting period (6 months):  PASSED

Prior Claims Analysis:
✓ No prior claims for this condition
✓ No related orthopedic claims
✓ No lameness/limping history

Breed Risk Assessment:
⚠ Golden Retrievers have elevated CCL risk
  └ Hereditary component possible
  └ Recommend: Review as acute injury vs degenerative

Pre-Existing Determination: LIKELY NOT PRE-EXISTING
Confidence: 87%
Recommendation: Approve with standard review
```

#### 3d. Fraud Detection
```
Fraud Analysis Results:
─────────────────────────────────
Score:           0.15 (LOW RISK)
Risk Level:      ●●○○○ Low

Indicators Checked:
✓ Policy age            Normal (>12 months)
✓ Claim frequency       Normal (0 claims in past year)
✓ Report timing         Prompt (same day as vet visit)
✓ Invoice authenticity  Verified clinic license
✓ Amount pattern        Reasonable for TPLO surgery
✓ Vet clinic            No fraud flags on provider
✓ Pet identity          Microchip matches policy

Recommendation: Proceed with standard processing
```

### Step 4: Agent Review
**Actor:** Insurance Agent

Agent reviews AI-generated insights:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI ANALYSIS RESULTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pet:             Max (Golden Retriever, 5 yrs, Male)           │
│  Condition:       Torn CCL - Back Left Leg                      │
│  Type:            Accident                                       │
│  Amount Billed:   $4,500.00                                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  FRAUD RISK: LOW (15%)                                      ││
│  │  ✓ No fraud indicators detected                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  PRE-EXISTING CHECK: PASSED                                 ││
│  │  ✓ Waiting periods satisfied                                ││
│  │  ✓ No prior related claims                                  ││
│  │  ⚠ Breed has elevated CCL risk (common in Golden Retrievers)││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Coverage Analysis:                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Plan Type:              Accident + Illness                 ││
│  │  Annual Limit:           $10,000                            ││
│  │  Used YTD:               $0                                 ││
│  │  Remaining:              $10,000                            ││
│  │  Deductible:             $250 (not yet met)                ││
│  │  Reimbursement:          80%                                ││
│  │                                                              ││
│  │  Eligible Amount:        $4,500.00                          ││
│  │  Less Deductible:        -$250.00                           ││
│  │  Reimbursable:           $4,250.00                          ││
│  │  Est. Payout (80%):      $3,400.00                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  AI Confidence: 94%                                              │
│                                                                  │
│  Triage Recommendation:                                          │
│  • Claim over $3,000 - requires adjuster review                 │
│  • Request pre-operative x-rays for file                        │
│  • Verify surgery completion before payment                     │
│                                                                  │
│         [ Accept Recommendations ]  [ Modify ]  [ Escalate ]    │
└─────────────────────────────────────────────────────────────────┘
```

### Step 5: Claim Creation
**System:** WS2 AI Claims Service → WS3 Integration Layer

Claim is created and synchronized:

```
Pet Claim Created Successfully
─────────────────────────────────
Claim Number:    CLM-PET-2024-00001
Status:          Under Review
Pet:             Max (Golden Retriever)
Policy:          PET-IL-2024-00001
Owner:           John Smith

Claim Details:
  Condition:         Torn CCL
  Type:              Accident
  Date of Service:   2024-06-15
  Vet Clinic:        Happy Paws Veterinary

Financial:
  Amount Billed:     $4,500.00
  Est. Payout:       $3,400.00

Assessment:
  Fraud Score:       15% (Low)
  Pre-Existing:      No
  Coverage:          Eligible

Next Steps:
  1. Claim assigned to adjuster queue
  2. Await surgery completion
  3. Request post-op invoice for payment
```

### Step 6: Dataverse Sync
**System:** WS3 Integration Layer

Claim is synced to Dynamics 365:
- Created in `eis_claim` entity
- Linked to `eis_pet` (Max)
- Linked to `eis_policy` record
- Linked to `eis_petowner` contact
- Linked to `eis_vetprovider` (Happy Paws)
- Activity created for follow-up

### Step 7: Confirmation
**Actor:** Pet Owner

Pet owner receives confirmation via email:

```
Subject: Pet Claim Received - CLM-PET-2024-00001

Dear John,

We have received your claim for Max's veterinary visit on June 15, 2024.

Claim Details:
  Claim Number:     CLM-PET-2024-00001
  Pet:              Max
  Condition:        CCL Injury
  Amount Claimed:   $4,500.00
  Est. Reimbursement: $3,400.00*

Status: Under Review

*Estimated amount after $250 deductible and 80% reimbursement

What Happens Next:
1. Our team will review your claim within 3-5 business days
2. If surgery proceeds, please submit the final invoice
3. Payment will be issued via direct deposit

Track your claim at: petinsurance.example.com/claims/CLM-PET-2024-00001

Questions? Call us at 1-800-PET-HELP or email claims@petinsurance.example.com

Thank you for insuring Max with us!

PetProtect Insurance
```

## Exception Handling

### Pre-Existing Condition Detected

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  POTENTIAL PRE-EXISTING CONDITION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Claim:    CLM-PET-2024-00002                                   │
│  Pet:      Bella (French Bulldog, 3 yrs)                        │
│  Condition: Intervertebral Disc Disease (IVDD)                  │
│                                                                  │
│  ⚠ Pre-Existing Indicators:                                     │
│  ─────────────────────────────────────────────────              │
│  ✗ Policy effective only 45 days ago                            │
│  ✗ IVDD is hereditary in French Bulldogs                        │
│  ✗ Vet notes mention "chronic back issues"                      │
│                                                                  │
│  AI Determination: LIKELY PRE-EXISTING (78% confidence)         │
│                                                                  │
│  REQUIRED ACTION:                                                │
│  Request full medical history from pet owner and previous       │
│  veterinarian before claim can be processed.                    │
│                                                                  │
│  Documents Needed:                                               │
│  □ Vet records from past 12 months                              │
│  □ Adoption/purchase medical records                            │
│  □ Any prior imaging (x-rays, MRI)                              │
│                                                                  │
│         [ Request Records ]  [ Deny - Pre-Existing ]            │
└─────────────────────────────────────────────────────────────────┘
```

### Waiting Period Violation

```
┌─────────────────────────────────────────────────────────────────┐
│  ❌  WAITING PERIOD NOT MET                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Claim:    CLM-PET-2024-00003                                   │
│  Pet:      Luna (Labrador, 2 yrs)                               │
│  Condition: Ear Infection                                        │
│  Type:     Illness                                               │
│                                                                  │
│  Policy Effective:   2024-06-01                                 │
│  Date of Service:    2024-06-10                                 │
│  Days Since Start:   9 days                                     │
│                                                                  │
│  ✗ Illness waiting period: 14 days                              │
│    (Claim is 5 days too early)                                  │
│                                                                  │
│  This claim is NOT eligible for coverage.                       │
│                                                                  │
│  Alternative Actions:                                            │
│  • Explain waiting period to pet owner                          │
│  • Note: Future ear infections will be covered after 06/15      │
│                                                                  │
│         [ Deny - Waiting Period ]  [ Override (Manager) ]       │
└─────────────────────────────────────────────────────────────────┘
```

### High Fraud Risk

```
┌─────────────────────────────────────────────────────────────────┐
│  🚨  HIGH FRAUD RISK DETECTED                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Fraud Score: 78% (HIGH RISK)                                   │
│                                                                  │
│  Indicators Triggered:                                           │
│  ⚠ Invoice appears altered (metadata inconsistency)             │
│  ⚠ Same pet claimed at 2 different insurers this month          │
│  ⚠ Vet clinic flagged for suspicious billing                    │
│  ⚠ Claim amount significantly higher than breed average         │
│                                                                  │
│  Recommended Actions:                                            │
│  1. Contact vet clinic directly to verify invoice               │
│  2. Request original itemized receipt                           │
│  3. Cross-reference with industry fraud database                │
│                                                                  │
│  REQUIRED ACTION:                                                │
│  This claim has been flagged for Special Investigations Unit    │
│  (SIU) review before processing can continue.                   │
│                                                                  │
│         [ Escalate to SIU ]  [ Request Additional Info ]        │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| FNOL Submission to Claim Created | < 30 seconds | 12 seconds |
| AI Extraction Accuracy (vet invoice) | ≥ 90% | 94% |
| Pre-Existing Detection Accuracy | ≥ 85% | 88% |
| Fraud Detection True Positive | ≥ 80% | 82% |
| Agent Time per FNOL | < 5 minutes | 3 minutes |
| Dataverse Sync Latency | < 5 minutes | 30 seconds |

## Integration Points

| System | Integration Type | Data Exchanged |
|--------|------------------|----------------|
| EIS Suite | Webhook | Policy/pet validation |
| Azure OpenAI | REST API | Condition extraction, fraud analysis |
| Azure Document Intelligence | REST API | Vet invoice OCR |
| Dataverse | Web API | Pet, claim, policy entities |
| Service Bus | Queue | Sync messages, fraud alerts |
| Blob Storage | REST | Vet invoices, medical records |
