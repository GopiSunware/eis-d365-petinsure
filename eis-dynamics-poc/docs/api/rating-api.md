# Pet Insurance Rating API Reference (WS5)

Base URL: `/api/v1`

## Overview

The Pet Insurance Rating API calculates premiums based on pet characteristics (species, breed, age), location, and coverage selections. It supports breed-based risk factors and comparison against EIS mock rates.

## Endpoints

### Calculate Pet Quote

Generate a pet insurance premium quote.

```
POST /rating/quote
```

#### Request Body

```json
{
  "state": "string (required) - 2-letter state code",
  "zip_code": "string (required) - 5-digit ZIP",
  "effective_date": "string (required) - ISO date",
  "pet": {
    "name": "string (required)",
    "species": "string (required) - dog|cat|bird|rabbit|reptile",
    "breed": "string (required) - breed name",
    "date_of_birth": "string (required) - ISO date",
    "gender": "string - male|female",
    "spayed_neutered": "boolean",
    "microchipped": "boolean",
    "microchip_id": "string (optional)",
    "weight_lbs": "number (optional)",
    "pre_existing_conditions": ["string"]
  },
  "coverage": {
    "plan_type": "string - accident_only|accident_illness|comprehensive",
    "annual_limit": "number - 5000|10000|15000|0 (unlimited)",
    "deductible": "number - 100|250|500|750",
    "reimbursement_pct": "number - 70|80|90"
  },
  "add_ons": {
    "wellness": "boolean",
    "dental": "boolean",
    "behavioral": "boolean"
  },
  "discounts": {
    "multi_pet": "boolean",
    "annual_pay": "boolean",
    "shelter_rescue": "boolean",
    "military_veteran": "boolean"
  }
}
```

#### Example Request

```bash
curl -X POST http://localhost:8003/api/v1/rating/quote \
  -H "Content-Type: application/json" \
  -d '{
    "state": "IL",
    "zip_code": "60601",
    "effective_date": "2024-07-01",
    "pet": {
      "name": "Max",
      "species": "dog",
      "breed": "Golden Retriever",
      "date_of_birth": "2019-03-15",
      "gender": "male",
      "spayed_neutered": true,
      "microchipped": true
    },
    "coverage": {
      "plan_type": "accident_illness",
      "annual_limit": 10000,
      "deductible": 250,
      "reimbursement_pct": 80
    },
    "add_ons": {
      "wellness": false,
      "dental": false,
      "behavioral": false
    },
    "discounts": {
      "multi_pet": false,
      "annual_pay": false,
      "shelter_rescue": false,
      "military_veteran": false
    }
  }'
```

#### Response (200 OK)

```json
{
  "quote_id": "QTE-PET-2024-00001",
  "state": "IL",
  "effective_date": "2024-07-01",
  "expiration_date": "2025-07-01",
  "valid_until": "2024-07-31T23:59:59Z",
  "pet": {
    "name": "Max",
    "species": "dog",
    "breed": "Golden Retriever",
    "age_years": 5,
    "gender": "male"
  },
  "premium_breakdown": {
    "base_rate": 420.00,
    "species_factor": 1.00,
    "breed_factor": 1.15,
    "size_factor": 1.08,
    "combined_breed_factor": 1.24,
    "age_factor": 1.20,
    "location_factor": 1.16,
    "base_premium_with_factors": 724.76,
    "coverage_adjustments": {
      "plan_type": "accident_illness",
      "plan_factor": 1.00,
      "annual_limit_factor": 1.00,
      "deductible_credit": -48.00,
      "reimbursement_factor": 1.00
    },
    "adjusted_premium": 676.76,
    "add_on_charges": [],
    "discounts": [
      {"name": "Spayed/Neutered", "rate": 0.05, "amount": -33.84},
      {"name": "Microchipped", "rate": 0.03, "amount": -20.30}
    ],
    "total_discounts": -54.14,
    "policy_fee": 15.00,
    "total_annual_premium": 637.62
  },
  "monthly_premium": 53.14,
  "comparison": {
    "eis_premium": 645.00,
    "difference": -7.38,
    "percentage_diff": -1.14,
    "within_tolerance": true
  }
}
```

