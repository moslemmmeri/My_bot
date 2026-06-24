# my_bot_project/src/my_bot/domain/entities/coupon.py
"""
موجودیت کوپن تخفیف (Coupon Entity).

این کلاس نمایانگر یک کد تخفیف در سیستم است که کاربران می‌توانند
برای دریافت تخفیف در سفارشات خود از آن استفاده کنند.
کوپن‌ها می‌توانند به‌صورت درصدی یا مبلغ ثابت باشند و دارای محدودیت‌هایی
مانند حداقل مبلغ سفارش، حداکثر تخفیف، تعداد استفاده و تاریخ انقضا هستند.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Set

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class CouponType(str, Enum):
    """نوع تخفیف کوپن."""
    PERCENTAGE = "percentage"  # تخفیف درصدی
    FIXED = "fixed"            # تخفیف مبلغ ثابت


@dataclass
class Coupon:
    """
    موجودیت کوپن تخفیف در سیستم.

    Attributes:
        id: شناسه یکتای کوپن در دیتابیس.
        code: کد تخفیف (یکتا، قابل نمایش).
        description: توضیحات کوپن.
        discount_type: نوع تخفیف (درصدی یا مبلغ ثابت).
        discount_value: مقدار تخفیف (درصد یا مبلغ).
        currency: واحد پول (برای تخفیف مبلغ ثابت).
        min_order_amount: حداقل مبلغ سفارش برای استفاده از کوپن (اختیاری).
        max_discount_amount: حداکثر مبلغ تخفیف قابل اعمال (برای تخفیف‌های درصدی).
        usage_limit: تعداد دفعات مجاز استفاده (کل).
        usage_count: تعداد دفعات استفاده‌شده تاکنون.
        user_usage_limit: حداکثر تعداد استفاده برای هر کاربر (پیش‌فرض ۱).
        user_usage_count: دیکشنری نگاشت شناسه کاربر به تعداد استفاده.
        valid_from: تاریخ شروع اعتبار.
        valid_until: تاریخ پایان اعتبار.
        is_active: وضعیت فعال بودن کوپن.
        applicable_products: لیست شناسه محصولات قابل اعمال (خالی یعنی همه).
        applicable_users: لیست شناسه کاربران مجاز (خالی یعنی همه).
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """

    code: str
    discount_type: CouponType
    discount_value: float
    currency: str = "IRR"
    min_order_amount: Optional[Money] = None
    max_discount_amount: Optional[Money] = None
    usage_limit: Optional[int] = None
    usage_count: int = 0
    user_usage_limit: int = 1
    user_usage_count: Dict[int, int] = field(default_factory=dict)
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    is_active: bool = True
    applicable_products: List[str] = field(default_factory=list)  # خالی = همه
    applicable_users: List[int] = field(default_factory=list)     # خالی = همه
    id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_code()
        self._validate_discount()
        self._validate_dates()
        self._validate_limits()

    def _validate_code(self) -> None:
        """اعتبارسنجی کد تخفیف (نباید خالی باشد)."""
        if not self.code or not self.code.strip():
            raise ValidationError(
                message="کد تخفیف نمی‌تواند خالی باشد.",
                context={"code": self.code},
            )

    def _validate_discount(self) -> None:
        """اعتبارسنجی مقدار تخفیف."""
        if self.discount_value <= 0:
            raise ValidationError(
                message="مقدار تخفیف باید مثبت باشد.",
                context={"code": self.code, "discount_value": self.discount_value},
            )

        if self.discount_type == CouponType.PERCENTAGE:
            if self.discount_value > 100:
                raise ValidationError(
                    message="تخفیف درصدی نمی‌تواند بیشتر از ۱۰۰ باشد.",
                    context={"code": self.code, "discount_value": self.discount_value},
                )

    def _validate_dates(self) -> None:
        """اعتبارسنجی تاریخ‌ها."""
        if self.valid_until and self.valid_from >= self.valid_until:
            raise ValidationError(
                message="تاریخ شروع باید قبل از تاریخ پایان باشد.",
                context={"code": self.code, "valid_from": self.valid_from, "valid_until": self.valid_until},
            )

    def _validate_limits(self) -> None:
        """اعتبارسنجی محدودیت‌های استفاده."""
        if self.usage_limit is not None and self.usage_limit <= 0:
            raise ValidationError(
                message="محدودیت استفاده باید بیشتر از صفر باشد.",
                context={"code": self.code, "usage_limit": self.usage_limit},
            )

        if self.user_usage_limit <= 0:
            raise ValidationError(
                message="محدودیت استفاده برای هر کاربر باید بیشتر از صفر باشد.",
                context={"code": self.code, "user_usage_limit": self.user_usage_limit},
            )

        # بررسی اینکه تعداد استفاده از محدودیت بیشتر نباشد
        if self.usage_limit is not None and self.usage_count > self.usage_limit:
            self.is_active = False
            logger.warning(f"Coupon {self.code} usage count ({self.usage_count}) exceeded limit ({self.usage_limit}). Deactivated.")

    def is_valid(self, user_id: Optional[int] = None, order_amount: Optional[Money] = None) -> bool:
        """
        بررسی اعتبار کوپن برای یک کاربر و مبلغ سفارش خاص.

        Args:
            user_id: شناسه کاربر (اختیاری).
            order_amount: مبلغ سفارش (اختیاری).

        Returns:
            True اگر کوپن معتبر باشد.
        """
        # بررسی فعال بودن
        if not self.is_active:
            logger.debug(f"Coupon {self.code} is inactive.")
            return False

        # بررسی تاریخ انقضا
        now = datetime.now()
        if self.valid_from and now < self.valid_from:
            logger.debug(f"Coupon {self.code} not valid yet (valid_from: {self.valid_from}).")
            return False

        if self.valid_until and now > self.valid_until:
            logger.debug(f"Coupon {self.code} expired (valid_until: {self.valid_until}).")
            return False

        # بررسی محدودیت کلی استفاده
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            logger.debug(f"Coupon {self.code} usage limit ({self.usage_limit}) reached.")
            return False

        # بررسی محدودیت کاربر
        if user_id is not None:
            if self.applicable_users and user_id not in self.applicable_users:
                logger.debug(f"User {user_id} not in applicable_users list for coupon {self.code}.")
                return False

            user_used = self.user_usage_count.get(user_id, 0)
            if user_used >= self.user_usage_limit:
                logger.debug(f"User {user_id} has used coupon {self.code} {user_used} times (limit {self.user_usage_limit}).")
                return False

        # بررسی حداقل مبلغ سفارش
        if order_amount is not None and self.min_order_amount is not None:
            if order_amount.amount < self.min_order_amount.amount:
                logger.debug(f"Order amount {order_amount.amount} is below minimum {self.min_order_amount.amount}.")
                return False

        return True

    def apply_discount(self, original_amount: Money) -> Money:
        """
        اعمال تخفیف روی مبلغ اصلی.

        Args:
            original_amount: مبلغ اصلی (قبل از تخفیف).

        Returns:
            مبلغ تخفیف‌خورده.

        Raises:
            ValidationError: اگر کوپن معتبر نباشد یا تخفیف نامعتبر باشد.
        """
        if self.discount_type == CouponType.PERCENTAGE:
            discount_amount = original_amount * (self.discount_value / 100)
            # اعمال حداکثر تخفیف (اگر تعیین شده باشد)
            if self.max_discount_amount is not None:
                discount_amount = min(discount_amount, self.max_discount_amount)
        else:  # FIXED
            discount_amount = Money(self.discount_value, original_amount.currency)
            # تخفیف نباید از مبلغ اصلی بیشتر شود
            if discount_amount.amount > original_amount.amount:
                discount_amount = original_amount

        # اطمینان از اینکه مبلغ نهایی منفی نمی‌شود
        final_amount = original_amount - discount_amount
        if final_amount.amount < 0:
            final_amount = Money(0, original_amount.currency)

        return final_amount

    def use(self, user_id: int) -> None:
        """
        ثبت استفاده از کوپن توسط یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Raises:
            ValidationError: اگر کوپن معتبر نباشد یا کاربر مجاز نباشد.
        """
        if not self.is_valid(user_id):
            raise ValidationError(
                message="کوپن معتبر نیست یا محدودیت استفاده آن تمام شده است.",
                context={"code": self.code, "user_id": user_id},
            )

        self.usage_count += 1
        self.user_usage_count[user_id] = self.user_usage_count.get(user_id, 0) + 1
        self.updated_at = datetime.now()

        # اگر محدودیت کلی تمام شد، غیرفعال می‌کنیم
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            self.is_active = False
            logger.info(f"Coupon {self.code} reached usage limit. Deactivated.")

        logger.info(f"Coupon {self.code} used by user {user_id}. Total usage: {self.usage_count}")

    def reset_usage(self) -> None:
        """بازنشانی آمار استفاده از کوپن."""
        self.usage_count = 0
        self.user_usage_count.clear()
        self.is_active = True
        self.updated_at = datetime.now()
        logger.info(f"Coupon {self.code} usage reset.")

    def activate(self) -> None:
        """فعال‌سازی کوپن."""
        if not self.is_active:
            self.is_active = True
            self.updated_at = datetime.now()
            logger.info(f"Coupon {self.code} activated.")

    def deactivate(self, reason: Optional[str] = None) -> None:
        """
        غیرفعال‌سازی کوپن.

        Args:
            reason: دلیل غیرفعال‌سازی (اختیاری).
        """
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.now()
            if reason:
                self.metadata["deactivation_reason"] = reason
            logger.info(f"Coupon {self.code} deactivated. Reason: {reason}")

    def is_expired(self) -> bool:
        """بررسی انقضای کوپن."""
        if self.valid_until is None:
            return False
        return datetime.now() > self.valid_until

    def is_applicable_to_product(self, product_id: str) -> bool:
        """
        بررسی اینکه کوپن برای یک محصول خاص قابل استفاده است.

        Args:
            product_id: شناسه محصول.

        Returns:
            True اگر کوپن برای این محصول قابل استفاده باشد.
        """
        if not self.applicable_products:
            return True  # خالی یعنی همه محصولات
        return product_id in self.applicable_products

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل موجودیت کوپن به دیکشنری.

        Returns:
            دیکشنری شامل اطلاعات کوپن.
        """
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "discount_type": self.discount_type.value,
            "discount_value": self.discount_value,
            "currency": self.currency,
            "min_order_amount": self.min_order_amount.amount if self.min_order_amount else None,
            "max_discount_amount": self.max_discount_amount.amount if self.max_discount_amount else None,
            "usage_limit": self.usage_limit,
            "usage_count": self.usage_count,
            "user_usage_limit": self.user_usage_limit,
            "user_usage_count": self.user_usage_count,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "is_active": self.is_active,
            "applicable_products": self.applicable_products,
            "applicable_users": self.applicable_users,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Coupon":
        """
        ساخت موجودیت کوپن از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات کوپن.

        Returns:
            نمونه‌ای از کلاس Coupon.
        """
        # تبدیل نوع تخفیف
        discount_type = CouponType(data.get("discount_type", "fixed"))

        # تبدیل تاریخ‌ها
        valid_from = None
        if data.get("valid_from"):
            try:
                valid_from = datetime.fromisoformat(data["valid_from"])
            except (ValueError, TypeError):
                valid_from = datetime.now()

        valid_until = None
        if data.get("valid_until"):
            try:
                valid_until = datetime.fromisoformat(data["valid_until"])
            except (ValueError, TypeError):
                pass

        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()

        updated_at = None
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                updated_at = datetime.now()

        # تبدیل مبالغ
        min_order_amount = None
        if data.get("min_order_amount") is not None:
            min_order_amount = Money(data["min_order_amount"], data.get("currency", "IRR"))

        max_discount_amount = None
        if data.get("max_discount_amount") is not None:
            max_discount_amount = Money(data["max_discount_amount"], data.get("currency", "IRR"))

        return cls(
            id=data.get("id"),
            code=data["code"],
            description=data.get("description"),
            discount_type=discount_type,
            discount_value=data["discount_value"],
            currency=data.get("currency", "IRR"),
            min_order_amount=min_order_amount,
            max_discount_amount=max_discount_amount,
            usage_limit=data.get("usage_limit"),
            usage_count=data.get("usage_count", 0),
            user_usage_limit=data.get("user_usage_limit", 1),
            user_usage_count=data.get("user_usage_count", {}),
            valid_from=valid_from or datetime.now(),
            valid_until=valid_until,
            is_active=data.get("is_active", True),
            applicable_products=data.get("applicable_products", []),
            applicable_users=data.get("applicable_users", []),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """نمایش رشته‌ای کوپن."""
        return f"Coupon({self.code}, discount: {self.discount_value}{'%' if self.discount_type == CouponType.PERCENTAGE else ' ' + self.currency})"