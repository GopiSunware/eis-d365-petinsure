---
name: deploy-aws
description: Deploy EIS-Dynamics POC to AWS using App Runner, ECR, and S3. Use when deploying to AWS, pushing Docker images, running terraform, updating production, or checking AWS deployment status.
allowed-tools: Read, Bash, Grep, Glob
---

# AWS Deployment for EIS-Dynamics POC

## Overview

Deploy the EIS-Dynamics pet insurance claims processing system to AWS infrastructure:
- **App Runner**: Unified Claims API (port 8000) + Agent Pipeline (port 8006)
- **ECR**: Docker image registry
- **S3**: Frontend hosting + Data Lake (medallion architecture)
- **Secrets Manager**: API keys (Anthropic, OpenAI)

## Live URLs

| Service | URL |
|---------|-----|
| Unified Claims API | https://p7qrmgi9sp.us-east-1.awsapprunner.com |
| Agent Pipeline | https://bn9ymuxtwp.us-east-1.awsapprunner.com |
| API Docs | https://p7qrmgi9sp.us-east-1.awsapprunner.com/docs |

## Connection Setup

**First time?** See [CONNECTION.md](CONNECTION.md) for full authentication setup.

### Quick Connection Check
```bash
# Verify AWS access
aws sts get-caller-identity --profile sunwaretech

# Test ECR access
aws ecr describe-repositories --profile sunwaretech --query 'repositories[].repositoryName'
```

## Quick Commands

### Check Deployment Status
```bash
# Health check - Unified API
curl -s https://p7qrmgi9sp.us-east-1.awsapprunner.com/ | head -20

# Health check - Agent Pipeline
curl -s https://bn9ymuxtwp.us-east-1.awsapprunner.com/api/v1/scenarios/ | head -20

# Check AWS identity
aws sts get-caller-identity --profile sunwaretech
```

### Full Deployment
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc
./deploy-aws.sh all
```

### Step-by-Step Deployment

#### 1. Initialize Terraform
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc
./deploy-aws.sh init
```

#### 2. Plan Infrastructure Changes
```bash
./deploy-aws.sh plan
```

#### 3. Apply Infrastructure
```bash
./deploy-aws.sh apply
```

#### 4. Build Docker Images
```bash
./deploy-aws.sh build
```

#### 5. Push to ECR
```bash
./deploy-aws.sh push
```

#### 6. Deploy Frontend (Optional)
```bash
./deploy-aws.sh frontend
```

#### 7. View Outputs
```bash
./deploy-aws.sh outputs
```

## Manual Docker Commands

### Build Unified Claims API
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/shared/claims_data_api
docker build -t eis-dynamics-unified-api:latest .
```

### Build Agent Pipeline
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline
docker build -t eis-dynamics-agent-pipeline:latest .
```

### Push to ECR
```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text --profile sunwaretech)
ECR_URL="${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com"

# Login to ECR
aws ecr get-login-password --region us-east-1 --profile sunwaretech | docker login --username AWS --password-stdin $ECR_URL

# Tag and push
docker tag eis-dynamics-unified-api:latest ${ECR_URL}/eis-dynamics-unified-api:latest
docker push ${ECR_URL}/eis-dynamics-unified-api:latest

docker tag eis-dynamics-agent-pipeline:latest ${ECR_URL}/eis-dynamics-agent-pipeline:latest
docker push ${ECR_URL}/eis-dynamics-agent-pipeline:latest
```

## Terraform Resources

Located in: `eis-dynamics-poc/terraform/aws/main.tf`

| Resource | Name | Purpose |
|----------|------|---------|
| ECR | eis-dynamics-unified-api | Docker images for Claims API |
| ECR | eis-dynamics-agent-pipeline | Docker images for Agent Pipeline |
| App Runner | eis-dynamics-unified-api | Hosts Claims API (8000) |
| App Runner | eis-dynamics-agent-pipeline | Hosts Agent Pipeline (8006) |
| S3 | eis-dynamics-frontend-* | Static website hosting |
| S3 | eis-dynamics-datalake-* | Medallion data lake |
| Secrets Manager | eis-dynamics/api-keys | API keys storage |

## Environment Variables

### Unified Claims API
- `ENVIRONMENT`: dev/prod
- `LOG_LEVEL`: INFO
- `S3_DATALAKE_BUCKET`: Data lake bucket name
- `AWS_REGION`: us-east-1

### Agent Pipeline
- `ENVIRONMENT`: dev/prod
- `LOG_LEVEL`: INFO
- `UNIFIED_API_URL`: URL to Claims API
- `AI_PROVIDER`: claude
- `ANTHROPIC_API_KEY`: From Secrets Manager

## Troubleshooting

### Check App Runner Logs
```bash
aws logs describe-log-groups --profile sunwaretech | grep apprunner
aws logs tail /aws/apprunner/eis-dynamics-unified-api --follow --profile sunwaretech
```

### Check ECR Images
```bash
aws ecr describe-images --repository-name eis-dynamics-unified-api --profile sunwaretech
aws ecr describe-images --repository-name eis-dynamics-agent-pipeline --profile sunwaretech
```

### Force Redeploy
```bash
# Update App Runner to pull latest image
aws apprunner start-deployment --service-arn <service-arn> --profile sunwaretech
```

## Configuration

AWS Profile: `sunwaretech`
Region: `us-east-1`
Project: `eis-dynamics`

## Cost Estimate

| Resource | Monthly Cost |
|----------|-------------|
| App Runner (2 services) | ~$50-100 |
| ECR Storage | ~$1-5 |
| S3 Storage | ~$1-5 |
| Secrets Manager | ~$1 |
| **Total** | **~$55-110/month** |
