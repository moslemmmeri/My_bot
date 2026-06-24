# my_bot_project/src/my_bot/shared/utils/text_validators.py
"""
اعتبارسنجی متن (Text Validators).

این ماژول شامل توابع کمکی برای اعتبارسنجی انواع مختلف متن‌ها مانند
ایمیل، شماره تلفن، آدرس اینترنتی، تاریخ، زمان، کد رنگ و الگوهای regex است.
"""

import re
from typing import Optional, Pattern, Any
from datetime import datetime

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


# ==========================================
# الگوهای اعتبارسنجی (Regex Patterns)
# ==========================================

# الگوی ایمیل (ساده‌شده بر اساس RFC 5322)
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# الگوی شماره تلفن بین‌المللی (E.164)
PHONE_INTERNATIONAL_PATTERN = re.compile(r"^\+[1-9][0-9]{1,14}$")

# الگوی شماره تلفن ایران
PHONE_IRAN_PATTERNS = [
    re.compile(r"^0?9[0-9]{9}$"),      # 09121234567 یا 9121234567
    re.compile(r"^\+989[0-9]{9}$"),    # +989121234567
]

# الگوی URL (ساده‌شده)
URL_PATTERN = re.compile(
    r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
)

# الگوی تاریخ (YYYY-MM-DD)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# الگوی زمان (HH:MM)
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")

# الگوی کد رنگ HEX (با یا بدون #)
COLOR_PATTERN = re.compile(r"^#?[0-9a-fA-F]{6}$")


# ==========================================
# توابع اعتبارسنجی
# ==========================================

def validate_email(email: str) -> bool:
    """
    اعتبارسنجی آدرس ایمیل.

    Args:
        email: آدرس ایمیل.

    Returns:
        bool: True اگر ایمیل معتبر باشد.

    Raises:
        ValidationError: اگر ایمیل نامعتبر باشد.
    """
    if not email or not email.strip():
        raise ValidationError(
            message="آدرس ایمیل نمی‌تواند خالی باشد.",
            context={"email": email},
        )

    cleaned = email.strip().lower()
    if not EMAIL_PATTERN.match(cleaned):
        raise ValidationError(
            message=f"آدرس ایمیل '{email}' معتبر نیست.",
            context={"email": email},
        )

    return True


def validate_phone(phone: str, allow_international: bool = True) -> bool:
    """
    اعتبارسنجی شماره تلفن.

    Args:
        phone: شماره تلفن.
        allow_international: آیا فرمت بین‌المللی مجاز است (پیش‌فرض True).

    Returns:
        bool: True اگر شماره تلفن معتبر باشد.

    Raises:
        ValidationError: اگر شماره تلفن نامعتبر باشد.
    """
    if not phone or not phone.strip():
        raise ValidationError(
            message="شماره تلفن نمی‌تواند خالی باشد.",
            context={"phone": phone},
        )

    cleaned = re.sub(r"[\s\-()/]", "", phone)

    # بررسی فرمت بین‌المللی
    if allow_international and PHONE_INTERNATIONAL_PATTERN.match(cleaned):
        return True

    # بررسی فرمت‌های ایران
    for pattern in PHONE_IRAN_PATTERNS:
        if pattern.match(cleaned):
            return True

    raise ValidationError(
        message=f"شماره تلفن '{phone}' معتبر نیست.",
        context={"phone": phone},
    )


def validate_url(url: str) -> bool:
    """
    اعتبارسنجی آدرس اینترنتی (URL).

    Args:
        url: آدرس اینترنتی.

    Returns:
        bool: True اگر URL معتبر باشد.

    Raises:
        ValidationError: اگر URL نامعتبر باشد.
    """
    if not url or not url.strip():
        raise ValidationError(
            message="آدرس اینترنتی نمی‌تواند خالی باشد.",
            context={"url": url},
        )

    cleaned = url.strip()
    if not URL_PATTERN.match(cleaned):
        raise ValidationError(
            message=f"آدرس اینترنتی '{url}' معتبر نیست.",
            context={"url": url},
        )

    return True


