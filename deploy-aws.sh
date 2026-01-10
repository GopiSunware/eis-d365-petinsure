#!/bin/bash
# =============================================================================
# PetInsure360 + EIS Dynamics - AWS Deployment Script
# =============================================================================
# This is the GOLDEN SCRIPT for deploying all services to AWS
# Run this after a clean destroy to redeploy everything
#
# Usage:
#   ./deploy-aws.sh              # Deploy all services
#   ./deploy-aws.sh backend      # Deploy only backend services
#   ./deploy-aws.sh frontend     # Deploy only frontend
#   ./deploy-aws.sh claims-api   # Deploy specific service
# =============================================================================

set -e  # Exit on error

# =============================================================================
# CONFIGURATION
# =============================================================================

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="611670815873"
AWS_PROFILE="sunwaretech"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Service configurations
declare -A SERVICES=(
    ["claims-data-api"]="eis-dynamics-poc/src/shared/claims_data_api"
    ["agent-pipeline"]="eis-dynamics-poc/src/ws6_agent_pipeline"
    ["petinsure360-backend"]="petinsure360/backend"
)

# Frontend configurations (Vite-based - outputs to dist/)
declare -A FRONTENDS=(
    ["petinsure360-customer-portal"]="petinsure360/frontend"
    ["petinsure360-bi-dashboard"]="petinsure360/bi-dashboard"
)

# Next.js Frontend configurations (outputs to out/)
declare -A NEXTJS_FRONTENDS=(
    ["eis-agent-portal"]="eis-dynamics-poc/src/ws4_agent_portal"
    ["eis-admin-portal"]="eis-dynamics-poc/src/ws8_admin_portal/frontend"
)

