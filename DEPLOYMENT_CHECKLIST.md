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

## Post-Deployment Verification

Run this after every deployment:

```bash
# 1. Check all backends are healthy
curl -s https://fucf3fwwwv.us-east-1.awsapprunner.com/health
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/health
curl -s https://qi2p3x5gsm.us-east-1.awsapprunner.com/health

# 2. Check synthetic data loaded
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/summary"
# Expected: total_customers: 5003, total_claims: 15000

# 3. Check demo login works
curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/lookup?email=demo@demologin.com"
# Expected: customer with pets and policies

# 4. Check AI providers (if keys configured)
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers
# Expected: enabled: true for configured providers

# 5. Check Admin API endpoints
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/config/ai
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/approvals/stats
curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1/audit/stats

# 6. Check frontends (should return 200)
curl -s -o /dev/null -w "%{http_code}" http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com/
curl -s -o /dev/null -w "%{http_code}" http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com/
curl -s -o /dev/null -w "%{http_code}" http://eis-agent-portal.s3-website-us-east-1.amazonaws.com/
curl -s -o /dev/null -w "%{http_code}" http://eis-admin-portal.s3-website-us-east-1.amazonaws.com/
```

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
