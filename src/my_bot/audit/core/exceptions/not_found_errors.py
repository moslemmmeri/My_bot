# my_bot_project/src/my_bot/core/exceptions/not_found_errors.py
"""
استثناهای مربوط به عدم پیدا شدن موجودیت‌ها (Not Found Errors).

این ماژول شامل کلاس‌های استثنایی است که زمانی رخ می‌دهند که یک موجودیت
(مانند کاربر، سفارش، فرم، محصول، و غیره) با شناسه مشخص در سیستم پیدا نشود.
"""

from typing import Any, Dict, Optional

from my_bot.core.exceptions.base import MyBotError


class NotFoundError(MyBotError):
    """
    خطای عمومی عدم پیدا شدن موجودیت.

    این استثنا زمانی رخ می‌دهد که یک موجودیت با شناسه مشخص
    در سیستم پیدا نشود.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'NOT_FOUND').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "NOT_FOUND"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مورد درخواستی یافت نشد."


class UserNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن کاربر.

    این استثنا زمانی رخ می‌دهد که کاربر با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        username: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن کاربر.

        Args:
            user_id: شناسه کاربر در سیستم (اختیاری).
            telegram_id: شناسه تلگرام کاربر (اختیاری).
            username: نام کاربری (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        if user_id is not None:
            message = f"کاربر با شناسه '{user_id}' یافت نشد."
        elif telegram_id is not None:
            message = f"کاربر با شناسه تلگرام '{telegram_id}' یافت نشد."
        elif username is not None:
            message = f"کاربر با نام کاربری '{username}' یافت نشد."
        else:
            message = "کاربر مورد نظر یافت نشد."

        context = context or {}
        if user_id is not None:
            context["user_id"] = user_id
        if telegram_id is not None:
            context["telegram_id"] = telegram_id
        if username is not None:
            context["username"] = username

        super().__init__(message, error_code="USER_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "کاربر مورد نظر یافت نشد. ممکن است حذف شده باشد."


class OrderNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن سفارش.

    این استثنا زمانی رخ می‌دهد که سفارش با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        order_id: str,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن سفارش.

        Args:
            order_id: شناسه سفارش.
            user_id: شناسه کاربر (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"سفارش با شناسه '{order_id}' یافت نشد."

        context = context or {}
        context["order_id"] = order_id
        if user_id is not None:
            context["user_id"] = user_id

        super().__init__(message, error_code="ORDER_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "سفارش مورد نظر یافت نشد. ممکن است حذف شده باشد."


class FormNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن فرم.

    این استثنا زمانی رخ می‌دهد که فرم با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        form_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن فرم.

        Args:
            form_id: شناسه فرم.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"فرم با شناسه '{form_id}' یافت نشد."

        context = context or {}
        context["form_id"] = form_id

        super().__init__(message, error_code="FORM_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "فرم مورد نظر یافت نشد. ممکن است حذف یا غیرفعال شده باشد."


class PaymentNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن تراکنش پرداخت.

    این استثنا زمانی رخ می‌دهد که تراکنش پرداخت با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        payment_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن تراکنش.

        Args:
            payment_id: شناسه تراکنش.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"تراکنش پرداخت با شناسه '{payment_id}' یافت نشد."

        context = context or {}
        context["payment_id"] = payment_id

        super().__init__(message, error_code="PAYMENT_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "تراکنش پرداخت مورد نظر یافت نشد."


class CouponNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن کوپن.

    این استثنا زمانی رخ می‌دهد که کوپن با کد مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        coupon_code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن کوپن.

        Args:
            coupon_code: کد کوپن.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"کوپن با کد '{coupon_code}' یافت نشد."

        context = context or {}
        context["coupon_code"] = coupon_code

        super().__init__(message, error_code="COUPON_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "کد تخفیف وارد شده معتبر نیست."


class TicketNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن تیکت پشتیبانی.

    این استثنا زمانی رخ می‌دهد که تیکت با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        ticket_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن تیکت.

        Args:
            ticket_id: شناسه تیکت.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"تیکت با شناسه '{ticket_id}' یافت نشد."

        context = context or {}
        context["ticket_id"] = ticket_id

        super().__init__(message, error_code="TICKET_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "تیکت مورد نظر یافت نشد."


class ProductNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن محصول.

    این استثنا زمانی رخ می‌دهد که محصول با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        product_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن محصول.

        Args:
            product_id: شناسه محصول.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"محصول با شناسه '{product_id}' یافت نشد."

        context = context or {}
        context["product_id"] = product_id

        super().__init__(message, error_code="PRODUCT_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "محصول مورد نظر یافت نشد."


class BroadcastNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن پیام گروهی.

    این استثنا زمانی رخ می‌دهد که پیام گروهی با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        broadcast_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن پیام گروهی.

        Args:
            broadcast_id: شناسه پیام گروهی.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"پیام گروهی با شناسه '{broadcast_id}' یافت نشد."

        context = context or {}
        context["broadcast_id"] = broadcast_id

        super().__init__(message, error_code="BROADCAST_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "پیام گروهی مورد نظر یافت نشد."


class FeedbackNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن بازخورد.

    این استثنا زمانی رخ می‌دهد که بازخورد با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        feedback_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن بازخورد.

        Args:
            feedback_id: شناسه بازخورد.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"بازخورد با شناسه '{feedback_id}' یافت نشد."

        context = context or {}
        context["feedback_id"] = feedback_id

        super().__init__(message, error_code="FEEDBACK_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "بازخورد مورد نظر یافت نشد."


class AuditLogNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن لاگ حسابرسی.

    این استثنا زمانی رخ می‌دهد که لاگ حسابرسی با شناسه مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        log_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن لاگ حسابرسی.

        Args:
            log_id: شناسه لاگ.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"لاگ حسابرسی با شناسه '{log_id}' یافت نشد."

        context = context or {}
        context["log_id"] = log_id

        super().__init__(message, error_code="AUDIT_LOG_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "لاگ حسابرسی مورد نظر یافت نشد."


class SettingNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن تنظیمات.

    این استثنا زمانی رخ می‌دهد که یک تنظیمات با کلید مشخص در سیستم پیدا نشود.
    """

    def __init__(
        self,
        setting_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن تنظیمات.

        Args:
            setting_key: کلید تنظیمات.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"تنظیمات با کلید '{setting_key}' یافت نشد."

        context = context or {}
        context["setting_key"] = setting_key

        super().__init__(message, error_code="SETTING_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "تنظیمات مورد نظر یافت نشد."


class ResourceNotFoundError(NotFoundError):
    """
    خطای عدم پیدا شدن منبع عمومی.

    این استثنا برای مواردی استفاده می‌شود که نوع موجودیت مشخص نیست
    یا برای موجودیت‌های سفارشی که کلاس خاصی برای آنها تعریف نشده است.
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم پیدا شدن منبع.

        Args:
            resource_type: نوع منبع.
            resource_id: شناسه منبع.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"{resource_type} با شناسه '{resource_id}' یافت نشد."

        context = context or {}
        context["resource_type"] = resource_type
        context["resource_id"] = resource_id

        super().__init__(message, error_code="RESOURCE_NOT_FOUND", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        resource_type = self.context.get("resource_type", "مورد")
        return f"{resource_type} مورد نظر یافت نشد."


__all__ = [
    "NotFoundError",
    "UserNotFoundError",
    "OrderNotFoundError",
    "FormNotFoundError",
    "PaymentNotFoundError",
    "CouponNotFoundError",
    "TicketNotFoundError",
    "ProductNotFoundError",
    "BroadcastNotFoundError",
    "FeedbackNotFoundError",
    "AuditLogNotFoundError",
    "SettingNotFoundError",
    "ResourceNotFoundError",
]