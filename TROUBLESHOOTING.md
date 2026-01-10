# Troubleshooting Guide

Common issues and solutions for the PetInsure360 and EIS Dynamics projects.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Pre-deployment validation & known issues |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture reference |
| [ENV_VARIABLES.md](ENV_VARIABLES.md) | Environment variable reference |
| [PORT_CONFIG.md](PORT_CONFIG.md) | Service ports & URLs |

---

## Pre-Deployment Validation

**Always run before deploying:**
```bash
./scripts/validate-deployment.sh
```

This script checks:
- Dockerfile copies synthetic data
- Environment files have AWS URLs (not localhost)
- Service ARNs are configured
- Required API services exist
- Demo login is configured

---

## CRITICAL: Complete Service List

**There are 12 total services that must be running for full functionality.**

### PetInsure360 (3 services)
| Port | Service | Entry Point | Notes |
|------|---------|-------------|-------|
| 3000 | Customer Portal | `npm run dev` | React/Vite UI |
| 3001 | BI Dashboard | `npm run dev` | React/Vite UI |
| 3002 | Backend API | `uvicorn app.main:socket_app` | **MUST use socket_app, NOT app** |

### EIS Dynamics Backend (7 services)
| Port | Service | Entry Point | Notes |
|------|---------|-------------|-------|
| 8000 | Claims Data API | `uvicorn app.main:app` | **Has Chat API endpoints** |
| 8002 | WS2 AI Claims | `uvicorn app.main:app` | Often forgotten! |
| 8003 | WS3 Integration | `uvicorn app.main:app` | EIS Mock proxy |
| 8005 | WS5 Rating Engine | `uvicorn app.main:app` | Often forgotten! |
| 8006 | WS6 Agent Pipeline | `uvicorn app.main:app` | LangGraph agents |
| 8007 | WS7 DocGen | `uvicorn app.main:app` | Often forgotten! |
| 8008 | WS8 Admin Backend | `uvicorn app.main:app` | Admin API |

### EIS Dynamics Frontend (2 services)
| Port | Service | Entry Point | Notes |
|------|---------|-------------|-------|
| 8080 | WS4 Agent Portal | `npm run dev` | Next.js UI |
| 8081 | WS8 Admin Portal | `npm run dev` | Next.js UI |

### Quick Status Check Script
```bash
for port in 3000 3001 3002 8000 8002 8003 8005 8006 8007 8008 8080 8081; do
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:$port/health 2>/dev/null)
  [ "$STATUS" = "000" ] && STATUS=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:$port/ 2>/dev/null)
  [ "$STATUS" = "200" ] && ICON="✅" || ICON="❌"
  echo "Port $port: $ICON ($STATUS)"
done
```

---

## PetInsure360 Issues

### 1. WebSocket Connection Failed

**Error:**
```
WebSocket connection to 'ws://localhost:3002/socket.io/?EIO=4&transport=websocket' failed
```

**Cause:** Backend started with `app` instead of `socket_app`. The Socket.IO wrapper is not active.

**Solution:** ALWAYS use `socket_app` entry point:
```bash
cd petinsure360/backend
source venv/bin/activate
uvicorn app.main:socket_app --host 0.0.0.0 --port 3002 --reload
#                ^^^^^^^^^^^ CRITICAL: Must be socket_app, NOT app
```

**Verify fix:**
```bash
# Health check - should show "websocket":"enabled"
curl http://localhost:3002/health

# Socket.IO check - should return JSON with "sid" and "upgrades":["websocket"]
curl 'http://localhost:3002/socket.io/?EIO=4&transport=polling'
```

**Root cause in code:** `app/main.py` line ~94:
```python
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
```

---

### 2. 307 Redirect on API Endpoints

**Error:** `GET /api/pets` returns 307 redirect to `/api/pets/`

**Cause:** FastAPI's default `redirect_slashes=True` behavior.

