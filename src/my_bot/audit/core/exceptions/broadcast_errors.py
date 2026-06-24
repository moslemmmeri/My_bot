# my_bot_project/src/my_bot/core/exceptions/broadcast_errors.py
"""
استثناهای مربوط به ارسال گروهی پیام (Broadcast Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان ارسال پیام‌های گروهی،
فیلتر کردن کاربران، زمان‌بندی، لغو و سایر عملیات‌های مرتبط با Broadcast رخ می‌دهند.
"""

from typing import Any, Dict, List, Optional

from my_bot.core.exceptions.base import MyBotError


class BroadcastError(MyBotError):
    """
    خطای عمومی مربوط به ارسال گروهی پیام.

    این استثنا زمانی رخ می‌دهد که مشکلی در فرآیند ارسال گروهی پیام وجود داشته باشد.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای Broadcast.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'BROADCAST_ERROR').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "BROADCAST_ERROR"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در ارسال پیام گروهی وجود دارد. لطفاً دوباره تلاش کنید."


class BroadcastNotFoundError(BroadcastError):
    """
    خطای عدم وجود Broadcast.

    این استثنا زمانی رخ می‌دهد که پیام گروهی درخواستی با شناسه مشخص در سیستم وجود نداشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم وجود Broadcast.

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


class BroadcastSendingError(BroadcastError):
    """
    خطای ارسال Broadcast.

    این استثنا زمانی رخ می‌دهد که مشکلی در ارسال پیام به کاربران وجود داشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        target_count: int,
        failed_count: int,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ارسال Broadcast.

        Args:
            broadcast_id: شناسه پیام گروهی.
            target_count: تعداد کل کاربران هدف.
            failed_count: تعداد ارسال‌های ناموفق.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = (
            f"خطا در ارسال پیام گروهی '{broadcast_id}'. "
            f"{failed_count} از {target_count} ارسال ناموفق بود."
        )
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        context["target_count"] = target_count
        context["failed_count"] = failed_count
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_SENDING_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        failed_count = self.context.get("failed_count", 0)
        target_count = self.context.get("target_count", 0)
        if failed_count == target_count:
            return "ارسال پیام گروهی کاملاً ناموفق بود. لطفاً دوباره تلاش کنید."
        return (
            f"ارسال پیام گروهی با {failed_count} خطا مواجه شد. "
            f"لطفاً گزارش کامل را بررسی کنید."
        )


class BroadcastFilterError(BroadcastError):
    """
    خطای فیلتر کردن کاربران در Broadcast.

    این استثنا زمانی رخ می‌دهد که مشکلی در اعمال فیلترها برای انتخاب
    کاربران هدف وجود داشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        filter_criteria: Dict[str, Any],
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای فیلتر Broadcast.

        Args:
            broadcast_id: شناسه پیام گروهی.
            filter_criteria: معیارهای فیلتر.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در اعمال فیلترها برای پیام گروهی '{broadcast_id}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        context["filter_criteria"] = filter_criteria
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_FILTER_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "خطا در اعمال فیلترهای انتخاب کاربران. لطفاً معیارهای فیلتر را بررسی کنید."


class BroadcastScheduleError(BroadcastError):
    """
    خطای زمان‌بندی Broadcast.

    این استثنا زمانی رخ می‌دهد که مشکلی در زمان‌بندی ارسال پیام گروهی وجود داشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        scheduled_time: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای زمان‌بندی Broadcast.

        Args:
            broadcast_id: شناسه پیام گروهی.
            scheduled_time: زمان برنامه‌ریزی‌شده.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در زمان‌بندی پیام گروهی '{broadcast_id}' برای زمان '{scheduled_time}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        context["scheduled_time"] = scheduled_time
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_SCHEDULE_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "خطا در زمان‌بندی پیام گروهی. لطفاً تاریخ و زمان را بررسی کنید."


class BroadcastCancelError(BroadcastError):
    """
    خطای لغو Broadcast.

    این استثنا زمانی رخ می‌دهد که مشکلی در لغو ارسال پیام گروهی وجود داشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        status: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای لغو Broadcast.

        Args:
            broadcast_id: شناسه پیام گروهی.
            status: وضعیت فعلی پیام.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در لغو پیام گروهی '{broadcast_id}'. وضعیت فعلی: {status}"
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        context["current_status"] = status
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_CANCEL_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "خطا در لغو پیام گروهی. ممکن است پیام در حال ارسال باشد یا قبلاً لغو شده باشد."


