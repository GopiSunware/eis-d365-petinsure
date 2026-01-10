# PetInsure360 + EIS Dynamics Architecture

## System Overview

```

Azure Bronze Layer Architecture

  1. Data Flow Overview

  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │                           Azure Medallion Architecture                             │
  ├────────────────┬──────────────────┬──────────────────┬───────────────────────────┤
  │   RAW DATA     │   BRONZE LAYER   │   SILVER LAYER   │      GOLD LAYER           │
  │  (ADLS Gen2)   │ (Delta Tables)   │  (Delta Tables)  │   (Delta/Parquet)         │
  ├────────────────┼──────────────────┼──────────────────┼───────────────────────────┤
  │ customers.csv  │ customers_raw    │ customers_clean  │ customer_360              │
  │ pets.csv       │ pets_raw         │ pets_clean       │ claims_analytics          │
  │ policies.csv   │ policies_raw     │ policies_clean   │ monthly_kpis              │
  │ claims.jsonl   │ claims_raw       │ claims_validated │ risk_scoring              │
  │ providers.csv  │ vet_providers_raw│ providers_clean  │ provider_performance      │
  └────────────────┴──────────────────┴──────────────────┴───────────────────────────┘

  2. Bronze Layer Processing (Databricks)

  The Bronze layer is processed by Azure Databricks notebook 01_bronze_ingestion.py:

  Storage Location:
  abfss://bronze@petinsud7i43.dfs.core.windows.net/

  What Bronze Does:
  1. Raw Ingestion - Reads CSV/JSON from raw container
  2. Schema Enforcement - Applies predefined schemas
  3. Metadata Addition - Adds 3 columns:
    - _ingestion_timestamp - When data was ingested
    - _source_file - Original file path
    - _batch_id - Batch identifier (YYYYMMDDHHMMSS)
  4. Delta Write - Saves as Delta tables in petinsure_bronze database

  Bronze Tables Created:
  ┌───────────────────┬───────────────┬─────────┐
  │       Table       │ Source Format │ Records │
  ├───────────────────┼───────────────┼─────────┤
  │ customers_raw     │ CSV           │ ~5,000  │
  ├───────────────────┼───────────────┼─────────┤
  │ pets_raw          │ CSV           │ ~6,500  │
  ├───────────────────┼───────────────┼─────────┤
  │ policies_raw      │ CSV           │ ~6,000  │
  ├───────────────────┼───────────────┼─────────┤
  │ claims_raw        │ JSONL         │ ~15,000 │
  ├───────────────────┼───────────────┼─────────┤
  │ vet_providers_raw │ CSV           │ ~200    │
  └───────────────────┴───────────────┴─────────┘
  ---
  3. How to Monitor Bronze Layer

  A. BI Dashboard (AWS-Hosted)

  URL: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com

  Navigate to "Rule Engine Pipeline" page:

  ┌─────────────────────────────────────────────────────────────────┐
  │  Rule Engine Pipeline                                           │
  ├─────────────┬─────────────┬─────────────┬───────────────────────┤
  │   SOURCE    │   BRONZE    │   SILVER    │   GOLD                │
  │   (API)     │  Ingestion  │  Validation │   Analytics           │
  │             │  15,000     │   5,003     │   5,003               │
  │             │  7 pending  │  5 pending  │   3 pending           │
  └─────────────┴─────────────┴─────────────┴───────────────────────┘

  Features:
  - Pending Claims Count - Shows claims waiting at each layer
  - Process Buttons - Manually trigger Bronze→Silver, Silver→Gold
  - Processing Log - Recent processing events
  - Real-time Updates - WebSocket notifications on claim movement

  B. API Endpoints (Direct Monitoring)

  # Pipeline Status - Shows counts at each layer
  curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/status

  # Pipeline Flow - Layer statistics
  curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/flow

  # Pending Claims - Claims at each layer
  curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/pending

  # Pipeline Metrics - Detailed stats
  curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/metrics

  C. Azure Portal / Databricks Monitoring

  For the actual Azure Bronze layer:

  1. Azure Portal → Storage Account → Containers
    - raw - Source files
    - bronze - Delta tables
  2. Databricks Workspace → Data
  -- Check Bronze table counts
  SELECT 'customers_raw' as table_name, COUNT(*) as cnt FROM petinsure_bronze.customers_raw
  UNION ALL
  SELECT 'claims_raw', COUNT(*) FROM petinsure_bronze.claims_raw
  3. Databricks → Jobs - Monitor scheduled notebook runs

  D. Azure Data Service Health Check

  # Check Azure connectivity from AWS
  curl https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/azure/health

  Returns:
  {
    "is_available": true,
    "storage_account": "petinsud7i43",
    "last_successful_read": "2026-01-10T13:30:00Z",
    "connection_failures": 0,
    "circuit_breaker_active": false
  }

  ---
  4. Manual Pipeline Operations
  ┌───────────────────────┬─────────────────────────────────────────────┬───────────────────────────────────┐
  │        Action         │                  Endpoint                   │            Description            │
  ├───────────────────────┼─────────────────────────────────────────────┼───────────────────────────────────┤
  │ Process Bronze→Silver │ POST /api/pipeline/process/bronze-to-silver │ Move claims from Bronze to Silver │
  ├───────────────────────┼─────────────────────────────────────────────┼───────────────────────────────────┤
  │ Process Silver→Gold   │ POST /api/pipeline/process/silver-to-gold   │ Move claims from Silver to Gold   │
  ├───────────────────────┼─────────────────────────────────────────────┼───────────────────────────────────┤
  │ Refresh Pipeline      │ POST /api/pipeline/refresh                  │ Reload demo data                  │
  ├───────────────────────┼─────────────────────────────────────────────┼───────────────────────────────────┤
  │ Clear Pipeline        │ DELETE /api/pipeline/clear                  │ Clear all pending claims          │
  └───────────────────────┴─────────────────────────────────────────────┴───────────────────────────────────┘
  ---
  Summary

  The Bronze layer is the raw data landing zone:
  - Azure Databricks runs 01_bronze_ingestion.py to create Delta tables
  - AWS reads the processed Gold layer data via AzureDataService
  - BI Dashboard shows pending claims at each layer with real-time WebSocket updates
  - Monitor via: BI Dashboard UI, API endpoints, Azure Portal, or Databricks SQL


Databricks SQL Queries

  Run these in Azure Databricks → SQL Editor or a notebook:

  -- ============================================
  -- BRONZE LAYER - Raw Ingested Data
  -- ============================================

  -- View all Bronze tables
  SHOW TABLES IN petinsure_bronze;

  -- Count records in all Bronze tables
  SELECT 'customers_raw' as table_name, COUNT(*) as record_count FROM petinsure_bronze.customers_raw
  UNION ALL SELECT 'pets_raw', COUNT(*) FROM petinsure_bronze.pets_raw
  UNION ALL SELECT 'policies_raw', COUNT(*) FROM petinsure_bronze.policies_raw
  UNION ALL SELECT 'claims_raw', COUNT(*) FROM petinsure_bronze.claims_raw
  UNION ALL SELECT 'vet_providers_raw', COUNT(*) FROM petinsure_bronze.vet_providers_raw;

  -- Sample customers (Bronze)
  SELECT customer_id, first_name, last_name, email, customer_segment,
         _ingestion_timestamp, _batch_id
  FROM petinsure_bronze.customers_raw LIMIT 10;

  -- Sample claims (Bronze)
  SELECT claim_id, customer_id, pet_id, claim_type, claim_amount, status,
         _ingestion_timestamp, _source_file
  FROM petinsure_bronze.claims_raw LIMIT 10;

  -- ============================================
  -- SILVER LAYER - Cleaned & Validated
  -- ============================================

  SHOW TABLES IN petinsure_silver;

  SELECT 'customers_clean' as table_name, COUNT(*) as record_count FROM petinsure_silver.customers_clean
  UNION ALL SELECT 'pets_clean', COUNT(*) FROM petinsure_silver.pets_clean
  UNION ALL SELECT 'policies_clean', COUNT(*) FROM petinsure_silver.policies_clean
  UNION ALL SELECT 'claims_validated', COUNT(*) FROM petinsure_silver.claims_validated
  UNION ALL SELECT 'providers_clean', COUNT(*) FROM petinsure_silver.providers_clean;

  -- ============================================
  -- GOLD LAYER - Business Analytics
  -- ============================================

  SHOW TABLES IN petinsure_gold;

  -- Customer 360 view
  SELECT customer_id, full_name, customer_segment, value_tier, risk_category,
         total_claims, total_annual_premium, loss_ratio, churn_risk
  FROM petinsure_gold.customer_360 LIMIT 10;

  -- Claims Analytics
  SELECT claim_id, customer_id, claim_amount, status, claim_category,
         processing_days, fraud_score, auto_adjudicated
  FROM petinsure_gold.claims_analytics LIMIT 10;

  -- Monthly KPIs
  SELECT month, total_claims, approved_claims, denied_claims,
         approval_rate, total_claim_amount, loss_ratio
  FROM petinsure_gold.monthly_kpis ORDER BY month DESC LIMIT 12;

  -- Risk Scoring
  SELECT customer_id, risk_category, risk_score, loss_ratio, claim_frequency
  FROM petinsure_gold.risk_scoring WHERE risk_category = 'High' LIMIT 10;

  ---
  2. Where Data Displays in Dashboard
  ┌─────────────────────────────────────┬──────────────────────┬───────────────────────────────────────┐
  │          Databricks Table           │    Dashboard Page    │              UI Section               │
  ├─────────────────────────────────────┼──────────────────────┼───────────────────────────────────────┤
  │ petinsure_gold.customer_360         │ Customer 360         │ Customer cards, segments, value tiers │
  ├─────────────────────────────────────┼──────────────────────┼───────────────────────────────────────┤
  │ petinsure_gold.claims_analytics     │ Claims Analytics     │ Claims table, status charts           │
  ├─────────────────────────────────────┼──────────────────────┼───────────────────────────────────────┤
  │ petinsure_gold.monthly_kpis         │ Executive Dashboard  │ KPI cards, trend charts               │
  ├─────────────────────────────────────┼──────────────────────┼───────────────────────────────────────┤
  │ petinsure_gold.risk_scoring         │ Risk Analysis        │ Risk distribution, high-risk list     │
  ├─────────────────────────────────────┼──────────────────────┼───────────────────────────────────────┤
  │ petinsure_gold.provider_performance │ Risk Analysis        │ Provider fraud scores                 │
  ├─────────────────────────────────────┼──────────────────────┼───────────────────────────────────────┤
  │ petinsure_bronze.* / silver.*       │ Rule Engine Pipeline │ Pending claims at each layer          │
  └─────────────────────────────────────┴──────────────────────┴───────────────────────────────────────┘
  Dashboard URL: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com

  ---
  3. Azure Storage Account Location

  The storage account name is: petinsud7i43

  To navigate in Azure Portal:

  1. Go to: https://portal.azure.com
  2. Search for: petinsud7i43 in the top search bar
  3. Or navigate: Home → Storage accounts → petinsud7i43

  Containers in this storage account:
  petinsud7i43.dfs.core.windows.net/
  ├── raw/          ← Source files (CSV, JSONL)
  ├── bronze/       ← Delta tables (raw + metadata)
  ├── silver/       ← Delta tables (cleaned)
  ├── gold/         ← Delta/Parquet (analytics)
  │   └── exports/  ← Parquet files for API consumption
  │       ├── customer_360/
  │       ├── claims_analytics/
  │       ├── monthly_kpis/
  │       ├── risk_scoring/
  │       └── provider_performance/
  └── checkpoints/  ← Streaming checkpoints

  Direct ADLS Gen2 URLs:
  # Raw data
  abfss://raw@petinsud7i43.dfs.core.windows.net/

  # Bronze layer
  abfss://bronze@petinsud7i43.dfs.core.windows.net/

  # Gold exports (what API reads)
  abfss://gold@petinsud7i43.dfs.core.windows.net/exports/

3. Azure Storage Account Location

  The storage account name is: petinsud7i43

  To navigate in Azure Portal:

  1. Go to: https://portal.azure.com
  2. Search for: petinsud7i43 in the top search bar
  3. Or navigate: Home → Storage accounts → petinsud7i43

  Containers in this storage account:
  petinsud7i43.dfs.core.windows.net/
  ├── raw/          ← Source files (CSV, JSONL)
  ├── bronze/       ← Delta tables (raw + metadata)
  ├── silver/       ← Delta tables (cleaned)
  ├── gold/         ← Delta/Parquet (analytics)
  │   └── exports/  ← Parquet files for API consumption
  │       ├── customer_360/
  │       ├── claims_analytics/
  │       ├── monthly_kpis/
  │       ├── risk_scoring/
  │       └── provider_performance/
  └── checkpoints/  ← Streaming checkpoints

  Direct ADLS Gen2 URLs:
  # Raw data
  abfss://raw@petinsud7i43.dfs.core.windows.net/

  # Bronze layer
  abfss://bronze@petinsud7i43.dfs.core.windows.net/

  # Gold exports (what API reads)
  abfss://gold@petinsud7i43.dfs.core.windows.net/exports/



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
| Claims Data API | http://localhost:8000 | **Unified API Gateway** |
| AI Claims | http://localhost:8002 | Fraud detection |
| Integration | http://localhost:8003 | Mock EIS APIs |
| Rating Engine | http://localhost:8005 | Premium calculation |
| Agent Pipeline | http://localhost:8006 | Medallion processing |
| DocGen | http://localhost:8007 | Document processing |
| Admin Backend | http://localhost:8008 | Admin API (local only) |
| Agent Portal | http://localhost:8080 | Claims agents UI |
| Admin Portal | http://localhost:8081 | Admin UI |

---

## Claims Data API - Unified Gateway (Port 8000)

The Claims Data API serves as the **single unified gateway** for all backend services in AWS deployment. It consolidates endpoints from multiple services to simplify deployment and reduce infrastructure complexity.

### Registered Service Routers

| Router | Prefix | Description |
|--------|--------|-------------|
| PolicyService | `/api/v1/policies` | Policy management (6 endpoints) |
| CustomerService | `/api/v1/customers` | Customer data (6 endpoints) |
| PetService | `/api/v1/pets` | Pet records (5 endpoints) |
| ProviderService | `/api/v1/providers` | Vet provider data (5 endpoints) |
| FraudService | `/api/v1/fraud` | Fraud detection (6 endpoints) |
| MedicalRefService | `/api/v1/medical` | Medical codes (5 endpoints) |
| BillingService | `/api/v1/billing` | Billing records (5 endpoints) |
| ValidationService | `/api/v1/validation` | AI-powered validation (7 endpoints) |
| RatingService | `/api/v1/rating` | Premium calculation (6 endpoints) |
| DocGenService | `/api/v1/docgen` | Document generation (8 endpoints) |
| AIConfigService | `/api/v1/claims/ai` | AI provider config (4 endpoints) |
| InsightsService | `/api/insights` | Analytics insights |
| PipelineService | `/api/pipeline` | Pipeline management |
| DataSourceService | `/api/data-source` | Data source toggle |
| **CostsService** | `/api/v1/costs` | Cloud cost monitoring (8 endpoints) |
| **AdminConfigService** | `/api/v1/config` | Admin configuration (15+ endpoints) |
| **ApprovalsService** | `/api/v1/approvals` | Approval workflows (6 endpoints) |
| **AuditService** | `/api/v1/audit` | Audit logging (6 endpoints) |
| ChatService | `/api/chat` | AI chat interface |
| DataLakeService | `/api/v1/datalake` | Data lake operations |

### AWS Deployment URLs

| Service | URL | Description |
|---------|-----|-------------|
| Claims Data API | https://9wvcjmrknc.us-east-1.awsapprunner.com | Unified backend gateway |
| PetInsure360 Backend | https://fucf3fwwwv.us-east-1.awsapprunner.com | Pipeline & WebSocket |
| Agent Pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com | LangGraph agents |
| EIS Agent Portal | http://eis-dynamics-frontend.s3-website-us-east-1.amazonaws.com | Agent UI |
| EIS Admin Portal | http://eis-admin-portal.s3-website-us-east-1.amazonaws.com | Admin UI |
| BI Dashboard | http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com | Analytics |
