# my_bot_project/src/my_bot/core/config/db_config.py
"""
پیکربندی دیتابیس (DBConfig).

این کلاس شامل تنظیمات مربوط به اتصال به پایگاه داده،
اندازهٔ Connection Pool و سایر پارامترهای مرتبط با دیتابیس است.
"""

import os
from dataclasses import dataclass
from typing import Optional

from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class DBConfig:
    """
    پیکربندی دیتابیس.

    Attributes:
        url: آدرس اتصال به دیتابیس (اجباری)
        pool_size: تعداد اتصالات اولیه در Connection Pool (پیش‌فرض ۱۰)
        max_overflow: حداکثر اتصالات اضافی در Pool (پیش‌فرض ۲۰)
        pool_timeout: زمان انتظار برای گرفتن اتصال از Pool بر حسب ثانیه (پیش‌فرض ۳۰)
        pool_recycle: زمان بازیابی اتصالات بر حسب ثانیه (پیش‌فرض ۳۶۰۰)
        echo: فعال‌سازی لاگ SQL (پیش‌فرض False)
        auto_migrate: اجرای خودکار مایگریشن‌ها در استارت‌آپ (پیش‌فرض False)
        ssl_mode: حالت SSL برای PostgreSQL (پیش‌فرض 'disable')
    """

    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    auto_migrate: bool = False
    ssl_mode: str = "disable"

    @classmethod
    def from_env(cls) -> "DBConfig":
        """
        بارگذاری پیکربندی دیتابیس از متغیرهای محیطی.

        Raises:
            ConfigurationError: در صورت عدم وجود DATABASE_URL.
        """
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ConfigurationError("DATABASE_URL is required but not set in environment.")

        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        echo = os.getenv("DB_ECHO", "false").lower() in ("true", "1", "yes")
        auto_migrate = os.getenv("DB_AUTO_MIGRATE", "false").lower() in ("true", "1", "yes")
        ssl_mode = os.getenv("DB_SSL_MODE", "disable")

        config = cls(
            url=url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo,
            auto_migrate=auto_migrate,
            ssl_mode=ssl_mode,
        )

        logger.info(f"Database config loaded: {config.db_type()} (pool_size={pool_size})")
        return config

    def is_sqlite(self) -> bool:
        """بررسی اینکه دیتابیس از نوع SQLite است."""
        return self.url.startswith("sqlite")

    def is_postgresql(self) -> bool:
        """بررسی اینکه دیتابیس از نوع PostgreSQL است."""
        return self.url.startswith("postgresql") or self.url.startswith("postgres")

    def db_type(self) -> str:
        """بازگرداندن نوع دیتابیس به‌صورت رشته."""
        if self.is_sqlite():
            return "SQLite"
        if self.is_postgresql():
            return "PostgreSQL"
        return "Unknown"

    def get_async_url(self) -> str:
        """
        تبدیل URL به فرمت مناسب برای درایور async (در صورت نیاز).

        برای PostgreSQL، پیشوند 'postgresql+asyncpg://' اعمال می‌شود.
        برای SQLite، تغییری ایجاد نمی‌شود.
        """
        if self.is_postgresql():
            # تبدیل postgresql:// به postgresql+asyncpg://
            if self.url.startswith("postgresql://"):
                return self.url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if self.url.startswith("postgres://"):
                return self.url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self.url