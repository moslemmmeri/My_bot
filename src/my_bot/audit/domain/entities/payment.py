# my_bot_project/src/my_bot/domain/entities/payment.py
"""
موجودیت تراکنش پرداخت (Payment Entity).

این کلاس نمایانگر یک تراکنش پرداخت در سیستم است که برای سفارشات یا
خدمات ثبت می‌شود. شامل اطلاعات مبلغ، وضعیت، درگاه، کد رهگیری،
و سایر جزئیات مرتبط با پرداخت است.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


@dataclass
class Payment:
    """
    موجودیت تراکنش پرداخت در سیستم.

    Attributes:
        id: شناسه یکتای تراکنش در دیتابیس.
        order_id: شناسه سفارش مرتبط (اختیاری).
        user_id: شناسه کاربر پرداخت‌کننده.
        amount: مبلغ پرداختی (به‌عنوان Money).
        currency: واحد پول (پیش‌فرض: IRR).
        status: وضعیت پرداخت (پیش‌فرض: PENDING).
        gateway: نام درگاه پرداخت (مثلاً 'zarinpal', 'mock').
        transaction_id: شناسه تراکنش در درگاه (اختیاری).
        tracking_code: کد رهگیری پرداخت (اختیاری).
        reference_id: شناسه مرجع در سیستم درگاه (اختیاری).
        callback_url: آدرس بازگشت پس از پرداخت (اختیاری).
        callback_data: داده‌های دریافتی از درگاه (اختیاری).
        paid_at: زمان پرداخت موفق (اختیاری).
        expired_at: زمان انقضای پرداخت (اختیاری).
        retry_count: تعداد تلاش‌های مجدد (پیش‌فرض: ۰).
        description: توضیحات پرداخت (اختیاری).
        error_message: پیام خطا (در صورت وجود).
        created_at: زمان ایجاد تراکنش.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """

    user_id: int
    amount: Money
    order_id: Optional[str] = None
    currency: str = "IRR"
    status: PaymentStatus = PaymentStatus.PENDING
    gateway: str = "mock"
    transaction_id: Optional[str] = None
    tracking_code: Optional[str] = None
    reference_id: Optional[str] = None
    callback_url: Optional[str] = None
    callback_data: Optional[Dict[str, Any]] = None
    paid_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    retry_count: int = 0
    description: Optional[str] = None
    error_message: Optional[str] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_amount()
        self._validate_gateway()
        self._validate_currency()

    def _validate_amount(self) -> None:
        """اعتبارسنجی مبلغ پرداخت (باید مثبت باشد)."""
        if self.amount.amount <= 0:
            raise ValidationError(
                message="مبلغ پرداخت باید مثبت باشد.",
                context={"user_id": self.user_id, "amount": self.amount.amount},
            )

    def _validate_gateway(self) -> None:
        """اعتبارسنجی نام درگاه پرداخت."""
        if not self.gateway or not self.gateway.strip():
            raise ValidationError(
                message="نام درگاه پرداخت نمی‌تواند خالی باشد.",
                context={"user_id": self.user_id},
            )

    def _validate_currency(self) -> None:
        """اعتبارسنجی واحد پول."""
        allowed_currencies = ("IRR", "IRT", "USD", "EUR")
        if self.currency not in allowed_currencies:
            raise ValidationError(
                message=f"واحد پول '{self.currency}' مجاز نیست. واحدهای مجاز: {', '.join(allowed_currencies)}",
                context={"user_id": self.user_id, "currency": self.currency},
            )

    def mark_as_success(
        self,
        transaction_id: str,
        reference_id: Optional[str] = None,
        tracking_code: Optional[str] = None,
        callback_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان موفق.

        Args:
            transaction_id: شناسه تراکنش در درگاه.
            reference_id: شناسه مرجع (اختیاری).
            tracking_code: کد رهگیری (اختیاری).
            callback_data: داده‌های دریافتی از درگاه (اختیاری).

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی موفقیت را ندهد.
        """
        if self.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise ValidationError(
                message=f"پرداخت در وضعیت '{self.status.value}' نمی‌تواند موفق شود.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.SUCCESS
        self.transaction_id = transaction_id
        self.reference_id = reference_id
        self.tracking_code = tracking_code
        self.paid_at = datetime.now()
        self.updated_at = datetime.now()

        if callback_data:
            self.callback_data = callback_data

        logger.info(f"Payment {self.id} marked as SUCCESS. Transaction: {transaction_id}")

    def mark_as_failed(self, error_message: str) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان ناموفق.

        Args:
            error_message: پیام خطا.

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی شکست را ندهد.
        """
        if self.status in (PaymentStatus.SUCCESS, PaymentStatus.REFUNDED):
            raise ValidationError(
                message=f"پرداخت با وضعیت '{self.status.value}' نمی‌تواند ناموفق شود.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now()
        logger.warning(f"Payment {self.id} marked as FAILED: {error_message}")

    def mark_as_canceled(self, reason: Optional[str] = None) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان لغو‌شده.

        Args:
            reason: دلیل لغو (اختیاری).

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی لغو را ندهد.
        """
        if not self.can_cancel():
            raise ValidationError(
                message=f"پرداخت در وضعیت '{self.status.value}' قابل لغو نیست.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.CANCELED
        if reason:
            self.metadata["cancel_reason"] = reason
        self.updated_at = datetime.now()
        logger.info(f"Payment {self.id} marked as CANCELED. Reason: {reason}")

    def mark_as_refunded(self, reason: Optional[str] = None) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان بازگشت‌وجه.

        Args:
            reason: دلیل بازگشت وجه (اختیاری).

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی بازگشت وجه را ندهد.
        """
        if not self.can_refund():
            raise ValidationError(
                message=f"پرداخت در وضعیت '{self.status.value}' قابل بازگشت نیست.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.REFUNDED
        if reason:
            self.metadata["refund_reason"] = reason
        self.updated_at = datetime.now()
        logger.info(f"Payment {self.id} marked as REFUNDED. Reason: {reason}")

    def mark_as_expired(self) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان منقضی‌شده.

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی انقضا را ندهد.
        """
        if self.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise ValidationError(
                message=f"پرداخت در وضعیت '{self.status.value}' نمی‌تواند منقضی شود.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.EXPIRED
        self.updated_at = datetime.now()
        logger.warning(f"Payment {self.id} marked as EXPIRED")

    def mark_as_processing(self) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان در حال پردازش.

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی پردازش را ندهد.
        """
        if self.status != PaymentStatus.PENDING:
            raise ValidationError(
                message=f"پرداخت در وضعیت '{self.status.value}' نمی‌تواند به پردازش برود.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.PROCESSING
        self.updated_at = datetime.now()
        logger.debug(f"Payment {self.id} marked as PROCESSING")

    def mark_as_waiting_verification(self, reason: Optional[str] = None) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان در انتظار تأیید.

        Args:
            reason: دلیل نیاز به تأیید (اختیاری).

        Raises:
            ValidationError: اگر وضعیت فعلی اجازه‌ی این تغییر را ندهد.
        """
        if self.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise ValidationError(
                message=f"پرداخت در وضعیت '{self.status.value}' نمی‌تواند به انتظار تأیید برود.",
                context={"payment_id": self.id, "current_status": self.status.value},
            )

        self.status = PaymentStatus.WAITING_VERIFICATION
        if reason:
            self.metadata["verification_reason"] = reason
        self.updated_at = datetime.now()
        logger.info(f"Payment {self.id} marked as WAITING_VERIFICATION. Reason: {reason}")

    def can_cancel(self) -> bool:
        """بررسی اینکه آیا پرداخت قابل لغو است."""
        return self.status.can_cancel()

    def can_refund(self) -> bool:
        """بررسی اینکه آیا پرداخت قابل بازگشت وجه است."""
        return self.status.is_refundable()

    def can_retry(self) -> bool:
        """بررسی اینکه آیا پرداخت قابل تلاش مجدد است."""
        return self.status.can_retry()

    def is_success(self) -> bool:
        """بررسی موفق بودن پرداخت."""
        return self.status.is_success()

    def is_failed(self) -> bool:
        """بررسی ناموفق بودن پرداخت."""
        return self.status.is_failed()

    def is_pending(self) -> bool:
        """بررسی در انتظار بودن پرداخت."""
        return self.status.is_pending()

    def is_final(self) -> bool:
        """بررسی نهایی بودن وضعیت پرداخت."""
        return self.status.is_final()

    def increment_retry(self) -> None:
        """افزایش تعداد تلاش‌های مجدد."""
        self.retry_count += 1
        self.updated_at = datetime.now()

    def set_expiry(self, seconds: int) -> None:
        """
        تنظیم زمان انقضای پرداخت.

        Args:
            seconds: تعداد ثانیه تا انقضا.
        """
        self.expired_at = datetime.now().timestamp() + seconds
        self.updated_at = datetime.now()

    def is_expired(self) -> bool:
        """
        بررسی انقضای پرداخت.

        Returns:
            True اگر پرداخت منقضی شده باشد.
        """
        if self.expired_at is None:
            return False
        # تبدیل timestamp به datetime
        if isinstance(self.expired_at, (int, float)):
            from datetime import datetime
            expiry_dt = datetime.fromtimestamp(self.expired_at)
            return datetime.now() > expiry_dt
        return datetime.now() > self.expired_at

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل موجودیت پرداخت به دیکشنری.

        Returns:
            دیکشنری شامل اطلاعات پرداخت.
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "amount": self.amount.amount,
            "currency": self.currency,
            "status": self.status.value,
            "gateway": self.gateway,
            "transaction_id": self.transaction_id,
            "tracking_code": self.tracking_code,
            "reference_id": self.reference_id,
            "callback_url": self.callback_url,
            "callback_data": self.callback_data,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "expired_at": self.expired_at,
            "retry_count": self.retry_count,
            "description": self.description,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Payment":
        """
        ساخت موجودیت پرداخت از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات پرداخت.

        Returns:
            نمونه‌ای از کلاس Payment.
        """
        # تبدیل وضعیت
        status = PaymentStatus.from_string(data.get("status", "pending"))
        if not status:
            status = PaymentStatus.PENDING

        # تبدیل تاریخ‌ها
        paid_at = None
        if data.get("paid_at"):
            try:
                paid_at = datetime.fromisoformat(data["paid_at"])
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
            order_id=data.get("order_id"),
            user_id=data["user_id"],
            amount=Money(data["amount"], data.get("currency", "IRR")),
            currency=data.get("currency", "IRR"),
            status=status,
            gateway=data.get("gateway", "mock"),
            transaction_id=data.get("transaction_id"),
            tracking_code=data.get("tracking_code"),
            reference_id=data.get("reference_id"),
            callback_url=data.get("callback_url"),
            callback_data=data.get("callback_data"),
            paid_at=paid_at,
            expired_at=data.get("expired_at"),
            retry_count=data.get("retry_count", 0),
            description=data.get("description"),
            error_message=data.get("error_message"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )