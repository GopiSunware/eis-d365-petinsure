#!/bin/bash
# Initialize Git Repository and Push to GitHub
# For EIS-D365 PetInsure project

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/mnt/c/Shri Hari Hari/Ubuntu/sunware-tech/ms-dynamics"
REPO_URL="https://github.com/GopiSunware/eis-d365-petinsure.git"

echo "=============================================="
echo "  Initialize Git Repository"
echo "  Target: $REPO_URL"
echo "=============================================="
echo ""

cd "$PROJECT_ROOT"

# Step 1: Initialize
echo "=== Step 1: Initialize Git ==="
if [[ -d ".git" ]]; then
    echo -e "${YELLOW}Git already initialized.${NC}"
else
    git init
    echo -e "${GREEN}Git initialized.${NC}"
fi
echo ""

# Step 2: Configure user
echo "=== Step 2: Configure Git User ==="
git config user.name "Gopinath Varadharajan"
git config user.email "gopi@sunwaretechnologies.com"
echo "User: $(git config user.name)"
echo "Email: $(git config user.email)"
echo ""

# Step 3: Create .gitignore
echo "=== Step 3: Create .gitignore ==="
cat > .gitignore << 'EOF'
# Environment files with secrets
.env
.env.local
.env.production
*.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env_*/
.venv/
*.egg-info/
dist/
build/

# Node.js
node_modules/
.next/
out/
npm-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
*.log

# Terraform
*.tfstate
*.tfstate.*
.terraform/
*.tfplan

# Docker
*.tar

# Temp files
*.tmp
*.temp
tmp/
temp/

# Large files
*.zip
*.tar.gz
*.rar

# Keep these
!.env.example
!requirements.txt
!package.json
EOF
echo -e "${GREEN}.gitignore created${NC}"
echo ""

# Step 4: Add remote
echo "=== Step 4: Configure Remote ==="
EXISTING_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

if [[ -n "$EXISTING_REMOTE" ]]; then
    echo "Current remote: $EXISTING_REMOTE"
    read -p "Update remote? [y/N]: " UPDATE_REMOTE
    if [[ "$UPDATE_REMOTE" != "y" && "$UPDATE_REMOTE" != "Y" ]]; then
        echo "Keeping existing remote."
    else
        echo ""
        echo "Enter your GitHub PAT (or press Enter to use credential prompt):"
        read -s PAT
        echo ""

        if [[ -n "$PAT" ]]; then
            git remote set-url origin "https://${PAT}@github.com/GopiSunware/eis-d365-petinsure.git"
            echo -e "${GREEN}Remote updated with PAT${NC}"
        else
            git remote set-url origin "$REPO_URL"
            echo -e "${GREEN}Remote updated (will prompt for credentials)${NC}"
        fi
    fi
else
    echo "No remote configured."
    echo ""
    echo "Enter your GitHub PAT (or press Enter to use credential prompt):"
    read -s PAT
    echo ""

    if [[ -n "$PAT" ]]; then
        git remote add origin "https://${PAT}@github.com/GopiSunware/eis-d365-petinsure.git"
        echo -e "${GREEN}Remote added with PAT${NC}"
    else
        git remote add origin "$REPO_URL"
        echo -e "${GREEN}Remote added (will prompt for credentials)${NC}"
    fi
fi
echo ""

# Step 5: Initial commit
echo "=== Step 5: Initial Commit ==="
git add .
CHANGES=$(git status --porcelain | wc -l)
echo "$CHANGES files staged"

if [[ $CHANGES -gt 0 ]]; then
    read -p "Create initial commit? [Y/n]: " DO_COMMIT
    if [[ "$DO_COMMIT" != "n" && "$DO_COMMIT" != "N" ]]; then
        git commit -m "Initial commit: EIS-D365 Pet Insurance Platform

- EIS-Dynamics POC: AI-powered claims processing
- PetInsure360: Azure data platform with medallion architecture
- Claude Code skills for deployment and configuration

🤖 Generated with Claude Code"
        echo -e "${GREEN}Committed!${NC}"
    fi
else
    echo "No changes to commit."
fi
echo ""

# Step 6: Push
echo "=== Step 6: Push to GitHub ==="
git branch -M main

read -p "Push to GitHub? [Y/n]: " DO_PUSH
if [[ "$DO_PUSH" != "n" && "$DO_PUSH" != "N" ]]; then
    echo "Pushing to origin/main..."
    git push -u origin main

    echo ""
    echo -e "${GREEN}✅ Repository initialized and pushed!${NC}"
    echo ""
    echo "View at: https://github.com/GopiSunware/eis-d365-petinsure"
else
    echo "Skipped push. Run 'git push -u origin main' when ready."
fi

echo ""
echo "=== Done ==="
