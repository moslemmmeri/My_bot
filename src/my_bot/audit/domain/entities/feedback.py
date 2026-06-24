# my_bot_project/src/my_bot/domain/entities/feedback.py
"""
موجودیت بازخورد (Feedback Entity).

این کلاس نمایانگر یک بازخورد یا نظر ارسال‌شده توسط کاربران در مورد
محصولات، خدمات، پشتیبانی، یا عملکرد کلی سیستم است.
بازخوردها می‌توانند امتیاز، نظر، پیشنهاد یا انتقاد داشته باشند.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class FeedbackStatus(str, Enum):
    """وضعیت‌های مختلف بازخورد."""
    PENDING = "pending"          # در انتظار بررسی
    REVIEWED = "reviewed"        # بررسی‌شده
    RESOLVED = "resolved"        # حل‌شده (اقدام انجام شده)
    DISMISSED = "dismissed"      # نادیده گرفته شده


class FeedbackCategory(str, Enum):
    """دسته‌بندی بازخورد."""
    GENERAL = "general"          # عمومی
    PRODUCT = "product"          # درباره محصول
    SERVICE = "service"          # درباره خدمات
    SUPPORT = "support"          # درباره پشتیبانی
    UI_UX = "ui_ux"              # درباره رابط کاربری
    FEATURE_REQUEST = "feature_request"  # درخواست ویژگی جدید
    BUG_REPORT = "bug_report"    # گزارش خطا
    COMPLAINT = "complaint"      # شکایت
    PRAISE = "praise"            # تعریف و تمجید
    SUGGESTION = "suggestion"    # پیشنهاد


@dataclass
class Feedback:
    """
    موجودیت بازخورد کاربر.

    Attributes:
        id: شناسه یکتای بازخورد.
        user_id: شناسه کاربر ارسال‌کننده.
        category: دسته‌بندی بازخورد.
        content: متن بازخورد.
        rating: امتیاز (۰ تا ۵) (اختیاری).
        status: وضعیت بازخورد (پیش‌فرض PENDING).
        is_anonymous: آیا بازخورد ناشناس است.
        response: پاسخ ادمین یا تیم (اختیاری).
        responded_by: شناسه کاربری که پاسخ داده (اختیاری).
        responded_at: زمان پاسخ (اختیاری).
        related_entity_type: نوع موجودیت مرتبط (مثلاً 'order', 'product') (اختیاری).
        related_entity_id: شناسه موجودیت مرتبط (اختیاری).
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    user_id: int
    category: FeedbackCategory
    content: str
    rating: Optional[float] = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    is_anonymous: bool = False
    response: Optional[str] = None
    responded_by: Optional[int] = None
    responded_at: Optional[datetime] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_content()
        self._validate_rating()
        self._validate_entity()

    def _validate_content(self) -> None:
        """اعتبارسنجی محتوای بازخورد."""
        if not self.content or not self.content.strip():
            raise ValidationError(
                message="محتوای بازخورد نمی‌تواند خالی باشد.",
                context={"user_id": self.user_id, "category": self.category.value},
            )
        if len(self.content) > 5000:
            raise ValidationError(
                message="متن بازخورد نباید بیشتر از ۵۰۰۰ کاراکتر باشد.",
                context={"user_id": self.user_id, "length": len(self.content)},
            )

    def _validate_rating(self) -> None:
        """اعتبارسنجی امتیاز (در صورت وجود)."""
        if self.rating is not None:
            if not (0 <= self.rating <= 5):
                raise ValidationError(
                    message="امتیاز باید بین ۰ تا ۵ باشد.",
                    context={"user_id": self.user_id, "rating": self.rating},
                )

    def _validate_entity(self) -> None:
        """اعتبارسنجی موجودیت مرتبط (در صورت وجود)."""
        if self.related_entity_type and not self.related_entity_id:
            raise ValidationError(
                message="در صورت تعیین نوع موجودیت مرتبط، شناسه آن نیز باید وارد شود.",
                context={"user_id": self.user_id, "entity_type": self.related_entity_type},
            )

    def review(self, reviewer_id: int) -> None:
        """
        علامت‌گذاری بازخورد به‌عنوان بررسی‌شده.

        Args:
            reviewer_id: شناسه کاربر بررسی‌کننده.
        """
        if self.status == FeedbackStatus.DISMISSED:
            raise ValidationError(
                message="بازخورد نادیده گرفته شده قابل بررسی مجدد نیست.",
                context={"feedback_id": self.id, "status": self.status.value},
            )
        self.status = FeedbackStatus.REVIEWED
        self.updated_at = datetime.now()
        self.metadata["reviewed_by"] = reviewer_id
        logger.info(f"Feedback {self.id} reviewed by user {reviewer_id}")

    def respond(self, response_text: str, responder_id: int) -> None:
        """
        افزودن پاسخ به بازخورد.

        Args:
            response_text: متن پاسخ.
            responder_id: شناسه کاربر پاسخ‌دهنده.
        """
        if not response_text or not response_text.strip():
            raise ValidationError(
                message="متن پاسخ نمی‌تواند خالی باشد.",
                context={"feedback_id": self.id},
            )
        self.response = response_text
        self.responded_by = responder_id
        self.responded_at = datetime.now()
        self.updated_at = datetime.now()
        if self.status == FeedbackStatus.PENDING:
            self.status = FeedbackStatus.REVIEWED
        logger.info(f"Feedback {self.id} responded by user {responder_id}")

    def resolve(self) -> None:
        """علامت‌گذاری بازخورد به‌عنوان حل‌شده."""
        if self.status in (FeedbackStatus.DISMISSED, FeedbackStatus.RESOLVED):
            raise ValidationError(
                message=f"بازخورد در وضعیت '{self.status.value}' قابل حل نیست.",
                context={"feedback_id": self.id, "status": self.status.value},
            )
        self.status = FeedbackStatus.RESOLVED
        self.updated_at = datetime.now()
        logger.info(f"Feedback {self.id} marked as resolved")

    def dismiss(self, reason: Optional[str] = None) -> None:
        """
        نادیده گرفتن بازخورد.

        Args:
            reason: دلیل نادیده گرفتن (اختیاری).
        """
        if self.status == FeedbackStatus.RESOLVED:
            raise ValidationError(
                message="بازخورد حل‌شده قابل نادیده گرفتن نیست.",
                context={"feedback_id": self.id, "status": self.status.value},
            )
        self.status = FeedbackStatus.DISMISSED
        self.updated_at = datetime.now()
        if reason:
            self.metadata["dismiss_reason"] = reason
        logger.info(f"Feedback {self.id} dismissed. Reason: {reason}")

    def is_pending(self) -> bool:
        """بررسی در انتظار بودن بازخورد."""
        return self.status == FeedbackStatus.PENDING

    def is_reviewed(self) -> bool:
        """بررسی بررسی‌شده بودن بازخورد."""
        return self.status == FeedbackStatus.REVIEWED

    def is_resolved(self) -> bool:
        """بررسی حل‌شده بودن بازخورد."""
        return self.status == FeedbackStatus.RESOLVED

    def has_response(self) -> bool:
        """بررسی وجود پاسخ برای بازخورد."""
        return self.response is not None

    def get_rating_display(self) -> str:
        """
        دریافت نمایش متنی امتیاز (ستاره‌ها).

        Returns:
            رشته‌ای شامل ستاره‌های توپر و توخالی.
        """
        if self.rating is None:
            return "بدون امتیاز"
        full_stars = int(self.rating)
        half_star = self.rating - full_stars >= 0.5
        stars = "⭐" * full_stars
        if half_star:
            stars += "✨"
        return stars or "⭐"

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل موجودیت بازخورد به دیکشنری."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category.value,
            "content": self.content,
            "rating": self.rating,
            "status": self.status.value,
            "is_anonymous": self.is_anonymous,
            "response": self.response,
            "responded_by": self.responded_by,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feedback":
        """ساخت موجودیت بازخورد از دیکشنری."""
        category = FeedbackCategory(data.get("category", "general"))
        status = FeedbackStatus(data.get("status", "pending"))

        responded_at = None
        if data.get("responded_at"):
            try:
                responded_at = datetime.fromisoformat(data["responded_at"])
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
            user_id=data["user_id"],
            category=category,
            content=data["content"],
            rating=data.get("rating"),
            status=status,
            is_anonymous=data.get("is_anonymous", False),
            response=data.get("response"),
            responded_by=data.get("responded_by"),
            responded_at=responded_at,
            related_entity_type=data.get("related_entity_type"),
            related_entity_id=data.get("related_entity_id"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        return f"Feedback(id={self.id}, user={self.user_id}, category={self.category.value}, rating={self.rating})"