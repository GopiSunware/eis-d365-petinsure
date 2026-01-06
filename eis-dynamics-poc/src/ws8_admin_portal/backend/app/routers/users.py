"""User management endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..middleware.auth import require_permission, require_role
from ..models.users import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
)
from ..models.audit import AuditAction, AuditCategory
from ..services.user_service import get_user_service
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_permission(Permission.USER_READ)),
):
    """List all users with optional filters."""
    user_service = get_user_service()
    users, total = await user_service.list_users(
        role=role,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    user_responses = [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            is_active=u.is_active,
            last_login=u.last_login,
            created_at=u.created_at,
            permissions=[p.value if hasattr(p, 'value') else p for p in u.get_all_permissions()],
        )
        for u in users
    ]

    return UserListResponse(
        users=user_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=UserResponse)
async def create_user(
    request: Request,
    user_create: UserCreate,
    current_user: User = Depends(require_permission(Permission.USER_WRITE)),
):
    """Create a new user."""
    user_service = get_user_service()
    audit_service = get_audit_service()

    try:
        user = await user_service.create_user(user_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Audit log
    await audit_service.log(
        action=AuditAction.CREATE,
        category=AuditCategory.USER_MANAGEMENT,
        entity_type="user",
        entity_id=user.id,
        user=current_user,
        request=request,
        new_value={"email": user.email, "name": user.name, "role": user.role},
        change_summary=f"Created user {user.email}",
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        permissions=[p.value if hasattr(p, 'value') else p for p in user.get_all_permissions()],
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.USER_READ)),
):
    """Get a specific user."""
    user_service = get_user_service()
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        permissions=[p.value if hasattr(p, 'value') else p for p in user.get_all_permissions()],
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: Request,
    update: UserUpdate,
    current_user: User = Depends(require_permission(Permission.USER_WRITE)),
):
    """Update a user."""
    user_service = get_user_service()
    audit_service = get_audit_service()

    # Get existing user for audit
    existing = await user_service.get_user(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Update
    user = await user_service.update_user(user_id, update)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Audit log
    await audit_service.log(
        action=AuditAction.UPDATE,
        category=AuditCategory.USER_MANAGEMENT,
        entity_type="user",
        entity_id=user.id,
        user=current_user,
        request=request,
        old_value={"name": existing.name, "role": existing.role, "is_active": existing.is_active},
        new_value=update.model_dump(exclude_none=True),
        change_summary=f"Updated user {user.email}",
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        permissions=[p.value if hasattr(p, 'value') else p for p in user.get_all_permissions()],
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Deactivate a user (soft delete)."""
    user_service = get_user_service()
    audit_service = get_audit_service()

    # Cannot delete yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    # Get user for audit
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Audit log
    await audit_service.log(
        action=AuditAction.DELETE,
        category=AuditCategory.USER_MANAGEMENT,
        entity_type="user",
        entity_id=user_id,
        user=current_user,
        request=request,
        old_value={"email": user.email, "name": user.name, "is_active": True},
        new_value={"is_active": False},
        change_summary=f"Deactivated user {user.email}",
    )

    return {"message": f"User {user_id} deactivated"}


@router.get("/roles/list")
async def list_roles(
    current_user: User = Depends(require_permission(Permission.USER_READ)),
):
    """Get available roles and their permissions."""
    return {
        "roles": [
            {
                "role": role.value,
                "permissions": [p.value for p in permissions],
            }
            for role, permissions in ROLE_PERMISSIONS.items()
        ]
    }


@router.get("/permissions/list")
async def list_permissions(
    current_user: User = Depends(require_permission(Permission.USER_READ)),
):
    """Get all available permissions."""
    return {
        "permissions": [p.value for p in Permission]
    }
