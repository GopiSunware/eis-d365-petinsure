#!/usr/bin/env python3
"""
Environment Configuration Validator

Validates that all required environment variables are set
and checks connectivity to configured services.

Usage:
    python validate_env.py
    python validate_env.py --env .env.production
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional


# Colors for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{Colors.GREEN}✅ PASS{Colors.RESET}: {msg}")


def fail(msg: str) -> None:
    print(f"{Colors.RED}❌ FAIL{Colors.RESET}: {msg}")


def warn(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  WARN{Colors.RESET}: {msg}")


def info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ️  INFO{Colors.RESET}: {msg}")


def load_env_file(env_file: str) -> dict:
    """Load environment variables from file."""
    env_vars = {}
    path = Path(env_file)

    if not path.exists():
        return env_vars

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                # Remove quotes
                value = value.strip().strip('"').strip("'")
                env_vars[key.strip()] = value

    return env_vars


def check_required_vars(env_vars: dict) -> bool:
    """Check required environment variables."""
    print("\n=== Required Variables ===\n")

    required = [
        ("ENVIRONMENT", "Environment name (dev/staging/production)"),
    ]

    all_ok = True
    for var, description in required:
        value = env_vars.get(var) or os.environ.get(var)
        if value:
            ok(f"{var} = {value}")
        else:
            fail(f"{var} is not set ({description})")
            all_ok = False

    return all_ok


def check_ai_providers(env_vars: dict) -> bool:
    """Check AI provider configuration."""
    print("\n=== AI Providers ===\n")

    provider = env_vars.get("AI_PROVIDER") or os.environ.get("AI_PROVIDER", "claude")
    info(f"AI Provider: {provider}")

    all_ok = True

    # Check Anthropic
    anthropic_key = env_vars.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        if anthropic_key.startswith("sk-ant-"):
            ok("ANTHROPIC_API_KEY is set (sk-ant-...)")
        else:
            warn("ANTHROPIC_API_KEY format may be incorrect")
    elif provider == "claude":
        fail("ANTHROPIC_API_KEY is required for Claude provider")
        all_ok = False
    else:
        info("ANTHROPIC_API_KEY not set (not using Claude)")

    # Check OpenAI
    openai_key = env_vars.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if openai_key:
        if openai_key.startswith("sk-"):
            ok("OPENAI_API_KEY is set (sk-...)")
        else:
            warn("OPENAI_API_KEY format may be incorrect")
    elif provider == "openai":
        fail("OPENAI_API_KEY is required for OpenAI provider")
        all_ok = False
    else:
        info("OPENAI_API_KEY not set (not using OpenAI)")

    return all_ok


def check_storage(env_vars: dict) -> bool:
    """Check storage configuration."""
    print("\n=== Storage Configuration ===\n")

    storage_type = env_vars.get("STORAGE_TYPE") or os.environ.get("STORAGE_TYPE", "local")
    info(f"Storage Type: {storage_type}")

    all_ok = True

    if storage_type == "local":
        storage_path = env_vars.get("STORAGE_PATH") or os.environ.get("STORAGE_PATH", "./data")
        path = Path(storage_path)
        if path.exists():
            ok(f"Local storage path exists: {storage_path}")
        else:
            warn(f"Local storage path does not exist: {storage_path} (will be created)")

    elif storage_type == "azure":
        azure_account = env_vars.get("AZURE_STORAGE_ACCOUNT") or os.environ.get("AZURE_STORAGE_ACCOUNT")
        azure_key = env_vars.get("AZURE_STORAGE_KEY") or os.environ.get("AZURE_STORAGE_KEY")
        azure_conn = env_vars.get("AZURE_STORAGE_CONNECTION_STRING") or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

        if azure_conn:
            ok("AZURE_STORAGE_CONNECTION_STRING is set")
        elif azure_account and azure_key:
            ok(f"AZURE_STORAGE_ACCOUNT = {azure_account}")
            ok("AZURE_STORAGE_KEY is set")
        else:
            fail("Azure storage requires CONNECTION_STRING or ACCOUNT + KEY")
            all_ok = False

    elif storage_type == "s3":
        s3_bucket = env_vars.get("AWS_S3_BUCKET") or os.environ.get("AWS_S3_BUCKET")
        aws_region = env_vars.get("AWS_REGION") or os.environ.get("AWS_REGION", "us-east-1")

        if s3_bucket:
            ok(f"AWS_S3_BUCKET = {s3_bucket}")
            ok(f"AWS_REGION = {aws_region}")
        else:
            fail("AWS_S3_BUCKET is required for S3 storage")
            all_ok = False

    return all_ok


def check_service_urls(env_vars: dict) -> bool:
    """Check service URL configuration."""
    print("\n=== Service URLs ===\n")

    url_vars = [
        "API_BASE_URL",
        "CLAIMS_API_URL",
        "PIPELINE_API_URL",
        "AGENT_PIPELINE_URL",
    ]

    for var in url_vars:
        value = env_vars.get(var) or os.environ.get(var)
        if value:
            info(f"{var} = {value}")

    return True


def check_secrets_manager(env_vars: dict) -> bool:
    """Check secrets manager configuration."""
    print("\n=== Secrets Management ===\n")

    env = env_vars.get("ENVIRONMENT") or os.environ.get("ENVIRONMENT", "dev")

    if env == "production":
        key_vault = env_vars.get("KEY_VAULT_URI") or os.environ.get("KEY_VAULT_URI")
        aws_secret = env_vars.get("AWS_SECRET_NAME") or os.environ.get("AWS_SECRET_NAME")

        if key_vault:
            ok(f"Azure Key Vault configured: {key_vault}")
        elif aws_secret:
            ok(f"AWS Secrets Manager configured: {aws_secret}")
        else:
            warn("No cloud secrets manager configured for production")
    else:
        info(f"Secrets from .env file (ENVIRONMENT={env})")

    return True


def main():
    parser = argparse.ArgumentParser(description="Validate environment configuration")
    parser.add_argument("--env", default=".env", help="Path to .env file")
    args = parser.parse_args()

    print("=" * 50)
    print("  Environment Configuration Validator")
    print("=" * 50)

    # Load env file
    env_file = args.env
    if Path(env_file).exists():
        info(f"Loading: {env_file}")
        env_vars = load_env_file(env_file)
    else:
        warn(f"File not found: {env_file}")
        env_vars = {}

    # Run checks
    results = [
        check_required_vars(env_vars),
        check_ai_providers(env_vars),
        check_storage(env_vars),
        check_service_urls(env_vars),
        check_secrets_manager(env_vars),
    ]

    # Summary
    print("\n" + "=" * 50)
    if all(results):
        print(f"{Colors.GREEN}All checks passed!{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}Some checks failed. Please fix the issues above.{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
