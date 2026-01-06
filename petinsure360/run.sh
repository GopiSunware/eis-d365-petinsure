#!/bin/bash

# PetInsure360 - Run All Services
# This script starts the backend API, frontend portal, and BI dashboard

echo "=================================================="
echo "PetInsure360 - Pet Insurance Data Platform"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    lsof -i:$1 > /dev/null 2>&1
    return $?
}

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed."
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed."
    exit 1
fi

echo -e "${BLUE}[1/4] Installing Backend Dependencies...${NC}"
cd backend
pip install -r requirements.txt -q
cd ..

echo -e "${BLUE}[2/4] Installing Frontend Dependencies...${NC}"
cd frontend
npm install --silent
cd ..

echo -e "${BLUE}[3/4] Installing BI Dashboard Dependencies...${NC}"
cd bi-dashboard
npm install --silent
cd ..

echo ""
echo -e "${GREEN}Starting Services...${NC}"
echo ""

# Start Backend API
echo -e "${BLUE}Starting Backend API on port 8000...${NC}"
cd backend
python3 -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
sleep 3

# Start Frontend
echo -e "${BLUE}Starting Frontend Portal on port 3000...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3

# Start BI Dashboard
echo -e "${BLUE}Starting BI Dashboard on port 3001...${NC}"
cd bi-dashboard
npm run dev &
BI_PID=$!
cd ..

echo ""
echo "=================================================="
echo -e "${GREEN}All services started!${NC}"
echo "=================================================="
echo ""
echo "  Backend API:      http://localhost:8000"
echo "  API Docs:         http://localhost:8000/docs"
echo "  Customer Portal:  http://localhost:3000"
echo "  BI Dashboard:     http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for any key to stop
trap "kill $BACKEND_PID $FRONTEND_PID $BI_PID 2>/dev/null; exit" INT TERM
wait