# App Runner Service ARNs (update after first deployment)
declare -A SERVICE_ARNS=(
    ["claims-data-api"]="arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d"
    ["agent-pipeline"]="arn:aws:apprunner:us-east-1:611670815873:service/agent-pipeline/REPLACE_WITH_ARN"
    ["petinsure360-backend"]="arn:aws:apprunner:us-east-1:611670815873:service/petinsure360-backend/88915082265448db85d506782d32eaaf"
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

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not installed. Install from https://aws.amazon.com/cli/"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
        log_error "AWS credentials not configured for profile: $AWS_PROFILE"
        log_info "Run: aws configure --profile $AWS_PROFILE"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

ecr_login() {
    log_info "Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | \
        docker login --username AWS --password-stdin $ECR_REGISTRY
    log_success "ECR login successful"
}

# =============================================================================
# ECR FUNCTIONS
# =============================================================================

create_ecr_repo() {
    local repo_name=$1
    log_info "Creating ECR repository: $repo_name"

    if aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION --profile $AWS_PROFILE &> /dev/null; then
        log_warning "Repository $repo_name already exists"
    else
        aws ecr create-repository \
            --repository-name $repo_name \
            --region $AWS_REGION \
            --profile $AWS_PROFILE \
            --image-scanning-configuration scanOnPush=true
        log_success "Created ECR repository: $repo_name"
    fi
}

# =============================================================================
# BACKEND DEPLOYMENT FUNCTIONS
# =============================================================================

build_and_push_service() {
    local service_name=$1
    local service_path=$2

    log_info "Building and pushing $service_name..."

    # Navigate to service directory
    cd "$SCRIPT_DIR/$service_path"

    # Build Docker image
    log_info "Building Docker image for $service_name..."
    docker build --platform linux/amd64 -t $service_name:latest .

    # Tag for ECR
    docker tag $service_name:latest $ECR_REGISTRY/$service_name:latest

    # Push to ECR
    log_info "Pushing $service_name to ECR..."
    docker push $ECR_REGISTRY/$service_name:latest

    log_success "Pushed $service_name to ECR"

    cd "$SCRIPT_DIR"
}

trigger_app_runner_deployment() {
    local service_name=$1
    local service_arn=${SERVICE_ARNS[$service_name]}

    if [[ $service_arn == *"REPLACE_WITH_ARN"* ]]; then
        log_warning "Service ARN not configured for $service_name. Skipping deployment trigger."
        log_info "After creating App Runner service, update SERVICE_ARNS in this script"
        return
    fi

    log_info "Triggering App Runner deployment for $service_name..."

    aws apprunner start-deployment \
        --service-arn "$service_arn" \
        --region $AWS_REGION \
        --profile $AWS_PROFILE

    log_success "Deployment triggered for $service_name"
}

wait_for_deployment() {
    local service_name=$1
    local service_arn=${SERVICE_ARNS[$service_name]}

    if [[ $service_arn == *"REPLACE_WITH_ARN"* ]]; then
        return
    fi

    log_info "Waiting for $service_name deployment to complete..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        local status=$(aws apprunner describe-service \
            --service-arn "$service_arn" \
            --region $AWS_REGION \
            --profile $AWS_PROFILE \
            --query "Service.Status" \
            --output text)

        if [ "$status" == "RUNNING" ]; then
            log_success "$service_name is RUNNING"
            return 0
        elif [ "$status" == "OPERATION_IN_PROGRESS" ]; then
            echo -n "."
            sleep 10
            ((attempt++))
        else
            log_error "$service_name deployment failed with status: $status"
            return 1
        fi
    done

    log_error "Timeout waiting for $service_name deployment"
    return 1
}

# =============================================================================
# FRONTEND DEPLOYMENT FUNCTIONS
# =============================================================================

create_s3_bucket() {
    local bucket_name=$1

    log_info "Creating S3 bucket: $bucket_name"

    if aws s3api head-bucket --bucket $bucket_name --profile $AWS_PROFILE 2>/dev/null; then
        log_warning "Bucket $bucket_name already exists"
    else
        aws s3api create-bucket \
            --bucket $bucket_name \
            --region $AWS_REGION \
            --profile $AWS_PROFILE

        # Enable static website hosting
        aws s3 website s3://$bucket_name \
            --index-document index.html \
            --error-document index.html \
            --profile $AWS_PROFILE

        # Set bucket policy for public access
        aws s3api put-bucket-policy \
            --bucket $bucket_name \
            --profile $AWS_PROFILE \
            --policy "{
                \"Version\": \"2012-10-17\",
                \"Statement\": [{
                    \"Sid\": \"PublicReadGetObject\",
                    \"Effect\": \"Allow\",
                    \"Principal\": \"*\",
                    \"Action\": \"s3:GetObject\",
                    \"Resource\": \"arn:aws:s3:::$bucket_name/*\"
                }]
            }"

        # Disable block public access
        aws s3api put-public-access-block \
            --bucket $bucket_name \
            --profile $AWS_PROFILE \
            --public-access-block-configuration \
            "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

        log_success "Created S3 bucket: $bucket_name"
    fi
}

build_and_deploy_frontend() {
    local bucket_name=$1
    local frontend_path=$2
    local build_success=false

    log_info "Building and deploying $bucket_name..."

    cd "$SCRIPT_DIR/$frontend_path"

    # CRITICAL: Swap .env.local with .env.production for build
    # .env.local ALWAYS overrides .env.production, even in production builds!
    if [ -f ".env.local" ]; then
        log_info "Swapping .env.local -> .env.local.bak (using .env.production for build)"
        mv .env.local .env.local.bak
    fi

    # CRITICAL: Check .env.production exists
    if [ ! -f ".env.production" ]; then
        log_error ".env.production not found in $frontend_path!"
        log_error "Build would use wrong environment variables (localhost instead of AWS URLs)"
        # Restore backup
        [ -f ".env.local.bak" ] && mv .env.local.bak .env.local
        cd "$SCRIPT_DIR"
        return 1
    fi
    cp .env.production .env.local

    # Install dependencies and build with error handling
    if npm install && npm run build; then
        build_success=true
    else
        log_error "Build failed for $bucket_name"
    fi

    # ALWAYS restore .env.local for local development (even on failure)
    if [ -f ".env.local.bak" ]; then
        log_info "Restoring .env.local for local development"
        mv .env.local.bak .env.local
    else
        rm -f .env.local  # Remove the copy we made
    fi

    # Only upload if build succeeded
    if [ "$build_success" = true ]; then
        log_info "Uploading to S3..."
        aws s3 sync dist s3://$bucket_name --delete --profile $AWS_PROFILE
        log_success "Deployed $bucket_name"
        log_info "URL: http://$bucket_name.s3-website-$AWS_REGION.amazonaws.com"
    else
        log_error "Skipping S3 upload due to build failure"
        cd "$SCRIPT_DIR"
        return 1
    fi

    cd "$SCRIPT_DIR"
}

