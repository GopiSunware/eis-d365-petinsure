"""API Routers for the Admin Portal."""

from . import (
    health,
    auth,
    ai_config,
    claims_rules,
    policy_config,
    rating_config,
    costs,
    audit,
    users,
    approvals,
)

__all__ = [
    "health",
    "auth",
    "ai_config",
    "claims_rules",
    "policy_config",
    "rating_config",
    "costs",
    "audit",
    "users",
    "approvals",
]