**Solution:** Fixed in `app/main.py`:
```python
app = FastAPI(..., redirect_slashes=False)
```

Plus dual route decorators in endpoint files:
```python
@router.get("/")
@router.get("")  # Handle both with and without trailing slash
async def list_items(...):
```

---

### 3. Schema Validation Errors (422)

**Error:** `422 Unprocessable Entity` on customer/claim creation

**Cause:** Frontend sends different field names than backend expects.

**Solution:** Use flexible schemas with aliases and helper methods in `app/models/schemas.py`:
- `CustomerCreate`: `address` alias for `address_line1`, optional `date_of_birth`
- `ClaimCreate`: `amount` alias for `claim_amount`, default `claim_category`, helper methods

---

## EIS Dynamics Issues

### 1. CORS Errors

**Error:**
```
Access to XMLHttpRequest at 'http://localhost:8003/api/v1/eis/policies' from origin 'http://localhost:8080'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Cause:** EIS backend services have empty `cors_origins` by default from `eis_common.config`.

**Solution:** Fixed in code - services now default to `["*"]` when `CORS_ORIGINS` env var is not set:
```python
# In each service's main.py
cors_origins = settings.cors_origins if settings.cors_origins else ["*"]
```

**Services that needed this fix:**
- `ws2_ai_claims/app/main.py`
- `ws3_integration/app/main.py`
- `ws5_rating_engine/app/main.py`

**Verify CORS:**
```bash
curl -I -X OPTIONS http://localhost:8003/api/v1/eis/policies \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: GET"
# Should show: access-control-allow-origin: http://localhost:8080
```

---

### 2. Chat API Provider Errors

**Error:**
```
GET http://localhost:8003/api/chat/providers 404 (Not Found)
GET http://localhost:8008/api/chat/providers 404 (Not Found)
Failed to fetch AI providers
```

**Cause:** Chat API endpoints are on port **8000** (Claims Data API), NOT on 8003 or 8008. Frontend was configured to call wrong ports.

**Solution:** Fixed in `ws4_agent_portal/lib/chatApi.ts`:
```typescript
// Chat API is on Claims Data API (port 8000) - separate from CLAIMS_API_URL (port 8003)
const API_BASE = process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:8000';
```

**Verify Chat API:**
```bash
curl http://localhost:8000/api/chat/providers
# Should return: {"providers":{"openai":{...},"anthropic":{...}},"enabled":[...],"default":"openai"}
```

**Key insight:** The Chat API lives on **Claims Data API (8000)**, not on Integration (8003) or Admin (8008).

---

### 3. Missing Services

**Symptom:** Various 404 errors or connection refused errors.

**Cause:** Not all 7 EIS backend services were started. Commonly missed:
- **8002** - WS2 AI Claims
- **8005** - WS5 Rating Engine
- **8007** - WS7 DocGen

**Solution:** Start ALL backend services. Use this script:
```bash
EIS_ROOT="/path/to/eis-dynamics-poc"

# Start all EIS backend services
for ws in "shared/claims_data_api:8000" "ws2_ai_claims:8002" "ws3_integration:8003" \
          "ws5_rating_engine:8005" "ws6_agent_pipeline:8006" "ws7_docgen:8007"; do
  DIR=$(echo $ws | cut -d: -f1)
  PORT=$(echo $ws | cut -d: -f2)
  cd "$EIS_ROOT" && source venv/bin/activate && \
    cd "src/$DIR" && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &
done