build_and_deploy_nextjs_frontend() {
    local bucket_name=$1
    local frontend_path=$2
    local build_success=false

    log_info "Building and deploying Next.js app: $bucket_name..."

    cd "$SCRIPT_DIR/$frontend_path"

    # CRITICAL: Swap .env.local with .env.production for build
    # .env.local ALWAYS overrides .env.production, even in production builds!
    if [ -f ".env.local" ]; then
        log_info "Swapping .env.local -> .env.local.bak (using .env.production for build)"
        mv .env.local .env.local.bak
    fi

    # CRITICAL: Check .env.production exists
    if [ ! -f ".env.production" ]; then
        log_error ".env.production not found in $frontend_path!"
        log_error "Build would use wrong environment variables (localhost instead of AWS URLs)"
        # Restore backup
        [ -f ".env.local.bak" ] && mv .env.local.bak .env.local
        cd "$SCRIPT_DIR"
        return 1
    fi
    cp .env.production .env.local

    # Install dependencies and build with error handling
    if npm install && STATIC_EXPORT=true npm run build; then
        build_success=true
    else
        log_error "Build failed for $bucket_name"
    fi

    # ALWAYS restore .env.local for local development (even on failure)
    if [ -f ".env.local.bak" ]; then
        log_info "Restoring .env.local for local development"
        mv .env.local.bak .env.local
    else
        rm -f .env.local  # Remove the copy we made
    fi

    # Only upload if build succeeded
    if [ "$build_success" = true ]; then
        log_info "Uploading to S3..."
        aws s3 sync out s3://$bucket_name --delete --profile $AWS_PROFILE
        log_success "Deployed $bucket_name"
        log_info "URL: http://$bucket_name.s3-website-$AWS_REGION.amazonaws.com"
    else
        log_error "Skipping S3 upload due to build failure"
        cd "$SCRIPT_DIR"
        return 1
    fi

    cd "$SCRIPT_DIR"
}

# =============================================================================
# CREATE APP RUNNER SERVICE (First-time setup)
# =============================================================================

create_app_runner_service() {
    local service_name=$1
    local ecr_image="$ECR_REGISTRY/$service_name:latest"
    local port=8080

    # Determine port based on service
    if [[ "$service_name" == "petinsure360-backend" ]]; then
        port=8000
    fi

    log_info "Creating App Runner service: $service_name"

    # Check if service already exists
    if aws apprunner list-services --region $AWS_REGION --profile $AWS_PROFILE \
        --query "ServiceSummaryList[?ServiceName=='$service_name'].ServiceArn" \
        --output text | grep -q "arn:aws"; then
        log_warning "Service $service_name already exists"
        return
    fi

    # Create service
    aws apprunner create-service \
        --service-name $service_name \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --source-configuration "{
            \"AuthenticationConfiguration\": {
                \"AccessRoleArn\": \"arn:aws:iam::$AWS_ACCOUNT_ID:role/AppRunnerECRAccessRole\"
            },
            \"AutoDeploymentsEnabled\": false,
            \"ImageRepository\": {
                \"ImageIdentifier\": \"$ecr_image\",
                \"ImageRepositoryType\": \"ECR\",
                \"ImageConfiguration\": {
                    \"Port\": \"$port\",
                    \"RuntimeEnvironmentVariables\": {
                        \"ENVIRONMENT\": \"production\",
                        \"LOG_LEVEL\": \"INFO\"
                    }
                }
            }
        }" \
        --instance-configuration "{
            \"Cpu\": \"1 vCPU\",
            \"Memory\": \"2 GB\"
        }" \
        --health-check-configuration "{
            \"Protocol\": \"HTTP\",
            \"Path\": \"/health\",
            \"Interval\": 10,
            \"Timeout\": 5,
            \"HealthyThreshold\": 1,
            \"UnhealthyThreshold\": 5
        }"

    log_success "Created App Runner service: $service_name"
    log_info "Get the ARN from AWS Console and update SERVICE_ARNS in this script"
}

