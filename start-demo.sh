#!/bin/bash
# PetInsure360 + EIS Dynamics Demo Startup Script
# This starts the minimum services needed for the demo

set -e

BASE_DIR="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics"
cd "$BASE_DIR"

echo "=========================================="
echo "  PetInsure360 + EIS Dynamics Demo"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Cloud Services Status:${NC}"
echo "  AWS Unified API:      https://p7qrmgi9sp.us-east-1.awsapprunner.com"
echo "  AWS Agent Pipeline:   https://bn9ymuxtwp.us-east-1.awsapprunner.com"
echo ""

echo -e "${YELLOW}Starting local services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start PetInsure360 Backend (port 3002)
echo "1. Starting PetInsure360 Backend (port 3002)..."
cd "$BASE_DIR/petinsure360/backend"
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env_backend" ]; then
    source env_backend/bin/activate
fi
python -m uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
sleep 3

# Start PetInsure360 Frontend (port 3000)
echo "2. Starting PetInsure360 Frontend (port 3000)..."
cd "$BASE_DIR/petinsure360/frontend"
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo -e "${GREEN}=========================================="
echo "  Demo is starting up!"
echo "==========================================${NC}"
echo ""
echo "  Local URLs:"
echo "    Customer Portal:  http://localhost:3000"
echo "    Backend API:      http://localhost:3002"
echo ""
echo "  Cloud URLs:"
echo "    Agent Pipeline:   https://bn9ymuxtwp.us-east-1.awsapprunner.com"
echo ""
echo "  Demo Users (from DEMO_WORKFLOW.md):"
echo "    DEMO-001: demo@demologin.com"
echo "    DEMO-002: demo1@demologin.com"
echo "    DEMO-003: demo2@demologin.com"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
