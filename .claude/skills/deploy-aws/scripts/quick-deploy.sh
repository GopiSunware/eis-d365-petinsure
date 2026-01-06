#!/bin/bash
# Quick Deploy Script for EIS-Dynamics to AWS
# Usage: ./quick-deploy.sh [api|pipeline|all]

set -e

PROJECT_DIR="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
AWS_PROFILE="sunwaretech"
AWS_REGION="us-east-1"

echo "=== EIS-Dynamics Quick Deploy ==="

get_account_id() {
    aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE
}

deploy_api() {
    echo ""
    echo ">>> Building Unified Claims API..."
    cd "$PROJECT_DIR/src/shared/claims_data_api"
    docker build -t eis-dynamics-unified-api:latest .

    echo ""
    echo ">>> Pushing to ECR..."
    ACCOUNT_ID=$(get_account_id)
    ECR_URL="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_URL
    docker tag eis-dynamics-unified-api:latest ${ECR_URL}/eis-dynamics-unified-api:latest
    docker push ${ECR_URL}/eis-dynamics-unified-api:latest

    echo "✅ Unified API deployed!"
}

deploy_pipeline() {
    echo ""
    echo ">>> Building Agent Pipeline..."
    cd "$PROJECT_DIR/src/ws6_agent_pipeline"
    docker build -t eis-dynamics-agent-pipeline:latest .

    echo ""
    echo ">>> Pushing to ECR..."
    ACCOUNT_ID=$(get_account_id)
    ECR_URL="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_URL
    docker tag eis-dynamics-agent-pipeline:latest ${ECR_URL}/eis-dynamics-agent-pipeline:latest
    docker push ${ECR_URL}/eis-dynamics-agent-pipeline:latest

    echo "✅ Agent Pipeline deployed!"
}

case "${1:-all}" in
    api)
        deploy_api
        ;;
    pipeline)
        deploy_pipeline
        ;;
    all)
        deploy_api
        deploy_pipeline
        ;;
    *)
        echo "Usage: $0 [api|pipeline|all]"
        exit 1
        ;;
esac

echo ""
echo "=== Deployment Complete ==="
echo "URLs:"
echo "  Claims API: https://p7qrmgi9sp.us-east-1.awsapprunner.com"
echo "  Pipeline:   https://bn9ymuxtwp.us-east-1.awsapprunner.com"
