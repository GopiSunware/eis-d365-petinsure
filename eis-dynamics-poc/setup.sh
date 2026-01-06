#!/bin/bash
# EIS-Dynamics POC Setup Script

set -e

echo "=========================================="
echo "EIS-Dynamics POC Setup"
echo "=========================================="

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install shared module first
echo "Installing shared module..."
cd "$PROJECT_ROOT/src/shared"
pip install -e .

# Install WS2 AI Claims dependencies
echo "Installing WS2 AI Claims dependencies..."
cd "$PROJECT_ROOT/src/ws2_ai_claims"
pip install -r requirements.txt

# Install WS3 Integration dependencies
echo "Installing WS3 Integration dependencies..."
cd "$PROJECT_ROOT/src/ws3_integration"
pip install -r requirements.txt

# Install WS5 Rating Engine dependencies
echo "Installing WS5 Rating Engine dependencies..."
cd "$PROJECT_ROOT/src/ws5_rating_engine"
pip install -r requirements.txt

# Setup .env if not exists
cd "$PROJECT_ROOT"
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "IMPORTANT: Edit .env file with your API keys!"
fi

# Install Agent Portal dependencies
echo ""
echo "Installing Agent Portal (Next.js) dependencies..."
cd "$PROJECT_ROOT/src/ws4_agent_portal"
if command -v npm &> /dev/null; then
    npm install
else
    echo "WARNING: npm not found. Install Node.js to run the Agent Portal."
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   - ANTHROPIC_API_KEY (for Claude)"
echo "   - AZURE_OPENAI_* (for OpenAI)"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the services (in separate terminals):"
echo "   ./run.sh"
echo ""
