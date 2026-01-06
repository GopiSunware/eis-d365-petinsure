#!/bin/bash
# Git Workflow Script
# Guided git operations for the pet insurance projects

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
echo "  Git Workflow - EIS-D365 PetInsure"
echo "=============================================="
echo ""

cd "$PROJECT_ROOT"

# Check if git is initialized
if [[ ! -d ".git" ]]; then
    echo -e "${YELLOW}Git not initialized. Initializing...${NC}"
    git init
    git branch -M main
    echo ""
fi

# Check remote
REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
if [[ -z "$REMOTE" ]]; then
    echo -e "${YELLOW}No remote configured.${NC}"
    echo ""
    echo "Enter your GitHub PAT (Personal Access Token):"
    read -s PAT
    echo ""

    if [[ -n "$PAT" ]]; then
        git remote add origin "https://${PAT}@github.com/GopiSunware/eis-d365-petinsure.git"
        echo -e "${GREEN}Remote added with PAT${NC}"
    else
        git remote add origin "$REPO_URL"
        echo -e "${GREEN}Remote added (will prompt for credentials on push)${NC}"
    fi
    echo ""
fi

# Show current status
echo "=== Current Status ==="
echo ""
git status --short
echo ""

# Count changes
CHANGES=$(git status --porcelain | wc -l)
if [[ $CHANGES -eq 0 ]]; then
    echo -e "${GREEN}No changes to commit.${NC}"
    exit 0
fi

echo -e "${BLUE}$CHANGES file(s) changed${NC}"
echo ""

# Show menu
echo "What would you like to do?"
echo "  1) Commit all changes"
echo "  2) Commit specific files"
echo "  3) Push to GitHub"
echo "  4) Pull from GitHub"
echo "  5) View diff"
echo "  6) Create branch"
echo "  7) Cancel"
echo ""
read -p "Select [1-7]: " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "Enter commit message:"
        read -p "> " COMMIT_MSG

        if [[ -z "$COMMIT_MSG" ]]; then
            echo "Commit message required."
            exit 1
        fi

        git add .
        git commit -m "$COMMIT_MSG"
        echo ""
        echo -e "${GREEN}Changes committed!${NC}"

        read -p "Push to GitHub? [y/N]: " PUSH
        if [[ "$PUSH" == "y" || "$PUSH" == "Y" ]]; then
            git push -u origin main
            echo -e "${GREEN}Pushed to GitHub!${NC}"
        fi
        ;;

    2)
        echo ""
        echo "Changed files:"
        git status --porcelain | nl
        echo ""
        echo "Enter file numbers to stage (space-separated):"
        read -p "> " FILE_NUMS

        for num in $FILE_NUMS; do
            FILE=$(git status --porcelain | sed -n "${num}p" | awk '{print $2}')
            if [[ -n "$FILE" ]]; then
                git add "$FILE"
                echo "Staged: $FILE"
            fi
        done

        echo ""
        echo "Enter commit message:"
        read -p "> " COMMIT_MSG

        git commit -m "$COMMIT_MSG"
        echo -e "${GREEN}Changes committed!${NC}"
        ;;

    3)
        BRANCH=$(git branch --show-current)
        echo ""
        echo "Pushing to origin/$BRANCH..."
        git push -u origin "$BRANCH"
        echo -e "${GREEN}Pushed!${NC}"
        ;;

    4)
        BRANCH=$(git branch --show-current)
        echo ""
        echo "Pulling from origin/$BRANCH..."
        git pull origin "$BRANCH"
        echo -e "${GREEN}Pulled!${NC}"
        ;;

    5)
        echo ""
        git diff --stat
        echo ""
        read -p "Show full diff? [y/N]: " FULL_DIFF
        if [[ "$FULL_DIFF" == "y" || "$FULL_DIFF" == "Y" ]]; then
            git diff | head -100
        fi
        ;;

    6)
        echo ""
        read -p "Enter branch name: " BRANCH_NAME
        git checkout -b "$BRANCH_NAME"
        echo -e "${GREEN}Created and switched to branch: $BRANCH_NAME${NC}"

        read -p "Push branch to GitHub? [y/N]: " PUSH_BRANCH
        if [[ "$PUSH_BRANCH" == "y" || "$PUSH_BRANCH" == "Y" ]]; then
            git push -u origin "$BRANCH_NAME"
        fi
        ;;

    7)
        echo "Cancelled."
        exit 0
        ;;

    *)
        echo "Invalid choice."
        exit 1
        ;;
esac

echo ""
echo "=== Done ==="
