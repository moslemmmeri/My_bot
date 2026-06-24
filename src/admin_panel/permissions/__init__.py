# my_bot_project/src/admin_panel/core/permissions/__init__.py
"""
ماژول دسترسی‌های پنل مدیریت (Admin Panel Permissions).

این ماژول شامل ابزارهای مدیریت دسترسی‌ها و نقش‌های کاربری در پنل مدیریت است:
- PermissionChecker: بررسی دسترسی کاربران به بخش‌های مختلف
- RoleDefinitions: تعاریف نقش‌ها و مجوزهای آنها
- AdminRole: نقش‌های قابل استفاده در پنل مدیریت
"""

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.core.permissions.role_definitions import RoleDefinitions, AdminRole

__all__ = [
    "PermissionChecker",
    "RoleDefinitions",
    "AdminRole",
]