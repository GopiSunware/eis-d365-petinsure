# Secrets Management Patterns

## Overview

Secrets (API keys, passwords, connection strings) should:
1. **Never** be committed to Git
2. Work locally via `.env` files
3. Use cloud secret managers in production

## Hierarchy of Secret Sources

```
1. Environment Variables    (highest priority)
2. .env file                (local development)
3. Cloud Secret Manager     (production)
4. Default value            (lowest priority, non-sensitive only)
```

## Configuration Pattern

```python
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment detection
    ENVIRONMENT: str = "dev"

    # Secrets from .env or environment
    ANTHROPIC_API_KEY: str = Field(default="")
    OPENAI_API_KEY: str = Field(default="")
    DATABASE_URL: str = Field(default="")

    # Cloud secret manager config
    KEY_VAULT_URI: str = Field(default="")  # Azure
    AWS_SECRET_NAME: str = Field(default="")  # AWS

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

## Secret Resolution Pattern

```python
from typing import Optional


async def get_secret(name: str) -> Optional[str]:
    """
    Get secret from best available source.

    Priority:
    1. Environment variable
    2. Azure Key Vault (if configured)
    3. AWS Secrets Manager (if configured)
    """
    settings = get_settings()

    # 1. Check environment variable
    env_value = getattr(settings, name, None)
    if env_value:
        return env_value

    # 2. Try Azure Key Vault
    if settings.KEY_VAULT_URI:
        secret = await get_from_azure_keyvault(name)
        if secret:
            return secret

    # 3. Try AWS Secrets Manager
    if settings.AWS_SECRET_NAME:
        secret = await get_from_aws_secrets(name)
        if secret:
            return secret

    return None
```

## Azure Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


async def get_from_azure_keyvault(secret_name: str) -> Optional[str]:
    """Retrieve secret from Azure Key Vault."""
    settings = get_settings()

    if not settings.KEY_VAULT_URI:
        return None

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(
            vault_url=settings.KEY_VAULT_URI,
            credential=credential
        )
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        print(f"Key Vault error: {e}")
        return None
```

### Azure Key Vault Setup

```bash
# Create Key Vault
az keyvault create \
    --name my-keyvault \
    --resource-group my-rg \
    --location eastus

# Store secret
az keyvault secret set \
    --vault-name my-keyvault \
    --name anthropic-api-key \
    --value "sk-ant-..."

# Grant access to app
az keyvault set-policy \
    --name my-keyvault \
    --object-id <app-object-id> \
    --secret-permissions get list
```

## AWS Secrets Manager

```python
import boto3
import json


async def get_from_aws_secrets(secret_name: str) -> Optional[str]:
    """Retrieve secret from AWS Secrets Manager."""
    settings = get_settings()

    try:
        client = boto3.client("secretsmanager", region_name="us-east-1")
        response = client.get_secret_value(SecretId=settings.AWS_SECRET_NAME)

        # Secrets can be JSON with multiple values
        secrets = json.loads(response["SecretString"])
        return secrets.get(secret_name)
    except Exception as e:
        print(f"AWS Secrets error: {e}")
        return None
```

### AWS Secrets Manager Setup

```bash
# Create secret
aws secretsmanager create-secret \
    --name eis-dynamics/api-keys \
    --secret-string '{"ANTHROPIC_API_KEY":"sk-ant-...","OPENAI_API_KEY":"sk-..."}'

# Update secret
aws secretsmanager put-secret-value \
    --secret-id eis-dynamics/api-keys \
    --secret-string '{"ANTHROPIC_API_KEY":"new-key"}'

# Grant access via IAM policy
{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:eis-dynamics/*"
}
```

## Environment Files

### .env.example (Committed)
```bash
# Secrets - fill in your values
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
DATABASE_URL=

# Cloud secret managers (optional)
KEY_VAULT_URI=
AWS_SECRET_NAME=
```

### .env (Local - Gitignored)
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-proj-xxxxx
DATABASE_URL=postgresql://localhost/mydb
```

### .env.production (Cloud - Gitignored or Encrypted)
```bash
# In production, secrets come from cloud managers
ANTHROPIC_API_KEY=  # Empty - fetched from Key Vault
KEY_VAULT_URI=https://my-keyvault.vault.azure.net/

# Or AWS
AWS_SECRET_NAME=eis-dynamics/api-keys
```

## API Key Validation

```python
def validate_api_key(key_name: str) -> bool:
    """Validate that an API key is configured."""
    key = get_settings().__dict__.get(key_name, "")

    if not key:
        return False

    # Basic format validation
    if key_name == "ANTHROPIC_API_KEY":
        return key.startswith("sk-ant-")
    elif key_name == "OPENAI_API_KEY":
        return key.startswith("sk-")

    return len(key) > 10


def check_required_secrets():
    """Check all required secrets are configured."""
    required = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    missing = [k for k in required if not validate_api_key(k)]

    if missing:
        raise ValueError(f"Missing secrets: {', '.join(missing)}")
```

## Git Safety

### .gitignore
```gitignore
# Environment files with secrets
.env
.env.local
.env.*.local
.env.production

# Keep templates
!.env.example
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for hardcoded secrets
if git diff --cached --name-only | xargs grep -l "sk-ant-\|sk-proj-\|password=" 2>/dev/null; then
    echo "ERROR: Potential secrets detected in staged files!"
    exit 1
fi
```

## Testing with Mock Secrets

```python
import pytest
from unittest.mock import patch


@pytest.fixture
def mock_secrets():
    """Mock secrets for testing."""
    test_secrets = {
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "OPENAI_API_KEY": "sk-test-key",
    }
    with patch.dict(os.environ, test_secrets):
        yield


def test_api_call(mock_secrets):
    # Tests run with mock API keys
    ...
```

## Rotating Secrets

```python
async def rotate_secret(secret_name: str, new_value: str):
    """Rotate a secret in cloud manager."""
    settings = get_settings()

    if settings.KEY_VAULT_URI:
        # Azure Key Vault
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=settings.KEY_VAULT_URI, credential=credential)
        client.set_secret(secret_name, new_value)

    elif settings.AWS_SECRET_NAME:
        # AWS Secrets Manager
        client = boto3.client("secretsmanager")
        current = json.loads(
            client.get_secret_value(SecretId=settings.AWS_SECRET_NAME)["SecretString"]
        )
        current[secret_name] = new_value
        client.put_secret_value(
            SecretId=settings.AWS_SECRET_NAME,
            SecretString=json.dumps(current)
        )
```
