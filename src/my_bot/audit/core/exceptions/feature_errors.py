# my_bot_project/src/my_bot/core/exceptions/feature_errors.py
"""
استثناهای مربوط به Feature Flags (مدیریت ویژگی‌ها).

این ماژول شامل کلاس‌های استثنایی است که در زمان مدیریت Feature Flags،
فعال/غیرفعال‌سازی ویژگی‌ها، بررسی دسترسی و سایر عملیات‌های مرتبط با
مدیریت ویژگی‌ها رخ می‌دهند.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class FeatureDisabledError(MyBotError):
    """
    خطای غیرفعال بودن ویژگی.

    این استثنا زمانی رخ می‌دهد که کاربر یا سیستمی تلاش به استفاده از
    ویژگی‌ای کند که در حال حاضر غیرفعال است.
    """

    def __init__(
        self,
        feature_name: str,
        reason: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ویژگی غیرفعال.

        Args:
            feature_name: نام ویژگی.
            reason: دلیل غیرفعال بودن (اختیاری).
            error_code: کد خطای اختیاری (پیش‌فرض: 'FEATURE_DISABLED').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "FEATURE_DISABLED"

        message = f"ویژگی '{feature_name}' در حال حاضر غیرفعال است."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["feature_name"] = feature_name
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        feature_name = self.context.get("feature_name", "این ویژگی")
        return f"{feature_name} در حال حاضر در دسترس نیست. لطفاً بعداً تلاش کنید."


class FeatureNotFoundError(MyBotError):
    """
    خطای عدم وجود ویژگی.

    این استثنا زمانی رخ می‌دهد که ویژگی درخواستی در سیستم تعریف نشده باشد.
    """

    def __init__(
        self,
        feature_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم وجود ویژگی.

        Args:
            feature_name: نام ویژگی.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"ویژگی '{feature_name}' در سیستم تعریف نشده است."

        context = context or {}
        context["feature_name"] = feature_name

        super().__init__(message, error_code="FEATURE_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "ویژگی مورد نظر در سیستم موجود نیست."


class FeatureAccessDeniedError(MyBotError):
    """
    خطای عدم دسترسی به ویژگی.

    این استثنا زمانی رخ می‌دهد که کاربر مجوز دسترسی به ویژگی‌ای را نداشته باشد.
    """

    def __init__(
        self,
        feature_name: str,
        user_id: Optional[int] = None,
        required_role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم دسترسی به ویژگی.

        Args:
            feature_name: نام ویژگی.
            user_id: شناسه کاربر (اختیاری).
            required_role: نقش مورد نیاز (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"کاربر دسترسی به ویژگی '{feature_name}' را ندارد."
        if user_id:
            message += f" (کاربر: {user_id})"
        if required_role:
            message += f" نقش مورد نیاز: {required_role}"

        context = context or {}
        context["feature_name"] = feature_name
        if user_id:
            context["user_id"] = user_id
        if required_role:
            context["required_role"] = required_role

        super().__init__(message, error_code="FEATURE_ACCESS_DENIED", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "شما مجوز دسترسی به این ویژگی را ندارید."


class FeatureToggleError(MyBotError):
    """
    خطای تغییر وضعیت ویژگی.

    این استثنا زمانی رخ می‌دهد که مشکلی در فعال یا غیرفعال‌سازی یک ویژگی وجود داشته باشد.
    """

    def __init__(
        self,
        feature_name: str,
        action: str,  # 'enable' یا 'disable'
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای تغییر وضعیت ویژگی.

        Args:
            feature_name: نام ویژگی.
            action: نوع عملیات ('enable' یا 'disable').
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        action_persian = "فعال‌سازی" if action == "enable" else "غیرفعال‌سازی"
        message = f"خطا در {action_persian} ویژگی '{feature_name}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["feature_name"] = feature_name
        context["action"] = action
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FEATURE_TOGGLE_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "خطا در تغییر وضعیت ویژگی. لطفاً دوباره تلاش کنید."


class FeatureStorageError(MyBotError):
    """
    خطای ذخیره‌سازی ویژگی.

    این استثنا زمانی رخ می‌دهد که مشکلی در ذخیره‌سازی یا بازیابی
    وضعیت ویژگی‌ها در دیتابیس یا کش وجود داشته باشد.
    """

    def __init__(
        self,
        operation: str,  # 'save', 'load', 'delete'
        feature_name: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ذخیره‌سازی ویژگی.

        Args:
            operation: نوع عملیات ('save', 'load', 'delete').
            feature_name: نام ویژگی (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در عملیات '{operation}' روی ویژگی‌ها."
        if feature_name:
            message += f" ویژگی: {feature_name}"
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["operation"] = operation
        if feature_name:
            context["feature_name"] = feature_name
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FEATURE_STORAGE_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در ذخیره‌سازی وضعیت ویژگی‌ها وجود دارد. لطفاً دوباره تلاش کنید."


class FeatureDependencyError(MyBotError):
    """
    خطای وابستگی بین ویژگی‌ها.

    این استثنا زمانی رخ می‌دهد که یک ویژگی به ویژگی دیگری وابسته است
    و آن ویژگی غیرفعال می‌باشد.
    """

    def __init__(
        self,
        feature_name: str,
        dependency: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای وابستگی ویژگی.

        Args:
            feature_name: نام ویژگی اصلی.
            dependency: نام ویژگی وابسته.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"ویژگی '{feature_name}' به ویژگی '{dependency}' وابسته است که غیرفعال می‌باشد."

        context = context or {}
        context["feature_name"] = feature_name
        context["dependency"] = dependency

        super().__init__(message, error_code="FEATURE_DEPENDENCY_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        dependency = self.context.get("dependency", "ویژگی دیگر")
        return f"این ویژگی به '{dependency}' وابسته است که در حال حاضر فعال نیست."


class FeatureValidationError(MyBotError):
    """
    خطای اعتبارسنجی ویژگی.

    این استثنا زمانی رخ می‌دهد که داده‌های مربوط به تعریف ویژگی
    (مانند نام، توضیحات، و ...) معتبر نباشند.
    """

    def __init__(
        self,
        feature_name: str,
        field: str,
        value: Any,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای اعتبارسنجی ویژگی.

        Args:
            feature_name: نام ویژگی.
            field: نام فیلد معتبر.
            value: مقدار نامعتبر.
            reason: دلیل نامعتبر بودن (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"داده‌های ویژگی '{feature_name}' معتبر نیستند. فیلد '{field}' با مقدار '{value}' نامعتبر است."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["feature_name"] = feature_name
        context["field"] = field
        context["value"] = str(value)
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FEATURE_VALIDATION_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        field = self.context.get("field", "فیلد")
        return f"داده‌های ورودی برای '{field}' معتبر نیستند. لطفاً بررسی کنید."


class FeatureExpiredError(MyBotError):
    """
    خطای منقضی شدن ویژگی.

    این استثنا زمانی رخ می‌دهد که یک ویژگی دارای تاریخ انقضا است
    و آن تاریخ گذشته باشد.
    """

    def __init__(
        self,
        feature_name: str,
        expired_at: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای منقضی شدن ویژگی.

        Args:
            feature_name: نام ویژگی.
            expired_at: تاریخ انقضا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"ویژگی '{feature_name}' منقضی شده است."
        if expired_at:
            message += f" تاریخ انقضا: {expired_at}"

        context = context or {}
        context["feature_name"] = feature_name
        if expired_at:
            context["expired_at"] = expired_at

        super().__init__(message, error_code="FEATURE_EXPIRED", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "این ویژگی منقضی شده و دیگر در دسترس نیست."


class FeatureLimitExceededError(MyBotError):
    """
    خطای تجاوز از محدودیت ویژگی.

    این استثنا زمانی رخ می‌دهد که استفاده از یک ویژگی از حد مجاز فراتر رود
    (مثلاً تعداد کاربران مجاز برای استفاده از ویژگی).
    """

    def __init__(
        self,
        feature_name: str,
        limit: int,
        current: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای تجاوز از محدودیت.

        Args:
            feature_name: نام ویژگی.
            limit: حد مجاز.
            current: تعداد فعلی.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"محدودیت ویژگی '{feature_name}' به پایان رسیده است. حد مجاز: {limit}، تعداد فعلی: {current}"

        context = context or {}
        context["feature_name"] = feature_name
        context["limit"] = limit
        context["current"] = current

        super().__init__(message, error_code="FEATURE_LIMIT_EXCEEDED", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        limit = self.context.get("limit", 0)
        return f"محدودیت استفاده از این ویژگی به پایان رسیده است. حداکثر {limit} کاربر می‌توانند از آن استفاده کنند."


class FeatureCacheError(MyBotError):
    """
    خطای کش ویژگی.

    این استثنا زمانی رخ می‌دهد که مشکلی در کش کردن یا بازیابی
    وضعیت ویژگی‌ها از کش وجود داشته باشد.
    """

    def __init__(
        self,
        operation: str,
        feature_name: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای کش ویژگی.

        Args:
            operation: نوع عملیات ('set', 'get', 'delete').
            feature_name: نام ویژگی (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در کش ویژگی‌ها هنگام عملیات '{operation}'."
        if feature_name:
            message += f" ویژگی: {feature_name}"
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["operation"] = operation
        if feature_name:
            context["feature_name"] = feature_name
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FEATURE_CACHE_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در سیستم کش ویژگی‌ها وجود دارد. لطفاً دوباره تلاش کنید."


__all__ = [
    "FeatureDisabledError",
    "FeatureNotFoundError",
    "FeatureAccessDeniedError",
    "FeatureToggleError",
    "FeatureStorageError",
    "FeatureDependencyError",
    "FeatureValidationError",
    "FeatureExpiredError",
    "FeatureLimitExceededError",
    "FeatureCacheError",
]