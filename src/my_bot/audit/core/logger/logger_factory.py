# my_bot_project/src/my_bot/core/logger/logger_factory.py
"""
کارخانه‌ی تولید لاگرها (Logger Factory).

این ماژول شامل کلاس `LoggerFactory` است که با استفاده از الگوی Factory،
لاگرهای پیکربندی‌شده را برای بخش‌های مختلف پروژه تولید می‌کند.
کارخانه امکان ایجاد لاگرهای با نام‌های استاندارد و پیکربندی یکسان را فراهم می‌کند.
"""

import logging
from typing import Dict, Optional, List

from my_bot.core.config.logging_config import LoggingConfig
from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.logger_setup import setup_logger, get_logger


class LoggerFactory:
    """
    کارخانه‌ی تولید لاگرها.

    این کلاس با دریافت پیکربندی، لاگرهای استاندارد برای بخش‌های مختلف
    پروژه ایجاد می‌کند و از تکرار کد جلوگیری می‌نماید.

    Attributes:
        config: پیکربندی لاگ‌گیری.
        _default_logger: لاگر پیش‌فرض (اختیاری).
    """

    def __init__(self, config: LoggingConfig) -> None:
        """
        مقداردهی اولیه کارخانه.

        Args:
            config: پیکربندی لاگ‌گیری.

        Raises:
            ConfigurationError: در صورت نامعتبر بودن پیکربندی.
        """
        if not config:
            raise ConfigurationError("پیکربندی لاگ‌گیری نمی‌تواند خالی باشد.")

        self.config = config
        self._default_logger: Optional[logging.Logger] = None

    def create_logger(
        self,
        name: str,
        enable_file: Optional[bool] = None,
        enable_console: Optional[bool] = None,
        log_level: Optional[str] = None,
    ) -> logging.Logger:
        """
        ایجاد یک لاگر با نام مشخص و تنظیمات سفارشی.

        Args:
            name: نام لاگر (معمولاً __name__ ماژول).
            enable_file: فعال‌سازی لاگ در فایل (در صورت None، از پیکربندی اصلی استفاده می‌شود).
            enable_console: فعال‌سازی لاگ در کنسول (در صورت None، از پیکربندی اصلی استفاده می‌شود).
            log_level: سطح لاگ (در صورت None، از پیکربندی اصلی استفاده می‌شود).

        Returns:
            نمونه‌ی لاگر پیکربندی‌شده.
        """
        # ایجاد یک کپی از پیکربندی با تنظیمات سفارشی
        config = self.config

        # اگر تنظیمات سفارشی وجود دارد، یک پیکربندی موقت ایجاد می‌کنیم
        if enable_file is not None or enable_console is not None or log_level is not None:
            # استفاده از dataclasses.replace برای ایجاد کپی (اگر از Python 3.7+ استفاده می‌کنیم)
            # در غیر این صورت، یک نمونه جدید می‌سازیم
            import copy
            config = copy.replace(
                self.config,
                enable_file_logging=enable_file if enable_file is not None else self.config.enable_file_logging,
                enable_console_logging=enable_console if enable_console is not None else self.config.enable_console_logging,
                log_level=log_level if log_level is not None else self.config.log_level,
            )

        # استفاده از setup_logger برای ایجاد لاگر
        return setup_logger(name, config)

    def get_default_logger(self) -> logging.Logger:
        """
        دریافت لاگر پیش‌فرض (برای استفاده در بخش‌هایی که نام ماژول مشخصی ندارند).

        Returns:
            نمونه‌ی لاگر پیش‌فرض.
        """
        if self._default_logger is None:
            self._default_logger = self.create_logger("my_bot")
        return self._default_logger

    def get_core_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای لایه‌ی Core.

        Returns:
            نمونه‌ی لاگر برای Core.
        """
        return self.create_logger("my_bot.core")

    def get_domain_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای لایه‌ی Domain.

        Returns:
            نمونه‌ی لاگر برای Domain.
        """
        return self.create_logger("my_bot.domain")

    def get_application_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای لایه‌ی Application.

        Returns:
            نمونه‌ی لاگر برای Application.
        """
        return self.create_logger("my_bot.application")

    def get_infrastructure_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای لایه‌ی Infrastructure.

        Returns:
            نمونه‌ی لاگر برای Infrastructure.
        """
        return self.create_logger("my_bot.infrastructure")

    def get_presentation_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای لایه‌ی Presentation.

        Returns:
            نمونه‌ی لاگر برای Presentation.
        """
        return self.create_logger("my_bot.presentation")

    def get_admin_panel_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای پنل مدیریت (Admin Panel).

        Returns:
            نمونه‌ی لاگر برای Admin Panel.
        """
        return self.create_logger("my_bot.admin_panel")

    def get_shared_logger(self) -> logging.Logger:
        """
        دریافت لاگر برای لایه‌ی Shared.

        Returns:
            نمونه‌ی لاگر برای Shared.
        """
        return self.create_logger("my_bot.shared")

    def get_module_logger(self, module_name: str) -> logging.Logger:
        """
        دریافت لاگر برای یک ماژول خاص.

        Args:
            module_name: نام ماژول (مثلاً 'user_management', 'feature_management').

        Returns:
            نمونه‌ی لاگر برای ماژول مشخص.
        """
        return self.create_logger(f"my_bot.modules.{module_name}")

    def get_handler_logger(self, handler_name: str) -> logging.Logger:
        """
        دریافت لاگر برای یک هندلر خاص.

        Args:
            handler_name: نام هندلر (مثلاً 'start_handler', 'payment_handler').

        Returns:
            نمونه‌ی لاگر برای هندلر مشخص.
        """
        return self.create_logger(f"my_bot.handlers.{handler_name}")

    def get_service_logger(self, service_name: str) -> logging.Logger:
        """
        دریافت لاگر برای یک سرویس خاص.

        Args:
            service_name: نام سرویس (مثلاً 'user_service', 'payment_service').

        Returns:
            نمونه‌ی لاگر برای سرویس مشخص.
        """
        return self.create_logger(f"my_bot.services.{service_name}")

    def get_repository_logger(self, repository_name: str) -> logging.Logger:
        """
        دریافت لاگر برای یک ریپازیتوری خاص.

        Args:
            repository_name: نام ریپازیتوری (مثلاً 'user_repository').

        Returns:
            نمونه‌ی لاگر برای ریپازیتوری مشخص.
        """
        return self.create_logger(f"my_bot.repositories.{repository_name}")

    def get_logger_with_level(self, name: str, level: str) -> logging.Logger:
        """
        ایجاد یک لاگر با سطح مشخص (صرف‌نظر از پیکربندی اصلی).

        Args:
            name: نام لاگر.
            level: سطح لاگ (DEBUG, INFO, WARNING, ERROR, CRITICAL).

        Returns:
            نمونه‌ی لاگر با سطح مشخص.
        """
        return self.create_logger(name, log_level=level)

    def get_debug_logger(self, name: str) -> logging.Logger:
        """
        ایجاد یک لاگر با سطح DEBUG برای دیباگ.

        Args:
            name: نام لاگر.

        Returns:
            نمونه‌ی لاگر با سطح DEBUG.
        """
        return self.get_logger_with_level(name, "DEBUG")

    @staticmethod
    def get_root_logger() -> logging.Logger:
        """
        دریافت لاگر ریشه (Root Logger).

        Returns:
            نمونه‌ی لاگر ریشه.
        """
        return logging.getLogger()

    def get_logger_for_class(self, class_name: str, module_name: str) -> logging.Logger:
        """
        دریافت لاگر برای یک کلاس خاص با فرمت استاندارد.

        Args:
            class_name: نام کلاس.
            module_name: نام ماژول کلاس.

        Returns:
            نمونه‌ی لاگر با نام ترکیبی.
        """
        return self.create_logger(f"{module_name}.{class_name}")

    def list_all_loggers(self) -> List[str]:
        """
        دریافت لیست تمام لاگرهای ثبت‌شده در سیستم.

        Returns:
            لیست نام‌های لاگرهای موجود.
        """
        from my_bot.core.logger.logger_setup import _loggers
        return list(_loggers.keys())

    def clear_cache(self) -> None:
        """
        پاک کردن کش لاگرها (برای استفاده در تست‌ها یا زمان تغییر پیکربندی).
        """
        from my_bot.core.logger.logger_setup import _loggers
        _loggers.clear()
        self._default_logger = None