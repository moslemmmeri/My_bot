# my_bot_project/src/my_bot/core/config/redis_config.py
"""
پیکربندی Redis (RedisConfig).

این کلاس شامل تنظیمات مربوط به اتصال به Redis Cache است.
Redis به‌عنوان یک گزینه‌ی اختیاری در نظر گرفته شده و در صورت عدم وجود،
سیستم به‌صورت خودکار به Local Cache Fallback می‌کند.
"""

import os
from dataclasses import dataclass
from typing import Optional

from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RedisConfig:
    """
    پیکربندی Redis.

    Attributes:
        url: آدرس اتصال به Redis (اختیاری)
        host: میزبان Redis (در صورت عدم استفاده از URL)
        port: پورت Redis (پیش‌فرض ۶۳۷۹)
        password: رمز عبور Redis (اختیاری)
        db: شماره دیتابیس Redis (پیش‌فرض ۰)
        ssl: فعال‌سازی SSL (پیش‌فرض False)
        decode_responses: دیکد خودکار پاسخ‌ها (پیش‌فرض True)
        max_connections: حداکثر تعداد اتصالات همزمان (پیش‌فرض ۱۰)
        socket_timeout: زمان انتظار سوکت بر حسب ثانیه (پیش‌فرض ۵)
        socket_connect_timeout: زمان انتظار برای اتصال بر حسب ثانیه (پیش‌فرض ۵)
        retry_on_timeout: تلاش مجدد در صورت Timeout (پیش‌فرض True)
        health_check_interval: بازه‌ی بررسی سلامت بر حسب ثانیه (پیش‌فرض ۳۰)
    """

    url: Optional[str] = None
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    decode_responses: bool = True
    max_connections: int = 10
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """
        بارگذاری پیکربندی Redis از متغیرهای محیطی.

        اولویت با REDIS_URL است، در غیر این صورت از ترکیب REDIS_HOST و REDIS_PORT استفاده می‌شود.
        """
        # تلاش برای دریافت URL کامل
        url = os.getenv("REDIS_URL")

        # اگر URL وجود نداشت، از اجزای جداگانه استفاده کن
        if not url:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            password = os.getenv("REDIS_PASSWORD")
            # ساخت URL با احتساب رمز عبور (در صورت وجود)
            if password:
                url = f"redis://:{password}@{host}:{port}"
            else:
                url = f"redis://{host}:{port}"

        return cls(
            url=url,
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            ssl=os.getenv("REDIS_SSL", "false").lower() in ("true", "1", "yes"),
            decode_responses=os.getenv("REDIS_DECODE_RESPONSES", "true").lower()
            in ("true", "1", "yes"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
            socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0")),
            socket_connect_timeout=float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5.0")),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower()
            in ("true", "1", "yes"),
            health_check_interval=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")),
        )

    @classmethod
    def is_enabled(cls) -> bool:
        """
        بررسی فعال بودن Redis بر اساس متغیرهای محیطی.

        Returns:
            True اگر REDIS_ENABLED = true یا REDIS_URL وجود داشته باشد.
        """
        enabled = os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes")
        has_url = bool(os.getenv("REDIS_URL"))
        has_host = bool(os.getenv("REDIS_HOST"))
        return enabled or has_url or has_host

    def get_connection_params(self) -> dict:
        """
        بازگرداندن پارامترهای اتصال برای استفاده در کتابخانه‌های Redis (مثل redis.asyncio).

        Returns:
            دیکشنری پارامترهای اتصال.
        """
        params = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "decode_responses": self.decode_responses,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
        }

        if self.password:
            params["password"] = self.password

        if self.ssl:
            params["ssl"] = True

        return params

    def get_url(self) -> Optional[str]:
        """
        بازگرداندن URL اتصال (در صورت وجود).
        """
        return self.url