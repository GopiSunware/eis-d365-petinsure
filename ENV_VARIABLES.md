# Environment Variables Reference

Complete reference for all environment variables used across PetInsure360 and EIS Dynamics POC.

---

## AWS Production URLs

| Service | URL |
|---------|-----|
| Claims Data API | https://9wvcjmrknc.us-east-1.awsapprunner.com |
| Agent Pipeline | https://qi2p3x5gsm.us-east-1.awsapprunner.com |
| PetInsure360 Backend | https://fucf3fwwwv.us-east-1.awsapprunner.com |
| Customer Portal | http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com |
| BI Dashboard | http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com |
| WebSocket | wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod |

---

## Frontend Environment Variables

### PetInsure360 Customer Portal
**File:** `petinsure360/frontend/.env.production`

```env
# Backend API - code calls without /api prefix, so include it
VITE_API_URL=https://fucf3fwwwv.us-east-1.awsapprunner.com/api

# WebSocket for real-time updates
VITE_SOCKET_URL=wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod

# Chat API - code includes /api/chat prefix
VITE_CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# Rating service - code adds /api/v1/rating/...
VITE_RATING_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# DocGen service - code adds /api/v1/docgen/...
VITE_DOCGEN_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# Pipeline service
VITE_PIPELINE_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com/api
```

### PetInsure360 BI Dashboard
**File:** `petinsure360/bi-dashboard/.env.production`

```env
# Main API - for /api/insights/* calls
VITE_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# WebSocket for real-time updates
VITE_SOCKET_URL=wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod

# Chat API
VITE_CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# AI configuration
VITE_AI_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# DocGen service
VITE_DOCGEN_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# Pipeline service
VITE_PIPELINE_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com/api
```

### EIS Agent Portal
**File:** `eis-dynamics-poc/src/ws4_agent_portal/.env.production`

```env
NEXT_PUBLIC_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
NEXT_PUBLIC_PIPELINE_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com
```

---

## Backend Environment Variables

### Claims Data API (All-in-One Gateway)
**Service:** `eis-dynamics-poc/src/shared/claims_data_api`
**Port:** 8000 (local) / 8080 (AWS App Runner)

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# AI Providers (optional - for chat service)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# CORS (configured in code for production)
CORS_ORIGINS=*
```

### Agent Pipeline
**Service:** `eis-dynamics-poc/src/ws6_agent_pipeline`
**Port:** 8006 (local) / 8080 (AWS App Runner)

```env
ENVIRONMENT=production
LOG_LEVEL=INFO

# AI Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Service URLs
CLAIMS_DATA_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com

# S3 Storage (AWS)
AWS_REGION=us-east-1
S3_BUCKET_NAME=petinsure360-pipeline-data
USE_S3=true

# Or local storage (development)
USE_LOCAL_STORAGE=true
LOCAL_STORAGE_PATH=./data
```

### PetInsure360 Backend
**Service:** `petinsure360/backend`
**Port:** 3002 (local) / 8000 (AWS App Runner)

```env
ENVIRONMENT=production
LOG_LEVEL=INFO

# Claims Data API integration
CLAIMS_API_URL=https://9wvcjmrknc.us-east-1.awsapprunner.com
PIPELINE_API_URL=https://qi2p3x5gsm.us-east-1.awsapprunner.com

# CORS
CORS_ORIGINS=*
```

---

## Local Development URLs

| Service | URL |
|---------|-----|
| Claims Data API | http://localhost:8000 |
| WS2 AI Claims | http://localhost:8002 |
| WS3 Integration | http://localhost:8003 |
| WS5 Rating | http://localhost:8005 |
| WS6 Agent Pipeline | http://localhost:8006 |
| WS7 DocGen | http://localhost:8007 |
| WS8 Admin | http://localhost:8008 |
| Agent Portal | http://localhost:8080 |
| Admin Portal | http://localhost:8081 |
| Customer Portal | http://localhost:3000 |
| BI Dashboard | http://localhost:3001 |
| PetInsure Backend | http://localhost:3002 |

---

## AI Provider Configuration

### Claude (Anthropic)
```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### OpenAI
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

### Azure OpenAI
```env
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

---

## URL Prefix Gotchas

**CRITICAL:** Pay attention to whether frontend code includes `/api` prefix or not:

| Frontend Code Pattern | Env Var Should Be |
|----------------------|-------------------|
| `api.get('/customers')` | `VITE_API_URL=.../api` |
| `fetch('${BASE}/api/chat')` | `VITE_API_URL=...` (no /api) |
| `fetch('${BASE}/api/v1/rating')` | `VITE_RATING_URL=...` (no prefix) |

### Common Mistakes

1. **Double /api prefix**: If code has `/api/...` and env has `/api`, you get `/api/api/...`
2. **Missing /api prefix**: If code has no prefix and env has no `/api`, calls fail

### How to Debug
```bash
# Check what URL is being called
# Open browser DevTools > Network tab
# Look for 404 errors and check the full URL
```

---

## AWS App Runner Environment

App Runner services automatically get these variables:
- `PORT=8080` (hardcoded by App Runner)
- Configured in App Runner service settings via AWS Console or CLI

### Setting Environment Variables in App Runner
```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/..." \
  --source-configuration '{
    "ImageRepository": {
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "ENVIRONMENT": "production",
          "LOG_LEVEL": "INFO",
          "ANTHROPIC_API_KEY": "sk-ant-..."
        }
      }
    }
  }'
```

---

## Secrets Management

For production deployments:

1. **AWS Secrets Manager** - Recommended for API keys
2. **AWS Parameter Store** - For configuration values
3. **App Runner Instance Role** - For S3/other AWS service access

Never commit API keys to git. Use `.env.example` files as templates.
