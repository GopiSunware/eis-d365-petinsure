# Claims Fraud Detection Skill

AI-powered fraud detection with pattern matching, velocity analysis, and cross-claim correlation.

## Fraud Detection Capabilities

### Quick Fraud Check

**Endpoint**: `POST /api/v1/fraud/check`

```bash
curl -X POST "http://localhost:8000/api/v1/fraud/check" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-023",
    "pet_id": "PET-034",
    "provider_id": "PROV-011",
    "claim_amount": 1600,
    "diagnosis_code": "S83.5",
    "service_date": "2024-12-15"
  }'
```

**Response**:
```json
{
  "fraud_score": 72,
  "risk_level": "HIGH",
  "indicators": [
    {
      "pattern": "CHRONIC_CONDITION_GAMING",
      "confidence": 0.85,
      "details": "CCL tear claimed as accident, but pet has 3 prior hip claims"
    },
    {
      "pattern": "VELOCITY_SPIKE",
      "confidence": 0.70,
      "details": "4th claim in 90 days (avg: 1.2 claims/year)"
    }
  ],
  "recommendation": "INVESTIGATION"
}
```

## Fraud Patterns

### 1. Chronic Condition Gaming

Pre-existing conditions disguised as accidents.

**Indicators**:
- Anatomical concentration (multiple claims on same body part)
- Cross-claim pattern recognition
- Breed-specific risk correlation
- Pre-policy condition history

**Example**:
```json
{
  "pattern": "CHRONIC_CONDITION_GAMING",
  "score_impact": 25-40,
  "indicators": {
    "same_anatomy_claims": 3,
    "diagnosis_history": ["hip dysplasia", "hip dysplasia", "CCL tear"],
    "breed_risk": "French Bulldog (high orthopedic risk)"
  }
}
```

### 2. Provider Collusion

Exclusive provider usage with suspicious patterns.

**Indicators**:
- 100% claims with one provider
- Out-of-network provider with high amounts
- Round number billing ($1,000, $2,000)
- Provider concentration anomaly

**Example**:
```json
{
  "pattern": "PROVIDER_COLLUSION",
  "score_impact": 15-45,
  "indicators": {
    "provider_concentration": "100%",
    "network_status": "out_of_network",
    "avg_claim_amount": 2500,
    "round_amounts": 4,
    "total_claims_with_provider": 8
  }
}
```

### 3. Staged Timing

Claims suspiciously close to waiting period end.

**Indicators**:
- Claim filed on day 15-17 (waiting period: 14 days)
- Breed-specific condition (French Bulldog + IVDD)
- Missing pre-policy medical records
- Statistical timing anomaly

**Example**:
```json
{
  "pattern": "STAGED_TIMING",
  "score_impact": 25-55,
  "indicators": {
    "days_after_waiting_period": 3,
    "condition": "IVDD",
    "breed": "French Bulldog",
    "pre_policy_records": "missing",
    "statistical_probability": 0.02
  }
}
```

## Velocity Analysis

**Endpoint**: `POST /api/v1/fraud/velocity`

```bash
curl -X POST "http://localhost:8000/api/v1/fraud/velocity" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-023"}'
```

**Response**:
```json
{
  "customer_id": "CUST-023",
  "velocity_metrics": {
    "claims_30_days": 2,
    "claims_90_days": 5,
    "claims_365_days": 12,
    "average_frequency": "1.2 claims/month",
    "expected_frequency": "0.3 claims/month"
  },
  "velocity_score": 45,
  "anomaly": true,
  "message": "Claim frequency 4x higher than average"
}
```

## Duplicate Detection

**Endpoint**: `POST /api/v1/fraud/duplicates`

```bash
curl -X POST "http://localhost:8000/api/v1/fraud/duplicates" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2024-100",
    "service_date": "2024-12-15",
    "diagnosis_code": "K91.1",
    "claim_amount": 1500
  }'
```

**Response**:
```json
{
  "duplicates_found": 2,
  "matches": [
    {
      "claim_id": "CLM-2024-098",
      "match_type": "EXACT",
      "confidence": 0.95,
      "matching_fields": ["service_date", "diagnosis_code", "claim_amount"]
    },
    {
      "claim_id": "CLM-2024-095",
      "match_type": "SIMILAR",
      "confidence": 0.72,
      "details": "Same provider, similar amount ($1,450), 3 days apart"
    }
  ]
}
```

## Fraud Scoring

### Score Calculation

```
Fraud Score = Σ (pattern_score × confidence × severity_weight)

Risk Levels:
  0-14:  LOW        → AUTO_APPROVE eligible
  15-49: MEDIUM     → STANDARD_REVIEW
  50-74: HIGH       → MANUAL_REVIEW
  75+:   CRITICAL   → INVESTIGATION
```

### Score Components

| Component | Weight | Max Score |
|-----------|--------|-----------|
| Chronic Condition Gaming | 1.2 | 40 |
| Provider Collusion | 1.5 | 45 |
| Staged Timing | 1.3 | 55 |
| Velocity Anomaly | 1.0 | 30 |
| Duplicate Detection | 1.4 | 35 |
| Amount Anomaly | 0.8 | 20 |

## Run Fraud Scenarios

3 pre-built fraud scenarios for testing:

```bash
# Run fraud scenario
curl -X POST "http://localhost:8006/api/v1/compare/scenario/FRAUD-001"
```

### Available Fraud Scenarios

| ID | Pattern | Description |
|----|---------|-------------|
| FRAUD-001 | Chronic Gaming | CCL tear on day 17, prior hip dysplasia claims |
| FRAUD-002 | Provider Collusion | 100% out-of-network, round amounts, high totals |
| FRAUD-003 | Staged Timing | French Bulldog IVDD, day 17, missing records |

## Fraud Detection in Agent Pipeline

The Gold Agent performs comprehensive fraud analysis:

```python
# Gold Agent Fraud Analysis
fraud_analysis = {
    "check_chronic_gaming": True,      # Cross-claim patterns
    "check_provider_collusion": True,   # Provider relationship
    "check_staged_timing": True,        # Timing anomalies
    "check_velocity": True,             # Claim frequency
    "check_duplicates": True,           # Similar claims
    "calculate_composite_score": True   # Final scoring
}
```

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/fraud/check` | Comprehensive fraud check |
| `POST /api/v1/fraud/velocity` | Velocity analysis only |
| `POST /api/v1/fraud/duplicates` | Duplicate detection |
| `GET /api/v1/fraud/patterns` | List known patterns |
| `GET /api/v1/fraud/customer/{id}` | Customer fraud history |

## Files

```
eis-dynamics-poc/src/shared/claims_data_api/
├── app/services/fraud_service.py
└── data/fraud_patterns.json

eis-dynamics-poc/src/ws6_agent_pipeline/
└── app/agents/gold_agent.py  # Fraud analysis in Gold layer
```