---

### Get Breed Factors

Retrieve breed-specific rating factors.

```
GET /rating/breeds
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| species | string | Filter by species (dog, cat) |
| breed | string | Search by breed name |

#### Response (200 OK)

```json
{
  "breeds": [
    {
      "breed_id": "golden-retriever",
      "species": "dog",
      "breed_name": "Golden Retriever",
      "breed_group": "Sporting",
      "size_category": "large",
      "avg_weight_lbs": 65,
      "avg_lifespan_years": 11,
      "base_rate": 420.00,
      "risk_factor": 1.15,
      "hereditary_conditions": [
        "hip_dysplasia",
        "elbow_dysplasia",
        "heart_disease",
        "cancer",
        "eye_conditions"
      ],
      "age_rating_curve": {
        "0-1": 0.85,
        "1-4": 1.00,
        "4-7": 1.20,
        "7-10": 1.50,
        "10+": 2.00
      }
    },
    {
      "breed_id": "french-bulldog",
      "species": "dog",
      "breed_name": "French Bulldog",
      "breed_group": "Non-Sporting",
      "size_category": "small",
      "avg_weight_lbs": 25,
      "avg_lifespan_years": 10,
      "base_rate": 380.00,
      "risk_factor": 1.35,
      "hereditary_conditions": [
        "boas",
        "ivdd",
        "allergies",
        "hip_dysplasia",
        "eye_conditions"
      ],
      "age_rating_curve": {
        "0-1": 0.90,
        "1-4": 1.00,
        "4-7": 1.30,
        "7-10": 1.70,
        "10+": 2.20
      }
    }
  ],
  "total": 2
}
```

---

### Get Rating Factors

Retrieve current rating factors by category.

```
GET /rating/factors
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| state | string | Filter by state code |
| category | string | Filter by category (species, age, location, discount) |

#### Response (200 OK)

```json
{
  "species_factors": {
    "dog": {
      "base_multiplier": 1.00,
      "size_categories": {
        "small": {"max_weight": 20, "factor": 0.95},
        "medium": {"max_weight": 50, "factor": 1.00},
        "large": {"max_weight": 90, "factor": 1.08},
        "giant": {"max_weight": 999, "factor": 1.15}
      }
    },
    "cat": {
      "base_multiplier": 0.80,
      "size_categories": {
        "domestic": {"factor": 1.00},
        "purebred": {"factor": 1.15}
      }
    }
  },
  "age_factors": {
    "dog": {
      "0-1": 0.85,
      "1-4": 1.00,
      "4-7": 1.20,
      "7-10": 1.50,
      "10-12": 2.00,
      "12+": 2.50
    },
    "cat": {
      "0-1": 0.85,
      "1-4": 1.00,
      "4-7": 1.10,
      "7-10": 1.30,
      "10-14": 1.50,
      "14+": 1.80
    }
  },
  "location_factors": {
    "IL": {"state_factor": 1.05, "urban_factor": 1.10},
    "CA": {"state_factor": 1.20, "urban_factor": 1.15},
    "TX": {"state_factor": 0.95, "urban_factor": 1.05},
    "NY": {"state_factor": 1.25, "urban_factor": 1.20}
  },
  "discounts": {
    "spayed_neutered": 0.05,
    "microchipped": 0.03,
    "multi_pet": 0.10,
    "annual_pay": 0.05,
    "shelter_rescue": 0.05,
    "military_veteran": 0.10,
    "loyalty": 0.05
  },
  "discount_cap": 0.30
}
```

---

### Update Rating Factor (Admin)

Update a rating factor (admin only).

```
PUT /rating/factors/{factor_id}
```

#### Request Body

```json
{
  "value": 0.08,
  "effective_date": "2024-07-01",
  "reason": "Annual rate review - increasing spayed/neutered discount"
}
```

#### Response (200 OK)

```json
{
  "factor_id": "spayed_neutered",
  "category": "discounts",
  "previous_value": 0.05,
  "new_value": 0.08,
  "effective_date": "2024-07-01",
  "updated_at": "2024-06-15T14:30:00Z",
  "updated_by": "admin@example.com"
}
```

---

### Compare with EIS

