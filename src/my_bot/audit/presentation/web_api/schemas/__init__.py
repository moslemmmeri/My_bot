# my_bot_project/src/my_bot/presentation/web_api/schemas/__init__.py
"""
ماژول Schemaهای وب API (Web API Schemas).

این ماژول شامل Schemaهای Pydantic برای اعتبارسنجی و سریال‌سازی
داده‌های ورودی و خروجی وب‌سرویس است.

Schemaهای موجود:
- WebhookSchemas: Schemaهای مربوط به وب‌هوک تلگرام
- HealthSchemas: Schemaهای مربوط به بررسی سلامت
- MetricsSchemas: Schemaهای مربوط به متریک‌ها
"""

from my_bot.presentation.web_api.schemas.webhook_schemas import (
    WebhookRequestSchema,
    WebhookResponseSchema,
    WebhookStatusSchema,
)

__all__ = [
    "WebhookRequestSchema",
    "WebhookResponseSchema",
    "WebhookStatusSchema",
]