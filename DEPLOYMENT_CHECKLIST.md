# Deployment Checklist

**CRITICAL:** Run through this checklist before every deployment to avoid known issues.

---

## Pre-Deployment Validation

### 1. Docker & Data Files

```bash
# Run validation script
./scripts/validate-deployment.sh

# Or manually check:
```

| Check | Command | Expected |
|-------|---------|----------|
| Dockerfile copies data/raw | `grep "COPY data/raw" petinsure360/backend/Dockerfile` | `COPY data/raw/ ./data/raw/` |
| Synthetic data exists | `wc -l petinsure360/backend/data/raw/customers.csv` | ~5004 lines |
| Claims data exists | `wc -l petinsure360/backend/data/raw/claims.jsonl` | ~15000 lines |
| Scenarios file exists | `ls petinsure360/backend/data/claim_scenarios.json` | File exists |

### 2. Environment Files

```bash
# Check all .env.production files have AWS URLs (not localhost)
grep -r "localhost" petinsure360/frontend/.env.production
grep -r "localhost" petinsure360/bi-dashboard/.env.production
grep -r "localhost" eis-dynamics-poc/src/ws4_agent_portal/.env.production
grep -r "localhost" eis-dynamics-poc/src/ws8_admin_portal/frontend/.env.production
# Expected: No matches (should return nothing)
```

### 3. Service ARNs

```bash
# Check deploy script has valid ARNs (not REPLACE_WITH_ARN)
grep "REPLACE_WITH_ARN" deploy-aws.sh
# Expected: No matches
```

### 4. API Endpoints in Frontends

| Frontend | Config File | Key Variables |
|----------|-------------|---------------|
| Customer Portal | `petinsure360/frontend/.env.production` | `VITE_API_URL=https://fucf3fwwwv...` |
| BI Dashboard | `petinsure360/bi-dashboard/.env.production` | `VITE_API_URL=https://fucf3fwwwv...` |
| Agent Portal | `eis-dynamics-poc/src/ws4_agent_portal/.env.production` | `NEXT_PUBLIC_CHAT_API_URL`, `NEXT_PUBLIC_CLAIMS_API_URL` |
| Admin Portal | `eis-dynamics-poc/src/ws8_admin_portal/frontend/.env.production` | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_CHAT_API_URL` |

---

## Known Issues & Prevention

### Issue 1: Synthetic Data Missing After Deployment

**Symptom:** Login works but no customers/pets/policies/claims in insights API.

**Root Cause:** Dockerfile was not copying `data/raw/` folder.

**Prevention:**
```dockerfile
# petinsure360/backend/Dockerfile MUST have:
COPY data/raw/ ./data/raw/
```

**Verification after deploy:**
```bash
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/summary"
# Should show: total_customers: 5003, total_claims: 15000
```

---

### Issue 2: Demo Login Email Not Pre-filled

**Symptom:** Login page shows empty email field.

**Root Cause:** LoginPage.jsx had `useState('')` instead of default email.

**Prevention:**
```jsx
// petinsure360/frontend/src/pages/LoginPage.jsx
const [email, setEmail] = useState('demo@demologin.com')
```

**Verification:**
- Open Customer Portal, login page should show `demo@demologin.com` pre-filled

---

### Issue 3: Service ARN Not Configured

**Symptom:** `./deploy-aws.sh` shows "Service ARN not configured, skipping deployment trigger"

**Root Cause:** SERVICE_ARNS array has placeholder values.

**Prevention:** After creating App Runner service, update `deploy-aws.sh`:
```bash
# Get actual ARNs
aws apprunner list-services --profile sunwaretech \
  --query 'ServiceSummaryList[*].[ServiceName,ServiceArn]' --output table

