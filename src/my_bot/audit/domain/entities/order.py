# my_bot_project/src/my_bot/domain/entities/order.py
"""
موجودیت سفارش (Order Entity).

این کلاس نمایانگر یک سفارش در سیستم است که توسط کاربر ثبت می‌شود.
شامل اطلاعات محصولات، قیمت‌ها، وضعیت، تخفیف‌ها، آدرس و سایر جزئیات مرتبط است.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


@dataclass
class OrderItem:
    """
    آیتم سفارش (یک محصول یا خدمت در سفارش).

    Attributes:
        product_id: شناسه محصول.
        product_name: نام محصول.
        quantity: تعداد.
        unit_price: قیمت واحد (به‌عنوان Money).
        total_price: قیمت کل (محاسبه‌شده).
        metadata: اطلاعات اضافی.
    """

    product_id: str
    product_name: str
    quantity: int
    unit_price: Money
    total_price: Money = field(init=False)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """محاسبه قیمت کل و اعتبارسنجی اولیه."""
        if self.quantity <= 0:
            raise ValidationError(
                message="تعداد آیتم سفارش باید مثبت باشد.",
                context={"product_id": self.product_id, "quantity": self.quantity},
            )
        self.total_price = self.unit_price * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل آیتم سفارش به دیکشنری."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price.amount,
            "currency": self.unit_price.currency,
            "total_price": self.total_price.amount,
            "metadata": self.metadata,
        }


@dataclass
class Order:
    """
    موجودیت سفارش در سیستم.

    Attributes:
        id: شناسه یکتای سفارش در دیتابیس.
        user_id: شناسه کاربر (در سیستم).
        order_number: شماره سفارش (یکتا، قابل نمایش).
        items: لیست آیتم‌های سفارش (OrderItem).
        total_amount: مبلغ کل سفارش (با احتساب تخفیف‌ها).
        subtotal: مبلغ پایه (قبل از تخفیف).
        discount_amount: مبلغ تخفیف اعمال‌شده.
        coupon_code: کد تخفیف استفاده‌شده (اختیاری).
        status: وضعیت سفارش (پیش‌فرض: PENDING).
        payment_id: شناسه پرداخت مرتبط (اختیاری).
        shipping_address: آدرس تحویل (اختیاری).
        tracking_code: کد رهگیری پستی (اختیاری).
        notes: یادداشت‌های اضافی.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """

    user_id: int
    order_number: str
    items: List[OrderItem]
    total_amount: Money
    subtotal: Money
    discount_amount: Money = field(default_factory=lambda: Money(0, "IRR"))
    coupon_code: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    payment_id: Optional[str] = None
    shipping_address: Optional[str] = None
    tracking_code: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه و محاسبه‌ی مقادیر."""
        self._validate_items()
        self._validate_total()
        self._validate_discount()

    def _validate_items(self) -> None:
        """بررسی وجود حداقل یک آیتم در سفارش."""
        if not self.items:
            raise ValidationError(
                message="سفارش باید حداقل یک آیتم داشته باشد.",
                context={"order_number": self.order_number},
            )

    def _validate_total(self) -> None:
        """بررسی اینکه مبلغ کل منفی نباشد."""
        if self.total_amount.amount < 0:
            raise ValidationError(
                message="مبلغ کل سفارش نمی‌تواند منفی باشد.",
                context={"order_number": self.order_number, "total": self.total_amount.amount},
            )

    def _validate_discount(self) -> None:
        """بررسی اینکه تخفیف از مبلغ پایه بیشتر نباشد."""
        if self.discount_amount.amount > self.subtotal.amount:
            raise ValidationError(
                message="تخفیف نمی‌تواند از مبلغ پایه بیشتر باشد.",
                context={"order_number": self.order_number, "discount": self.discount_amount.amount, "subtotal": self.subtotal.amount},
            )

    def apply_coupon(self, coupon_code: str, discount_amount: Money) -> None:
        """
        اعمال کد تخفیف روی سفارش.

        Args:
            coupon_code: کد تخفیف.
            discount_amount: مبلغ تخفیف.

        Raises:
            ValidationError: اگر تخفیف از مبلغ پایه بیشتر باشد یا سفارش قابل اعمال نباشد.
        """
        if not self.can_apply_discount():
            raise ValidationError(
                message="سفارش در وضعیت فعلی قابل اعمال تخفیف نیست.",
                context={"order_number": self.order_number, "status": self.status.value},
            )

        if discount_amount.amount > self.subtotal.amount:
            raise ValidationError(
                message="تخفیف نمی‌تواند از مبلغ پایه بیشتر باشد.",
                context={"order_number": self.order_number, "discount": discount_amount.amount, "subtotal": self.subtotal.amount},
            )

        self.coupon_code = coupon_code
        self.discount_amount = discount_amount
        self.total_amount = Money(self.subtotal.amount - discount_amount.amount, self.subtotal.currency)
        self.updated_at = datetime.now()
        logger.info(f"Coupon '{coupon_code}' applied to order {self.order_number}")

    def can_apply_discount(self) -> bool:
        """بررسی اینکه آیا سفارش قابلیت اعمال تخفیف دارد (وضعیت PENDING یا PAID)."""
        return self.status in (OrderStatus.PENDING, OrderStatus.PAID)

    def update_status(self, new_status: OrderStatus, reason: Optional[str] = None) -> None:
        """
        به‌روزرسانی وضعیت سفارش.

        Args:
            new_status: وضعیت جدید.
            reason: دلیل تغییر وضعیت (اختیاری).

        Raises:
            ValidationError: اگر تغییر وضعیت غیرمجاز باشد.
        """
        if not self._is_transition_allowed(new_status):
            raise ValidationError(
                message=f"تغییر وضعیت از '{self.status.value}' به '{new_status.value}' مجاز نیست.",
                context={"order_number": self.order_number, "current_status": self.status.value, "new_status": new_status.value},
            )

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        if reason:
            self.metadata["status_change_reason"] = reason
            self.metadata["status_change_from"] = old_status.value
            self.metadata["status_change_to"] = new_status.value

        logger.info(f"Order {self.order_number} status changed from {old_status.value} to {new_status.value}")

    def _is_transition_allowed(self, new_status: OrderStatus) -> bool:
        """بررسی مجاز بودن تغییر وضعیت بر اساس قوانین دامنه."""
        # جدول انتقال وضعیت‌های مجاز
        transitions = {
            OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELED, OrderStatus.ON_HOLD],
            OrderStatus.PAID: [OrderStatus.PROCESSING, OrderStatus.CANCELED, OrderStatus.REFUNDED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELED, OrderStatus.REFUNDED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.REFUNDED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],  # در صورت بازگشت وجه
            OrderStatus.ON_HOLD: [OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.CANCELED],
            OrderStatus.CANCELED: [],  # نهایی
            OrderStatus.REFUNDED: [],  # نهایی
            OrderStatus.FAILED: [],  # نهایی
        }
        return new_status in transitions.get(self.status, [])

    def mark_as_paid(self, payment_id: str) -> None:
        """
        علامت‌گذاری سفارش به‌عنوان پرداخت‌شده.

        Args:
            payment_id: شناسه تراکنش پرداخت.

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی پرداخت را ندهد.
        """
        if self.status != OrderStatus.PENDING:
            raise ValidationError(
                message="تنها سفارشات با وضعیت PENDING قابلیت پرداخت دارند.",
                context={"order_number": self.order_number, "current_status": self.status.value},
            )
        self.payment_id = payment_id
        self.update_status(OrderStatus.PAID, "Payment successful")

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        لغو سفارش (در صورت امکان).

        Args:
            reason: دلیل لغو (اختیاری).

        Raises:
            ValidationError: اگر سفارش قابل لغو نباشد.
        """
        if not self.status.can_cancel():
            raise ValidationError(
                message="سفارش در وضعیت فعلی قابل لغو نیست.",
                context={"order_number": self.order_number, "current_status": self.status.value},
            )
        self.update_status(OrderStatus.CANCELED, reason or "Cancelled by user/system")

    def refund(self, reason: Optional[str] = None) -> None:
        """
        بازگشت وجه سفارش (در صورت امکان).

        Args:
            reason: دلیل بازگشت وجه (اختیاری).

        Raises:
            ValidationError: اگر سفارش قابل بازگشت نباشد.
        """
        if not self.status.can_refund():
            raise ValidationError(
                message="سفارش در وضعیت فعلی قابل بازگشت نیست.",
                context={"order_number": self.order_number, "current_status": self.status.value},
            )
        self.update_status(OrderStatus.REFUNDED, reason or "Refund requested")

    def is_paid(self) -> bool:
        """بررسی پرداخت‌شده بودن سفارش."""
        return self.status.is_paid()

    def is_final(self) -> bool:
        """بررسی نهایی بودن وضعیت سفارش."""
        return self.status.is_final()

    def is_active(self) -> bool:
        """بررسی فعال بودن سفارش (در جریان پردازش)."""
        return self.status.is_active()

    def get_total_items(self) -> int:
        """دریافت تعداد کل آیتم‌های سفارش."""
        return sum(item.quantity for item in self.items)

    def get_total_quantity(self) -> int:
        """دریافت تعداد کل محصولات (جمع تعداد آیتم‌ها)."""
        return self.get_total_items()

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل موجودیت سفارش به دیکشنری.

        Returns:
            دیکشنری شامل اطلاعات سفارش.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_number": self.order_number,
            "items": [item.to_dict() for item in self.items],
            "subtotal": self.subtotal.amount,
            "discount_amount": self.discount_amount.amount,
            "total_amount": self.total_amount.amount,
            "currency": self.total_amount.currency,
            "coupon_code": self.coupon_code,
            "status": self.status.value,
            "payment_id": self.payment_id,
            "shipping_address": self.shipping_address,
            "tracking_code": self.tracking_code,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        """
        ساخت موجودیت سفارش از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات سفارش.

        Returns:
            نمونه‌ای از کلاس Order.
        """
        # تبدیل آیتم‌ها
        items = []
        for item_data in data.get("items", []):
            unit_price = Money(item_data["unit_price"], item_data.get("currency", "IRR"))
            item = OrderItem(
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                quantity=item_data["quantity"],
                unit_price=unit_price,
                metadata=item_data.get("metadata", {}),
            )
            items.append(item)

        # تبدیل تاریخ‌ها
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

        # تبدیل وضعیت
        status = OrderStatus.from_string(data.get("status", "pending"))
        if not status:
            status = OrderStatus.PENDING

        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            order_number=data["order_number"],
            items=items,
            subtotal=Money(data["subtotal"], data.get("currency", "IRR")),
            total_amount=Money(data["total_amount"], data.get("currency", "IRR")),
            discount_amount=Money(data.get("discount_amount", 0), data.get("currency", "IRR")),
            coupon_code=data.get("coupon_code"),
            status=status,
            payment_id=data.get("payment_id"),
            shipping_address=data.get("shipping_address"),
            tracking_code=data.get("tracking_code"),
            notes=data.get("notes"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )