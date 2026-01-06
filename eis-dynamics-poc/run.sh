#!/bin/bash
# EIS-Dynamics POC Run Script
# Starts all services in the background

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Run ./setup.sh first or copy .env.example to .env"
    exit 1
fi

# Export environment variables
export $(grep -v '^#' .env | xargs)

echo "=========================================="
echo "Starting EIS-Dynamics POC Services"
echo "=========================================="

# Kill any existing services on these ports
echo "Stopping any existing services..."
pkill -f "uvicorn.*8001" 2>/dev/null || true
pkill -f "uvicorn.*8002" 2>/dev/null || true
pkill -f "uvicorn.*8003" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
sleep 2

# Activate virtual environment
source venv/bin/activate

# Start WS2 AI Claims (port 8001)
echo "Starting WS2 AI Claims Service on port 8001..."
cd "$PROJECT_ROOT/src/ws2_ai_claims"
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
WS2_PID=$!

# Start WS3 Integration (port 8002)
echo "Starting WS3 Integration Service on port 8002..."
cd "$PROJECT_ROOT/src/ws3_integration"
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
WS3_PID=$!

# Start WS5 Rating Engine (port 8003)
echo "Starting WS5 Rating Engine on port 8003..."
cd "$PROJECT_ROOT/src/ws5_rating_engine"
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload &
WS5_PID=$!

# Start WS4 Agent Portal (port 3000)
echo "Starting WS4 Agent Portal on port 3000..."
cd "$PROJECT_ROOT/src/ws4_agent_portal"
npm run dev &
WS4_PID=$!

echo ""
echo "=========================================="
echo "All services started!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - AI Claims API:    http://localhost:8001/docs"
echo "  - Integration API:  http://localhost:8002/docs"
echo "  - Rating API:       http://localhost:8003/docs"
echo "  - Agent Portal:     http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $WS2_PID $WS3_PID $WS5_PID $WS4_PID 2>/dev/null; exit" INT TERM

wait
