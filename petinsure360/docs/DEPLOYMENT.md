# PetInsure360 Azure Deployment Guide

## Deployment Status (2026-01-01) - FULLY LIVE

### Successfully Deployed Components

| Component | URL | Status |
|-----------|-----|--------|
| Frontend Portal | https://petinsure360frontend.z5.web.core.windows.net | **LIVE** |
| Backend API | https://petinsure360-backend.azurewebsites.net | **LIVE** |
| API Docs | https://petinsure360-backend.azurewebsites.net/docs | **LIVE** |
| Health Check | https://petinsure360-backend.azurewebsites.net/health | **LIVE** |
| Databricks Workspace | https://adb-7405619408519767.7.azuredatabricks.net | **LIVE** |
| Databricks Cluster | PetInsure360-Demo-v2 | **RUNNING** |

### Current Features

- **Pipeline Visualization Page**: Visual representation of Medallion architecture (Bronze→Silver→Gold) at `/pipeline`
- **20 Pre-built Claim Scenarios**: Quick-fill realistic claim data (chocolate toxicity, ACL surgery, cancer treatment, etc.)
- **Manual Pipeline Triggers**: Click to process claims through Bronze→Silver→Gold layers
- **Real-time WebSocket Updates**: Dashboard auto-refreshes when users submit claims
- **Customer 360 View**: Unified customer profiles with risk scoring and segmentation
- **Claims Analytics**: Full claims analysis with filtering and drill-down
- **Connection Status Indicator**: Shows live/offline status in dashboard header
- **SPA Routing**: All client-side routes work correctly with Azure Static Websites

### Demo Data (Loaded on Backend)

| Data Type | Count | Description |
|-----------|-------|-------------|
| Customers | 5,000 | Diverse customer profiles |
| Pets | 6,500 | Dogs, cats, exotic pets |
| Policies | 6,000 | Various coverage types |
| Claims | 15,000 | All statuses and categories |
| Providers | 200 | Veterinary network |

### Azure Resources

| Resource Name | Resource Type | Location | SKU/Tier |
|---------------|---------------|----------|----------|
| petinsure360frontend | Storage Account (Static Web) | West US 2 | Standard |
| petinsure360bi | Storage Account (Static Web) | West US 2 | Standard |
| petinsure360-backend | Azure Web App | UK West | B1 Basic |
| petinsure360-plan | App Service Plan | UK West | B1 Basic |
| rg-petinsure360 | Resource Group | West US 2 | - |

### Existing Data Platform Resources

| Resource Name | Resource Type | Purpose |
|---------------|---------------|---------|
| petinsud7i43 | Storage Account (ADLS Gen2) | Data Lake Storage |
| petinsuredatabricks | Azure Databricks | Data Processing |
| petinsuresynapse | Azure Synapse | Analytics |
| petinsurekv | Azure Key Vault | Secrets Management |

---

## Backend API Overview

### What the Backend Does

The PetInsure360 backend is a **FastAPI application** that serves as the data ingestion and BI insights API layer. It provides:

#### 1. Data Ingestion Endpoints
- `POST /api/customers` - Create/update customer records
- `POST /api/pets` - Register pet information
- `POST /api/policies` - Create insurance policies
- `POST /api/claims` - Submit insurance claims

#### 2. BI Insights Endpoints (Read from Gold Layer)
- `GET /api/insights/kpis` - Monthly KPI metrics
- `GET /api/insights/segments` - Customer segmentation data
- `GET /api/insights/summary` - Dashboard summary statistics
- `GET /api/insights/customers` - Customer 360 profiles
- `GET /api/insights/claims` - Claims analytics
- `GET /api/insights/risks` - Risk score analysis
- `GET /api/insights/cross-sell` - Cross-sell recommendations

#### 3. Real-time Features
- WebSocket support via Socket.IO for live updates
- Claim status change notifications
- Real-time dashboard refresh

#### 4. Storage Integration
- Writes to Azure Data Lake Storage Gen2 (Bronze layer)
- Reads from Gold layer Parquet files via Azure Synapse

