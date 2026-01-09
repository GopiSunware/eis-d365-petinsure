# PetInsure360 - AWS Deployment Guide

Complete deployment guide with automated scripts to avoid configuration issues.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Deployment](#quick-deployment)
- [Manual Deployment](#manual-deployment)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. **AWS CLI** with `sunwaretech` profile configured
2. **Docker** installed and running
3. **Node.js 18+** and npm
4. **API Keys**:
   - OpenAI API Key
   - Anthropic API Key (Claude)

### Verify AWS Profile

```bash
export AWS_PROFILE=sunwaretech
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAY42TL6SAYTB4HCKJY",
    "Account": "611670815873",
    "Arn": "arn:aws:iam::611670815873:user/gopi@sunwaretechnologies.com"
}
```

---

## Quick Deployment

### Option 1: Full Deployment Script

```bash
cd /path/to/petinsure360
./deploy-aws.sh
```

### Option 2: Step-by-Step

```bash
# 1. Deploy backend
./scripts/deploy-backend.sh

# 2. Deploy WebSocket infrastructure
./scripts/deploy-websocket.sh

# 3. Deploy frontends
./scripts/deploy-frontends.sh
```

---

## Manual Deployment

### Step 1: Backend Deployment

#### 1.1 Build Docker Image

```bash
cd petinsure360/backend

# Build image
docker build -t petinsure360-backend:latest .

# Tag for ECR
docker tag petinsure360-backend:latest \
  611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest

# Login to ECR
export AWS_PROFILE=sunwaretech
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  611670815873.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest
```

#### 1.2 Deploy to App Runner

```bash
export AWS_PROFILE=sunwaretech

aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-east-1:611670815873:service/petinsure360-backend/88915082265448db85d506782d32eaaf \
  --region us-east-1
```

**Service Details**:
- **Name**: `petinsure360-backend`
- **URL**: `https://fucf3fwwwv.us-east-1.awsapprunner.com`
- **Port**: 3002
- **Base Path**: `/api/*`

---

### Step 2: Claims Data API Deployment

This service provides chat functionality and requires AI provider keys.

#### 2.1 Update Service with Environment Variables

```bash
export AWS_PROFILE=sunwaretech

# Get API keys from main .env
ANTHROPIC_KEY=$(grep ANTHROPIC_API_KEY ../../eis-dynamics-poc/.env | cut -d= -f2)
OPENAI_KEY=$(grep OPENAI_API_KEY ../../eis-dynamics-poc/.env | cut -d= -f2)

# Update App Runner service
aws apprunner update-service \
  --service-arn arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d \
  --region us-east-1 \
  --source-configuration "{
    \"AutoDeploymentsEnabled\": true,
    \"ImageRepository\": {
      \"ImageIdentifier\": \"611670815873.dkr.ecr.us-east-1.amazonaws.com/claims-data-api:latest\",
      \"ImageRepositoryType\": \"ECR\",
      \"ImageConfiguration\": {
        \"Port\": \"8000\",
        \"RuntimeEnvironmentVariables\": {
          \"ANTHROPIC_API_KEY\": \"$ANTHROPIC_KEY\",
          \"OPENAI_API_KEY\": \"$OPENAI_KEY\"
        }
      }
    }
  }"
```

**Service Details**:
- **Name**: `claims-data-api`
- **URL**: `https://9wvcjmrknc.us-east-1.awsapprunner.com`
- **Port**: 8000
- **Base Path**: `/api/v1/*` and `/api/chat/*`

---

### Step 3: WebSocket Infrastructure

WebSocket uses AWS API Gateway WebSocket API (proven architecture).

#### 3.1 Deploy Lambda Function

```bash
cd petinsure360/lambda/websocket

# Package Lambda
zip -r function.zip lambda_function.py

# Update Lambda
export AWS_PROFILE=sunwaretech
aws lambda update-function-code \
  --function-name petinsure360-websocket-handler \
  --zip-file fileb://function.zip \
  --region us-east-1
```

#### 3.2 Verify WebSocket API

```bash
export AWS_PROFILE=sunwaretech

# Get WebSocket URL
aws apigatewayv2 get-apis \
  --region us-east-1 \
  --query "Items[?Name=='petinsure360-websocket'].{ID:ApiId,URL:ApiEndpoint}" \
  --output table
```

**WebSocket Details**:
- **API ID**: `zi4qogocri`
- **URL**: `wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod`
- **DynamoDB Table**: `petinsure360_ws_connections`

---

### Step 4: Frontend Deployment

#### 4.1 Update Environment Variables

**CRITICAL**: Ensure all environment variables have correct `/api` suffixes.

```bash
# Customer Portal (.env.production)
cat > frontend/.env.production << 'EOF'
VITE_API_URL=https://fucf3fwwwv.us-east-1.awsapprunner.com/api
VITE_SOCKET_URL=wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
VITE_CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com/api
VITE_DOCGEN_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1
VITE_PIPELINE_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com/api
EOF

# BI Dashboard (.env.production)
cat > bi-dashboard/.env.production << 'EOF'
VITE_API_URL=https://fucf3fwwwv.us-east-1.awsapprunner.com/api
VITE_SOCKET_URL=wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
VITE_CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com/api
VITE_DOCGEN_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1
VITE_PIPELINE_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com/api
EOF
```

#### 4.2 Build and Deploy Customer Portal

```bash
cd frontend

# Build
npm run build

# Deploy to S3
export AWS_PROFILE=sunwaretech
aws s3 sync dist/ s3://petinsure360-customer-portal --delete
```

**Portal Details**:
- **S3 Bucket**: `petinsure360-customer-portal`
- **URL**: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com

#### 4.3 Build and Deploy BI Dashboard

```bash
cd bi-dashboard

# Build
npm run build

# Deploy to S3
export AWS_PROFILE=sunwaretech
aws s3 sync dist/ s3://petinsure360-bi-dashboard --delete
```

**Dashboard Details**:
- **S3 Bucket**: `petinsure360-bi-dashboard`
- **URL**: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com

---

## Environment Variables

### Backend Service Environment Variables

| Variable | Value | Service |
|----------|-------|---------|
| `PORT` | `3002` | petinsure360-backend |
| `ENVIRONMENT` | `production` | petinsure360-backend |

### Claims Data API Environment Variables

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | ✅ Yes |
| `OPENAI_API_KEY` | `sk-proj-...` | ✅ Yes |
| `PORT` | `8000` | Auto-configured |

### Frontend Environment Variables

Both frontends require these variables in `.env.production`:

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | `https://fucf3fwwwv.us-east-1.awsapprunner.com/api` | Backend API (with /api) |
| `VITE_SOCKET_URL` | `wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod` | WebSocket API |
| `VITE_CLAIMS_API_URL` | `https://9wvcjmrknc.us-east-1.awsapprunner.com/api` | Claims Data API + Chat (with /api, NOT /api/v1) |
| `VITE_DOCGEN_URL` | `https://9wvcjmrknc.us-east-1.awsapprunner.com/api/v1` | DocGen API |
| `VITE_PIPELINE_URL` | `https://qi2p3x5gsm.us-east-1.awsapprunner.com/api` | Agent Pipeline API |

---

## Deployment Scripts

### scripts/deploy-backend.sh

```bash
#!/bin/bash
set -e

echo "=== Deploying PetInsure360 Backend ==="
export AWS_PROFILE=sunwaretech

# Build Docker image
echo "Building Docker image..."
cd backend
docker build -t petinsure360-backend:latest .

# Tag for ECR
echo "Tagging image for ECR..."
docker tag petinsure360-backend:latest \
  611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  611670815873.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
echo "Pushing image to ECR..."
docker push 611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest

# Trigger deployment
echo "Triggering App Runner deployment..."
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-east-1:611670815873:service/petinsure360-backend/88915082265448db85d506782d32eaaf \
  --region us-east-1

echo "✅ Backend deployment triggered!"
echo "Monitor at: https://console.aws.amazon.com/apprunner/home?region=us-east-1#/services"
```

### scripts/deploy-frontends.sh

```bash
#!/bin/bash
set -e

echo "=== Deploying PetInsure360 Frontends ==="
export AWS_PROFILE=sunwaretech

# Deploy Customer Portal
echo "Building Customer Portal..."
cd frontend
npm run build

echo "Deploying Customer Portal to S3..."
aws s3 sync dist/ s3://petinsure360-customer-portal --delete
echo "✅ Customer Portal deployed: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com"

# Deploy BI Dashboard
echo "Building BI Dashboard..."
cd ../bi-dashboard
npm run build

echo "Deploying BI Dashboard to S3..."
aws s3 sync dist/ s3://petinsure360-bi-dashboard --delete
echo "✅ BI Dashboard deployed: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com"

echo "=== Frontend deployment complete! ==="
```

### scripts/update-ai-keys.sh

```bash
#!/bin/bash
set -e

echo "=== Updating AI Provider Keys ==="
export AWS_PROFILE=sunwaretech

# Get API keys from .env
ANTHROPIC_KEY=$(grep ANTHROPIC_API_KEY ../../eis-dynamics-poc/.env | cut -d= -f2)
OPENAI_KEY=$(grep OPENAI_API_KEY ../../eis-dynamics-poc/.env | cut -d= -f2)

if [ -z "$ANTHROPIC_KEY" ] || [ -z "$OPENAI_KEY" ]; then
  echo "❌ Error: API keys not found in ../../eis-dynamics-poc/.env"
  exit 1
fi

echo "Updating claims-data-api with AI provider keys..."
aws apprunner update-service \
  --service-arn arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d \
  --region us-east-1 \
  --source-configuration "{
    \"AutoDeploymentsEnabled\": true,
    \"ImageRepository\": {
      \"ImageIdentifier\": \"611670815873.dkr.ecr.us-east-1.amazonaws.com/claims-data-api:latest\",
      \"ImageRepositoryType\": \"ECR\",
      \"ImageConfiguration\": {
        \"Port\": \"8000\",
        \"RuntimeEnvironmentVariables\": {
          \"ANTHROPIC_API_KEY\": \"$ANTHROPIC_KEY\",
          \"OPENAI_API_KEY\": \"$OPENAI_KEY\"
        }
      }
    }
  }"

echo "✅ AI provider keys updated!"
echo "Deployment in progress. Monitor status:"
echo "aws apprunner describe-service --service-arn arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d --region us-east-1 --query 'Service.Status'"
```

---

## Troubleshooting

### Issue: "No AI providers configured"

**Symptom**: Chat sidebar shows warning "No AI providers configured"

**Root Cause 1**: Claims Data API missing ANTHROPIC_API_KEY or OPENAI_API_KEY

**Fix**:
```bash
cd petinsure360
./scripts/update-ai-keys.sh
```

**Root Cause 2**: Frontend calling wrong URL (`/api/v1/chat/providers` instead of `/api/chat/providers`)

**Fix**: Ensure `VITE_CLAIMS_API_URL` is set to `https://9wvcjmrknc.us-east-1.awsapprunner.com/api` (NOT `/api/v1`)
```bash
# Check current value
grep VITE_CLAIMS_API_URL frontend/.env.production

# Should be: https://9wvcjmrknc.us-east-1.awsapprunner.com/api
# If it shows /api/v1, update and rebuild:
cd frontend
npm run build
aws s3 sync dist/ s3://petinsure360-customer-portal --delete
```

**Verify Fix**:
```bash
# Test the endpoint directly
curl https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers

# Should return: {"providers": {...}, "enabled": ["openai", "anthropic"], ...}
```

### Issue: Demo user login fails with 404

**Symptom**: Login returns "No account found with this email"

**Root Cause**: Frontend calling wrong API path (missing `/api` prefix)

**Fix**:
1. Verify `.env.production` has `/api` suffix in `VITE_API_URL`
2. Rebuild and redeploy frontend:
```bash
cd frontend
npm run build
export AWS_PROFILE=sunwaretech
aws s3 sync dist/ s3://petinsure360-customer-portal --delete
```

### Issue: WebSocket connection fails

**Symptom**: Console shows "WebSocket connection failed"

**Root Cause**: Frontend using wrong WebSocket URL or Lambda not deployed

**Fix**:
1. Verify WebSocket URL in `.env.production`:
```bash
grep VITE_SOCKET_URL frontend/.env.production
# Should be: wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
```

2. Test WebSocket connection:
```bash
npm install -g wscat
wscat -c wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
```

### Issue: Backend returns 404 for /api/customers

**Symptom**: API returns 404 for endpoints without trailing slash

**Root Cause**: FastAPI `redirect_slashes=False` configuration

**Fix**: Ensure `redirect_slashes` is not set to `False` in `backend/app/main.py`:
```python
app = FastAPI(
    title="PetInsure360 API",
    # redirect_slashes=True by default - DO NOT set to False
)
```

---

## Automated Testing

### Quick Verification Script

Run the automated test suite to verify all endpoints:

```bash
cd petinsure360
./scripts/test-deployment.sh
```

This script tests:
- ✓ All backend API endpoints
- ✓ AI chat providers configuration
- ✓ Agent pipeline health
- ✓ Frontend accessibility
- ✓ Demo user availability
- ✓ WebSocket infrastructure (if wscat installed)

**Expected output:**
```
✅ All tests passed!
🎉 Deployment is fully functional!
```

If tests fail, the script will show:
- Which endpoint failed
- HTTP status code
- Error response
- Suggested fixes

---

## Manual Verification

After deployment, you can manually verify services:

### Backend API
```bash
curl https://fucf3fwwwv.us-east-1.awsapprunner.com/health
# Expected: {"status":"healthy",...}

curl https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/lookup?email=demo@demologin.com
# Expected: Customer data with pets and policies
```

### Claims Data API (Chat)
```bash
curl https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers
# Expected: {"enabled":["openai","anthropic"],...}
```

### WebSocket
```bash
npm install -g wscat
wscat -c wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod
# Connected? Send: {"action":"ping"}
# Expected: {"type":"pong",...}
```

### Frontends
- Customer Portal: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com
- BI Dashboard: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com

### Demo Login
Login with: `demo@demologin.com`
- Should succeed and show customer dashboard
- Chat sidebar should show AI provider selector (not "No AI providers configured")

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Customer   │    │      BI      │    │   Lambda     │ │
│  │   Portal     │    │   Dashboard  │    │  WebSocket   │ │
│  │   (S3)       │    │   (S3)       │    │   Handler    │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘ │
│         │                    │                    │          │
│         └────────────────────┴────────────────────┘          │
│                              │                               │
│         ┌────────────────────┴────────────────────┐          │
│         │                                          │          │
│  ┌──────▼──────┐    ┌──────────────┐    ┌────────▼──────┐  │
│  │ PetInsure360│    │ Claims Data  │    │  API Gateway  │  │
│  │   Backend   │    │     API      │    │   WebSocket   │  │
│  │ (App Runner)│    │ (App Runner) │    │      API      │  │
│  │ :3002       │    │ :8000        │    │               │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │   DynamoDB   │    │     ECR      │                       │
│  │ Connections  │    │  Container   │                       │
│  │    Table     │    │   Registry   │                       │
│  └──────────────┘    └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Cost Estimates

| Service | Configuration | Monthly Cost (est.) |
|---------|--------------|---------------------|
| App Runner (Backend) | 1 vCPU, 2GB RAM | ~$25-35 |
| App Runner (Claims API) | 1 vCPU, 2GB RAM | ~$25-35 |
| S3 (Frontends) | Static hosting | ~$1-2 |
| API Gateway WebSocket | 1M messages/month | ~$1-3 |
| Lambda (WebSocket) | 1M invocations/month | ~$0.20 |
| DynamoDB | On-demand | ~$1-2 |
| ECR | Image storage | ~$1 |
| **Total** | | **~$55-80/month** |

---

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
2. Check [AWS_WEBSOCKET_STANDARD.md](AWS_WEBSOCKET_STANDARD.md) for WebSocket details
3. Review App Runner logs:
```bash
export AWS_PROFILE=sunwaretech
aws logs tail /aws/apprunner/petinsure360-backend --follow
```
