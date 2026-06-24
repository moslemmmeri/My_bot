# src/admin_panel/core/permissions/role_definitions.py
"""
Role Definitions for Admin Panel.

This module defines all available roles and their permissions
for the admin panel. It provides utilities for checking role
permissions and role hierarchy.
"""

from typing import Dict, List, Set, Optional
from enum import Enum


class Role(str, Enum):
    """Enumeration of available admin roles."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"

    @classmethod
    def get_all_roles(cls) -> List[str]:
        """Get list of all role names."""
        return [role.value for role in cls]

    @classmethod
    def get_role_hierarchy(cls) -> Dict[str, int]:
        """Get role hierarchy levels (higher number = higher access)."""
        return {
            cls.SUPER_ADMIN.value: 100,
            cls.ADMIN.value: 80,
            cls.MODERATOR.value: 60,
            cls.SUPPORT.value: 40,
        }

    @classmethod
    def is_higher_or_equal(cls, role1: str, role2: str) -> bool:
        """Check if role1 is higher than or equal to role2."""
        hierarchy = cls.get_role_hierarchy()
        return hierarchy.get(role1, 0) >= hierarchy.get(role2, 0)


# Permission definitions
class Permission:
    """
    Permission constants for admin panel operations.
    """

    # User management permissions
    USERS_VIEW = "users.view"
    USERS_EDIT = "users.edit"
    USERS_DELETE = "users.delete"
    USERS_CREATE = "users.create"
    USERS_EXPORT = "users.export"

    # Order management permissions
    ORDERS_VIEW = "orders.view"
    ORDERS_EDIT = "orders.edit"
    ORDERS_DELETE = "orders.delete"
    ORDERS_EXPORT = "orders.export"

    # Analytics permissions
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"

    # Content management permissions
    CONTENT_VIEW = "content.view"
    CONTENT_CREATE = "content.create"
    CONTENT_EDIT = "content.edit"
    CONTENT_DELETE = "content.delete"

    # Broadcast permissions
    BROADCAST_VIEW = "broadcast.view"
    BROADCAST_CREATE = "broadcast.create"
    BROADCAST_SEND = "broadcast.send"
    BROADCAST_SCHEDULE = "broadcast.schedule"

    # Admin management permissions
    ADMIN_VIEW = "admin.view"
    ADMIN_CREATE = "admin.create"
    ADMIN_EDIT = "admin.edit"
    ADMIN_DELETE = "admin.delete"

    # Backup permissions
    BACKUP_CREATE = "backup.create"
    BACKUP_RESTORE = "backup.restore"
    BACKUP_DELETE = "backup.delete"

    # Settings permissions
    SETTINGS_VIEW = "settings.view"
    SETTINGS_EDIT = "settings.edit"

    # Logs permissions
    LOGS_VIEW = "logs.view"
    LOGS_CLEAR = "logs.clear"

    # Error logs permissions
    ERRORS_VIEW = "errors.view"
    ERRORS_CLEAR = "errors.clear"

    # System health permissions
    HEALTH_VIEW = "health.view"

    # Ticket permissions
    TICKETS_VIEW = "tickets.view"
    TICKETS_REPLY = "tickets.reply"
    TICKETS_CLOSE = "tickets.close"
    TICKETS_ASSIGN = "tickets.assign"

    # Coupon permissions
    COUPONS_VIEW = "coupons.view"
    COUPONS_CREATE = "coupons.create"
    COUPONS_EDIT = "coupons.edit"
    COUPONS_DELETE = "coupons.delete"
    COUPONS_APPLY = "coupons.apply"

    # Feature management permissions
    FEATURES_VIEW = "features.view"
    FEATURES_TOGGLE = "features.toggle"
    FEATURES_CREATE = "features.create"
    FEATURES_DELETE = "features.delete"

    # A/B Testing permissions
    ABTEST_VIEW = "abtest.view"
    ABTEST_CREATE = "abtest.create"
    ABTEST_EDIT = "abtest.edit"
    ABTEST_DELETE = "abtest.delete"
    ABTEST_START = "abtest.start"
    ABTEST_STOP = "abtest.stop"

    # Behavior analytics permissions
    BEHAVIOR_VIEW = "behavior.view"
    BEHAVIOR_EXPORT = "behavior.export"

    # Feedback permissions
    FEEDBACK_VIEW = "feedback.view"
    FEEDBACK_REPLY = "feedback.reply"
    FEEDBACK_DELETE = "feedback.delete"


# Role permission definitions
_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    # Super Admin: All permissions
    Role.SUPER_ADMIN.value: set(Permission.__dict__.values()) - set(dir(Permission)) - {"__module__", "__dict__", "__weakref__", "__doc__"},

    # Admin: Most permissions except super admin specific ones
    Role.ADMIN.value: {
        Permission.USERS_VIEW,
        Permission.USERS_EDIT,
        Permission.USERS_CREATE,
        Permission.USERS_EXPORT,
        Permission.ORDERS_VIEW,
        Permission.ORDERS_EDIT,
        Permission.ORDERS_EXPORT,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_DELETE,
        Permission.BROADCAST_VIEW,
        Permission.BROADCAST_CREATE,
        Permission.BROADCAST_SEND,
        Permission.BROADCAST_SCHEDULE,
        Permission.BACKUP_CREATE,
        Permission.BACKUP_RESTORE,
        Permission.BACKUP_DELETE,
        Permission.SETTINGS_VIEW,
        Permission.SETTINGS_EDIT,
        Permission.LOGS_VIEW,
        Permission.ERRORS_VIEW,
        Permission.HEALTH_VIEW,
        Permission.TICKETS_VIEW,
        Permission.TICKETS_REPLY,
        Permission.TICKETS_CLOSE,
        Permission.TICKETS_ASSIGN,
        Permission.COUPONS_VIEW,
        Permission.COUPONS_CREATE,
        Permission.COUPONS_EDIT,
        Permission.COUPONS_DELETE,
        Permission.COUPONS_APPLY,
        Permission.FEATURES_VIEW,
        Permission.FEATURES_TOGGLE,
        Permission.FEATURES_CREATE,
        Permission.FEATURES_DELETE,
        Permission.ABTEST_VIEW,
        Permission.ABTEST_CREATE,
        Permission.ABTEST_EDIT,
        Permission.ABTEST_START,
        Permission.ABTEST_STOP,
        Permission.BEHAVIOR_VIEW,
        Permission.BEHAVIOR_EXPORT,
        Permission.FEEDBACK_VIEW,
        Permission.FEEDBACK_REPLY,
        Permission.FEEDBACK_DELETE,
    },

    # Moderator: Limited permissions
    Role.MODERATOR.value: {
        Permission.USERS_VIEW,
        Permission.ORDERS_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.BROADCAST_VIEW,
        Permission.TICKETS_VIEW,
        Permission.TICKETS_REPLY,
        Permission.TICKETS_CLOSE,
        Permission.TICKETS_ASSIGN,
        Permission.COUPONS_VIEW,
        Permission.COUPONS_APPLY,
        Permission.FEATURES_VIEW,
        Permission.ABTEST_VIEW,
        Permission.BEHAVIOR_VIEW,
        Permission.FEEDBACK_VIEW,
        Permission.FEEDBACK_REPLY,
    },

    # Support: Limited to support-related permissions
    Role.SUPPORT.value: {
        Permission.USERS_VIEW,
        Permission.ORDERS_VIEW,
        Permission.CONTENT_VIEW,
        Permission.TICKETS_VIEW,
        Permission.TICKETS_REPLY,
        Permission.TICKETS_CLOSE,
        Permission.TICKETS_ASSIGN,
        Permission.COUPONS_VIEW,
        Permission.COUPONS_APPLY,
        Permission.FEEDBACK_VIEW,
        Permission.FEEDBACK_REPLY,
    },
}


def get_role_permissions(role: str) -> Set[str]:
    """
    Get permissions for a specific role.

    Args:
        role: Role name (e.g., 'admin', 'super_admin')

    Returns:
        Set[str]: Set of permission strings for the role
    """
    return _ROLE_PERMISSIONS.get(role, set())


def get_permission_list(role: str) -> List[str]:
    """
    Get permissions for a role as a sorted list.

    Args:
        role: Role name

    Returns:
        List[str]: Sorted list of permissions
    """
    return sorted(get_role_permissions(role))


def has_permission(role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: Role name
        permission: Permission to check

    Returns:
        bool: True if role has permission, False otherwise
    """
    return permission in get_role_permissions(role)


