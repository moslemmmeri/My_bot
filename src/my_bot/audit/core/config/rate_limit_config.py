# my_bot_project/src/my_bot/core/config/rate_limit_config.py
"""
پیکربندی محدودیت نرخ درخواست (Rate Limit Config).

این کلاس شامل تنظیمات مربوط به محدودیت نرخ درخواست با الگوریتم Sliding Window است.
پارامترهای این بخش کنترل می‌کنند که هر کاربر در بازه‌ی زمانی مشخص،
چند درخواست می‌تواند به ربات ارسال کند.
"""

import os
from dataclasses import dataclass
from typing import Optional

from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RateLimitConfig:
    """
    پیکربندی محدودیت نرخ درخواست.

    Attributes:
        enabled: فعال بودن یا نبودن محدودیت نرخ (پیش‌فرض True)
        requests_per_window: تعداد درخواست‌های مجاز در هر پنجره (پیش‌فرض ۳۰)
        window_seconds: طول پنجره‌ی زمانی بر حسب ثانیه (پیش‌فرض ۶۰)
        storage_backend: نوع ذخیره‌سازی ('redis' یا 'local') (پیش‌فرض 'local')
        key_prefix: پیشوند کلیدها در ذخیره‌سازی (پیش‌فرض 'rate_limit')
        block_duration_seconds: مدت زمان بلاک شدن کاربر پس از تجاوز از حد (پیش‌فرض ۳۰۰)
        whitelist_ids: لیست شناسه‌های کاربران معاف از محدودیت (اختیاری)
        enable_blocking: فعال‌سازی بلاک کردن کاربران متخلف (پیش‌فرض True)
    """

    enabled: bool = True
    requests_per_window: int = 30
    window_seconds: int = 60
    storage_backend: str = "local"  # 'redis' or 'local'
    key_prefix: str = "rate_limit"
    block_duration_seconds: int = 300
    whitelist_ids: Optional[list[int]] = None
    enable_blocking: bool = True

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """
        بارگذاری پیکربندی محدودیت نرخ از متغیرهای محیطی.

        در صورت وجود خطا در مقادیر عددی، از مقادیر پیش‌فرض استفاده می‌شود.
        """
        enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
        enable_blocking = os.getenv("RATE_LIMIT_BLOCKING", "true").lower() in ("true", "1", "yes")

        try:
            requests_per_window = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
        except ValueError:
            logger.warning("Invalid RATE_LIMIT_REQUESTS, using default 30")
            requests_per_window = 30

        try:
            window_seconds = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        except ValueError:
            logger.warning("Invalid RATE_LIMIT_WINDOW, using default 60")
            window_seconds = 60

        try:
            block_duration_seconds = int(os.getenv("RATE_LIMIT_BLOCK_DURATION", "300"))
        except ValueError:
            logger.warning("Invalid RATE_LIMIT_BLOCK_DURATION, using default 300")
            block_duration_seconds = 300

        storage_backend = os.getenv("RATE_LIMIT_STORAGE", "local").lower()
        if storage_backend not in ("redis", "local"):
            logger.warning(f"Invalid RATE_LIMIT_STORAGE '{storage_backend}', using 'local'")
            storage_backend = "local"

        key_prefix = os.getenv("RATE_LIMIT_KEY_PREFIX", "rate_limit")

        whitelist_str = os.getenv("RATE_LIMIT_WHITELIST", "")
        whitelist_ids = None
        if whitelist_str:
            try:
                whitelist_ids = [int(x.strip()) for x in whitelist_str.split(",") if x.strip()]
            except ValueError as e:
                logger.warning(f"Invalid RATE_LIMIT_WHITELIST, ignoring: {e}")

        config = cls(
            enabled=enabled,
            requests_per_window=requests_per_window,
            window_seconds=window_seconds,
            storage_backend=storage_backend,
            key_prefix=key_prefix,
            block_duration_seconds=block_duration_seconds,
            whitelist_ids=whitelist_ids,
            enable_blocking=enable_blocking,
        )

        logger.info(
            f"Rate limit config loaded: enabled={enabled}, "
            f"requests={requests_per_window}/{window_seconds}s, "
            f"storage={storage_backend}"
        )
        return config

    def is_whitelisted(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر در لیست سفید قرار دارد (معاف از محدودیت).

        Returns:
            True اگر کاربر در لیست سفید باشد یا لیست سفید تعریف نشده باشد.
        """
        if self.whitelist_ids is None:
            return False
        return user_id in self.whitelist_ids

    def get_redis_key(self, user_id: int, action: str = "default") -> str:
        """
        تولید کلید مناسب برای ذخیره‌سازی در Redis.

        Format: {key_prefix}:{action}:{user_id}
        """
        return f"{self.key_prefix}:{action}:{user_id}"

    def get_local_key(self, user_id: int, action: str = "default") -> str:
        """
        تولید کلید مناسب برای ذخیره‌سازی محلی (Local Cache).

        Format: {key_prefix}_{action}_{user_id}
        """
        return f"{self.key_prefix}_{action}_{user_id}"