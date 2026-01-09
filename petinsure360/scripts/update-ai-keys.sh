#!/bin/bash
set -e

echo "=== Updating AI Provider Keys ==="
export AWS_PROFILE=sunwaretech

# Navigate to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get API keys from .env
ENV_FILE="$SCRIPT_DIR/../../eis-dynamics-poc/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Error: .env file not found at $ENV_FILE"
  exit 1
fi

ANTHROPIC_KEY=$(grep ANTHROPIC_API_KEY "$ENV_FILE" | cut -d= -f2)
OPENAI_KEY=$(grep OPENAI_API_KEY "$ENV_FILE" | cut -d= -f2)

if [ -z "$ANTHROPIC_KEY" ] || [ -z "$OPENAI_KEY" ]; then
  echo "❌ Error: API keys not found in $ENV_FILE"
  echo "Please ensure ANTHROPIC_API_KEY and OPENAI_API_KEY are set"
  exit 1
fi

echo "Found API keys in $ENV_FILE"
echo "Updating claims-data-api App Runner service..."

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
  }" > /dev/null

echo ""
echo "✅ AI provider keys updated!"
echo ""
echo "Deployment in progress. Monitor status:"
echo "  watch -n 5 'aws apprunner describe-service --service-arn arn:aws:apprunner:us-east-1:611670815873:service/claims-data-api/b6e7e21cdb564c78bc3e69e9cd76f61d --region us-east-1 --query \"Service.Status\" --output text'"
echo ""
echo "Once RUNNING, test with:"
echo "  curl https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers"
