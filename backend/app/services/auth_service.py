"""
Authentication and User Account Service.

Module: Core
See: service_contracts.md → AuthService
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_service
from app.core.enums import AuditAction, UserRole
from app.core.exceptions import (
    AuthenticationError,
    BusinessValidationError,
    DuplicateError,
    NotFoundError,
)
from app.core.pagination import PaginatedResult, paginate
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class AuthService:
    """Handles authentication workflows and user account lifecycle."""

    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        ip_address: str | None = None,
    ) -> tuple[str, User]:
        """
        Validate credentials, record login event, and generate access token.

        Raises:
            AuthenticationError: On invalid credentials or disabled account.
        """
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        user.last_login = datetime.now(UTC)

        await audit_service.log(
            db,
            user_id=user.id,
            action=AuditAction.LOGIN,
            entity_type="User",
            entity_id=user.id,
            ip_address=ip_address,
        )

        token = create_access_token(
            {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
            }
        )
        return token, user

    async def change_password(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Verify existing password and set new password.

        Raises:
            NotFoundError: If user doesn't exist.
            AuthenticationError: If current password is wrong.
            BusinessValidationError: If new password does not meet requirements.
        """
        user = await self.get_user_by_id(db, user_id)

        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        if len(new_password) < 8:
            raise BusinessValidationError("New password must be at least 8 characters long")

        user.hashed_password = hash_password(new_password)

        await audit_service.log(
            db,
            user_id=user_id,
            action=AuditAction.CONFIG_CHANGE,
            entity_type="User",
            entity_id=user_id,
            old_values={"password_changed": False},
            new_values={"password_changed": True},
            ip_address=ip_address,
        )

    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> User:
        """Retrieve user by UUID or raise NotFoundError."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")
        return user

    async def create_user(
        self,
        db: AsyncSession,
        data: UserCreate,
        creator_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        """Create a new user account with uniqueness checks and audit log."""
        # Check duplicate username
        stmt_u = select(User).where(User.username == data.username)
        res_u = await db.execute(stmt_u)
        if res_u.scalar_one_or_none():
            raise DuplicateError("username", data.username)

        # Check duplicate email
        stmt_e = select(User).where(User.email == data.email)
        res_e = await db.execute(stmt_e)
        if res_e.scalar_one_or_none():
            raise DuplicateError("email", data.email)

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        await audit_service.log(
            db,
            user_id=creator_id,
            action=AuditAction.CREATE,
            entity_type="User",
            entity_id=user.id,
            new_values={
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
            },
            ip_address=ip_address,
        )
        return user

    async def list_users(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 25,
    ) -> PaginatedResult:
        """List users with pagination."""
        query = select(User).order_by(User.created_at.desc())
        return await paginate(db, query, page=page, per_page=per_page)

    async def _count_active_admins(self, db: AsyncSession) -> int:
        """Count currently active administrators."""
        stmt = select(func.count(User.id)).where(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
        )
        result = await db.execute(stmt)
        return int(result.scalar_one())

    async def update_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        data: UserUpdate,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        """
        Update user properties (email, full_name, role, is_active).

        Guards:
            - Prevents administrators from demoting or deactivating their own account
            - Prevents any update that leaves zero active administrators
            - Preserves legitimate unrelated edits (email, full_name, setting role to ADMIN)
        """
        user = await self.get_user_by_id(db, user_id)
        old_vals = {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        }

        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        is_admin = user_role_str == UserRole.ADMIN.value

        # Check effective changes
        is_effective_deactivation = data.is_active is False and user.is_active is True
        target_role_str = (
            data.role.value if hasattr(data.role, "value") else str(data.role)
            if data.role is not None
            else None
        )
        is_effective_demotion = (
            is_admin and target_role_str is not None and target_role_str != UserRole.ADMIN.value
        )

        # 1. Prevent self-demotion and self-deactivation
        if user_id == actor_id:
            if is_effective_deactivation:
                raise BusinessValidationError("Administrators cannot deactivate their own account")
            if is_effective_demotion:
                raise BusinessValidationError("Administrators cannot demote their own account")

        # 2. Prevent leaving zero active administrators
        if is_admin and user.is_active and (is_effective_deactivation or is_effective_demotion):
            active_admin_count = await self._count_active_admins(db)
            if active_admin_count <= 1:
                action_desc = "deactivate" if is_effective_deactivation else "demote"
                raise BusinessValidationError(
                    f"Cannot {action_desc} the sole remaining active administrator"
                )

        if data.email is not None:
            # Check unique if changed
            if data.email != user.email:
                stmt = select(User).where(User.email == data.email)
                res = await db.execute(stmt)
                if res.scalar_one_or_none():
                    raise DuplicateError("email", data.email)
            user.email = data.email

        if data.full_name is not None:
            user.full_name = data.full_name

        if data.role is not None:
            user.role = data.role

        if data.is_active is not None:
            user.is_active = data.is_active

        new_vals = {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        }

        await audit_service.log(
            db,
            user_id=actor_id,
            action=AuditAction.UPDATE,
            entity_type="User",
            entity_id=user.id,
            old_values=old_vals,
            new_values=new_vals,
            ip_address=ip_address,
        )
        return user

    async def deactivate_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        """
        Deactivate a user account (never physically delete).

        Guards:
            - Prevents administrators from deactivating their own account
            - Prevents deactivating the sole remaining active administrator
        """
        user = await self.get_user_by_id(db, user_id)
        if not user.is_active:
            return user

        # 1. Prevent self-deactivation
        if user_id == actor_id:
            raise BusinessValidationError("Administrators cannot deactivate their own account")

        # 2. Prevent deactivating the sole remaining active administrator
        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        if user_role_str == UserRole.ADMIN.value:
            active_admin_count = await self._count_active_admins(db)
            if active_admin_count <= 1:
                raise BusinessValidationError(
                    "Cannot deactivate the sole remaining active administrator"
                )

        user.is_active = False

        await audit_service.log(
            db,
            user_id=actor_id,
            action=AuditAction.DEACTIVATE,
            entity_type="User",
            entity_id=user.id,
            old_values={"is_active": True},
            new_values={"is_active": False},
            ip_address=ip_address,
        )
        return user


auth_service = AuthService()
