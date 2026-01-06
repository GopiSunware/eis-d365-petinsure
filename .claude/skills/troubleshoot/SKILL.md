---
name: troubleshoot
description: Debug and fix issues in pet insurance projects. Follows local-first workflow - fix locally, test, get user confirmation, then deploy to cloud. Use when debugging errors, fixing bugs, services not working, or deployment issues.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Troubleshooting Workflow

## Golden Rule

**Fix Local → Test Local → User Confirms → Deploy to Cloud**

Never deploy broken code. Always verify fixes locally first.

## Quick Diagnosis

### Check Service Health
```bash
# EIS-Dynamics (AWS)
curl -s https://p7qrmgi9sp.us-east-1.awsapprunner.com/ | head -5
curl -s https://bn9ymuxtwp.us-east-1.awsapprunner.com/api/v1/scenarios/ | head -5

# PetInsure360 (Azure)
curl -s https://petinsure360-backend.azurewebsites.net/health
curl -s -o /dev/null -w "%{http_code}" https://petinsure360frontend.z5.web.core.windows.net/
```

### Check Local Services
```bash
# Check if ports are in use
lsof -i :8000 -i :8006 -i :3000 2>/dev/null || netstat -tlnp 2>/dev/null | grep -E "8000|8006|3000"

# Check running Python processes
ps aux | grep -E "uvicorn|python" | grep -v grep
```

## Troubleshooting Workflow

### Step 1: Identify Environment
```
Where is the issue?
├── LOCAL  → Fix locally first
├── CLOUD  → Reproduce locally, fix, then deploy
└── BOTH   → Start with local
```

### Step 2: Reproduce Locally
```bash
# Start local services
cd eis-dynamics-poc
./run.sh  # Or start individual services

# Test the failing scenario
curl http://localhost:8000/health
```

### Step 3: Fix & Test Locally
```bash
# Make code changes
# ...

# Test locally
python -m pytest tests/
curl http://localhost:8000/your-endpoint
```

### Step 4: Get User Confirmation
```
ASK USER:
"I've fixed [issue] locally. The fix was [description].
Local tests pass. Ready to deploy to [AWS/Azure]?"
```

### Step 5: Deploy to Cloud
```bash
# AWS (EIS-Dynamics)
./deploy-aws.sh build && ./deploy-aws.sh push

# Azure (PetInsure360)
cd backend && zip -r deploy.zip app data requirements.txt
az webapp deploy --resource-group rg-petinsure360 --name petinsure360-backend --src-path deploy.zip
```

### Step 6: Verify Cloud Deployment
```bash
# Check cloud health after deploy
curl -s https://your-service-url/health
```

## Common Issues & Fixes

See [COMMON_ISSUES.md](COMMON_ISSUES.md) for detailed solutions.

### Quick Reference

| Issue | Local Check | Cloud Check |
|-------|-------------|-------------|
| Service not starting | `lsof -i :PORT` | Check App Runner/App Service logs |
| API returning 500 | Check terminal logs | `az webapp log tail` / CloudWatch |
| CORS errors | Check CORS_ORIGINS in .env | Check deployed env vars |
| Auth failures | Check API keys in .env | Check Secrets Manager/Key Vault |
| Database errors | Check connection string | Check cloud DB connectivity |

## Debug Commands

### Python Backend
```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload --port 8000

# Check for import errors
python -c "from app.main import app"

# Run specific test
python -m pytest tests/test_api.py -v -s
```

### Next.js Frontend
```bash
# Development mode with errors
npm run dev

# Check for build errors
npm run build

# Check TypeScript errors
npx tsc --noEmit
```

### Docker
```bash
# Build and check for errors
docker build -t test-image .

# Run interactively
docker run -it --rm test-image /bin/bash

# Check container logs
docker logs <container-id>
```

## Log Locations

### Local
```
Backend: Terminal output (stdout/stderr)
Frontend: Browser console + terminal
```

### Cloud
```bash
# AWS App Runner
aws logs tail /aws/apprunner/eis-dynamics-unified-api --follow --profile sunwaretech

# Azure App Service
az webapp log tail --resource-group rg-petinsure360 --name petinsure360-backend
```

## Diagnostic Script

Run comprehensive diagnostics:
```bash
python scripts/diagnose.py
```