# Start WS8 Admin Backend (different path)
cd "$EIS_ROOT/src/ws8_admin_portal/backend" && \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 &
```

---

## API Endpoint Reference

### Chat API (Port 8000 - Claims Data API)
```
GET  /api/chat/providers  - List available AI providers
GET  /api/chat/status     - Check chat availability
POST /api/chat            - Send chat message
```

### Pipeline API (Port 8000 - Claims Data API)
```
GET    /api/pipeline/status   - Get pipeline status (mode: demo/cleared)
GET    /api/pipeline/pending  - Get pending claims by layer
GET    /api/pipeline/flow     - Get pipeline flow visualization
GET    /api/pipeline/metrics  - Get detailed pipeline metrics
POST   /api/pipeline/refresh  - Reload demo data (resets cleared state)
DELETE /api/pipeline/clear    - Clear all pending claims
POST   /api/pipeline/process/bronze-to-silver - Trigger Bronze→Silver
POST   /api/pipeline/process/silver-to-gold   - Trigger Silver→Gold
```

### Admin Config API (Port 8000 - Claims Data API)
```
GET  /api/v1/config/ai                    - Get AI configuration
PUT  /api/v1/config/ai                    - Update AI configuration
GET  /api/v1/config/ai/models             - List available AI models
GET  /api/v1/config/ai/history            - Get config change history
GET  /api/v1/config/claims                - Get claims config
PUT  /api/v1/config/claims                - Update claims config
GET  /api/v1/config/claims/auto-adjudication  - Auto-adjudication settings
GET  /api/v1/config/claims/fraud-detection    - Fraud detection settings
GET  /api/v1/config/policies              - Get policy config
GET  /api/v1/config/rating                - Get rating config
```

### Approvals API (Port 8000 - Claims Data API)
```
GET  /api/v1/approvals/stats              - Get approval statistics
GET  /api/v1/approvals/pending            - List pending approvals
GET  /api/v1/approvals/history            - Get approval history
GET  /api/v1/approvals/{id}               - Get approval details
POST /api/v1/approvals/{id}/action        - Approve/reject/escalate
POST /api/v1/approvals                    - Create approval request
```

### Audit API (Port 8000 - Claims Data API)
```
GET  /api/v1/audit/stats                  - Get audit statistics
GET  /api/v1/audit/events                 - Search audit events
GET  /api/v1/audit/events/{id}            - Get audit event details
GET  /api/v1/audit/timeline               - Get audit timeline
GET  /api/v1/audit/export                 - Export audit logs
GET  /api/v1/audit/compliance-report      - Generate compliance report
```

### Costs API (Port 8000 - Claims Data API)
```
GET  /api/v1/costs/dashboard              - Aggregated cost dashboard
GET  /api/v1/costs/azure/summary          - Azure cost summary
GET  /api/v1/costs/aws/summary            - AWS cost summary
GET  /api/v1/costs/forecast               - Cost forecast
GET  /api/v1/costs/ai-usage               - AI/LLM usage and costs
GET  /api/v1/costs/platform-usage         - Platform usage (AI, OCR, DB)
GET  /api/v1/costs/budgets                - Get budget alerts
POST /api/v1/costs/budgets                - Create budget alert
```

### AI Config API (Port 8000 - Claims Data API)
```
GET  /api/v1/claims/ai/config             - Get current AI config
PUT  /api/v1/claims/ai/config             - Update AI config
GET  /api/v1/claims/ai/models             - List available models
POST /api/v1/claims/ai/test               - Test AI connection
```

### EIS Mock API (Port 8003 - WS3 Integration)
```
GET  /api/v1/eis/claims   - List claims
GET  /api/v1/eis/policies - List policies
GET  /api/v1/eis/customers - List customers
```

### Agent Pipeline (Port 8006)
```
POST /api/v1/pipeline/trigger - Trigger claim processing
GET  /api/v1/pipeline/status  - Get pipeline status
```

### DocGen (Port 8007)
```
POST /api/v1/docgen/batch/from-claim - Create batch from claim
POST /api/v1/docgen/upload           - Upload documents
```

---

## Environment Variables

### PetInsure360 Backend
```bash
# In petinsure360/backend/.env
DOCGEN_SERVICE_URL=http://localhost:8007
AGENT_PIPELINE_URL=http://localhost:8006
```

### EIS Dynamics
```bash
# In eis-dynamics-poc/src/.env
CORS_ORIGINS=  # Leave empty for ["*"] in dev
```

### Frontend Portals
```bash
# ws4_agent_portal/.env.local
NEXT_PUBLIC_CLAIMS_API_URL=http://localhost:8003
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000    # Chat is on 8000!
NEXT_PUBLIC_PIPELINE_API_URL=http://localhost:8006
NEXT_PUBLIC_DOCGEN_API_URL=http://localhost:8007

