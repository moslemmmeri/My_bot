# my_bot_project/src/my_bot/application/dtos/user_dto.py
"""
DTOهای مربوط به کاربر (User DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) برای مدیریت
کاربران در سیستم است. تمام DTOها از Pydantic برای اعتبارسنجی داده‌ها
استفاده می‌کنند و شامل نوع‌دهی کامل (Type Hints) هستند.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator

from my_bot.core.constants.user_roles import UserRole
from my_bot.domain.value_objects.user_level import UserLevel


class UserCreateDTO(BaseModel):
    """
    DTO برای ایجاد کاربر جدید.

    Attributes:
        telegram_id: شناسه تلگرام کاربر (اجباری).
        username: نام کاربری تلگرام (اختیاری).
        first_name: نام کوچک (اختیاری).
        last_name: نام خانوادگی (اختیاری).
        phone_number: شماره تماس (اختیاری).
        email: آدرس ایمیل (اختیاری).
        role: نقش کاربری (پیش‌فرض: USER).
        metadata: داده‌های اضافی (اختیاری).
    """
    telegram_id: int = Field(..., gt=0, description="شناسه تلگرام کاربر")
    username: Optional[str] = Field(None, max_length=32, description="نام کاربری تلگرام")
    first_name: Optional[str] = Field(None, max_length=64, description="نام کوچک")
    last_name: Optional[str] = Field(None, max_length=64, description="نام خانوادگی")
    phone_number: Optional[str] = Field(None, description="شماره تماس")
    email: Optional[EmailStr] = Field(None, description="آدرس ایمیل")
    role: UserRole = Field(UserRole.USER, description="نقش کاربری")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @validator("phone_number")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی شماره تلفن."""
        if v is None:
            return v
        # حذف فضاها و کاراکترهای اضافی
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError("شماره تلفن باید بین ۱۰ تا ۱۵ رقم باشد")
        return cleaned


class UserUpdateDTO(BaseModel):
    """
    DTO برای به‌روزرسانی اطلاعات کاربر.

    Attributes:
        username: نام کاربری جدید (اختیاری).
        first_name: نام کوچک جدید (اختیاری).
        last_name: نام خانوادگی جدید (اختیاری).
        phone_number: شماره تماس جدید (اختیاری).
        email: آدرس ایمیل جدید (اختیاری).
        role: نقش کاربری جدید (اختیاری).
        is_active: وضعیت فعال بودن (اختیاری).
        is_banned: وضعیت مسدود بودن (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
    """
    username: Optional[str] = Field(None, max_length=32, description="نام کاربری جدید")
    first_name: Optional[str] = Field(None, max_length=64, description="نام کوچک جدید")
    last_name: Optional[str] = Field(None, max_length=64, description="نام خانوادگی جدید")
    phone_number: Optional[str] = Field(None, description="شماره تماس جدید")
    email: Optional[EmailStr] = Field(None, description="آدرس ایمیل جدید")
    role: Optional[UserRole] = Field(None, description="نقش کاربری جدید")
    is_active: Optional[bool] = Field(None, description="وضعیت فعال بودن")
    is_banned: Optional[bool] = Field(None, description="وضعیت مسدود بودن")
    metadata: Optional[Dict[str, Any]] = Field(None, description="داده‌های اضافی")

    @validator("phone_number")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی شماره تلفن."""
        if v is None:
            return v
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError("شماره تلفن باید بین ۱۰ تا ۱۵ رقم باشد")
        return cleaned


class UserResponseDTO(BaseModel):
    """
    DTO برای پاسخ اطلاعات کاربر.

    Attributes:
        id: شناسه کاربر.
        telegram_id: شناسه تلگرام.
        username: نام کاربری.
        first_name: نام کوچک.
        last_name: نام خانوادگی.
        full_name: نام کامل (محاسبه‌شده).
        phone_number: شماره تماس.
        email: آدرس ایمیل.
        role: نقش کاربری.
        level: سطح کاربری.
        points: امتیاز.
        is_active: وضعیت فعال بودن.
        is_banned: وضعیت مسدود بودن.
        last_activity: زمان آخرین فعالیت.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    id: Optional[int] = Field(None, description="شناسه کاربر")
    telegram_id: Optional[int] = Field(None, description="شناسه تلگرام")
    username: Optional[str] = Field(None, description="نام کاربری")
    first_name: Optional[str] = Field(None, description="نام کوچک")
    last_name: Optional[str] = Field(None, description="نام خانوادگی")
    full_name: str = Field("", description="نام کامل")
    phone_number: Optional[str] = Field(None, description="شماره تماس")
    email: Optional[str] = Field(None, description="آدرس ایمیل")
    role: UserRole = Field(UserRole.USER, description="نقش کاربری")
    level: UserLevel = Field(UserLevel.BRONZE, description="سطح کاربری")
    points: int = Field(0, description="امتیاز")
    is_active: bool = Field(True, description="وضعیت فعال بودن")
    is_banned: bool = Field(False, description="وضعیت مسدود بودن")
    last_activity: Optional[datetime] = Field(None, description="زمان آخرین فعالیت")
    created_at: datetime = Field(default_factory=datetime.now, description="زمان ایجاد")
    updated_at: datetime = Field(default_factory=datetime.now, description="زمان آخرین به‌روزرسانی")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, user) -> "UserResponseDTO":
        """
        ساخت DTO از موجودیت کاربر.

        Args:
            user: موجودیت User.

        Returns:
            UserResponseDTO: DTO ساخته‌شده.
        """
        return cls(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone_number=user.phone_number,
            email=user.email,
            role=user.role,
            level=user.level,
            points=user.points,
            is_active=user.is_active,
            is_banned=user.is_banned,
            last_activity=user.last_activity,
            created_at=user.created_at,
            updated_at=user.updated_at,
            metadata=user.metadata,
        )


