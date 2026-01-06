# AWS Connection Guide

## Prerequisites

1. **AWS CLI** installed
2. **Docker** installed and running
3. **Terraform** installed (for infrastructure changes)

## Authentication Setup

### Step 1: Configure AWS Profile

The project uses the `sunwaretech` AWS profile.

```bash
# Check if profile exists
cat ~/.aws/config | grep sunwaretech

# If not configured, add to ~/.aws/config:
[profile sunwaretech]
region = us-east-1
output = json
```

### Step 2: Configure AWS Credentials

```bash
# Add to ~/.aws/credentials:
[sunwaretech]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

Or use SSO:
```bash
aws configure sso --profile sunwaretech
```

### Step 3: Verify Connection

```bash
# Test AWS identity
aws sts get-caller-identity --profile sunwaretech

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

## Environment Variables

Create/update `.env` in `eis-dynamics-poc/`:

```bash
# ===========================================
# AI PROVIDERS (Required for Agent Pipeline)
# ===========================================
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-proj-xxxxx

# ===========================================
# AWS SETTINGS
# ===========================================
AWS_PROFILE=sunwaretech
AWS_REGION=us-east-1

# ===========================================
# APPLICATION SETTINGS
# ===========================================
ENVIRONMENT=dev
DEBUG=true
LOG_LEVEL=INFO
```

## AWS Resources & Endpoints

| Resource | Value |
|----------|-------|
| **AWS Profile** | `sunwaretech` |
| **Region** | `us-east-1` |
| **Account** | (run `aws sts get-caller-identity`) |

### ECR Repositories
```bash
# List repositories
aws ecr describe-repositories --profile sunwaretech --query 'repositories[].repositoryName'

# Expected:
# - eis-dynamics-unified-api
# - eis-dynamics-agent-pipeline
```

### App Runner Services
```bash
# List services
aws apprunner list-services --profile sunwaretech --query 'ServiceSummaryList[].{Name:ServiceName,URL:ServiceUrl}'
```

### S3 Buckets
```bash
# List project buckets
aws s3 ls --profile sunwaretech | grep eis-dynamics

# Expected:
# - eis-dynamics-frontend-{account-id}
# - eis-dynamics-datalake-{account-id}
```

### Secrets Manager
```bash
# List secrets
aws secretsmanager list-secrets --profile sunwaretech --query 'SecretList[?starts_with(Name, `eis-dynamics`)].Name'

# Get secret value
aws secretsmanager get-secret-value --secret-id eis-dynamics/api-keys --profile sunwaretech
```

## Docker & ECR Authentication

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 --profile sunwaretech | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --profile sunwaretech --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

## Terraform State

```bash
cd eis-dynamics-poc/terraform/aws

# Initialize
terraform init

# Check current state
terraform show

# View outputs
terraform output
```

## Common Issues

### "Unable to locate credentials"
```bash
# Solution: Set AWS_PROFILE
export AWS_PROFILE=sunwaretech

# Or use --profile flag
aws s3 ls --profile sunwaretech
```

### "ECR login failed"
```bash
# Refresh ECR token (expires after 12 hours)
aws ecr get-login-password --region us-east-1 --profile sunwaretech | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### "App Runner deployment stuck"
```bash
# Check service status
aws apprunner describe-service --service-arn SERVICE_ARN --profile sunwaretech

# Force new deployment
aws apprunner start-deployment --service-arn SERVICE_ARN --profile sunwaretech
```

## Quick Connection Test

Run this script to verify all connections:

```bash
echo "=== AWS Connection Test ==="

echo "1. Identity:"
aws sts get-caller-identity --profile sunwaretech

echo "2. ECR Repositories:"
aws ecr describe-repositories --profile sunwaretech --query 'repositories[].repositoryName' --output table

echo "3. App Runner Services:"
aws apprunner list-services --profile sunwaretech --query 'ServiceSummaryList[].ServiceName' --output table

echo "4. S3 Buckets:"
aws s3 ls --profile sunwaretech | grep eis-dynamics

echo "=== Done ==="
```
