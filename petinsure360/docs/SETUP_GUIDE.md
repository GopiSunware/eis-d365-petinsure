# PetInsure360 - Azure Data Platform Setup Guide

## Overview

PetInsure360 is a comprehensive pet insurance data platform demonstrating the **Medallion Lakehouse Architecture** (Bronze → Silver → Gold) on Azure.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PetInsure360 Data Platform                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  API /   │───▶│  BRONZE  │───▶│  SILVER  │───▶│   GOLD   │             │
│   │ Customer │    │  (Raw)   │    │ (Clean)  │    │(Business)│             │
│   │  Portal  │    │          │    │          │    │          │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│        │               │               │               │                    │
│        │         ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐             │
│        │         │Delta Lake │   │Delta Lake │   │Delta Lake │             │
│        │         │  Tables   │   │  Tables   │   │  Tables   │             │
│        │         └───────────┘   └───────────┘   └───────────┘             │
│        │                                              │                     │
│        │                    DATABRICKS                │                     │
│        │                   ETL Pipeline               ▼                     │
│        │                                       ┌──────────┐                 │
│        │                                       │ Synapse  │                 │
│        │                                       │Serverless│                 │
│        │                                       └────┬─────┘                 │
│        │                                            │                       │
│        ▼                                            ▼                       │
│   ┌──────────┐                              ┌──────────────┐               │
│   │ Backend  │◀────────────────────────────▶│BI Dashboard  │               │
│   │  API     │      Real-time WebSocket     │   (React)    │               │
│   └──────────┘                              └──────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Processing Modes

PetInsure360 supports **two processing modes**:

### Option 1: Demo Mode (In-Memory with Persistence)
- Real-time claim submission via Customer Portal
- Interactive Bronze → Silver → Gold pipeline buttons
- Data persisted to Azure Blob Storage (survives restarts)
- Best for: Live demos, quick testing

### Option 2: ETL Mode (Databricks Notebooks)
- Full Databricks notebooks for Bronze → Silver → Gold
- Delta Lake tables with ACID transactions
- Production-grade data quality and transformations
- Synapse Serverless for SQL queries
- Best for: Production workloads, large data volumes

---

## Prerequisites

1. **Azure Subscription** (Personal or Enterprise)
2. **Azure CLI** installed and logged in
3. **Terraform** v1.0+ installed
4. **Python 3.9+** with pip
5. **Node.js 18+** for frontend development
6. **Databricks CLI** (for notebook deployment): `pip install databricks-cli`

---

## Step 1: Azure CLI Setup

### Install Azure CLI

**Windows (PowerShell):**
```powershell
winget install Microsoft.AzureCLI
```

**Mac:**
```bash
brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Login to Azure

```bash
# Login (opens browser)
az login

# Verify subscription
az account show

# List subscriptions (if you have multiple)
az account list --output table

# Set specific subscription
az account set --subscription "<subscription-id>"
```

---

## Step 2: Deploy Infrastructure with Terraform

### Navigate to infra directory

```bash
cd petinsure360/infra
```

### Initialize Terraform

```bash
terraform init
```

### Preview changes

```bash
terraform plan
```

### Deploy (this will create all Azure resources)

```bash
terraform apply
```

**Expected resources created:**
- Resource Group: `rg-petinsure360`
- Storage Account (ADLS Gen2): `petinsud7i43`
- Databricks Workspace: `petinsure360-databricks-dev`
- Synapse Workspace: `petinsure360-synapse-dev`
- Data Factory: `petinsure360-adf-dev`
- Key Vault: `petinsure360-kv-dev`

### Save outputs

```bash
# Get storage account key
terraform output -raw storage_account_key

# Get Databricks URL
terraform output databricks_workspace_url

# Get Synapse endpoint
terraform output synapse_sql_endpoint
```

---

## Step 3: Generate Synthetic Data

### Install Python dependencies

```bash
cd ../data
pip install pandas numpy
```

### Generate data

```bash
python generate_synthetic_data.py
```

**Expected output files in `data/raw/`:**
- `customers.csv` (~5,000 records)
- `pets.csv` (~6,500 records)
- `policies.csv` (~6,000 records)
- `vet_providers.csv` (~200 records)
- `claims.jsonl` (~15,000 records)

---

## Step 4: Upload Data to Azure Storage

### Using Azure CLI

```bash
# Get storage account name from Terraform output
STORAGE_ACCOUNT="petinsud7i43"

