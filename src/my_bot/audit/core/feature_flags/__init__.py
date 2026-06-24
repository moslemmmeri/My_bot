# my_bot_project/src/my_bot/core/feature_flags/__init__.py
"""
ماژول مدیریت Feature Flags (ویژگی‌های فعال/غیرفعال).

این ماژول امکانات مدیریت ویژگی‌های نرم‌افزاری را به‌صورت پویا فراهم می‌کند.
با استفاده از Feature Flags می‌توان ویژگی‌های مختلف سیستم را بدون نیاز
به تغییر کد یا استقرار مجدد، فعال یا غیرفعال کرد.

امکانات اصلی:
- مدیریت وضعیت ویژگی‌ها (فعال/غیرفعال)
- ذخیره‌سازی در دیتابیس و کش (Redis + Local Fallback)
- اعتبارسنجی وابستگی‌های بین ویژگی‌ها
- بررسی دسترسی کاربران به ویژگی‌ها
- پشتیبانی از تاریخ انقضا و محدودیت‌های استفاده

اجزای اصلی:
- FlagManager: مدیریت مرکزی ویژگی‌ها با کش و ذخیره‌سازی
- FlagRepository: ذخیره‌سازی و بازیابی وضعیت ویژگی‌ها در دیتابیس
- FlagCache: کش کردن وضعیت ویژگی‌ها برای افزایش سرعت
"""

from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.core.feature_flags.flag_repository import FlagRepository
from my_bot.core.feature_flags.flag_cache import FlagCache

__all__ = [
    "FeatureFlagManager",
    "FlagRepository",
    "FlagCache",
]