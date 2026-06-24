# my_bot_project/src/my_bot/core/config/logging_config.py
"""
پیکربندی لاگ‌گیری (LoggingConfig).

این کلاس شامل تنظیمات مربوط به لاگ‌گیری با استفاده از RotatingFileHandler
و همچنین فرمت، سطح و سایر پارامترهای مرتبط با ثبت رویدادها است.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.log_formatter import LogFormatter

# از logger_setup استفاده نمی‌کنیم تا وابستگی دایره‌ای ایجاد نشود
# logger = get_logger(__name__)  # این خط را بعداً در logger_setup استفاده می‌کنیم


@dataclass(frozen=True)
class LoggingConfig:
    """
    پیکربندی لاگ‌گیری.

    Attributes:
        log_file_path: مسیر فایل لاگ (پیش‌فرض 'logs/my_bot.log')
        log_max_bytes: حداکثر حجم هر فایل لاگ بر حسب بایت (پیش‌فرض ۱۰ مگابایت)
        log_backup_count: تعداد فایل‌های پشتیبان (پیش‌فرض ۵)
        log_level: سطح لاگ (DEBUG, INFO, WARNING, ERROR, CRITICAL) (پیش‌فرض 'INFO')
        console_log_level: سطح لاگ برای کنسول (پیش‌فرض 'INFO')
        log_format: فرمت لاگ (پیش‌فرض استاندارد)
        log_date_format: فرمت تاریخ در لاگ (پیش‌فرض '%Y-%m-%d %H:%M:%S')
        enable_json_logs: فعال‌سازی خروجی JSON برای لاگ‌ها (پیش‌فرض False)
        enable_console_logging: فعال‌سازی لاگ در کنسول (پیش‌فرض True)
        enable_file_logging: فعال‌سازی لاگ در فایل (پیش‌فرض True)
        log_file_permissions: سطح دسترسی فایل لاگ (پیش‌فرض '0640')
        log_directory_permissions: سطح دسترسی دایرکتوری لاگ (پیش‌فرض '0750')
        error_log_file_path: مسیر فایل لاگ خطاها (پیش‌فرض 'logs/errors.log')
        enable_error_separation: جدا کردن خطاها در فایل مجزا (پیش‌فرض True)
    """

    log_file_path: str = "logs/my_bot.log"
    log_max_bytes: int = 10_485_760  # 10 MB
    log_backup_count: int = 5
    log_level: str = "INFO"
    console_log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    enable_json_logs: bool = False
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    log_file_permissions: str = "0640"
    log_directory_permissions: str = "0750"
    error_log_file_path: str = "logs/errors.log"
    enable_error_separation: bool = True

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """
        بارگذاری پیکربندی لاگ‌گیری از متغیرهای محیطی.

        مقادیر پیش‌فرض برای مواردی که در محیط تعریف نشده‌اند استفاده می‌شوند.
        """
        log_file_path = os.getenv("LOG_FILE_PATH", "logs/my_bot.log")
        error_log_file_path = os.getenv("ERROR_LOG_FILE_PATH", "logs/errors.log")

        try:
            log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
        except ValueError:
            log_max_bytes = 10_485_760

        try:
            log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        except ValueError:
            log_backup_count = 5

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            log_level = "INFO"

        console_log_level = os.getenv("CONSOLE_LOG_LEVEL", "INFO").upper()
        if console_log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            console_log_level = "INFO"

        log_format = os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        log_date_format = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")

        enable_json_logs = os.getenv("ENABLE_JSON_LOGS", "false").lower() in ("true", "1", "yes")
        enable_console_logging = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() in ("true", "1", "yes")
        enable_file_logging = os.getenv("ENABLE_FILE_LOGGING", "true").lower() in ("true", "1", "yes")
        enable_error_separation = os.getenv("ENABLE_ERROR_SEPARATION", "true").lower() in ("true", "1", "yes")

        log_file_permissions = os.getenv("LOG_FILE_PERMISSIONS", "0640")
        log_directory_permissions = os.getenv("LOG_DIRECTORY_PERMISSIONS", "0750")

        config = cls(
            log_file_path=log_file_path,
            log_max_bytes=log_max_bytes,
            log_backup_count=log_backup_count,
            log_level=log_level,
            console_log_level=console_log_level,
            log_format=log_format,
            log_date_format=log_date_format,
            enable_json_logs=enable_json_logs,
            enable_console_logging=enable_console_logging,
            enable_file_logging=enable_file_logging,
            log_file_permissions=log_file_permissions,
            log_directory_permissions=log_directory_permissions,
            error_log_file_path=error_log_file_path,
            enable_error_separation=enable_error_separation,
        )

        # اطمینان از وجود دایرکتوری لاگ (بدون ایجاد فایل)
        config.ensure_log_directory()

        return config

    def ensure_log_directory(self) -> None:
        """
        اطمینان از وجود دایرکتوری لاگ با سطح دسترسی مناسب.

        Raises:
            ConfigurationError: در صورت عدم توانایی در ایجاد دایرکتوری.
        """
        try:
            log_dir = Path(self.log_file_path).parent
            error_dir = Path(self.error_log_file_path).parent

            for directory in (log_dir, error_dir):
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    # تنظیم سطح دسترسی (در ویندوز ممکن است کار نکند)
                    try:
                        # فقط در سیستم‌های Unix-like
                        if os.name != "nt":
                            directory.chmod(int(self.log_directory_permissions, 8))
                    except Exception:
                        pass  # در ویندوز یا سیستم‌های غیرمجاز خطا نادیده گرفته شود

        except Exception as e:
            raise ConfigurationError(f"Failed to create log directory: {e}")

    def get_log_file_path(self) -> Path:
        """بازگرداندن مسیر فایل لاگ به‌عنوان شیء Path."""
        return Path(self.log_file_path)

    def get_error_log_file_path(self) -> Path:
        """بازگرداندن مسیر فایل لاگ خطاها به‌عنوان شیء Path."""
        return Path(self.error_log_file_path)

    def get_formatter(self) -> LogFormatter:
        """
        ایجاد و بازگرداندن یک شیء LogFormatter بر اساس تنظیمات.

        Returns:
            شیء LogFormatter با فرمت و تاریخ مشخص.
        """
        return LogFormatter(
            fmt=self.log_format,
            datefmt=self.log_date_format,
            use_json=self.enable_json_logs,
        )