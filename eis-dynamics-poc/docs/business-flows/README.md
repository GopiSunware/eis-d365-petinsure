# Business Flows Documentation

## Contents

1. [FNOL Flow](./fnol-flow.md) - First Notice of Loss processing
2. [Quote Flow](./quote-flow.md) - Insurance quote generation
3. [Sync Flow](./sync-flow.md) - EIS to D365 synchronization
4. [Customer 360](./customer-360.md) - Unified customer view

## Business Process Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        INSURANCE OPERATIONS WORKFLOW                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │   ACQUIRE    │────▶│   MANAGE     │────▶│   SERVICE    │────▶│   RETAIN     │
  │              │     │              │     │              │     │              │
  │  • Quote     │     │  • Issue     │     │  • FNOL      │     │  • Renewal   │
  │  • Bind      │     │  • Endorse   │     │  • Claims    │     │  • Cross-sell│
  │  • UW        │     │  • Billing   │     │  • Support   │     │  • Loyalty   │
  └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
         │                    │                    │                    │
         └────────────────────┴────────────────────┴────────────────────┘
                                       │
                              ┌────────▼────────┐
                              │  EIS-D365 POC   │
                              │  ─────────────  │
                              │  WS2: Claims    │
                              │  WS5: Rating    │
                              │  WS3: Sync      │
                              │  WS4: Portal    │
                              └─────────────────┘
```

## Key Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Quote Response Time | < 2 seconds | API latency P95 |
| FNOL Processing | < 30 seconds | End-to-end with AI |
| Fraud Detection Accuracy | ≥ 85% | True positive rate |
| Sync Latency | < 5 minutes | EIS to Dataverse |
| Rating Parity | ± 2% | vs EIS calculation |
