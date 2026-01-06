"""Data models for the Admin Portal."""

from .users import User, UserCreate, UserUpdate, UserRole, Permission, ROLE_PERMISSIONS
from .approval import (
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalAction,
    ApprovalStatus,
    ConfigChangeType,
)
from .audit import AuditLog, AuditAction, AuditCategory, AuditLogQuery
from .ai_config import AIConfiguration, AIConfigUpdate, AIProvider, AIModel
from .claims_rules import (
    ClaimsRulesConfig,
    AutoAdjudicationConfig,
    FraudDetectionConfig,
    EscalationRules,
)
from .rating_config import (
    RatingFactorsConfig,
    BaseRates,
    BreedMultipliers,
    AgeFactors,
    GeographicFactors,
    Discounts,
)
from .policy_config import (
    PolicyPlansConfig,
    PlanDefinition,
    CoverageRules,
    WaitingPeriods,
    Exclusions,
)
from .costs import (
    CostSummary,
    CostDataPoint,
    CostDashboardData,
    BudgetAlert,
    BudgetAlertCreate,
    CostForecast,
    CloudProvider,
    TimeGranularity,
)

__all__ = [
    # Users
    "User",
    "UserCreate",
    "UserUpdate",
    "UserRole",
    "Permission",
    "ROLE_PERMISSIONS",
    # Approvals
    "ApprovalRequest",
    "ApprovalRequestCreate",
    "ApprovalAction",
    "ApprovalStatus",
    "ConfigChangeType",
    # Audit
    "AuditLog",
    "AuditAction",
    "AuditCategory",
    "AuditLogQuery",
    # AI Config
    "AIConfiguration",
    "AIConfigUpdate",
    "AIProvider",
    "AIModel",
    # Claims Rules
    "ClaimsRulesConfig",
    "AutoAdjudicationConfig",
    "FraudDetectionConfig",
    "EscalationRules",
    # Rating Config
    "RatingFactorsConfig",
    "BaseRates",
    "BreedMultipliers",
    "AgeFactors",
    "GeographicFactors",
    "Discounts",
    # Policy Config
    "PolicyPlansConfig",
    "PlanDefinition",
    "CoverageRules",
    "WaitingPeriods",
    "Exclusions",
    # Costs
    "CostSummary",
    "CostDataPoint",
    "CostDashboardData",
    "BudgetAlert",
    "BudgetAlertCreate",
    "CostForecast",
    "CloudProvider",
    "TimeGranularity",
]
