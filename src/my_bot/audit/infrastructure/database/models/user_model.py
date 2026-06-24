# my_bot_project/src/my_bot/infrastructure/database/models/user_model.py
"""
مدل SQLAlchemy برای جدول کاربران (UserModel).

این مدل معادل موجودیت User در لایه دامنه است و نگاشت به جدول users را انجام می‌دهد.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
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
from my_bot.core.constants.user_roles import UserRole
from my_bot.domain.value_objects.user_level import UserLevel
from my_bot.domain.entities.user import User


class UserModel(Base):
    """
    مدل SQLAlchemy برای جدول users.

    Attributes:
        id: شناسه یکتای کاربر (Primary Key)
        telegram_id: شناسه تلگرام کاربر (Unique, Not Null)
        username: نام کاربری تلگرام
        first_name: نام کوچک
        last_name: نام خانوادگی
        phone_number: شماره تماس
        email: آدرس ایمیل
        role: نقش کاربری (پیش‌فرض: user)
        level: سطح کاربری (پیش‌فرض: bronze)
        points: امتیاز کاربر (پیش‌فرض: ۰)
        is_active: فعال بودن حساب
        is_banned: مسدود بودن
        last_activity: زمان آخرین فعالیت
        created_at: زمان ایجاد
        updated_at: زمان آخرین به‌روزرسانی
        metadata: داده‌های اضافی (JSON)

        # فیلدهای اضافه شده در مهاجرت ۰۰۲
        language: زبان کاربر
        timezone: منطقه زمانی
        avatar_url: آدرس تصویر پروفایل
        bio: بیوگرافی
        last_login: زمان آخرین ورود
        login_count: تعداد ورودها
        referral_code: کد معرف
        referred_by: شناسه کاربر معرف

    Relationships:
        orders: سفارشات کاربر
        payments: تراکنش‌های پرداخت کاربر
        tickets: تیکت‌های ایجادشده توسط کاربر
        feedbacks: بازخوردهای کاربر
        broadcasts: ارسال‌های گروهی ایجادشده توسط کاربر
        audit_logs: لاگ‌های حسابرسی کاربر
        forms_created: فرم‌های ساخته‌شده توسط کاربر
        form_responses: پاسخ‌های فرم کاربر
    """

    __tablename__ = "users"

    # ----------------------------------------------
    # ستون‌های اصلی
    # ----------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # نقش و سطح
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="user", index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="bronze", index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # وضعیت
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # زمان‌ها
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # داده‌های اضافی
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ----------------------------------------------
    # فیلدهای اضافه‌شده در مهاجرت ۰۰۲
    # ----------------------------------------------
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True, index=True)
    referred_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # ----------------------------------------------
    # روابط (Relationships)
    # ----------------------------------------------
    # سفارشات
    orders: Mapped[List["OrderModel"]] = relationship(
        "OrderModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # تراکنش‌های پرداخت
    payments: Mapped[List["PaymentModel"]] = relationship(
        "PaymentModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # تیکت‌ها (به‌عنوان ایجادکننده)
    tickets: Mapped[List["TicketModel"]] = relationship(
        "TicketModel",
        foreign_keys="TicketModel.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # تیکت‌های اختصاص‌یافته (به‌عنوان مسئول)
    assigned_tickets: Mapped[List["TicketModel"]] = relationship(
        "TicketModel",
        foreign_keys="TicketModel.assigned_to",
        back_populates="assignee",
        lazy="selectin",
    )

    # بازخوردها
    feedbacks: Mapped[List["FeedbackModel"]] = relationship(
        "FeedbackModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ارسال‌های گروهی (به‌عنوان ایجادکننده)
    broadcasts: Mapped[List["BroadcastModel"]] = relationship(
        "BroadcastModel",
        back_populates="creator",
        lazy="selectin",
    )

    # لاگ‌های حسابرسی
    audit_logs: Mapped[List["AuditLogModel"]] = relationship(
        "AuditLogModel",
        back_populates="user",
        lazy="selectin",
    )

    # فرم‌های ساخته‌شده
    forms_created: Mapped[List["FormModel"]] = relationship(
        "FormModel",
        foreign_keys="FormModel.created_by",
        back_populates="creator",
        lazy="selectin",
    )

    # پاسخ‌های فرم
    form_responses: Mapped[List["FormResponseModel"]] = relationship(
        "FormResponseModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # کاربران معرفی‌شده
    referred_users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        remote_side=[id],
        backref="referrer",
        lazy="selectin",
    )

    # ----------------------------------------------
    # ایندکس‌های اضافی (تعریف شده در متادیتا)
    # ----------------------------------------------
    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_level", "level"),
        Index("ix_users_language", "language"),
        Index("ix_users_last_login", "last_login"),
        Index("ix_users_referral_code", "referral_code"),
    )

    # ----------------------------------------------
    # متدهای تبدیل به/از دامنه
    # ----------------------------------------------
    def to_domain(self) -> User:
        """
        تبدیل مدل SQLAlchemy به موجودیت دامنه User.

        Returns:
            User: موجودیت دامنه.
        """
        return User(
            id=self.id,
            telegram_id=self.telegram_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            phone_number=self.phone_number,
            email=self.email,
            role=UserRole(self.role) if self.role else UserRole.USER,
            level=UserLevel(self.level) if self.level else UserLevel.BRONZE,
            points=self.points,
            is_active=self.is_active,
            is_banned=self.is_banned,
            last_activity=self.last_activity,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata or {},
        )

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        """
        ساخت مدل SQLAlchemy از موجودیت دامنه User.

        Args:
            user: موجودیت دامنه.

        Returns:
            UserModel: مدل SQLAlchemy.
        """
        return cls(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            email=user.email,
            role=user.role.value if user.role else UserRole.USER.value,
            level=user.level.value if user.level else UserLevel.BRONZE.value,
            points=user.points,
            is_active=user.is_active,
            is_banned=user.is_banned,
            last_activity=user.last_activity,
            created_at=user.created_at,
            updated_at=user.updated_at,
            metadata=user.metadata,
        )

    def __repr__(self) -> str:
        """نمایش رشته‌ای مدل."""
        return f"<UserModel(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"