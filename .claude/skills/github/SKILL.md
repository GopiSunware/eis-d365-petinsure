---
name: github
description: Git and GitHub operations for pet insurance projects. Commit, push, pull using PAT authentication. Use when committing code, pushing to GitHub, creating branches, or syncing with remote repository.
allowed-tools: Bash, Read, Write
---

# GitHub Operations

## Repository

| Project | GitHub URL |
|---------|------------|
| EIS-D365-PetInsure | https://github.com/GopiSunware/eis-d365-petinsure |

## Quick Commands

### Status & Info
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics
git status
git log --oneline -5
git remote -v
```

### Commit Changes
```bash
git add .
git commit -m "feat: your message here"
```

### Push to GitHub
```bash
git push origin main
```

## Setup (First Time)

### Step 1: Initialize Git Repository
```bash
cd /mnt/c/Shri\ Hari\ Hari/Ubuntu/sunware-tech/ms-dynamics
git init
git branch -M main
```

### Step 2: Add Remote with PAT
```bash
# Using PAT in URL (replace YOUR_PAT with actual token)
git remote add origin https://YOUR_PAT@github.com/GopiSunware/eis-d365-petinsure.git

# Or if remote exists, update it
git remote set-url origin https://YOUR_PAT@github.com/GopiSunware/eis-d365-petinsure.git
```

### Step 3: Configure Git User
```bash
git config user.name "Gopinath Varadharajan"
git config user.email "gopi@sunwaretechnologies.com"
```

### Step 4: First Push
```bash
git add .
git commit -m "Initial commit: EIS-D365 Pet Insurance Platform"
git push -u origin main
```

## PAT Authentication

See [PAT_SETUP.md](PAT_SETUP.md) for detailed PAT configuration.

### Quick PAT Setup
```bash
# Store credentials
git config --global credential.helper store

# First push will prompt for credentials
# Username: GopiSunware
# Password: YOUR_GITHUB_PAT (not your password!)
```

## Common Operations

### Create Feature Branch
```bash
git checkout -b feature/your-feature-name
git push -u origin feature/your-feature-name
```

### Update from Remote
```bash
git fetch origin
git pull origin main
```

### Merge Feature Branch
```bash
git checkout main
git merge feature/your-feature-name
git push origin main
```

### Discard Local Changes
```bash
# Discard unstaged changes
git checkout -- .

# Discard all changes including staged
git reset --hard HEAD
```

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```bash
git commit -m "feat(claims): add fraud detection endpoint"
git commit -m "fix(auth): resolve API key validation error"
git commit -m "docs(readme): update deployment instructions"
```

## .gitignore

Ensure these are ignored:
```gitignore
# Environment files with secrets
.env
.env.local
.env.production

# Python
__pycache__/
*.pyc
venv/
env_*/
*.egg-info/

# Node
node_modules/
.next/
dist/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Terraform
*.tfstate
*.tfstate.*
.terraform/

# Logs
*.log
logs/
```

## Workflow Script

For guided git operations:
```bash
./scripts/git-workflow.sh
```
