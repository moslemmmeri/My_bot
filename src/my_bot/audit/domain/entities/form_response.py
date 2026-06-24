# my_bot_project/src/my_bot/domain/entities/form_response.py
"""
موجودیت پاسخ فرم (Form Response Entity).

این کلاس نمایانگر پاسخ‌های ارسال‌شده توسط کاربران برای یک فرم خاص است.
هر پاسخ شامل مجموعه‌ای از مقادیر برای فیلدهای فرم به همراه اطلاعات
کاربر و زمان ارسال می‌باشد.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.form import Form

logger = get_logger(__name__)


@dataclass
class FormResponse:
    """
    موجودیت پاسخ فرم در سیستم.

    Attributes:
        id: شناسه یکتای پاسخ در دیتابیس.
        form_id: شناسه فرم مربوطه.
        user_id: شناسه کاربر پاسخ‌دهنده (اختیاری).
        answers: دیکشنری شامل پاسخ‌ها (نام فیلد -> مقدار).
        submitted_at: زمان ارسال پاسخ.
        is_valid: وضعیت اعتبارسنجی پاسخ (پس از بررسی).
        validation_errors: لیست خطاهای اعتبارسنجی (در صورت وجود).
        metadata: داده‌های اضافی.
    """

    form_id: int
    answers: Dict[str, Any]
    user_id: Optional[int] = None
    id: Optional[int] = None
    submitted_at: datetime = field(default_factory=datetime.now)
    is_valid: bool = False
    validation_errors: Optional[list[Dict[str, str]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_answers()

    def _validate_answers(self) -> None:
        """اعتبارسنجی اولیه پاسخ‌ها (عدم وجود خالی برای فیلدهای اجباری را بعداً بررسی می‌کنیم)."""
        if not isinstance(self.answers, dict):
            raise ValidationError(
                message="پاسخ‌ها باید به‌صورت دیکشنری باشند.",
                context={"form_id": self.form_id, "user_id": self.user_id},
            )

    def validate_with_form(self, form: Form) -> bool:
        """
        اعتبارسنجی پاسخ‌ها با استفاده از قوانین فرم.

        Args:
            form: فرم مربوطه (برای دسترسی به فیلدها و قوانین).

        Returns:
            True اگر پاسخ‌ها معتبر باشند، در غیر این صورت False.

        Raises:
            ValidationError: اگر فرم نامعتبر باشد یا پاسخ‌ها قابل اعتبارسنجی نباشند.
        """
        if form.id != self.form_id:
            raise ValidationError(
                message="شناسه فرم در پاسخ با فرم ارائه‌شده مطابقت ندارد.",
                context={"response_form_id": self.form_id, "provided_form_id": form.id},
            )

        # اعتبارسنجی با استفاده از متد validate_response فرم
        errors = form.validate_response(self.answers)
        self.is_valid = len(errors) == 0
        self.validation_errors = errors if errors else None

        if not self.is_valid:
            logger.warning(f"Form response for form {self.form_id} by user {self.user_id} has validation errors: {errors}")

        return self.is_valid

    def get_field_value(self, field_name: str) -> Any:
        """
        دریافت مقدار یک فیلد خاص از پاسخ‌ها.

        Args:
            field_name: نام فیلد.

        Returns:
            مقدار فیلد یا None در صورت عدم وجود.
        """
        return self.answers.get(field_name)

    def set_field_value(self, field_name: str, value: Any) -> None:
        """
        تنظیم مقدار یک فیلد در پاسخ‌ها.

        Args:
            field_name: نام فیلد.
            value: مقدار جدید.
        """
        self.answers[field_name] = value
        # پس از تغییر، وضعیت اعتبارسنجی را ریست می‌کنیم
        self.is_valid = False
        self.validation_errors = None
        logger.debug(f"Field '{field_name}' updated in response for form {self.form_id}")

    def clear_answers(self) -> None:
        """پاک کردن تمام پاسخ‌ها."""
        self.answers.clear()
        self.is_valid = False
        self.validation_errors = None
        logger.debug(f"Answers cleared for response of form {self.form_id}")

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل موجودیت پاسخ فرم به دیکشنری.

        Returns:
            دیکشنری شامل اطلاعات پاسخ.
        """
        return {
            "id": self.id,
            "form_id": self.form_id,
            "user_id": self.user_id,
            "answers": self.answers,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormResponse":
        """
        ساخت موجودیت پاسخ فرم از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات پاسخ.

        Returns:
            نمونه‌ای از کلاس FormResponse.
        """
        submitted_at = None
        if data.get("submitted_at"):
            try:
                submitted_at = datetime.fromisoformat(data["submitted_at"])
            except (ValueError, TypeError):
                submitted_at = datetime.now()

        return cls(
            id=data.get("id"),
            form_id=data["form_id"],
            user_id=data.get("user_id"),
            answers=data.get("answers", {}),
            submitted_at=submitted_at or datetime.now(),
            is_valid=data.get("is_valid", False),
            validation_errors=data.get("validation_errors"),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """نمایش رشته‌ای پاسخ فرم."""
        return f"FormResponse(id={self.id}, form_id={self.form_id}, user_id={self.user_id}, submitted_at={self.submitted_at})"