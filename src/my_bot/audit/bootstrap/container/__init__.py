# my_bot_project/src/my_bot/bootstrap/container/__init__.py
"""
ماژول ظرف DI (Dependency Injection Container).

این ماژول شامل اجزای مدیریت وابستگی‌ها در سیستم است:
- DIContainer: ظرف اصلی DI برای ثبت و دریافت سرویس‌ها
- ServiceRegistry: ثبت سرویس‌های لایه کاربرد و زیرساخت
- RepositoryRegistry: ثبت ریپازیتوری‌ها
"""

from my_bot.bootstrap.container.di_container import DIContainer
from my_bot.bootstrap.container.service_registry import ServiceRegistry
from my_bot.bootstrap.container.repository_registry import RepositoryRegistry

__all__ = [
    "DIContainer",
    "ServiceRegistry",
    "RepositoryRegistry",
]