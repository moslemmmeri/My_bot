# my_bot_project/src/my_bot/domain/entities/broadcast.py
"""
موجودیت ارسال گروهی پیام (Broadcast Entity).

این کلاس نمایانگر یک پیام گروهی است که توسط ادمین برای گروهی از کاربران
ارسال می‌شود. شامل محتوای پیام، فیلترهای هدف، زمان‌بندی ارسال،
وضعیت، آمار و تاریخچه‌ی ارسال است.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Union

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class BroadcastStatus(str, Enum):
    """وضعیت‌های مختلف ارسال گروهی."""
    DRAFT = "draft"                 # پیش‌نویس
    SCHEDULED = "scheduled"         # زمان‌بندی‌شده
    SENDING = "sending"             # در حال ارسال
    SENT = "sent"                   # ارسال شده
    PARTIALLY_SENT = "partially_sent"  # بخشی ارسال شده
    FAILED = "failed"               # ناموفق
    CANCELLED = "cancelled"         # لغو شده


class BroadcastPriority(str, Enum):
    """اولویت ارسال گروهی."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BroadcastType(str, Enum):
    """نوع محتوای پیام گروهی."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    ANIMATION = "animation"
    STICKER = "sticker"
    VOICE = "voice"
    MEDIA_GROUP = "media_group"  # گروهی از رسانه‌ها


@dataclass
class BroadcastFilter:
    """
    فیلترهای انتخاب کاربران هدف برای ارسال گروهی.

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
        tags: لیست برچسب‌ها (اختیاری).
        exclude_user_ids: لیست شناسه‌های کاربران برای حذف (اختیاری).
    """
    user_ids: Optional[List[int]] = None
    roles: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    min_points: Optional[int] = None
    max_points: Optional[int] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_activity_after: Optional[datetime] = None
    tags: Optional[List[str]] = None
    exclude_user_ids: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل فیلترها به دیکشنری."""
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
            "tags": self.tags,
            "exclude_user_ids": self.exclude_user_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BroadcastFilter":
        """ساخت فیلترها از دیکشنری."""
        created_after = None
        if data.get("created_after"):
            try:
                created_after = datetime.fromisoformat(data["created_after"])
            except (ValueError, TypeError):
                pass

        created_before = None
        if data.get("created_before"):
            try:
                created_before = datetime.fromisoformat(data["created_before"])
            except (ValueError, TypeError):
                pass

        last_activity_after = None
        if data.get("last_activity_after"):
            try:
                last_activity_after = datetime.fromisoformat(data["last_activity_after"])
            except (ValueError, TypeError):
                pass

        return cls(
            user_ids=data.get("user_ids"),
            roles=data.get("roles"),
            levels=data.get("levels"),
            min_points=data.get("min_points"),
            max_points=data.get("max_points"),
            is_active=data.get("is_active"),
            is_banned=data.get("is_banned"),
            created_after=created_after,
            created_before=created_before,
            last_activity_after=last_activity_after,
            tags=data.get("tags"),
            exclude_user_ids=data.get("exclude_user_ids"),
            metadata=data.get("metadata", {}),
        )

    def has_filters(self) -> bool:
        """بررسی اینکه آیا حداقل یک فیلتر تعریف شده است."""
        return any([
            self.user_ids is not None,
            self.roles is not None,
            self.levels is not None,
            self.min_points is not None,
            self.max_points is not None,
            self.is_active is not None,
            self.is_banned is not None,
            self.created_after is not None,
            self.created_before is not None,
            self.last_activity_after is not None,
            self.tags is not None,
            self.exclude_user_ids is not None,
        ])


