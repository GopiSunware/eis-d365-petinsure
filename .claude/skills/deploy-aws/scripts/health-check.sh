#!/bin/bash
# AWS Health Check Script for EIS-Dynamics

echo "=== EIS-Dynamics AWS Health Check ==="
echo ""

echo "1. Unified Claims API:"
UNIFIED_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://p7qrmgi9sp.us-east-1.awsapprunner.com/)
if [ "$UNIFIED_STATUS" = "200" ]; then
    echo "   Status: ✅ Healthy ($UNIFIED_STATUS)"
else
    echo "   Status: ❌ Unhealthy ($UNIFIED_STATUS)"
fi

echo ""
echo "2. Agent Pipeline:"
PIPELINE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bn9ymuxtwp.us-east-1.awsapprunner.com/api/v1/scenarios/)
if [ "$PIPELINE_STATUS" = "200" ]; then
    echo "   Status: ✅ Healthy ($PIPELINE_STATUS)"
else
    echo "   Status: ❌ Unhealthy ($PIPELINE_STATUS)"
fi

echo ""
echo "3. AWS Identity:"
aws sts get-caller-identity --profile sunwaretech 2>/dev/null || echo "   ❌ AWS CLI not configured"

echo ""
echo "=== URLs ==="
echo "   Claims API: https://p7qrmgi9sp.us-east-1.awsapprunner.com"
echo "   Pipeline:   https://bn9ymuxtwp.us-east-1.awsapprunner.com"
echo "   API Docs:   https://p7qrmgi9sp.us-east-1.awsapprunner.com/docs"
