# my_bot_project/src/my_bot/domain/entities/ticket.py
"""
موجودیت تیکت پشتیبانی (Ticket Entity).

این کلاس نمایانگر یک درخواست پشتیبانی یا تیکت است که توسط کاربران
برای گزارش مشکل، سوال یا درخواست کمک ثبت می‌شود.
تیکت‌ها دارای وضعیت، اولویت، دسته‌بندی و تاریخچه‌ی پیگیری هستند.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class TicketStatus(str, Enum):
    """وضعیت‌های مختلف تیکت."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """اولویت تیکت."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, Enum):
    """دسته‌بندی تیکت."""
    GENERAL = "general"
    TECHNICAL = "technical"
    BILLING = "billing"
    ORDER = "order"
    FEEDBACK = "feedback"
    OTHER = "other"


@dataclass
class TicketMessage:
    """
    پیام درون تیکت (تاریخچه مکالمات).

    Attributes:
        id: شناسه پیام (اختیاری).
        ticket_id: شناسه تیکت.
        user_id: شناسه کاربر فرستنده.
        message: متن پیام.
        is_internal: پیام داخلی (فقط برای ادمین‌ها قابل مشاهده است).
        created_at: زمان ارسال.
    """
    user_id: int
    message: str
    is_internal: bool = False
    id: Optional[int] = None
    ticket_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "message": self.message,
            "is_internal": self.is_internal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TicketMessage":
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()
        return cls(
            id=data.get("id"),
            ticket_id=data.get("ticket_id"),
            user_id=data["user_id"],
            message=data["message"],
            is_internal=data.get("is_internal", False),
            created_at=created_at or datetime.now(),
        )


@dataclass
class Ticket:
    """
    موجودیت تیکت پشتیبانی.

    Attributes:
        id: شناسه یکتای تیکت.
        user_id: شناسه کاربر ایجادکننده.
        subject: عنوان تیکت.
        description: شرح اولیه مشکل.
        status: وضعیت تیکت (پیش‌فرض OPEN).
        priority: اولویت (پیش‌فرض MEDIUM).
        category: دسته‌بندی (پیش‌فرض GENERAL).
        assigned_to: شناسه ادمین یا اپراتور مسئول (اختیاری).
        messages: لیست پیام‌های تیکت.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        resolved_at: زمان حل شدن (اختیاری).
        closed_at: زمان بسته شدن (اختیاری).
        metadata: داده‌های اضافی.
    """
    user_id: int
    subject: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory = TicketCategory.GENERAL
    assigned_to: Optional[int] = None
    messages: List[TicketMessage] = field(default_factory=list)
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه."""
        self._validate_subject()
        self._validate_description()

    def _validate_subject(self) -> None:
        if not self.subject or not self.subject.strip():
            raise ValidationError(
                message="عنوان تیکت نمی‌تواند خالی باشد.",
                context={"ticket_id": self.id, "user_id": self.user_id},
            )

    def _validate_description(self) -> None:
        if not self.description or not self.description.strip():
            raise ValidationError(
                message="شرح تیکت نمی‌تواند خالی باشد.",
                context={"ticket_id": self.id, "user_id": self.user_id},
            )

    def add_message(self, user_id: int, message: str, is_internal: bool = False) -> None:
        """
        افزودن پیام جدید به تیکت.

        Args:
            user_id: شناسه کاربر فرستنده.
            message: متن پیام.
            is_internal: پیام داخلی (فقط برای ادمین‌ها).
        """
        if not message or not message.strip():
            raise ValidationError(
                message="متن پیام نمی‌تواند خالی باشد.",
                context={"ticket_id": self.id, "user_id": user_id},
            )
        msg = TicketMessage(
            ticket_id=self.id,
            user_id=user_id,
            message=message,
            is_internal=is_internal,
        )
        self.messages.append(msg)
        self.updated_at = datetime.now()
        logger.debug(f"Message added to ticket {self.id} by user {user_id}")

    def assign_to(self, admin_id: int) -> None:
        """
        اختصاص تیکت به یک ادمین یا اپراتور.

        Args:
            admin_id: شناسه کاربر مسئول.
        """
        self.assigned_to = admin_id
        self.updated_at = datetime.now()
        logger.info(f"Ticket {self.id} assigned to user {admin_id}")

    def change_status(self, new_status: TicketStatus, reason: Optional[str] = None) -> None:
        """
        تغییر وضعیت تیکت.

        Args:
            new_status: وضعیت جدید.
            reason: دلیل تغییر (اختیاری).
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == TicketStatus.RESOLVED:
            self.resolved_at = datetime.now()
        if new_status == TicketStatus.CLOSED:
            self.closed_at = datetime.now()

        if reason:
            self.metadata["status_change_reason"] = reason
        self.metadata[f"status_change_from_{old_status.value}"] = new_status.value

        logger.info(f"Ticket {self.id} status changed from {old_status.value} to {new_status.value}")

    def resolve(self, reason: Optional[str] = None) -> None:
        """حل کردن تیکت (تغییر وضعیت به RESOLVED)."""
        self.change_status(TicketStatus.RESOLVED, reason)

    def close(self, reason: Optional[str] = None) -> None:
        """بستن تیکت (تغییر وضعیت به CLOSED)."""
        self.change_status(TicketStatus.CLOSED, reason)

    def reopen(self) -> None:
        """بازگشایی تیکت (تغییر وضعیت به OPEN)."""
        if self.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            self.status = TicketStatus.OPEN
            self.resolved_at = None
            self.closed_at = None
            self.updated_at = datetime.now()
            logger.info(f"Ticket {self.id} reopened.")
        else:
            raise ValidationError(
                message="فقط تیکت‌های حل‌شده یا بسته‌شده قابل بازگشایی هستند.",
                context={"ticket_id": self.id, "current_status": self.status.value},
            )

    def is_active(self) -> bool:
        """بررسی فعال بودن تیکت (وضعیت OPEN یا IN_PROGRESS)."""
        return self.status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS)

    def is_closed(self) -> bool:
        """بررسی بسته بودن تیکت."""
        return self.status == TicketStatus.CLOSED

    def is_resolved(self) -> bool:
        """بررسی حل شدن تیکت."""
        return self.status == TicketStatus.RESOLVED

    def get_last_message(self) -> Optional[TicketMessage]:
        """دریافت آخرین پیام تیکت."""
        if self.messages:
            return self.messages[-1]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "category": self.category.value,
            "assigned_to": self.assigned_to,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        status = TicketStatus(data.get("status", "open"))
        priority = TicketPriority(data.get("priority", "medium"))
        category = TicketCategory(data.get("category", "general"))

        messages = []
        for msg_data in data.get("messages", []):
            messages.append(TicketMessage.from_dict(msg_data))

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

        resolved_at = None
        if data.get("resolved_at"):
            try:
                resolved_at = datetime.fromisoformat(data["resolved_at"])
            except (ValueError, TypeError):
                pass

        closed_at = None
        if data.get("closed_at"):
            try:
                closed_at = datetime.fromisoformat(data["closed_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            subject=data["subject"],
            description=data["description"],
            status=status,
            priority=priority,
            category=category,
            assigned_to=data.get("assigned_to"),
            messages=messages,
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            resolved_at=resolved_at,
            closed_at=closed_at,
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        return f"Ticket(id={self.id}, subject={self.subject}, status={self.status.value})"