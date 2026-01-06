#!/bin/bash
# Quick Deploy Script for PetInsure360 to Azure
# Usage: ./quick-deploy.sh [backend|frontend|bi|all]

set -e

PROJECT_DIR="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics/petinsure360"
RESOURCE_GROUP="rg-petinsure360"
BACKEND_NAME="petinsure360-backend"
FRONTEND_STORAGE="petinsure360frontend"

echo "=== PetInsure360 Quick Deploy ==="

deploy_backend() {
    echo ""
    echo ">>> Deploying Backend..."
    cd "$PROJECT_DIR/backend"

    # Create deployment package
    rm -f deploy.zip
    zip -r deploy.zip app data requirements.txt .env .funcignore host.json -x "*.pyc" -x "*__pycache__*" -x "env_backend/*" -x "node_modules/*"

    # Deploy
    az webapp deploy --resource-group $RESOURCE_GROUP --name $BACKEND_NAME --src-path deploy.zip --type zip

    # Cleanup
    rm -f deploy.zip

    echo "✅ Backend deployed!"
}

deploy_frontend() {
    echo ""
    echo ">>> Deploying Frontend..."
    cd "$PROJECT_DIR/frontend"

    # Build
    npm run build

    # Deploy to Azure Storage
    az storage blob upload-batch --account-name $FRONTEND_STORAGE --destination '$web' --source dist --overwrite

    echo "✅ Frontend deployed!"
}

deploy_bi() {
    echo ""
    echo ">>> Deploying BI Dashboard..."
    cd "$PROJECT_DIR/bi-dashboard"

    # Build
    npm run build

    echo "✅ BI Dashboard built! (Manual upload needed if separate hosting)"
}

case "${1:-all}" in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    bi)
        deploy_bi
        ;;
    all)
        deploy_backend
        deploy_frontend
        deploy_bi
        ;;
    *)
        echo "Usage: $0 [backend|frontend|bi|all]"
        exit 1
        ;;
esac

echo ""
echo "=== Deployment Complete ==="
echo "URLs:"
echo "  Frontend: https://petinsure360frontend.z5.web.core.windows.net"
echo "  Backend:  https://petinsure360-backend.azurewebsites.net"
echo "  API Docs: https://petinsure360-backend.azurewebsites.net/docs"