### Dependencies
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-socketio==5.10.0
azure-storage-blob==12.19.0
azure-identity==1.15.0
pydantic[email]==2.5.3
pandas==2.1.4
httpx==0.26.0
gunicorn==21.2.0
```

---

## Deployment Issues Encountered

### 1. Azure VM Quota Limitations
- **Error**: "Operation cannot be completed without additional quota"
- **Affected Regions**: West US 2, East US
- **Affected SKUs**: Basic VMs, Free VMs
- **Resolution**: Deployed App Service Plan in UK West

### 2. Azure Functions ASGI Integration
- **Issue**: Function app showing default page instead of FastAPI routes
- **Cause**: Python V2 programming model configuration
- **Status**: Requires Azure Functions Core Tools for proper deployment

### 3. Web App Build Configuration
- **Issue**: Oryx build not installing Python dependencies
- **Cause**: Deployment method not triggering pip install
- **Status**: Build process needs refinement

---

## Alternative Deployment Options

### Option 1: Local Development Server
Run the backend locally for development/demo:
```bash
cd petinsure360/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:socket_app --host 0.0.0.0 --port 8000
```
Then update frontend API URL to `http://localhost:8000`

### Option 2: Azure Container Instances (ACI)
Deploy as a Docker container:
```bash
# Build and push to Azure Container Registry
az acr create --resource-group rg-petinsure360 --name petinsure360acr --sku Basic
az acr build --registry petinsure360acr --image petinsure360-api:v1 ./backend

# Deploy to ACI
az container create \
  --resource-group rg-petinsure360 \
  --name petinsure360-api \
  --image petinsure360acr.azurecr.io/petinsure360-api:v1 \
  --ports 8000 \
  --dns-name-label petinsure360-api
```

### Option 3: Azure Container Apps
Serverless container hosting with auto-scaling:
```bash
az containerapp create \
  --name petinsure360-api \
  --resource-group rg-petinsure360 \
  --environment petinsure360-env \
  --image petinsure360acr.azurecr.io/petinsure360-api:v1 \
  --target-port 8000 \
  --ingress external
```

### Option 4: Azure Web App (CURRENT - RECOMMENDED)
Azure Web App with Oryx build system - currently deployed and working.

**Deployment Steps:**
```bash
cd petinsure360/backend

# Create deployment zip (include data files for demo)
zip -r ../backend-deploy.zip app/ data/ requirements.txt Procfile runtime.txt

# Deploy to Azure Web App
az webapp deploy \
  --resource-group rg-petinsure360 \
  --name petinsure360-backend \
  --src-path ../backend-deploy.zip \
  --type zip
```

**Important**: The `data/raw/` folder must be included in the deployment for the demo data to work.

**Environment Variables (set in Azure Portal > Web App > Configuration):**
```
AZURE_STORAGE_ACCOUNT=petinsud7i43
AZURE_STORAGE_KEY=your-key
USE_LOCAL_DATA=true
```

After deployment, the API is available at:
- https://petinsure360-backend.azurewebsites.net
- https://petinsure360-backend.azurewebsites.net/docs (Swagger UI)

### Option 5: Static Demo Mode (No Backend)
The frontend already has fallback demo data. If the API is unavailable, the dashboards display sample data automatically.

---

## Updating Frontend API URLs

To point frontends to a different backend:

### Frontend Portal
Edit `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://YOUR-BACKEND-URL'
```

