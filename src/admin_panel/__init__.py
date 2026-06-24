# my_bot_project/src/admin_panel/core/__init__.py
"""
ماژول Core پنل مدیریت (Admin Panel Core).

این ماژول شامل اجزای اصلی پنل مدیریت است که برای مدیریت دسترسی‌ها،
نقش‌های کاربری و تنظیمات مرکزی استفاده می‌شود.

اجزای اصلی:
- Permissions: مدیریت دسترسی‌ها و نقش‌های کاربری (permission_checker, role_definitions)
- AdminConfig: پیکربندی مرکزی پنل مدیریت
"""

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.core.permissions.role_definitions import RoleDefinitions, AdminRole
from admin_panel.core.admin_config import AdminConfig

__all__ = [
    "PermissionChecker",
    "RoleDefinitions",
    "AdminRole",
    "AdminConfig",
]