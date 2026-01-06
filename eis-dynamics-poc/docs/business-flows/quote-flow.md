# Pet Insurance Quote Generation Business Flow

## Overview

The pet insurance quote generation process calculates premiums based on pet characteristics (species, breed, age), owner location, and coverage selections. This POC demonstrates a complete rating engine with breed-based risk factors and comparison against EIS mock rates.

## Process Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           PET QUOTE GENERATION PROCESS                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  PET OWNER              AGENT                  RATING ENGINE             EIS COMPARISON
     │                     │                          │                        │
     │  1. Request Quote   │                          │                        │
     │ ───────────────────▶│                          │                        │
     │                     │                          │                        │
     │                     │  2. Enter Pet Info       │                        │
     │                     │ ────────────────────────▶│                        │
     │                     │                          │                        │
     │                     │                          │  3. Calculate          │
     │                     │                          │  ┌───────────────────┐ │
     │                     │                          │  │ • Species Rate    │ │
     │                     │                          │  │ • Breed Factor    │ │
     │                     │                          │  │ • Age Curve       │ │
     │                     │                          │  │ • Location Factor │ │
     │                     │                          │  │ • Coverage Calc   │ │
     │                     │                          │  │ • Discounts       │ │
     │                     │                          │  └───────────────────┘ │
     │                     │                          │                        │
     │                     │                          │  4. Compare Rate       │
     │                     │                          │ ───────────────────────▶
     │                     │                          │                        │
     │                     │                          │  5. Parity Check       │
     │                     │                          │ ◀───────────────────────
     │                     │                          │                        │
     │                     │  6. Quote Result         │                        │
     │                     │ ◀────────────────────────│                        │
     │                     │                          │                        │
     │  7. Present Quote   │                          │                        │
     │ ◀───────────────────│                          │                        │
     │                     │                          │                        │
     ▼                     ▼                          ▼                        ▼
```

## Quote Wizard Steps

### Step 1: Pet Owner Information

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUOTE WIZARD - STEP 1/4                       │
│                      Pet Owner Information                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Contact Information                                             │
│  ─────────────────────────────────────────────                  │
│  First Name:       [John                     ]                  │
│  Last Name:        [Smith                    ]                  │
│  Email:            [john.smith@email.com     ]                  │
│  Phone:            [312-555-0100             ]                  │
│                                                                  │
│  Address                                                         │
│  ─────────────────────────────────────────────                  │
│  Street:           [456 Oak Avenue           ]                  │
│  City:             [Chicago                  ]                  │
│  State:            [Illinois            ▼    ]                  │
│  ZIP Code:         [60601                    ]                  │
│                                                                  │
│                           [ Previous ]  [ Next: Pet Info → ]    │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Pet Information

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUOTE WIZARD - STEP 2/4                       │
│                        Pet Information                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pet Details                                                     │
│  ─────────────────────────────────────────────                  │
│  Pet Name:         [Max                      ]                  │
│  Species:          ● Dog  ○ Cat  ○ Bird  ○ Other               │
│  Breed:            [Golden Retriever    ▼    ]                  │
│  Date of Birth:    [03/15/2019               ]  Age: 5 yrs     │
│  Gender:           ● Male  ○ Female                             │
│                                                                  │
│  Health Information                                              │
│  ─────────────────────────────────────────────                  │
│  ☑ Spayed/Neutered                                              │
│  ☑ Microchipped                                                  │
│  Microchip ID:     [985121012345678          ] (optional)       │
│                                                                  │
│  Pre-Existing Conditions                                         │
│  ─────────────────────────────────────────────                  │
│  ☐ Has known pre-existing conditions                            │
│     If yes, describe: [                      ]                  │
│                                                                  │
│  [ + Add Another Pet ]                                           │
│                                                                  │
│                           [ ← Previous ]  [ Next: Coverage → ]  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Coverage Selection

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUOTE WIZARD - STEP 3/4                       │
│                      Coverage Selection                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Plan Type                                                       │
│  ─────────────────────────────────────────────                  │
│  ○ Accident Only          $15-25/mo                             │
│    Covers injuries from accidents only                          │
│                                                                  │
│  ● Accident + Illness     $35-55/mo                             │
│    Covers accidents AND illnesses (recommended)                 │
│                                                                  │
│  ○ Comprehensive          $50-80/mo                             │
│    Accident + Illness + Wellness                                │
│                                                                  │
│  Annual Limit                                                    │
│  ─────────────────────────────────────────────                  │
│  ○ $5,000/year                                                   │
│  ● $10,000/year  (most popular)                                 │
│  ○ $15,000/year                                                  │
│  ○ Unlimited                                                     │
│                                                                  │
│  Deductible                                                      │
│  ─────────────────────────────────────────────                  │
│  ○ $100    (higher premium)                                     │
│  ● $250    (balanced)                                           │
│  ○ $500    (lower premium)                                      │
│  ○ $750                                                          │
│                                                                  │
│  Reimbursement Percentage                                        │
│  ─────────────────────────────────────────────                  │
│  ○ 70%     (lower premium)                                      │
│  ● 80%     (most popular)                                       │
│  ○ 90%     (higher premium)                                     │
│                                                                  │
│  Optional Add-Ons                                                │
│  ─────────────────────────────────────────────                  │
│  ☐ Wellness Add-On        +$15/mo                               │
│     Covers: Vaccines, checkups, dental cleaning                 │
│                                                                  │
│  ☐ Dental Add-On          +$8/mo                                │
│     Covers: Dental illness, extractions, periodontal            │
│                                                                  │
│  ☐ Behavioral Add-On      +$5/mo                                │
│     Covers: Behavioral therapy, training for anxiety            │
│                                                                  │
│                           [ ← Previous ]  [ Next: Review → ]    │
└─────────────────────────────────────────────────────────────────┘
```

