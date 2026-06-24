# my_bot_project/src/my_bot/core/exceptions/validation_errors.py
"""
استثناهای مربوط به اعتبارسنجی داده‌ها (Validation Errors).

این ماژول شامل کلاس‌های استثنایی است که در زمان اعتبارسنجی ورودی‌ها،
پارامترها، داده‌های فرم، DTOها و سایر داده‌های دریافتی از کاربر یا سیستم‌های خارجی رخ می‌دهند.
"""

from typing import Any, Dict, List, Optional

from my_bot.core.exceptions.base import MyBotError


class ValidationError(MyBotError):
    """
    خطای عمومی مربوط به اعتبارسنجی.

    این استثنا زمانی رخ می‌دهد که داده‌های ورودی با قوانین اعتبارسنجی مطابقت نداشته باشند.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای اعتبارسنجی.

        Args:
            message: پیام خطا.
            error_code: کد خطای اختیاری (پیش‌فرض: 'VALIDATION_ERROR').
            context: اطلاعات زمینه‌ای اضافی.
        """
        if error_code is None:
            error_code = "VALIDATION_ERROR"
        super().__init__(message, error_code, context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند.
        """
        return "داده‌های وارد شده معتبر نیستند. لطفاً دوباره بررسی کنید."


class InvalidInputError(ValidationError):
    """
    خطای ورودی نامعتبر.

    این استثنا زمانی رخ می‌دهد که ورودی از نظر نوع، فرمت یا مقدار نامعتبر باشد.
    """

    def __init__(
        self,
        field: str,
        value: Any,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای ورودی نامعتبر.

        Args:
            field: نام فیلد ورودی.
            value: مقدار ورودی.
            reason: دلیل نامعتبر بودن (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"ورودی '{field}' با مقدار '{value}' نامعتبر است."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["field"] = field
        context["value"] = str(value)
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="INVALID_INPUT", context=context)


class MissingFieldError(ValidationError):
    """
    خطای عدم وجود فیلد اجباری.

    این استثنا زمانی رخ می‌دهد که یک فیلد اجباری در داده‌های ورودی وجود نداشته باشد.
    """

    def __init__(
        self,
        field: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای فیلد اجباری.

        Args:
            field: نام فیلد اجباری.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"فیلد اجباری '{field}' در داده‌ها وجود ندارد."

        context = context or {}
        context["field"] = field

        super().__init__(message, error_code="MISSING_FIELD", context=context)


class InvalidFormatError(ValidationError):
    """
    خطای فرمت نامعتبر.

    این استثنا زمانی رخ می‌دهد که داده‌های ورودی فرمت مورد انتظار را نداشته باشند
    (مانند فرمت ایمیل، شماره تلفن، تاریخ و ...).
    """

    def __init__(
        self,
        field: str,
        expected_format: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای فرمت نامعتبر.

        Args:
            field: نام فیلد.
            expected_format: فرمت مورد انتظار.
            value: مقدار ورودی.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"فرمت فیلد '{field}' نامعتبر است. فرمت صحیح: {expected_format}"

        context = context or {}
        context["field"] = field
        context["expected_format"] = expected_format
        context["value"] = str(value)

        super().__init__(message, error_code="INVALID_FORMAT", context=context)


class InvalidChoiceError(ValidationError):
    """
    خطای انتخاب نامعتبر.

    این استثنا زمانی رخ می‌دهد که مقدار انتخاب شده در گزینه‌های مجاز نباشد.
    """

    def __init__(
        self,
        field: str,
        value: Any,
        choices: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای انتخاب نامعتبر.

        Args:
            field: نام فیلد.
            value: مقدار انتخاب شده.
            choices: لیست گزینه‌های مجاز.
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"مقدار '{value}' برای فیلد '{field}' معتبر نیست. گزینه‌های مجاز: {', '.join(map(str, choices))}"

        context = context or {}
        context["field"] = field
        context["value"] = str(value)
        context["choices"] = choices

        super().__init__(message, error_code="INVALID_CHOICE", context=context)


class LengthError(ValidationError):
    """
    خطای طول رشته.

    این استثنا زمانی رخ می‌دهد که طول یک رشته ورودی کمتر یا بیشتر از حد مجاز باشد.
    """

    def __init__(
        self,
        field: str,
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای طول.

        Args:
            field: نام فیلد.
            value: مقدار ورودی.
            min_length: حداقل طول مجاز (اختیاری).
            max_length: حداکثر طول مجاز (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"طول فیلد '{field}' نامعتبر است."
        if min_length is not None and max_length is not None:
            message += f" طول باید بین {min_length} و {max_length} باشد."
        elif min_length is not None:
            message += f" طول باید حداقل {min_length} باشد."
        elif max_length is not None:
            message += f" طول باید حداکثر {max_length} باشد."

        context = context or {}
        context["field"] = field
        context["value"] = value
        if min_length is not None:
            context["min_length"] = min_length
        if max_length is not None:
            context["max_length"] = max_length

        super().__init__(message, error_code="LENGTH_ERROR", context=context)


class RangeError(ValidationError):
    """
    خطای بازه عددی.

    این استثنا زمانی رخ می‌دهد که مقدار عددی ورودی خارج از بازه مجاز باشد.
    """

    def __init__(
        self,
        field: str,
        value: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای بازه.

        Args:
            field: نام فیلد.
            value: مقدار ورودی.
            min_value: حداقل مقدار مجاز (اختیاری).
            max_value: حداکثر مقدار مجاز (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"مقدار '{value}' برای فیلد '{field}' خارج از بازه مجاز است."
        if min_value is not None and max_value is not None:
            message += f" مقدار باید بین {min_value} و {max_value} باشد."
        elif min_value is not None:
            message += f" مقدار باید حداقل {min_value} باشد."
        elif max_value is not None:
            message += f" مقدار باید حداکثر {max_value} باشد."

        context = context or {}
        context["field"] = field
        context["value"] = value
        if min_value is not None:
            context["min_value"] = min_value
        if max_value is not None:
            context["max_value"] = max_value

        super().__init__(message, error_code="RANGE_ERROR", context=context)


class ValidationRuleError(ValidationError):
    """
    خطای قانون اعتبارسنجی سفارشی.

    این استثنا زمانی رخ می‌دهد که یک قانون اعتبارسنجی سفارشی نقض شود.
    """

    def __init__(
        self,
        rule_name: str,
        field: str,
        value: Any,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای قانون اعتبارسنجی.

        Args:
            rule_name: نام قانون اعتبارسنجی.
            field: نام فیلد.
            value: مقدار ورودی.
            reason: دلیل نقض قانون (اختیاری).
            context: اطلاعات زمینه‌ای اضافی.
        """
        message = f"قانون اعتبارسنجی '{rule_name}' برای فیلد '{field}' نقض شد."
        if reason:
            message += f" دلیل: {reason}"

        context = context or {}
        context["rule_name"] = rule_name
        context["field"] = field
        context["value"] = str(value)
        if reason:
            context["reason"] = reason

        super().__init__(message, error_code="VALIDATION_RULE_ERROR", context=context)


class MultipleValidationErrors(ValidationError):
    """
    خطای چندین خطای اعتبارسنجی همزمان.

    این استثنا زمانی رخ می‌دهد که در یک عملیات، چندین خطای اعتبارسنجی وجود داشته باشد.
    """

    def __init__(
        self,
        errors: List[ValidationError],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        مقداردهی اولیه استثنای چندین خطا.

        Args:
            errors: لیست خطاهای اعتبارسنجی.
            context: اطلاعات زمینه‌ای اضافی.
        """
        messages = [str(e) for e in errors]
        message = f"چندین خطای اعتبارسنجی رخ داده است: {', '.join(messages)}"

        context = context or {}
        context["errors_count"] = len(errors)
        context["errors"] = [e.to_dict() for e in errors]

        super().__init__(message, error_code="MULTIPLE_VALIDATION_ERRORS", context=context)

    def get_user_friendly_message(self) -> str:
        """
        دریافت پیام خطای مناسب برای نمایش به کاربر.

        Returns:
            پیام خطای کاربرپسند با تفکیک خطاها.
        """
        lines = ["خطاهای زیر در داده‌های ورودی وجود دارد:"]
        for i, error in enumerate(self.context.get("errors", []), 1):
            lines.append(f"{i}. {error.get('error', 'خطا')}")
        return "\n".join(lines)


__all__ = [
    "ValidationError",
    "InvalidInputError",
    "MissingFieldError",
    "InvalidFormatError",
    "InvalidChoiceError",
    "LengthError",
    "RangeError",
    "ValidationRuleError",
    "MultipleValidationErrors",
]