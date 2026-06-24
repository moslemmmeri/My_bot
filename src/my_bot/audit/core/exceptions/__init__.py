# my_bot_project/src/my_bot/core/exceptions/__init__.py
"""
ماژول استثناهای سفارشی (Custom Exceptions).

این ماژول شامل سلسله‌مراتب استثناهای سفارشی پروژه است که برای مدیریت
خطاها در لایه‌های مختلف به‌کار می‌روند. تمام استثناها از کلاس پایه `MyBotError`
ارث‌بری می‌کنند و بر اساس نوع خطا دسته‌بندی شده‌اند.
"""

# کلاس پایه استثناها
from my_bot.core.exceptions.base import MyBotError

# استثناهای مربوط به پیکربندی
from my_bot.core.exceptions.config_errors import ConfigurationError

# استثناهای مربوط به دیتابیس
from my_bot.core.exceptions.db_errors import DatabaseError

# استثناهای مربوط به کش
from my_bot.core.exceptions.cache_errors import CacheError

# استثناهای مربوط به اعتبارسنجی
from my_bot.core.exceptions.validation_errors import ValidationError

# استثناهای مربوط به دسترسی و مجوزها
from my_bot.core.exceptions.permission_errors import PermissionDeniedError

# استثناهای مربوط به محدودیت نرخ درخواست
from my_bot.core.exceptions.rate_limit_errors import RateLimitExceededError

# استثناهای مربوط به پردازش فرم
from my_bot.core.exceptions.form_errors import FormProcessingError

# استثناهای مربوط به ارسال گروهی
from my_bot.core.exceptions.broadcast_errors import BroadcastError

# استثناهای مربوط به فیچر فلاگ
from my_bot.core.exceptions.feature_errors import FeatureDisabledError

# استثناهای مربوط به عدم پیدا شدن مورد درخواستی
from my_bot.core.exceptions.not_found_errors import NotFoundError


__all__ = [
    "MyBotError",
    "ConfigurationError",
    "DatabaseError",
    "CacheError",
    "ValidationError",
    "PermissionDeniedError",
    "RateLimitExceededError",
    "FormProcessingError",
    "BroadcastError",
    "FeatureDisabledError",
    "NotFoundError",
]