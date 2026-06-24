# my_bot_project/src/my_bot/bootstrap/__init__.py
"""
ماژول راه‌اندازی (Bootstrap).

این ماژول شامل ابزارهای راه‌اندازی و مقداردهی اولیه برنامه است:
- Container: ظرف DI (Dependency Injection) برای مدیریت وابستگی‌ها
- App: بارگذاری و راه‌اندازی برنامه (App Loader, Startup/Shutdown Hooks)
"""

from my_bot.bootstrap.container.di_container import DIContainer
from my_bot.bootstrap.app.app_loader import AppLoader
from my_bot.bootstrap.app.startup_hooks import StartupHooks
from my_bot.bootstrap.app.shutdown_hooks import ShutdownHooks

__all__ = [
    "DIContainer",
    "AppLoader",
    "StartupHooks",
    "ShutdownHooks",
]