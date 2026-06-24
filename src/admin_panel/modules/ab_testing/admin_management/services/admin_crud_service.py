# src/admin_panel/modules/admin_management/services/admin_crud_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.admin_repository import AdminRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.entities.admin import Admin
from my_bot.domain.entities.user import User

logger = get_logger(__name__)


class AdminCRUDService:
    """Service for CRUD operations on admin users."""

    def __init__(
        self,
        admin_repo: AdminRepository,
        user_repo: UserRepository,
    ) -> None:
        self.admin_repo = admin_repo
        self.user_repo = user_repo

    async def list_admins(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of admin users with optional filters.
        Returns dict with 'items' (list of admin dicts) and 'total'.
        """
        try:
            offset = (page - 1) * page_size
            items, total = await self.admin_repo.find_filtered(
                role=role,
                is_active=is_active,
                limit=page_size,
                offset=offset,
            )
            return {
                "items": [self._to_dict(item) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            logger.error(f"Error listing admins: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve admin list.") from e

    async def get_admin(self, admin_id: int) -> Optional[Dict[str, Any]]:
        """Get a single admin by ID."""
        try:
            admin = await self.admin_repo.find_by_id(admin_id)
            if not admin:
                return None
            return self._to_dict(admin)
        except Exception as e:
            logger.error(f"Error getting admin {admin_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve admin.") from e

    async def get_admin_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get admin by user ID."""
        try:
            admin = await self.admin_repo.find_by_user_id(user_id)
            if not admin:
                return None
            return self._to_dict(admin)
        except Exception as e:
            logger.error(f"Error getting admin by user {user_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve admin.") from e

    async def add_admin(
        self,
        user_id: int,
        role: str = "admin",
        added_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add a new admin."""
        try:
            # Validate role
            valid_roles = ["super_admin", "admin", "moderator", "support"]
            if role not in valid_roles:
                raise ValidationError(f"Invalid role: {role}. Valid: {valid_roles}")

            # Check if user exists
            user = await self.user_repo.find_by_telegram_id(user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found")

            # Check if already an admin
            existing = await self.admin_repo.find_by_user_id(user_id)
            if existing:
                raise ValidationError(f"User {user_id} is already an admin")

            # Create admin
            admin = Admin(
                user_id=user_id,
                role=role,
                is_active=True,
                created_by=added_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            saved = await self.admin_repo.save(admin)
            logger.info(f"Admin added: user {user_id} as {role} by {added_by}")
            return self._to_dict(saved)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding admin for user {user_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to add admin.") from e

    async def update_admin(
        self,
        admin_id: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        updated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update an admin."""
        try:
            admin = await self.admin_repo.find_by_id(admin_id)
            if not admin:
                raise NotFoundError(f"Admin {admin_id} not found")

            if role is not None:
                valid_roles = ["super_admin", "admin", "moderator", "support"]
                if role not in valid_roles:
                    raise ValidationError(f"Invalid role: {role}. Valid: {valid_roles}")
                admin.role = role

            if is_active is not None:
                admin.is_active = is_active

            admin.updated_by = updated_by
            admin.updated_at = datetime.now()

            saved = await self.admin_repo.save(admin)
            logger.info(f"Admin {admin_id} updated by {updated_by}")
            return self._to_dict(saved)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating admin {admin_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update admin.") from e

    async def remove_admin(self, admin_id: int, removed_by: Optional[int] = None) -> bool:
        """Remove an admin."""
        try:
            admin = await self.admin_repo.find_by_id(admin_id)
            if not admin:
                raise NotFoundError(f"Admin {admin_id} not found")

            # Check if this is the last super_admin
            if admin.role == "super_admin":
                super_admins = await self.admin_repo.find_by_role("super_admin")
                if len(super_admins) <= 1:
                    raise PermissionDeniedError("Cannot remove the last super_admin")

            await self.admin_repo.delete(admin_id)
            logger.info(f"Admin {admin_id} removed by {removed_by}")
            return True
        except NotFoundError:
            raise
        except PermissionDeniedError:
            raise
        except Exception as e:
            logger.error(f"Error removing admin {admin_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to remove admin.") from e

    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information for adding as admin."""
        try:
            user = await self.user_repo.find_by_telegram_id(user_id)
            if not user:
                return None
            return {
                "id": user.id,
                "user_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
            }
        except Exception as e:
            logger.error(f"Error getting user info {user_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to get user information.") from e

    @staticmethod
    def _to_dict(admin: Admin) -> Dict[str, Any]:
        """Convert Admin entity to dict."""
        return {
            "id": admin.id,
            "user_id": admin.user_id,
            "role": admin.role,
            "is_active": admin.is_active,
            "created_by": admin.created_by,
            "updated_by": getattr(admin, "updated_by", None),
            "created_at": admin.created_at.isoformat() if admin.created_at else None,
            "updated_at": admin.updated_at.isoformat() if admin.updated_at else None,
        }