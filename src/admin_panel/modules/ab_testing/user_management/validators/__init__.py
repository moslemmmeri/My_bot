# my_bot_project/src/admin_panel/modules/user_management/validators/__init__.py
"""
ماژول اعتبارسنجی مدیریت کاربران (User Management Validators).

این ماژول شامل کلاس‌های اعتبارسنجی داده‌های مربوط به کاربران است:
- UserValidator: اعتبارسنجی اطلاعات کاربران (نام، ایمیل، تلفن، نقش و ...)
"""

from admin_panel.modules.user_management.validators.user_validator import UserValidator

__all__ = [
    "UserValidator",
]