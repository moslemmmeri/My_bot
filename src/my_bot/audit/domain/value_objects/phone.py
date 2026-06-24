# my_bot_project/src/my_bot/domain/value_objects/phone.py
"""
ارزش‌مقدار شماره تلفن (Phone Value Object).

این کلاس نمایانگر یک شماره تلفن معتبر است و اعتبارسنجی فرمت آن را
بر اساس استانداردهای بین‌المللی (E.164) و داخلی انجام می‌دهد.
شماره تلفن به‌صورت غیرقابل تغییر (Immutable) ذخیره می‌شود و
متدهای کمکی برای تبدیل به فرمت‌های مختلف و اعتبارسنجی فراهم است.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


# الگوی شماره تلفن بین‌المللی (E.164)
# شروع با + و کد کشور، سپس اعداد
INTERNATIONAL_PATTERN = re.compile(r"^\+[1-9][0-9]{1,14}$")

# الگوی شماره تلفن ایران
# ۰۹۱۲۱۲۳۴۵۶۷ یا 9121234567 یا +989121234567
IRAN_PATTERNS = [
    re.compile(r"^0?9[0-9]{9}$"),  # 09121234567 یا 9121234567
    re.compile(r"^\+989[0-9]{9}$"),  # +989121234567
]

# کدهای کشور معتبر (در صورت نیاز)
VALID_COUNTRY_CODES = [
    "98",  # ایران
    "1",   # آمریکا/کانادا
    "44",  # بریتانیا
    "91",  # هند
    "86",  # چین
    "81",  # ژاپن
    "49",  # آلمان
    "33",  # فرانسه
    "39",  # ایتالیا
    "34",  # اسپانیا
    "61",  # استرالیا
    "55",  # برزیل
    "7",   # روسیه
    "82",  # کره جنوبی
    "31",  # هلند
    "46",  # سوئد
    "41",  # سوئیس
    "20",  # مصر
    "90",  # ترکیه
    "971", # امارات
    "966", # عربستان سعودی
    "962", # اردن
    "964", # عراق
    "93",  # افغانستان
    "92",  # پاکستان
]


@dataclass(frozen=True)
class Phone:
    """
    ارزش‌مقدار شماره تلفن.

    این کلاس یک شماره تلفن را با اعتبارسنجی کامل ذخیره می‌کند و
    امکانات کمکی برای کار با آن فراهم می‌کند.

    Attributes:
        value: شماره تلفن به‌صورت رشته (با فرمت بین‌المللی).
        country_code: کد کشور (اختیاری).
    """

    value: str
    country_code: Optional[str] = None

    def __post_init__(self) -> None:
        """اعتبارسنجی شماره تلفن پس از ساخت آبجکت."""
        if not self.value or not self.value.strip():
            raise ValidationError(
                message="شماره تلفن نمی‌تواند خالی باشد.",
                context={"phone": self.value},
            )

        # حذف فضاهای خالی و کاراکترهای اضافی
        cleaned = self._clean(self.value)
        object.__setattr__(self, "value", cleaned)

        # اعتبارسنجی شماره
        if not self.is_valid():
            raise ValidationError(
                message=f"شماره تلفن '{self.value}' معتبر نیست.",
                context={"phone": self.value},
            )

    def _clean(self, phone: str) -> str:
        """
        پاکسازی شماره تلفن (حذف فاصله، خط تیره، پرانتز و ...).

        Args:
            phone: شماره تلفن ورودی.

        Returns:
            شماره تلفن پاکسازی‌شده.
        """
        # حذف فاصله‌ها، خط تیره، پرانتز و اسلش
        cleaned = re.sub(r"[\s\-()/]", "", phone)
        return cleaned

    def is_valid(self) -> bool:
        """
        بررسی اعتبار شماره تلفن.

        Returns:
            True اگر شماره تلفن معتبر باشد.
        """
        # ابتدا بررسی فرمت بین‌المللی
        if self.is_international():
            return True

        # سپس بررسی فرمت‌های داخلی (ایران)
        if self.is_iranian():
            return True

        return False

    def is_international(self) -> bool:
        """
        بررسی اینکه آیا شماره تلفن به فرمت بین‌المللی (E.164) است.

        Returns:
            True اگر فرمت بین‌المللی باشد.
        """
        return bool(INTERNATIONAL_PATTERN.match(self.value))

    def is_iranian(self) -> bool:
        """
        بررسی اینکه آیا شماره تلفن ایرانی است.

        Returns:
            True اگر شماره تلفن ایرانی باشد.
        """
        for pattern in IRAN_PATTERNS:
            if pattern.match(self.value):
                return True
        return False

    def get_country_code(self) -> Optional[str]:
        """
        دریافت کد کشور از شماره تلفن.

        Returns:
            کد کشور یا None در صورت عدم تشخیص.
        """
        if self.is_international():
            # استخراج کد کشور از ابتدای شماره (بعد از +)
            # پیدا کردن طول کد کشور (1 تا 3 رقم)
            for i in range(1, 4):
                if i >= len(self.value):
                    break
                code = self.value[1:1+i]
                if code in VALID_COUNTRY_CODES:
                    return code

        if self.is_iranian():
            return "98"

        return self.country_code

    def get_national_number(self) -> Optional[str]:
        """
        دریافت شماره ملی (بدون کد کشور و پیشوند صفر).

        Returns:
            شماره ملی یا None در صورت عدم تشخیص.
        """
        if self.is_international():
            code = self.get_country_code()
            if code:
                return self.value[1+len(code):]

        if self.is_iranian():
            # اگر با ۰ شروع شده، حذف کن
            number = self.value
            if number.startswith("0"):
                number = number[1:]
            # اگر با ۹ شروع شده، یعنی کد کشور ۹۸ حذف شده
            if number.startswith("9") and len(number) == 10:
                return number
            # اگر با +989 شروع شده
            if number.startswith("+989"):
                return number[4:]

        return None

    def to_international(self) -> str:
        """
        تبدیل شماره تلفن به فرمت بین‌المللی (E.164).

        Returns:
            شماره تلفن با فرمت بین‌المللی.
        """
        if self.is_international():
            return self.value

        if self.is_iranian():
            number = self.value
            # حذف صفر ابتدایی
            if number.startswith("0"):
                number = number[1:]
            # اگر با ۹ شروع شده، کد کشور ۹۸ را اضافه کن
            if number.startswith("9") and len(number) == 10:
                return f"+98{number}"
            # اگر با +989 شروع شده
            if number.startswith("+989"):
                return number
            # اگر فقط اعداد بدون کد کشور هستند
            if number.isdigit() and len(number) == 10:
                return f"+98{number}"

        # اگر فرمت دیگری داشت، سعی کن کد کشور را اضافه کنی
        if self.country_code:
            return f"+{self.country_code}{self.value}"

        return self.value

    def to_national(self) -> str:
        """
        تبدیل شماره تلفن به فرمت ملی (با صفر ابتدایی برای ایران).

        Returns:
            شماره تلفن با فرمت ملی.
        """
        if self.is_iranian():
            number = self.value
            # اگر بین‌المللی است، کد کشور را حذف کن
            if number.startswith("+"):
                # حذف +98
                if number.startswith("+98"):
                    number = number[3:]
                else:
                    code = self.get_country_code()
                    if code:
                        number = number[1+len(code):]

            # اطمینان از وجود صفر ابتدایی
            if not number.startswith("0"):
                number = f"0{number}"

            return number

        return self.value

    def is_mobile(self) -> bool:
        """
        بررسی اینکه آیا شماره تلفن همراه است (برای ایران).

        Returns:
            True اگر شماره همراه باشد.
        """
        if not self.is_iranian():
            return False

        number = self.to_national()
        # همراه‌های ایران با ۰۹ شروع می‌شوند
        if number.startswith("09"):
            # همراه اول: 0910-0919, 0930-0939
            # ایرانسل: 0920-0929
            # رایتل: 0930-0939
            # شاتل: 0940-0949
            prefixes = ["091", "092", "093", "094"]
            for prefix in prefixes:
                if number.startswith(prefix):
                    return True
        return False

    def is_fixed_line(self) -> bool:
        """
        بررسی اینکه آیا شماره تلفن ثابت است (برای ایران).

        Returns:
            True اگر شماره ثابت باشد.
        """
        if not self.is_iranian():
            return False

        number = self.to_national()
        # تلفن‌های ثابت ایران با ۰۲۱ (تهران) یا ۰۳ (استان‌ها) شروع می‌شوند
        return number.startswith("0") and not number.startswith("09")

    def get_operator(self) -> Optional[str]:
        """
        دریافت اپراتور همراه (برای ایران).

        Returns:
            نام اپراتور یا None در صورت عدم تشخیص.
        """
        if not self.is_mobile():
            return None

        number = self.to_national()
        prefix = number[:3]

        operator_map = {
            "091": "همراه اول",
            "092": "ایرانسل",
            "093": "رایتل",
            "094": "شاتل",
            "090": "همراه اول",
            "099": "همراه اول",
        }

        return operator_map.get(prefix, "سایر")

    def mask(self) -> str:
        """
        دریافت نسخهٔ ماسک‌شده از شماره تلفن (برای نمایش محافظت‌شده).

        Returns:
            شماره ماسک‌شده (مثلاً ۰۹۱۲***۴۵۶۷).
        """
        if self.is_iranian():
            number = self.to_national()
            if len(number) >= 11:
                return f"{number[:4]}***{number[-4:]}"
            if len(number) >= 8:
                return f"{number[:3]}***{number[-3:]}"
            return "***" + number[-4:] if len(number) >= 4 else number

        if self.is_international():
            if len(self.value) >= 8:
                return f"{self.value[:3]}***{self.value[-3:]}"
            return "***" + self.value[-4:] if len(self.value) >= 4 else self.value

        return self.value

    def __str__(self) -> str:
        """نمایش رشته‌ای شماره تلفن."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """مقایسه دو شماره تلفن (با نرمال‌سازی)."""
        if not isinstance(other, Phone):
            return False
        # مقایسه بعد از نرمال‌سازی به فرمت بین‌المللی
        return self.to_international() == other.to_international()

    def __hash__(self) -> int:
        """محاسبه هش برای استفاده در مجموعه‌ها و دیکشنری‌ها."""
        return hash(self.to_international())