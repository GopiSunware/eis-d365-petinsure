#!/bin/bash
# =============================================================================
# Test AWS Deployment - Quick verification of all endpoints
# =============================================================================
# Usage:
#   ./test-aws.sh           # Run all tests
#   ./test-aws.sh pipeline  # Test only pipeline endpoints
#   ./test-aws.sh chat      # Test only chat endpoints
# =============================================================================

# Configuration
API_URL="https://9wvcjmrknc.us-east-1.awsapprunner.com"
CUSTOMER_PORTAL="http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com"
BI_DASHBOARD="http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
info() { echo -e "${YELLOW}[TEST]${NC} $1"; }

test_endpoint() {
  local name=$1
  local url=$2
  local expected=$3

  info "Testing $name..."
  response=$(curl -s -w "\n%{http_code}" "$url")
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" == "$expected" ]; then
    pass "$name - HTTP $http_code"
    return 0
  else
    fail "$name - Expected $expected, got $http_code"
    return 1
  fi
}

test_json_field() {
  local name=$1
  local url=$2
  local jq_query=$3
  local expected=$4

  info "Testing $name..."
  response=$(curl -s "$url")
  value=$(echo "$response" | jq -r "$jq_query" 2>/dev/null)

  if [ "$value" == "$expected" ]; then
    pass "$name - $jq_query = $value"
    return 0
  else
    fail "$name - Expected $expected, got $value"
    return 1
  fi
}

# =============================================================================
# TEST SUITES
# =============================================================================

test_health() {
  echo ""
  echo "=== Health Checks ==="
  test_endpoint "Backend Health" "$API_URL/health" "200"
  test_endpoint "Customer Portal" "$CUSTOMER_PORTAL/" "200"
  test_endpoint "BI Dashboard" "$BI_DASHBOARD/" "200"
}

test_chat() {
  echo ""
  echo "=== Chat API ==="
  test_endpoint "Chat Providers" "$API_URL/api/chat/providers" "200"

  # Check if providers are enabled
  info "Checking OpenAI enabled..."
  enabled=$(curl -s "$API_URL/api/chat/providers" | jq -r '.providers.openai.enabled')
  [ "$enabled" == "true" ] && pass "OpenAI enabled" || fail "OpenAI disabled"

  info "Checking Anthropic enabled..."
  enabled=$(curl -s "$API_URL/api/chat/providers" | jq -r '.providers.anthropic.enabled')
  [ "$enabled" == "true" ] && pass "Anthropic enabled" || fail "Anthropic disabled"
}

test_pipeline() {
  echo ""
  echo "=== Pipeline API ==="
  test_endpoint "Pipeline Status" "$API_URL/api/pipeline/status" "200"
  test_endpoint "Pipeline Pending" "$API_URL/api/pipeline/pending" "200"
  test_endpoint "Pipeline Metrics" "$API_URL/api/pipeline/metrics" "200"

  # Test mode
  info "Checking pipeline mode..."
  mode=$(curl -s "$API_URL/api/pipeline/status" | jq -r '.mode')
  [ "$mode" == "demo" ] || [ "$mode" == "cleared" ] && pass "Mode: $mode" || fail "Invalid mode: $mode"

  # Test refresh
  info "Testing pipeline refresh..."
  result=$(curl -s -X POST "$API_URL/api/pipeline/refresh" | jq -r '.status')
  [ "$result" == "success" ] && pass "Refresh: $result" || fail "Refresh failed: $result"
}

test_data() {
  echo ""
  echo "=== Insights API ==="
  test_endpoint "Claims Insights" "$API_URL/api/insights/claims" "200"
  test_endpoint "Customer 360" "$API_URL/api/insights/customers" "200"
  test_endpoint "KPIs" "$API_URL/api/insights/kpis" "200"
  test_endpoint "Summary" "$API_URL/api/insights/summary" "200"
}

# =============================================================================
# MAIN
# =============================================================================

echo "==========================================="
echo "  AWS Deployment Test Suite"
echo "==========================================="
echo "API: $API_URL"
echo ""

case "${1:-all}" in
  "health")
    test_health
    ;;
  "chat")
    test_chat
    ;;
  "pipeline")
    test_pipeline
    ;;
  "data")
    test_data
    ;;
  "all"|*)
    test_health
    test_chat
    test_pipeline
    test_data
    ;;
esac

echo ""
echo "==========================================="
echo "  Tests Complete"
echo "==========================================="
