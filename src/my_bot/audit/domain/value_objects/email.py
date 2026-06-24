# my_bot_project/src/my_bot/domain/value_objects/email.py
"""
ارزش‌مقدار ایمیل (Email Value Object).

این کلاس نمایانگر یک آدرس ایمیل معتبر است و اعتبارسنجی فرمت آن را
بر اساس استانداردهای RFC 5322 انجام می‌دهد. ایمیل به‌صورت غیرقابل تغییر
(Immutable) ذخیره می‌شود و متدهای کمکی برای دسترسی به بخش‌های مختلف آن فراهم است.
"""

import re
from dataclasses import dataclass
from typing import Optional

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


# الگوی اعتبارسنجی ایمیل بر اساس استاندارد RFC 5322 (ساده‌شده)
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# دامنه‌های معتبر (اختیاری)
VALID_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "mail.com",
    "protonmail.com",
    "icloud.com",
    "aol.com",
    "yandex.com",
    "gmx.com",
    "zoho.com",
    # دامنه‌های ایرانی
    "gmail.ir",
    "yahoo.ir",
    "hotmail.ir",
    "chmail.ir",
    "parsemail.ir",
    "persiangig.com",
    "mailfa.com",
]


@dataclass(frozen=True)
class Email:
    """
    ارزش‌مقدار ایمیل.

    این کلاس یک آدرس ایمیل را با اعتبارسنجی کامل ذخیره می‌کند و
    امکانات کمکی برای کار با آن فراهم می‌کند.

    Attributes:
        value: آدرس ایمیل به‌صورت رشته.
    """

    value: str

    def __post_init__(self) -> None:
        """اعتبارسنجی ایمیل پس از ساخت آبجکت."""
        if not self.value or not self.value.strip():
            raise ValidationError(
                message="آدرس ایمیل نمی‌تواند خالی باشد.",
                context={"email": self.value},
            )

        # حذف فضاهای خالی اضافی
        cleaned = self.value.strip().lower()
        object.__setattr__(self, "value", cleaned)

        # اعتبارسنجی فرمت
        if not self.is_valid_format():
            raise ValidationError(
                message=f"آدرس ایمیل '{self.value}' معتبر نیست.",
                context={"email": self.value},
            )

    def is_valid_format(self) -> bool:
        """
        بررسی فرمت ایمیل با استفاده از الگوی regex.

        Returns:
            True اگر فرمت ایمیل معتبر باشد.
        """
        return bool(EMAIL_PATTERN.match(self.value))

    def is_valid_domain(self) -> bool:
        """
        بررسی اینکه دامنهٔ ایمیل در لیست دامنه‌های معتبر قرار دارد.

        Returns:
            True اگر دامنه معتبر باشد.
        """
        domain = self.get_domain()
        if not domain:
            return False
        return domain in VALID_DOMAINS

    def get_username(self) -> Optional[str]:
        """
        دریافت بخش username از ایمیل (قبل از @).

        Returns:
            نام کاربری یا None در صورت عدم وجود.
        """
        try:
            return self.value.split("@")[0]
        except IndexError:
            return None

    def get_domain(self) -> Optional[str]:
        """
        دریافت بخش دامنه از ایمیل (بعد از @).

        Returns:
            دامنه یا None در صورت عدم وجود.
        """
        try:
            return self.value.split("@")[1]
        except IndexError:
            return None

    def is_gmail(self) -> bool:
        """بررسی اینکه آیا ایمیل از دامنهٔ Gmail است."""
        domain = self.get_domain()
        return domain is not None and domain in ("gmail.com", "googlemail.com")

    def is_outlook(self) -> bool:
        """بررسی اینکه آیا ایمیل از دامنهٔ Outlook/Hotmail است."""
        domain = self.get_domain()
        return domain is not None and domain in ("outlook.com", "hotmail.com", "live.com", "msn.com")

    def is_yahoo(self) -> bool:
        """بررسی اینکه آیا ایمیل از دامنهٔ Yahoo است."""
        domain = self.get_domain()
        return domain is not None and domain in ("yahoo.com", "yahoo.co.uk", "yahoo.fr", "yahoo.de")

    def normalize(self) -> "Email":
        """
        نرمال‌سازی ایمیل (حذف + و نقطه‌های اضافی برای Gmail).

        برای ایمیل‌های Gmail، نقطه‌ها و قسمت + حذف می‌شوند.

        Returns:
            Email نرمال‌سازی‌شده.
        """
        if not self.is_gmail():
            return self

        username = self.get_username()
        if not username:
            return self

        # حذف بخش + و نقطه‌ها
        if "+" in username:
            username = username.split("+")[0]
        normalized_username = username.replace(".", "")
        normalized_email = f"{normalized_username}@gmail.com"

        return Email(normalized_email)

    def mask(self) -> str:
        """
        دریافت نسخهٔ ماسک‌شده از ایمیل (برای نمایش محافظت‌شده).

        Returns:
            ایمیل ماسک‌شده (مثلاً u***r@example.com).
        """
        username = self.get_username()
        domain = self.get_domain()
        if not username or not domain:
            return self.value

        if len(username) <= 2:
            masked_username = username[0] + "***"
        else:
            masked_username = username[0] + "***" + username[-1]

        return f"{masked_username}@{domain}"

    def __str__(self) -> str:
        """نمایش رشته‌ای ایمیل."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """مقایسه دو ایمیل (مقایسه حساس به بزرگی/کوچکی حروف نیست)."""
        if not isinstance(other, Email):
            return False
        return self.value.lower() == other.value.lower()

    def __hash__(self) -> int:
        """محاسبه هش برای استفاده در مجموعه‌ها و دیکشنری‌ها."""
        return hash(self.value.lower())