### Step 4: Discounts & Review

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUOTE WIZARD - STEP 4/4                       │
│                      Discounts & Review                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Available Discounts                                             │
│  ─────────────────────────────────────────────                  │
│  ☑ Spayed/Neutered (5%)                                         │
│  ☑ Microchipped (3%)                                            │
│  ☐ Multi-Pet (10% each additional pet)                          │
│  ☐ Annual Payment (5%)                                          │
│  ☐ Shelter/Rescue Pet (5%)                                      │
│  ☐ Military/Veteran (10%)                                       │
│                                                                  │
│  Policy Details                                                  │
│  ─────────────────────────────────────────────                  │
│  Effective Date:    [07/01/2024              ]                  │
│  Payment Frequency: ● Monthly  ○ Annual                         │
│                                                                  │
│  Quote Summary                                                   │
│  ─────────────────────────────────────────────                  │
│  Pet:               Max (Golden Retriever, 5 yrs)               │
│  Plan:              Accident + Illness                          │
│  Annual Limit:      $10,000                                     │
│  Deductible:        $250                                        │
│  Reimbursement:     80%                                         │
│                                                                  │
│                           [ ← Previous ]  [ Calculate Quote ]   │
└─────────────────────────────────────────────────────────────────┘
```

## Premium Calculation

### Calculation Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PET INSURANCE PREMIUM CALCULATION                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  BASE RATE (Golden Retriever - Large Dog)                       $420.00/year         │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  SPECIES/BREED FACTORS                                                                 │
  │                                                                                        │
  │    Species (Dog):                  1.00 (base)                                        │
  │    Breed Risk (Golden Retriever):  1.15 (elevated due to hereditary conditions)      │
  │    Size Category (Large):          1.08                                               │
  │                                    ─────────────────                                  │
  │    Combined Breed Factor:          1.24                                               │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  AGE FACTOR                                                                            │
  │                                                                                        │
  │    Age 5 years falls in tier 4-7:  1.20                                              │
  │                                                                                        │
  │    Age Curve Reference:                                                               │
  │    ┌────────────────────────────────────────┐                                        │
  │    │  0-1 years:   0.85  (puppy discount)  │                                        │
  │    │  1-4 years:   1.00  (standard)        │                                        │
  │    │  4-7 years:   1.20  ◀ Current        │                                        │
  │    │  7-10 years:  1.50  (senior)          │                                        │
  │    │  10+ years:   2.00  (geriatric)       │                                        │
  │    └────────────────────────────────────────┘                                        │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  LOCATION FACTOR                                                                       │
  │                                                                                        │
  │    State (Illinois):               1.05                                               │
  │    ZIP (60601 - Chicago):          1.10 (urban area = higher vet costs)              │
  │                                    ─────────────────                                  │
  │    Combined Location Factor:       1.16                                               │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  COVERAGE CHARGES                                                                      │
  │                                                                                        │
  │    Base Premium after Factors:                                                        │
  │    $420 × 1.24 × 1.20 × 1.16 =                                $724.76                │
  │                                                                                        │
  │    Plan Adjustments:                                                                  │
  │    Accident + Illness Plan:                                   × 1.00                 │
  │    $10K Annual Limit:                                         × 1.00                 │
  │    $250 Deductible (credit):                                  - $48.00               │
  │    80% Reimbursement:                                         × 1.00                 │
  │                                    ─────────────────                                  │
  │    Adjusted Premium:                                          $676.76                │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  DISCOUNTS APPLIED                                                                     │
  │                                                                                        │
  │    Spayed/Neutered (5%):                                       -$33.84               │
  │    Microchipped (3%):                                          -$20.30               │
  │                                    ─────────────────                                  │
  │    Total Discounts (8%):                                       -$54.14               │
  └───────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
  ┌───────────────────────────────────────────────────────────────────────────────────────┐
  │  FINAL PREMIUM                                                                         │
  │                                                                                        │
  │    Adjusted Premium:              $676.76                                             │
  │    Discounts:                     -$54.14                                             │
  │    Policy Fee:                     $15.00                                             │
  │                                   ═════════════════                                   │
  │    TOTAL ANNUAL PREMIUM:                                      $637.62                 │
  │    Monthly (if financed):                                      $53.14                 │
  └───────────────────────────────────────────────────────────────────────────────────────┘
```

