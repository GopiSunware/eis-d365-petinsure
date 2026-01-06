---
description: Run a claims processing test scenario
---

# Claims Scenario Command

Run pre-built claims processing scenarios to test the system.

## Instructions

1. **List Scenarios** (if no argument)
   - Show available scenario categories
   - Standard (SCN-001 to SCN-020)
   - Fraud (FRAUD-001 to FRAUD-003)
   - Validation (VAL-001 to VAL-013)

2. **Run Scenario**
   - Execute the specified scenario
   - Compare rule-based vs agent-driven results
   - Show decision comparison

3. **Report Results**
   - Show both processing approaches
   - Highlight any differences
   - Explain the reasoning

## Arguments

`$ARGUMENTS` should be:
- Empty: List all scenarios
- Scenario ID: Run that scenario (e.g., "SCN-001", "FRAUD-001", "VAL-005")
- "all": Run all standard scenarios
- "fraud": Run all fraud scenarios
- "validation": Run all validation scenarios

## Scenario Categories

| Category | IDs | Purpose |
|----------|-----|---------|
| Standard | SCN-001 to SCN-020 | Normal claim processing |
| Fraud | FRAUD-001 to FRAUD-003 | Fraud detection patterns |
| Validation | VAL-001 to VAL-013 | Validation rule testing |

## API Endpoints

```bash
# Run comparison scenario
POST http://localhost:8006/api/v1/compare/scenario/{id}

# Run validation scenario
POST http://localhost:8000/api/v1/validation/run-scenario/{id}

# List all scenarios
GET http://localhost:8006/api/v1/scenarios/
```

## Examples

```
/scenario              # List available scenarios
/scenario SCN-001      # Run simple gastritis claim
/scenario FRAUD-001    # Run chronic gaming fraud test
/scenario VAL-001      # Run diagnosis mismatch test
/scenario all          # Run all standard scenarios
```