# ws8_admin_portal/frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8008
NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000    # Chat is on 8000!
```

---

## Common Mistakes to Avoid

1. **Starting PetInsure360 backend with `app` instead of `socket_app`**
   - WebSocket/Socket.IO will not work
   - Always use: `uvicorn app.main:socket_app`

2. **Forgetting to start WS2, WS5, or WS7 services**
   - These are often missed but required for full functionality
   - Check all 7 EIS backend ports: 8000, 8002, 8003, 8005, 8006, 8007, 8008

3. **Calling Chat API on wrong port**
   - Chat API is on **8000** (Claims Data API)
   - NOT on 8003 (Integration) or 8008 (Admin)

4. **CORS not configured for development**
   - EIS services default to empty cors_origins
   - Code fix: `cors_origins = settings.cors_origins if settings.cors_origins else ["*"]`

5. **API endpoints with/without trailing slash**
   - Use dual decorators: `@router.get("/")` and `@router.get("")`
   - Set `redirect_slashes=False` in FastAPI app

---

## Startup Checklist

Before testing, verify:

- [ ] All 12 services are running (use status check script above)
- [ ] PetInsure360 backend uses `socket_app` entry point
- [ ] Chat API responds on port 8000: `curl http://localhost:8000/api/chat/providers`
- [ ] CORS headers present: `curl -I http://localhost:8003/api/v1/eis/claims`
- [ ] Socket.IO working: `curl http://localhost:3002/socket.io/?EIO=4&transport=polling`

---

## Demo Data & Login

### Demo Login Credentials

| Email | User | Description |
|-------|------|-------------|
| `demo@demologin.com` | Demo User | Primary demo account (default) |
| `demo1@demologin.com` | Demo One | Secondary demo account |
| `demo2@demologin.com` | Demo Two | Tertiary demo account |

### Demo User Data

Each demo user comes with pre-configured pets and policies:

**DEMO-001 (demo@demologin.com)**:
- Pets: Buddy (Golden Retriever), Whiskers (Persian Cat)
- Policies: Premium Plus ($89.99/mo), Standard ($45.99/mo)

**DEMO-002 (demo1@demologin.com)**:
- Pets: Max (German Shepherd), Luna (Siamese Cat)
- Policies: Premium ($79.99/mo)

**DEMO-003 (demo2@demologin.com)**:
- Pets: Charlie (Labrador)
- Policies: Basic ($29.99/mo)

### Seeding Demo Data

Demo data is auto-seeded on PetInsure360 backend startup. To manually reseed:

```bash
# Seed demo data via API
curl -X POST https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/seed-demo

# Or locally
curl -X POST http://localhost:3002/api/customers/seed-demo
```

The deploy script automatically seeds demo data after deployment. See `deploy-aws.sh`.

### Missing Demo Data After Deployment

If demo users don't have pets/policies:
1. The backend container may have restarted (in-memory data lost)
2. Run the seed endpoint: `POST /api/customers/seed-demo`
3. Or redeploy with `./deploy-aws.sh petinsure360-backend`

**Note:** Demo users always work for login because they're defined statically in `customers.py`. However, their pets and policies need to be seeded into the insights service.

---

## AWS/Azure Deployment Issues

### 1. Frontends Calling Localhost in Production

**Error:** Browser console shows:
```
GET http://localhost:8000/api/chat/providers net::ERR_CONNECTION_REFUSED
GET http://localhost:8008/api/v1/costs/dashboard net::ERR_CONNECTION_REFUSED
```

