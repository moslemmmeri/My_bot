# my_bot_project/src/my_bot/application/services/user/__init__.py
"""
ماژول سرویس‌های کاربر (User Services).

این ماژول شامل سرویس‌های مربوط به مدیریت کاربران در سیستم است:
- UserRegistrationService: ثبت‌نام کاربر جدید
- UserProfileService: مدیریت پروفایل کاربر
- UserLevelUpgradeService: ارتقاء سطح کاربر بر اساس امتیاز
"""

from my_bot.application.services.user.user_registration import UserRegistrationService
from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.application.services.user.user_level_upgrade import UserLevelUpgradeService

__all__ = [
    "UserRegistrationService",
    "UserProfileService",
    "UserLevelUpgradeService",
]