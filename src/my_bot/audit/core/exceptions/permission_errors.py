# my_bot_project/src/my_bot/core/exceptions/permission_errors.py
"""
استثناهای مربوط به دسترسی و مجوزها (Permission Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان بررسی مجوزهای دسترسی،
نقش‌های کاربری، مالکیت منابع و سایر موارد مرتبط با امنیت رخ می‌دهند.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class PermissionDeniedError(MyBotError):
    """
    خطای عمومی مربوط به عدم دسترسی.

    این استثنا زمانی رخ می‌دهد که کاربر تلاش به انجام عملیاتی کند
    که مجوز انجام آن را ندارد.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم دسترسی.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'PERMISSION_DENIED').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "PERMISSION_DENIED"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "شما مجوز انجام این عملیات را ندارید."


class AdminRequiredError(PermissionDeniedError):
    """
    خطای نیاز به دسترسی ادمین.

    این استثنا زمانی رخ می‌دهد که کاربر برای انجام عملیات نیاز به سطح دسترسی ادمین دارد.
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        required_role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای نیاز به ادمین.

        Args:
            user_id: شناسه کاربر (اختیاری).
            required_role: نقش مورد نیاز (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "این عملیات نیاز به دسترسی ادمین دارد."
        if required_role:
            message += f" نقش مورد نیاز: {required_role}"

        context = context or {}
        if user_id:
            context["user_id"] = user_id
        if required_role:
            context["required_role"] = required_role

        super().__init__(message, error_code="ADMIN_REQUIRED", context=context)


class RoleRequiredError(PermissionDeniedError):
    """
    خطای نیاز به نقش خاص.

    این استثنا زمانی رخ می‌دهد که کاربر برای انجام عملیات نیاز به نقش مشخصی دارد.
    """

    def __init__(
        self,
        required_roles: list[str],
        user_role: Optional[str] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای نیاز به نقش.

        Args:
            required_roles: لیست نقش‌های مورد نیاز.
            user_role: نقش فعلی کاربر (اختیاری).
            user_id: شناسه کاربر (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"این عملیات نیاز به یکی از نقش‌های زیر دارد: {', '.join(required_roles)}"
        if user_role:
            message += f" نقش فعلی شما: {user_role}"

        context = context or {}
        context["required_roles"] = required_roles
        if user_role:
            context["user_role"] = user_role
        if user_id:
            context["user_id"] = user_id

        super().__init__(message, error_code="ROLE_REQUIRED", context=context)


class ResourceAccessError(PermissionDeniedError):
    """
    خطای دسترسی به منبع.

    این استثنا زمانی رخ می‌دهد که کاربر تلاش به دسترسی به منبعی (مانند فایل، دیتا، یا صفحه)
    کند که مجوز دسترسی به آن را ندارد.
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای دسترسی به منبع.

        Args:
            resource_type: نوع منبع (مانند 'user', 'order', 'form').
            resource_id: شناسه منبع (اختیاری).
            user_id: شناسه کاربر (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"شما به منبع '{resource_type}' دسترسی ندارید."
        if resource_id:
            message += f" شناسه: {resource_id}"

        context = context or {}
        context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id
        if user_id:
            context["user_id"] = user_id

        super().__init__(message, error_code="RESOURCE_ACCESS_DENIED", context=context)


class OwnershipError(PermissionDeniedError):
    """
    خطای مالکیت.

    این استثنا زمانی رخ می‌دهد که کاربر تلاش به ویرایش یا حذف منبعی کند
    که مالک آن نیست (و اجازه‌ی انجام این کار را ندارد).
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: Optional[int] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای مالکیت.

        Args:
            resource_type: نوع منبع.
            resource_id: شناسه منبع.
            owner_id: شناسه مالک منبع (اختیاری).
            user_id: شناسه کاربر درخواست‌دهنده (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"شما مالک منبع '{resource_type}' با شناسه '{resource_id}' نیستید."

        context = context or {}
        context["resource_type"] = resource_type
        context["resource_id"] = resource_id
        if owner_id:
            context["owner_id"] = owner_id
        if user_id:
            context["user_id"] = user_id

        super().__init__(message, error_code="OWNERSHIP_ERROR", context=context)


class FeatureAccessError(PermissionDeniedError):
    """
    خطای دسترسی به ویژگی (Feature).

    این استثنا زمانی رخ می‌دهد که کاربر تلاش به استفاده از ویژگی‌ای کند
    که برای او فعال نشده است یا به آن دسترسی ندارد.
    """

    def __init__(
        self,
        feature_name: str,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای دسترسی به ویژگی.

        Args:
            feature_name: نام ویژگی.
            user_id: شناسه کاربر (اختیاری).
            reason: دلیل عدم دسترسی (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"شما به ویژگی '{feature_name}' دسترسی ندارید."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["feature_name"] = feature_name
        if user_id:
            context["user_id"] = user_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FEATURE_ACCESS_DENIED", context=context)


class InvalidTokenError(PermissionDeniedError):
    """
    خطای توکن نامعتبر یا منقضی.

    این استثنا زمانی رخ می‌دهد که توکن احراز هویت کاربر نامعتبر یا منقضی شده باشد.
    """

    def __init__(
        self,
        reason: Optional[str] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای توکن نامعتبر.

        Args:
            reason: دلیل نامعتبر بودن (اختیاری).
            user_id: شناسه کاربر (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "توکن احراز هویت نامعتبر یا منقضی شده است."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        if reason:
            context["reason"] = reason
        if user_id:
            context["user_id"] = user_id

        super().__init__(message, error_code="INVALID_TOKEN", context=context)


__all__ = [
    "PermissionDeniedError",
    "AdminRequiredError",
    "RoleRequiredError",
    "ResourceAccessError",
    "OwnershipError",
    "FeatureAccessError",
    "InvalidTokenError",
]