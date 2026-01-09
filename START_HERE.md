# START HERE - New Claude Session Guide

**Purpose:** Quick orientation for new Claude sessions.

**Last Updated:** 2026-01-09

**Status:** Hybrid AWS (Compute) + Azure (Data Platform) - DEPLOYED

---

## Read These Files In Order

### 1. CRITICAL_RULES.md - READ FIRST!
Rules that MUST NEVER be violated:
- Never use `/tmp/` folder - always use project-relative paths
- Data storage patterns (Bronze/Silver/Gold layers)
- File path conventions

### 2. README.md - Live Deployment Status
Current deployment URLs:
- AWS services (App Runner, S3, Lambda)
- Azure resources (Databricks, ADLS Gen2)
- All production URLs

### 3. CLAUDE.md - Project Overview
- Project structure (EIS-Dynamics POC + PetInsure360)
- Available skills, agents, and commands
- Tech stack details

### 4. AWS_DEPLOYMENT_FINAL_STATUS.md - Deployment Details
- Complete AWS deployment guide
- Golden deploy/destroy scripts
- Service ARNs and environment variables
- Cost estimates

---

## Quick Reference

### AWS Services (Compute Layer)

| Service | Production URL |
|---------|----------------|
| Customer Portal | http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com |
| BI Dashboard | http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com |
| EIS Agent Portal | http://eis-agent-portal.s3-website-us-east-1.amazonaws.com |
| EIS Admin Portal | http://eis-admin-portal.s3-website-us-east-1.amazonaws.com |
| Claims Data API | https://9wvcjmrknc.us-east-1.awsapprunner.com |
| Agent Pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com |
| PetInsure360 Backend | https://fucf3fwwwv.us-east-1.awsapprunner.com |
| WebSocket | wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod |

### Azure Services (Data Platform)

| Resource | Name |
|----------|------|
| Storage (ADLS Gen2) | petinsud7i43 |
| Databricks | petinsure360-databricks-dev |
| Key Vault | petins-kv-ud7i43 |

### Deployment Scripts

```bash
./deploy-aws.sh              # Deploy all services to AWS
./deploy-aws.sh status       # Check deployment status
./destroy-aws.sh             # Clean up all AWS resources
./destroy-aws.sh --dry-run   # Preview what would be deleted
```

### AWS Configuration

```bash
export AWS_PROFILE=sunwaretech
aws sts get-caller-identity
# Account: 611670815873, Region: us-east-1
```

---

## Key Documentation

| File | Purpose |
|------|---------|
| **CRITICAL_RULES.md** | Never use /tmp - MUST READ |
| **README.md** | Live deployment URLs |
| **AWS_DEPLOYMENT_FINAL_STATUS.md** | Complete deployment guide |
| **CLAUDE.md** | Claude Code config & skills |
| **ARCHITECTURE.md** | System architecture |
| **TROUBLESHOOTING.md** | Common issues & fixes |
| **ENV_VARIABLES.md** | Environment variable reference |
| **PORT_CONFIG.md** | Local development ports |

---

## Quick Start Scenarios

### "I need to deploy changes"
```bash
./deploy-aws.sh              # Full deployment
./deploy-aws.sh claims-data-api  # Single service
./deploy-aws.sh frontend     # All frontends
```

### "Something is broken"
1. Check TROUBLESHOOTING.md
2. Review AWS_DEPLOYMENT_FINAL_STATUS.md (common issues section)
3. Check AWS logs: `aws logs tail /aws/apprunner/claims-data-api --follow`

### "I need to work on claims processing"
Use skills:
```
/claims/submit    - Submit claims
/claims/validate  - Validation rules
/claims/fraud     - Fraud detection
/claims/scenarios - Test scenarios
```

---

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Chat API 404 | Chat is on port 8000 (Claims Data API) |
| CORS errors | EIS services need `["*"]` fallback |
| WebSocket fails | Use `socket_app` not `app` for PetInsure360 |
| Data lost on restart | Never use /tmp - use project paths |

---

## Project Structure

```
ms-dynamics/
├── deploy-aws.sh              # Golden deployment script
├── destroy-aws.sh             # Cleanup script
├── CRITICAL_RULES.md          # READ FIRST
├── README.md                  # Live URLs
├── AWS_DEPLOYMENT_FINAL_STATUS.md
│
├── eis-dynamics-poc/          # AI Claims Processing
│   └── src/
│       ├── ws4_agent_portal/  # Next.js (React Flow)
│       ├── ws6_agent_pipeline/ # LangGraph agents
│       ├── ws7_docgen/        # Document AI
│       └── shared/claims_data_api/ # Unified API
│
└── petinsure360/              # Customer Platform
    ├── frontend/              # Customer Portal
    ├── bi-dashboard/          # BI Dashboard
    └── backend/               # FastAPI + Socket.IO
```

---

**Remember:** Read CRITICAL_RULES.md before writing any code!
