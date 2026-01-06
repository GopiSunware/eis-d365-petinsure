# GitHub PAT (Personal Access Token) Setup

## Overview

GitHub requires Personal Access Tokens (PAT) for HTTPS authentication instead of passwords.

## Create a PAT

### Step 1: Go to GitHub Settings
1. Log in to https://github.com
2. Click your profile picture → **Settings**
3. Scroll down to **Developer settings** (left sidebar)
4. Click **Personal access tokens** → **Tokens (classic)**

### Step 2: Generate New Token
1. Click **Generate new token** → **Generate new token (classic)**
2. Set a descriptive name: `eis-d365-petinsure-dev`
3. Set expiration (90 days recommended)
4. Select scopes:
   - ✅ `repo` (full repository access)
   - ✅ `workflow` (if using GitHub Actions)

5. Click **Generate token**
6. **COPY THE TOKEN NOW** - you won't see it again!

## Configure Git to Use PAT

### Method 1: URL with PAT (Simplest)

```bash
# Set remote with PAT embedded
git remote set-url origin https://YOUR_PAT@github.com/GopiSunware/eis-d365-petinsure.git

# Verify
git remote -v
```

### Method 2: Credential Helper (Recommended)

```bash
# Enable credential storage
git config --global credential.helper store

# First push will prompt for credentials
git push origin main

# Enter when prompted:
# Username: GopiSunware
# Password: YOUR_PAT (paste your token here)
```

Credentials are stored in `~/.git-credentials`

### Method 3: Credential Manager (Windows)

```bash
# Use Windows Credential Manager
git config --global credential.helper manager

# Credentials stored in Windows Credential Manager
```

### Method 4: Environment Variable

```bash
# Set in .bashrc or .zshrc
export GITHUB_TOKEN=your_pat_here

# Use in git commands
git clone https://${GITHUB_TOKEN}@github.com/GopiSunware/eis-d365-petinsure.git
```

## Verify PAT Works

```bash
# Test authentication
curl -H "Authorization: token YOUR_PAT" https://api.github.com/user

# Should return your GitHub user info
```

## Rotate/Update PAT

When PAT expires or needs updating:

```bash
# Update remote URL
git remote set-url origin https://NEW_PAT@github.com/GopiSunware/eis-d365-petinsure.git

# Or clear stored credentials and re-authenticate
# Linux/Mac:
rm ~/.git-credentials

# Windows:
# Open Credential Manager → Windows Credentials → Remove github.com entries

# Next push will prompt for new credentials
git push origin main
```

## Security Best Practices

1. **Never commit PAT** - Don't put it in code or .env files that get committed
2. **Use minimal scopes** - Only grant permissions you need
3. **Set expiration** - Rotate tokens regularly
4. **Use different tokens** - One per machine/project
5. **Revoke if compromised** - Delete token immediately in GitHub settings

## Troubleshooting

### "Authentication failed"
```bash
# Check remote URL
git remote -v

# Update with valid PAT
git remote set-url origin https://VALID_PAT@github.com/GopiSunware/eis-d365-petinsure.git
```

### "Permission denied"
```bash
# Verify PAT has 'repo' scope
# Regenerate token with correct permissions
```

### "Token expired"
```bash
# Generate new token in GitHub settings
# Update remote URL or credentials
```

## Quick Reference

| Setting | Value |
|---------|-------|
| GitHub User | `GopiSunware` |
| Repository | `eis-d365-petinsure` |
| Remote URL | `https://github.com/GopiSunware/eis-d365-petinsure.git` |
| Clone URL | `https://PAT@github.com/GopiSunware/eis-d365-petinsure.git` |