# =============================================================================
# MAIN DEPLOYMENT FUNCTIONS
# =============================================================================

deploy_all_backends() {
    log_info "=========================================="
    log_info "Deploying all backend services"
    log_info "=========================================="

    ecr_login

    for service_name in "${!SERVICES[@]}"; do
        create_ecr_repo $service_name
        build_and_push_service $service_name "${SERVICES[$service_name]}"
        trigger_app_runner_deployment $service_name
    done

    log_info "Waiting for all deployments to complete..."
    for service_name in "${!SERVICES[@]}"; do
        wait_for_deployment $service_name
    done

    log_success "All backend services deployed!"
}

deploy_all_frontends() {
    log_info "=========================================="
    log_info "Deploying all frontend applications"
    log_info "=========================================="

    # Deploy Vite-based frontends (PetInsure360)
    for bucket_name in "${!FRONTENDS[@]}"; do
        create_s3_bucket $bucket_name
        build_and_deploy_frontend $bucket_name "${FRONTENDS[$bucket_name]}"
    done

    # Deploy Next.js frontends (EIS Dynamics)
    for bucket_name in "${!NEXTJS_FRONTENDS[@]}"; do
        create_s3_bucket $bucket_name
        build_and_deploy_nextjs_frontend $bucket_name "${NEXTJS_FRONTENDS[$bucket_name]}"
    done

    log_success "All frontend applications deployed!"
}

deploy_single_service() {
    local service_name=$1

    if [[ -v "SERVICES[$service_name]" ]]; then
        log_info "Deploying backend service: $service_name"
        ecr_login
        create_ecr_repo $service_name
        build_and_push_service $service_name "${SERVICES[$service_name]}"
        trigger_app_runner_deployment $service_name
        wait_for_deployment $service_name
    elif [[ -v "FRONTENDS[$service_name]" ]]; then
        log_info "Deploying Vite frontend: $service_name"
        create_s3_bucket $service_name
        build_and_deploy_frontend $service_name "${FRONTENDS[$service_name]}"
    elif [[ -v "NEXTJS_FRONTENDS[$service_name]" ]]; then
        log_info "Deploying Next.js frontend: $service_name"
        create_s3_bucket $service_name
        build_and_deploy_nextjs_frontend $service_name "${NEXTJS_FRONTENDS[$service_name]}"
    else
        log_error "Unknown service: $service_name"
        log_info "Available services:"
        log_info "  Backends: ${!SERVICES[@]}"
        log_info "  Vite Frontends: ${!FRONTENDS[@]}"
        log_info "  Next.js Frontends: ${!NEXTJS_FRONTENDS[@]}"
        exit 1
    fi
}

