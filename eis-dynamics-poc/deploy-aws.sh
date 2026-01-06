#!/bin/bash
# EIS-Dynamics AWS Deployment Script
# Usage: ./deploy-aws.sh [init|plan|apply|build|push|all]

set -e

# Configuration
export AWS_PROFILE=sunwaretech
export AWS_REGION=us-east-1
PROJECT_NAME="eis-dynamics"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_DIR="$PROJECT_DIR/terraform/aws"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text
}

# Initialize Terraform
tf_init() {
    log_info "Initializing Terraform..."
    cd "$TERRAFORM_DIR"
    terraform init
}

# Plan Terraform changes
tf_plan() {
    log_info "Planning Terraform changes..."
    cd "$TERRAFORM_DIR"
    terraform plan -out=tfplan
}

# Apply Terraform changes
tf_apply() {
    log_info "Applying Terraform changes..."
    cd "$TERRAFORM_DIR"
    terraform apply tfplan
}

# Build Docker images
docker_build() {
    log_info "Building Docker images..."

    # Build Unified Claims API
    log_info "Building Unified Claims API..."
    cd "$PROJECT_DIR/src/shared/claims_data_api"
    docker build -t ${PROJECT_NAME}-unified-api:latest .

    # Build Agent Pipeline
    log_info "Building Agent Pipeline..."
    cd "$PROJECT_DIR/src/ws6_agent_pipeline"
    docker build -t ${PROJECT_NAME}-agent-pipeline:latest .

    log_info "Docker builds complete!"
}

# Push images to ECR
docker_push() {
    log_info "Pushing Docker images to ECR..."

    ACCOUNT_ID=$(get_account_id)
    ECR_URL="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

    # Tag and push Unified API
    log_info "Pushing Unified Claims API..."
    docker tag ${PROJECT_NAME}-unified-api:latest ${ECR_URL}/${PROJECT_NAME}-unified-api:latest
    docker push ${ECR_URL}/${PROJECT_NAME}-unified-api:latest

    # Tag and push Agent Pipeline
    log_info "Pushing Agent Pipeline..."
    docker tag ${PROJECT_NAME}-agent-pipeline:latest ${ECR_URL}/${PROJECT_NAME}-agent-pipeline:latest
    docker push ${ECR_URL}/${PROJECT_NAME}-agent-pipeline:latest

    log_info "Images pushed to ECR!"
}

# Build frontend and deploy to S3
deploy_frontend() {
    log_info "Building and deploying frontend..."

    cd "$PROJECT_DIR/src/ws4_agent_portal"

    # Build Next.js app
    npm run build

    # Get S3 bucket from Terraform output
    BUCKET=$(cd "$TERRAFORM_DIR" && terraform output -raw frontend_bucket 2>/dev/null || echo "")

    if [ -z "$BUCKET" ]; then
        log_error "Frontend bucket not found. Run terraform apply first."
        exit 1
    fi

    # Sync to S3
    log_info "Syncing to S3 bucket: $BUCKET"
    aws s3 sync out/ s3://$BUCKET/ --delete

    log_info "Frontend deployed!"
}

# Show outputs
show_outputs() {
    log_info "Deployment outputs:"
    cd "$TERRAFORM_DIR"
    terraform output
}

# Full deployment
deploy_all() {
    tf_init
    tf_plan
    tf_apply
    docker_build
    docker_push
    # deploy_frontend  # Uncomment when frontend is ready
    show_outputs
}

# Main
case "${1:-help}" in
    init)
        tf_init
        ;;
    plan)
        tf_plan
        ;;
    apply)
        tf_apply
        ;;
    build)
        docker_build
        ;;
    push)
        docker_push
        ;;
    frontend)
        deploy_frontend
        ;;
    outputs)
        show_outputs
        ;;
    all)
        deploy_all
        ;;
    *)
        echo "EIS-Dynamics AWS Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  init      - Initialize Terraform"
        echo "  plan      - Plan Terraform changes"
        echo "  apply     - Apply Terraform changes"
        echo "  build     - Build Docker images locally"
        echo "  push      - Push Docker images to ECR"
        echo "  frontend  - Build and deploy frontend to S3"
        echo "  outputs   - Show Terraform outputs"
        echo "  all       - Run full deployment"
        echo ""
        ;;
esac
