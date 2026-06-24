# my_bot_project/src/my_bot/domain/entities/audit_log.py
"""
موجودیت لاگ حسابرسی (Audit Log Entity).

این کلاس نمایانگر یک رویداد ثبت‌شده در سیستم است که برای پیگیری
فعالیت‌های کاربران، تغییرات داده‌ها، رویدادهای امنیتی و سایر عملیات‌های
حساس استفاده می‌شود. لاگ‌های حسابرسی امکان بررسی و تحلیل رویدادهای
سیستم را فراهم می‌کنند.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class AuditAction(str, Enum):
    """نوع عملیات انجام‌شده."""
    CREATE = "create"          # ایجاد
    READ = "read"              # مشاهده
    UPDATE = "update"          # به‌روزرسانی
    DELETE = "delete"          # حذف
    LOGIN = "login"            # ورود
    LOGOUT = "logout"          # خروج
    REGISTER = "register"      # ثبت‌نام
    PAYMENT = "payment"        # پرداخت
    REFUND = "refund"          # بازگشت وجه
    APPROVE = "approve"        # تأیید
    REJECT = "reject"          # رد
    EXPORT = "export"          # خروجی گرفتن
    IMPORT = "import"          # واردات
    BROADCAST = "broadcast"    # ارسال گروهی
    SETTINGS = "settings"      # تغییر تنظیمات
    PERMISSION = "permission"  # تغییر دسترسی
    FEATURE = "feature"        # تغییر فیچر فلاگ
    BACKUP = "backup"          # پشتیبان‌گیری
    RESTORE = "restore"        # بازگردانی
    OTHER = "other"            # سایر


class AuditStatus(str, Enum):
    """وضعیت عملیات."""
    SUCCESS = "success"        # موفق
    FAILED = "failed"          # ناموفق
    PARTIAL = "partial"        # تا حدی موفق
    PENDING = "pending"        # در انتظار
    CANCELLED = "cancelled"    # لغو‌شده


@dataclass
class AuditLog:
    """
    موجودیت لاگ حسابرسی.

    Attributes:
        id: شناسه یکتای لاگ.
        user_id: شناسه کاربر انجام‌دهنده (اختیاری).
        username: نام کاربری (اختیاری، برای مواردی که کاربر لاگین نبوده).
        action: نوع عملیات.
        entity_type: نوع موجودیت (مثلاً 'user', 'order', 'payment').
        entity_id: شناسه موجودیت (اختیاری).
        status: وضعیت عملیات.
        message: پیام توضیحی (اختیاری).
        changes: تغییرات اعمال‌شده (به‌صورت JSON).
        ip_address: آدرس IP کاربر (اختیاری).
        user_agent: مرورگر یا کلاینت کاربر (اختیاری).
        session_id: شناسه جلسه (اختیاری).
        request_id: شناسه درخواست (برای ردیابی).
        duration_ms: مدت زمان اجرا بر حسب میلی‌ثانیه (اختیاری).
        created_at: زمان ثبت رویداد.
        metadata: داده‌های اضافی.
    """
    action: AuditAction
    entity_type: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    entity_id: Optional[str] = None
    status: AuditStatus = AuditStatus.SUCCESS
    message: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه."""
        self._validate_action()
        self._validate_entity_type()
        self._validate_user()

    def _validate_action(self) -> None:
        """اعتبارسنجی نوع عملیات."""
        if not self.action:
            raise ValidationError(
                message="نوع عملیات نمی‌تواند خالی باشد.",
                context={"audit_id": self.id},
            )

    def _validate_entity_type(self) -> None:
        """اعتبارسنجی نوع موجودیت."""
        if not self.entity_type or not self.entity_type.strip():
            raise ValidationError(
                message="نوع موجودیت نمی‌تواند خالی باشد.",
                context={"audit_id": self.id},
            )

    def _validate_user(self) -> None:
        """اعتبارسنجی اطلاعات کاربر."""
        if self.user_id is None and self.username is None:
            raise ValidationError(
                message="حداقل یکی از user_id یا username باید مشخص شود.",
                context={"audit_id": self.id},
            )

    def is_success(self) -> bool:
        """بررسی موفق بودن عملیات."""
        return self.status == AuditStatus.SUCCESS

    def is_failed(self) -> bool:
        """بررسی ناموفق بودن عملیات."""
        return self.status == AuditStatus.FAILED

    def get_summary(self) -> str:
        """
        دریافت خلاصه‌ای از رویداد به‌صورت متن.

        Returns:
            رشته خلاصه.
        """
        user = self.username or f"user_{self.user_id}"
        entity = f"{self.entity_type}"
        if self.entity_id:
            entity += f"_{self.entity_id}"
        return f"{user} {self.action.value} {entity} {self.status.value}"

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل موجودیت لاگ حسابرسی به دیکشنری."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status.value,
            "message": self.message,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLog":
        """ساخت موجودیت لاگ حسابرسی از دیکشنری."""
        action = AuditAction(data.get("action", "other"))
        status = AuditStatus(data.get("status", "success"))

        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()

        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            username=data.get("username"),
            action=action,
            entity_type=data["entity_type"],
            entity_id=data.get("entity_id"),
            status=status,
            message=data.get("message"),
            changes=data.get("changes"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            duration_ms=data.get("duration_ms"),
            created_at=created_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        return f"AuditLog(id={self.id}, user={self.user_id or self.username}, action={self.action.value}, status={self.status.value})"