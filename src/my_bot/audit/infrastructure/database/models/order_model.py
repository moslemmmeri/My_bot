# my_bot_project/src/my_bot/infrastructure/database/models/order_model.py
"""
مدل SQLAlchemy برای جدول سفارشات (OrderModel).

این مدل معادل موجودیت Order در لایه دامنه است و نگاشت به جدول orders را انجام می‌دهد.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from my_bot.infrastructure.database.models import Base
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.domain.entities.order import Order
from my_bot.domain.value_objects.money import Money


class OrderModel(Base):
    """
    مدل SQLAlchemy برای جدول orders.

    Attributes:
        id: شناسه یکتای سفارش (Primary Key)
        user_id: شناسه کاربر (Foreign Key to users.id)
        order_number: شماره سفارش (Unique)
        subtotal: مبلغ پایه
        discount_amount: مبلغ تخفیف
        total_amount: مبلغ کل
        currency: واحد پول
        coupon_code: کد تخفیف استفاده‌شده
        status: وضعیت سفارش
        payment_id: شناسه پرداخت مرتبط
        shipping_address: آدرس تحویل
        tracking_code: کد رهگیری پستی
        notes: یادداشت‌ها
        created_at: زمان ایجاد
        updated_at: زمان آخرین به‌روزرسانی
        metadata: داده‌های اضافی (JSON)

    Relationships:
        user: کاربر صاحب سفارش
        items: آیتم‌های سفارش
        payment: پرداخت مرتبط (اختیاری)
    """

    __tablename__ = "orders"

    # ----------------------------------------------
    # ستون‌های اصلی
    # ----------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # مبالغ
    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, server_default="0.00")
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="IRR")

    # تخفیف و وضعیت
    coupon_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending", index=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # اطلاعات ارسال
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tracking_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # یادداشت‌ها
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # زمان‌ها
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # داده‌های اضافی
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ----------------------------------------------
    # روابط (Relationships)
    # ----------------------------------------------
    # کاربر
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="orders",
        lazy="selectin",
    )

    # آیتم‌های سفارش
    items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # پرداخت مرتبط (در صورت وجود)
    # این رابطه از طریق payment_id که به payments.id ارجاع می‌دهد، در PaymentModel تعریف شده است
    # برای جلوگیری از وابستگی دایره‌ای، این رابطه را در PaymentModel تعریف می‌کنیم

    # ----------------------------------------------
    # ایندکس‌های اضافی
    # ----------------------------------------------
    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        Index("ix_orders_created_at", "created_at"),
    )

    # ----------------------------------------------
    # متدهای تبدیل به/از دامنه
    # ----------------------------------------------
    def to_domain(self) -> Order:
        """
        تبدیل مدل SQLAlchemy به موجودیت دامنه Order.

        Returns:
            Order: موجودیت دامنه.
        """
        from my_bot.infrastructure.database.models.order_item_model import OrderItemModel

        # تبدیل آیتم‌ها
        items = []
        for item_model in self.items or []:
            items.append(item_model.to_domain())

        return Order(
            id=self.id,
            user_id=self.user_id,
            order_number=self.order_number,
            items=items,
            subtotal=Money(self.subtotal, self.currency),
            total_amount=Money(self.total_amount, self.currency),
            discount_amount=Money(self.discount_amount, self.currency),
            coupon_code=self.coupon_code,
            status=OrderStatus(self.status) if self.status else OrderStatus.PENDING,
            payment_id=self.payment_id,
            shipping_address=self.shipping_address,
            tracking_code=self.tracking_code,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata or {},
        )

    @classmethod
    def from_domain(cls, order: Order) -> "OrderModel":
        """
        ساخت مدل SQLAlchemy از موجودیت دامنه Order.

        Args:
            order: موجودیت دامنه.

        Returns:
            OrderModel: مدل SQLAlchemy.
        """
        from my_bot.infrastructure.database.models.order_item_model import OrderItemModel

        # تبدیل آیتم‌ها
        items = []
        for item in order.items:
            items.append(OrderItemModel.from_domain(item))

        return cls(
            id=order.id,
            user_id=order.user_id,
            order_number=order.order_number,
            subtotal=float(order.subtotal.amount),
            discount_amount=float(order.discount_amount.amount) if order.discount_amount else 0.0,
            total_amount=float(order.total_amount.amount),
            currency=order.total_amount.currency,
            coupon_code=order.coupon_code,
            status=order.status.value if order.status else OrderStatus.PENDING.value,
            payment_id=order.payment_id,
            shipping_address=order.shipping_address,
            tracking_code=order.tracking_code,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            metadata=order.metadata,
            items=items,
        )

    def __repr__(self) -> str:
        """نمایش رشته‌ای مدل."""
        return f"<OrderModel(id={self.id}, order_number={self.order_number}, user_id={self.user_id}, status={self.status})>"