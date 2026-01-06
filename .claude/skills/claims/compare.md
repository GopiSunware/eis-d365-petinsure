# Rule vs Agent Comparison Skill

Compare rule-based (PetInsure360) and agent-driven (EIS-Dynamics) claims processing approaches.

## Comparison Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPARISON FRAMEWORK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   RULE-BASED (PetInsure360)     │    AGENT-DRIVEN (EIS-Dynamics)│
│   ─────────────────────────     │    ────────────────────────── │
│   • Fixed business rules         │    • LLM-powered reasoning    │
│   • Deterministic outcomes       │    • Adaptive decision-making │
│   • < 100ms processing          │    • 30-120s processing       │
│   • No reasoning trail          │    • Full audit trail         │
│   • Pattern: if-then-else       │    • Pattern: analyze-reason  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Run Comparison

### Compare Single Scenario

**Endpoint**: `POST http://localhost:8006/api/v1/compare/scenario/{scenario_id}`

```bash
curl -X POST "http://localhost:8006/api/v1/compare/scenario/SCN-001"
```

**Response**:
```json
{
  "scenario_id": "SCN-001",
  "scenario_name": "Simple gastritis claim",
  "comparison": {
    "rule_based": {
      "decision": "APPROVED",
      "payment_amount": 1125,
      "processing_time_ms": 45,
      "reasoning": null
    },
    "agent_driven": {
      "decision": "APPROVED",
      "payment_amount": 1125,
      "processing_time_ms": 38500,
      "reasoning": "Claim validated through Bronze layer. Coverage confirmed at 80% after $250 deductible. Treatment costs within benchmark range (65th percentile). No fraud indicators detected (score: 8). Recommendation: AUTO_APPROVE."
    }
  },
  "match": true,
  "decision_alignment": "FULL_MATCH",
  "amount_difference": 0
}
```

### Compare All Scenarios

```bash
curl -X POST "http://localhost:8006/api/v1/compare/all"
```

**Response**:
```json
{
  "total_scenarios": 20,
  "completed": 20,
  "results": {
    "full_match": 17,
    "partial_match": 2,
    "mismatch": 1
  },
  "match_rate": 0.85,
  "average_times": {
    "rule_based_ms": 52,
    "agent_driven_ms": 42300
  },
  "mismatches": [
    {
      "scenario_id": "SCN-015",
      "rule_decision": "DENY",
      "agent_decision": "APPROVED",
      "reason": "Agent detected edge case coverage exception"
    }
  ]
}
```

## Comparison Metrics

### Decision Alignment

| Alignment | Description |
|-----------|-------------|
| `FULL_MATCH` | Same decision and payment amount |
| `PARTIAL_MATCH` | Same decision, different amount (±5%) |
| `MISMATCH` | Different decisions |

### Performance Metrics

```json
{
  "metrics": {
    "rule_based": {
      "avg_processing_ms": 50,
      "p95_processing_ms": 120,
      "throughput_per_second": 200
    },
    "agent_driven": {
      "avg_processing_ms": 42000,
      "p95_processing_ms": 95000,
      "throughput_per_second": 0.02
    }
  }
}
```

## Feature Comparison Matrix

| Feature | Rule-Based | Agent-Driven |
|---------|------------|--------------|
| **Processing Speed** | < 100ms | 30-120 seconds |
| **Decision Explainability** | None | Full reasoning |
| **Edge Case Handling** | Limited | Adaptive |
| **Fraud Detection** | Pattern matching | Cross-claim analysis |
| **Consistency** | 100% deterministic | 95%+ consistent |
| **Maintenance** | Code changes | Prompt updates |
| **Cost per Claim** | ~$0.001 | ~$0.15-0.30 |
| **Scalability** | Excellent | Limited by API |
| **Audit Trail** | Log-based | Reasoning-based |

## When to Use Each Approach

### Use Rule-Based When:
- High volume, simple claims
- Speed is critical
- Decisions are straightforward
- Regulatory requirements demand determinism
- Cost optimization is priority

### Use Agent-Driven When:
- Complex claims requiring judgment
- Edge cases or exceptions
- Fraud investigation needed
- Full audit trail required
- Novel scenarios encountered

## Hybrid Approach

The recommended approach combines both:

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID PROCESSING                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Claim Intake → Router Assessment                              │
│                        │                                         │
│        ┌───────────────┼───────────────┐                        │
│        ▼               ▼               ▼                        │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                    │
│   │  SIMPLE │    │ MEDIUM  │    │ COMPLEX │                    │
│   │  Rules  │    │  Rules  │    │  Agent  │                    │
│   │  Only   │    │ + Agent │    │  Full   │                    │
│   │         │    │  Review │    │ Pipeline│                    │
│   └────┬────┘    └────┬────┘    └────┬────┘                    │
│        │              │              │                          │
│        └──────────────┴──────────────┘                          │
│                        │                                         │
│                   Final Decision                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Comparison Reports

### Generate Comparison Report

```bash
curl "http://localhost:8006/api/v1/compare/report?format=json"
```

**Response**:
```json
{
  "report_id": "RPT-2024-001",
  "generated_at": "2024-12-15T10:30:00Z",
  "summary": {
    "total_claims_compared": 100,
    "decision_match_rate": 0.87,
    "amount_variance_avg": 2.3,
    "agent_advantages": [
      "Caught 3 fraud cases missed by rules",
      "Approved 5 edge cases correctly denied by rules"
    ],
    "rule_advantages": [
      "850x faster processing",
      "100% consistent decisions",
      "Lower operational cost"
    ]
  },
  "recommendations": [
    "Use rules for claims under $1000 with no flags",
    "Route claims with fraud indicators to agent pipeline",
    "Review mismatched decisions weekly for rule updates"
  ]
}
```

## Code Processor (Rule-Based)

The rule-based processor in `code_processor.py`:

```python
class CodeProcessor:
    def process_claim(self, claim_data: dict) -> dict:
        # 1. Validate policy
        policy = self.validate_policy(claim_data['policy_id'])

        # 2. Check coverage
        coverage = self.check_coverage(
            policy,
            claim_data['diagnosis_code']
        )

        # 3. Calculate payment
        payment = self.calculate_payment(
            claim_data['claim_amount'],
            policy['deductible'],
            policy['copay']
        )

        # 4. Basic fraud check
        fraud_flag = self.check_fraud_patterns(claim_data)

        # 5. Make decision
        if not coverage['covered']:
            return {'decision': 'DENY', 'reason': 'NOT_COVERED'}
        if fraud_flag:
            return {'decision': 'REVIEW', 'reason': 'FRAUD_FLAG'}

        return {
            'decision': 'APPROVED',
            'payment_amount': payment
        }
```

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/compare/scenario/{id}` | Compare single scenario |
| `POST /api/v1/compare/all` | Compare all scenarios |
| `GET /api/v1/compare/report` | Generate comparison report |
| `GET /api/v1/compare/metrics` | Get performance metrics |
| `POST /api/v1/compare/custom` | Compare custom claim data |

## Files

```
eis-dynamics-poc/src/ws6_agent_pipeline/
├── app/
│   ├── services/
│   │   ├── code_processor.py      # Rule-based processor
│   │   └── comparison_service.py  # Comparison logic
│   └── routers/
│       └── compare.py             # Comparison endpoints
└── data/
    └── claim_scenarios.json       # Test scenarios

petinsure360/backend/
└── app/
    └── services/
        └── pipeline_service.py    # Rule-based pipeline
```
