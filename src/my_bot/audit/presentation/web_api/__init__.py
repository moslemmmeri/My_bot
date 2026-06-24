# my_bot_project/src/my_bot/presentation/web_api/__init__.py
"""
ماژول Web API (رابط برنامه‌نویسی وب).

این ماژول شامل سرویس‌های HTTP برای ارتباط با سیستم از طریق وب است:
- WebApp: برنامه اصلی وب (FastAPI)
- WebhookRouter: مسیریابی وب‌هوک
- HealthRouter: بررسی سلامت سرویس
- MetricsRouter: متریک‌های سیستم
"""

from my_bot.presentation.web_api.web_app import WebApp
from my_bot.presentation.web_api.routes.webhook import WebhookRouter
from my_bot.presentation.web_api.routes.health import HealthRouter
from my_bot.presentation.web_api.routes.metrics import MetricsRouter

__all__ = [
    "WebApp",
    "WebhookRouter",
    "HealthRouter",
    "MetricsRouter",
]