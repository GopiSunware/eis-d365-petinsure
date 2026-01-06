#!/bin/bash
# AWS Connection Test Script for EIS-Dynamics
# Tests all AWS service connections

set -e

AWS_PROFILE="sunwaretech"
AWS_REGION="us-east-1"

echo "=============================================="
echo "  AWS Connection Test - EIS-Dynamics"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✅ PASS${NC}: $1"; }
fail() { echo -e "${RED}❌ FAIL${NC}: $1"; }
warn() { echo -e "${YELLOW}⚠️  WARN${NC}: $1"; }

echo "1. AWS Identity"
echo "   ─────────────"
if aws sts get-caller-identity --profile $AWS_PROFILE &>/dev/null; then
    ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
    USER=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Arn --output text)
    pass "Authenticated"
    echo "      Account: $ACCOUNT"
    echo "      User: $USER"
else
    fail "Cannot authenticate with AWS"
    echo ""
    echo "   Fix: Configure AWS credentials"
    echo "   aws configure --profile sunwaretech"
    exit 1
fi

echo ""
echo "2. ECR Repositories"
echo "   ─────────────────"
REPOS=$(aws ecr describe-repositories --profile $AWS_PROFILE --query 'repositories[].repositoryName' --output text 2>/dev/null || echo "")
if [[ "$REPOS" == *"eis-dynamics"* ]]; then
    pass "ECR repositories found"
    for repo in $REPOS; do
        if [[ "$repo" == *"eis-dynamics"* ]]; then
            echo "      - $repo"
        fi
    done
else
    warn "No eis-dynamics ECR repositories found"
    echo "      Run: terraform apply to create them"
fi

echo ""
echo "3. App Runner Services"
echo "   ────────────────────"
SERVICES=$(aws apprunner list-services --profile $AWS_PROFILE --query 'ServiceSummaryList[].ServiceName' --output text 2>/dev/null || echo "")
if [[ "$SERVICES" == *"eis-dynamics"* ]]; then
    pass "App Runner services found"
    aws apprunner list-services --profile $AWS_PROFILE \
        --query 'ServiceSummaryList[?contains(ServiceName, `eis-dynamics`)].{Name:ServiceName,Status:Status}' \
        --output table
else
    warn "No eis-dynamics App Runner services found"
    echo "      Run: terraform apply to create them"
fi

echo ""
echo "4. S3 Buckets"
echo "   ──────────"
BUCKETS=$(aws s3 ls --profile $AWS_PROFILE 2>/dev/null | grep eis-dynamics || echo "")
if [ -n "$BUCKETS" ]; then
    pass "S3 buckets found"
    echo "$BUCKETS" | while read line; do
        echo "      $line"
    done
else
    warn "No eis-dynamics S3 buckets found"
fi

echo ""
echo "5. Secrets Manager"
echo "   ────────────────"
SECRETS=$(aws secretsmanager list-secrets --profile $AWS_PROFILE \
    --query "SecretList[?contains(Name, 'eis-dynamics')].Name" --output text 2>/dev/null || echo "")
if [ -n "$SECRETS" ]; then
    pass "Secrets found"
    for secret in $SECRETS; do
        echo "      - $secret"
    done
else
    warn "No eis-dynamics secrets found"
fi

echo ""
echo "6. Docker"
echo "   ──────"
if docker info &>/dev/null; then
    pass "Docker is running"
else
    fail "Docker is not running"
    echo "      Start Docker Desktop or docker service"
fi

echo ""
echo "7. ECR Login Test"
echo "   ───────────────"
ECR_URL="${ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
if aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE 2>/dev/null | \
   docker login --username AWS --password-stdin $ECR_URL &>/dev/null; then
    pass "ECR login successful"
    echo "      Registry: $ECR_URL"
else
    fail "ECR login failed"
fi

echo ""
echo "=============================================="
echo "  Connection Test Complete"
echo "=============================================="
