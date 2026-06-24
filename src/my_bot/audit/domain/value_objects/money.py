# my_bot_project/src/my_bot/domain/value_objects/money.py
"""
ارزش‌مقدار پول (Money Value Object).

این کلاس نمایانگر یک مقدار پولی با واحد پول مشخص است و عملیات‌های
ریاضی پایه مانند جمع، تفریق، ضرب و مقایسه را پشتیبانی می‌کند.
پول به‌صورت غیرقابل تغییر (Immutable) ذخیره می‌شود و از دقت بالا
با استفاده از عدد اعشاری (Decimal) بهره می‌برد.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Money:
    """
    ارزش‌مقدار پول.

    این کلاس یک مقدار پولی را با واحد پول مشخص ذخیره می‌کند و
    عملیات‌های ریاضی پایه را پشتیبانی می‌کند.

    Attributes:
        amount: مقدار پول به‌صورت عدد اعشاری (Decimal).
        currency: واحد پول (پیش‌فرض: IRR).
    """

    amount: Decimal
    currency: str = "IRR"

    def __post_init__(self) -> None:
        """اعتبارسنجی مقدار پول پس از ساخت آبجکت."""
        # تبدیل به Decimal در صورت نیاز
        if not isinstance(self.amount, Decimal):
            if isinstance(self.amount, (int, float, str)):
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            else:
                raise ValidationError(
                    message="مقدار پول باید عددی باشد.",
                    context={"amount": self.amount, "type": type(self.amount).__name__},
                )

        # اعتبارسنجی واحد پول
        if not self.currency or not self.currency.strip():
            raise ValidationError(
                message="واحد پول نمی‌تواند خالی باشد.",
                context={"currency": self.currency},
            )

        # گرد کردن به ۲ رقم اعشار (برای واحدهای اعشاری)
        rounded = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", rounded)

    def __add__(self, other: Union["Money", Decimal, int, float]) -> "Money":
        """
        جمع دو مقدار پولی با همان واحد پول.

        Args:
            other: مقدار پولی دیگر.

        Returns:
            Money جدید با مجموع مقادیر.

        Raises:
            ValidationError: اگر واحد پول‌ها متفاوت باشد.
        """
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise ValidationError(
                    message=f"واحد پول‌ها متفاوت است: {self.currency} و {other.currency}",
                    context={"currency1": self.currency, "currency2": other.currency},
                )
            return Money(self.amount + other.amount, self.currency)
        else:
            # اگر عدد باشد، به‌عنوان همان واحد پول در نظر گرفته می‌شود
            return Money(self.amount + Decimal(str(other)), self.currency)

    def __sub__(self, other: Union["Money", Decimal, int, float]) -> "Money":
        """
        تفریق دو مقدار پولی با همان واحد پول.

        Args:
            other: مقدار پولی دیگر.

        Returns:
            Money جدید با تفاضل مقادیر.

        Raises:
            ValidationError: اگر واحد پول‌ها متفاوت باشد یا نتیجه منفی شود.
        """
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise ValidationError(
                    message=f"واحد پول‌ها متفاوت است: {self.currency} و {other.currency}",
                    context={"currency1": self.currency, "currency2": other.currency},
                )
            result = self.amount - other.amount
            if result < 0:
                raise ValidationError(
                    message="نتیجه تفریق نمی‌تواند منفی باشد.",
                    context={"amount": self.amount, "other": other.amount},
                )
            return Money(result, self.currency)
        else:
            result = self.amount - Decimal(str(other))
            if result < 0:
                raise ValidationError(
                    message="نتیجه تفریق نمی‌تواند منفی باشد.",
                    context={"amount": self.amount, "other": other},
                )
            return Money(result, self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> "Money":
        """
        ضرب مقدار پولی در یک عدد.

        Args:
            multiplier: ضریب (عدد صحیح، اعشاری یا Decimal).

        Returns:
            Money جدید با مقدار ضرب‌شده.
        """
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "Money":
        """
        تقسیم مقدار پولی بر یک عدد.

        Args:
            divisor: مقسوم‌علیه (عدد صحیح، اعشاری یا Decimal).

        Returns:
            Money جدید با مقدار تقسیم‌شده.

        Raises:
            ValidationError: اگر مقسوم‌علیه صفر باشد.
        """
        if divisor == 0:
            raise ValidationError(
                message="تقسیم بر صفر مجاز نیست.",
                context={"divisor": divisor},
            )
        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __eq__(self, other: object) -> bool:
        """
        مقایسه برابری دو مقدار پولی (با همان واحد پول).

        Args:
            other: مقدار پولی دیگر.

        Returns:
            True اگر برابر باشند.
        """
        if not isinstance(other, Money):
            return False
        if other.currency != self.currency:
            return False
        return self.amount == other.amount

    def __lt__(self, other: "Money") -> bool:
        """
        مقایسه کوچکتر بودن.

        Args:
            other: مقدار پولی دیگر.

        Returns:
            True اگر self کمتر از other باشد.

        Raises:
            ValidationError: اگر واحد پول‌ها متفاوت باشد.
        """
        if other.currency != self.currency:
            raise ValidationError(
                message=f"واحد پول‌ها متفاوت است: {self.currency} و {other.currency}",
                context={"currency1": self.currency, "currency2": other.currency},
            )
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """
        مقایسه کوچکتر یا مساوی.

        Args:
            other: مقدار پولی دیگر.

        Returns:
            True اگر self کوچکتر یا مساوی other باشد.

        Raises:
            ValidationError: اگر واحد پول‌ها متفاوت باشد.
        """
        if other.currency != self.currency:
            raise ValidationError(
                message=f"واحد پول‌ها متفاوت است: {self.currency} و {other.currency}",
                context={"currency1": self.currency, "currency2": other.currency},
            )
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        """
        مقایسه بزرگتر بودن.

        Args:
            other: مقدار پولی دیگر.

        Returns:
            True اگر self بزرگتر از other باشد.

        Raises:
            ValidationError: اگر واحد پول‌ها متفاوت باشد.
        """
        if other.currency != self.currency:
            raise ValidationError(
                message=f"واحد پول‌ها متفاوت است: {self.currency} و {other.currency}",
                context={"currency1": self.currency, "currency2": other.currency},
            )
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """
        مقایسه بزرگتر یا مساوی.

        Args:
            other: مقدار پولی دیگر.

        Returns:
            True اگر self بزرگتر یا مساوی other باشد.

        Raises:
            ValidationError: اگر واحد پول‌ها متفاوت باشد.
        """
        if other.currency != self.currency:
            raise ValidationError(
                message=f"واحد پول‌ها متفاوت است: {self.currency} و {other.currency}",
                context={"currency1": self.currency, "currency2": other.currency},
            )
        return self.amount >= other.amount

    def __neg__(self) -> "Money":
        """
        منفی کردن مقدار پول (برای نمایش بدهی).

        Returns:
            Money با مقدار منفی (همان واحد پول).
        """
        return Money(-self.amount, self.currency)

    def __pos__(self) -> "Money":
        """
        مثبت کردن مقدار پول.

        Returns:
            همان Money.
        """
        return self

    def __abs__(self) -> "Money":
        """
        مقدار مطلق پول.

        Returns:
            Money با مقدار مطلق.
        """
        return Money(abs(self.amount), self.currency)

    def __str__(self) -> str:
        """
        نمایش رشته‌ای مقدار پول با واحد پول.

        Returns:
            رشته شامل مقدار و واحد پول.
        """
        return f"{self.amount} {self.currency}"

    def __repr__(self) -> str:
        """
        نمایش رسمی برای دیباگ.

        Returns:
            رشته قابل استفاده برای بازسازی.
        """
        return f"Money(amount={self.amount}, currency='{self.currency}')"

    def is_zero(self) -> bool:
        """
        بررسی صفر بودن مقدار پول.

        Returns:
            True اگر مقدار صفر باشد.
        """
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        """
        بررسی مثبت بودن مقدار پول.

        Returns:
            True اگر مقدار مثبت باشد.
        """
        return self.amount > Decimal("0")

    def is_negative(self) -> bool:
        """
        بررسی منفی بودن مقدار پول.

        Returns:
            True اگر مقدار منفی باشد.
        """
        return self.amount < Decimal("0")

    def to_decimal(self) -> Decimal:
        """
        دریافت مقدار به‌صورت Decimal.

        Returns:
            مقدار پول.
        """
        return self.amount

    def to_float(self) -> float:
        """
        دریافت مقدار به‌صورت float.

        Returns:
            مقدار پول به‌صورت اعشاری.
        """
        return float(self.amount)

    def to_int(self) -> int:
        """
        دریافت مقدار به‌صورت عدد صحیح (با گرد کردن).

        Returns:
            مقدار پول به‌صورت عدد صحیح.
        """
        return int(self.amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def to_rial(self) -> int:
        """
        تبدیل به ریال (برای واحدهایی که ریال پایه هستند).

        این متد برای واحدهایی مانند IRR که ریال پایه است، مقدار را به عدد صحیح
        (بدون اعشار) برمی‌گرداند.

        Returns:
            مقدار به ریال (عدد صحیح).
        """
        if self.currency == "IRR":
            return self.to_int()
        return int(self.amount * 10)  # برای واحدهای اعشاری

    def to_toman(self) -> int:
        """
        تبدیل به تومان (برای واحد IRR).

        Returns:
            مقدار به تومان (تقسیم بر ۱۰).
        """
        if self.currency == "IRR":
            return int((self.amount / 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return self.to_int()

    def format(self, with_currency: bool = True) -> str:
        """
        فرمت‌سازی مقدار پول برای نمایش به کاربر.

        Args:
            with_currency: آیا واحد پول نیز نمایش داده شود.

        Returns:
            رشته فرمت‌شده (با جداکننده هزارگان).
        """
        formatted_amount = f"{self.amount:,.0f}"
        if with_currency:
            return f"{formatted_amount} {self.currency}"
        return formatted_amount

    def convert_to(self, target_currency: str, exchange_rate: Decimal) -> "Money":
        """
        تبدیل پول به واحد دیگر با نرخ مشخص.

        Args:
            target_currency: واحد پول مقصد.
            exchange_rate: نرخ تبدیل (مقدار ۱ واحد از پول جاری به واحد مقصد).

        Returns:
            Money با واحد جدید و مقدار تبدیل‌شده.
        """
        if target_currency == self.currency:
            return self
        return Money(self.amount * exchange_rate, target_currency)

    @classmethod
    def zero(cls, currency: str = "IRR") -> "Money":
        """
        ایجاد مقدار صفر با واحد پول مشخص.

        Args:
            currency: واحد پول.

        Returns:
            Money با مقدار صفر.
        """
        return cls(Decimal("0"), currency)

    @classmethod
    def from_rial(cls, amount: int, currency: str = "IRR") -> "Money":
        """
        ایجاد Money از مقدار ریال (عدد صحیح).

        Args:
            amount: مقدار به ریال.
            currency: واحد پول (پیش‌فرض IRR).

        Returns:
            Money با مقدار ریال.
        """
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def from_toman(cls, amount: int, currency: str = "IRR") -> "Money":
        """
        ایجاد Money از مقدار تومان (ضرب در ۱۰ برای تبدیل به ریال).

        Args:
            amount: مقدار به تومان.
            currency: واحد پول (پیش‌فرض IRR).

        Returns:
            Money با مقدار تومان تبدیل‌شده به ریال.
        """
        if currency == "IRR":
            return cls(Decimal(str(amount * 10)), currency)
        return cls(Decimal(str(amount)), currency)