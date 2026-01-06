"""User management service."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from passlib.context import CryptContext

from ..config import settings
from ..models.users import User, UserCreate, UserUpdate, UserRole
from .cosmos_service import get_cosmos_client

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service for managing users."""

    COLLECTION = "users"

    # In-memory storage fallback
    _memory_store: List[dict] = []
    _initialized = False

    def __init__(self):
        self.cosmos = get_cosmos_client()

    async def initialize_default_admin(self):
        """Create default admin user if no users exist."""
        if self._initialized:
            return

        users, _ = await self.list_users(limit=1)
        if not users:
            logger.info("Creating default admin user")
            await self.create_user(UserCreate(
                email=settings.DEFAULT_ADMIN_EMAIL,
                name=settings.DEFAULT_ADMIN_NAME,
                password="admin123!",  # Should be changed immediately
                role=UserRole.ADMIN,
            ))

        self._initialized = True

    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if email already exists
        existing = await self.get_user_by_email(user_create.email)
        if existing:
            raise ValueError(f"User with email {user_create.email} already exists")

        user = User(
            id=f"USR-{uuid4().hex[:8].upper()}",
            email=user_create.email,
            name=user_create.name,
            role=user_create.role,
            password_hash=pwd_context.hash(user_create.password),
            azure_ad_oid=user_create.azure_ad_oid,
            additional_permissions=user_create.additional_permissions,
        )

        user_dict = user.model_dump()
        user_dict["created_at"] = user_dict["created_at"].isoformat()
        user_dict["updated_at"] = user_dict["updated_at"].isoformat()

        if settings.cosmos_db_configured:
            await self.cosmos.create_document(
                collection=self.COLLECTION,
                document=user_dict,
                partition_key=user.role,
            )
        else:
            self._memory_store.append(user_dict)

        logger.info(f"Created user {user.id} ({user.email})")
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": user_id}],
            )
            if results:
                return User(**results[0])
        else:
            for doc in self._memory_store:
                if doc.get("id") == user_id:
                    return User(**doc)

        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query="SELECT * FROM c WHERE c.email = @email",
                parameters=[{"name": "@email", "value": email}],
            )
            if results:
                return User(**results[0])
        else:
            for doc in self._memory_store:
                if doc.get("email") == email:
                    return User(**doc)

        return None

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None

        if not user.password_hash:
            return None

        if not pwd_context.verify(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        # Update last login
        await self.update_last_login(user.id)

        return user

    async def update_user(self, user_id: str, update: UserUpdate) -> Optional[User]:
        """Update user."""
        user = await self.get_user(user_id)
        if not user:
            return None

        update_dict = update.model_dump(exclude_none=True)

        # Handle password update
        if "password" in update_dict:
            update_dict["password_hash"] = pwd_context.hash(update_dict.pop("password"))

        # Apply updates
        user_dict = user.model_dump()
        for key, value in update_dict.items():
            user_dict[key] = value

        user_dict["updated_at"] = datetime.utcnow().isoformat()

        # Handle datetime serialization
        if isinstance(user_dict.get("created_at"), datetime):
            user_dict["created_at"] = user_dict["created_at"].isoformat()
        if isinstance(user_dict.get("last_login"), datetime):
            user_dict["last_login"] = user_dict["last_login"].isoformat()

        if settings.cosmos_db_configured:
            await self.cosmos.update_document(
                collection=self.COLLECTION,
                document_id=user_id,
                document=user_dict,
                partition_key=user_dict.get("role"),
            )
        else:
            for i, doc in enumerate(self._memory_store):
                if doc.get("id") == user_id:
                    self._memory_store[i] = user_dict
                    break

        logger.info(f"Updated user {user_id}")
        return User(**user_dict)

    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        user = await self.get_user(user_id)
        if user:
            user_dict = user.model_dump()
            user_dict["last_login"] = datetime.utcnow().isoformat()

            if isinstance(user_dict.get("created_at"), datetime):
                user_dict["created_at"] = user_dict["created_at"].isoformat()
            if isinstance(user_dict.get("updated_at"), datetime):
                user_dict["updated_at"] = user_dict["updated_at"].isoformat()

            if settings.cosmos_db_configured:
                await self.cosmos.update_document(
                    collection=self.COLLECTION,
                    document_id=user_id,
                    document=user_dict,
                    partition_key=user_dict.get("role"),
                )
            else:
                for i, doc in enumerate(self._memory_store):
                    if doc.get("id") == user_id:
                        self._memory_store[i] = user_dict
                        break

    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active=False)."""
        user = await self.get_user(user_id)
        if not user:
            return False

        await self.update_user(user_id, UserUpdate(is_active=False))
        logger.info(f"Deactivated user {user_id}")
        return True

    async def list_users(
        self,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[User], int]:
        """List users with optional filters."""
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []

        if role:
            query += " AND c.role = @role"
            parameters.append({"name": "@role", "value": role.value})

        if is_active is not None:
            query += " AND c.is_active = @is_active"
            parameters.append({"name": "@is_active", "value": is_active})

        query += " ORDER BY c.created_at DESC"

        if settings.cosmos_db_configured:
            results = await self.cosmos.query_documents(
                collection=self.COLLECTION,
                query=query,
                parameters=parameters,
            )
        else:
            results = self._memory_store.copy()
            if role:
                results = [r for r in results if r.get("role") == role.value]
            if is_active is not None:
                results = [r for r in results if r.get("is_active") == is_active]
            results = sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)

        total = len(results)
        paginated = results[offset:offset + limit]

        users = [User(**r) for r in paginated]
        return users, total

    async def get_approvers(self) -> List[User]:
        """Get all users who can approve requests."""
        users, _ = await self.list_users(is_active=True)
        approvers = [
            u for u in users
            if u.role in [UserRole.ADMIN.value, UserRole.APPROVER.value, "admin", "approver"]
        ]
        return approvers


# Singleton
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get user service singleton."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