show_status() {
    log_info "=========================================="
    log_info "Current Deployment Status"
    log_info "=========================================="

    echo ""
    log_info "App Runner Services:"
    aws apprunner list-services \
        --region $AWS_REGION \
        --profile $AWS_PROFILE \
        --query "ServiceSummaryList[].{Name:ServiceName,Status:Status,URL:ServiceUrl}" \
        --output table

    echo ""
    log_info "S3 Buckets (PetInsure360):"
    for bucket_name in "${!FRONTENDS[@]}"; do
        if aws s3api head-bucket --bucket $bucket_name --profile $AWS_PROFILE 2>/dev/null; then
            echo "  $bucket_name: http://$bucket_name.s3-website-$AWS_REGION.amazonaws.com"
        else
            echo "  $bucket_name: NOT DEPLOYED"
        fi
    done

    echo ""
    log_info "S3 Buckets (EIS Dynamics):"
    for bucket_name in "${!NEXTJS_FRONTENDS[@]}"; do
        if aws s3api head-bucket --bucket $bucket_name --profile $AWS_PROFILE 2>/dev/null; then
            echo "  $bucket_name: http://$bucket_name.s3-website-$AWS_REGION.amazonaws.com"
        else
            echo "  $bucket_name: NOT DEPLOYED"
        fi
    done
}

# =============================================================================
# MAIN
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

check_prerequisites

case "${1:-all}" in
    "all")
        deploy_all_backends
        deploy_all_frontends
        show_status
        ;;
    "backend"|"backends")
        deploy_all_backends
        ;;
    "frontend"|"frontends")
        deploy_all_frontends
        ;;
    "status")
        show_status
        ;;
    "create-services")
        # First-time setup: create App Runner services
        ecr_login
        for service_name in "${!SERVICES[@]}"; do
            create_ecr_repo $service_name
            build_and_push_service $service_name "${SERVICES[$service_name]}"
            create_app_runner_service $service_name
        done
        ;;
    *)
        deploy_single_service "$1"
        ;;
esac

log_success "Deployment complete!"

# =============================================================================
# POST-DEPLOYMENT: SEED DEMO DATA
# =============================================================================

seed_demo_data() {
    log_info "=========================================="
    log_info "Seeding Demo Data"
    log_info "=========================================="

    # PetInsure360 Backend - Seed demo customers, pets, policies
    log_info "Seeding PetInsure360 demo data..."
    PETINSURE_URL="https://fucf3fwwwv.us-east-1.awsapprunner.com"

    # Check if backend is healthy
    if curl -s "$PETINSURE_URL/health" | grep -q "healthy"; then
        # Seed demo data
        SEED_RESULT=$(curl -s -X POST "$PETINSURE_URL/api/customers/seed-demo")
        if echo "$SEED_RESULT" | grep -q "success"; then
            log_success "Demo data seeded: $SEED_RESULT"
        else
            log_warning "Seed response: $SEED_RESULT"
        fi
    else
        log_warning "PetInsure360 backend not healthy, skipping seed"
    fi

    echo ""
    log_info "Demo Login Credentials:"
    echo "  Primary:   demo@demologin.com"
    echo "  Secondary: demo1@demologin.com"
    echo "  Tertiary:  demo2@demologin.com"
    echo ""
    log_info "Each demo user has pets and policies pre-configured."
}

# Run demo data seeding
seed_demo_data

echo ""
echo "=========================================="
echo "DEPLOYED SERVICES"
echo "=========================================="
echo ""
echo "Backend APIs:"
echo "  Claims Data API:      https://9wvcjmrknc.us-east-1.awsapprunner.com"
echo "  Agent Pipeline:       https://qi2p3x5gsm.us-east-1.awsapprunner.com"
echo "  PetInsure360 Backend: https://fucf3fwwwv.us-east-1.awsapprunner.com"
echo ""
echo "PetInsure360 Frontends:"
echo "  Customer Portal: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com"
echo "  BI Dashboard:    http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com"
echo ""
echo "EIS Dynamics Frontends:"
echo "  Agent Portal:    http://eis-agent-portal.s3-website-us-east-1.amazonaws.com"
echo "  Admin Portal:    http://eis-admin-portal.s3-website-us-east-1.amazonaws.com"
echo ""
echo "WebSocket:"
echo "  wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod"
echo ""
