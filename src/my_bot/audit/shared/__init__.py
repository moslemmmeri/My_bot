# my_bot_project/src/my_bot/shared/__init__.py
"""
ماژول اشتراکی (Shared).

این ماژول شامل ابزارها، دکوراتورها و قابلیت‌های مشترکی است که
در سراسر پروژه استفاده می‌شوند. این ماژول وابستگی به لایه‌های دیگر ندارد
و می‌تواند در هر بخشی از پروژه مورد استفاده قرار گیرد.

اجزای اصلی:
- Utils: توابع کمکی (message_pool, validators, helpers)
- Decorators: دکوراتورهای کاربردی (retry, rate_limit, feature_flag, admin_only)
- I18n: مدیریت چندزبانی (locale_manager, translations, language_detector)
"""

# ----------------------------------------------
# Import Utils
# ----------------------------------------------
from my_bot.shared.utils.message_pool import MessagePool
from my_bot.shared.utils.text_validators import (
    validate_email,
    validate_phone,
    validate_url,
    validate_date,
    validate_time,
    validate_color,
    validate_pattern,
)
from my_bot.shared.utils.date_helpers import (
    format_datetime,
    parse_datetime,
    get_timezone,
    get_date_range,
    is_valid_datetime,
)
from my_bot.shared.utils.excel_parser import ExcelParser

# ----------------------------------------------
# Import Decorators
# ----------------------------------------------
from my_bot.shared.decorators.retry_backoff import retry_backoff
from my_bot.shared.decorators.rate_limit import rate_limit
from my_bot.shared.decorators.feature_flag import feature_flag
from my_bot.shared.decorators.admin_only import admin_only
from my_bot.shared.decorators.log_execution import log_execution

# ----------------------------------------------
# Import I18n
# ----------------------------------------------
from my_bot.shared.i18n.locale_manager import LocaleManager
from my_bot.shared.i18n.language_detector import LanguageDetector

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Utils
    "MessagePool",
    "validate_email",
    "validate_phone",
    "validate_url",
    "validate_date",
    "validate_time",
    "validate_color",
    "validate_pattern",
    "format_datetime",
    "parse_datetime",
    "get_timezone",
    "get_date_range",
    "is_valid_datetime",
    "ExcelParser",

    # Decorators
    "retry_backoff",
    "rate_limit",
    "feature_flag",
    "admin_only",
    "log_execution",

    # I18n
    "LocaleManager",
    "LanguageDetector",
]