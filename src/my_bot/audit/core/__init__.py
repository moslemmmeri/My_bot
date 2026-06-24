# my_bot_project/src/my_bot/core/__init__.py
"""
ماژول Core: شامل پیکربندی، ثابت‌ها، استثناهای سفارشی، ابزارهای لاگ‌گیری و مدیریت Feature Flag.

این ماژول به‌عنوان قلب پروژه، وابستگی‌های زیرساختی را مدیریت کرده و
امکانات پایه‌ای را در اختیار سایر لایه‌ها قرار می‌دهد.
"""

from typing import TypeVar

# ----------------------------------------------
# Export از زیرماژول‌ها برای دسترسی آسان
# ----------------------------------------------

# Config
from my_bot.core.config.app_config import AppConfig
from my_bot.core.config.db_config import DBConfig
from my_bot.core.config.redis_config import RedisConfig
from my_bot.core.config.rate_limit_config import RateLimitConfig
from my_bot.core.config.logging_config import LoggingConfig

# Constants
from my_bot.core.constants.user_roles import UserRole
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.constants.form_types import FormType

# Exceptions
from my_bot.core.exceptions.base import MyBotError
from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.cache_errors import CacheError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.rate_limit_errors import RateLimitExceededError
from my_bot.core.exceptions.form_errors import FormProcessingError
from my_bot.core.exceptions.broadcast_errors import BroadcastError
from my_bot.core.exceptions.feature_errors import FeatureDisabledError
from my_bot.core.exceptions.not_found_errors import NotFoundError

# Logger
from my_bot.core.logger.logger_setup import setup_logger, get_logger
from my_bot.core.logger.logger_factory import LoggerFactory
from my_bot.core.logger.log_formatter import LogFormatter

# Feature Flags
from my_bot.core.feature_flags.flag_manager import FeatureFlagManager
from my_bot.core.feature_flags.flag_repository import FlagRepository
from my_bot.core.feature_flags.flag_cache import FlagCache

# ----------------------------------------------
# نوع‌های عمومی برای استفاده در سایر ماژول‌ها
# ----------------------------------------------
T = TypeVar("T")  # برای استفاده در ژنریک‌ها

# ----------------------------------------------
# لیست اشیاء قابل export (اختیاری)
# ----------------------------------------------
__all__ = [
    # Config
    "AppConfig",
    "DBConfig",
    "RedisConfig",
    "RateLimitConfig",
    "LoggingConfig",

    # Constants
    "UserRole",
    "OrderStatus",
    "PaymentStatus",
    "FormType",

    # Exceptions
    "MyBotError",
    "ConfigurationError",
    "DatabaseError",
    "CacheError",
    "ValidationError",
    "PermissionDeniedError",
    "RateLimitExceededError",
    "FormProcessingError",
    "BroadcastError",
    "FeatureDisabledError",
    "NotFoundError",

    # Logger
    "setup_logger",
    "get_logger",
    "LoggerFactory",
    "LogFormatter",

    # Feature Flags
    "FeatureFlagManager",
    "FlagRepository",
    "FlagCache",

    # Generic
    "T",
]

# ----------------------------------------------
# اطلاعات نسخه (اختیاری)
# ----------------------------------------------
__version__ = "1.0.0"