### Quote Result Display

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              YOUR PET INSURANCE QUOTE                                    │
│                           Quote #: QTE-PET-2024-0001                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Pet: Max (Golden Retriever, 5 years old)                                               │
│                                                                                          │
│                        ┌─────────────────────────────────┐                              │
│                        │                                 │                              │
│                        │      $637.62/year               │                              │
│                        │      $53.14/month               │                              │
│                        │                                 │                              │
│                        └─────────────────────────────────┘                              │
│                                                                                          │
│  ✓ Valid for 30 days                                                                    │
│  ✓ Coverage starts: July 1, 2024                                                        │
│  ✓ 14-day illness waiting period                                                        │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │  COVERAGE SUMMARY                                                                    ││
│  │                                                                                      ││
│  │  Plan Type:              Accident + Illness                                         ││
│  │  Annual Limit:           $10,000                                                    ││
│  │  Deductible:             $250 per year                                              ││
│  │  Reimbursement:          80%                                                        ││
│  │                                                                                      ││
│  │  What's Covered:                                                                     ││
│  │  ✓ Accidents (broken bones, lacerations, ingestion)                                ││
│  │  ✓ Illnesses (infections, cancer, allergies, diabetes)                             ││
│  │  ✓ Hereditary conditions (hip dysplasia, heart disease)                            ││
│  │  ✓ Emergency & specialty care                                                       ││
│  │  ✓ Surgery, hospitalization, medications                                           ││
│  │  ✓ Diagnostic tests (x-rays, bloodwork, MRI)                                       ││
│  │                                                                                      ││
│  │  What's Not Covered:                                                                 ││
│  │  ✗ Pre-existing conditions                                                          ││
│  │  ✗ Routine wellness (vaccines, checkups) - add Wellness option                     ││
│  │  ✗ Cosmetic procedures                                                              ││
│  │  ✗ Breeding-related conditions                                                      ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │  DISCOUNTS EARNED                                              SAVINGS              ││
│  │                                                                                      ││
│  │  ✓ Spayed/Neutered                                             -$33.84            ││
│  │  ✓ Microchipped                                                -$20.30            ││
│  │                                                                ─────────            ││
│  │  Total Savings:                                                -$54.14/year        ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐│
│  │  EXAMPLE CLAIMS                                                                      ││
│  │                                                                                      ││
│  │  Scenario              Vet Bill    Your Cost    We Pay                             ││
│  │  ─────────────────────────────────────────────────────                             ││
│  │  Ear Infection         $350        $330         $20*                               ││
│  │  Broken Leg            $3,000      $700         $2,300                             ││
│  │  Cancer Treatment      $8,000      $1,850       $6,150                             ││
│  │                                                                                      ││
│  │  *After $250 deductible is met, we reimburse 80%                                   ││
│  └─────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
│                    [ Modify Coverage ]    [ Save Quote ]    [ Enroll Now ]              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## EIS Rate Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    RATE COMPARISON                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Our Premium:          $637.62                                  │
│  EIS Mock Premium:     $645.00                                  │
│                        ──────────                               │
│  Difference:           -$7.38 (-1.14%)                          │
│                                                                  │
│  ✓ WITHIN TOLERANCE (±2%)                                       │
│                                                                  │
│  Factor Comparison:                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Factor           Ours      EIS     Variance                ││
│  │  ─────────────────────────────────────────────              ││
│  │  Base Rate        $420      $420    0.0%                    ││
│  │  Breed Factor     1.24      1.25    -0.8%                   ││
│  │  Age Factor       1.20      1.20    0.0%                    ││
│  │  Location Factor  1.16      1.15    +0.9%                   ││
│  │  Discount Rate    8%        8%      0.0%                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Rating Factors Reference

