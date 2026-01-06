#!/bin/bash
# Azure Connection Test Script for PetInsure360
# Tests all Azure service connections

set -e

RESOURCE_GROUP="rg-petinsure360"
STORAGE_ACCOUNT="petinsud7i43"
FRONTEND_STORAGE="petinsure360frontend"
APP_SERVICE="petinsure360-backend"

echo "=============================================="
echo "  Azure Connection Test - PetInsure360"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✅ PASS${NC}: $1"; }
fail() { echo -e "${RED}❌ FAIL${NC}: $1"; }
warn() { echo -e "${YELLOW}⚠️  WARN${NC}: $1"; }

echo "1. Azure Account"
echo "   ─────────────"
if az account show &>/dev/null; then
    ACCOUNT=$(az account show --query name -o tsv)
    STATE=$(az account show --query state -o tsv)
    pass "Logged in to Azure"
    echo "      Subscription: $ACCOUNT"
    echo "      State: $STATE"
else
    fail "Not logged in to Azure"
    echo ""
    echo "   Fix: Run 'az login'"
    exit 1
fi

echo ""
echo "2. Resource Group"
echo "   ───────────────"
if az group show --name $RESOURCE_GROUP &>/dev/null; then
    LOCATION=$(az group show --name $RESOURCE_GROUP --query location -o tsv)
    pass "Resource group exists"
    echo "      Name: $RESOURCE_GROUP"
    echo "      Location: $LOCATION"
else
    fail "Resource group not found: $RESOURCE_GROUP"
fi

echo ""
echo "3. Storage Account (Data Lake)"
echo "   ────────────────────────────"
if az storage account show --name $STORAGE_ACCOUNT &>/dev/null; then
    KIND=$(az storage account show --name $STORAGE_ACCOUNT --query kind -o tsv)
    HNS=$(az storage account show --name $STORAGE_ACCOUNT --query isHnsEnabled -o tsv)
    pass "Storage account exists"
    echo "      Name: $STORAGE_ACCOUNT"
    echo "      Kind: $KIND"
    echo "      HNS (ADLS Gen2): $HNS"

    # List containers
    echo "      Containers:"
    az storage container list --account-name $STORAGE_ACCOUNT --query "[].name" -o tsv 2>/dev/null | while read c; do
        echo "        - $c"
    done
else
    fail "Storage account not found: $STORAGE_ACCOUNT"
fi

echo ""
echo "4. Storage Account (Frontend)"
echo "   ───────────────────────────"
if az storage account show --name $FRONTEND_STORAGE &>/dev/null; then
    WEB_URL=$(az storage account show --name $FRONTEND_STORAGE --query "primaryEndpoints.web" -o tsv)
    pass "Frontend storage exists"
    echo "      Name: $FRONTEND_STORAGE"
    echo "      URL: $WEB_URL"
else
    fail "Frontend storage not found: $FRONTEND_STORAGE"
fi

echo ""
echo "5. App Service (Backend)"
echo "   ──────────────────────"
if az webapp show --resource-group $RESOURCE_GROUP --name $APP_SERVICE &>/dev/null; then
    STATE=$(az webapp show --resource-group $RESOURCE_GROUP --name $APP_SERVICE --query state -o tsv)
    URL=$(az webapp show --resource-group $RESOURCE_GROUP --name $APP_SERVICE --query defaultHostName -o tsv)
    pass "App Service exists"
    echo "      Name: $APP_SERVICE"
    echo "      State: $STATE"
    echo "      URL: https://$URL"
else
    fail "App Service not found: $APP_SERVICE"
fi

echo ""
echo "6. Databricks Workspace"
echo "   ─────────────────────"
DATABRICKS=$(az databricks workspace list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$DATABRICKS" ]; then
    DBURL=$(az databricks workspace show --resource-group $RESOURCE_GROUP --name $DATABRICKS --query workspaceUrl -o tsv)
    pass "Databricks workspace exists"
    echo "      Name: $DATABRICKS"
    echo "      URL: https://$DBURL"
else
    warn "No Databricks workspace found"
fi

echo ""
echo "7. Key Vault"
echo "   ──────────"
KV=$(az keyvault list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")
if [ -n "$KV" ]; then
    pass "Key Vault exists"
    echo "      Name: $KV"

    # List secrets
    echo "      Secrets:"
    az keyvault secret list --vault-name $KV --query "[].name" -o tsv 2>/dev/null | while read s; do
        echo "        - $s"
    done
else
    warn "No Key Vault found"
fi

echo ""
echo "8. Live Service Health"
echo "   ────────────────────"
echo "   Backend API:"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://petinsure360-backend.azurewebsites.net/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    pass "Backend healthy (HTTP $BACKEND_STATUS)"
else
    warn "Backend returned HTTP $BACKEND_STATUS"
fi

echo "   Frontend:"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://petinsure360frontend.z5.web.core.windows.net/ 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    pass "Frontend healthy (HTTP $FRONTEND_STATUS)"
else
    warn "Frontend returned HTTP $FRONTEND_STATUS"
fi

echo ""
echo "=============================================="
echo "  Connection Test Complete"
echo "=============================================="
