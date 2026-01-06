#!/bin/bash
# Azure Health Check Script for PetInsure360

echo "=== PetInsure360 Azure Health Check ==="
echo ""

echo "1. Backend API:"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://petinsure360-backend.azurewebsites.net/health)
if [ "$BACKEND_STATUS" = "200" ]; then
    echo "   Status: ✅ Healthy ($BACKEND_STATUS)"
else
    echo "   Status: ❌ Unhealthy ($BACKEND_STATUS)"
fi

echo ""
echo "2. Frontend Portal:"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://petinsure360frontend.z5.web.core.windows.net/)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "   Status: ✅ Healthy ($FRONTEND_STATUS)"
else
    echo "   Status: ❌ Unhealthy ($FRONTEND_STATUS)"
fi

echo ""
echo "3. Azure Account:"
az account show --query "{Name:name, State:state}" -o table 2>/dev/null || echo "   ❌ Azure CLI not logged in (run: az login)"

echo ""
echo "=== URLs ==="
echo "   Frontend:   https://petinsure360frontend.z5.web.core.windows.net"
echo "   Backend:    https://petinsure360-backend.azurewebsites.net"
echo "   API Docs:   https://petinsure360-backend.azurewebsites.net/docs"
echo "   Databricks: https://adb-7405619408519767.7.azuredatabricks.net"