# Upload all raw files
az storage blob upload-batch \
    --account-name $STORAGE_ACCOUNT \
    --destination raw \
    --source ./raw \
    --auth-mode login
```

### Verify upload

```bash
az storage blob list \
    --account-name $STORAGE_ACCOUNT \
    --container-name raw \
    --output table
```

---

## Step 5: Configure Databricks (ETL Mode)

### Deploy Notebooks

Use the deployment script:

```bash
cd petinsure360/notebooks
chmod +x deploy_notebooks.sh
./deploy_notebooks.sh
```

Or manually:
1. Go to Azure Portal → Resource Groups → `rg-petinsure360`
2. Click on Databricks workspace
3. Click "Launch Workspace"
4. Import notebooks from `petinsure360/notebooks/`

### Create Cluster

1. In Databricks, go to **Compute** → **Create Cluster**
2. Settings:
   - **Name**: `PetInsure360-Demo-v2`
   - **Cluster Mode**: Single Node (for cost savings)
   - **Databricks Runtime**: 13.3 LTS (includes Spark 3.5)
   - **Node Type**: Standard_D4s_v3 (16GB, 4 cores)
   - **Auto-termination**: 60 minutes

**Current Active Cluster**: `PetInsure360-Demo-v2` (ID: `0101-204045-2fdc7837`)

### Configure Storage Access

In Databricks, create a new notebook and run:

```python
# Set up storage access
storage_account = "petinsud7i43"
storage_key = "<your-storage-key>"  # From Terraform output

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    storage_key
)

# Test access
dbutils.fs.ls(f"abfss://raw@{storage_account}.dfs.core.windows.net/")
```

### Run ETL Pipeline

Run notebooks in order:
1. `01_bronze_ingestion` - Loads raw data to Bronze Delta tables
2. `02_silver_transformations` - Cleans, validates, deduplicates to Silver
3. `03_gold_aggregations` - Creates business aggregations in Gold

**Delta Lake Tables Created:**

| Layer | Database | Tables |
|-------|----------|--------|
| Bronze | petinsure_bronze | customers_raw, pets_raw, policies_raw, claims_raw, vet_providers_raw |
| Silver | petinsure_silver | dim_customers, dim_pets, dim_policies, dim_vet_providers, fact_claims |
| Gold | petinsure_gold | customer_360_view, claims_analytics, monthly_kpis, cross_sell_recommendations, provider_performance, risk_scoring |

---

## Step 6: Configure Synapse Serverless

### Access Synapse Studio

1. Go to Azure Portal → Resource Groups → `rg-petinsure360`
2. Click on Synapse workspace
3. Click "Open Synapse Studio"

### Create External Tables

1. In Synapse Studio, go to **Develop** → **SQL scripts**
2. Create new script
3. Copy contents from `notebooks/synapse_gold_views.sql`
4. Update storage account name and SAS token
5. Run script to create views

### Test Queries

```sql
-- Test Customer 360
SELECT TOP 10 * FROM petinsure_gold.vw_customer_360;

-- Test Monthly KPIs
SELECT * FROM petinsure_gold.vw_monthly_kpis ORDER BY year_month DESC;

-- Test Executive Dashboard
SELECT * FROM petinsure_gold.vw_executive_dashboard;
```

---

## Step 7: Deploy Backend API

### Configure Environment

```bash
cd petinsure360/backend

# Create .env file
cat > .env << EOF
AZURE_STORAGE_ACCOUNT=petinsud7i43
AZURE_STORAGE_KEY=<your-storage-key>
AZURE_STORAGE_CONTAINER=raw
USE_LOCAL_DATA=true
EOF
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### Deploy to Azure App Service

```bash
# Create deployment package
zip -r backend-deploy.zip app/ data/ requirements.txt

# Deploy
az webapp deployment source config-zip \
    --resource-group rg-petinsure360 \
    --name petinsure360-backend \
    --src backend-deploy.zip
```

