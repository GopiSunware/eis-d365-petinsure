#!/bin/bash
set -e

echo "=== Deploying PetInsure360 Backend ==="
export AWS_PROFILE=sunwaretech

# Navigate to backend directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../backend"

# Build Docker image
echo "Building Docker image..."
docker build -t petinsure360-backend:latest .

# Tag for ECR
echo "Tagging image for ECR..."
docker tag petinsure360-backend:latest \
  611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  611670815873.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
echo "Pushing image to ECR..."
docker push 611670815873.dkr.ecr.us-east-1.amazonaws.com/petinsure360-backend:latest

# Trigger deployment
echo "Triggering App Runner deployment..."
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:us-east-1:611670815873:service/petinsure360-backend/88915082265448db85d506782d32eaaf \
  --region us-east-1

echo ""
echo "✅ Backend deployment triggered!"
echo "URL: https://fucf3fwwwv.us-east-1.awsapprunner.com"
echo ""
echo "Monitor deployment:"
echo "  aws apprunner describe-service --service-arn arn:aws:apprunner:us-east-1:611670815873:service/petinsure360-backend/88915082265448db85d506782d32eaaf --region us-east-1 --query 'Service.Status'"