**Cause:** Frontends were built with `.env.local` (localhost URLs) instead of `.env.production` (AWS URLs).

**Root Cause:** For Next.js apps, `.env.local` **OVERRIDES** `.env.production` during builds. For Vite apps, same behavior.

**Solution:** Before building for production, temporarily copy `.env.production` to `.env.local`:
```bash
# For each frontend project:
mv .env.local .env.local.bak       # Backup local config
cp .env.production .env.local       # Use production config for build
npm run build                       # Build with production URLs
mv .env.local.bak .env.local        # Restore local config
```

**Prevention:** Use the deploy script (see below) which handles this automatically.

---

### 2. AI Providers Showing "Disabled" in Production

**Error:** `/api/chat/providers` returns:
```json
{"providers":{"openai":{"enabled":false},"anthropic":{"enabled":false}}}
```

**Cause:** API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) missing from AWS App Runner environment.

**Solution:** Update App Runner environment variables:
```bash
export AWS_PROFILE=sunwaretech

# First, get the correct service ARN
aws apprunner list-services --query 'ServiceSummaryList[*].[ServiceName,ServiceArn]' --output table

# Then update with API keys (use correct image identifier!)
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:ACCOUNT:service/SERVICE_NAME/SERVICE_ID" \
  --source-configuration file:///tmp/apprunner-config.json
```

**Key insight:** The `ImageIdentifier` in the update config MUST match the existing service. Check with:
```bash
aws apprunner describe-service --service-arn $ARN \
  --query 'Service.SourceConfiguration.ImageRepository.ImageIdentifier' --output text
```

**Verification:**
```bash
curl https://YOUR-APP-RUNNER-URL/api/chat/providers
# Should show: "enabled": true for both providers
```

---

### 3. App Runner Update Rolling Back

**Error:** App Runner update shows `ROLLBACK_SUCCEEDED` status.

**Cause:** Usually one of:
1. Wrong `ImageIdentifier` in update config
2. Missing `AuthenticationConfiguration` for ECR access
3. Container fails health check with new env vars

**Solution:** Include ALL required configuration fields:
```json
{
  "ImageRepository": {
    "ImageIdentifier": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/REPO:TAG",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8080",
      "RuntimeEnvironmentVariables": {
        "KEY": "VALUE"
      }
    }
  },
  "AutoDeploymentsEnabled": true,
  "AuthenticationConfiguration": {
    "AccessRoleArn": "arn:aws:iam::ACCOUNT:role/AppRunnerECRAccessRole"
  }
}
```

**Debugging:**
```bash
# Check latest operation status
aws apprunner list-operations --service-arn $ARN --query 'OperationSummaryList[0]'

# Check application logs
aws logs get-log-events \
  --log-group-name "/aws/apprunner/SERVICE/ID/application" \
  --log-stream-name "instance/INSTANCE_ID" \
  --limit 50 --query 'events[*].message' --output text
```

---

### 4. Pipeline Page Issues (BI Dashboard)

#### 4a. Demo Mode Always Showing (Even with Azure Connected)

**Error:** Pipeline page shows "Demo Mode (In-Memory)" badge even when Azure ADLS is configured.

**Root Cause:** Multiple issues:
1. **Wrong API URL:** BI Dashboard was calling `claims-data-api` (EIS) instead of `petinsure360-backend`
2. **Wrong condition:** UI checked `data_source === 'synapse'` but backend returned `'local'` or `'azure'`
3. **No Azure detection:** Backend didn't detect Azure ADLS connection (only Synapse)

**Solution (Jan 2026):**

1. **Fixed API URL in `.env.production`:**
```bash
# WRONG - points to claims-data-api (no pipeline endpoints!)
VITE_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# CORRECT - points to petinsure360-backend
VITE_API_URL=https://fucf3fwwwv.us-east-1.awsapprunner.com
```

