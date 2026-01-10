#!/bin/bash
set -e

echo "=== Deploying PetInsure360 Frontends ==="
export AWS_PROFILE=sunwaretech

# Navigate to petinsure360 directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# =============================================================================
# CRITICAL: .env.local handling
# =============================================================================
# .env.local ALWAYS overrides .env.production, even during production builds!
# This function swaps .env files to ensure production builds use correct URLs.
# =============================================================================

swap_env_for_build() {
    if [ -f ".env.local" ]; then
        echo "  📝 Swapping .env.local -> .env.local.bak (using .env.production for build)"
        mv .env.local .env.local.bak
    fi
    if [ -f ".env.production" ]; then
        cp .env.production .env.local
    fi
}

restore_env_after_build() {
    if [ -f ".env.local.bak" ]; then
        echo "  📝 Restoring .env.local for local development"
        mv .env.local.bak .env.local
    elif [ -f ".env.production" ]; then
        rm -f .env.local
    fi
}

# Deploy Customer Portal
echo ""
echo "=== Customer Portal ==="
cd frontend

swap_env_for_build

echo "Building Customer Portal..."
npm run build

restore_env_after_build

echo "Deploying Customer Portal to S3..."
aws s3 sync dist/ s3://petinsure360-customer-portal --delete
echo "✅ Customer Portal deployed!"
echo "URL: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com"

# Deploy BI Dashboard
echo ""
echo "=== BI Dashboard ==="
cd ../bi-dashboard

swap_env_for_build

echo "Building BI Dashboard..."
npm run build

restore_env_after_build

echo "Deploying BI Dashboard to S3..."
aws s3 sync dist/ s3://petinsure360-bi-dashboard --delete
echo "✅ BI Dashboard deployed!"
echo "URL: http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com"

echo ""
echo "=== Frontend deployment complete! ==="
echo ""
echo "⚠️  REMINDER: Test that frontends are NOT calling localhost:"
echo "   curl -s http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com/ | grep -o 'localhost' || echo '✅ No localhost references'"
echo ""
