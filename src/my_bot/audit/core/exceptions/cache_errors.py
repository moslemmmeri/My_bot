# my_bot_project/src/my_bot/core/exceptions/cache_errors.py
"""
استثناهای مربوط به کش (Cache Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان ارتباط با سیستم‌های کش
(Redis، Local Cache و ...)، عملیات ذخیره‌سازی، بازیابی و حذف داده‌ها رخ می‌دهند.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class CacheError(MyBotError):
    """
    خطای عمومی مربوط به کش.

    این استثنا زمانی رخ می‌دهد که مشکلی در ارتباط با سیستم کش،
    ذخیره‌سازی، بازیابی یا حذف داده‌ها وجود داشته باشد.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای کش.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'CACHE_ERROR').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "CACHE_ERROR"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در سیستم کش وجود دارد. لطفاً دوباره تلاش کنید."


class CacheConnectionError(CacheError):
    """
    خطای اتصال به سیستم کش.

    این استثنا زمانی رخ می‌دهد که امکان برقراری اتصال به سیستم کش
    (مانند Redis) وجود نداشته باشد.
    """

    def __init__(
        self,
        backend: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای اتصال به کش.

        Args:
            backend: نام سیستم کش (مانند 'redis', 'local').
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در اتصال به سیستم کش '{backend}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["backend"] = backend
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CACHE_CONNECTION_ERROR", context=context)


class CacheOperationError(CacheError):
    """
    خطای عملیات روی کش.

    این استثنا زمانی رخ می‌دهد که عملیات‌های ذخیره‌سازی، بازیابی،
    حذف یا سایر عملیات‌های کش با خطا مواجه شوند.
    """

    def __init__(
        self,
        operation: str,
        key: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عملیات کش.

        Args:
            operation: نوع عملیات (set, get, delete, etc).
            key: کلید مربوطه (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در عملیات کش '{operation}'."
        if key:
            message += f" برای کلید '{key}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["operation"] = operation
        if key:
            context["key"] = key
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CACHE_OPERATION_ERROR", context=context)


class CacheKeyError(CacheError):
    """
    خطای کلید در کش.

    این استثنا زمانی رخ می‌دهد که کلید مورد نظر در کش وجود نداشته باشد
    یا فرمت کلید نامعتبر باشد.
    """

    def __init__(
        self,
        key: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای کلید کش.

        Args:
            key: کلید مورد نظر.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در کلید کش '{key}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["key"] = key
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CACHE_KEY_ERROR", context=context)


class CacheSerializationError(CacheError):
    """
    خطای سریال‌سازی/دیسریال‌سازی داده در کش.

    این استثنا زمانی رخ می‌دهد که داده‌ها قابل سریال‌سازی یا دیسریال‌سازی نباشند.
    """

    def __init__(
        self,
        operation: str,
        data_type: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای سریال‌سازی.

        Args:
            operation: نوع عملیات (serialize, deserialize).
            data_type: نوع داده‌ای که با خطا مواجه شده (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در {operation} داده‌ها برای کش."
        if data_type:
            message += f" نوع داده: '{data_type}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["operation"] = operation
        if data_type:
            context["data_type"] = data_type
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CACHE_SERIALIZATION_ERROR", context=context)


class CacheBackendError(CacheError):
    """
    خطای Backend کش.

    این استثنا زمانی رخ می‌دهد که Backend کش (مانند Redis) به‌درستی
    پیکربندی نشده باشد یا غیرقابل دسترس باشد.
    """

    def __init__(
        self,
        backend: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای Backend کش.

        Args:
            backend: نام Backend کش.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در Backend کش '{backend}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["backend"] = backend
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CACHE_BACKEND_ERROR", context=context)


class CacheTimeoutError(CacheError):
    """
    خطای Timeout در عملیات کش.

    این استثنا زمانی رخ می‌دهد که عملیات کش به دلیل زمان‌بر بودن با Timeout مواجه شود.
    """

    def __init__(
        self,
        operation: str,
        key: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای Timeout.

        Args:
            operation: نوع عملیات (set, get, delete, etc).
            key: کلید مربوطه (اختیاری).
            timeout_seconds: زمان Timeout بر حسب ثانیه (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"Timeout در عملیات کش '{operation}'."
        if key:
            message += f" برای کلید '{key}'."
        if timeout_seconds:
            message += f" زمان انتظار: {timeout_seconds} ثانیه."

        context = context or {}
        context["operation"] = operation
        if key:
            context["key"] = key
        if timeout_seconds:
            context["timeout_seconds"] = timeout_seconds

        super().__init__(message, error_code="CACHE_TIMEOUT_ERROR", context=context)


class CachePoolError(CacheError):
    """
    خطای Connection Pool کش.

    این استثنا زمانی رخ می‌دهد که مشکلی در Connection Pool
    (مانند تمام شدن اتصالات، timeout و ...) وجود داشته باشد.
    """

    def __init__(
        self,
        backend: str,
        operation: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای Connection Pool کش.

        Args:
            backend: نام سیستم کش.
            operation: نوع عملیات (get_connection, release, etc).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در Connection Pool کش '{backend}' هنگام عملیات '{operation}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["backend"] = backend
        context["operation"] = operation
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="CACHE_POOL_ERROR", context=context)


__all__ = [
    "CacheError",
    "CacheConnectionError",
    "CacheOperationError",
    "CacheKeyError",
    "CacheSerializationError",
    "CacheBackendError",
    "CacheTimeoutError",
    "CachePoolError",
]