Compare calculated premium against EIS mock rate.

```
POST /rating/compare
```

#### Request Body

Same as `/rating/quote` request body.

#### Response (200 OK)

```json
{
  "our_premium": 637.62,
  "eis_premium": 645.00,
  "difference": -7.38,
  "percentage_diff": -1.14,
  "within_tolerance": true,
  "factor_comparison": [
    {
      "factor": "breed_factor",
      "our_value": 1.24,
      "eis_value": 1.25,
      "difference_pct": -0.8
    },
    {
      "factor": "age_factor",
      "our_value": 1.20,
      "eis_value": 1.20,
      "difference_pct": 0.0
    },
    {
      "factor": "location_factor",
      "our_value": 1.16,
      "eis_value": 1.15,
      "difference_pct": 0.9
    }
  ],
  "analysis": "Premium is within +/-2% tolerance. Minor variances in breed and location factors cancel out."
}
```

---

### Get Coverage Options

Retrieve available coverage options and plans.

```
GET /rating/coverages
```

#### Response (200 OK)

```json
{
  "plan_types": [
    {
      "type": "accident_only",
      "name": "Accident Only",
      "description": "Covers injuries from accidents only",
      "price_range": "$15-25/mo",
      "includes": ["accidents", "emergency_care", "surgery_accident"]
    },
    {
      "type": "accident_illness",
      "name": "Accident + Illness",
      "description": "Covers accidents AND illnesses (recommended)",
      "price_range": "$35-55/mo",
      "includes": ["accidents", "illnesses", "emergency_care", "surgery", "medications", "diagnostics", "hereditary"]
    },
    {
      "type": "comprehensive",
      "name": "Comprehensive",
      "description": "Accident + Illness + Wellness",
      "price_range": "$50-80/mo",
      "includes": ["accidents", "illnesses", "wellness", "dental", "behavioral", "alternative"]
    }
  ],
  "annual_limits": [
    {"value": 5000, "label": "$5,000/year", "factor": 0.85},
    {"value": 10000, "label": "$10,000/year", "factor": 1.00},
    {"value": 15000, "label": "$15,000/year", "factor": 1.15},
    {"value": 0, "label": "Unlimited", "factor": 1.40}
  ],
  "deductibles": [
    {"value": 100, "label": "$100", "factor": 1.15},
    {"value": 250, "label": "$250", "factor": 1.00},
    {"value": 500, "label": "$500", "factor": 0.88},
    {"value": 750, "label": "$750", "factor": 0.80}
  ],
  "reimbursement_rates": [
    {"value": 70, "label": "70%", "factor": 0.85},
    {"value": 80, "label": "80%", "factor": 1.00},
    {"value": 90, "label": "90%", "factor": 1.20}
  ],
  "add_ons": [
    {
      "type": "wellness",
      "name": "Wellness Add-On",
      "description": "Vaccines, checkups, dental cleaning, flea/tick",
      "monthly_cost": 15.00,
      "annual_limit": 450.00
    },
    {
      "type": "dental",
      "name": "Dental Add-On",
      "description": "Dental illness, extractions, periodontal disease",
      "monthly_cost": 8.00,
      "annual_limit": 500.00
    },
    {
      "type": "behavioral",
      "name": "Behavioral Add-On",
      "description": "Behavioral therapy, anxiety training",
      "monthly_cost": 5.00,
      "annual_limit": 300.00
    }
  ],
  "waiting_periods": {
    "accident": {"days": 3, "description": "Accidents"},
    "illness": {"days": 14, "description": "Illnesses"},
    "orthopedic": {"days": 180, "description": "Cruciate/orthopedic"},
    "hip_dysplasia": {"days": 365, "description": "Hip dysplasia"},
    "cancer": {"days": 30, "description": "Cancer"}
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| INVALID_STATE | State code not recognized |
| INVALID_SPECIES | Species not supported |
| BREED_NOT_FOUND | Breed not in database |
| PET_AGE_INELIGIBLE | Pet too young or too old for coverage |
| INVALID_COVERAGE | Coverage option not valid |
| RATE_CALCULATION_ERROR | Error during premium calculation |
| FACTOR_NOT_FOUND | Rating factor not found |
