# my_bot_project/src/my_bot/core/exceptions/form_errors.py
"""
استثناهای مربوط به پردازش فرم‌ها (Form Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان ایجاد، پر کردن،
اعتبارسنجی، ارسال و پردازش فرم‌های پویا در سیستم رخ می‌دهند.
"""

from typing import Any, Dict, List, Optional

from my_bot.core.exceptions.base import MyBotError


class FormProcessingError(MyBotError):
    """
    خطای عمومی مربوط به پردازش فرم.

    این استثنا زمانی رخ می‌دهد که مشکلی در فرآیند پردازش فرم وجود داشته باشد.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای پردازش فرم.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'FORM_PROCESSING_ERROR').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "FORM_PROCESSING_ERROR"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "مشکلی در پردازش فرم وجود دارد. لطفاً دوباره تلاش کنید."


class FormNotFoundError(FormProcessingError):
    """
    خطای عدم وجود فرم.

    این استثنا زمانی رخ می‌دهد که فرم درخواستی با شناسه مشخص در سیستم وجود نداشته باشد.
    """

    def __init__(
        self,
        form_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای عدم وجود فرم.

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
        return "فرم مورد نظر یافت نشد. ممکن است حذف شده یا منقضی شده باشد."


class FormInactiveError(FormProcessingError):
    """
    خطای غیرفعال بودن فرم.

    این استثنا زمانی رخ می‌دهد که فرم درخواستی غیرفعال است و کاربر نمی‌تواند آن را پر کند.
    """

    def __init__(
        self,
        form_id: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای غیرفعال بودن فرم.

        Args:
            form_id: شناسه فرم.
            reason: دلیل غیرفعال بودن (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"فرم با شناسه '{form_id}' غیرفعال است."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["form_id"] = form_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FORM_INACTIVE", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "این فرم در حال حاضر غیرفعال است و نمی‌توانید آن را پر کنید."


class FormExpiredError(FormProcessingError):
    """
    خطای منقضی شدن فرم.

    این استثنا زمانی رخ می‌دهد که زمان مجاز برای پر کردن فرم به پایان رسیده باشد.
    """

    def __init__(
        self,
        form_id: str,
        expired_at: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای منقضی شدن فرم.

        Args:
            form_id: شناسه فرم.
            expired_at: زمان انقضا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"فرم با شناسه '{form_id}' منقضی شده است."
        if expired_at:
            message += f" زمان انقضا: {expired_at}"

        context = context or {}
        context["form_id"] = form_id
        if expired_at:
            context["expired_at"] = expired_at

        super().__init__(message, error_code="FORM_EXPIRED", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "زمان پر کردن این فرم به پایان رسیده است."


class FormValidationError(FormProcessingError):
    """
    خطای اعتبارسنجی فرم.

    این استثنا زمانی رخ می‌دهد که داده‌های وارد شده در فرم با قوانین اعتبارسنجی مطابقت نداشته باشند.
    """

    def __init__(
        self,
        form_id: str,
        errors: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای اعتبارسنجی فرم.

        Args:
            form_id: شناسه فرم.
            errors: لیست خطاهای اعتبارسنجی.
            context: اطلاعات زمینه‌ای اضافی.
        """
        error_messages = [e.get("message", "خطای ناشناخته") for e in errors]
        message = f"خطاهای اعتبارسنجی در فرم '{form_id}': {', '.join(error_messages)}"

        context = context or {}
        context["form_id"] = form_id
        context["errors"] = errors
        context["errors_count"] = len(errors)

        super().__init__(message, error_code="FORM_VALIDATION_ERROR", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند با تفکیک خطاها.
        """
        lines = ["خطاهای زیر در فرم وجود دارد:"]
        for i, error in enumerate(self.context.get("errors", []), 1):
            field = error.get("field", "نامشخص")
            msg = error.get("message", "خطا")
            lines.append(f"{i}. فیلد '{field}': {msg}")
        return "\n".join(lines)


class FormFieldError(FormValidationError):
    """
    خطای فیلد خاص در فرم.

    این استثنا برای نمایش خطای یک فیلد خاص در فرم استفاده می‌شود.
    """

    def __init__(
        self,
        form_id: str,
        field_name: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای فیلد فرم.

        Args:
            form_id: شناسه فرم.
            field_name: نام فیلد.
            error_message: پیام خطای فیلد.
            context: اطلاعات زمینه‌ای اضافی.
        """
        errors = [{"field": field_name, "message": error_message}]
        super().__init__(form_id, errors, context)

        # اضافه کردن اطلاعات فیلد به context
        self.context["field_name"] = field_name
        self.context["error_message"] = error_message


class FormSubmissionError(FormProcessingError):
    """
    خطای ارسال فرم.

    این استثنا زمانی رخ می‌دهد که مشکلی در فرآیند ارسال و ذخیره‌سازی فرم وجود داشته باشد.
    """

    def __init__(
        self,
        form_id: str,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ارسال فرم.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در ارسال فرم '{form_id}'."
        if reason:
            message += f" دلیل: {reason}"
        if user_id:
            message += f" (کاربر: {user_id})"

        context = context or {}
        context["form_id"] = form_id
        if user_id:
            context["user_id"] = user_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FORM_SUBMISSION_ERROR", context=context)


class FormBuildError(FormProcessingError):
    """
    خطای ساخت فرم.

    این استثنا زمانی رخ می‌دهد که مشکلی در فرآیند ساخت یا تعریف فرم وجود داشته باشد.
    """

    def __init__(
        self,
        form_id: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ساخت فرم.

        Args:
            form_id: شناسه فرم (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = "خطا در ساخت فرم."
        if form_id:
            message += f" شناسه فرم: {form_id}"
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        if form_id:
            context["form_id"] = form_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FORM_BUILD_ERROR", context=context)


class FormAccessDeniedError(FormProcessingError):
    """
    خطای دسترسی به فرم.

    این استثنا زمانی رخ می‌دهد که کاربر مجوز دسترسی یا پر کردن فرم را نداشته باشد.
    """

    def __init__(
        self,
        form_id: str,
        user_id: int,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای دسترسی به فرم.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.
            reason: دلیل عدم دسترسی (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"کاربر {user_id} به فرم '{form_id}' دسترسی ندارد."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["form_id"] = form_id
        context["user_id"] = user_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FORM_ACCESS_DENIED", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "شما مجوز پر کردن این فرم را ندارید."


class FormStateError(FormProcessingError):
    """
    خطای وضعیت فرم.

    این استثنا زمانی رخ می‌دهد که عملیات روی فرم با وضعیت فعلی آن سازگاری نداشته باشد.
    """

    def __init__(
        self,
        form_id: str,
        current_state: str,
        expected_state: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای وضعیت فرم.

        Args:
            form_id: شناسه فرم.
            current_state: وضعیت فعلی فرم.
            expected_state: وضعیت مورد انتظار (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"وضعیت فعلی فرم '{form_id}' ({current_state}) اجازه این عملیات را نمی‌دهد."
        if expected_state:
            message += f" وضعیت مورد انتظار: {expected_state}"

        context = context or {}
        context["form_id"] = form_id
        context["current_state"] = current_state
        if expected_state:
            context["expected_state"] = expected_state

        super().__init__(message, error_code="FORM_STATE_ERROR", context=context)


class FormDuplicateError(FormProcessingError):
    """
    خطای فرم تکراری.

    این استثنا زمانی رخ می‌دهد که کاربر تلاش به ثبت فرمی کند که قبلاً ثبت کرده است.
    """

    def __init__(
        self,
        form_id: str,
        user_id: int,
        existing_response_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای فرم تکراری.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.
            existing_response_id: شناسه پاسخ قبلی (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"کاربر {user_id} قبلاً فرم '{form_id}' را ثبت کرده است."
        if existing_response_id:
            message += f" شناسه پاسخ قبلی: {existing_response_id}"

        context = context or {}
        context["form_id"] = form_id
        context["user_id"] = user_id
        if existing_response_id:
            context["existing_response_id"] = existing_response_id

        super().__init__(message, error_code="FORM_DUPLICATE", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "شما قبلاً این فرم را ثبت کرده‌اید و نمی‌توانید دوباره ثبت کنید."


class FormTemplateError(FormProcessingError):
    """
    خطای قالب فرم.

    این استثنا زمانی رخ می‌دهد که مشکلی در قالب یا ساختار تعریف‌شده برای فرم وجود داشته باشد.
    """

    def __init__(
        self,
        template_id: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای قالب فرم.

        Args:
            template_id: شناسه قالب.
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در قالب فرم '{template_id}'."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["template_id"] = template_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FORM_TEMPLATE_ERROR", context=context)


class FormAnswerError(FormProcessingError):
    """
    خطای پاسخ به فرم.

    این استثنا زمانی رخ می‌دهد که مشکل در ذخیره‌سازی یا بازیابی پاسخ‌های فرم وجود داشته باشد.
    """

    def __init__(
        self,
        form_id: str,
        response_id: Optional[str] = None,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای پاسخ فرم.

        Args:
            form_id: شناسه فرم.
            response_id: شناسه پاسخ (اختیاری).
            reason: دلیل خطا (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"خطا در پاسخ‌دهی به فرم '{form_id}'."
        if response_id:
            message += f" شناسه پاسخ: {response_id}"
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["form_id"] = form_id
        if response_id:
            context["response_id"] = response_id
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="FORM_ANSWER_ERROR", context=context)


__all__ = [
    "FormProcessingError",
    "FormNotFoundError",
    "FormInactiveError",
    "FormExpiredError",
    "FormValidationError",
    "FormFieldError",
    "FormSubmissionError",
    "FormBuildError",
    "FormAccessDeniedError",
    "FormStateError",
    "FormDuplicateError",
    "FormTemplateError",
    "FormAnswerError",
]