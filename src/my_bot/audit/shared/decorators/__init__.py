# my_bot_project/src/my_bot/shared/decorators/__init__.py
"""
ماژول دکوراتورهای مشترک (Shared Decorators).

این ماژول شامل دکوراتورهای پرکاربرد است که در سراسر پروژه
برای اضافه کردن قابلیت‌های مختلف به توابع و متدها استفاده می‌شوند.

دکوراتورهای موجود:
- retry_backoff: تلاش مجدد با Backoff نمایی
- rate_limit: محدودیت نرخ درخواست
- feature_flag: بررسی فعال بودن فیچر
- admin_only: محدودیت دسترسی فقط برای ادمین‌ها
- log_execution: ثبت لاگ زمان اجرا و پارامترها
"""

from my_bot.shared.decorators.retry_backoff import retry_backoff
from my_bot.shared.decorators.rate_limit import rate_limit
from my_bot.shared.decorators.feature_flag import feature_flag
from my_bot.shared.decorators.admin_only import admin_only
from my_bot.shared.decorators.log_execution import log_execution

__all__ = [
    "retry_backoff",
    "rate_limit",
    "feature_flag",
    "admin_only",
    "log_execution",
]