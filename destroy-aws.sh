#!/bin/bash
# =============================================================================
# PetInsure360 + EIS Dynamics - AWS Cleanup/Destroy Script
# =============================================================================
# WARNING: This script will DELETE all AWS resources created by deploy-aws.sh
# Use with caution! All data will be lost.
#
# Usage:
#   ./destroy-aws.sh              # Interactive mode (prompts for confirmation)
#   ./destroy-aws.sh --force      # Skip confirmation (use in CI/CD)
#   ./destroy-aws.sh --dry-run    # Show what would be deleted without deleting
# =============================================================================

set -e  # Exit on error

# =============================================================================
# CONFIGURATION (must match deploy-aws.sh)
# =============================================================================

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="611670815873"
AWS_PROFILE="sunwaretech"

# ECR repositories to delete
ECR_REPOS=(
    "claims-data-api"
    "agent-pipeline"
    "petinsure360-backend"
    "docgen-service"
)

# App Runner services to delete
APP_RUNNER_SERVICES=(
    "claims-data-api"
    "agent-pipeline"
    "petinsure360-backend"
    "docgen-service"
)

# S3 buckets to delete
S3_BUCKETS=(
    "petinsure360-customer-portal"
    "petinsure360-bi-dashboard"
    "eis-agent-portal"
    "eis-admin-portal"
)

# API Gateway WebSocket API name
WEBSOCKET_API_NAME="petinsure360-websocket"

# Lambda function names
LAMBDA_FUNCTIONS=(
    "petinsure360-websocket-handler"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_danger() {
    echo -e "${RED}[DANGER]${NC} $1"
}

# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

delete_app_runner_service() {
    local service_name=$1

    log_info "Checking App Runner service: $service_name"

    # Get service ARN
    local service_arn=$(aws apprunner list-services \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --query "ServiceSummaryList[?ServiceName=='$service_name'].ServiceArn" \
        --output text 2>/dev/null)

    if [ -z "$service_arn" ] || [ "$service_arn" == "None" ]; then
        log_warning "Service $service_name not found, skipping"
        return
    fi

    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY-RUN] Would delete App Runner service: $service_name ($service_arn)"
        return
    fi

    log_info "Deleting App Runner service: $service_name"
    aws apprunner delete-service \
        --service-arn "$service_arn" \
        --region $AWS_REGION \
        --profile $AWS_PROFILE

    log_success "Deleted App Runner service: $service_name"
}

delete_ecr_repository() {
    local repo_name=$1

    log_info "Checking ECR repository: $repo_name"

    if ! aws ecr describe-repositories \
        --repository-names $repo_name \
        --region $AWS_REGION \
        --profile $AWS_PROFILE &> /dev/null; then
        log_warning "Repository $repo_name not found, skipping"
        return
    fi

    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY-RUN] Would delete ECR repository: $repo_name"
        return
    fi

    log_info "Deleting ECR repository: $repo_name (including all images)"
    aws ecr delete-repository \
        --repository-name $repo_name \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --force

    log_success "Deleted ECR repository: $repo_name"
}

delete_s3_bucket() {
    local bucket_name=$1

    log_info "Checking S3 bucket: $bucket_name"

    if ! aws s3api head-bucket --bucket $bucket_name --profile $AWS_PROFILE 2>/dev/null; then
        log_warning "Bucket $bucket_name not found, skipping"
        return
    fi

    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY-RUN] Would delete S3 bucket: $bucket_name"
        return
    fi

    log_info "Emptying S3 bucket: $bucket_name"
    aws s3 rm s3://$bucket_name --recursive --profile $AWS_PROFILE

    log_info "Deleting S3 bucket: $bucket_name"
    aws s3api delete-bucket \
        --bucket $bucket_name \
        --region $AWS_REGION \
        --profile $AWS_PROFILE

    log_success "Deleted S3 bucket: $bucket_name"
}

delete_lambda_function() {
    local function_name=$1

    log_info "Checking Lambda function: $function_name"

    if ! aws lambda get-function \
        --function-name $function_name \
        --region $AWS_REGION \
        --profile $AWS_PROFILE &> /dev/null; then
        log_warning "Lambda function $function_name not found, skipping"
        return
    fi

    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY-RUN] Would delete Lambda function: $function_name"
        return
    fi

    log_info "Deleting Lambda function: $function_name"
    aws lambda delete-function \
        --function-name $function_name \
        --region $AWS_REGION \
        --profile $AWS_PROFILE

    log_success "Deleted Lambda function: $function_name"
}

