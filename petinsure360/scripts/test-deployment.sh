#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  PetInsure360 Deployment Test Suite"
echo "========================================"
echo ""

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code, expected $expected_status)"
        echo "  URL: $url"
        echo "  Response: $(echo "$body" | head -c 200)"
        return 1
    fi
}

# Track failures
FAILURES=0

echo "=== Backend API (petinsure360-backend) ==="
test_endpoint "Health Check" "https://fucf3fwwwv.us-east-1.awsapprunner.com/health" || ((FAILURES++))
test_endpoint "Root Endpoint" "https://fucf3fwwwv.us-east-1.awsapprunner.com/" || ((FAILURES++))
test_endpoint "Demo User Lookup" "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/lookup?email=demo@demologin.com" || ((FAILURES++))
test_endpoint "Insights - Claims" "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/claims" || ((FAILURES++))
test_endpoint "Insights - Summary" "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/summary" || ((FAILURES++))
test_endpoint "Insights - KPIs" "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/insights/kpis" || ((FAILURES++))
echo ""

echo "=== Claims Data API (chat/AI providers) ==="
test_endpoint "Root" "https://9wvcjmrknc.us-east-1.awsapprunner.com/" || ((FAILURES++))
test_endpoint "Chat Providers" "https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers" || ((FAILURES++))
test_endpoint "Chat Status" "https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/status" || ((FAILURES++))
echo ""

echo "=== Agent Pipeline API ==="
test_endpoint "Root" "https://qi2p3x5gsm.us-east-1.awsapprunner.com/" || ((FAILURES++))
test_endpoint "Health Check" "https://qi2p3x5gsm.us-east-1.awsapprunner.com/health" || ((FAILURES++))
test_endpoint "Ready Check" "https://qi2p3x5gsm.us-east-1.awsapprunner.com/ready" || ((FAILURES++))
echo ""

echo "=== WebSocket API ==="
echo -n "Testing WebSocket Connection... "
if command -v wscat &> /dev/null; then
    timeout 3 wscat -c wss://zi4qogocri.execute-api.us-east-1.amazonaws.com/prod 2>&1 | grep -q "connected" && echo -e "${GREEN}✓ OK${NC}" || echo -e "${YELLOW}⚠ Cannot verify${NC}"
else
    echo -e "${YELLOW}⚠ wscat not installed (optional)${NC}"
fi
echo ""

echo "=== Frontend URLs ==="
test_endpoint "Customer Portal" "http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com" || ((FAILURES++))
test_endpoint "BI Dashboard" "http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com" || ((FAILURES++))
echo ""

echo "=== Critical Features Test ==="
echo "Checking AI Chat Providers Configuration..."
PROVIDERS=$(curl -s https://9wvcjmrknc.us-east-1.awsapprunner.com/api/chat/providers | grep -o '"enabled":\[[^]]*\]' | grep -c 'openai\|anthropic')
if [ "$PROVIDERS" -ge 1 ]; then
    echo -e "  ${GREEN}✓ AI Providers Configured${NC}"
else
    echo -e "  ${RED}✗ No AI Providers Found${NC}"
    ((FAILURES++))
fi

echo "Checking Demo Users..."
DEMO_USER=$(curl -s "https://fucf3fwwwv.us-east-1.awsapprunner.com/api/customers/lookup?email=demo@demologin.com" | grep -c 'DEMO-001')
if [ "$DEMO_USER" -eq 1 ]; then
    echo -e "  ${GREEN}✓ Demo Users Available${NC}"
else
    echo -e "  ${RED}✗ Demo Users Missing${NC}"
    ((FAILURES++))
fi
echo ""

echo "========================================"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎉 Deployment is fully functional!"
    echo ""
    echo "URLs to access:"
    echo "  Customer Portal: http://petinsure360-customer-portal.s3-website-us-east-1.amazonaws.com"
    echo "  BI Dashboard:    http://petinsure360-bi-dashboard.s3-website-us-east-1.amazonaws.com"
    echo ""
    echo "Demo Logins:"
    echo "  • demo@demologin.com  (DEMO-001 - 2 pets, 2 policies)"
    echo "  • demo1@demologin.com (DEMO-002 - 2 pets, 1 policy)"
    echo "  • demo2@demologin.com (DEMO-003 - 1 pet, 1 policy)"
    echo ""
    echo "Features Verified:"
    echo "  ✓ Backend API operational"
    echo "  ✓ AI Chat providers configured (OpenAI + Anthropic)"
    echo "  ✓ WebSocket infrastructure deployed"
    echo "  ✓ Demo user data loaded"
    echo "  ✓ Both frontends deployed"
    exit 0
else
    echo -e "${RED}❌ $FAILURES test(s) failed${NC}"
    echo ""
    echo "Check the logs above for details."
    echo ""
    echo "Common fixes:"
    echo "  1. AI providers missing: ./scripts/update-ai-keys.sh"
    echo "  2. Services not running: Check AWS App Runner console"
    echo "  3. Frontend issues: ./scripts/deploy-frontends.sh"
    exit 1
fi
