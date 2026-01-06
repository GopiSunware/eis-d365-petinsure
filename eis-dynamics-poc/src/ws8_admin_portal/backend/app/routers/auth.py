"""Authentication endpoints."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request

from ..config import settings
from ..middleware.auth import create_access_token, get_current_user
from ..models.users import User, LoginRequest, LoginResponse, UserResponse
from ..services.user_service import get_user_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
):
    """
    Authenticate user and return JWT token.
    """
    user_service = get_user_service()
    audit_service = get_audit_service()

    # Initialize default admin if needed
    await user_service.initialize_default_admin()

    # Authenticate
    user = await user_service.authenticate(login_data.email, login_data.password)

    if not user:
        # Log failed attempt
        dummy_user = User(
            id="unknown",
            email=login_data.email,
            name="Unknown",
            role="viewer"
        )
        await audit_service.log_login(
            user=dummy_user,
            request=request,
            success=False,
            error_message="Invalid credentials",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token = create_access_token(user)

    # Log successful login
    await audit_service.log_login(
        user=user,
        request=request,
        success=True,
    )

    # Build response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        permissions=[p.value if hasattr(p, 'value') else p for p in user.get_all_permissions()],
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        user=user_response,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        permissions=[p.value if hasattr(p, 'value') else p for p in current_user.get_all_permissions()],
    )


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
):
    """Refresh JWT token."""
    access_token = create_access_token(current_user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRATION_HOURS * 3600,
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Logout (client should discard token).
    In a production system, you might add the token to a blacklist.
    """
    audit_service = get_audit_service()

    await audit_service.log(
        action="logout",
        category="authentication",
        entity_type="user",
        entity_id=current_user.id,
        user=current_user,
        request=request,
        success=True,
    )

    return {"message": "Successfully logged out"}
