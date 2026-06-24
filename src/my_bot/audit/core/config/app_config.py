# my_bot_project/src/my_bot/core/config/app_config.py
"""
پیکربندی اصلی اپلیکیشن (AppConfig).

این کلاس شامل تنظیمات مربوط به ربات تلگرام، ادمین‌ها و سایر پارامترهای عمومی است.
همه مقادیر از متغیرهای محیطی (Environment Variables) بارگذاری می‌شوند.
"""

import os
from dataclasses import dataclass
from typing import List, Optional

from my_bot.core.exceptions.config_errors import ConfigurationError


@dataclass(frozen=True)
class AppConfig:
    """
    پیکربندی اصلی برنامه.

    Attributes:
        bot_token: توکن ربات تلگرام (اجباری)
        admin_ids: لیست شناسه‌های عددی ادمین‌ها (اجباری)
        webhook_url: آدرس وب‌هوک (اختیاری، در صورت استفاده از Webhook)
        webhook_port: پورت سرویس وب‌هوک (پیش‌فرض ۸۴۴۳)
        enable_webhook: فعال‌سازی وب‌هوک به‌جای Long Polling (پیش‌فرض False)
        default_language: زبان پیش‌فرض (پیش‌فرض 'fa')
        timezone: منطقه زمانی (پیش‌فرض 'Asia/Tehran')
    """

    bot_token: str
    admin_ids: List[int]
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    enable_webhook: bool = False
    default_language: str = "fa"
    timezone: str = "Asia/Tehran"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        بارگذاری پیکربندی از متغیرهای محیطی.

        Raises:
            ConfigurationError: در صورت عدم وجود توکن یا لیست ادمین‌ها.
        """
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ConfigurationError("BOT_TOKEN is required but not set in environment.")

        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            raise ConfigurationError("ADMIN_IDS is required but not set in environment.")

        try:
            admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        except ValueError as e:
            raise ConfigurationError(f"ADMIN_IDS must be comma-separated integers: {e}")

        if not admin_ids:
            raise ConfigurationError("ADMIN_IDS must contain at least one valid integer.")

        return cls(
            bot_token=bot_token,
            admin_ids=admin_ids,
            webhook_url=os.getenv("WEBHOOK_URL"),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8443")),
            enable_webhook=os.getenv("ENABLE_WEBHOOK", "false").lower() in ("true", "1", "yes"),
            default_language=os.getenv("DEFAULT_LANGUAGE", "fa"),
            timezone=os.getenv("TIMEZONE", "Asia/Tehran"),
        )

    def is_admin(self, user_id: int) -> bool:
        """بررسی اینکه آیا کاربر با شناسه داده شده در لیست ادمین‌ها وجود دارد."""
        return user_id in self.admin_ids