### Base Rates by Species/Breed Category

| Species | Breed Category | Base Rate/Year |
|---------|----------------|----------------|
| Dog | Small (< 20 lbs) | $320 |
| Dog | Medium (20-50 lbs) | $380 |
| Dog | Large (50-90 lbs) | $420 |
| Dog | Giant (90+ lbs) | $480 |
| Cat | Domestic/Mixed | $280 |
| Cat | Purebred | $340 |

### Breed Risk Factors (Sample)

| Breed | Risk Factor | Common Conditions |
|-------|-------------|-------------------|
| Golden Retriever | 1.15 | Hip dysplasia, cancer, heart disease |
| French Bulldog | 1.35 | BOAS, IVDD, allergies |
| German Shepherd | 1.20 | Hip/elbow dysplasia, bloat |
| Labrador Retriever | 1.10 | Hip dysplasia, obesity |
| Maine Coon | 1.15 | HCM, hip dysplasia |
| Persian Cat | 1.20 | PKD, respiratory issues |
| Mixed Breed Dog | 0.95 | Lower hereditary risk |
| Domestic Shorthair | 0.90 | Lower hereditary risk |

### Age Factor Curve

| Age Range | Dog Factor | Cat Factor |
|-----------|------------|------------|
| 0-1 years | 0.85 | 0.85 |
| 1-4 years | 1.00 | 1.00 |
| 4-7 years | 1.20 | 1.10 |
| 7-10 years | 1.50 | 1.30 |
| 10-12 years | 2.00 | 1.50 |
| 12+ years | 2.50 | 1.80 |

### Discount Schedule

| Discount | Rate | Requirements |
|----------|------|--------------|
| Spayed/Neutered | 5% | Pet is fixed |
| Microchipped | 3% | Has registered microchip |
| Multi-Pet | 10% | 2+ pets on policy |
| Annual Pay | 5% | Pay full year upfront |
| Shelter/Rescue | 5% | Adopted from shelter |
| Military/Veteran | 10% | Active or veteran |
| Loyalty | 5% | Renewing customer |
| **Total Cap** | **30%** | Maximum combined discounts |

### Coverage Options

| Option | Annual Limit | Deductible | Reimbursement |
|--------|--------------|------------|---------------|
| Basic | $5,000 | $500 | 70% |
| Standard | $10,000 | $250 | 80% |
| Premium | $15,000 | $100 | 90% |
| Unlimited | No cap | $250 | 80% |

### Waiting Periods

| Coverage Type | Waiting Period |
|---------------|----------------|
| Accidents | 0-3 days |
| Illnesses | 14 days |
| Orthopedic (cruciate) | 6 months |
| Hip Dysplasia | 12 months |
| Cancer | 30 days |
