# Azure Connection Guide

## Prerequisites

1. **Azure CLI** installed
2. **Node.js** (for frontend builds)
3. **Python 3.11+** (for backend)
4. **Terraform** installed (for infrastructure changes)

## Authentication Setup

### Step 1: Login to Azure

```bash
# Interactive login (opens browser)
az login

# Or use device code flow
az login --use-device-code

# For service principal (CI/CD)
az login --service-principal -u CLIENT_ID -p CLIENT_SECRET --tenant TENANT_ID
```

### Step 2: Set Subscription

```bash
# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription "YOUR_SUBSCRIPTION_NAME"

# Verify
az account show
```

### Step 3: Verify Connection

```bash
# Test resource access
az group show --name rg-petinsure360

# Expected output with resource group details
```

## Environment Variables

Create/update `.env` in `petinsure360/backend/`:

```bash
# ===========================================
# AZURE STORAGE (Required)
# ===========================================
AZURE_STORAGE_ACCOUNT=petinsud7i43
AZURE_STORAGE_KEY=your-storage-key-here
AZURE_STORAGE_CONTAINER=raw

# ===========================================
# API CONFIGURATION
# ===========================================
API_HOST=0.0.0.0
API_PORT=3002
DEBUG=true

# ===========================================
# DATA PATH
# ===========================================
DATA_PATH=../data/raw

# ===========================================
# INTEGRATION (Optional)
# ===========================================
AGENT_PIPELINE_URL=https://bn9ymuxtwp.us-east-1.awsapprunner.com
DOCGEN_SERVICE_URL=http://localhost:8007
```

## Azure Resources & Endpoints

| Resource | Name | Purpose |
|----------|------|---------|
| **Resource Group** | `rg-petinsure360` | Container |
| **Storage (Data)** | `petinsud7i43` | ADLS Gen2 data lake |
| **Storage (Frontend)** | `petinsure360frontend` | Static website |
| **App Service** | `petinsure360-backend` | FastAPI backend |
| **Databricks** | `petinsure360-databricks` | ETL notebooks |
| **Synapse** | `petins-syn-ud7i43` | Serverless SQL |
| **Key Vault** | `petins-kv-ud7i43` | Secrets |

### Live URLs

| Service | URL |
|---------|-----|
| Frontend | https://petinsure360frontend.z5.web.core.windows.net |
| Backend | https://petinsure360-backend.azurewebsites.net |
| API Docs | https://petinsure360-backend.azurewebsites.net/docs |
| Databricks | https://adb-7405619408519767.7.azuredatabricks.net |

## Get Storage Account Key

```bash
# Method 1: Azure CLI
az storage account keys list \
  --account-name petinsud7i43 \
  --resource-group rg-petinsure360 \
  --query '[0].value' -o tsv

# Method 2: From Key Vault
az keyvault secret show \
  --vault-name petins-kv-ud7i43 \
  --name storage-account-key \
  --query value -o tsv
```

## Storage Account Access

```bash
# List containers
az storage container list --account-name petinsud7i43 --output table

# List blobs in raw container
az storage blob list --account-name petinsud7i43 --container-name raw --output table

# Upload file
az storage blob upload \
  --account-name petinsud7i43 \
  --container-name raw \
  --name test.json \
  --file ./test.json
```

## App Service Management

```bash
# Check status
az webapp show --resource-group rg-petinsure360 --name petinsure360-backend --query state

# View logs
az webapp log tail --resource-group rg-petinsure360 --name petinsure360-backend

# Restart
az webapp restart --resource-group rg-petinsure360 --name petinsure360-backend

# Set environment variables
az webapp config appsettings set \
  --resource-group rg-petinsure360 \
  --name petinsure360-backend \
  --settings KEY=VALUE
```

## Static Website (Frontend)

```bash
# Enable static website (one-time)
az storage blob service-properties update \
  --account-name petinsure360frontend \
  --static-website \
  --index-document index.html \
  --404-document index.html

# Upload files
az storage blob upload-batch \
  --account-name petinsure360frontend \
  --destination '$web' \
  --source ./dist \
  --overwrite

# Get website URL
az storage account show \
  --name petinsure360frontend \
  --query "primaryEndpoints.web" -o tsv
```

## Databricks Access

```bash
# Get workspace URL
az databricks workspace show \
  --resource-group rg-petinsure360 \
  --name petinsure360-databricks-dev \
  --query workspaceUrl -o tsv

# Generate access token (via UI or REST API)
# Navigate to: User Settings > Developer > Access Tokens
```

## Terraform State

```bash
cd petinsure360/infra

# Initialize
terraform init

# Check current state
terraform show

# View outputs
terraform output

# Get storage key from output
terraform output -raw storage_account_key
```

## Common Issues

### "AuthorizationFailed"
```bash
# Check current account
az account show

# Re-login
az login

# Check role assignments
az role assignment list --assignee YOUR_EMAIL --output table
```

### "Storage account key expired"
```bash
# Regenerate key
az storage account keys renew \
  --account-name petinsud7i43 \
  --resource-group rg-petinsure360 \
  --key primary

# Update .env with new key
```

### "App Service deployment failed"
```bash
# Check deployment logs
az webapp log deployment show \
  --resource-group rg-petinsure360 \
  --name petinsure360-backend

# Check application logs
az webapp log tail \
  --resource-group rg-petinsure360 \
  --name petinsure360-backend
```

### "Static website not updating"
```bash
# Clear and re-upload
az storage blob delete-batch \
  --account-name petinsure360frontend \
  --source '$web'

az storage blob upload-batch \
  --account-name petinsure360frontend \
  --destination '$web' \
  --source ./dist \
  --overwrite
```

## Quick Connection Test

Run this script to verify all connections:

```bash
echo "=== Azure Connection Test ==="

echo "1. Account:"
az account show --query "{Name:name, State:state}" -o table

echo "2. Resource Group:"
az group show --name rg-petinsure360 --query "{Name:name, Location:location}" -o table

echo "3. Storage Accounts:"
az storage account list --resource-group rg-petinsure360 --query "[].{Name:name, Kind:kind}" -o table

echo "4. App Service:"
az webapp show --resource-group rg-petinsure360 --name petinsure360-backend --query "{Name:name, State:state, URL:defaultHostName}" -o table

echo "5. Databricks:"
az databricks workspace show --resource-group rg-petinsure360 --name petinsure360-databricks-dev --query "{Name:name, URL:workspaceUrl}" -o table

echo "=== Done ==="
```

## Service Principal (For CI/CD)

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "petinsure360-deploy" \
  --role contributor \
  --scopes /subscriptions/SUBSCRIPTION_ID/resourceGroups/rg-petinsure360

# Output:
# {
#   "appId": "CLIENT_ID",
#   "password": "CLIENT_SECRET",
#   "tenant": "TENANT_ID"
# }

# Login with SP
az login --service-principal \
  -u CLIENT_ID \
  -p CLIENT_SECRET \
  --tenant TENANT_ID
```