def get_role_display_name(role: str) -> str:
    """
    Get display name for a role.

    Args:
        role: Role name

    Returns:
        str: Display name in Persian
    """
    display_names = {
        Role.SUPER_ADMIN.value: "🔱 سوپر ادمین",
        Role.ADMIN.value: "👤 ادمین",
        Role.MODERATOR.value: "🛡️ مدیر",
        Role.SUPPORT.value: "💬 پشتیبان",
    }
    return display_names.get(role, role)


def get_roles_with_permission(permission: str) -> List[str]:
    """
    Get list of roles that have a specific permission.

    Args:
        permission: Permission to check

    Returns:
        List[str]: List of role names
    """
    return [
        role for role in Role.get_all_roles()
        if permission in get_role_permissions(role)
    ]


def get_all_permissions() -> List[str]:
    """
    Get list of all defined permissions.

    Returns:
        List[str]: Sorted list of all permission names
    """
    permissions = set()
    for role in Role.get_all_roles():
        permissions.update(get_role_permissions(role))
    return sorted(permissions)


def is_valid_role(role: str) -> bool:
    """
    Check if a role name is valid.

    Args:
        role: Role name to check

    Returns:
        bool: True if valid, False otherwise
    """
    return role in Role.get_all_roles()


def get_role_hierarchy_level(role: str) -> int:
    """
    Get hierarchy level for a role.

    Args:
        role: Role name

    Returns:
        int: Hierarchy level (higher = more privileged)
    """
    return Role.get_role_hierarchy().get(role, 0)


def can_access_module(role: str, module: str) -> bool:
    """
    Check if a role can access a specific module.

    Args:
        role: Role name
        module: Module name (e.g., 'users', 'orders')

    Returns:
        bool: True if role can access the module
    """
    module_permissions = {
        "users": [Permission.USERS_VIEW],
        "orders": [Permission.ORDERS_VIEW],
        "analytics": [Permission.ANALYTICS_VIEW],
        "content": [Permission.CONTENT_VIEW],
        "broadcast": [Permission.BROADCAST_VIEW],
        "admin_management": [Permission.ADMIN_VIEW],
        "backup": [Permission.BACKUP_CREATE],
        "settings": [Permission.SETTINGS_VIEW],
        "logs": [Permission.LOGS_VIEW],
        "errors": [Permission.ERRORS_VIEW],
        "health": [Permission.HEALTH_VIEW],
        "tickets": [Permission.TICKETS_VIEW],
        "coupons": [Permission.COUPONS_VIEW],
        "features": [Permission.FEATURES_VIEW],
        "abtest": [Permission.ABTEST_VIEW],
        "behavior": [Permission.BEHAVIOR_VIEW],
        "feedback": [Permission.FEEDBACK_VIEW],
    }

    module_perms = module_permissions.get(module, [])
    role_perms = get_role_permissions(role)
    return any(perm in role_perms for perm in module_perms)