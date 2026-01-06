#!/bin/bash
# Start the Unified Claims Data API on port 8000

cd "$(dirname "$0")"

echo "=============================================="
echo "Starting Unified Claims Data API"
echo "Port: 8000"
echo "=============================================="

# Check if data exists
if [ ! -f "data/customers.json" ]; then
    echo "Data not found. Generating synthetic data..."
    python3 generators/generate_all.py
fi

# Start the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
