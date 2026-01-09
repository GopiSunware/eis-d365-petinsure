# AWS Deployment - Final Status
**Date:** 2026-01-09
**Status:** ALL SERVICES OPERATIONAL

---

## Golden Scripts

### Deploy All Services
```bash
./deploy-aws.sh              # Deploy everything
./deploy-aws.sh backend      # Deploy only backend services
./deploy-aws.sh frontend     # Deploy only frontends
./deploy-aws.sh claims-data-api  # Deploy specific service
./deploy-aws.sh status       # Show deployment status
```

### Clean Destroy
```bash
./destroy-aws.sh             # Interactive (prompts confirmation)
./destroy-aws.sh --dry-run   # Show what would be deleted
./destroy-aws.sh --force     # Skip confirmation (CI/CD)
```

---

## Service Architecture Overview

```
                        ┌─────────────────────────────────────────┐
                        │           AWS S3 (Static Hosting)        │
                        │               us-east-1                  │
                        ├─────────────────────────────────────────┤
                        │                                          │
                        │  Customer Portal                         │
                        │  http://petinsure360-customer-portal.    │
                        │        s3-website-us-east-1.amazonaws.com│
                        │                                          │
                        │  BI Dashboard                            │
                        │  http://petinsure360-bi-dashboard.       │
                        │        s3-website-us-east-1.amazonaws.com│
                        │                                          │
                        └─────────────────┬───────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AWS App Runner Services                              │
│                              us-east-1                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Claims Data API (Port 8080)                                                │
│  https://9wvcjmrknc.us-east-1.awsapprunner.com                             │
│  ├─ Data Services: /api/v1/customers, /api/v1/pets, /api/v1/policies       │
│  ├─ Claims: /api/v1/fraud, /api/v1/validation, /api/v1/billing             │
│  ├─ BI Insights: /api/insights/* (customers, claims, KPIs, segments)       │
│  ├─ AI Chat: /api/chat (Claude + OpenAI)                                   │
│  ├─ AI Config: /api/v1/claims/ai/config, /api/v1/claims/ai/models          │
│  ├─ Rating: /api/v1/rating/*                                                │
│  └─ DocGen: /api/v1/docgen/*                                                │
│                                                                              │
│  Agent Pipeline (Port 8080)                                                 │
│  https://qi2p3x5gsm.us-east-1.awsapprunner.com                             │
│  ├─ /api/pipeline/process - Multi-agent claim processing                   │
│  ├─ /api/pipeline/status - Pipeline status                                  │
│  └─ /api/pipeline/stats - Processing KPIs                                   │
│                                                                              │
│  PetInsure360 Backend (Port 8000)                                           │
│  https://fucf3fwwwv.us-east-1.awsapprunner.com                             │
│  ├─ /api/claims - Claims management                                         │
│  ├─ /api/customers - Customer management                                    │
│  ├─ /api/pets - Pet management                                              │
│  └─ /api/pipeline - Pipeline integration                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Details

### 1. Claims Data API (PRIMARY SERVICE)
**URL:** https://9wvcjmrknc.us-east-1.awsapprunner.com
**Status:** HEALTHY
**ECR:** 611670815873.dkr.ecr.us-east-1.amazonaws.com/claims-data-api:latest
**Instance:** 1 vCPU, 2GB RAM

**Data Loaded:**
- 5,000 customers
- 6,500 pets
- 6,000 policies
- 200 providers
- 15,000 claims

**Endpoints:**
| Category | Prefix | Description |
|----------|--------|-------------|
| Policy | /api/v1/policies | Policy CRUD |
| Customer | /api/v1/customers | Customer management |
| Pet | /api/v1/pets | Pet management |
| Provider | /api/v1/providers | Provider directory |
| Fraud | /api/v1/fraud | Fraud detection |
| Medical | /api/v1/medical | Medical codes |
| Billing | /api/v1/billing | Billing operations |
| Validation | /api/v1/validation | AI validation |
| DataLake | /api/v1/datalake | Data lake ops |
| Chat | /api/chat | AI chat (Claude/OpenAI) |
| Rating | /api/v1/rating | Insurance rating |
| DocGen | /api/v1/docgen | Document generation |
| AI Config | /api/v1/claims/ai | AI model configuration |
| **Insights** | **/api/insights** | **BI analytics** |
| **Pipeline** | **/api/pipeline** | **Pipeline status (NEW)** |

**Test:**
```bash
curl https://9wvcjmrknc.us-east-1.awsapprunner.com/health
curl https://9wvcjmrknc.us-east-1.awsapprunner.com/api/insights/summary
```

---

### 2. Agent Pipeline
**URL:** https://qi2p3x5gsm.us-east-1.awsapprunner.com
**Status:** HEALTHY
**ECR:** 611670815873.dkr.ecr.us-east-1.amazonaws.com/agent-pipeline:latest
**Instance:** 1 vCPU, 2GB RAM

**Agent Architecture:**
```
Router Agent → Bronze Agent → Silver Agent → Gold Agent
 (Classify)     (Extract)      (Enrich)      (Decide)
