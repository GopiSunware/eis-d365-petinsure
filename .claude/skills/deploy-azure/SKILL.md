---
name: deploy-azure
description: Deploy PetInsure360 to Azure using App Service, Storage, and Databricks. Use when deploying to Azure, uploading to blob storage, updating Azure services, or checking Azure deployment status.
allowed-tools: Read, Bash, Grep, Glob
---

# Azure Deployment for PetInsure360

## Overview

Deploy the PetInsure360 pet insurance data platform to Azure infrastructure:
- **App Service**: FastAPI backend with Socket.IO
- **Storage Account**: Static website (frontend) + ADLS Gen2 (data lake)
- **Databricks**: ETL pipelines (Bronze/Silver/Gold)
- **Synapse**: Serverless SQL queries
- **Key Vault**: Secrets management

## Live URLs

| Service | URL |
|---------|-----|
| Customer Portal | https://petinsure360frontend.z5.web.core.windows.net |
| Backend API | https://petinsure360-backend.azurewebsites.net |
| API Docs | https://petinsure360-backend.azurewebsites.net/docs |
| Databricks | https://adb-7405619408519767.7.azuredatabricks.net |

## Connection Setup

**First time?** See [CONNECTION.md](CONNECTION.md) for full authentication setup.

### Quick Connection Check
```bash
# Verify Azure access
az account show

# Test resource group access
az group show --name rg-petinsure360 --query name
```

## Quick Commands

### Check Deployment Status
```bash
# Backend health check
curl -s https://petinsure360-backend.azurewebsites.net/health

# Frontend check
curl -s -o /dev/null -w "%{http_code}" https://petinsure360frontend.z5.web.core.windows.net/

# Azure login status
az account show
```

### Deploy Backend
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend

# Create deployment package
zip -r deploy.zip app data requirements.txt .env .funcignore host.json -x "*.pyc" -x "*__pycache__*" -x "env_backend/*" -x "node_modules/*"

# Deploy to Azure App Service
az webapp deploy --resource-group rg-petinsure360 --name petinsure360-backend --src-path deploy.zip --type zip

# Restart (if needed)
az webapp restart --resource-group rg-petinsure360 --name petinsure360-backend
```

### Deploy Frontend
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/frontend

# Build
npm run build

# Deploy to Azure Storage Static Website
az storage blob upload-batch --account-name petinsure360frontend --destination '$web' --source dist --overwrite
```

### Deploy BI Dashboard
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/bi-dashboard

# Build
npm run build

# Deploy (if separate hosting)
az storage blob upload-batch --account-name petinsure360bi --destination '$web' --source dist --overwrite
```

## Infrastructure (Terraform)

Located in: `petinsure360/infra/main.tf`

### Initialize Infrastructure
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/infra
terraform init
terraform plan
terraform apply
```

### Azure Resources

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | rg-petinsure360 | Container for all resources |
| Storage Account | petinsud7i43 | ADLS Gen2 data lake |
| Storage Account | petinsure360frontend | Static website hosting |
| App Service | petinsure360-backend | FastAPI + Socket.IO |
| Databricks | petinsure360-databricks | ETL notebooks |
| Synapse | petins-syn-ud7i43 | Serverless SQL |
| Key Vault | petins-kv-ud7i43 | Secrets storage |
| Data Factory | petinsure360-adf | Orchestration |

### Storage Containers (Medallion)

| Container | Purpose |
|-----------|---------|
| raw | Incoming JSON/CSV files |
| bronze | Raw data with metadata |
| silver | Cleansed, deduplicated |
| gold | Business aggregations |

## Upload Data to ADLS

```bash
# Upload raw data
az storage blob upload-batch \
    --account-name petinsud7i43 \
    --destination raw \
    --source /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/data/raw

# List containers
az storage container list --account-name petinsud7i43 --output table
```

## Environment Variables

### Backend App Service
```bash
# Set environment variables
az webapp config appsettings set --resource-group rg-petinsure360 --name petinsure360-backend --settings \
    AZURE_STORAGE_KEY="<storage-key>" \
    USE_LOCAL_DATA="true" \
    AZURE_STORAGE_ACCOUNT="petinsud7i43"
```

### Required Variables
| Variable | Description |
|----------|-------------|
| AZURE_STORAGE_KEY | Storage account key for petinsud7i43 |
| USE_LOCAL_DATA | Use local CSV data (true/false) |
| AZURE_STORAGE_ACCOUNT | Storage account name |

## Databricks ETL

### Run Notebooks
```
01_bronze_ingestion.py    - Raw → Bronze
02_silver_transformations.py - Bronze → Silver
03_gold_aggregations.py   - Silver → Gold
04_verify_data.py         - Data verification
```

### Access Databricks
```bash
# Open Databricks workspace
az databricks workspace show --resource-group rg-petinsure360 --name petinsure360-databricks-dev
```

## Troubleshooting

### Check App Service Logs
```bash
az webapp log tail --resource-group rg-petinsure360 --name petinsure360-backend
```

### Check App Service Status
```bash
az webapp show --resource-group rg-petinsure360 --name petinsure360-backend --query "state"
```

### Restart App Service
```bash
az webapp restart --resource-group rg-petinsure360 --name petinsure360-backend
```

### Clear Static Website Cache
```bash
# Azure Storage doesn't require cache purge - files are updated immediately
az storage blob list --account-name petinsure360frontend --container-name '$web' --output table
```

### Check Storage Account
```bash
az storage account show --name petinsud7i43 --query "primaryEndpoints"
```

## Full Deployment Script

```bash
#!/bin/bash
# Full PetInsure360 deployment

echo "=== Deploying Backend ==="
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend
zip -r deploy.zip app data requirements.txt .env .funcignore host.json -x "*.pyc" -x "*__pycache__*" -x "env_backend/*"
az webapp deploy --resource-group rg-petinsure360 --name petinsure360-backend --src-path deploy.zip --type zip

echo "=== Deploying Frontend ==="
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/frontend
npm run build
az storage blob upload-batch --account-name petinsure360frontend --destination '$web' --source dist --overwrite

echo "=== Verifying ==="
curl -s https://petinsure360-backend.azurewebsites.net/health
curl -s -o /dev/null -w "Frontend: %{http_code}\n" https://petinsure360frontend.z5.web.core.windows.net/

echo "=== Done ==="
```

## Configuration

- Resource Group: `rg-petinsure360`
- Location: `West US 2` / `East US`
- Storage Account: `petinsud7i43`
- Frontend Storage: `petinsure360frontend`

## Cost Estimate

| Resource | Monthly Cost |
|----------|-------------|
| App Service (Basic) | ~$15-55 |
| Storage (10GB) | ~$2 |
| Databricks (10 hrs) | ~$15 |
| Synapse Serverless | ~$5 |
| Key Vault | ~$0.30 |
| **Total** | **~$40-80/month** |

## Demo Users

| Email | Customer ID |
|-------|-------------|
| demo@demologin.com | DEMO-001 |
| demo1@demologin.com | DEMO-002 |
| demo2@demologin.com | DEMO-003 |
