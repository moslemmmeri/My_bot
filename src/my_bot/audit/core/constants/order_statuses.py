# my_bot_project/src/my_bot/core/constants/order_statuses.py
"""
ثابت‌های مربوط به وضعیت‌های سفارش (Order Statuses).

این ماژول شامل Enum وضعیت‌های مختلف سفارش در سیستم است که برای
مدیریت چرخه‌ی حیات سفارشات و نمایش وضعیت آنها به کاربران استفاده می‌شود.
"""

from enum import Enum
from typing import Optional


class OrderStatus(str, Enum):
    """
    وضعیت‌های مختلف سفارش در سیستم.

    هر وضعیت نشان‌دهنده‌ی مرحله‌ای از چرخه‌ی پردازش سفارش است و
    قوانین خاص خود را برای انتقال به وضعیت‌های دیگر دارد.

    Attributes:
        PENDING: در انتظار پرداخت (وضعیت اولیه پس از ثبت سفارش)
        PAID: پرداخت شده (پرداخت با موفقیت انجام شده)
        PROCESSING: در حال پردازش (تأیید و آماده‌سازی سفارش)
        SHIPPED: ارسال شده (سفارش به پست تحویل داده شده)
        DELIVERED: تحویل داده شده (سفارش به دست مشتری رسیده)
        CANCELED: لغو شده (سفارش توسط کاربر یا سیستم لغو شده)
        REFUNDED: بازگشت وجه (وجه سفارش به کاربر برگردانده شده)
        FAILED: ناموفق (پرداخت ناموفق یا خطا در پردازش)
        ON_HOLD: در انتظار بررسی (نیاز به تأیید دستی)
    """

    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    FAILED = "failed"
    ON_HOLD = "on_hold"

    @classmethod
    def from_string(cls, value: str) -> Optional["OrderStatus"]:
        """
        تبدیل یک رشته به وضعیت سفارش.

        Args:
            value: رشته‌ای که نمایانگر وضعیت سفارش است.

        Returns:
            وضعیت سفارش متناظر با رشته داده شده، یا None در صورت عدم تطابق.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def is_active(self) -> bool:
        """
        بررسی اینکه آیا سفارش در حالت فعال است (هنوز به پایان نرسیده).

        وضعیت‌های فعال: PENDING, PAID, PROCESSING, SHIPPED, ON_HOLD
        """
        return self in (
            OrderStatus.PENDING,
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.ON_HOLD,
        )

    def is_final(self) -> bool:
        """
        بررسی اینکه آیا سفارش به وضعیت نهایی رسیده است.

        وضعیت‌های نهایی: DELIVERED, CANCELED, REFUNDED, FAILED
        """
        return self in (
            OrderStatus.DELIVERED,
            OrderStatus.CANCELED,
            OrderStatus.REFUNDED,
            OrderStatus.FAILED,
        )

    def is_paid(self) -> bool:
        """
        بررسی اینکه آیا سفارش پرداخت شده است (وضعیت پرداخت موفق).

        وضعیت‌هایی که نشان‌دهنده‌ی پرداخت موفق هستند:
        PAID, PROCESSING, SHIPPED, DELIVERED
        """
        return self in (
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        )

    def can_cancel(self) -> bool:
        """
        بررسی اینکه آیا سفارش قابل لغو است.

        سفارشات قابل لغو: PENDING, PAID, ON_HOLD
        """
        return self in (OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.ON_HOLD)

    def can_refund(self) -> bool:
        """
        بررسی اینکه آیا سفارش قابل بازگشت وجه است.

        سفارشات قابل بازگشت: PAID, PROCESSING (در صورت عدم ارسال)
        """
        return self in (OrderStatus.PAID, OrderStatus.PROCESSING)

    def can_update(self) -> bool:
        """
        بررسی اینکه آیا سفارش قابل ویرایش است (توسط کاربر).

        فقط سفارشات PENDING قابل ویرایش هستند.
        """
        return self == OrderStatus.PENDING

    def is_user_visible(self) -> bool:
        """
        بررسی اینکه آیا این وضعیت برای کاربر قابل مشاهده است.

        تمام وضعیت‌ها به جز FAILED و ON_HOLD (در برخی موارد) قابل مشاهده هستند.
        """
        return self != OrderStatus.FAILED

    def get_display_name(self) -> str:
        """
        دریافت نام نمایشی وضعیت سفارش (به فارسی).

        Returns:
            نام نمایشی وضعیت سفارش.
        """
        display_names = {
            OrderStatus.PENDING: "در انتظار پرداخت",
            OrderStatus.PAID: "پرداخت شده",
            OrderStatus.PROCESSING: "در حال پردازش",
            OrderStatus.SHIPPED: "ارسال شده",
            OrderStatus.DELIVERED: "تحویل داده شده",
            OrderStatus.CANCELED: "لغو شده",
            OrderStatus.REFUNDED: "بازگشت وجه",
            OrderStatus.FAILED: "ناموفق",
            OrderStatus.ON_HOLD: "در انتظار بررسی",
        }
        return display_names.get(self, self.value)

    def get_emoji(self) -> str:
        """
        دریافت ایموجی متناسب با وضعیت سفارش.

        Returns:
            ایموجی نمایشی برای وضعیت سفارش.
        """
        emojis = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.PAID: "✅",
            OrderStatus.PROCESSING: "🔄",
            OrderStatus.SHIPPED: "🚚",
            OrderStatus.DELIVERED: "📦",
            OrderStatus.CANCELED: "❌",
            OrderStatus.REFUNDED: "💰",
            OrderStatus.FAILED: "⚠️",
            OrderStatus.ON_HOLD: "🔍",
        }
        return emojis.get(self, "❓")

    def get_color_code(self) -> str:
        """
        دریافت کد رنگ مناسب برای نمایش وضعیت (برای استفاده در گزارشات یا UI).

        Returns:
            کد رنگ هگزادسیمال.
        """
        colors = {
            OrderStatus.PENDING: "#FFA500",  # نارنجی
            OrderStatus.PAID: "#28A745",     # سبز
            OrderStatus.PROCESSING: "#007BFF", # آبی
            OrderStatus.SHIPPED: "#17A2B8",   # فیروزه‌ای
            OrderStatus.DELIVERED: "#28A745", # سبز تیره
            OrderStatus.CANCELED: "#DC3545",  # قرمز
            OrderStatus.REFUNDED: "#6C757D",  # خاکستری
            OrderStatus.FAILED: "#DC3545",    # قرمز
            OrderStatus.ON_HOLD: "#FFC107",   # زرد
        }
        return colors.get(self, "#6C757D")

    def get_priority(self) -> int:
        """
        دریافت اولویت پردازش وضعیت (عدد بالاتر = اولویت بیشتر).

        Returns:
            عدد اولویت (۱ تا ۱۰).
        """
        priorities = {
            OrderStatus.PENDING: 8,
            OrderStatus.PAID: 9,
            OrderStatus.PROCESSING: 7,
            OrderStatus.SHIPPED: 5,
            OrderStatus.DELIVERED: 3,
            OrderStatus.CANCELED: 1,
            OrderStatus.REFUNDED: 2,
            OrderStatus.FAILED: 4,
            OrderStatus.ON_HOLD: 6,
        }
        return priorities.get(self, 5)


# لیست وضعیت‌های قابل پرداخت (برای اعتبارسنجی در پرداخت)
PAYABLE_STATUSES = (OrderStatus.PENDING,)

# لیست وضعیت‌های قابل ارسال (برای بررسی قبل از ارسال)
SHIPPABLE_STATUSES = (OrderStatus.PAID, OrderStatus.PROCESSING)

# لیست وضعیت‌های قابل لغو توسط کاربر
CANCELABLE_BY_USER_STATUSES = (OrderStatus.PENDING, OrderStatus.PAID)

# لیست وضعیت‌های قابل لغو توسط ادمین
CANCELABLE_BY_ADMIN_STATUSES = (
    OrderStatus.PENDING,
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.ON_HOLD,
)

# وضعیت پیش‌فرض برای سفارش جدید
DEFAULT_STATUS = OrderStatus.PENDING

# لیست وضعیت‌های نهایی (پایان چرخه)
FINAL_STATUSES = (OrderStatus.DELIVERED, OrderStatus.CANCELED, OrderStatus.REFUNDED, OrderStatus.FAILED)


__all__ = [
    "OrderStatus",
    "PAYABLE_STATUSES",
    "SHIPPABLE_STATUSES",
    "CANCELABLE_BY_USER_STATUSES",
    "CANCELABLE_BY_ADMIN_STATUSES",
    "DEFAULT_STATUS",
    "FINAL_STATUSES",
]