2. **Fixed data source detection in `insights.py`:**
```python
# Now detects Azure ADLS (not just Synapse)
self.azure_storage_configured = bool(os.getenv('AZURE_STORAGE_KEY', ''))
if self.azure_storage_configured:
    self.data_source = 'azure'  # Was always 'local' before
```

3. **Fixed isLive check in `PipelinePage.jsx`:**
```javascript
// OLD - only checked synapse
const isLive = pipelineStatus?.data_source === 'synapse'

// NEW - checks both azure and synapse
const isLive = pipelineStatus?.data_source === 'synapse' ||
               pipelineStatus?.data_source === 'azure'
```

**Verification:**
```bash
# Backend should return data_source: "azure" when AZURE_STORAGE_KEY is set
curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/status | jq '.data_source'
# Expected: "azure"
```

---

#### 4b. Missing Demo/Azure Toggle Switch

**Error:** No way to switch between Demo and Azure modes in UI.

**Cause:** Backend had toggle API but frontend UI was never implemented.

**Solution (Jan 2026):** Added toggle switch UI in `PipelinePage.jsx`:
- Visual toggle button (gray = demo, green = azure)
- Demo/Azure labels
- Status badge shows "Connected to Azure ADLS" or "Demo Mode (In-Memory)"

**Note:** The toggle reflects current mode based on backend configuration. To actually switch modes, update `AZURE_STORAGE_KEY` environment variable and restart backend.

---

#### 4c. Pipeline Reset Not Persisting (Data Reappears on Refresh)

**Error:** Clicking "Reset Pipeline" clears UI, but refreshing page brings data back.

**Root Cause:** The `clear_pipeline` endpoint called `insights.refresh_data()` which **reloaded from CSV files**, undoing the clear!

**Solution (Jan 2026):** Modified `pipeline.py` to NOT reload from CSV:
```python
# OLD - reloaded from CSV (BAD!)
insights.refresh_data()

# NEW - directly clear in-memory data without reloading
if insights._claims is not None:
    insights._claims = insights._claims[
        ~(insights._claims['customer_id'].str.startswith('DEMO-') |
          insights._claims['claim_id'].str.startswith('CLM-'))
    ]
```

**Verification:**
```bash
# Clear pipeline
curl -X DELETE https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/clear

# Check - should stay cleared
curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/pending | jq '.counts'
# Expected: {"bronze":0,"silver":0,"gold":0}

# Refresh page in browser - counts should still be 0
```

---

#### 4d. Quick Fix Checklist for Pipeline Page

If pipeline page shows Demo Mode when Azure is configured:

1. **Check backend URL:**
   ```bash
   # BI Dashboard must call petinsure360-backend, NOT claims-data-api
   grep VITE_API_URL petinsure360/bi-dashboard/.env.production
   # Should show: https://fucf3fwwwv.us-east-1.awsapprunner.com
   ```

2. **Check backend returns azure:**
   ```bash
   curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/status | jq '.data_source'
   # Should return: "azure" (not "local" or "demo")
   ```

3. **Rebuild and redeploy frontend:**
   ```bash
   cd petinsure360/bi-dashboard
   npm run build
   aws s3 sync dist/ s3://petinsure360-bi-dashboard --delete --profile sunwaretech
   ```

4. **Clear browser cache:** Ctrl+Shift+R or open in incognito

---

### 5. Browser Popup Confirmation Dialogs

**Error:** Reset/Clear buttons show ugly browser `confirm()` dialog.

**Cause:** Code uses native `confirm()` function.

**Solution:** Replace with inline React confirmation UI:
```jsx
// BAD - uses browser popup
const handleClear = () => {
  if (!confirm('Are you sure?')) return
  doClear()
}

// GOOD - inline confirmation
const [showConfirm, setShowConfirm] = useState(false)

{showConfirm ? (
  <div className="inline-confirm">
    <span>Are you sure?</span>
    <button onClick={doAction}>Yes</button>
    <button onClick={() => setShowConfirm(false)}>Cancel</button>
  </div>
) : (
  <button onClick={() => setShowConfirm(true)}>Clear</button>
)}
```