```

**Test:**
```bash
curl https://qi2p3x5gsm.us-east-1.awsapprunner.com/health
```

---

### 3. PetInsure360 Backend
**URL:** https://fucf3fwwwv.us-east-1.awsapprunner.com
**Status:** HEALTHY
**ECR:** 611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest
**Instance:** 1 vCPU, 2GB RAM

**Note:** Contains DEMO data (3 users). Use Claims Data API for full synthetic data.

---

### 4. Customer Portal (Frontend)
**URL:** http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com
**Bucket:** petinsure360-customer-portal
**Source:** petinsure360/frontend/dist

---

### 5. BI Dashboard (Frontend)
**URL:** http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com
**Bucket:** petinsure360-bi-dashboard
**Source:** petinsure360/bi-dashboard/dist

**Environment Configuration:**
- VITE_API_URL → Claims Data API (for /api/insights/*)
- VITE_CLAIMS_API_URL → Claims Data API (for /api/chat)
- VITE_AI_API_URL → Claims Data API (for AI config)
- VITE_PIPELINE_URL → Agent Pipeline (for /api/pipeline)

---

## WebSocket Configuration

**Lambda WebSocket Gateway:**
- URL: wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
- Used for real-time updates in BI Dashboard

---

## How to Deploy

### Prerequisites
```bash
# Ensure AWS CLI is configured
aws configure --profile sunwaretech

# Set profile
export AWS_PROFILE=sunwaretech

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  611670815873.dkr.ecr.us-east-1.amazonaws.com
```

### Deploy Claims Data API (or any backend)
```bash
# 1. Navigate to service directory
cd eis-dynamics-poc/src/shared/claims_data_api

# 2. Build Docker image
docker build --platform linux/amd64 -t claims-data-api:latest .

# 3. Tag for ECR
docker tag claims-data-api:latest \
  611670815873.dkr.ecr.us-east-1.amazonaws.com/claims-data-api:latest

# 4. Push to ECR
docker push 611670815873.dkr.ecr.us-east-1.amazonaws.com/claims-data-api:latest

# 5. Trigger App Runner deployment
aws apprunner start-deployment \
  --service-arn "arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d" \
  --region us-east-1

# 6. Check deployment status
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d" \
  --region us-east-1 \
  --query "Service.Status"
```

### Deploy Frontend to S3
```bash
# Customer Portal
cd petinsure360/frontend
npm run build
aws s3 sync dist s3://petinsure360-customer-portal --delete

# BI Dashboard
cd petinsure360/bi-dashboard
npm run build
aws s3 sync dist s3://petinsure360-bi-dashboard --delete
```

### S3 SPA Routing Fix
Both S3 buckets are configured with error document = index.html for client-side routing:
```bash
aws s3 website s3://petinsure360-customer-portal \
  --index-document index.html --error-document index.html

aws s3 website s3://petinsure360-bi-dashboard \
  --index-document index.html --error-document index.html
