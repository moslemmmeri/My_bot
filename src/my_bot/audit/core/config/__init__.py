# my_bot_project/src/my_bot/core/config/__init__.py
"""
ماژول پیکربندی (Config): شامل کلاس‌های پیکربندی برای بخش‌های مختلف پروژه.

این ماژول با استفاده از dataclass ها، پیکربندی متمرکز و نوع‌مطمئنی را
برای برنامه فراهم می‌کند و از متغیرهای محیطی (.env) بارگذاری می‌شود.
"""

from typing import Optional

# Import کلاس‌های پیکربندی از زیرماژول‌ها
from my_bot.core.config.app_config import AppConfig
from my_bot.core.config.db_config import DBConfig
from my_bot.core.config.redis_config import RedisConfig
from my_bot.core.config.rate_limit_config import RateLimitConfig
from my_bot.core.config.logging_config import LoggingConfig

# ----------------------------------------------
# کلاس اصلی پیکربندی که همه را یکجا جمع می‌کند (اختیاری)
# ----------------------------------------------
from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalConfig:
    """
    کلاس جامع پیکربندی که شامل تمام زیرمجموعه‌هاست.
    این کلاس برای دسترسی آسان به همهٔ تنظیمات در یک شیء استفاده می‌شود.
    """
    app: AppConfig
    db: DBConfig
    redis: Optional[RedisConfig] = None
    rate_limit: RateLimitConfig
    logging: LoggingConfig

    @classmethod
    def from_env(cls) -> "GlobalConfig":
        """
        بارگذاری تمام پیکربندی‌ها از متغیرهای محیطی.
        """
        return cls(
            app=AppConfig.from_env(),
            db=DBConfig.from_env(),
            redis=RedisConfig.from_env() if RedisConfig.is_enabled() else None,
            rate_limit=RateLimitConfig.from_env(),
            logging=LoggingConfig.from_env(),
        )


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "AppConfig",
    "DBConfig",
    "RedisConfig",
    "RateLimitConfig",
    "LoggingConfig",
    "GlobalConfig",
]