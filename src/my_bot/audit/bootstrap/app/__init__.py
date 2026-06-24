# my_bot_project/src/my_bot/bootstrap/app/__init__.py
"""
ماژول راه‌اندازی برنامه (Application Bootstrap).

این ماژول شامل ابزارهای راه‌اندازی، بارگذاری و مدیریت چرخه‌ی حیات برنامه است:
- AppLoader: بارگذاری و راه‌اندازی کامل برنامه
- StartupHooks: اجرای عملیات‌های اولیه هنگام شروع برنامه
- ShutdownHooks: اجرای عملیات‌های پاکسازی هنگام خاموش‌سازی برنامه
"""

from my_bot.bootstrap.app.app_loader import AppLoader
from my_bot.bootstrap.app.startup_hooks import StartupHooks
from my_bot.bootstrap.app.shutdown_hooks import ShutdownHooks

__all__ = [
    "AppLoader",
    "StartupHooks",
    "ShutdownHooks",
]