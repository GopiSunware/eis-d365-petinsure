# PetInsure360 + EIS Dynamics Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PETINSURE360 (Rule-Based)                           │
│                           Ports 3000-3099                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Customer   │    │  BI Dashboard│    │   Backend    │                  │
│  │    Portal    │    │    (3001)    │    │    (3002)    │                  │
│  │   (3000)     │    │              │    │              │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                           │
│         └───────────────────┴───────────────────┘                           │
│                             │                                               │
│                             │ Claims Upload                                 │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Azure Data Lake Storage Gen2                      │  │
│  │              Account: petinsud7i43 | Container: raw                   │  │
│  │                                                                        │  │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐                   │  │
│  │  │   Bronze   │───▶│   Silver   │───▶│    Gold    │                   │  │
│  │  │  (raw/)    │    │(processed/)│    │ (curated/) │                   │  │
│  │  └────────────┘    └────────────┘    └────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              │ DocGen Integration (http://localhost:8007)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EIS DYNAMICS (Agent-Driven)                          │
│                           Ports 8000-8099                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Backend Services                              │  │
│  │                                                                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │  │
│  │  │Claims Data │  │   DocGen   │  │  Pipeline  │  │   Admin    │      │  │
│  │  │ API (8000) │  │   (8007)   │  │   (8006)   │  │   (8008)   │      │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘      │  │
│  │                                                                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                      │  │
│  │  │ AI Claims  │  │Integration │  │   Rating   │                      │  │
│  │  │   (8002)   │  │   (8003)   │  │   (8005)   │                      │  │
│  │  └────────────┘  └────────────┘  └────────────┘                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Frontend UIs                                  │  │
│  │                                                                        │  │
│  │  ┌────────────────────────────┐  ┌────────────────────────────┐      │  │
│  │  │    EIS Agent Portal        │  │    EIS Admin Portal        │      │  │
│  │  │         (8080)             │  │         (8081)             │      │  │
│  │  │  - Claims processing       │  │  - System configuration    │      │  │
│  │  │  - Pipeline monitoring     │  │  - AI config management    │      │  │
│  │  │  - Document management     │  │  - Audit logs              │      │  │
│  │  └────────────────────────────┘  └────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Claims Processing Flow (Medallion Architecture)

### 1. Bronze Layer (Raw Data)
- User uploads claim documents via PetInsure360 Customer Portal
- Raw data written to Azure Data Lake Storage Gen2 (`raw/` container)
- Supports: JSON, PDF, Images

### 2. Silver Layer (Processed)
- DocGen Service (8007) processes documents with AI Agent:
  - OCR extraction
  - Data validation
  - Policy matching
  - Initial scoring
- Processed data written to `processed/` container

### 3. Gold Layer (Curated)
- Final claim decisions
- Aggregated analytics
- Business-ready data for BI Dashboard

---

## Cloud Credentials Configuration

### AI API Keys (Required for Agent Processing)

**Location**: `eis-dynamics-poc/.env`

```bash
# Anthropic Claude API (PRIMARY - used by DocGen Agent)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...

# OpenAI API (alternative provider)
OPENAI_API_KEY=sk-proj-xxxxx...
```

The DocGen service (8007) loads API keys from the root `.env` file.
All EIS services inherit from this configuration.

**Important**: Without a valid `ANTHROPIC_API_KEY`, the Agent Pipeline will fail with:
> "Claude API required for agent-driven processing"

### Azure (PetInsure360)

**Method**: Azure CLI Login + Environment Variables

```bash
# Login via Azure CLI (already done)
az login

# Environment variables (petinsure360/backend/.env):
AZURE_STORAGE_ACCOUNT=petinsud7i43
AZURE_STORAGE_KEY=<key>
AZURE_STORAGE_CONTAINER=raw
```

The storage service uses `DefaultAzureCredential` which automatically:
1. Checks for environment variables
2. Falls back to Azure CLI credentials
3. Works identically in local/cloud

### AWS (EIS Dynamics)

**Method**: AWS CLI Profile

```bash
# AWS Profile configured
export AWS_PROFILE=sunwaretech
export AWS_REGION=us-east-1

# Verify credentials
aws sts get-caller-identity
```

---

## Environment Consistency (Local/Cloud)

The architecture uses **environment variables** to abstract storage locations:

| Environment | PetInsure360 Storage | EIS Services |
|-------------|---------------------|--------------|
| **Local** | Azure ADLS Gen2 (via env) | Local JSON files |
| **Azure** | Azure ADLS Gen2 | Azure App Services |
| **AWS** | S3 | ECS/Fargate |

### Key Environment Files

| File | Purpose |
|------|---------|
| `eis-dynamics-poc/.env` | **AI API Keys** (Claude, OpenAI), App settings |
| `petinsure360/backend/.env` | Azure Storage, API port |
| `petinsure360/bi-dashboard/.env` | DocGen URL override |
| `eis-dynamics-poc/deploy-aws.sh` | AWS deployment config |

---

## Integration Points

### PetInsure360 → EIS DocGen

```
Customer Portal (3000)
         │
         ▼
   Backend (3002)
         │
         │ POST /api/docgen/process
         ▼
   DocGen Service (8007)
         │
         │ AI Agent processes document
         │
         ▼
   Returns: decision, confidence, extracted_data
```

**Configuration**:
```python
# petinsure360/backend/app/api/docgen.py
DOCGEN_SERVICE_URL = os.getenv("DOCGEN_SERVICE_URL", "http://localhost:8007")
```

---

## Starting Services

### Quick Start (All Services)

```bash
# Terminal 1: EIS DocGen (START FIRST)
cd eis-dynamics-poc/src/ws7_docgen
source ../../../venv/bin/activate
uvicorn app.main:app --port 8007 --reload

# Terminal 2: PetInsure360 Backend
cd petinsure360/backend
source env_backend/bin/activate
uvicorn app.main:socket_app --port 3002 --reload

# Terminal 3: PetInsure360 Customer Portal
cd petinsure360/frontend
npm run dev

# Terminal 4: PetInsure360 BI Dashboard
cd petinsure360/bi-dashboard
npm run dev

# Terminal 5: EIS Agent Portal
cd eis-dynamics-poc/src/ws4_agent_portal
npm run dev

# Terminal 6: EIS Admin Portal
cd eis-dynamics-poc/src/ws8_admin_portal/frontend
npm run dev
```

---

## Deployment

### AWS Deployment (EIS Dynamics)

```bash
cd eis-dynamics-poc
./deploy-aws.sh all
```

This will:
1. Initialize Terraform
2. Create ECR, ECS, S3 resources
3. Build and push Docker images
4. Deploy services

### Azure Deployment (PetInsure360)

```bash
# Ensure az login is active
az login

# Deploy via Azure CLI or Azure DevOps pipeline
# (Storage already configured in ADLS Gen2)
```

---

## Service URLs Summary

| Service | Local URL | Purpose |
|---------|-----------|---------|
| Customer Portal | http://localhost:3000 | User claim submission |
| BI Dashboard | http://localhost:3001 | Analytics & insights |
| PetInsure Backend | http://localhost:3002 | API + Storage |
| Claims Data API | http://localhost:8000 | EIS data gateway |
| AI Claims | http://localhost:8002 | Fraud detection |
| Integration | http://localhost:8003 | Mock EIS APIs |
| Rating Engine | http://localhost:8005 | Premium calculation |
| Agent Pipeline | http://localhost:8006 | Medallion processing |
| DocGen | http://localhost:8007 | Document processing |
| Admin Backend | http://localhost:8008 | Admin API |
| Agent Portal | http://localhost:8080 | Claims agents UI |
| Admin Portal | http://localhost:8081 | Admin UI |
