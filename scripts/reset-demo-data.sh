#!/bin/bash
# Reset Demo Data Script
# Clears all user-submitted data while keeping synthetic demo data

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default to local, can override with environment variable
PETINSURE_BACKEND="${PETINSURE_BACKEND:-http://localhost:3002}"
AGENT_PIPELINE="${AGENT_PIPELINE:-http://localhost:8006}"
DOCGEN_SERVICE="${DOCGEN_SERVICE:-http://localhost:8007}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         PetInsure360 Demo Data Reset                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Endpoints:${NC}"
echo "  • PetInsure Backend: $PETINSURE_BACKEND"
echo "  • Agent Pipeline:    $AGENT_PIPELINE"
echo "  • DocGen Service:    $DOCGEN_SERVICE"
echo ""

# Track results
PIPELINE_RESULT=""
AGENT_RESULT=""
DOCGEN_RESULT=""

# 1. Clear PetInsure360 Pipeline (includes uploads, claims)
echo -e "${BLUE}[1/4]${NC} Clearing PetInsure360 Pipeline..."
RESPONSE=$(curl -s -X DELETE "$PETINSURE_BACKEND/api/pipeline/clear?include_demo_data=true" 2>/dev/null)
if echo "$RESPONSE" | grep -q '"success":true' 2>/dev/null; then
    CLAIMS=$(echo "$RESPONSE" | grep -o '"claims_cleared":[0-9]*' | cut -d: -f2)
    UPLOADS=$(echo "$RESPONSE" | grep -o '"uploads_cleared":[0-9]*' | cut -d: -f2)
    echo -e "  ${GREEN}✓${NC} Pipeline cleared: ${CLAIMS:-0} claims, ${UPLOADS:-0} uploads"
    PIPELINE_RESULT="success"
else
    echo -e "  ${RED}✗${NC} Failed or service unavailable"
    PIPELINE_RESULT="failed"
fi

# 2. Clear EIS Agent Pipeline runs
echo -e "${BLUE}[2/4]${NC} Clearing Agent Pipeline runs..."
RESPONSE=$(curl -s -X DELETE "$AGENT_PIPELINE/clear" 2>/dev/null)
if echo "$RESPONSE" | grep -q '"success":true' 2>/dev/null; then
    RUNS=$(echo "$RESPONSE" | grep -o '"runs_cleared":[0-9]*' | cut -d: -f2)
    echo -e "  ${GREEN}✓${NC} Agent runs cleared: ${RUNS:-0} runs"
    AGENT_RESULT="success"
else
    echo -e "  ${RED}✗${NC} Failed or service unavailable"
    AGENT_RESULT="failed"
fi

# 3. Clear DocGen batches (EIS side)
echo -e "${BLUE}[3/4]${NC} Clearing DocGen batches..."
# DocGen service clears its own state on restart, but let's check the count
RESPONSE=$(curl -s "$DOCGEN_SERVICE/api/v1/docgen/batches?limit=1000" 2>/dev/null)
if echo "$RESPONSE" | grep -q '"total":' 2>/dev/null; then
    COUNT=$(echo "$RESPONSE" | grep -o '"total":[0-9]*' | cut -d: -f2)
    echo -e "  ${YELLOW}ℹ${NC} DocGen service has ${COUNT:-0} batches (in-memory, clears on restart)"
    DOCGEN_RESULT="info"
else
    echo -e "  ${RED}✗${NC} DocGen service unavailable"
    DOCGEN_RESULT="unavailable"
fi

# 4. Re-seed demo data (users, pets, policies)
echo -e "${BLUE}[4/5]${NC} Re-seeding demo data..."
SEED_RESPONSE=$(curl -s -X POST "$PETINSURE_BACKEND/api/customers/seed-demo" 2>/dev/null)
if echo "$SEED_RESPONSE" | grep -q '"success":true' 2>/dev/null; then
    CUSTOMERS=$(echo "$SEED_RESPONSE" | grep -o '"customers":[0-9]*' | cut -d: -f2)
    PETS=$(echo "$SEED_RESPONSE" | grep -o '"pets":[0-9]*' | cut -d: -f2)
    POLICIES=$(echo "$SEED_RESPONSE" | grep -o '"policies":[0-9]*' | cut -d: -f2)
    echo -e "  ${GREEN}✓${NC} Demo data seeded: ${CUSTOMERS:-0} customers, ${PETS:-0} pets, ${POLICIES:-0} policies"
    SEED_RESULT="success"
else
    echo -e "  ${RED}✗${NC} Failed to seed demo data"
    SEED_RESULT="failed"
fi

# 5. Verify clean state
echo -e "${BLUE}[5/5]${NC} Verifying clean state..."
echo ""

# Check PetInsure pipeline status
echo -e "  ${YELLOW}PetInsure360:${NC}"
STATUS=$(curl -s "$PETINSURE_BACKEND/api/pipeline/status" 2>/dev/null)
if [ -n "$STATUS" ]; then
    BRONZE=$(echo "$STATUS" | grep -o '"bronze":[0-9]*' | head -1 | cut -d: -f2)
    SILVER=$(echo "$STATUS" | grep -o '"silver":[0-9]*' | head -1 | cut -d: -f2)
    GOLD=$(echo "$STATUS" | grep -o '"gold":[0-9]*' | head -1 | cut -d: -f2)
    echo "    • Pending: Bronze=${BRONZE:-0}, Silver=${SILVER:-0}, Gold=${GOLD:-0}"
fi

# Check batch count
BATCHES=$(curl -s "$PETINSURE_BACKEND/api/docgen/batches" 2>/dev/null)
if [ -n "$BATCHES" ]; then
    TOTAL=$(echo "$BATCHES" | grep -o '"total":[0-9]*' | cut -d: -f2)
    echo "    • Upload batches: ${TOTAL:-0}"
fi

# Check demo pets
echo -e "  ${YELLOW}Demo Users:${NC}"
DEMO_PETS=$(curl -s "$PETINSURE_BACKEND/api/pets?customer_id=DEMO-001" 2>/dev/null)
DEMO_PET_COUNT=$(echo "$DEMO_PETS" | grep -o '"count":[0-9]*' | cut -d: -f2)
echo "    • demo@demologin.com pets: ${DEMO_PET_COUNT:-0}"

DEMO1_PETS=$(curl -s "$PETINSURE_BACKEND/api/pets?customer_id=DEMO-002" 2>/dev/null)
DEMO1_PET_COUNT=$(echo "$DEMO1_PETS" | grep -o '"count":[0-9]*' | cut -d: -f2)
echo "    • demo1@demologin.com pets: ${DEMO1_PET_COUNT:-0}"

# Check agent pipeline
echo -e "  ${YELLOW}Agent Pipeline:${NC}"
METRICS=$(curl -s "$AGENT_PIPELINE/metrics" 2>/dev/null)
if [ -n "$METRICS" ]; then
    TOTAL_RUNS=$(echo "$METRICS" | grep -o '"total_runs":[0-9]*' | cut -d: -f2)
    echo "    • Total runs: ${TOTAL_RUNS:-0}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      Reset Complete                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓${NC} Demo data reset complete."
echo ""
echo -e "${YELLOW}Demo Login Credentials:${NC}"
echo "  Primary:   demo@demologin.com   (2 pets: Buddy, Whiskers)"
echo "  Secondary: demo1@demologin.com  (2 pets: Max, Luna)"
echo "  Tertiary:  demo2@demologin.com  (1 pet: Charlie)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Refresh browser pages to see clean state"
echo "  2. Submit new claims to test the pipeline"
echo ""
