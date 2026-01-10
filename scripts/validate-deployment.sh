#!/bin/bash
# =============================================================================
# Pre-Deployment Validation Script
# =============================================================================
# Run this before deploying to catch common issues early
#
# Usage:
#   ./scripts/validate-deployment.sh
#   ./scripts/validate-deployment.sh --fix    # Attempt auto-fixes
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((ERRORS++)); }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARNINGS++)); }

echo "=============================================="
echo "Pre-Deployment Validation"
echo "=============================================="
echo ""

# =============================================================================
# 1. DOCKER & DATA FILES
# =============================================================================
echo "--- Docker & Data Files ---"

# Check Dockerfile copies synthetic data
if grep -q "COPY data/raw/" petinsure360/backend/Dockerfile; then
    log_pass "Dockerfile copies data/raw/ folder"
else
    log_fail "Dockerfile missing 'COPY data/raw/' - synthetic data won't be in container!"
fi

# Check synthetic data files exist
DATA_DIR="petinsure360/backend/data/raw"
declare -A DATA_FILES=(
    ["customers.csv"]=5000
    ["pets.csv"]=6000
    ["policies.csv"]=6000
    ["claims.jsonl"]=10000
)

for file in "${!DATA_FILES[@]}"; do
    min_lines=${DATA_FILES[$file]}
    if [ -f "$DATA_DIR/$file" ]; then
        lines=$(wc -l < "$DATA_DIR/$file")
        if [ "$lines" -ge "$min_lines" ]; then
            log_pass "$file exists ($lines lines)"
        else
            log_warn "$file has only $lines lines (expected $min_lines+)"
        fi
    else
        log_fail "$file not found in $DATA_DIR"
    fi
done

# Check scenarios file
if [ -f "petinsure360/backend/data/claim_scenarios.json" ]; then
    log_pass "claim_scenarios.json exists"
else
    log_fail "claim_scenarios.json not found"
fi

echo ""

# =============================================================================
# 2. ENVIRONMENT FILES
# =============================================================================
echo "--- Environment Files (.env.production) ---"

declare -A ENV_FILES=(
    ["petinsure360/frontend/.env.production"]="VITE_API_URL"
    ["petinsure360/bi-dashboard/.env.production"]="VITE_API_URL"
    ["eis-dynamics-poc/src/ws4_agent_portal/.env.production"]="NEXT_PUBLIC"
    ["eis-dynamics-poc/src/ws8_admin_portal/frontend/.env.production"]="NEXT_PUBLIC"
)

for env_file in "${!ENV_FILES[@]}"; do
    if [ -f "$env_file" ]; then
        # Check for localhost (should NOT have localhost in production)
        if grep -q "localhost" "$env_file"; then
            log_fail "$env_file contains 'localhost' - will fail in production!"
        else
            log_pass "$env_file has no localhost references"
        fi

        # Check key variable exists
        key="${ENV_FILES[$env_file]}"
        if grep -q "$key" "$env_file"; then
            log_pass "$env_file has $key configured"
        else
            log_warn "$env_file missing $key"
        fi
    else
        log_fail "$env_file not found"
    fi
done

echo ""

# =============================================================================
# 3. SERVICE ARNs
# =============================================================================
echo "--- Service ARNs (deploy-aws.sh) ---"

# Check only the SERVICE_ARNS array (not conditional logic)
if grep -A 5 "declare -A SERVICE_ARNS" deploy-aws.sh | grep -q "REPLACE_WITH_ARN"; then
    log_warn "deploy-aws.sh has placeholder ARNs (REPLACE_WITH_ARN)"
    echo "       Run: aws apprunner list-services --profile sunwaretech --query 'ServiceSummaryList[*].[ServiceName,ServiceArn]' --output table"
else
    log_pass "All service ARNs configured in deploy-aws.sh"
fi

echo ""

# =============================================================================
# 4. API SERVICE FILES
# =============================================================================
echo "--- Required API Service Files ---"

SERVICES_DIR="eis-dynamics-poc/src/shared/claims_data_api/app/services"
REQUIRED_SERVICES=(
    "admin_config_service.py"
    "approvals_service.py"
    "audit_service.py"
    "costs_service.py"
    "azure_data_service.py"
    "chat_service.py"
)

for service in "${REQUIRED_SERVICES[@]}"; do
    if [ -f "$SERVICES_DIR/$service" ]; then
        log_pass "$service exists"
    else
        log_fail "$service not found - Admin Portal will show 404 errors!"
    fi
done

echo ""

# =============================================================================
# 5. LOGIN DEFAULT EMAIL
# =============================================================================
echo "--- Demo Login Configuration ---"

LOGIN_FILE="petinsure360/frontend/src/pages/LoginPage.jsx"
if [ -f "$LOGIN_FILE" ]; then
    if grep -q "demo@demologin.com" "$LOGIN_FILE"; then
        log_pass "Default demo email configured in LoginPage"
    else
        log_warn "LoginPage.jsx missing default 'demo@demologin.com'"
    fi
else
    log_fail "LoginPage.jsx not found"
fi

echo ""

# =============================================================================
# 6. PIPELINE PAGE DATA SOURCE CHECK
# =============================================================================
echo "--- Pipeline Page Configuration ---"

PIPELINE_FILE="petinsure360/bi-dashboard/src/pages/PipelinePage.jsx"
if [ -f "$PIPELINE_FILE" ]; then
    if grep -q "azure" "$PIPELINE_FILE"; then
        log_pass "PipelinePage checks for 'azure' data source"
    else
        log_warn "PipelinePage may not detect Azure ADLS connection"
    fi
else
    log_fail "PipelinePage.jsx not found"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo "=============================================="
echo "Validation Summary"
echo "=============================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed! Safe to deploy.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}$WARNINGS warnings found. Review before deploying.${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS errors found. Fix before deploying!${NC}"
    echo ""
    echo "See DEPLOYMENT_CHECKLIST.md for fixes."
    exit 1
fi