---

## AWS Deployment Checklist

Before deploying to AWS:

- [ ] Check `.env.production` files have correct AWS URLs (not localhost)
- [ ] Use `./deploy-aws.sh` which handles `.env.local` swapping automatically
- [ ] Use correct AWS_PROFILE: `export AWS_PROFILE=sunwaretech`

After deploying backend:

- [ ] Update AI provider keys in App Runner:
  ```bash
  cd petinsure360/scripts && bash update-ai-keys.sh
  ```

Verification tests:
```bash
# PetInsure360 Backend health (pipeline, insights endpoints)
curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/health

# Claims Data API health (chat, EIS integration)
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/health

# AI providers enabled
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers | jq '.enabled'

# Pipeline status (MUST use petinsure360-backend!)
curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/status | jq '.data_source'
# Expected: "azure" when AZURE_STORAGE_KEY is set

# Frontends accessible
curl -s -o /dev/null -w "%{http_code}" http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com/
```

**AWS Service URLs Reference:**
| Service | URL | Purpose |
|---------|-----|---------|
| petinsure360-backend | https://fucf3fwwwv.us-east-1.awsapprunner.com | Pipeline, Insights, WebSocket |
| claims-data-api | https://9wvcjmrknc.us-east-1.awsapprunner.com | Chat API, EIS Integration |
| agent-pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com | LangGraph Agents |

---

## Environment Files Reference

### Next.js (EIS Portals)
| File | Purpose | Loaded When |
|------|---------|-------------|
| `.env` | Defaults | Always |
| `.env.local` | Local overrides | Always (HIGHEST priority) |
| `.env.production` | Production values | NODE_ENV=production |

**Build behavior:** `.env.local` ALWAYS overrides `.env.production`!

### Vite (PetInsure360)
| File | Purpose | Loaded When |
|------|---------|-------------|
| `.env` | Defaults | Always |
| `.env.local` | Local overrides | Always (HIGHEST priority) |
| `.env.production` | Production values | `vite build` |

**Build behavior:** `.env.local` ALWAYS overrides `.env.production`!

---

## Deployment Issues Quick Fix Reference

### Issue: Synthetic Data Missing (No Customers/Claims)
```bash
# Check: Does Dockerfile copy data?
grep "COPY data/raw" petinsure360/backend/Dockerfile
# Fix: Add to Dockerfile: COPY data/raw/ ./data/raw/
# Rebuild & redeploy
```

### Issue: Demo Login Not Pre-filled
```bash
# Check: LoginPage default email
grep "useState" petinsure360/frontend/src/pages/LoginPage.jsx | grep email
# Fix: Change useState('') to useState('demo@demologin.com')
```

### Issue: Admin Portal 404 Errors
```bash
# Check: Required services exist
ls eis-dynamics-poc/src/shared/claims_data_api/app/services/ | grep -E "admin_config|approvals|audit"
# Fix: Create missing services, register in main.py
```

### Issue: Frontends Calling Localhost
```bash
# Check: .env.production has AWS URLs
grep localhost petinsure360/frontend/.env.production
# Fix: Update to AWS URLs, deploy script handles .env.local swap
```

### Issue: AI Providers Disabled
```bash
# Check: Chat providers status
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers
# Fix: Update App Runner env vars with API keys (see DEPLOYMENT_CHECKLIST.md)
```

### Issue: Service ARN Not Configured
```bash
# Check: ARN placeholders
grep "REPLACE_WITH_ARN" deploy-aws.sh
# Fix: Get ARNs from AWS and update deploy-aws.sh
aws apprunner list-services --profile sunwaretech --query 'ServiceSummaryList[*].[ServiceName,ServiceArn]' --output table
```

---

## Full Issue Details

For comprehensive documentation of all deployment issues with root causes and prevention strategies, see **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**.
