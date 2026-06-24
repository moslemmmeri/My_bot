# my_bot_project/src/my_bot/core/constants/payment_statuses.py
"""
ثابت‌های مربوط به وضعیت‌های پرداخت (Payment Statuses).

این ماژول شامل Enum وضعیت‌های مختلف پرداخت در سیستم است که برای
مدیریت تراکنش‌های مالی و نمایش وضعیت آنها به کاربران استفاده می‌شود.
"""

from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    """
    وضعیت‌های مختلف پرداخت در سیستم.

    هر وضعیت نشان‌دهنده‌ی مرحله‌ای از چرخه‌ی حیات یک تراکنش پرداخت است
    و قوانین خاص خود را برای انتقال به وضعیت‌های دیگر دارد.

    Attributes:
        PENDING: در انتظار پرداخت (وضعیت اولیه پس از ایجاد تراکنش)
        PROCESSING: در حال پردازش (ارسال به درگاه پرداخت)
        SUCCESS: موفق (پرداخت با موفقیت انجام شده)
        FAILED: ناموفق (پرداخت با خطا مواجه شده)
        CANCELED: لغو شده (پرداخت توسط کاربر لغو شده)
        REFUNDED: بازگشت وجه (پرداخت به کاربر برگردانده شده)
        EXPIRED: منقضی شده (زمان پرداخت به پایان رسیده)
        REVERSED: برگشت خورده (پرداخت توسط سیستم برگشت خورده)
        WAITING_VERIFICATION: در انتظار تأیید (نیاز به بررسی دستی)
    """

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    REVERSED = "reversed"
    WAITING_VERIFICATION = "waiting_verification"

    @classmethod
    def from_string(cls, value: str) -> Optional["PaymentStatus"]:
        """
        تبدیل یک رشته به وضعیت پرداخت.

        Args:
            value: رشته‌ای که نمایانگر وضعیت پرداخت است.

        Returns:
            وضعیت پرداخت متناظر با رشته داده شده، یا None در صورت عدم تطابق.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def is_success(self) -> bool:
        """
        بررسی اینکه آیا پرداخت با موفقیت انجام شده است.
        """
        return self == PaymentStatus.SUCCESS

    def is_failed(self) -> bool:
        """
        بررسی اینکه آیا پرداخت ناموفق بوده است.
        """
        return self in (PaymentStatus.FAILED, PaymentStatus.EXPIRED, PaymentStatus.REVERSED)

    def is_pending(self) -> bool:
        """
        بررسی اینکه آیا پرداخت در حال انتظار است.
        """
        return self in (PaymentStatus.PENDING, PaymentStatus.PROCESSING, PaymentStatus.WAITING_VERIFICATION)

    def is_final(self) -> bool:
        """
        بررسی اینکه آیا پرداخت به وضعیت نهایی رسیده است.

        وضعیت‌های نهایی: SUCCESS, FAILED, CANCELED, REFUNDED, EXPIRED, REVERSED
        """
        return self in (
            PaymentStatus.SUCCESS,
            PaymentStatus.FAILED,
            PaymentStatus.CANCELED,
            PaymentStatus.REFUNDED,
            PaymentStatus.EXPIRED,
            PaymentStatus.REVERSED,
        )

    def is_refundable(self) -> bool:
        """
        بررسی اینکه آیا پرداخت قابل بازگشت است.

        فقط پرداخت‌های موفق قابل بازگشت هستند.
        """
        return self == PaymentStatus.SUCCESS

    def is_cancelable(self) -> bool:
        """
        بررسی اینکه آیا پرداخت قابل لغو است.

        پرداخت‌های در حال انتظار قابل لغو هستند.
        """
        return self in (PaymentStatus.PENDING, PaymentStatus.PROCESSING, PaymentStatus.WAITING_VERIFICATION)

    def can_retry(self) -> bool:
        """
        بررسی اینکه آیا پرداخت قابل تلاش مجدد است.

        پرداخت‌های ناموفق، لغو شده، منقضی و برگشت خورده قابل تلاش مجدد هستند.
        """
        return self in (PaymentStatus.FAILED, PaymentStatus.CANCELED, PaymentStatus.EXPIRED, PaymentStatus.REVERSED)

    def get_display_name(self) -> str:
        """
        دریافت نام نمایشی وضعیت پرداخت (به فارسی).

        Returns:
            نام نمایشی وضعیت پرداخت.
        """
        display_names = {
            PaymentStatus.PENDING: "در انتظار پرداخت",
            PaymentStatus.PROCESSING: "در حال پردازش",
            PaymentStatus.SUCCESS: "پرداخت موفق",
            PaymentStatus.FAILED: "پرداخت ناموفق",
            PaymentStatus.CANCELED: "لغو شده",
            PaymentStatus.REFUNDED: "بازگشت وجه",
            PaymentStatus.EXPIRED: "منقضی شده",
            PaymentStatus.REVERSED: "برگشت خورده",
            PaymentStatus.WAITING_VERIFICATION: "در انتظار تأیید",
        }
        return display_names.get(self, self.value)

    def get_emoji(self) -> str:
        """
        دریافت ایموجی متناسب با وضعیت پرداخت.

        Returns:
            ایموجی نمایشی برای وضعیت پرداخت.
        """
        emojis = {
            PaymentStatus.PENDING: "⏳",
            PaymentStatus.PROCESSING: "🔄",
            PaymentStatus.SUCCESS: "✅",
            PaymentStatus.FAILED: "❌",
            PaymentStatus.CANCELED: "🚫",
            PaymentStatus.REFUNDED: "💰",
            PaymentStatus.EXPIRED: "⌛",
            PaymentStatus.REVERSED: "↩️",
            PaymentStatus.WAITING_VERIFICATION: "🔍",
        }
        return emojis.get(self, "❓")

    def get_color_code(self) -> str:
        """
        دریافت کد رنگ مناسب برای نمایش وضعیت (برای استفاده در گزارشات یا UI).

        Returns:
            کد رنگ هگزادسیمال.
        """
        colors = {
            PaymentStatus.PENDING: "#FFA500",  # نارنجی
            PaymentStatus.PROCESSING: "#007BFF", # آبی
            PaymentStatus.SUCCESS: "#28A745",   # سبز
            PaymentStatus.FAILED: "#DC3545",    # قرمز
            PaymentStatus.CANCELED: "#6C757D",  # خاکستری
            PaymentStatus.REFUNDED: "#17A2B8",  # فیروزه‌ای
            PaymentStatus.EXPIRED: "#6C757D",   # خاکستری
            PaymentStatus.REVERSED: "#FFC107",  # زرد
            PaymentStatus.WAITING_VERIFICATION: "#FFC107", # زرد
        }
        return colors.get(self, "#6C757D")

    def get_payment_gateway_status(self) -> str:
        """
        تبدیل وضعیت به فرمت مناسب برای درگاه‌های پرداخت.

        Returns:
            وضعیت قابل استفاده برای درگاه پرداخت.
        """
        gateway_mapping = {
            PaymentStatus.PENDING: "pending",
            PaymentStatus.PROCESSING: "processing",
            PaymentStatus.SUCCESS: "paid",
            PaymentStatus.FAILED: "failed",
            PaymentStatus.CANCELED: "canceled",
            PaymentStatus.REFUNDED: "refunded",
            PaymentStatus.EXPIRED: "expired",
            PaymentStatus.REVERSED: "reversed",
            PaymentStatus.WAITING_VERIFICATION: "waiting",
        }
        return gateway_mapping.get(self, "unknown")


# لیست وضعیت‌های موفق (برای تأیید پرداخت)
SUCCESS_STATUSES = (PaymentStatus.SUCCESS,)

# لیست وضعیت‌های ناموفق (برای نمایش خطا)
FAILED_STATUSES = (PaymentStatus.FAILED, PaymentStatus.EXPIRED, PaymentStatus.REVERSED)

# لیست وضعیت‌های در حال انتظار (برای نمایش در وضعیت‌های در حال پردازش)
PENDING_STATUSES = (PaymentStatus.PENDING, PaymentStatus.PROCESSING, PaymentStatus.WAITING_VERIFICATION)

# لیست وضعیت‌های قابل بازگشت (برای اعتبارسنجی بازگشت وجه)
REFUNDABLE_STATUSES = (PaymentStatus.SUCCESS,)

# لیست وضعیت‌های قابل لغو (برای اعتبارسنجی لغو پرداخت)
CANCELABLE_STATUSES = (PaymentStatus.PENDING, PaymentStatus.PROCESSING, PaymentStatus.WAITING_VERIFICATION)

# لیست وضعیت‌های قابل تلاش مجدد
RETRYABLE_STATUSES = (PaymentStatus.FAILED, PaymentStatus.CANCELED, PaymentStatus.EXPIRED, PaymentStatus.REVERSED)

# وضعیت پیش‌فرض برای پرداخت جدید
DEFAULT_STATUS = PaymentStatus.PENDING

# لیست وضعیت‌های نهایی (پایان چرخه)
FINAL_STATUSES = (
    PaymentStatus.SUCCESS,
    PaymentStatus.FAILED,
    PaymentStatus.CANCELED,
    PaymentStatus.REFUNDED,
    PaymentStatus.EXPIRED,
    PaymentStatus.REVERSED,
)


__all__ = [
    "PaymentStatus",
    "SUCCESS_STATUSES",
    "FAILED_STATUSES",
    "PENDING_STATUSES",
    "REFUNDABLE_STATUSES",
    "CANCELABLE_STATUSES",
    "RETRYABLE_STATUSES",
    "DEFAULT_STATUS",
    "FINAL_STATUSES",
]