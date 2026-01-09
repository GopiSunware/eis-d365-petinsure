#!/bin/bash
# Restart All Services - Clean slate with fresh data

set -e  # Exit on error

echo "=============================================="
echo "  Pet Insurance Platform - Clean Restart"
echo "=============================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kill all existing services
echo -e "${YELLOW}Step 1: Stopping existing services...${NC}"
lsof -ti:3000 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 3000" || echo "  - Port 3000 not running"
lsof -ti:3001 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 3001" || echo "  - Port 3001 not running"
lsof -ti:3002 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 3002" || echo "  - Port 3002 not running"
lsof -ti:8000 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 8000" || echo "  - Port 8000 not running"
lsof -ti:8007 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 8007" || echo "  - Port 8007 not running"
lsof -ti:8080 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 8080" || echo "  - Port 8080 not running"
lsof -ti:8081 2>/dev/null | xargs -r kill -9 && echo "  ✓ Killed port 8081" || echo "  - Port 8081 not running"

sleep 2
echo ""

# Clear old test data
echo -e "${YELLOW}Step 2: Clearing ALL old test data...${NC}"

# Clear DocGen batches
rm -f "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws7_docgen/data/batches/batches.json"
echo "  ✓ Cleared DocGen batches"

# Clear pipeline state
rm -f "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend/data/pipeline/pipeline_state.json"
echo "  ✓ Cleared pipeline state"

# Clear Bronze/Silver/Gold pipeline data (THIS WAS MISSING!)
rm -rf "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline/data/agent_pipeline/bronze/"*
rm -rf "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline/data/agent_pipeline/silver/"*
rm -rf "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline/data/agent_pipeline/gold/"*
echo "  ✓ Cleared Bronze/Silver/Gold pipeline data"

# Recreate directory structure
mkdir -p "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline/data/agent_pipeline/bronze"
mkdir -p "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline/data/agent_pipeline/silver"
mkdir -p "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws6_agent_pipeline/data/agent_pipeline/gold"
echo "  ✓ Recreated pipeline directory structure"

echo ""

# Start backend services
echo -e "${YELLOW}Step 3: Starting backend services...${NC}"

cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/shared/claims_data_api"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/claims-api.log 2>&1 &
echo "  ✓ Starting Claims Data API (port 8000)"

cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws7_docgen"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 > /tmp/docgen.log 2>&1 &
echo "  ✓ Starting DocGen Service (port 8007)"

cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/backend"
python -m uvicorn app.main:socket_app --host 0.0.0.0 --port 3002 > /tmp/backend.log 2>&1 &
echo "  ✓ Starting PetInsure360 Backend with Socket.IO (port 3002)"

echo "  Waiting for backend services to initialize..."
sleep 8

# Start UI services
echo ""
echo -e "${YELLOW}Step 4: Starting UI services...${NC}"

cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/frontend"
npm run dev > /tmp/ui-3000.log 2>&1 &
echo "  ✓ Starting Customer Portal (port 3000)"

cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360/bi-dashboard"
npm run dev > /tmp/ui-3001.log 2>&1 &
echo "  ✓ Starting BI Dashboard (port 3001)"

cd "/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc/src/ws8_admin_portal/frontend"
PORT=8081 npm run dev > /tmp/ui-8081.log 2>&1 &
echo "  ✓ Starting EIS Admin Portal (port 8081)"

echo "  Waiting for UI services to build..."
sleep 12

# Verify all services
echo ""
echo -e "${YELLOW}Step 5: Verifying services...${NC}"

check_service() {
    local port=$1
    local name=$2
    local url=$3

    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$http_code" = "200" ]; then
        echo -e "  ${GREEN}✓${NC} Port $port ($name): Running"
        return 0
    else
        echo -e "  ${RED}✗${NC} Port $port ($name): Not responding (HTTP $http_code)"
        return 1
    fi
}

all_ok=true

check_service 8000 "Claims API" "http://localhost:8000/health" || all_ok=false
check_service 8007 "DocGen" "http://localhost:8007/health" || all_ok=false
check_service 3002 "Backend" "http://localhost:3002/health" || all_ok=false
check_service 3000 "Customer Portal" "http://localhost:3000" || all_ok=false
check_service 3001 "BI Dashboard" "http://localhost:3001" || all_ok=false
check_service 8081 "EIS Admin" "http://localhost:8081" || all_ok=false

echo ""
echo "=============================================="

if [ "$all_ok" = true ]; then
    echo -e "${GREEN}✓ All services started successfully!${NC}"
    echo ""
    echo "Access the applications:"
    echo "  • Customer Portal:  http://localhost:3000"
    echo "  • BI Dashboard:     http://localhost:3001"
    echo "  • EIS Admin Portal: http://localhost:8081"
    echo ""
    echo "API Documentation:"
    echo "  • Claims API:       http://localhost:8000/docs"
    echo "  • DocGen API:       http://localhost:8007/docs"
    echo "  • Backend API:      http://localhost:3002/docs"
else
    echo -e "${RED}⚠ Some services failed to start${NC}"
    echo ""
    echo "Check logs:"
    echo "  tail -f /tmp/claims-api.log"
    echo "  tail -f /tmp/docgen.log"
    echo "  tail -f /tmp/backend.log"
    echo "  tail -f /tmp/ui-3000.log"
    echo "  tail -f /tmp/ui-3001.log"
    echo "  tail -f /tmp/ui-8081.log"
fi

echo "=============================================="
echo ""
echo "To stop all services: ./stop-all.sh"
echo ""
