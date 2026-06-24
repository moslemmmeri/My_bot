# my_bot_project/src/my_bot/application/dtos/broadcast_dto.py
"""
DTOهای مربوط به ارسال گروهی (Broadcast DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) برای مدیریت
ارسال‌های گروهی در سیستم است. تمام DTOها از Pydantic برای اعتبارسنجی داده‌ها
استفاده می‌کنند و شامل نوع‌دهی کامل (Type Hints) هستند.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

from my_bot.domain.entities.broadcast import BroadcastStatus, BroadcastPriority, BroadcastType


class BroadcastFilterDTO(BaseModel):
    """
    DTO برای فیلترهای انتخاب کاربران هدف در ارسال گروهی.

    Attributes:
        user_ids: لیست شناسه‌های خاص کاربران (اختیاری).
        roles: لیست نقش‌های کاربری (اختیاری).
        levels: لیست سطوح کاربری (اختیاری).
        min_points: حداقل امتیاز (اختیاری).
        max_points: حداکثر امتیاز (اختیاری).
        is_active: وضعیت فعال بودن کاربر (اختیاری).
        is_banned: وضعیت مسدود بودن کاربر (اختیاری).
        created_after: تاریخ ایجاد بعد از (اختیاری).
        created_before: تاریخ ایجاد قبل از (اختیاری).
        last_activity_after: آخرین فعالیت بعد از (اختیاری).
        last_activity_before: آخرین فعالیت قبل از (اختیاری).
        tags: لیست برچسب‌ها (اختیاری).
        exclude_user_ids: لیست شناسه‌های کاربران برای حذف (اختیاری).
    """
    user_ids: Optional[List[int]] = Field(None, description="لیست شناسه‌های خاص کاربران")
    roles: Optional[List[str]] = Field(None, description="لیست نقش‌های کاربری")
    levels: Optional[List[str]] = Field(None, description="لیست سطوح کاربری")
    min_points: Optional[int] = Field(None, ge=0, description="حداقل امتیاز")
    max_points: Optional[int] = Field(None, ge=0, description="حداکثر امتیاز")
    is_active: Optional[bool] = Field(None, description="وضعیت فعال بودن کاربر")
    is_banned: Optional[bool] = Field(None, description="وضعیت مسدود بودن کاربر")
    created_after: Optional[datetime] = Field(None, description="تاریخ ایجاد بعد از")
    created_before: Optional[datetime] = Field(None, description="تاریخ ایجاد قبل از")
    last_activity_after: Optional[datetime] = Field(None, description="آخرین فعالیت بعد از")
    last_activity_before: Optional[datetime] = Field(None, description="آخرین فعالیت قبل از")
    tags: Optional[List[str]] = Field(None, description="لیست برچسب‌ها")
    exclude_user_ids: Optional[List[int]] = Field(None, description="لیست شناسه‌های کاربران برای حذف")

    @model_validator(mode="after")
    def validate_points(self) -> "BroadcastFilterDTO":
        """اعتبارسنجی امتیازها."""
        if self.min_points is not None and self.max_points is not None:
            if self.min_points > self.max_points:
                raise ValueError("حداقل امتیاز نمی‌تواند بیشتر از حداکثر امتیاز باشد.")
        return self

    @model_validator(mode="after")
    def validate_dates(self) -> "BroadcastFilterDTO":
        """اعتبارسنجی تاریخ‌ها."""
        if self.created_after and self.created_before and self.created_after > self.created_before:
            raise ValueError("تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")
        if self.last_activity_after and self.last_activity_before and self.last_activity_after > self.last_activity_before:
            raise ValueError("تاریخ آخرین فعالیت شروع نمی‌تواند بعد از تاریخ پایان باشد.")
        return self

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری."""
        return {
            "user_ids": self.user_ids,
            "roles": self.roles,
            "levels": self.levels,
            "min_points": self.min_points,
            "max_points": self.max_points,
            "is_active": self.is_active,
            "is_banned": self.is_banned,
            "created_after": self.created_after.isoformat() if self.created_after else None,
            "created_before": self.created_before.isoformat() if self.created_before else None,
            "last_activity_after": self.last_activity_after.isoformat() if self.last_activity_after else None,
            "last_activity_before": self.last_activity_before.isoformat() if self.last_activity_before else None,
            "tags": self.tags,
            "exclude_user_ids": self.exclude_user_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BroadcastFilterDTO":
        """ساخت از دیکشنری."""
        return cls(**data)


class BroadcastCreateDTO(BaseModel):
    """
    DTO برای ایجاد ارسال گروهی جدید.

    Attributes:
        title: عنوان ارسال گروهی (اجباری).
        content_type: نوع محتوا (اجباری).
        content: محتوای اصلی پیام (اجباری).
        filter: فیلترهای انتخاب کاربران هدف (اجباری).
        media_url: آدرس فایل رسانه (اختیاری).
        media_group: لیست آدرس‌های رسانه برای Media Group (اختیاری).
        caption: کپشن (برای رسانه‌ها، اختیاری).
        keyboard: کیبورد شیشه‌ای (JSON) (اختیاری).
        priority: اولویت ارسال (پیش‌فرض: normal).
        scheduled_at: زمان برنامه‌ریزی‌شده برای ارسال (اختیاری).
        is_draft: آیا در حالت پیش‌نویس است (پیش‌فرض: True).
        metadata: داده‌های اضافی (اختیاری).
    """
    title: str = Field(..., max_length=200, description="عنوان ارسال گروهی")
    content_type: str = Field(..., description="نوع محتوا")
    content: str = Field(..., description="محتوای اصلی پیام")
    filter: BroadcastFilterDTO = Field(..., description="فیلترهای انتخاب کاربران هدف")
    media_url: Optional[str] = Field(None, max_length=500, description="آدرس فایل رسانه")
    media_group: Optional[List[str]] = Field(None, description="لیست آدرس‌های رسانه برای Media Group")
    caption: Optional[str] = Field(None, max_length=1024, description="کپشن (برای رسانه‌ها)")
    keyboard: Optional[Dict[str, Any]] = Field(None, description="کیبورد شیشه‌ای (JSON)")
    priority: str = Field("normal", description="اولویت ارسال")
    scheduled_at: Optional[datetime] = Field(None, description="زمان برنامه‌ریزی‌شده برای ارسال")
    is_draft: bool = Field(True, description="آیا در حالت پیش‌نویس است")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """اعتبارسنجی نوع محتوا."""
        valid_types = [t.value for t in BroadcastType]
        if v not in valid_types:
            raise ValueError(f"نوع محتوا '{v}' نامعتبر است.")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """اعتبارسنجی اولویت."""
        valid_priorities = [p.value for p in BroadcastPriority]
        if v not in valid_priorities:
            raise ValueError(f"اولویت '{v}' نامعتبر است.")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """اعتبارسنجی محتوا."""
        if not v or not v.strip():
            raise ValueError("محتوای پیام نمی‌تواند خالی باشد.")
        if len(v) > 4096:
            raise ValueError("محتوای پیام نباید بیشتر از ۴۰۹۶ کاراکتر باشد.")
        return v

    @model_validator(mode="after")
    def validate_media(self) -> "BroadcastCreateDTO":
        """اعتبارسنجی رسانه‌ها."""
        content_type = self.content_type
        if content_type in ["photo", "video", "document", "audio", "animation", "sticker", "voice"]:
            if not self.media_url:
                raise ValueError(f"برای نوع محتوای '{content_type}' باید آدرس رسانه وارد شود.")
        if content_type == "media_group":
            if not self.media_group or len(self.media_group) < 2:
                raise ValueError("برای Media Group باید حداقل ۲ رسانه وارد شود.")
        return self

    @model_validator(mode="after")
    def validate_scheduled_at(self) -> "BroadcastCreateDTO":
        """اعتبارسنجی زمان ارسال."""
        if self.scheduled_at and self.scheduled_at <= datetime.now():
            raise ValueError("زمان ارسال باید در آینده باشد.")
        return self


class BroadcastUpdateDTO(BaseModel):
    """
    DTO برای به‌روزرسانی ارسال گروهی.

    Attributes:
        title: عنوان جدید (اختیاری).
        content_type: نوع محتوای جدید (اختیاری).
        content: محتوای جدید (اختیاری).
        filter: فیلترهای جدید (اختیاری).
        media_url: آدرس رسانه جدید (اختیاری).
        media_group: لیست رسانه جدید (اختیاری).
        caption: کپشن جدید (اختیاری).
        keyboard: کیبورد جدید (اختیاری).
        priority: اولویت جدید (اختیاری).
        scheduled_at: زمان ارسال جدید (اختیاری).
        is_draft: وضعیت پیش‌نویس جدید (اختیاری).
        metadata: داده‌های اضافی جدید (اختیاری).
    """
    title: Optional[str] = Field(None, max_length=200, description="عنوان جدید")
    content_type: Optional[str] = Field(None, description="نوع محتوای جدید")
    content: Optional[str] = Field(None, description="محتوای جدید")
    filter: Optional[BroadcastFilterDTO] = Field(None, description="فیلترهای جدید")
    media_url: Optional[str] = Field(None, max_length=500, description="آدرس رسانه جدید")
    media_group: Optional[List[str]] = Field(None, description="لیست رسانه جدید")
    caption: Optional[str] = Field(None, max_length=1024, description="کپشن جدید")
    keyboard: Optional[Dict[str, Any]] = Field(None, description="کیبورد جدید")
    priority: Optional[str] = Field(None, description="اولویت جدید")
    scheduled_at: Optional[datetime] = Field(None, description="زمان ارسال جدید")
    is_draft: Optional[bool] = Field(None, description="وضعیت پیش‌نویس جدید")
    metadata: Optional[Dict[str, Any]] = Field(None, description="داده‌های اضافی جدید")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی نوع محتوا."""
        if v is not None:
            valid_types = [t.value for t in BroadcastType]
            if v not in valid_types:
                raise ValueError(f"نوع محتوا '{v}' نامعتبر است.")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی اولویت."""
        if v is not None:
            valid_priorities = [p.value for p in BroadcastPriority]
            if v not in valid_priorities:
                raise ValueError(f"اولویت '{v}' نامعتبر است.")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی محتوا."""
        if v is not None:
            if not v.strip():
                raise ValueError("محتوای پیام نمی‌تواند خالی باشد.")
            if len(v) > 4096:
                raise ValueError("محتوای پیام نباید بیشتر از ۴۰۹۶ کاراکتر باشد.")
        return v


class BroadcastResponseDTO(BaseModel):
    """
    DTO برای پاسخ اطلاعات ارسال گروهی.

    Attributes:
        id: شناسه ارسال گروهی.
        title: عنوان ارسال گروهی.
        content_type: نوع محتوا.
        content: محتوای اصلی پیام.
        filter: فیلترهای انتخاب کاربران هدف.
        media_url: آدرس فایل رسانه (اختیاری).
        media_group: لیست آدرس‌های رسانه (اختیاری).
        caption: کپشن (اختیاری).
        keyboard: کیبورد شیشه‌ای (اختیاری).
        status: وضعیت ارسال.
        priority: اولویت ارسال.
        scheduled_at: زمان برنامه‌ریزی‌شده (اختیاری).
        created_by: شناسه کاربر ایجادکننده.
        total_count: تعداد کل کاربران هدف.
        sent_count: تعداد ارسال‌های موفق.
        failed_count: تعداد ارسال‌های ناموفق.
        failed_user_ids: لیست شناسه کاربرانی که ارسال برای آنها ناموفق بوده.
        sent_at: زمان اتمام ارسال (اختیاری).
        is_draft: آیا در حالت پیش‌نویس است.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    id: Optional[int] = Field(None, description="شناسه ارسال گروهی")
    title: str = Field(..., description="عنوان ارسال گروهی")
    content_type: str = Field(..., description="نوع محتوا")
    content: str = Field(..., description="محتوای اصلی پیام")
    filter: BroadcastFilterDTO = Field(..., description="فیلترهای انتخاب کاربران هدف")
    media_url: Optional[str] = Field(None, description="آدرس فایل رسانه")
    media_group: Optional[List[str]] = Field(None, description="لیست آدرس‌های رسانه")
    caption: Optional[str] = Field(None, description="کپشن")
    keyboard: Optional[Dict[str, Any]] = Field(None, description="کیبورد شیشه‌ای")
    status: str = Field("draft", description="وضعیت ارسال")
    priority: str = Field("normal", description="اولویت ارسال")
    scheduled_at: Optional[datetime] = Field(None, description="زمان برنامه‌ریزی‌شده")
    created_by: int = Field(..., description="شناسه کاربر ایجادکننده")
    total_count: int = Field(0, description="تعداد کل کاربران هدف")
    sent_count: int = Field(0, description="تعداد ارسال‌های موفق")
    failed_count: int = Field(0, description="تعداد ارسال‌های ناموفق")
    failed_user_ids: List[int] = Field(default_factory=list, description="لیست کاربرانی که ارسال ناموفق بوده")
    sent_at: Optional[datetime] = Field(None, description="زمان اتمام ارسال")
    is_draft: bool = Field(True, description="آیا در حالت پیش‌نویس است")
    created_at: datetime = Field(default_factory=datetime.now, description="زمان ایجاد")
    updated_at: datetime = Field(default_factory=datetime.now, description="زمان آخرین به‌روزرسانی")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, broadcast) -> "BroadcastResponseDTO":
        """
        ساخت DTO از موجودیت Broadcast.

        Args:
            broadcast: موجودیت Broadcast.

        Returns:
            BroadcastResponseDTO: DTO ساخته‌شده.
        """
        return cls(
            id=broadcast.id,
            title=broadcast.title,
            content_type=broadcast.content_type.value,
            content=broadcast.content,
            filter=BroadcastFilterDTO.from_dict(broadcast.filter.to_dict()),
            media_url=broadcast.media_url,
            media_group=broadcast.media_group,
            caption=broadcast.caption,
            keyboard=broadcast.keyboard,
            status=broadcast.status.value,
            priority=broadcast.priority.value,
            scheduled_at=broadcast.scheduled_at,
            created_by=broadcast.created_by,
            total_count=broadcast.total_count,
            sent_count=broadcast.sent_count,
            failed_count=broadcast.failed_count,
            failed_user_ids=broadcast.failed_user_ids,
            sent_at=broadcast.sent_at,
            is_draft=broadcast.is_draft,
            created_at=broadcast.created_at,
            updated_at=broadcast.updated_at,
            metadata=broadcast.metadata,
        )

    def get_progress(self) -> float:
        """دریافت درصد پیشرفت ارسال."""
        if self.total_count == 0:
            return 0.0
        return ((self.sent_count + self.failed_count) / self.total_count) * 100

    def is_completed(self) -> bool:
        """بررسی کامل شدن ارسال."""
        return self.status in ["sent", "partially_sent", "failed"]

    def get_summary(self) -> str:
        """
        دریافت خلاصه ارسال گروهی به‌صورت متن.

        Returns:
            str: خلاصه ارسال گروهی.
        """
        status_map = {
            "draft": "پیش‌نویس",
            "scheduled": "زمان‌بندی‌شده",
            "sending": "در حال ارسال",
            "sent": "ارسال‌شده",
            "partially_sent": "بخشی ارسال‌شده",
            "failed": "ناموفق",
            "cancelled": "لغو‌شده",
        }
        status_text = status_map.get(self.status, self.status)
        return f"ارسال گروهی '{self.title}' - وضعیت: {status_text} - پیشرفت: {self.get_progress():.1f}%"