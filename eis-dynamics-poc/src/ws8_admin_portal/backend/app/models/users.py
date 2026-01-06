"""User management and RBAC models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"  # Full access to everything
    CONFIG_MANAGER = "config_manager"  # Can manage configs, needs approval for critical changes
    APPROVER = "approver"  # Can approve/reject pending changes
    VIEWER = "viewer"  # Read-only access
    COST_ANALYST = "cost_analyst"  # Access to cost data only


class Permission(str, Enum):
    """Granular permissions."""
    # Config permissions
    CONFIG_AI_READ = "config:ai:read"
    CONFIG_AI_WRITE = "config:ai:write"
    CONFIG_CLAIMS_READ = "config:claims:read"
    CONFIG_CLAIMS_WRITE = "config:claims:write"
    CONFIG_POLICY_READ = "config:policy:read"
    CONFIG_POLICY_WRITE = "config:policy:write"
    CONFIG_RATING_READ = "config:rating:read"
    CONFIG_RATING_WRITE = "config:rating:write"

    # Approval permissions
    APPROVAL_CREATE = "approval:create"
    APPROVAL_APPROVE = "approval:approve"
    APPROVAL_REJECT = "approval:reject"

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"

    # Audit
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

    # Cost monitoring
    COST_READ = "cost:read"
    COST_BUDGET_WRITE = "cost:budget:write"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: list(Permission),  # All permissions
    UserRole.CONFIG_MANAGER: [
        Permission.CONFIG_AI_READ,
        Permission.CONFIG_AI_WRITE,
        Permission.CONFIG_CLAIMS_READ,
        Permission.CONFIG_CLAIMS_WRITE,
        Permission.CONFIG_POLICY_READ,
        Permission.CONFIG_POLICY_WRITE,
        Permission.CONFIG_RATING_READ,
        Permission.CONFIG_RATING_WRITE,
        Permission.APPROVAL_CREATE,
        Permission.AUDIT_READ,
        Permission.COST_READ,
    ],
    UserRole.APPROVER: [
        Permission.CONFIG_AI_READ,
        Permission.CONFIG_CLAIMS_READ,
        Permission.CONFIG_POLICY_READ,
        Permission.CONFIG_RATING_READ,
        Permission.APPROVAL_APPROVE,
        Permission.APPROVAL_REJECT,
        Permission.AUDIT_READ,
    ],
    UserRole.VIEWER: [
        Permission.CONFIG_AI_READ,
        Permission.CONFIG_CLAIMS_READ,
        Permission.CONFIG_POLICY_READ,
        Permission.CONFIG_RATING_READ,
        Permission.AUDIT_READ,
        Permission.COST_READ,
    ],
    UserRole.COST_ANALYST: [
        Permission.COST_READ,
        Permission.COST_BUDGET_WRITE,
        Permission.AUDIT_READ,
    ],
}


class User(BaseModel):
    """Admin portal user."""
    id: Optional[str] = None
    email: EmailStr
    name: str
    role: UserRole

    # Password (hashed, not returned in responses)
    password_hash: Optional[str] = Field(default=None, exclude=True)

    # Azure AD integration (optional)
    azure_ad_oid: Optional[str] = None

    # Status
    is_active: bool = True
    last_login: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Additional permissions beyond role
    additional_permissions: List[Permission] = Field(default_factory=list)

    model_config = {"use_enum_values": True}

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        # Convert role string back to enum if needed
        role = UserRole(self.role) if isinstance(self.role, str) else self.role
        role_perms = ROLE_PERMISSIONS.get(role, [])
        return permission in role_perms or permission in self.additional_permissions

    def get_all_permissions(self) -> List[Permission]:
        """Get all permissions for this user."""
        role = UserRole(self.role) if isinstance(self.role, str) else self.role
        role_perms = set(ROLE_PERMISSIONS.get(role, []))
        additional = set(self.additional_permissions)
        return list(role_perms | additional)


class UserCreate(BaseModel):
    """Request to create a user."""
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)
    role: UserRole
    azure_ad_oid: Optional[str] = None
    additional_permissions: List[Permission] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Request to update a user."""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    additional_permissions: Optional[List[Permission]] = None
    password: Optional[str] = Field(default=None, min_length=8)


class UserResponse(BaseModel):
    """User response without sensitive data."""
    id: str
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    permissions: List[str] = Field(default_factory=list)

    model_config = {"use_enum_values": True}


class UserListResponse(BaseModel):
    """Response for listing users."""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
