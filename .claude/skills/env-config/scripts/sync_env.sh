#!/bin/bash
# Sync Environment Files
# Compares .env files and shows differences

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=============================================="
echo "  Environment File Sync Tool"
echo "=============================================="
echo ""

# Find project root (look for .env.example)
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.env.example" ]]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo "$PWD"
}

PROJECT_ROOT=$(find_project_root)
cd "$PROJECT_ROOT"

echo -e "${BLUE}Project Root:${NC} $PROJECT_ROOT"
echo ""

# List all .env files
echo "=== Environment Files Found ==="
find . -maxdepth 3 -name ".env*" -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/.git/*" | sort

echo ""
echo "=== Variable Comparison ==="

# Extract variables from a file
get_vars() {
    grep "^[A-Z]" "$1" 2>/dev/null | cut -d= -f1 | sort | uniq
}

# Compare .env.example with .env
if [[ -f ".env.example" ]]; then
    echo ""
    echo -e "${YELLOW}.env.example vs .env${NC}"

    if [[ -f ".env" ]]; then
        EXAMPLE_VARS=$(get_vars .env.example)
        ENV_VARS=$(get_vars .env)

        # Missing in .env
        MISSING=$(comm -23 <(echo "$EXAMPLE_VARS") <(echo "$ENV_VARS"))
        if [[ -n "$MISSING" ]]; then
            echo -e "${RED}Missing in .env:${NC}"
            echo "$MISSING" | while read var; do
                echo "  - $var"
            done
        else
            echo -e "${GREEN}✅ All variables from .env.example are in .env${NC}"
        fi

        # Extra in .env
        EXTRA=$(comm -13 <(echo "$EXAMPLE_VARS") <(echo "$ENV_VARS"))
        if [[ -n "$EXTRA" ]]; then
            echo -e "${BLUE}Extra in .env (not in .env.example):${NC}"
            echo "$EXTRA" | while read var; do
                echo "  + $var"
            done
        fi
    else
        echo -e "${RED}.env file not found${NC}"
        echo "Create from template: cp .env.example .env"
    fi
fi

# Compare .env.local with .env.production
if [[ -f ".env.local" ]] && [[ -f ".env.production" ]]; then
    echo ""
    echo -e "${YELLOW}.env.local vs .env.production${NC}"

    LOCAL_VARS=$(get_vars .env.local)
    PROD_VARS=$(get_vars .env.production)

    # Show differences
    echo "Variables only in .env.local:"
    comm -23 <(echo "$LOCAL_VARS") <(echo "$PROD_VARS") | while read var; do
        echo "  - $var"
    done

    echo "Variables only in .env.production:"
    comm -13 <(echo "$LOCAL_VARS") <(echo "$PROD_VARS") | while read var; do
        echo "  + $var"
    done
fi

# Check for sensitive values that might be committed
echo ""
echo "=== Security Check ==="

check_sensitive() {
    local file=$1
    if grep -q "sk-ant-\|sk-proj-\|password=.*[a-zA-Z0-9]" "$file" 2>/dev/null; then
        echo -e "${RED}⚠️  WARNING: $file may contain sensitive values!${NC}"
        return 1
    fi
    return 0
}

for envfile in .env .env.local .env.production; do
    if [[ -f "$envfile" ]]; then
        check_sensitive "$envfile" || true
    fi
done

echo ""
echo "=== Quick Commands ==="
echo "  Switch to local:      cp .env.local .env"
echo "  Switch to production: cp .env.production .env"
echo "  Validate config:      python scripts/validate_env.py"
echo ""
