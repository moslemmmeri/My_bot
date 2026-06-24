# my_bot_project/src/my_bot/core/exceptions/config_errors.py
"""
استثناهای مربوط به پیکربندی (Configuration Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان بارگذاری، اعتبارسنجی
یا استفاده از پیکربندی‌های برنامه رخ می‌دهند.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class ConfigurationError(MyBotError):
    """
    خطای عمومی مربوط به پیکربندی.

    این استثنا زمانی رخ می‌دهد که مشکلی در پیکربندی برنامه وجود داشته باشد،
    مانند عدم وجود متغیر محیطی اجباری، مقدار نامعتبر، یا مشکل در بارگذاری فایل پیکربندی.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای پیکربندی.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'CONFIG_ERROR').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "CONFIG_ERROR"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در پیکربندی سیستم وجود دارد. لطفاً با پشتیبانی تماس بگیرید."


class MissingConfigError(ConfigurationError):
    """
    خطای عدم وجود متغیر پیکربندی.

    این استثنا زمانی رخ می‌دهد که یک متغیر محیطی اجباری در سیستم تعریف نشده باشد.
    """

    def __init__(
        self,
        config_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم وجود متغیر پیکربندی.

        Args:
            config_key: نام متغیر پیکربندی که وجود ندارد.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"متغیر پیکربندی '{config_key}' در محیط تعریف نشده است."
        context = context or {}
        context["config_key"] = config_key
        super().__init__(message, error_code="MISSING_CONFIG", context=context)


class InvalidConfigError(ConfigurationError):
    """
    خطای نامعتبر بودن مقدار پیکربندی.

    این استثنا زمانی رخ می‌دهد که مقدار یک متغیر پیکربندی از نوع یا فرمت نامعتبر باشد.
    """

    def __init__(
        self,
        config_key: str,
        value: Any,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای مقدار نامعتبر.

        Args:
            config_key: نام متغیر پیکربندی.
            value: مقدار نامعتبر.
            reason: دلیل نامعتبر بودن (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"مقدار '{value}' برای متغیر پیکربندی '{config_key}' نامعتبر است."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["config_key"] = config_key
        context["value"] = str(value)
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="INVALID_CONFIG", context=context)


class ConfigLoadError(ConfigurationError):
    """
    خطای بارگذاری فایل پیکربندی.

    این استثنا زمانی رخ می‌دهد که مشکلی در بارگذاری یا خواندن فایل پیکربندی وجود داشته باشد.
    """

    def __init__(
        self,
        file_path: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای بارگذاری پیکربندی.

        Args:
            file_path: مسیر فایل پیکربندی.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در بارگذاری فایل پیکربندی '{file_path}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["file_path"] = file_path
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CONFIG_LOAD_ERROR", context=context)


__all__ = [
    "ConfigurationError",
    "MissingConfigError",
    "InvalidConfigError",
    "ConfigLoadError",
]