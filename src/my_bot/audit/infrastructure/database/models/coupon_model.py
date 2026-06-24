# my_bot_project/src/my_bot/infrastructure/database/models/coupon_model.py
"""
مدل SQLAlchemy برای جدول کوپن‌های تخفیف (CouponModel).

این مدل معادل موجودیت Coupon در لایه دامنه است و نگاشت به جدول coupons را انجام می‌دهد.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from my_bot.infrastructure.database.models import Base
from my_bot.domain.entities.coupon import Coupon, CouponType
from my_bot.domain.value_objects.money import Money


class CouponModel(Base):
    """
    مدل SQLAlchemy برای جدول coupons.

    Attributes:
        id: شناسه یکتای کوپن (Primary Key)
        code: کد تخفیف (Unique, Not Null)
        description: توضیحات کوپن
        discount_type: نوع تخفیف (percentage, fixed)
        discount_value: مقدار تخفیف
        currency: واحد پول
        min_order_amount: حداقل مبلغ سفارش برای استفاده
        max_discount_amount: حداکثر مبلغ تخفیف قابل اعمال
        usage_limit: تعداد دفعات مجاز استفاده (کل)
        usage_count: تعداد دفعات استفاده‌شده تاکنون
        user_usage_limit: حداکثر تعداد استفاده برای هر کاربر
        user_usage_count: دیکشنری نگاشت شناسه کاربر به تعداد استفاده (JSON)
        valid_from: تاریخ شروع اعتبار
        valid_until: تاریخ پایان اعتبار
        is_active: وضعیت فعال بودن
        applicable_products: لیست شناسه محصولات قابل اعمال (JSON)
        applicable_users: لیست شناسه کاربران مجاز (JSON)
        created_at: زمان ایجاد
        updated_at: زمان آخرین به‌روزرسانی
        metadata: داده‌های اضافی (JSON)
    """

    __tablename__ = "coupons"

    # ----------------------------------------------
    # ستون‌های اصلی
    # ----------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # نوع و مقدار تخفیف
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="IRR")

    # محدودیت‌های مبلغ
    min_order_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    max_discount_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)

    # محدودیت‌های استفاده
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    user_usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    user_usage_count: Mapped[Optional[Dict[int, int]]] = mapped_column(JSON, nullable=True)

    # تاریخ‌های اعتبار
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # وضعیت
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)

    # فیلترهای اعمال
    applicable_products: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    applicable_users: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)

    # زمان‌های سیستمی
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # داده‌های اضافی
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ----------------------------------------------
    # ایندکس‌های اضافی
    # ----------------------------------------------
    __table_args__ = (
        Index("ix_coupons_valid_dates", "valid_from", "valid_until"),
        Index("ix_coupons_is_active", "is_active"),
    )

    # ----------------------------------------------
    # متدهای تبدیل به/از دامنه
    # ----------------------------------------------
    def to_domain(self) -> Coupon:
        """
        تبدیل مدل SQLAlchemy به موجودیت دامنه Coupon.

        Returns:
            Coupon: موجودیت دامنه.
        """
        return Coupon(
            id=self.id,
            code=self.code,
            description=self.description,
            discount_type=CouponType(self.discount_type) if self.discount_type else CouponType.FIXED,
            discount_value=self.discount_value,
            currency=self.currency,
            min_order_amount=Money(self.min_order_amount, self.currency) if self.min_order_amount is not None else None,
            max_discount_amount=Money(self.max_discount_amount, self.currency) if self.max_discount_amount is not None else None,
            usage_limit=self.usage_limit,
            usage_count=self.usage_count,
            user_usage_limit=self.user_usage_limit,
            user_usage_count=self.user_usage_count or {},
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            is_active=self.is_active,
            applicable_products=self.applicable_products or [],
            applicable_users=self.applicable_users or [],
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata or {},
        )

    @classmethod
    def from_domain(cls, coupon: Coupon) -> "CouponModel":
        """
        ساخت مدل SQLAlchemy از موجودیت دامنه Coupon.

        Args:
            coupon: موجودیت دامنه.

        Returns:
            CouponModel: مدل SQLAlchemy.
        """
        return cls(
            id=coupon.id,
            code=coupon.code,
            description=coupon.description,
            discount_type=coupon.discount_type.value if coupon.discount_type else CouponType.FIXED.value,
            discount_value=coupon.discount_value,
            currency=coupon.currency,
            min_order_amount=float(coupon.min_order_amount.amount) if coupon.min_order_amount else None,
            max_discount_amount=float(coupon.max_discount_amount.amount) if coupon.max_discount_amount else None,
            usage_limit=coupon.usage_limit,
            usage_count=coupon.usage_count,
            user_usage_limit=coupon.user_usage_limit,
            user_usage_count=coupon.user_usage_count,
            valid_from=coupon.valid_from,
            valid_until=coupon.valid_until,
            is_active=coupon.is_active,
            applicable_products=coupon.applicable_products,
            applicable_users=coupon.applicable_users,
            created_at=coupon.created_at,
            updated_at=coupon.updated_at,
            metadata=coupon.metadata,
        )

    def __repr__(self) -> str:
        """نمایش رشته‌ای مدل."""
        return f"<CouponModel(id={self.id}, code={self.code}, discount={self.discount_value} {self.discount_type}, is_active={self.is_active})>"