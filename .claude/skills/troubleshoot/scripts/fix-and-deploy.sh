#!/bin/bash
# Fix and Deploy Workflow Script
# Guides through: Test Local → Confirm → Deploy

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=============================================="
echo "  Fix & Deploy Workflow"
echo "=============================================="
echo ""

# Determine project
echo "Which project?"
echo "  1) EIS-Dynamics (AWS)"
echo "  2) PetInsure360 (Azure)"
read -p "Select [1/2]: " PROJECT_CHOICE

case $PROJECT_CHOICE in
    1)
        PROJECT="eis-dynamics"
        PROJECT_DIR="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/eis-dynamics-poc"
        CLOUD="AWS"
        ;;
    2)
        PROJECT="petinsure360"
        PROJECT_DIR="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360"
        CLOUD="Azure"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Project:${NC} $PROJECT"
echo -e "${BLUE}Cloud:${NC} $CLOUD"
echo ""

# Step 1: Test Local
echo "=== Step 1: Test Local ==="
echo ""
read -p "Have you tested the fix locally? [y/N]: " LOCAL_TEST

if [[ "$LOCAL_TEST" != "y" && "$LOCAL_TEST" != "Y" ]]; then
    echo ""
    echo -e "${YELLOW}Please test locally first:${NC}"
    echo ""
    if [[ "$PROJECT" == "eis-dynamics" ]]; then
        echo "  cd $PROJECT_DIR"
        echo "  # Start services"
        echo "  uvicorn app.main:app --reload --port 8000"
        echo "  # Test"
        echo "  curl http://localhost:8000/health"
    else
        echo "  cd $PROJECT_DIR/backend"
        echo "  # Start backend"
        echo "  uvicorn app.main:socket_app --reload --port 8000"
        echo "  # Test"
        echo "  curl http://localhost:8000/health"
    fi
    echo ""
    exit 0
fi

# Step 2: Confirm deployment
echo ""
echo "=== Step 2: Confirm Deployment ==="
echo ""
echo -e "${YELLOW}You are about to deploy to $CLOUD production.${NC}"
echo ""
read -p "Deploy to $CLOUD? [y/N]: " DEPLOY_CONFIRM

if [[ "$DEPLOY_CONFIRM" != "y" && "$DEPLOY_CONFIRM" != "Y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 3: Deploy
echo ""
echo "=== Step 3: Deploying to $CLOUD ==="
echo ""

if [[ "$PROJECT" == "eis-dynamics" ]]; then
    # AWS Deployment
    cd "$PROJECT_DIR"

    echo "Building Docker images..."
    ./deploy-aws.sh build

    echo ""
    echo "Pushing to ECR..."
    ./deploy-aws.sh push

    echo ""
    echo -e "${GREEN}Deployment complete!${NC}"
    echo ""
    echo "Verify at:"
    echo "  https://p7qrmgi9sp.us-east-1.awsapprunner.com/"
    echo "  https://bn9ymuxtwp.us-east-1.awsapprunner.com/"

else
    # Azure Deployment
    cd "$PROJECT_DIR/backend"

    echo "Creating deployment package..."
    rm -f deploy.zip
    zip -r deploy.zip app data requirements.txt .env .funcignore host.json -x "*.pyc" -x "*__pycache__*" -x "env_backend/*"

    echo ""
    echo "Deploying to Azure..."
    az webapp deploy --resource-group rg-petinsure360 --name petinsure360-backend --src-path deploy.zip --type zip

    rm -f deploy.zip

    echo ""
    echo -e "${GREEN}Deployment complete!${NC}"
    echo ""
    echo "Verify at:"
    echo "  https://petinsure360-backend.azurewebsites.net/health"
fi

# Step 4: Verify
echo ""
echo "=== Step 4: Verify Deployment ==="
echo ""
read -p "Run health check? [Y/n]: " VERIFY

if [[ "$VERIFY" != "n" && "$VERIFY" != "N" ]]; then
    sleep 5  # Wait for deployment to stabilize

    if [[ "$PROJECT" == "eis-dynamics" ]]; then
        echo "Checking AWS services..."
        curl -s https://p7qrmgi9sp.us-east-1.awsapprunner.com/ | head -3
    else
        echo "Checking Azure services..."
        curl -s https://petinsure360-backend.azurewebsites.net/health
    fi
fi

echo ""
echo -e "${GREEN}✅ Fix & Deploy workflow complete!${NC}"
