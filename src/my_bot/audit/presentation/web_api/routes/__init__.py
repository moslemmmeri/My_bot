# my_bot_project/src/my_bot/presentation/web_api/routes/__init__.py
"""
ماژول مسیرهای وب API (Web API Routes).

این ماژول شامل مسیرهای مختلف وب‌سرویس است که برای وب‌هوک،
بررسی سلامت و متریک‌ها استفاده می‌شوند.

مسیرهای موجود:
- WebhookRouter: مسیر وب‌هوک برای دریافت رویدادهای تلگرام
- HealthRouter: مسیرهای بررسی سلامت (health, ready, live)
- MetricsRouter: مسیر متریک‌ها برای مانیتورینگ
"""

from my_bot.presentation.web_api.routes.webhook import WebhookRouter
from my_bot.presentation.web_api.routes.health import HealthRouter
from my_bot.presentation.web_api.routes.metrics import MetricsRouter

__all__ = [
    "WebhookRouter",
    "HealthRouter",
    "MetricsRouter",
]