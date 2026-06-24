# my_bot_project/src/my_bot/infrastructure/database/models/payment_model.py
"""
مدل SQLAlchemy برای جدول تراکنش‌های پرداخت (PaymentModel).

این مدل معادل موجودیت Payment در لایه دامنه است و نگاشت به جدول payments را انجام می‌دهد.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Integer,
    String,
    Numeric,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from my_bot.infrastructure.database.models import Base
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.domain.entities.payment import Payment
from my_bot.domain.value_objects.money import Money


class PaymentModel(Base):
    """
    مدل SQLAlchemy برای جدول payments.

    Attributes:
        id: شناسه یکتای تراکنش (Primary Key)
        user_id: شناسه کاربر پرداخت‌کننده (Foreign Key to users.id)
        order_id: شناسه سفارش مرتبط (اختیاری)
        amount: مبلغ پرداختی
        currency: واحد پول
        status: وضعیت پرداخت
        gateway: نام درگاه پرداخت
        transaction_id: شناسه تراکنش در درگاه
        tracking_code: کد رهگیری پرداخت
        reference_id: شناسه مرجع در سیستم درگاه
        callback_url: آدرس بازگشت پس از پرداخت
        callback_data: داده‌های دریافتی از درگاه (JSON)
        paid_at: زمان پرداخت موفق
        expired_at: زمان انقضای پرداخت
        retry_count: تعداد تلاش‌های مجدد
        description: توضیحات پرداخت
        error_message: پیام خطا (در صورت وجود)
        created_at: زمان ایجاد تراکنش
        updated_at: زمان آخرین به‌روزرسانی
        metadata: داده‌های اضافی (JSON)

    Relationships:
        user: کاربر پرداخت‌کننده
        order: سفارش مرتبط (اختیاری)
    """

    __tablename__ = "payments"

    # ----------------------------------------------
    # ستون‌های اصلی
    # ----------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # مبالغ
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="IRR")

    # وضعیت و درگاه
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending", index=True)
    gateway: Mapped[str] = mapped_column(String(50), nullable=False, server_default="mock")

    # شناسه‌ها
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    tracking_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # اطلاعات callback
    callback_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    callback_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # زمان‌ها
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # آمار و خطاها
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # زمان‌های سیستمی
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # داده‌های اضافی
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ----------------------------------------------
    # روابط (Relationships)
    # ----------------------------------------------
    # کاربر پرداخت‌کننده
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="payments",
        lazy="selectin",
    )

    # سفارش مرتبط (اختیاری)
    # از آنجا که order_id یک رشته است، نمی‌توانیم مستقیماً ForeignKey تعیین کنیم
    # اما در صورت نیاز، می‌توانیم یک رابطه با OrderModel ایجاد کنیم
    # این رابطه از طریق شناسه سفارش برقرار می‌شود (در صورت وجود)
    # برای جلوگیری از پیچیدگی، اینجا تعریف نمی‌شود و در OrderModel تعریف می‌شود

    # ----------------------------------------------
    # ایندکس‌های اضافی
    # ----------------------------------------------
    __table_args__ = (
        Index("ix_payments_user_status", "user_id", "status"),
        Index("ix_payments_created_at", "created_at"),
        Index("ix_payments_transaction_id", "transaction_id"),
        Index("ix_payments_tracking_code", "tracking_code"),
    )

    # ----------------------------------------------
    # متدهای تبدیل به/از دامنه
    # ----------------------------------------------
    def to_domain(self) -> Payment:
        """
        تبدیل مدل SQLAlchemy به موجودیت دامنه Payment.

        Returns:
            Payment: موجودیت دامنه.
        """
        return Payment(
            id=self.id,
            user_id=self.user_id,
            order_id=self.order_id,
            amount=Money(self.amount, self.currency),
            currency=self.currency,
            status=PaymentStatus(self.status) if self.status else PaymentStatus.PENDING,
            gateway=self.gateway,
            transaction_id=self.transaction_id,
            tracking_code=self.tracking_code,
            reference_id=self.reference_id,
            callback_url=self.callback_url,
            callback_data=self.callback_data,
            paid_at=self.paid_at,
            expired_at=self.expired_at,
            retry_count=self.retry_count,
            description=self.description,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata or {},
        )

    @classmethod
    def from_domain(cls, payment: Payment) -> "PaymentModel":
        """
        ساخت مدل SQLAlchemy از موجودیت دامنه Payment.

        Args:
            payment: موجودیت دامنه.

        Returns:
            PaymentModel: مدل SQLAlchemy.
        """
        return cls(
            id=payment.id,
            user_id=payment.user_id,
            order_id=payment.order_id,
            amount=float(payment.amount.amount),
            currency=payment.amount.currency,
            status=payment.status.value if payment.status else PaymentStatus.PENDING.value,
            gateway=payment.gateway,
            transaction_id=payment.transaction_id,
            tracking_code=payment.tracking_code,
            reference_id=payment.reference_id,
            callback_url=payment.callback_url,
            callback_data=payment.callback_data,
            paid_at=payment.paid_at,
            expired_at=payment.expired_at,
            retry_count=payment.retry_count,
            description=payment.description,
            error_message=payment.error_message,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            metadata=payment.metadata,
        )

    def __repr__(self) -> str:
        """نمایش رشته‌ای مدل."""
        return f"<PaymentModel(id={self.id}, user_id={self.user_id}, status={self.status}, amount={self.amount} {self.currency})>"