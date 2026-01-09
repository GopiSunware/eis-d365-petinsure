#!/bin/bash
# Stop All Services

echo "=============================================="
echo "  Stopping All Services"
echo "=============================================="
echo ""

lsof -ti:3000 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 3000 (Customer Portal)" || echo "- Port 3000 not running"
lsof -ti:3001 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 3001 (BI Dashboard)" || echo "- Port 3001 not running"
lsof -ti:3002 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 3002 (Backend)" || echo "- Port 3002 not running"
lsof -ti:8000 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 8000 (Claims API)" || echo "- Port 8000 not running"
lsof -ti:8007 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 8007 (DocGen)" || echo "- Port 8007 not running"
lsof -ti:8080 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 8080 (Agent Portal)" || echo "- Port 8080 not running"
lsof -ti:8081 2>/dev/null | xargs -r kill -9 && echo "✓ Stopped port 8081 (EIS Admin)" || echo "- Port 8081 not running"

echo ""
echo "✓ All services stopped"
echo ""