class BroadcastRateLimitError(BroadcastError):
    """
    خطای محدودیت نرخ در ارسال گروهی.

    این استثنا زمانی رخ می‌دهد که سرعت ارسال پیام از حد مجاز فراتر رود.
    """

    def __init__(
        self,
        broadcast_id: str,
        max_rate: int,
        current_rate: int,
        retry_after_seconds: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای محدودیت نرخ.

        Args:
            broadcast_id: شناسه پیام گروهی.
            max_rate: حداکثر نرخ مجاز (پیام در ثانیه).
            current_rate: نرخ فعلی.
            retry_after_seconds: زمان انتظار برای تلاش مجدد (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = (
            f"محدودیت نرخ ارسال برای پیام گروهی '{broadcast_id}'. "
            f"حداکثر: {max_rate}، نرخ فعلی: {current_rate}"
        )
        if retry_after_seconds:
            message += f" {retry_after_seconds} ثانیه صبر کنید."

        context = context or {}
        context["broadcast_id"] = broadcast_id
        context["max_rate"] = max_rate
        context["current_rate"] = current_rate
        if retry_after_seconds:
            context["retry_after_seconds"] = retry_after_seconds

        super().__init__(message, error_code="BROADCAST_RATE_LIMIT", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        retry_after = self.context.get("retry_after_seconds")
        if retry_after:
            return f"سرعت ارسال بیش از حد مجاز است. {retry_after} ثانیه دیگر تلاش کنید."
        return "سرعت ارسال بیش از حد مجاز است. لطفاً کمی صبر کنید."


class BroadcastTargetError(BroadcastError):
    """
    خطای کاربران هدف در Broadcast.

    این استثنا زمانی رخ می‌دهد که هیچ کاربری برای ارسال پیام وجود نداشته باشد
    یا لیست کاربران هدف خالی باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای کاربران هدف.

        Args:
            broadcast_id: شناسه پیام گروهی.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"هیچ کاربر هدفی برای پیام گروهی '{broadcast_id}' یافت نشد."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_TARGET_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "هیچ کاربری با معیارهای انتخاب‌شده یافت نشد. لطفاً فیلترها را بررسی کنید."


class BroadcastTemplateError(BroadcastError):
    """
    خطای قالب پیام در Broadcast.

    این استثنا زمانی رخ می‌دهد که مشکلی در قالب یا محتوای پیام وجود داشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        template: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای قالب پیام.

        Args:
            broadcast_id: شناسه پیام گروهی.
            template: قالب پیام (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در قالب پیام گروهی '{broadcast_id}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        if template:
            context["template"] = template[:200]  # محدود کردن طول قالب
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_TEMPLATE_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "خطا در قالب پیام. لطفاً محتوای پیام را بررسی کنید."


class BroadcastPermissionsError(BroadcastError):
    """
    خطای عدم دسترسی به Broadcast.

    این استثنا زمانی رخ می‌دهد که کاربر مجوز ارسال پیام گروهی را نداشته باشد.
    """

    def __init__(
        self,
        user_id: int,
        required_role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای دسترسی به Broadcast.

        Args:
            user_id: شناسه کاربر.
            required_role: نقش مورد نیاز (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"کاربر {user_id} مجوز ارسال پیام گروهی را ندارد."
        if required_role:
            message += f" نقش مورد نیاز: {required_role}"

        context = context or {}
        context["user_id"] = user_id
        if required_role:
            context["required_role"] = required_role

        super().__init__(message, error_code="BROADCAST_PERMISSIONS_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "شما مجوز ارسال پیام گروهی را ندارید."


class BroadcastProcessingError(BroadcastError):
    """
    خطای پردازش Broadcast.

    این استثنا زمانی رخ می‌دهد که مشکلی در پردازش کلی Broadcast
    (غیر از مراحل خاص مانند ارسال، فیلتر، و غیره) وجود داشته باشد.
    """

    def __init__(
        self,
        broadcast_id: str,
        step: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای پردازش Broadcast.

        Args:
            broadcast_id: شناسه پیام گروهی.
            step: مرحله‌ای که خطا در آن رخ داده.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در پردازش پیام گروهی '{broadcast_id}' در مرحله '{step}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["broadcast_id"] = broadcast_id
        context["step"] = step
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="BROADCAST_PROCESSING_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "خطا در پردازش پیام گروهی. لطفاً دوباره تلاش کنید."


__all__ = [
    "BroadcastError",
    "BroadcastNotFoundError",
    "BroadcastSendingError",
    "BroadcastFilterError",
    "BroadcastScheduleError",
    "BroadcastCancelError",
    "BroadcastRateLimitError",
    "BroadcastTargetError",
    "BroadcastTemplateError",
    "BroadcastPermissionsError",
    "BroadcastProcessingError",
]