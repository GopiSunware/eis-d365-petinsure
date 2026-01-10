#!/bin/bash
# =============================================================================
# Update AI Provider Keys in AWS App Runner
# =============================================================================
# This script updates the ANTHROPIC_API_KEY and OPENAI_API_KEY environment
# variables in the claims-data-api App Runner service.
#
# Usage:
#   ./update-ai-keys.sh          # Update AI keys from eis-dynamics-poc/.env
#   ./update-ai-keys.sh --check  # Check current status without updating
# =============================================================================

set -e

# Configuration
AWS_PROFILE="sunwaretech"
AWS_REGION="us-east-1"
SERVICE_ARN="arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d"
ECR_IMAGE="611670815873.dkr.ecr.us-east-1.amazonaws.com/claims-data-api:latest"
API_URL="https://9wvcjmrknc.us-east-1.awsapprunner.com"

export AWS_PROFILE

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/../../eis-dynamics-poc/.env"

# Check status only
if [ "$1" == "--check" ]; then
  echo "=== Checking AI Provider Status ==="
  echo ""
  log_info "App Runner service status:"
  aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$AWS_REGION" \
    --query "Service.{Status:Status,URL:ServiceUrl}" --output table
  echo ""
  log_info "AI providers status:"
  curl -s "$API_URL/api/chat/providers" | jq '.providers | to_entries[] | {name: .key, enabled: .value.enabled}'
  exit 0
fi

echo "=== Updating AI Provider Keys ==="

# Validate .env file
if [ ! -f "$ENV_FILE" ]; then
  log_error ".env file not found at $ENV_FILE"
  exit 1
fi

# Extract API keys
ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" "$ENV_FILE" | cut -d= -f2)
OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d= -f2)

if [ -z "$ANTHROPIC_KEY" ] || [ -z "$OPENAI_KEY" ]; then
  log_error "API keys not found in $ENV_FILE"
  echo "Please ensure ANTHROPIC_API_KEY and OPENAI_API_KEY are set"
  exit 1
fi

log_info "Found API keys in $ENV_FILE"
log_info "Updating claims-data-api App Runner service..."

# Update App Runner with all required environment variables
aws apprunner update-service \
  --service-arn "$SERVICE_ARN" \
  --region "$AWS_REGION" \
  --source-configuration "{
    \"AutoDeploymentsEnabled\": true,
    \"ImageRepository\": {
      \"ImageIdentifier\": \"$ECR_IMAGE\",
      \"ImageRepositoryType\": \"ECR\",
      \"ImageConfiguration\": {
        \"Port\": \"8080\",
        \"RuntimeEnvironmentVariables\": {
          \"ANTHROPIC_API_KEY\": \"$ANTHROPIC_KEY\",
          \"OPENAI_API_KEY\": \"$OPENAI_KEY\",
          \"ENVIRONMENT\": \"production\",
          \"LOG_LEVEL\": \"INFO\",
          \"CORS_ORIGINS\": \"[\\\"*\\\"]\"
        }
      }
    }
  }" > /dev/null

log_success "AI provider keys updated!"
echo ""
log_info "Deployment in progress. Wait 2-5 minutes for completion."
echo ""
echo "Monitor status:"
echo "  watch -n 10 'aws apprunner describe-service --service-arn $SERVICE_ARN --region $AWS_REGION --query \"Service.Status\" --output text --profile $AWS_PROFILE'"
echo ""
echo "Or run: $0 --check"
echo ""
echo "Test endpoints:"
echo "  curl $API_URL/api/chat/providers"
echo "  curl $API_URL/api/pipeline/status"