### BI Dashboard
Edit `bi-dashboard/src/services/api.js`:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://YOUR-BACKEND-URL'
```

Then rebuild and redeploy:
```bash
cd frontend && npm run build
cd bi-dashboard && npm run build
```

---

## Cost Considerations

| Service | Estimated Monthly Cost |
|---------|----------------------|
| Storage Accounts (Static Web) | ~$0.50 each |
| App Service Plan (B1) | ~$13/month |
| Azure Functions (Consumption) | Pay-per-execution |
| Container Instances | ~$30/month (always-on) |
| Container Apps | Pay-per-request |

**Recommendation**: For development/demo, use the static demo mode (free) or local backend. For production, consider Azure Container Apps for cost-effective scaling.

---

## Troubleshooting

### Frontend Not Loading
1. Check static website is enabled on storage account
2. Verify index.html exists in $web container
3. Check CORS settings if calling backend

### Backend API Errors
1. Check application logs: `az webapp log tail --name petinsure360-backend --resource-group rg-petinsure360`
2. Verify environment variables are set
3. Ensure startup command is correct

### CORS Issues
Add backend URL to allowed origins:
```bash
az webapp cors add --resource-group rg-petinsure360 --name petinsure360-backend --allowed-origins "*"
```

---

## Commands Reference

### Deploy Frontend Portal
```bash
cd frontend
npm run build
az storage blob upload-batch -d '$web' -s dist --account-name petinsure360frontend --overwrite
# Configure SPA routing
az storage blob service-properties update --account-name petinsure360frontend --static-website --404-document 404.html
```

### Deploy BI Dashboard
```bash
cd bi-dashboard
npm run build
az storage blob upload-batch -d '$web' -s dist --account-name petinsure360bi --overwrite
```

### Restart Backend
```bash
az webapp restart --name petinsure360-backend --resource-group rg-petinsure360
```

### View Logs
```bash
az webapp log download --name petinsure360-backend --resource-group rg-petinsure360 --log-file logs.zip
```

## STATUS SUMMARY (Updated 2026-01-01)

### Infrastructure (DEPLOYED ✅)

| Service            | Name                        | Status     |
|--------------------|-----------------------------|------------|
| Databricks         | petinsure360-databricks-dev | ✅ Running |
| Synapse            | petins-syn-ud7i43           | ✅ Running |
| Data Factory       | petinsure360-adf-dev        | ✅ Running |
| Data Lake          | petinsud7i43                | ✅ Running |
| Storage Containers | bronze/silver/gold/raw      | ✅ Created |

### ETL Notebooks (DEPLOYED ✅)

| Notebook                     | Purpose                   | Status               |
|------------------------------|---------------------------|----------------------|
| 01_bronze_ingestion.py       | Raw → Bronze Delta tables | ✅ Deployed & Run    |
| 02_silver_transformations.py | Bronze → Silver (cleaned) | ✅ Deployed & Run    |
| 03_gold_aggregations.py      | Silver → Gold (analytics) | ✅ Deployed & Run    |
| 04_delta_lake_demo.py        | Delta Lake features demo  | ✅ Deployed          |
| synapse_gold_views.sql       | Synapse external tables   | ✅ Updated           |

### Databricks Cluster

| Property | Value |
|----------|-------|
| Name | PetInsure360-Demo-v2 |
| Cluster ID | 0101-204045-2fdc7837 |
| Node Type | Standard_D4s_v3 |
| Runtime | 13.3 LTS |
| Auto-termination | 60 minutes |

### Data Status

| Layer  | Container | Status                                   |
|--------|-----------|------------------------------------------|
| Raw    | raw/      | ✅ Has data (45 files)                   |
| Bronze | bronze/   | ✅ ETL Complete (Databricks Metastore)   |
| Silver | silver/   | ✅ ETL Complete (Databricks Metastore)   |
| Gold   | gold/     | ✅ ETL Complete (39 Delta files in ADLS) |

### Gold Delta Tables in ADLS

| Table | Path | Records |
|-------|------|---------|
| customer_360_view | gold/customer_360_view | CDP unified view |
| claims_analytics | gold/claims_analytics | Detailed claims |
| monthly_kpis | gold/monthly_kpis | Executive metrics |
| cross_sell_recommendations | gold/cross_sell_recommendations | Upsell opportunities |
| provider_performance | gold/provider_performance | Vet analytics |
| risk_scoring | gold/risk_scoring | Risk assessment |

---

## Demo Instructions

### Show Delta Lake Features

1. Open Databricks: https://adb-7405619408519767.7.azuredatabricks.net
2. Navigate to **Workspace** → **Shared** → **PetInsure360**
3. Open **04_delta_lake_demo** notebook
4. Attach to cluster **PetInsure360-Demo-v2**
5. Run cells to demonstrate:
   - `DESCRIBE HISTORY` - Audit trail
   - Time Travel queries
   - Table details
   - Sample data queries