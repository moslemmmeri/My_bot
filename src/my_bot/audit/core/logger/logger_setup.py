# my_bot_project/src/my_bot/core/logger/logger_setup.py
"""
راه‌اندازی لاگ‌گیری (Logger Setup).

این ماژول شامل توابعی برای راه‌اندازی و دریافت لاگرها با استفاده از
RotatingFileHandler و پیکربندی از LoggingConfig است.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Optional

from my_bot.core.config.logging_config import LoggingConfig
from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.log_formatter import LogFormatter

# کش لاگرهای ساخته شده برای جلوگیری از ایجاد مجدد
_loggers: Dict[str, logging.Logger] = {}


def setup_logger(name: str, config: LoggingConfig) -> logging.Logger:
    """
    راه‌اندازی یک لاگر با نام مشخص و پیکربندی داده شده.

    این تابع یک لاگر با نام `name` ایجاد می‌کند و هندلرهای فایل و کنسول
    را بر اساس پیکربندی به آن اضافه می‌کند. همچنین لاگر را در کش داخلی
    ذخیره می‌کند تا دفعات بعدی همان نمونه برگردانده شود.

    Args:
        name: نام لاگر (معمولاً __name__ ماژول).
        config: شیء پیکربندی LoggingConfig.

    Returns:
        نمونه‌ی لاگر پیکربندی‌شده.

    Raises:
        ConfigurationError: در صورت بروز خطا در ایجاد دایرکتوری لاگ.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(config.log_level)

    # حذف هندلرهای موجود برای جلوگیری از تکراری شدن
    if logger.handlers:
        logger.handlers.clear()

    # ایجاد فرمتر از پیکربندی
    formatter = config.get_formatter()  # شیء LogFormatter

    # هندلر فایل با چرخش
    if config.enable_file_logging:
        try:
            log_file = Path(config.log_file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=config.log_max_bytes,
                backupCount=config.log_backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(config.log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            raise ConfigurationError(
                f"خطا در ایجاد هندلر فایل لاگ: {e}",
                context={"log_file_path": config.log_file_path},
            )

    # هندلر کنسول
    if config.enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.console_log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # هندلر جداگانه برای خطاها (در صورت فعال بودن)
    if config.enable_error_separation:
        try:
            error_file = Path(config.error_log_file_path)
            error_file.parent.mkdir(parents=True, exist_ok=True)

            error_handler = logging.handlers.RotatingFileHandler(
                filename=error_file,
                maxBytes=config.log_max_bytes,
                backupCount=config.log_backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        except Exception as e:
            raise ConfigurationError(
                f"خطا در ایجاد هندلر فایل خطاها: {e}",
                context={"error_log_file_path": config.error_log_file_path},
            )

    # ذخیره در کش
    _loggers[name] = logger
    return logger


def get_logger(name: str, config: Optional[LoggingConfig] = None) -> logging.Logger:
    """
    دریافت یک لاگر با نام مشخص.

    اگر لاگر قبلاً با `setup_logger` ساخته شده باشد، نمونه‌ی موجود
    برگردانده می‌شود. در غیر این صورت، در صورت ارائه config،
    لاگر جدید ساخته می‌شود، وگرنه یک لاگر ساده (بدون هندلر اضافی)
    از logging.getLogger برگردانده می‌شود.

    Args:
        name: نام لاگر.
        config: پیکربندی اختیاری برای ساخت لاگر در صورت عدم وجود.

    Returns:
        نمونه‌ی لاگر.
    """
    if name in _loggers:
        return _loggers[name]

    if config is not None:
        return setup_logger(name, config)

    # Fallback: یک لاگر ساده بدون هندلر اضافی
    return logging.getLogger(name)