---

## Step 8: Deploy BI Dashboard

### Install Dependencies

```bash
cd petinsure360/bi-dashboard
npm install
```

### Configure API Endpoint

Edit `src/services/api.js`:
```javascript
const API_BASE_URL = 'https://petinsure360-backend.azurewebsites.net';
```

### Build for Production

```bash
npm run build
```

### Deploy to Azure Blob Storage

```bash
az storage blob upload-batch \
    --account-name petinsure360bi \
    --destination '$web' \
    --source dist/ \
    --overwrite
```

---

## Step 9: Deploy Customer Portal (Optional)

```bash
cd petinsure360/frontend
npm install
npm run build

az storage blob upload-batch \
    --account-name petinsure360frontend \
    --destination '$web' \
    --source dist/ \
    --overwrite
```

---

## Deployed URLs (Updated 2026-01-01)

| Component | URL | Status |
|-----------|-----|--------|
| Customer Portal | https://petinsure360frontend.z5.web.core.windows.net | LIVE |
| Backend API | https://petinsure360-backend.azurewebsites.net | LIVE |
| API Docs | https://petinsure360-backend.azurewebsites.net/docs | LIVE |
| Databricks | https://adb-7405619408519767.7.azuredatabricks.net | LIVE |
| Synapse Studio | https://web.azuresynapse.net | Ready |

---

## Demo Mode Usage

### Submit a Claim
1. Open Customer Portal or BI Dashboard Pipeline page
2. Fill in claim details
3. Click Submit → Claim goes to Bronze layer

### Process Through Layers
1. **Bronze → Silver**: Click button to validate and clean data
2. **Silver → Gold**: Click button to aggregate and enrich
3. View results in Customer 360, Risk Analysis, Claims Analytics pages

### Data Persistence
- Demo data is automatically persisted to Azure Blob Storage
- Data survives backend restarts
- Clear demo data via Pipeline → Clear button

---

## Cost Management Tips

### Minimize Costs

1. **Databricks**: Use auto-termination (30 min), single-node cluster
2. **Synapse**: Serverless = pay-per-query only
3. **Storage**: Standard tier, LRS replication
4. **Shutdown when not using**: Pause Databricks cluster

### Estimated Monthly Cost (Dev/Demo)

| Resource | Estimated Cost |
|----------|---------------|
| Storage (10GB) | ~$2 |
| Databricks (10 hrs/month) | ~$15 |
| Synapse Serverless (1TB queries) | ~$5 |
| App Service (Basic) | ~$13 |
| Key Vault | ~$0.30 |
| **Total** | **~$35/month** |

### Clean Up Resources

```bash
# Destroy all resources when done
cd infra
terraform destroy
```

---

## Troubleshooting

### Databricks can't access storage
- Verify storage account key is correct
- Check container permissions
- Ensure firewall allows Databricks IPs

### Synapse views return empty
- Verify Delta tables exist in Gold container
- Check external data source credentials
- Ensure path matches Databricks output location

### Demo data not appearing after restart
- Check Azure Storage for demo/ folder
- Verify AZURE_STORAGE_KEY is set correctly
- Check backend logs for loading errors

### Power BI connection fails
- Verify Azure AD permissions
- Check Synapse firewall rules
- Ensure your IP is whitelisted

---

## Project Structure

```
petinsure360/
├── backend/                 # FastAPI backend with WebSocket
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── models/         # Pydantic schemas
│   │   └── services/       # Business logic
│   └── data/               # Sample data files
├── frontend/               # Customer Portal (React)
├── bi-dashboard/           # BI Analytics Dashboard (React)
├── notebooks/              # Databricks ETL notebooks
│   ├── 01_bronze_ingestion.py
│   ├── 02_silver_transformations.py
│   ├── 03_gold_aggregations.py
│   ├── synapse_gold_views.sql
│   └── deploy_notebooks.sh
├── infra/                  # Terraform infrastructure
└── docs/                   # Documentation
```

---

## Support

For questions or issues, contact:
- **Company**: Sunware Technologies
- **Email**: info@sunwaretechnologies.com
- **Website**: https://sunwaretechnologies.com