# Update deploy-aws.sh SERVICE_ARNS array with real values
```

---

### Issue 4: Admin Portal 404 Errors

**Symptom:** Admin Portal shows 404 for `/api/v1/config/*`, `/api/v1/approvals/*`, `/api/v1/audit/*`

**Root Cause:** Missing service routers in Claims Data API.

**Prevention:** Ensure these services exist in `eis-dynamics-poc/src/shared/claims_data_api/app/services/`:
- `admin_config_service.py`
- `approvals_service.py`
- `audit_service.py`

And are registered in `main.py`:
```python
app.include_router(admin_config_service.router, prefix="/api/v1/config")
app.include_router(approvals_service.router, prefix="/api/v1/approvals")
app.include_router(audit_service.router, prefix="/api/v1/audit")
```

---

### Issue 5: Frontends Calling Localhost in Production

**Symptom:** Browser console shows `GET http://localhost:8000/... net::ERR_CONNECTION_REFUSED`

**Root Cause:** `.env.local` overrides `.env.production` even in production builds!

**Prevention:** The `deploy-aws.sh` script handles this automatically by:
1. Backing up `.env.local` to `.env.local.bak`
2. Copying `.env.production` to `.env.local`
3. Running build
4. Restoring original `.env.local`

**Manual fix if needed:**
```bash
mv .env.local .env.local.bak
cp .env.production .env.local
npm run build
mv .env.local.bak .env.local
```

---

### Issue 6: AI Providers Showing "Disabled"

**Symptom:** `/api/chat/providers` returns `{"openai":{"enabled":false},"anthropic":{"enabled":false}}`

**Root Cause:** API keys not set in App Runner environment variables.

**Prevention:** After deployment, run:
```bash
# Get current image identifier
ARN="arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d"
IMAGE=$(aws apprunner describe-service --service-arn $ARN --profile sunwaretech \
  --query 'Service.SourceConfiguration.ImageRepository.ImageIdentifier' --output text)

# Update with API keys
cat > /tmp/config.json << EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$IMAGE",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8080",
      "RuntimeEnvironmentVariables": {
        "ANTHROPIC_API_KEY": "your-key-here",
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  },
  "AutoDeploymentsEnabled": true,
  "AuthenticationConfiguration": {
    "AccessRoleArn": "arn:aws:iam::611670815873:role/AppRunnerECRAccessRole"
  }
}
EOF

aws apprunner update-service --service-arn $ARN --profile sunwaretech \
  --source-configuration file:///tmp/config.json
```

---

### Issue 7: Pipeline Page Shows Wrong Data Source

**Symptom:** Pipeline page shows "Demo Mode" even when Azure is connected.

**Root Cause:**
1. BI Dashboard calling wrong backend (`claims-data-api` instead of `petinsure360-backend`)
2. Frontend checking wrong condition (`synapse` instead of `azure`)

**Prevention:**
- `.env.production` must point to `petinsure360-backend`:
  ```
  VITE_API_URL=https://fucf3fwwwv.us-east-1.awsapprunner.com
  ```
- `PipelinePage.jsx` must check both:
  ```javascript
  const isLive = data_source === 'synapse' || data_source === 'azure'
  ```

---

### Issue 8: Demo Customers Not Showing at Top in Customer 360

**Symptom:** Demo customers (DEMO-001, DEMO-002) don't appear at top of Customer 360 list.

**Root Cause:** Frontend sorts by `customer_since` date (newest first), but demo customers had old dates (2024-01-01).

**Prevention:**
```python
# petinsure360/backend/app/api/insights.py - DEMO_CUSTOMERS_360
# Dates must be recent (today's date or yesterday)
"customer_since": "2026-01-10",  # Use current date
```

**Verification:**
```bash
curl -s ".../api/insights/customers?limit=2" | jq '.customers[].customer_id'
# Expected: "DEMO-001", "DEMO-002"
```

---

### Issue 9: DocGen Service URL Mismatch

**Symptom:** Document uploads fail with "DocGen service unavailable" even when service is online.

**Root Cause:** `DOCGEN_SERVICE_URL` environment variable in petinsure360-backend pointing to old/wrong URL.

**Prevention:** After DocGen service deployment, update petinsure360-backend:
```bash
# Check current URL
curl -s https://fucf3fwwwv.../api/docgen/health
# If docgen_url is wrong, update App Runner env vars

# Correct URL should be: https://tbkh2svcwm.us-east-1.awsapprunner.com
```

**Important:** When updating App Runner env vars, use correct **port** (8080 for petinsure360-backend).

---

### Issue 10: Customer Portal Shows Scary Error Messages

**Symptom:** Customer Portal shows "Failed" with technical error messages to customers.

**Root Cause:** Upload page displaying raw error_message from backend.

**Prevention:** Customer-facing pages should never show technical errors:
```jsx
// petinsure360/frontend/src/pages/UploadDocsPage.jsx
// Status badge shows "In Review" (amber) not "Failed" (red)
case 'failed':
  return <span className="bg-amber-100">In Review</span>

// Error message shows friendly text
{upload.status === 'failed' && (
  <span>Your claim is being reviewed by our team.</span>
)}
```

**Note:** BI Dashboard SHOULD show full error details for admins.

---

### Issue 11: BI Dashboard DocGen Page Shows Empty/Wrong Data

**Symptom:** Doc Processing page shows "0 batches" or wrong URL errors.

**Root Cause:**
1. DocGenAdminPage.jsx using wrong API URL (EIS DocGen format instead of petinsure360-backend)
2. Missing `/api/docgen/batches` endpoint in backend

**Prevention:**
```jsx
// petinsure360/bi-dashboard/src/pages/DocGenAdminPage.jsx
// Use VITE_API_URL (petinsure360-backend), not VITE_DOCGEN_URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3002'
// Call /api/docgen/batches, not /api/v1/docgen/batches
```

---

## Post-Deployment Steps (Automated)

The `deploy-aws.sh` script now **automatically runs** these post-deployment steps in order:

### Step 1: Wait for Services to be Healthy
Polls all backend services until they respond healthy:
- PetInsure360 Backend (`/health`)
- Agent Pipeline (`/health`)
- Claims Data API (`/`)

### Step 2: Clear Old Pipeline Data
Removes any stale CLM-* claims from previous runs:
- Agent Pipeline: `DELETE /clear` - Clears all pipeline runs
- PetInsure360: `DELETE /api/pipeline/clear` - Clears claims and uploads

### Step 3: Seed Demo Data
Creates demo users with pets and policies:
- `POST /api/customers/seed-demo`
- Creates: 3 customers, 5 pets, 4 policies

### Step 4: Verify Clean State
Confirms the system is ready for demo:
- Pipeline runs = 0
- Demo users have pets configured

---

## Manual Post-Deployment Verification

If you need to verify manually after deployment:

```bash
# 1. Check all backends are healthy
curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/health
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/health
curl -s https://qi2p3x5gsm.us-east-1.awsapprunner.com/health

# 2. Check synthetic data loaded
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/summary"
# Expected: total_customers: 5003, total_claims: 15000

# 3. Check demo login works with pets
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/lookup?email=demo@demologin.com"
# Expected: customer with 2 pets (Buddy, Whiskers) and 2 policies

# 4. Check demo pets are accessible via pets API
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pets?customer_id=DEMO-001"
# Expected: 2 pets (Buddy, Whiskers)
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pets?customer_id=DEMO-002"
# Expected: 2 pets (Max, Luna)

# 5. Check Agent Pipeline is clean (no old CLM-* claims)
curl -s https://qi2p3x5gsm.us-east-1.awsapprunner.com/metrics
# Expected: total_runs: 0

# 6. Check AI providers (if keys configured)
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers
# Expected: enabled: true for configured providers

# 7. Check Admin API endpoints
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/config/ai
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/approvals/stats
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/audit/stats

# 8. Check frontends (should return 200)
curl -s -o /dev/null -w "%{http_code}" http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com/
curl -s -o /dev/null -w "%{http_code}" http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com/
curl -s -o /dev/null -w "%{http_code}" http://eis-agent-portal.s3-website-us-east-1.amazonaws.com/
curl -s -o /dev/null -w "%{http_code}" http://eis-admin-portal.s3-website-us-east-1.amazonaws.com/

# 9. Check Demo Customers show at TOP in Customer 360
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/customers?limit=3" | jq '.customers[0:2] | .[].customer_id'
# Expected: "DEMO-001", "DEMO-002" (demo users should be first due to recent dates)

# 10. Check DocGen batches endpoint works
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/docgen/batches"
# Expected: {"batches":[], "stats": {...}} (empty if fresh deploy)

# 11. Check DocGen service connection
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/docgen/health"
# Expected: {"status":"healthy","docgen_service":"connected","docgen_url":"https://..."}
```

---

## Manual Reset Script

To reset demo data without full redeployment, use:

```bash
./scripts/reset-demo-data.sh

# Or with AWS endpoints:
PETINSURE_BACKEND="https://fucf3fwwwv.us-east-1.awsapprunner.com" \
AGENT_PIPELINE="https://qi2p3x5gsm.us-east-1.awsapprunner.com" \
./scripts/reset-demo-data.sh
```

This script:
1. Clears PetInsure360 pipeline data
2. Clears Agent Pipeline runs (CLM-* claims)
3. Verifies clean state

---

## Demo Data Verification Checklist

**After every backend deployment, verify demo data is working:**

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Demo customers at top | `curl .../api/insights/customers?limit=2 \| jq '.customers[].customer_id'` | `DEMO-001`, `DEMO-002` |
| Demo customers have recent dates | Check `customer_since` | `2026-01-10`, `2026-01-09` (today/yesterday) |
| DocGen batches endpoint | `curl .../api/docgen/batches` | Returns JSON with `batches` array |
| DocGen service connected | `curl .../api/docgen/health` | `docgen_service: "connected"` |
| Claims from uploads show | After upload, check `/api/insights/claims` | New claims with `source: "document_upload"` |

---

## Quick Reference: AWS Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| PetInsure360 Backend | https://fucf3fwwwv.us-east-1.awsapprunner.com | Pipeline, Insights, WebSocket |
| Claims Data API | https://9wvcjmrknc.us-east-1.awsapprunner.com | Chat API, Admin Config, EIS |
| Agent Pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com | LangGraph Agents |
| Customer Portal | http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com | Customer UI |
| BI Dashboard | http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com | Analytics UI |
| Agent Portal | http://eis-agent-portal.s3-website-us-east-1.amazonaws.com | Claims Agent UI |
| Admin Portal | http://eis-admin-portal.s3-website-us-east-1.amazonaws.com | Admin Config UI |

---

## Data Files Reference

| File | Location | Records | Purpose |
|------|----------|---------|---------|
| customers.csv | `petinsure360/backend/data/raw/` | 5,003 | Customer profiles |
| pets.csv | `petinsure360/backend/data/raw/` | 6,504 | Pet records |
| policies.csv | `petinsure360/backend/data/raw/` | 6,004 | Insurance policies |
| claims.jsonl | `petinsure360/backend/data/raw/` | 15,000 | Claims history |
| providers.csv | `petinsure360/backend/data/raw/` | 200 | Vet providers |
| claim_scenarios.json | `petinsure360/backend/data/` | 36 | Test scenarios |

**CRITICAL:** These files MUST be copied into the Docker container. See Dockerfile.

---

## Issue 12: Demo Users Missing Pets in Customer Portal

**Symptom:** Demo user logs in but shows "0 Pets" even though `/api/customers/lookup` returns pets correctly.

**Root Cause:** The pets are defined in `DEMO_PETS` constant but stored in-memory. After service restart (e.g., App Runner deployment), the in-memory data is lost and the `/api/pets` endpoint returns empty.

**The Difference:**
- `/api/customers/lookup` - Returns pets from hardcoded `DEMO_USERS` constant (always works)
- `/api/pets?customer_id=X` - Returns pets from in-memory `insights._pets` DataFrame (needs seeding)

**Prevention:** The `deploy-aws.sh` script now automatically calls the seed endpoint after deployment:
```bash
curl -X POST "https://fucf3fwwwv.../api/customers/seed-demo"
```

**Manual Fix:**
```bash
# Seed demo data (creates customers, pets, policies in insights service)
curl -X POST "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/seed-demo"

# Verify pets are now available
curl -s "https://fucf3fwwwv.../api/pets?customer_id=DEMO-001"
# Expected: 2 pets (Buddy, Whiskers)
```

**Verification:**
| User | Email | Expected Pets |
|------|-------|---------------|
| Demo | demo@demologin.com | Buddy (Dog), Whiskers (Cat) |
| Demo1 | demo1@demologin.com | Max (Dog), Luna (Cat) |
| Demo2 | demo2@demologin.com | Charlie (Dog) |

---

## Issue 13: Old Pipeline Runs (CLM-* Claims) Persist After Deployment

**Symptom:** BI Dashboard Agent Pipeline page shows old CLM-* claims from previous demo sessions.

**Root Cause:** Agent Pipeline stores runs in-memory. While App Runner restarts clear this, partial deployments or config updates may not restart all services.

**Prevention:** The `deploy-aws.sh` script now automatically clears pipeline data:
```bash
curl -X DELETE "https://qi2p3x5gsm.../clear"
```

**Manual Fix:**
```bash
# Clear Agent Pipeline runs
curl -X DELETE "https://qi2p3x5gsm.us-east-1.awsapprunner.com/clear"

# Verify clean state
curl -s "https://qi2p3x5gsm.us-east-1.awsapprunner.com/metrics"
# Expected: total_runs: 0
```

---

## Issue 14: Rule Engine Pipeline Execution Mode

**Understanding:** The Bronze → Silver → Gold processing is done **entirely in Python** (in-memory), NOT via Databricks notebooks.

**Current Implementation:**
- `process_bronze_to_silver()` - Python data transformations (validation, quality scoring)
- `process_silver_to_gold()` - Python aggregations (customer joins, reimbursement calculation)
- No actual Databricks API calls or notebook execution

**Verification:**
```bash
# Check pipeline status - should show execution_info
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/status" | jq '.execution_info'
# Expected: {"mode":"python_local","databricks_connected":false,...}
```

**UI Proof:**
- BI Dashboard Pipeline page shows "Execution Mode" banner
- After processing, "Processing Proof" panel shows transformations applied and values calculated
- Each claim shows: completeness_score, validity_score, quality_score (Bronze→Silver)
- Each claim shows: customer_name, estimated_reimbursement, priority (Silver→Gold)

**To Enable Actual Databricks Execution:**
Set environment variables in App Runner:
```bash
DATABRICKS_HOST=https://adb-xxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapiXXXXXXXXXX
```

---

## Issue 15: Duplicate Claims in Recent Claims List

**Symptom:** Same claim appears twice in "Recent Claims" table.

**Root Cause:** `add_claim()` was called twice:
1. When claim submitted to Bronze layer
2. When claim processed to Gold layer

**Prevention:** `insights.py` now checks for existing claim_id before adding:
```python
def add_claim(self, claim_data):
    claim_id = str(claim_data.get('claim_id', ''))
    if claim_id and len(self._claims) > 0:
        existing = self._claims[self._claims['claim_id'].astype(str) == claim_id]
        if not existing.empty:
            print(f"Claim {claim_id} already exists - skipping duplicate add")
            return  # Skip duplicate
```

**Verification:**
After submitting and processing a claim, check that it only appears once:
```bash
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/claims?limit=5" | jq '.claims[].claim_id'
# Each claim_id should appear only once
```

---

## Issue 16: Azure CPU Quota Blocks Databricks Jobs

**Symptom:** Databricks job shows "Running" but tasks are stuck in "Blocked" state. UI shows "Databricks Job Triggered" but job never completes.

**Root Cause:** Azure subscription has insufficient CPU quota for the Databricks cluster:
```
"This account may not have enough CPU cores to satisfy this request"
"Estimated available: 0, requested: 4"
```

**Diagnosis:**
1. Open Databricks workspace → Jobs → View running job
2. Click on cluster name to see compute configuration
3. Look for orange warning banner about CPU quota

**Resolution Options:**

**Option 1: Request Azure Quota Increase**
1. Go to Azure Portal → Subscriptions → [Your Subscription]
2. Navigate to Usage + quotas
3. Request increase for "Standard DSv5 Family vCPUs" in your region
4. Wait for approval (can take 1-24 hours)

**Option 2: Use Smaller VM Size**
1. In Databricks workspace → Compute → shared_cluster
2. Edit cluster configuration
3. Change from `Standard_D4s_v5` (4 cores) to `Standard_D2s_v5` (2 cores)
4. Save and restart cluster

**Option 3: Use Different VM Family**
1. Check which VM families have available quota in Azure
2. Update cluster to use a different family (e.g., `Standard_E2s_v3`)

**UI Fix Applied:**
The BI Dashboard now shows:
- **Orange/Amber** styling when Databricks job is running
- **"Databricks Running..."** badge instead of green "completed"
- Note: "Local processing complete. Databricks job running in background"
- Status polling every 10 seconds to update when job completes

**Verification:**
```bash
# Check Databricks job status via API
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/pipeline/databricks/run/{run_id}"
# Expected when blocked: life_cycle_state: "RUNNING", tasks showing "BLOCKED"
```