class UserProfileDTO(UserResponseDTO):
    """
    DTO برای پروفایل کامل کاربر (با آمار اضافی).

    Attributes:
        total_orders: تعداد کل سفارشات.
        total_spent: مجموع مبلغ پرداختی.
        average_order_value: میانگین مبلغ هر سفارش.
        last_order_date: تاریخ آخرین سفارش.
        level_progress: درصد پیشرفت به سطح بعدی.
        next_level: سطح بعدی (در صورت وجود).
        points_to_next_level: امتیاز مورد نیاز برای ارتقاء.
    """
    total_orders: int = Field(0, description="تعداد کل سفارشات")
    total_spent: float = Field(0.0, description="مجموع مبلغ پرداختی")
    average_order_value: float = Field(0.0, description="میانگین مبلغ هر سفارش")
    last_order_date: Optional[datetime] = Field(None, description="تاریخ آخرین سفارش")
    level_progress: float = Field(0.0, description="درصد پیشرفت به سطح بعدی")
    next_level: Optional[UserLevel] = Field(None, description="سطح بعدی")
    points_to_next_level: Optional[int] = Field(None, description="امتیاز مورد نیاز برای ارتقاء")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, user, stats: Optional[Dict[str, Any]] = None) -> "UserProfileDTO":
        """
        ساخت DTO پروفایل از موجودیت کاربر و آمار.

        Args:
            user: موجودیت User.
            stats: آمار اضافی (اختیاری).

        Returns:
            UserProfileDTO: DTO پروفایل ساخته‌شده.
        """
        stats = stats or {}

        # محاسبه پیشرفت سطح
        current_level = user.level
        next_level = current_level.next_level
        points_to_next_level = None
        level_progress = 0.0

        if next_level:
            points_to_next_level = current_level.points_to_next_level(user.points)
            level_progress = current_level.get_progress(user.points)

        return cls(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone_number=user.phone_number,
            email=user.email,
            role=user.role,
            level=user.level,
            points=user.points,
            is_active=user.is_active,
            is_banned=user.is_banned,
            last_activity=user.last_activity,
            created_at=user.created_at,
            updated_at=user.updated_at,
            metadata=user.metadata,
            total_orders=stats.get("total_orders", 0),
            total_spent=stats.get("total_spent", 0.0),
            average_order_value=stats.get("average_order_value", 0.0),
            last_order_date=stats.get("last_order_date"),
            level_progress=level_progress,
            next_level=next_level,
            points_to_next_level=points_to_next_level,
        )