#!/bin/bash
# Comprehensive Diagnostic Script
# Checks local services, cloud connectivity, and configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok() { echo -e "${GREEN}✅ OK${NC}: $1"; }
fail() { echo -e "${RED}❌ FAIL${NC}: $1"; }
warn() { echo -e "${YELLOW}⚠️  WARN${NC}: $1"; }
info() { echo -e "${BLUE}ℹ️  INFO${NC}: $1"; }

echo "=============================================="
echo "  System Diagnostics"
echo "=============================================="
echo ""

# Find project root
PROJECT_ROOT="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics"
cd "$PROJECT_ROOT" 2>/dev/null || { fail "Cannot find project root"; exit 1; }

echo "=== 1. Environment Files ==="
for env_file in .env eis-dynamics-poc/.env petinsure360/backend/.env; do
    if [[ -f "$env_file" ]]; then
        ok "$env_file exists"
    else
        warn "$env_file not found"
    fi
done

echo ""
echo "=== 2. Local Services ==="

check_port() {
    local port=$1
    local name=$2
    if lsof -i :$port &>/dev/null || netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        ok "$name (port $port) is running"
        return 0
    else
        info "$name (port $port) is not running"
        return 1
    fi
}

check_port 8000 "Claims API"
check_port 8006 "Agent Pipeline"
check_port 3000 "Frontend"

echo ""
echo "=== 3. Local API Health ==="

check_local_api() {
    local url=$1
    local name=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [[ "$status" == "200" ]]; then
        ok "$name returns HTTP 200"
    elif [[ "$status" == "000" ]]; then
        info "$name not reachable (service not running)"
    else
        warn "$name returns HTTP $status"
    fi
}

check_local_api "http://localhost:8000/" "Claims API"
check_local_api "http://localhost:8006/api/v1/scenarios/" "Agent Pipeline"
check_local_api "http://localhost:3000/" "Frontend"

echo ""
echo "=== 4. Cloud Services (AWS) ==="

check_cloud_api() {
    local url=$1
    local name=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
    if [[ "$status" == "200" ]]; then
        ok "$name returns HTTP 200"
    elif [[ "$status" == "000" ]]; then
        warn "$name not reachable (network issue or service down)"
    else
        warn "$name returns HTTP $status"
    fi
}

check_cloud_api "https://p7qrmgi9sp.us-east-1.awsapprunner.com/" "AWS Claims API"
check_cloud_api "https://bn9ymuxtwp.us-east-1.awsapprunner.com/api/v1/scenarios/" "AWS Agent Pipeline"

echo ""
echo "=== 5. Cloud Services (Azure) ==="

check_cloud_api "https://petinsure360-backend.azurewebsites.net/health" "Azure Backend"
check_cloud_api "https://petinsure360frontend.z5.web.core.windows.net/" "Azure Frontend"

echo ""
echo "=== 6. Configuration Check ==="

# Check EIS config
if [[ -f "eis-dynamics-poc/.env" ]]; then
    if grep -q "ANTHROPIC_API_KEY=sk-" eis-dynamics-poc/.env 2>/dev/null; then
        ok "EIS: ANTHROPIC_API_KEY is set"
    else
        warn "EIS: ANTHROPIC_API_KEY may not be set"
    fi
fi

# Check PetInsure360 config
if [[ -f "petinsure360/backend/.env" ]]; then
    if grep -q "AZURE_STORAGE_ACCOUNT=" petinsure360/backend/.env 2>/dev/null; then
        ok "PetInsure360: Azure storage configured"
    else
        warn "PetInsure360: Azure storage may not be configured"
    fi
fi

echo ""
echo "=== 7. Python Environment ==="

if command -v python &>/dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    ok "Python installed: $PYTHON_VERSION"
else
    fail "Python not found"
fi

echo ""
echo "=== 8. Node.js Environment ==="

if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    ok "Node.js installed: $NODE_VERSION"
else
    warn "Node.js not found"
fi

echo ""
echo "=== 9. Docker ==="

if docker info &>/dev/null; then
    ok "Docker is running"
else
    warn "Docker is not running"
fi

echo ""
echo "=== 10. Git Status ==="

if [[ -d ".git" ]]; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    ok "Git repo found, branch: $BRANCH"

    CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
    if [[ $CHANGES -gt 0 ]]; then
        info "$CHANGES uncommitted changes"
    fi
else
    info "Not a git repository"
fi

echo ""
echo "=============================================="
echo "  Diagnostic Complete"
echo "=============================================="
