# my_bot_project/src/my_bot/core/logger/__init__.py
"""
ماژول لاگ‌گیری (Logger).

این ماژول شامل ابزارهای حرفه‌ای برای لاگ‌گیری در پروژه است.
با استفاده از RotatingFileHandler، لاگ‌ها به‌صورت خودکار در فایل‌های
چرخشی ذخیره می‌شوند و امکان تنظیم سطح لاگ، فرمت و سایر پارامترها فراهم است.

امکانات اصلی:
- ایجاد لاگر با نام مشخص
- پشتیبانی از RotatingFileHandler با تنظیم حجم و تعداد فایل‌های پشتیبان
- لاگ‌گیری همزمان در فایل و کنسول
- فرمت‌سازی پیشرفته با قابلیت خروجی JSON
- جداسازی لاگ‌های خطا در فایل مجزا
"""

# Import core components from submodules
from my_bot.core.logger.logger_setup import setup_logger, get_logger
from my_bot.core.logger.logger_factory import LoggerFactory
from my_bot.core.logger.log_formatter import LogFormatter

# تعریف لیست اشیاء قابل export
__all__ = [
    "setup_logger",
    "get_logger",
    "LoggerFactory",
    "LogFormatter",
]