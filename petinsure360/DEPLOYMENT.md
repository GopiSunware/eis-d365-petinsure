# PetInsure360 - Deployment Guide

## Tech Stack (STRICTLY FOLLOW)

### Frontend
- **Framework**: React + Vite
- **Hosting**: Azure Storage Static Website
- **Storage Account**: `petinsure360frontend`
- **URL**: https://petinsure360frontend.z5.web.core.windows.net/
- **NO CDN** - Files served directly from Azure Storage

### Backend
- **Framework**: Python FastAPI + Socket.IO
- **Hosting**: Azure App Service (Linux)
- **App Name**: `petinsure360-backend`
- **Resource Group**: `rg-petinsure360`
- **URL**: https://petinsure360-backend.azurewebsites.net/

### Data Storage
- **Azure Blob Storage**: `petinsud7i43`
- **Container**: `raw`
- **Purpose**: Medallion Lakehouse (Bronze/Silver/Gold layers)

### Database
- **Local Data**: CSV/JSONL files in `backend/data/raw/`
- **Demo Persistence**: Azure Blob Storage (`demo/` folder)

---

## Deployment Commands

### Prerequisites
```bash
az login
```

### Deploy Backend
```bash
cd backend

# Create deployment package (exclude venv folders)
zip -r deploy.zip app data requirements.txt .env .funcignore host.json -x "*.pyc" -x "*__pycache__*"

# Deploy to Azure App Service
az webapp deploy --resource-group rg-petinsure360 --name petinsure360-backend --src-path deploy.zip --type zip

# Restart (optional)
az webapp restart --resource-group rg-petinsure360 --name petinsure360-backend
```

### Deploy Frontend
```bash
cd frontend

# Build
npm run build

# Deploy to Azure Storage Static Website
az storage blob upload-batch --account-name petinsure360frontend --destination '$web' --source dist --overwrite
```

### Verify Deployment
```bash
# Backend health check
curl https://petinsure360-backend.azurewebsites.net/health

# Frontend check
curl -s -o /dev/null -w "%{http_code}" https://petinsure360frontend.z5.web.core.windows.net/
```

---

## Environment Variables (Backend)

Required in Azure App Service Configuration:
- `AZURE_STORAGE_KEY` - Storage account key for petinsud7i43
- `USE_LOCAL_DATA` - Set to `true` for local CSV data

---

## Important Notes

1. **NO Cloudflare** - This project uses Azure services only
2. **NO CDN** - Frontend served directly from Azure Storage
3. **Cache**: Azure Storage handles caching; no manual purge needed
4. **Demo Data**: Persisted to Azure Blob Storage, loaded on startup

---

## Demo Users

| Email | Customer ID | Name |
|-------|-------------|------|
| demo@demologin.com | DEMO-001 | Demo User |
| demo1@demologin.com | DEMO-002 | Demo One |
| demo2@demologin.com | DEMO-003 | Demo Two |
