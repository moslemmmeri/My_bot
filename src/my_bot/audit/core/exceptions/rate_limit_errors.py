# my_bot_project/src/my_bot/core/exceptions/rate_limit_errors.py
"""
استثناهای مربوط به محدودیت نرخ درخواست (Rate Limit Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان بررسی محدودیت نرخ درخواست،
تجاوز از سقف مجاز، خطا در ذخیره‌سازی اطلاعات محدودیت و سایر موارد مرتبط
با Rate Limiting رخ می‌دهند.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class RateLimitExceededError(MyBotError):
    """
    خطای تجاوز از محدودیت نرخ درخواست.

    این استثنا زمانی رخ می‌دهد که کاربر بیش از حد مجاز در بازه‌ی زمانی مشخص
    درخواست ارسال کرده باشد.

    Attributes:
        retry_after_seconds: مدت زمان انتظار پیشنهادی برای تلاش مجدد (ثانیه).
    """

    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[int] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای تجاوز از محدودیت.

        Args:
            message: پیام خطا.
            retry_after_seconds: زمان انتظار پیشنهادی برای تلاش مجدد (ثانیه).
            error_code: کد خطای اختیاری (پیش‌فرض: 'RATE_LIMIT_EXCEEDED').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "RATE_LIMIT_EXCEEDED"

        context = context or {}
        if retry_after_seconds is not None:
            context["retry_after_seconds"] = retry_after_seconds

        self.retry_after_seconds = retry_after_seconds
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند با ذکر زمان انتظار (در صورت وجود).
        """
        base_message = "تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید."
        if self.retry_after_seconds:
            if self.retry_after_seconds < 60:
                return f"{base_message} {self.retry_after_seconds} ثانیه دیگر تلاش کنید."
            minutes = self.retry_after_seconds // 60
            seconds = self.retry_after_seconds % 60
            if seconds > 0:
                return f"{base_message} {minutes} دقیقه و {seconds} ثانیه دیگر تلاش کنید."
            return f"{base_message} {minutes} دقیقه دیگر تلاش کنید."
        return base_message


class RateLimitTemporaryError(RateLimitExceededError):
    """
    خطای محدودیت موقت.

    این استثنا زمانی رخ می‌دهد که کاربر به‌صورت موقت (برای مدت کوتاهی)
    محدود شده باشد.
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        retry_after_seconds: int = 60,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای محدودیت موقت.

        Args:
            user_id: شناسه کاربر محدود شده (اختیاری).
            retry_after_seconds: زمان انتظار پیشنهادی برای تلاش مجدد (پیش‌فرض ۶۰ ثانیه).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "محدودیت موقت اعمال شد. لطفاً کمی صبر کنید."
        if user_id:
            message += f" (کاربر: {user_id})"

        context = context or {}
        if user_id:
            context["user_id"] = user_id

        super().__init__(
            message=message,
            retry_after_seconds=retry_after_seconds,
            error_code="RATE_LIMIT_TEMPORARY",
            context=context,
        )


class RateLimitPermanentError(RateLimitExceededError):
    """
    خطای محدودیت دائم.

    این استثنا زمانی رخ می‌دهد که کاربر به‌صورت دائم محدود شده باشد
    (معمولاً به دلیل نقض مکرر قوانین).
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای محدودیت دائم.

        Args:
            user_id: شناسه کاربر محدود شده (اختیاری).
            reason: دلیل محدودیت (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "دسترسی شما به‌صورت دائم محدود شده است."
        if reason:
            message += f" دلیل: {reason}"
        if user_id:
            message += f" (کاربر: {user_id})"

        context = context or {}
        if user_id:
            context["user_id"] = user_id
        if reason:
            context["reason"] = reason

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_PERMANENT",
            context=context,
        )

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند برای محدودیت دائم.
        """
        return "دسترسی شما به دلیل نقض مکرر قوانین محدود شده است. برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."


class RateLimitRetryError(RateLimitExceededError):
    """
    خطای تلاش مجدد با زمان انتظار مشخص.

    این استثنا زمانی رخ می‌دهد که کاربر باید پس از مدت زمان مشخصی
    دوباره تلاش کند.
    """

    def __init__(
        self,
        retry_after_seconds: int,
        action: str = "درخواست",
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای تلاش مجدد.

        Args:
            retry_after_seconds: زمان انتظار برای تلاش مجدد (ثانیه).
            action: نوع عملیات (پیش‌فرض: 'درخواست').
            user_id: شناسه کاربر (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"{action} با محدودیت مواجه شد. {retry_after_seconds} ثانیه دیگر تلاش کنید."
        if user_id:
            message += f" (کاربر: {user_id})"

        context = context or {}
        context["action"] = action
        if user_id:
            context["user_id"] = user_id

        super().__init__(
            message=message,
            retry_after_seconds=retry_after_seconds,
            error_code="RATE_LIMIT_RETRY",
            context=context,
        )


class RateLimitWhitelistError(RateLimitExceededError):
    """
    خطای عدم وجود در لیست سفید.

    این استثنا زمانی رخ می‌دهد که کاربر تلاش به استفاده از ویژگی‌ای کند
    که نیاز به حضور در لیست سفید دارد.
    """

    def __init__(
        self,
        user_id: int,
        feature: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای لیست سفید.

        Args:
            user_id: شناسه کاربر.
            feature: نام ویژگی (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "شما در لیست سفید این ویژگی قرار ندارید."
        if feature:
            message += f" ویژگی: {feature}"
        message += f" (کاربر: {user_id})"

        context = context or {}
        context["user_id"] = user_id
        if feature:
            context["feature"] = feature

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_WHITELIST",
            context=context,
        )


class RateLimitStorageError(RateLimitExceededError):
    """
    خطای ذخیره‌سازی اطلاعات محدودیت.

    این استثنا زمانی رخ می‌دهد که مشکلی در ذخیره‌سازی یا بازیابی اطلاعات
    محدودیت نرخ درخواست وجود داشته باشد (مشکل در Redis یا Local Storage).
    """

    def __init__(
        self,
        storage_backend: str,
        operation: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ذخیره‌سازی.

        Args:
            storage_backend: نام Backend ذخیره‌سازی ('redis', 'local').
            operation: نوع عملیات ('set', 'get', 'delete').
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در عملیات '{operation}' روی Backend ذخیره‌سازی '{storage_backend}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["storage_backend"] = storage_backend
        context["operation"] = operation
        if reason:
            context["reason"] = reason

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_STORAGE_ERROR",
            context=context,
        )

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در سیستم محدودیت درخواست وجود دارد. لطفاً دوباره تلاش کنید."


class RateLimitConfigError(RateLimitExceededError):
    """
    خطای پیکربندی محدودیت نرخ.

    این استثنا زمانی رخ می‌دهد که پیکربندی محدودیت نرخ درخواست
    نامعتبر یا ناقص باشد.
    """

    def __init__(
        self,
        config_key: str,
        value: Any,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای پیکربندی.

        Args:
            config_key: نام کلید پیکربندی.
            value: مقدار پیکربندی.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"پیکربندی محدودیت نرخ '{config_key}' نامعتبر است. مقدار: {value}"
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["config_key"] = config_key
        context["value"] = str(value)
        if reason:
            context["reason"] = reason

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_CONFIG_ERROR",
            context=context,
        )


__all__ = [
    "RateLimitExceededError",
    "RateLimitTemporaryError",
    "RateLimitPermanentError",
    "RateLimitRetryError",
    "RateLimitWhitelistError",
    "RateLimitStorageError",
    "RateLimitConfigError",
]