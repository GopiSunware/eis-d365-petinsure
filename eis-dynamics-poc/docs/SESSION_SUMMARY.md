# EIS-Dynamics POC - Build Summary

## Version: v1.0.0 (January 2, 2026)

**Status**: Deployed to AWS

---

## AWS Deployment

### Live Services

| Service | URL | Status |
|---------|-----|--------|
| **Unified Claims API** | https://p7qrmgi9sp.us-east-1.awsapprunner.com | Running |
| **Agent Pipeline** | https://bn9ymuxtwp.us-east-1.awsapprunner.com | Running |
| **API Docs** | https://p7qrmgi9sp.us-east-1.awsapprunner.com/docs | Available |

### Infrastructure (Terraform)

| Resource | Details |
|----------|---------|
| **Region** | us-east-1 |
| **Account** | 611670815873 |
| **ECR Repos** | eis-dynamics-unified-api, eis-dynamics-agent-pipeline |
| **App Runner** | 2 services (auto-scaling, 1 vCPU, 2GB RAM) |
| **S3 Bucket** | eis-dynamics-frontend-611670815873 |
| **Secrets Manager** | API keys stored securely |

---

## What Was Built

### 1. Unified Claims API (Port 8000)

Core data gateway with 6 services:

| Service | Endpoints | Purpose |
|---------|-----------|---------|
| ClaimService | 11 | CRUD, search, status |
| PolicyService | 9 | Coverage, limits |
| PetService | 8 | Medical history |
| ProviderService | 8 | Network, licensing |
| ValidationService | 9 | AI-powered validation |
| FraudService | 6 | Pattern detection |

**Total: 60 endpoints, 44 LLM tools**

### 2. Agent Pipeline (Port 8006)

LangGraph-based medallion architecture:

| Agent | Role | Tools |
|-------|------|-------|
| Router | Classify complexity | Basic |
| Bronze | Validate & clean | 27 |
| Silver | Enrich data | 13 |
| Gold | Full analysis | 44 |

### 3. Demo Scenarios (28 Total)

| Category | Count | Purpose |
|----------|-------|---------|
| **Fraud** | 3 | AI vs Rules comparison |
| **Validation** | 5 | Data quality detection |
| **Standard** | 20 | Baseline claims |

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     AWS App Runner                         │
│                                                           │
│  ┌─────────────────────┐    ┌─────────────────────────┐  │
│  │   Unified API       │    │   Agent Pipeline        │  │
│  │   (ECR Image)       │    │   (ECR Image)           │  │
│  │   Port 8000         │    │   Port 8006             │  │
│  └─────────────────────┘    └─────────────────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
                              │
                              │ Secrets Manager
                              │ (ANTHROPIC_API_KEY)
                              ▼
                    ┌─────────────────┐
                    │   Claude AI     │
                    │   (LLM calls)   │
                    └─────────────────┘
```

---

## Demo Flow

### From UI to Backend

```
1. User opens /pipeline/compare
2. Selects scenario (FRAUD-001, VAL-001, etc.)
3. Clicks "Run Comparison"
4. Frontend calls POST /api/v1/compare/scenario/{id}
5. Agent Pipeline service:
   a. Loads scenario data
   b. Runs CODE path (<1ms, 8 rules)
   c. Runs AGENT path (30-120s, 44 tools)
   d. Merges results
6. UI displays side-by-side comparison
```

### Key Scenarios

| ID | Pattern | Rule Result | AI Result |
|----|---------|-------------|-----------|
| FRAUD-001 | Pre-existing gaming | APPROVED | FLAGGED |
| FRAUD-002 | Provider collusion | APPROVED | FLAGGED |
| FRAUD-003 | Staged timing | APPROVED | FLAGGED |
| VAL-001 | Diagnosis mismatch | APPROVED | FAIL |
| VAL-005 | DEA violation | APPROVED | FAIL |

---

## Key Files

| Component | Path |
|-----------|------|
| Unified API | `src/shared/claims_data_api/` |
| Agent Pipeline | `src/ws6_agent_pipeline/` |
| Frontend | `src/ws4_agent_portal/` |
| Terraform | `terraform/aws/` |
| Deploy Script | `deploy-aws.sh` |
| Scenarios | `src/ws6_agent_pipeline/data/claim_scenarios.json` |
| Comparison Router | `src/ws6_agent_pipeline/app/routers/comparison.py` |

---

## Version History

### v1.0.0 (January 2, 2026)
- **AWS Deployment**: App Runner with ECR images
- **Terraform Infrastructure**: S3, ECR, IAM, Secrets Manager
- **Documentation**: SHOWCASE_GUIDE.md with step-by-step instructions
- **Local Validation**: All 28 scenarios tested
- **Bug Fix**: comparison.py reasoning_log attribute

### v0.9.2 (January 1, 2025)
- Code vs Agent comparison page
- 3 fraud scenarios (FRAUD-001 to FRAUD-003)
- 5 validation scenarios (VAL-001 to VAL-005)
- Grouped scenario selector

### v0.9.1 (December 31, 2024)
- AI Demo page at `/pipeline/demo`
- ValidationService with 5 types
- 44 LLM tools for agent pipeline
- Auto-trigger AI summary on completion

### v0.9.0 (December 30, 2024)
- Initial Unified Claims API (60 endpoints)
- LangGraph agent pipeline
- React Flow visualization
- 20 standard demo scenarios

---

## Deployment Commands

### Full Deploy (Local → AWS)

```bash
# Initialize Terraform
cd terraform/aws
terraform init

# Plan and apply
terraform plan -out=tfplan
terraform apply tfplan

# Build Docker images
docker build -t eis-dynamics-unified-api:latest src/shared/claims_data_api/
docker build -t eis-dynamics-agent-pipeline:latest src/ws6_agent_pipeline/

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 611670815873.dkr.ecr.us-east-1.amazonaws.com
docker tag eis-dynamics-unified-api:latest 611670815873.dkr.ecr.us-east-1.amazonaws.com/eis-dynamics-unified-api:latest
docker push 611670815873.dkr.ecr.us-east-1.amazonaws.com/eis-dynamics-unified-api:latest
docker tag eis-dynamics-agent-pipeline:latest 611670815873.dkr.ecr.us-east-1.amazonaws.com/eis-dynamics-agent-pipeline:latest
docker push 611670815873.dkr.ecr.us-east-1.amazonaws.com/eis-dynamics-agent-pipeline:latest
```

### Using Deploy Script

```bash
./deploy-aws.sh all
```

---

## Testing

### Verify AWS Services

```bash
# Unified API
curl https://p7qrmgi9sp.us-east-1.awsapprunner.com/

# Agent Pipeline scenarios
curl https://bn9ymuxtwp.us-east-1.awsapprunner.com/api/v1/scenarios/
```

### Expected Response

```json
{
  "name": "Unified Claims Data API",
  "version": "1.0.0",
  "status": "healthy",
  "data_loaded": true,
  "stats": {
    "customers": 100,
    "pets": 150,
    "policies": 150,
    "claims": 438
  }
}
```
