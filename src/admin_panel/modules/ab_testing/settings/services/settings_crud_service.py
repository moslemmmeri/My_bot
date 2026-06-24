# src/admin_panel/modules/settings/services/settings_crud_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.setting_repository import SettingRepository
from my_bot.domain.entities.setting import Setting

logger = get_logger(__name__)


class SettingsCRUDService:
    """Service for CRUD operations on settings."""

    def __init__(self, setting_repo: SettingRepository) -> None:
        self.setting_repo = setting_repo

    async def list_settings_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings for a specific category."""
        try:
            settings = await self.setting_repo.find_by_category(category)
            if not settings:
                return {}
            return {setting.key: setting.value for setting in settings}
        except Exception as e:
            logger.error(f"Error listing settings by category {category}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve settings.") from e

    async def get_setting(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        """Get a single setting by category and key."""
        try:
            setting = await self.setting_repo.find_by_category_and_key(category, key)
            if not setting:
                return None
            return self._to_dict(setting)
        except Exception as e:
            logger.error(f"Error getting setting {category}:{key}: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve setting.") from e

    async def update_setting(
        self,
        category: str,
        key: str,
        value: Any,
        updated_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update an existing setting or create if not exists."""
        try:
            setting = await self.setting_repo.find_by_category_and_key(category, key)
            if setting:
                setting.value = value
                setting.updated_by = updated_by
                setting.updated_at = datetime.now()
            else:
                # Create new setting
                setting = Setting(
                    category=category,
                    key=key,
                    value=value,
                    created_by=updated_by,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            saved = await self.setting_repo.save(setting)
            logger.info(f"Setting {category}:{key} updated by {updated_by}")
            return self._to_dict(saved)
        except Exception as e:
            logger.error(f"Error updating setting {category}:{key}: {e}", exc_info=True)
            raise DatabaseError("Failed to update setting.") from e

    async def reset_setting(
        self,
        category: str,
        key: str,
        reset_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Reset a setting to its default value."""
        try:
            setting = await self.setting_repo.find_by_category_and_key(category, key)
            if not setting:
                raise NotFoundError(f"Setting {category}:{key} not found")

            # Reset to default value (could be stored in default_value field)
            # For now, we'll use a predefined default mapping
            default_value = self._get_default_value(category, key)
            setting.value = default_value
            setting.updated_by = reset_by
            setting.updated_at = datetime.now()
            saved = await self.setting_repo.save(setting)
            logger.info(f"Setting {category}:{key} reset to default by {reset_by}")
            return self._to_dict(saved)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error resetting setting {category}:{key}: {e}", exc_info=True)
            raise DatabaseError("Failed to reset setting.") from e

    def _get_default_value(self, category: str, key: str) -> Any:
        """Get default value for a setting."""
        # This could be loaded from a config file or constants
        defaults = {
            "general": {
                "site_name": "My Bot",
                "site_description": "Telegram Bot",
            },
            "security": {
                "max_login_attempts": 5,
                "session_timeout": 3600,
            },
            "payment": {
                "default_currency": "IRR",
                "min_payment": 1000,
            },
            "notifications": {
                "enable_email": True,
                "enable_sms": False,
            },
        }
        return defaults.get(category, {}).get(key, None)

    @staticmethod
    def _to_dict(setting: Setting) -> Dict[str, Any]:
        """Convert Setting entity to dict."""
        return {
            "id": setting.id,
            "category": setting.category,
            "key": setting.key,
            "value": setting.value,
            "description": getattr(setting, "description", ""),
            "type": getattr(setting, "type", "string"),
            "created_by": setting.created_by,
            "updated_by": getattr(setting, "updated_by", None),
            "created_at": setting.created_at.isoformat() if setting.created_at else None,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
        }