def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    اعتبارسنجی تاریخ.

    Args:
        date_str: رشته تاریخ.
        format: فرمت تاریخ (پیش‌فرض: %Y-%m-%d).

    Returns:
        bool: True اگر تاریخ معتبر باشد.

    Raises:
        ValidationError: اگر تاریخ نامعتبر باشد.
    """
    if not date_str or not date_str.strip():
        raise ValidationError(
            message="تاریخ نمی‌تواند خالی باشد.",
            context={"date": date_str},
        )

    try:
        datetime.strptime(date_str.strip(), format)
        return True
    except ValueError:
        raise ValidationError(
            message=f"تاریخ '{date_str}' معتبر نیست (فرمت: {format}).",
            context={"date": date_str, "format": format},
        )


def validate_time(time_str: str, format: str = "%H:%M") -> bool:
    """
    اعتبارسنجی زمان.

    Args:
        time_str: رشته زمان.
        format: فرمت زمان (پیش‌فرض: %H:%M).

    Returns:
        bool: True اگر زمان معتبر باشد.

    Raises:
        ValidationError: اگر زمان نامعتبر باشد.
    """
    if not time_str or not time_str.strip():
        raise ValidationError(
            message="زمان نمی‌تواند خالی باشد.",
            context={"time": time_str},
        )

    try:
        datetime.strptime(time_str.strip(), format)
        return True
    except ValueError:
        raise ValidationError(
            message=f"زمان '{time_str}' معتبر نیست (فرمت: {format}).",
            context={"time": time_str, "format": format},
        )


def validate_color(color: str) -> bool:
    """
    اعتبارسنجی کد رنگ HEX.

    Args:
        color: کد رنگ (با یا بدون #).

    Returns:
        bool: True اگر کد رنگ معتبر باشد.

    Raises:
        ValidationError: اگر کد رنگ نامعتبر باشد.
    """
    if not color or not color.strip():
        raise ValidationError(
            message="کد رنگ نمی‌تواند خالی باشد.",
            context={"color": color},
        )

    cleaned = color.strip()
    if not COLOR_PATTERN.match(cleaned):
        raise ValidationError(
            message=f"کد رنگ '{color}' معتبر نیست (فرمت: #RRGGBB).",
            context={"color": color},
        )

    return True


def validate_pattern(text: str, pattern: Pattern, error_message: Optional[str] = None) -> bool:
    """
    اعتبارسنجی یک متن با استفاده از الگوی regex.

    Args:
        text: متن برای اعتبارسنجی.
        pattern: الگوی regex (از نوع re.Pattern).
        error_message: پیام خطای سفارشی (اختیاری).

    Returns:
        bool: True اگر متن با الگو مطابقت داشته باشد.

    Raises:
        ValidationError: اگر متن با الگو مطابقت نداشته باشد.
    """
    if not text or not text.strip():
        raise ValidationError(
            message="متن نمی‌تواند خالی باشد.",
            context={"text": text},
        )

    if not pattern.match(text.strip()):
        msg = error_message or f"متن '{text}' با الگوی تعیین‌شده مطابقت ندارد."
        raise ValidationError(
            message=msg,
            context={"text": text, "pattern": pattern.pattern},
        )

    return True


def validate_length(text: str, min_length: Optional[int] = None, max_length: Optional[int] = None) -> bool:
    """
    اعتبارسنجی طول یک متن.

    Args:
        text: متن برای اعتبارسنجی.
        min_length: حداقل طول مجاز (اختیاری).
        max_length: حداکثر طول مجاز (اختیاری).

    Returns:
        bool: True اگر طول متن در بازه مجاز باشد.

    Raises:
        ValidationError: اگر طول متن خارج از بازه مجاز باشد.
    """
    if text is None:
        raise ValidationError(
            message="متن نمی‌تواند None باشد.",
            context={"text": text},
        )

    length = len(str(text))

    if min_length is not None and length < min_length:
        raise ValidationError(
            message=f"طول متن باید حداقل {min_length} کاراکتر باشد.",
            context={"text": text, "length": length, "min_length": min_length},
        )

    if max_length is not None and length > max_length:
        raise ValidationError(
            message=f"طول متن نباید بیشتر از {max_length} کاراکتر باشد.",
            context={"text": text, "length": length, "max_length": max_length},
        )

    return True


def validate_range(value: Any, min_value: Optional[Any] = None, max_value: Optional[Any] = None) -> bool:
    """
    اعتبارسنجی بازه یک مقدار عددی.

    Args:
        value: مقدار برای اعتبارسنجی.
        min_value: حداقل مقدار مجاز (اختیاری).
        max_value: حداکثر مقدار مجاز (اختیاری).

    Returns:
        bool: True اگر مقدار در بازه مجاز باشد.

    Raises:
        ValidationError: اگر مقدار خارج از بازه مجاز باشد.
    """
    if value is None:
        raise ValidationError(
            message="مقدار نمی‌تواند None باشد.",
            context={"value": value},
        )

    try:
        num_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(
            message=f"مقدار '{value}' باید عدد باشد.",
            context={"value": value},
        )

    if min_value is not None and num_value < min_value:
        raise ValidationError(
            message=f"مقدار باید حداقل {min_value} باشد.",
            context={"value": value, "min_value": min_value},
        )

    if max_value is not None and num_value > max_value:
        raise ValidationError(
            message=f"مقدار نباید بیشتر از {max_value} باشد.",
            context={"value": value, "max_value": max_value},
        )

    return True


def validate_not_empty(text: str, field_name: str = "فیلد") -> bool:
    """
    اعتبارسنجی خالی نبودن یک متن.

    Args:
        text: متن برای اعتبارسنجی.
        field_name: نام فیلد برای نمایش در پیام خطا.

    Returns:
        bool: True اگر متن خالی نباشد.

    Raises:
        ValidationError: اگر متن خالی باشد.
    """
    if text is None or (isinstance(text, str) and not text.strip()):
        raise ValidationError(
            message=f"{field_name} نمی‌تواند خالی باشد.",
            context={"field_name": field_name, "text": text},
        )

    return True


def validate_choice(value: Any, choices: list, field_name: str = "فیلد") -> bool:
    """
    اعتبارسنجی انتخاب یک گزینه از لیست مجاز.

    Args:
        value: مقدار انتخاب‌شده.
        choices: لیست گزینه‌های مجاز.
        field_name: نام فیلد برای نمایش در پیام خطا.

    Returns:
        bool: True اگر مقدار در لیست گزینه‌ها باشد.

    Raises:
        ValidationError: اگر مقدار در لیست گزینه‌ها نباشد.
    """
    if value not in choices:
        raise ValidationError(
            message=f"{field_name} باید یکی از گزینه‌های {choices} باشد.",
            context={"field_name": field_name, "value": value, "choices": choices},
        )

    return True


def validate_boolean(value: Any, field_name: str = "فیلد") -> bool:
    """
    اعتبارسنجی مقدار بولی (True/False).

    Args:
        value: مقدار برای اعتبارسنجی.
        field_name: نام فیلد برای نمایش در پیام خطا.

    Returns:
        bool: True اگر مقدار بولی باشد.

    Raises:
        ValidationError: اگر مقدار بولی نباشد.
    """
    if not isinstance(value, bool):
        raise ValidationError(
            message=f"{field_name} باید True یا False باشد.",
            context={"field_name": field_name, "value": value},
        )

    return True