delete_api_gateway_websocket() {
    log_info "Checking API Gateway WebSocket API: $WEBSOCKET_API_NAME"

    # Get API ID
    local api_id=$(aws apigatewayv2 get-apis \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --query "Items[?Name=='$WEBSOCKET_API_NAME'].ApiId" \
        --output text 2>/dev/null)

    if [ -z "$api_id" ] || [ "$api_id" == "None" ]; then
        log_warning "WebSocket API $WEBSOCKET_API_NAME not found, skipping"
        return
    fi

    if [ "$DRY_RUN" == "true" ]; then
        log_info "[DRY-RUN] Would delete API Gateway: $WEBSOCKET_API_NAME ($api_id)"
        return
    fi

    log_info "Deleting API Gateway WebSocket API: $WEBSOCKET_API_NAME"
    aws apigatewayv2 delete-api \
        --api-id "$api_id" \
        --region $AWS_REGION \
        --profile $AWS_PROFILE

    log_success "Deleted API Gateway WebSocket API: $WEBSOCKET_API_NAME"
}

# =============================================================================
# MAIN
# =============================================================================

DRY_RUN="false"
FORCE="false"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN="true"
            ;;
        --force)
            FORCE="true"
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--force]"
            echo ""
            echo "Options:"
            echo "  --dry-run   Show what would be deleted without actually deleting"
            echo "  --force     Skip confirmation prompt"
            echo ""
            exit 0
            ;;
    esac
done

echo ""
echo "=========================================="
log_danger "AWS RESOURCE CLEANUP SCRIPT"
echo "=========================================="
echo ""
echo "This script will DELETE the following AWS resources:"
echo ""
echo "App Runner Services:"
for svc in "${APP_RUNNER_SERVICES[@]}"; do
    echo "  - $svc"
done
echo ""
echo "ECR Repositories:"
for repo in "${ECR_REPOS[@]}"; do
    echo "  - $repo"
done
echo ""
echo "S3 Buckets:"
for bucket in "${S3_BUCKETS[@]}"; do
    echo "  - $bucket"
done
echo ""
echo "Lambda Functions:"
for fn in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "  - $fn"
done
echo ""
echo "API Gateway:"
echo "  - $WEBSOCKET_API_NAME (WebSocket)"
echo ""

if [ "$DRY_RUN" == "true" ]; then
    log_warning "DRY-RUN MODE: No resources will actually be deleted"
    echo ""
fi

# Confirmation prompt
if [ "$FORCE" != "true" ] && [ "$DRY_RUN" != "true" ]; then
    echo -e "${RED}WARNING: This action cannot be undone!${NC}"
    echo ""
    read -p "Type 'DELETE' to confirm destruction of all resources: " confirmation

    if [ "$confirmation" != "DELETE" ]; then
        log_info "Aborted. No resources were deleted."
        exit 0
    fi
fi

echo ""
log_info "Starting cleanup..."
echo ""

# 1. Delete App Runner services first (they reference ECR images)
log_info "=========================================="
log_info "Step 1: Deleting App Runner Services"
log_info "=========================================="
for service in "${APP_RUNNER_SERVICES[@]}"; do
    delete_app_runner_service "$service"
done

# 2. Delete Lambda functions (before API Gateway)
log_info "=========================================="
log_info "Step 2: Deleting Lambda Functions"
log_info "=========================================="
for fn in "${LAMBDA_FUNCTIONS[@]}"; do
    delete_lambda_function "$fn"
done

# 3. Delete API Gateway
log_info "=========================================="
log_info "Step 3: Deleting API Gateway"
log_info "=========================================="
delete_api_gateway_websocket

# 4. Delete S3 buckets
log_info "=========================================="
log_info "Step 4: Deleting S3 Buckets"
log_info "=========================================="
for bucket in "${S3_BUCKETS[@]}"; do
    delete_s3_bucket "$bucket"
done

# 5. Delete ECR repositories (after App Runner services are deleted)
log_info "=========================================="
log_info "Step 5: Deleting ECR Repositories"
log_info "=========================================="
for repo in "${ECR_REPOS[@]}"; do
    delete_ecr_repository "$repo"
done

echo ""
echo "=========================================="
if [ "$DRY_RUN" == "true" ]; then
    log_info "DRY-RUN COMPLETE - No resources were deleted"
else
    log_success "CLEANUP COMPLETE!"
fi
echo "=========================================="
echo ""

if [ "$DRY_RUN" != "true" ]; then
    echo "All PetInsure360 + EIS Dynamics AWS resources have been deleted."
    echo ""
    echo "To redeploy, run:"
    echo "  ./deploy-aws.sh"
    echo ""
fi
