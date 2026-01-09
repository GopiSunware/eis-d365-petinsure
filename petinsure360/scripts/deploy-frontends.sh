#!/bin/bash
set -e

echo "=== Deploying PetInsure360 Frontends ==="
export AWS_PROFILE=sunwaretech

# Navigate to petinsure360 directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Deploy Customer Portal
echo ""
echo "=== Customer Portal ==="
cd frontend

echo "Building Customer Portal..."
npm run build

echo "Deploying Customer Portal to S3..."
aws s3 sync dist/ s3://petinsure360-customer-portal --delete
echo "✅ Customer Portal deployed!"
echo "URL: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com"

# Deploy BI Dashboard
echo ""
echo "=== BI Dashboard ==="
cd ../bi-dashboard

echo "Building BI Dashboard..."
npm run build

echo "Deploying BI Dashboard to S3..."
aws s3 sync dist/ s3://petinsure360-bi-dashboard --delete
echo "✅ BI Dashboard deployed!"
echo "URL: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com"

echo ""
echo "=== Frontend deployment complete! ==="
