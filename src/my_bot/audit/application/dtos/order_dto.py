# my_bot_project/src/my_bot/application/dtos/order_dto.py
"""
DTOهای مربوط به سفارش (Order DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) برای مدیریت
سفارشات در سیستم است. تمام DTOها از Pydantic برای اعتبارسنجی داده‌ها
استفاده می‌کنند و شامل نوع‌دهی کامل (Type Hints) هستند.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator, field_validator

from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.domain.value_objects.money import Money


class OrderItemDTO(BaseModel):
    """
    DTO برای آیتم سفارش.

    Attributes:
        product_id: شناسه محصول.
        product_name: نام محصول.
        quantity: تعداد.
        unit_price: قیمت واحد.
        total_price: قیمت کل (محاسبه‌شده).
        currency: واحد پول.
        metadata: داده‌های اضافی.
    """
    product_id: str = Field(..., description="شناسه محصول")
    product_name: str = Field(..., max_length=255, description="نام محصول")
    quantity: int = Field(..., gt=0, description="تعداد")
    unit_price: float = Field(..., gt=0, description="قیمت واحد")
    total_price: float = Field(0.0, description="قیمت کل")
    currency: str = Field("IRR", max_length=3, description="واحد پول")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("total_price", mode="before")
    @classmethod
    def calculate_total_price(cls, v, info) -> float:
        """محاسبه قیمت کل در صورت عدم وجود."""
        if v is not None and v > 0:
            return v
        # محاسبه از روی unit_price و quantity
        data = info.data
        if "unit_price" in data and "quantity" in data:
            return data["unit_price"] * data["quantity"]
        return 0.0

    @classmethod
    def from_entity(cls, item) -> "OrderItemDTO":
        """
        ساخت DTO از موجودیت OrderItem.

        Args:
            item: موجودیت OrderItem.

        Returns:
            OrderItemDTO: DTO ساخته‌شده.
        """
        return cls(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=float(item.unit_price.amount),
            total_price=float(item.total_price.amount),
            currency=item.unit_price.currency,
            metadata=item.metadata,
        )


class OrderCreateDTO(BaseModel):
    """
    DTO برای ایجاد سفارش جدید.

    Attributes:
        items: لیست آیتم‌های سفارش.
        shipping_address: آدرس تحویل (اختیاری).
        notes: یادداشت (اختیاری).
        coupon_code: کد تخفیف (اختیاری).
        ip_address: آدرس IP کاربر (اختیاری).
        user_agent: مرورگر کاربر (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
    """
    items: List[OrderItemDTO] = Field(..., min_length=1, description="لیست آیتم‌های سفارش")
    shipping_address: Optional[str] = Field(None, max_length=500, description="آدرس تحویل")
    notes: Optional[str] = Field(None, max_length=1000, description="یادداشت")
    coupon_code: Optional[str] = Field(None, max_length=50, description="کد تخفیف")
    ip_address: Optional[str] = Field(None, description="آدرس IP کاربر")
    user_agent: Optional[str] = Field(None, max_length=500, description="مرورگر کاربر")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("items")
    @classmethod
    def validate_items(cls, items: List[OrderItemDTO]) -> List[OrderItemDTO]:
        """اعتبارسنجی آیتم‌های سفارش."""
        if not items:
            raise ValueError("سفارش باید حداقل یک آیتم داشته باشد.")
        # بررسی یکتایی product_id
        product_ids = [item.product_id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("شناسه محصولات در آیتم‌های سفارش باید یکتا باشد.")
        return items


class OrderUpdateDTO(BaseModel):
    """
    DTO برای به‌روزرسانی سفارش.

    Attributes:
        status: وضعیت جدید سفارش (اختیاری).
        shipping_address: آدرس تحویل جدید (اختیاری).
        tracking_code: کد رهگیری جدید (اختیاری).
        notes: یادداشت جدید (اختیاری).
        metadata: داده‌های اضافی جدید (اختیاری).
    """
    status: Optional[OrderStatus] = Field(None, description="وضعیت جدید سفارش")
    shipping_address: Optional[str] = Field(None, max_length=500, description="آدرس تحویل جدید")
    tracking_code: Optional[str] = Field(None, max_length=100, description="کد رهگیری جدید")
    notes: Optional[str] = Field(None, max_length=1000, description="یادداشت جدید")
    metadata: Optional[Dict[str, Any]] = Field(None, description="داده‌های اضافی جدید")


class OrderResponseDTO(BaseModel):
    """
    DTO برای پاسخ اطلاعات سفارش.

    Attributes:
        id: شناسه سفارش.
        user_id: شناسه کاربر.
        order_number: شماره سفارش.
        items: لیست آیتم‌های سفارش.
        subtotal: مبلغ پایه.
        discount_amount: مبلغ تخفیف.
        total_amount: مبلغ کل.
        currency: واحد پول.
        coupon_code: کد تخفیف استفاده‌شده (اختیاری).
        status: وضعیت سفارش.
        payment_id: شناسه پرداخت (اختیاری).
        shipping_address: آدرس تحویل (اختیاری).
        tracking_code: کد رهگیری (اختیاری).
        notes: یادداشت (اختیاری).
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    id: Optional[int] = Field(None, description="شناسه سفارش")
    user_id: int = Field(..., description="شناسه کاربر")
    order_number: str = Field(..., description="شماره سفارش")
    items: List[OrderItemDTO] = Field(..., description="لیست آیتم‌های سفارش")
    subtotal: float = Field(..., description="مبلغ پایه")
    discount_amount: float = Field(0.0, description="مبلغ تخفیف")
    total_amount: float = Field(..., description="مبلغ کل")
    currency: str = Field("IRR", description="واحد پول")
    coupon_code: Optional[str] = Field(None, description="کد تخفیف استفاده‌شده")
    status: OrderStatus = Field(OrderStatus.PENDING, description="وضعیت سفارش")
    payment_id: Optional[str] = Field(None, description="شناسه پرداخت")
    shipping_address: Optional[str] = Field(None, description="آدرس تحویل")
    tracking_code: Optional[str] = Field(None, description="کد رهگیری")
    notes: Optional[str] = Field(None, description="یادداشت")
    created_at: datetime = Field(default_factory=datetime.now, description="زمان ایجاد")
    updated_at: datetime = Field(default_factory=datetime.now, description="زمان آخرین به‌روزرسانی")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, order) -> "OrderResponseDTO":
        """
        ساخت DTO از موجودیت سفارش.

        Args:
            order: موجودیت Order.

        Returns:
            OrderResponseDTO: DTO ساخته‌شده.
        """
        return cls(
            id=order.id,
            user_id=order.user_id,
            order_number=order.order_number,
            items=[OrderItemDTO.from_entity(item) for item in order.items],
            subtotal=float(order.subtotal.amount),
            discount_amount=float(order.discount_amount.amount) if order.discount_amount else 0.0,
            total_amount=float(order.total_amount.amount),
            currency=order.total_amount.currency,
            coupon_code=order.coupon_code,
            status=order.status,
            payment_id=order.payment_id,
            shipping_address=order.shipping_address,
            tracking_code=order.tracking_code,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            metadata=order.metadata,
        )

    def to_entity(self) -> dict:
        """
        تبدیل DTO به دیکشنری برای استفاده در موجودیت.

        Returns:
            dict: دیکشنری اطلاعات سفارش.
        """
        return {
            "user_id": self.user_id,
            "order_number": self.order_number,
            "items": [item.model_dump() for item in self.items],
            "subtotal": self.subtotal,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "coupon_code": self.coupon_code,
            "status": self.status.value if self.status else "pending",
            "payment_id": self.payment_id,
            "shipping_address": self.shipping_address,
            "tracking_code": self.tracking_code,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    def get_formatted_total(self) -> str:
        """
        دریافت مبلغ کل به‌صورت فرمت‌شده.

        Returns:
            str: مبلغ فرمت‌شده با واحد پول.
        """
        if self.currency == "IRR":
            toman = self.total_amount / 10
            return f"{toman:,.0f} تومان"
        return f"{self.total_amount:,.2f} {self.currency}"

    def get_summary(self) -> str:
        """
        دریافت خلاصه سفارش به‌صورت متن.

        Returns:
            str: خلاصه سفارش.
        """
        items_summary = ", ".join([f"{item.product_name} (x{item.quantity})" for item in self.items[:3]])
        if len(self.items) > 3:
            items_summary += f" و {len(self.items) - 3} آیتم دیگر"
        return f"سفارش #{self.order_number}: {items_summary} - {self.get_formatted_total()}"