@dataclass
class Broadcast:
    """
    موجودیت ارسال گروهی پیام.

    Attributes:
        id: شناسه یکتای ارسال گروهی.
        title: عنوان (برای استفاده داخلی).
        content_type: نوع محتوا.
        content: محتوای اصلی (متن، کپشن، و ...).
        media_url: آدرس فایل رسانه (اختیاری).
        media_group: لیست آدرس‌های رسانه برای Media Group (اختیاری).
        caption: کپشن (برای رسانه‌ها، اختیاری).
        keyboard: کیبورد شیشه‌ای (JSON) (اختیاری).
        filter: فیلترهای انتخاب کاربران هدف.
        status: وضعیت ارسال.
        priority: اولویت ارسال (پیش‌فرض NORMAL).
        scheduled_at: زمان برنامه‌ریزی‌شده برای ارسال (اختیاری).
        created_by: شناسه کاربر ایجادکننده (ادمین).
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
    title: str
    content_type: BroadcastType
    content: str
    created_by: int
    filter: BroadcastFilter
    media_url: Optional[str] = None
    media_group: Optional[List[str]] = None
    caption: Optional[str] = None
    keyboard: Optional[Dict[str, Any]] = None
    status: BroadcastStatus = BroadcastStatus.DRAFT
    priority: BroadcastPriority = BroadcastPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    total_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    failed_user_ids: List[int] = field(default_factory=list)
    sent_at: Optional[datetime] = None
    is_draft: bool = True
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه."""
        self._validate_title()
        self._validate_content()
        self._validate_scheduled_date()
        self._validate_media()

    def _validate_title(self) -> None:
        if not self.title or not self.title.strip():
            raise ValidationError(
                message="عنوان ارسال گروهی نمی‌تواند خالی باشد.",
                context={"broadcast_id": self.id},
            )

    def _validate_content(self) -> None:
        if not self.content or not self.content.strip():
            raise ValidationError(
                message="محتوای پیام نمی‌تواند خالی باشد.",
                context={"broadcast_id": self.id},
            )

    def _validate_scheduled_date(self) -> None:
        """اعتبارسنجی تاریخ زمان‌بندی‌شده."""
        if self.scheduled_at and self.scheduled_at <= datetime.now():
            raise ValidationError(
                message="زمان ارسال باید در آینده باشد.",
                context={"broadcast_id": self.id, "scheduled_at": self.scheduled_at},
            )

    def _validate_media(self) -> None:
        """اعتبارسنجی رسانه‌ها."""
        if self.content_type in (BroadcastType.PHOTO, BroadcastType.VIDEO, 
                                 BroadcastType.DOCUMENT, BroadcastType.AUDIO,
                                 BroadcastType.ANIMATION, BroadcastType.STICKER,
                                 BroadcastType.VOICE):
            if not self.media_url:
                raise ValidationError(
                    message=f"برای نوع محتوای '{self.content_type.value}' باید آدرس رسانه وارد شود.",
                    context={"broadcast_id": self.id, "content_type": self.content_type.value},
                )

        if self.content_type == BroadcastType.MEDIA_GROUP:
            if not self.media_group or len(self.media_group) < 2:
                raise ValidationError(
                    message="برای Media Group باید حداقل ۲ رسانه وارد شود.",
                    context={"broadcast_id": self.id, "media_group_count": len(self.media_group) if self.media_group else 0},
                )

    def schedule(self, scheduled_at: datetime) -> None:
        """
        زمان‌بندی ارسال گروهی.

        Args:
            scheduled_at: زمان ارسال.
        """
        if self.status not in (BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED):
            raise ValidationError(
                message="فقط ارسال‌های گروهی در وضعیت DRAFT یا SCHEDULED قابل زمان‌بندی هستند.",
                context={"broadcast_id": self.id, "current_status": self.status.value},
            )

        if scheduled_at <= datetime.now():
            raise ValidationError(
                message="زمان ارسال باید در آینده باشد.",
                context={"broadcast_id": self.id, "scheduled_at": scheduled_at},
            )

        self.scheduled_at = scheduled_at
        self.status = BroadcastStatus.SCHEDULED
        self.is_draft = False
        self.updated_at = datetime.now()
        logger.info(f"Broadcast {self.id} scheduled at {scheduled_at}")

    def start_sending(self) -> None:
        """شروع ارسال گروهی (تغییر وضعیت به SENDING)."""
        if self.status not in (BroadcastStatus.SCHEDULED, BroadcastStatus.DRAFT):
            raise ValidationError(
                message="فقط ارسال‌های گروهی در وضعیت SCHEDULED یا DRAFT قابل شروع هستند.",
                context={"broadcast_id": self.id, "current_status": self.status.value},
            )

        if self.status == BroadcastStatus.DRAFT:
            # اگر پیش‌نویس بود، مستقیماً ارسال می‌شود
            self.is_draft = False

        self.status = BroadcastStatus.SENDING
        self.updated_at = datetime.now()
        logger.info(f"Broadcast {self.id} started sending.")

    def mark_as_sent(self, total_count: int, sent_count: int, failed_count: int, failed_user_ids: List[int]) -> None:
        """
        ثبت اتمام ارسال گروهی.

        Args:
            total_count: تعداد کل کاربران هدف.
            sent_count: تعداد ارسال‌های موفق.
            failed_count: تعداد ارسال‌های ناموفق.
            failed_user_ids: لیست شناسه کاربرانی که ارسال برای آنها ناموفق بوده.
        """
        if self.status != BroadcastStatus.SENDING:
            raise ValidationError(
                message="فقط ارسال‌های گروهی در وضعیت SENDING قابل پایان هستند.",
                context={"broadcast_id": self.id, "current_status": self.status.value},
            )

        self.total_count = total_count
        self.sent_count = sent_count
        self.failed_count = failed_count
        self.failed_user_ids = failed_user_ids
        self.sent_at = datetime.now()

        if failed_count == 0:
            self.status = BroadcastStatus.SENT
        elif sent_count > 0 and failed_count > 0:
            self.status = BroadcastStatus.PARTIALLY_SENT
        else:
            self.status = BroadcastStatus.FAILED

        self.updated_at = datetime.now()
        logger.info(f"Broadcast {self.id} finished. Sent: {sent_count}, Failed: {failed_count}")

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        لغو ارسال گروهی.

        Args:
            reason: دلیل لغو (اختیاری).
        """
        if self.status in (BroadcastStatus.SENT, BroadcastStatus.PARTIALLY_SENT, BroadcastStatus.FAILED):
            raise ValidationError(
                message="ارسال‌های گروهی که به پایان رسیده‌اند قابل لغو نیستند.",
                context={"broadcast_id": self.id, "current_status": self.status.value},
            )

        self.status = BroadcastStatus.CANCELLED
        self.updated_at = datetime.now()
        if reason:
            self.metadata["cancel_reason"] = reason
        logger.info(f"Broadcast {self.id} cancelled. Reason: {reason}")

    def can_send(self) -> bool:
        """بررسی اینکه آیا ارسال گروهی قابل اجرا است."""
        if self.status in (BroadcastStatus.SENDING, BroadcastStatus.SENT,
                           BroadcastStatus.PARTIALLY_SENT, BroadcastStatus.FAILED,
                           BroadcastStatus.CANCELLED):
            return False

        if self.scheduled_at and datetime.now() < self.scheduled_at:
            return False

        return True

    def can_cancel(self) -> bool:
        """بررسی اینکه آیا ارسال گروهی قابل لغو است."""
        return self.status not in (BroadcastStatus.SENT, BroadcastStatus.PARTIALLY_SENT,
                                    BroadcastStatus.FAILED, BroadcastStatus.CANCELLED)

    def progress_percentage(self) -> float:
        """
        دریافت درصد پیشرفت ارسال.

        Returns:
            درصد پیشرفت (۰ تا ۱۰۰).
        """
        if self.total_count == 0:
            return 0.0
        return (self.sent_count + self.failed_count) / self.total_count * 100

    def is_completed(self) -> bool:
        """بررسی اینکه آیا ارسال گروهی کامل شده است."""
        return self.status in (BroadcastStatus.SENT, BroadcastStatus.PARTIALLY_SENT, BroadcastStatus.FAILED)

    def is_pending(self) -> bool:
        """بررسی اینکه آیا ارسال گروهی در حال انتظار است."""
        return self.status in (BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED)

    def get_summary(self) -> Dict[str, Any]:
        """
        دریافت خلاصه‌ای از آمار ارسال.

        Returns:
            دیکشنری شامل آمار ارسال.
        """
        return {
            "total": self.total_count,
            "sent": self.sent_count,
            "failed": self.failed_count,
            "pending": self.total_count - self.sent_count - self.failed_count,
            "progress": self.progress_percentage(),
            "status": self.status.value,
        }

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل موجودیت ارسال گروهی به دیکشنری."""
        return {
            "id": self.id,
            "title": self.title,
            "content_type": self.content_type.value,
            "content": self.content,
            "media_url": self.media_url,
            "media_group": self.media_group,
            "caption": self.caption,
            "keyboard": self.keyboard,
            "filter": self.filter.to_dict(),
            "status": self.status.value,
            "priority": self.priority.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "created_by": self.created_by,
            "total_count": self.total_count,
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "failed_user_ids": self.failed_user_ids,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "is_draft": self.is_draft,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Broadcast":
        """ساخت موجودیت ارسال گروهی از دیکشنری."""
        content_type = BroadcastType(data.get("content_type", "text"))
        status = BroadcastStatus(data.get("status", "draft"))
        priority = BroadcastPriority(data.get("priority", "normal"))

        filter_data = data.get("filter", {})
        broadcast_filter = BroadcastFilter.from_dict(filter_data)

        scheduled_at = None
        if data.get("scheduled_at"):
            try:
                scheduled_at = datetime.fromisoformat(data["scheduled_at"])
            except (ValueError, TypeError):
                pass

        sent_at = None
        if data.get("sent_at"):
            try:
                sent_at = datetime.fromisoformat(data["sent_at"])
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

        return cls(
            id=data.get("id"),
            title=data["title"],
            content_type=content_type,
            content=data["content"],
            created_by=data["created_by"],
            filter=broadcast_filter,
            media_url=data.get("media_url"),
            media_group=data.get("media_group"),
            caption=data.get("caption"),
            keyboard=data.get("keyboard"),
            status=status,
            priority=priority,
            scheduled_at=scheduled_at,
            total_count=data.get("total_count", 0),
            sent_count=data.get("sent_count", 0),
            failed_count=data.get("failed_count", 0),
            failed_user_ids=data.get("failed_user_ids", []),
            sent_at=sent_at,
            is_draft=data.get("is_draft", True),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        return f"Broadcast(id={self.id}, title={self.title}, status={self.status.value})"