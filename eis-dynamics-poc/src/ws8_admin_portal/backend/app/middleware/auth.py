"""Authentication and authorization middleware."""

import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from ..config import settings
from ..models.users import User, Permission, ROLE_PERMISSIONS, UserRole

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for user."""
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))

    to_encode = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role if isinstance(user.role, str) else user.role.value,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """Get current authenticated user from JWT token."""
    # DEV MODE: Return a default admin user for development
    if settings.DEV_MODE:
        dev_user = User(
            id="dev-admin-001",
            email="admin@eis-dynamics.com",
            name="Dev Admin",
            role=UserRole.ADMIN,
        )
        request.state.user = dev_user
        return dev_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Create user object from token payload
    user = User(
        id=user_id,
        email=payload.get("email", ""),
        name=payload.get("name", ""),
        role=payload.get("role", "viewer"),
    )

    # Store user in request state for audit logging
    request.state.user = user

    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def require_permission(permission: Permission) -> Callable:
    """
    Dependency factory that requires a specific permission.

    Usage:
        @router.get("/config")
        async def get_config(user: User = Depends(require_permission(Permission.CONFIG_AI_READ))):
            ...
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required",
            )
        return user

    return permission_checker


def require_role(*roles: UserRole) -> Callable:
    """
    Dependency factory that requires one of the specified roles.

    Usage:
        @router.post("/approve")
        async def approve(user: User = Depends(require_role(UserRole.ADMIN, UserRole.APPROVER))):
            ...
    """
    async def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        user_role = UserRole(user.role) if isinstance(user.role, str) else user.role

        if user_role not in roles:
            role_names = [r.value for r in roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: one of {role_names}",
            )
        return user

    return role_checker


class AuthMiddleware:
    """
    Middleware to extract user from token for all requests.
    Does not enforce authentication - use dependencies for that.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Create a mock request to extract headers
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()

            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = verify_token(token)
                if payload:
                    scope["state"] = scope.get("state", {})
                    scope["state"]["user"] = User(
                        id=payload.get("sub", ""),
                        email=payload.get("email", ""),
                        name=payload.get("name", ""),
                        role=payload.get("role", "viewer"),
                    )

        await self.app(scope, receive, send)
