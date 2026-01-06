---
name: env-config
description: Configuration-driven development - same code runs locally and in cloud. Use when setting up environment variables, creating config files, switching between local/cloud, managing secrets, or configuring services for different environments.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Environment Configuration Management

## Overview

This skill enables **configuration-driven development** where the same codebase runs seamlessly in:
- **Local development** (localhost, file storage)
- **Cloud production** (AWS/Azure, managed services)

The key principle: **Code never changes between environments - only configuration does.**

## Quick Reference

### Check Current Environment
```bash
# See all .env files in project
find . -name ".env*" -not -path "*/node_modules/*" -not -path "*/venv/*"

# View current config
cat .env | grep -v "^#" | grep -v "^$"
```

### Switch Environments
```bash
# Local development
cp .env.local .env

# Production/Cloud
cp .env.production .env

# Or use symbolic links
ln -sf .env.local .env
```

## Configuration Pattern (Pydantic)

The projects use **Pydantic Settings** for type-safe configuration:

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment detection
    ENVIRONMENT: str = Field(default="dev")
    DEBUG: bool = Field(default=False)

    # Storage abstraction (local vs cloud)
    STORAGE_TYPE: Literal["local", "azure", "s3"] = "local"
    STORAGE_PATH: str = "./data"  # Local path

    # Cloud storage (when STORAGE_TYPE != "local")
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AWS_S3_BUCKET: str = ""

    # Service URLs (change per environment)
    API_URL: str = "http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }
```

## Environment Files

### File Hierarchy
```
project/
├── .env              # Active config (gitignored)
├── .env.example      # Template with placeholders (committed)
├── .env.local        # Local development (gitignored)
├── .env.production   # Production values (gitignored or encrypted)
└── .env.test         # Test environment (optional)
```

### .env.example (Committed to Git)
```bash
# ===========================================
# ENVIRONMENT
# ===========================================
ENVIRONMENT=dev
DEBUG=true

# ===========================================
# STORAGE (local | azure | s3)
# ===========================================
STORAGE_TYPE=local
STORAGE_PATH=./data

# Azure Storage (when STORAGE_TYPE=azure)
AZURE_STORAGE_ACCOUNT=
AZURE_STORAGE_KEY=
AZURE_STORAGE_CONTAINER=

# AWS S3 (when STORAGE_TYPE=s3)
AWS_S3_BUCKET=
AWS_REGION=

# ===========================================
# SERVICE URLS
# ===========================================
API_URL=http://localhost:8000
```

## Storage Abstraction

See [STORAGE.md](STORAGE.md) for complete storage abstraction patterns.

### Quick Pattern
```python
def get_storage_client():
    settings = get_settings()

    if settings.STORAGE_TYPE == "local":
        return LocalStorage(settings.STORAGE_PATH)
    elif settings.STORAGE_TYPE == "azure":
        return AzureStorage(settings.AZURE_STORAGE_CONNECTION_STRING)
    elif settings.STORAGE_TYPE == "s3":
        return S3Storage(settings.AWS_S3_BUCKET)
```

## Service URLs Pattern

### Backend (Python)
```python
class Settings(BaseSettings):
    # Default to local, override in production
    CLAIMS_API_URL: str = "http://localhost:8000"
    PIPELINE_API_URL: str = "http://localhost:8006"
```

### Frontend (Next.js/React)
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8006

# .env.production
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_WS_URL=wss://api.example.com
```

## Project-Specific Configs

### EIS-Dynamics POC

**Local** (`.env.local`):
```bash
NEXT_PUBLIC_CLAIMS_API_URL=http://localhost:8000
NEXT_PUBLIC_PIPELINE_API_URL=http://localhost:8006
NEXT_PUBLIC_PIPELINE_WS_URL=ws://localhost:8006
```

**Production** (`.env.production`):
```bash
NEXT_PUBLIC_CLAIMS_API_URL=https://p7qrmgi9sp.us-east-1.awsapprunner.com
NEXT_PUBLIC_PIPELINE_API_URL=https://bn9ymuxtwp.us-east-1.awsapprunner.com
```

### PetInsure360

**Local**:
```bash
AZURE_STORAGE_ACCOUNT=petinsud7i43
USE_LOCAL_DATA=true
DATA_PATH=./data/raw
```

**Production**:
```bash
AZURE_STORAGE_ACCOUNT=petinsud7i43
USE_LOCAL_DATA=false
```

## Secrets Management

See [SECRETS.md](SECRETS.md) for complete secrets handling patterns.

### Quick Pattern
```python
def get_api_key():
    settings = get_settings()

    # Try environment variable first
    if settings.ANTHROPIC_API_KEY:
        return settings.ANTHROPIC_API_KEY

    # Fall back to cloud secrets manager
    if settings.ENVIRONMENT == "production":
        return get_from_keyvault("anthropic-api-key")

    raise ValueError("API key not configured")
```

## Validation Script

Run to validate your environment:
```bash
python scripts/validate_env.py
```

## Common Tasks

### Create New Service Config
```bash
# Generate .env.example template
python -c "from app.config import Settings; print(Settings.model_json_schema())"
```

### Sync Environments
```bash
# Compare .env files
diff .env.local .env.production
```

### Check Missing Variables
```bash
# Find vars in .env.example not in .env
comm -23 <(grep "^[A-Z]" .env.example | cut -d= -f1 | sort) \
         <(grep "^[A-Z]" .env | cut -d= -f1 | sort)
```
