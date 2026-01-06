# Common Issues & Solutions

## Backend Issues

### 1. Service Won't Start

**Symptoms**: `uvicorn` fails to start, port already in use

**Local Fix**:
```bash
# Find and kill process on port
lsof -ti :8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

**Verify**:
```bash
curl http://localhost:8000/health
```

---

### 2. Import Errors

**Symptoms**: `ModuleNotFoundError`, `ImportError`

**Local Fix**:
```bash
# Activate virtual environment
source venv/bin/activate  # or env_backend/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

**Verify**:
```bash
python -c "from app.main import app; print('OK')"
```

---

### 3. API Key Not Found

**Symptoms**: `ANTHROPIC_API_KEY not set`, AI calls failing

**Local Fix**:
```bash
# Check .env file
cat .env | grep API_KEY

# Ensure .env is loaded
python -c "from app.config import get_settings; print(get_settings().ANTHROPIC_API_KEY[:20])"
```

**Cloud Fix**:
```bash
# AWS - Check Secrets Manager
aws secretsmanager get-secret-value --secret-id eis-dynamics/api-keys --profile sunwaretech

# Azure - Check App Settings
az webapp config appsettings list --resource-group rg-petinsure360 --name petinsure360-backend
```

---

### 4. CORS Errors

**Symptoms**: Browser shows CORS error, API works in Postman but not browser

**Local Fix**:
```bash
# Update .env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

**Code Fix** (if needed):
```python
# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Verify**:
```bash
curl -H "Origin: http://localhost:3000" -I http://localhost:8000/api/endpoint
# Should see Access-Control-Allow-Origin header
```

---

### 5. Database/Storage Connection Failed

**Symptoms**: `ConnectionError`, `StorageAccountNotFound`

**Local Fix**:
```bash
# Check storage config
cat .env | grep -E "STORAGE|AZURE|AWS"

# Test Azure connection
az storage container list --account-name petinsud7i43

# Test AWS connection
aws s3 ls --profile sunwaretech | grep eis-dynamics
```

---

## Frontend Issues

### 6. Build Failures

**Symptoms**: `npm run build` fails, TypeScript errors

**Local Fix**:
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

**Verify**:
```bash
npm run dev
# Open http://localhost:3000
```

---

### 7. Environment Variables Not Loading

**Symptoms**: `NEXT_PUBLIC_*` variables undefined

**Local Fix**:
```bash
# Check .env.local exists
cat .env.local

# Ensure NEXT_PUBLIC_ prefix
# Wrong: API_URL=http://localhost:8000
# Right: NEXT_PUBLIC_API_URL=http://localhost:8000

# Restart dev server after .env changes
npm run dev
```

---

### 8. WebSocket Connection Failed

**Symptoms**: Real-time updates not working, WS connection errors

**Local Fix**:
```bash
# Check WebSocket URL
cat .env.local | grep WS_URL

# Ensure backend supports WebSocket
curl -I http://localhost:8006/ws
```

**Code Check**:
```javascript
// Should use ws:// for local, wss:// for production
const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8006'
```

---

## Deployment Issues

### 9. AWS Deployment Failed

**Symptoms**: Docker push failed, App Runner not updating

**Fix**:
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 --profile sunwaretech | \
  docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Force new deployment
aws apprunner start-deployment --service-arn <arn> --profile sunwaretech
```

**Verify**:
```bash
curl https://p7qrmgi9sp.us-east-1.awsapprunner.com/health
```

---

### 10. Azure Deployment Failed

**Symptoms**: Deployment times out, app not responding

**Fix**:
```bash
# Check deployment status
az webapp deployment list --resource-group rg-petinsure360 --name petinsure360-backend

# Restart app
az webapp restart --resource-group rg-petinsure360 --name petinsure360-backend

# Check logs
az webapp log tail --resource-group rg-petinsure360 --name petinsure360-backend
```

**Verify**:
```bash
curl https://petinsure360-backend.azurewebsites.net/health
```

---

## Data Issues

### 11. Claims Data Not Loading

**Symptoms**: Empty responses, 404 on data endpoints

**Local Fix**:
```bash
# Check data directory
ls -la data/
ls -la src/shared/claims_data_api/data/

# Verify JSON files
python -c "import json; json.load(open('data/claims.json'))"
```

---

### 12. Pipeline Processing Stuck

**Symptoms**: Claims stuck in Bronze, not progressing to Gold

**Local Fix**:
```bash
# Check pipeline status
curl http://localhost:8006/api/v1/pipeline/status

# Clear and retry
curl -X POST http://localhost:8006/api/v1/pipeline/clear
curl -X POST http://localhost:8006/api/v1/pipeline/process
```

---

## Quick Diagnostic Commands

```bash
# Full system check
./scripts/diagnose.sh

# Check all services
for port in 8000 8001 8002 8003 8006 8007 3000; do
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null || echo "DOWN"
done

# Check environment
python -c "from app.config import get_settings; s=get_settings(); print(f'ENV={s.ENVIRONMENT}, DEBUG={s.DEBUG}')"
```