```

---

## Service ARNs Reference

| Service | ARN |
|---------|-----|
| Claims Data API | arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d |
| Agent Pipeline | arn:aws:apprunner:us-east-1:611670815873:service/agent-pipeline/... |
| PetInsure360 Backend | arn:aws:apprunner:us-east-1:611670815873:service/petinsure360-backend/... |

---

## Environment Variables

> **See [ENV_VARIABLES.md](ENV_VARIABLES.md) for complete reference**

### BI Dashboard (.env.production)
```env
VITE_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
VITE_SOCKET_URL=wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
VITE_CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
VITE_AI_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
VITE_DOCGEN_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
VITE_PIPELINE_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com/api
```

### Customer Portal (.env.production)
```env
VITE_API_URL=https://fucf3fwwwv.us-east-1.awsapprunner.com
VITE_CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
VITE_SOCKET_URL=wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
```

---

## Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| Claims Data API (App Runner) | $25 |
| Agent Pipeline (App Runner) | $25 |
| PetInsure360 Backend (App Runner) | $25 |
| ECR Storage (~4GB) | $2 |
| S3 Static Hosting | $1 |
| Lambda WebSocket | $1 |
| **Total** | **$79/month** |

---

## Troubleshooting

### Check App Runner Logs
```bash
aws logs tail /aws/apprunner/claims-data-api --follow --region us-east-1
```

### Common Issues

1. **404 on refresh (S3 SPA)**
   - Fix: Set error document to index.html

2. **CORS errors**
   - Claims Data API has `allow_origins=["*"]` configured

3. **AI service offline**
   - Check /api/v1/claims/ai/config endpoint
   - Verify ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables

4. **Missing synthetic data in BI Dashboard**
   - Ensure VITE_API_URL points to Claims Data API (9wvcjmrknc)
   - Claims Data API has /api/insights/* endpoints with 5000 customers

---

## Recent Updates (2026-01-09)

1. Added `/api/insights/*` endpoints to Claims Data API for BI Dashboard
2. Fixed customer name field mapping (first_name + last_name)
3. Updated BI Dashboard to use Claims Data API for insights (was using PetInsure360 backend)
4. Added `/api/v1/claims/ai/config` and `/api/v1/claims/ai/models` endpoints
5. Configured S3 error document for SPA routing on both frontends
6. Added `/api/pipeline/*` endpoints (pending, flow, status, metrics)
7. Optimized insights/customers endpoint with pre-computed indexes (O(1) lookups)
8. Added 3 demo customers (DEMO-001, DEMO-002, DEMO-003) to customer list
9. Added sorting support (customer_since, last_claim, total_claims) to insights
10. Created golden deployment script (`deploy-aws.sh`)
11. Created cleanup/destroy script (`destroy-aws.sh`)
12. Deployed EIS Agent Portal to S3 (http://eis-agent-portal.s3-website-us-east-1.amazonaws.com)
13. Deployed EIS Admin Portal to S3 (http://eis-admin-portal.s3-website-us-east-1.amazonaws.com)
14. Fixed Next.js dynamic routes for static export (generateStaticParams)

---

## API Endpoint Details

### Insights Service (/api/insights)
```
GET /api/insights/summary          # Overall KPIs
GET /api/insights/customers?limit=100&sort_by=customer_since&sort_order=desc
GET /api/insights/claims?limit=100&sort_by=claim_date&sort_order=desc
GET /api/insights/kpis             # Claims KPIs
GET /api/insights/segments         # Customer segments
```

### Pipeline Service (/api/pipeline)
```
GET /api/pipeline/pending          # Claims pending at each layer
GET /api/pipeline/flow             # Pipeline flow visualization
GET /api/pipeline/status           # Current pipeline health
GET /api/pipeline/metrics          # Detailed pipeline metrics
```

### AI Config Service (/api/v1/claims/ai)
```
GET /api/v1/claims/ai/config       # AI configuration
GET /api/v1/claims/ai/models       # Available AI models
```


 All tasks are complete. Here's a summary of what was created:

  Golden Scripts Created

  1. deploy-aws.sh - Deployment Script

  - Deploys all backend services to AWS App Runner
  - Deploys all frontends to S3
  - Supports selective deployment (./deploy-aws.sh claims-data-api)
  - Shows status with ./deploy-aws.sh status

  2. destroy-aws.sh - Cleanup Script

  - Destroys all AWS resources (App Runner, ECR, S3, Lambda, API Gateway)
  - Supports --dry-run to preview what would be deleted
  - Requires typing DELETE for confirmation (or --force to skip)

  Documentation Updated

  AWS_DEPLOYMENT_FINAL_STATUS.md

  - Added golden script usage instructions
  - Added pipeline service endpoints
  - Added 11 recent updates including all fixes made today
  - Added API endpoint details for insights, pipeline, and AI config

  ENV_VARIABLES.md (NEW)

  - Complete environment variable reference for all services
  - AWS production URLs
  - Frontend and backend env vars
  - URL prefix gotchas and debugging tips
  - AI provider configuration
  - Secrets management guidance

  Service Endpoints Summary
  ┌──────────────────────┬────────────────────────────────────────────────────────────────────────┐
  │       Service        │                             Production URL                             │
  ├──────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Claims Data API      │ https://9wvcjmrknc.us-east-1.awsapprunner.com                          │
  ├──────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Agent Pipeline       │ https://qi2p3x5gsm.us-east-1.awsapprunner.com                          │
  ├──────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ PetInsure360 Backend │ https://fucf3fwwwv.us-east-1.awsapprunner.com                          │
  ├──────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Customer Portal      │ http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com │
  ├──────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ BI Dashboard         │ http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com    │
  ├──────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ WebSocket            │ wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod              │
  └──────────────────────┴────────────────────────────────────────────────────────────────────────┘

    All AWS Deployed Services

  Backend APIs (App Runner)
  ┌──────────────────────┬───────────────────────────────────────────────┬─────────┐
  │       Service        │                      URL                      │ Status  │
  ├──────────────────────┼───────────────────────────────────────────────┼─────────┤
  │ Claims Data API      │ https://9wvcjmrknc.us-east-1.awsapprunner.com │ RUNNING │
  ├──────────────────────┼───────────────────────────────────────────────┼─────────┤
  │ Agent Pipeline       │ https://qi2p3x5gsm.us-east-1.awsapprunner.com │ RUNNING │
  ├──────────────────────┼───────────────────────────────────────────────┼─────────┤
  │ PetInsure360 Backend │ https://fucf3fwwwv.us-east-1.awsapprunner.com │ RUNNING │
  └──────────────────────┴───────────────────────────────────────────────┴─────────┘
  PetInsure360 Frontends (S3)
  ┌─────────────────┬────────────────────────────────────────────────────────────────────────┐
  │     Service     │                                  URL                                   │
  ├─────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ Customer Portal │ http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com │
  ├─────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ BI Dashboard    │ http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com    │
  └─────────────────┴────────────────────────────────────────────────────────────────────────┘
  EIS Dynamics Frontends (S3) - NEW
  ┌──────────────┬────────────────────────────────────────────────────────────┐
  │   Service    │                            URL                             │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Agent Portal │ http://eis-agent-portal.s3-website-us-east-1.amazonaws.com │  React Flow visual pipeline (drag-drop nodes)
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Admin Portal │ http://eis-admin-portal.s3-website-us-east-1.amazonaws.com │
  └──────────────┴────────────────────────────────────────────────────────────┘
  WebSocket
  ┌───────────────────┬───────────────────────────────────────────────────────────┐
  │      Service      │                            URL                            │
  ├───────────────────┼───────────────────────────────────────────────────────────┤
  │ Real-time Updates │ wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod │
  └───────────────────┴───────────────────────────────────────────────────────────┘

  For a clean destroy and redeploy:
  ./destroy-aws.sh           # Destroys all resources
  ./deploy-aws.sh            # Redeploys everything

