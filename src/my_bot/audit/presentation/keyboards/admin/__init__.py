# my_bot_project/src/my_bot/presentation/keyboards/admin/__init__.py
"""
ماژول کیبوردهای پنل مدیریت (Admin Keyboards).

این ماژول شامل کیبوردهای مربوط به پنل مدیریت است:
- admin_keyboards: کیبوردهای اصلی پنل مدیریت (منوی اصلی، ماژول‌ها)
"""

from my_bot.presentation.keyboards.admin.admin_keyboards import (
    get_admin_main_keyboard,
    get_admin_users_keyboard,
    get_admin_orders_keyboard,
    get_admin_analytics_keyboard,
    get_admin_broadcast_keyboard,
    get_admin_content_keyboard,
    get_admin_settings_keyboard,
    get_admin_features_keyboard,
    get_admin_coupons_keyboard,
    get_admin_tickets_keyboard,
    get_admin_backup_keyboard,
    get_admin_health_keyboard,
    get_admin_abtest_keyboard,
    get_admin_logs_keyboard,
    get_admin_errors_keyboard,
)

__all__ = [
    "get_admin_main_keyboard",
    "get_admin_users_keyboard",
    "get_admin_orders_keyboard",
    "get_admin_analytics_keyboard",
    "get_admin_broadcast_keyboard",
    "get_admin_content_keyboard",
    "get_admin_settings_keyboard",
    "get_admin_features_keyboard",
    "get_admin_coupons_keyboard",
    "get_admin_tickets_keyboard",
    "get_admin_backup_keyboard",
    "get_admin_health_keyboard",
    "get_admin_abtest_keyboard",
    "get_admin_logs_keyboard",
    "get_admin_errors_keyboard",
]