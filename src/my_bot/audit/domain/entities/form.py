# my_bot_project/src/my_bot/domain/entities/form.py
"""
موجودیت فرم (Form Entity).

این کلاس نمایانگر یک فرم پویا در سیستم است که توسط ادمین ساخته می‌شود
و کاربران می‌توانند آن را پر کرده و ارسال کنند.
فرم شامل مجموعه‌ای از فیلدها با انواع مختلف، اعتبارسنجی‌ها،
و قوانین خاص برای نمایش و پردازش است.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Set

from my_bot.core.constants.form_types import FormType
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.form_field import FormField

logger = get_logger(__name__)


@dataclass
class Form:
    """
    موجودیت فرم پویا در سیستم.

    Attributes:
        id: شناسه یکتای فرم در دیتابیس.
        title: عنوان فرم.
        description: توضیحات فرم (اختیاری).
        form_type: نوع فرم (بر اساس FormType).
        fields: لیست فیلدهای فرم (FormField).
        is_active: وضعیت فعال بودن فرم.
        is_public: عمومی بودن فرم (قابل مشاهده برای همه کاربران).
        requires_login: نیاز به احراز هویت برای پر کردن فرم.
        is_multistep: چند مرحله‌ای بودن فرم.
        steps: تعداد مراحل (برای فرم‌های چند مرحله‌ای).
        current_step: مرحله فعلی (در زمان پر کردن).
        submit_button_text: متن دکمه ارسال.
        success_message: پیام موفقیت پس از ارسال.
        redirect_url: آدرس هدایت پس از ارسال (اختیاری).
        created_by: شناسه کاربر سازنده (ادمین).
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        published_at: زمان انتشار (در صورت انتشار).
        expires_at: زمان انقضا (اختیاری).
        max_submissions: حداکثر تعداد ارسال (اختیاری).
        submission_count: تعداد ارسال‌های ثبت‌شده.
        metadata: داده‌های اضافی.
    """

    title: str
    form_type: FormType
    fields: List[FormField]
    created_by: int
    description: Optional[str] = None
    is_active: bool = True
    is_public: bool = True
    requires_login: bool = False
    is_multistep: bool = False
    steps: int = 1
    current_step: int = 0
    submit_button_text: str = "✅ ارسال"
    success_message: Optional[str] = None
    redirect_url: Optional[str] = None
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    max_submissions: Optional[int] = None
    submission_count: int = 0
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_title()
        self._validate_fields()
        self._validate_steps()
        self._validate_dates()
        self._validate_max_submissions()

    def _validate_title(self) -> None:
        """اعتبارسنجی عنوان فرم."""
        if not self.title or not self.title.strip():
            raise ValidationError(
                message="عنوان فرم نمی‌تواند خالی باشد.",
                context={"form_id": self.id},
            )

    def _validate_fields(self) -> None:
        """اعتبارسنجی فیلدهای فرم."""
        if not self.fields:
            raise ValidationError(
                message="فرم باید حداقل یک فیلد داشته باشد.",
                context={"form_id": self.id, "title": self.title},
            )

        # بررسی یکتایی نام فیلدها
        field_names = [f.name for f in self.fields]
        if len(field_names) != len(set(field_names)):
            raise ValidationError(
                message="نام فیلدها باید یکتا باشند.",
                context={"form_id": self.id, "field_names": field_names},
            )

    def _validate_steps(self) -> None:
        """اعتبارسنجی تعداد مراحل."""
        if self.is_multistep:
            if self.steps < 2:
                raise ValidationError(
                    message="فرم چند مرحله‌ای باید حداقل ۲ مرحله داشته باشد.",
                    context={"form_id": self.id, "steps": self.steps},
                )
            if self.steps > len(self.fields):
                raise ValidationError(
                    message="تعداد مراحل نمی‌تواند بیشتر از تعداد فیلدها باشد.",
                    context={"form_id": self.id, "steps": self.steps, "fields_count": len(self.fields)},
                )
        else:
            self.steps = 1

    def _validate_dates(self) -> None:
        """اعتبارسنجی تاریخ‌ها."""
        if self.expires_at and self.created_at >= self.expires_at:
            raise ValidationError(
                message="تاریخ انقضا باید بعد از زمان ایجاد باشد.",
                context={"form_id": self.id, "created_at": self.created_at, "expires_at": self.expires_at},
            )

        if self.published_at and self.expires_at and self.published_at >= self.expires_at:
            raise ValidationError(
                message="تاریخ انتشار باید قبل از تاریخ انقضا باشد.",
                context={"form_id": self.id, "published_at": self.published_at, "expires_at": self.expires_at},
            )

    def _validate_max_submissions(self) -> None:
        """اعتبارسنجی حداکثر تعداد ارسال."""
        if self.max_submissions is not None and self.max_submissions <= 0:
            raise ValidationError(
                message="حداکثر تعداد ارسال باید بیشتر از صفر باشد.",
                context={"form_id": self.id, "max_submissions": self.max_submissions},
            )

        # بررسی اینکه تعداد ارسال از حد مجاز بیشتر نباشد
        if self.max_submissions is not None and self.submission_count > self.max_submissions:
            self.is_active = False
            logger.warning(f"Form {self.id} submission count ({self.submission_count}) exceeded limit ({self.max_submissions}). Deactivated.")

    def is_available(self) -> bool:
        """
        بررسی در دسترس بودن فرم (فعال، منتشر شده، منقضی نشده).

        Returns:
            True اگر فرم در دسترس باشد.
        """
        if not self.is_active:
            return False

        if self.published_at and datetime.now() < self.published_at:
            return False

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        if self.max_submissions is not None and self.submission_count >= self.max_submissions:
            return False

        return True

    def is_expired(self) -> bool:
        """بررسی انقضای فرم."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_published(self) -> bool:
        """بررسی انتشار فرم."""
        if self.published_at is None:
            return False
        return datetime.now() >= self.published_at

    def can_submit(self, user_id: Optional[int] = None) -> bool:
        """
        بررسی اینکه آیا کاربر می‌تواند فرم را پر کند.

        Args:
            user_id: شناسه کاربر (اختیاری).

        Returns:
            True اگر کاربر مجاز به پر کردن فرم باشد.
        """
        # بررسی در دسترس بودن فرم
        if not self.is_available():
            return False

        # بررسی نیاز به لاگین
        if self.requires_login and user_id is None:
            return False

        return True

    def get_field(self, field_name: str) -> Optional[FormField]:
        """
        دریافت یک فیلد خاص از فرم با استفاده از نام.

        Args:
            field_name: نام فیلد.

        Returns:
            فیلد مورد نظر یا None در صورت عدم وجود.
        """
        for field in self.fields:
            if field.name == field_name:
                return field
        return None

    def get_fields_by_step(self, step: int) -> List[FormField]:
        """
        دریافت فیلدهای یک مرحله خاص (برای فرم‌های چند مرحله‌ای).

        Args:
            step: شماره مرحله (از ۱ شروع می‌شود).

        Returns:
            لیست فیلدهای آن مرحله.
        """
        if not self.is_multistep:
            return self.fields

        if step < 1 or step > self.steps:
            return []

        # توزیع فیلدها بین مراحل به‌صورت مساوی
        fields_per_step = len(self.fields) // self.steps
        start_idx = (step - 1) * fields_per_step
        end_idx = start_idx + fields_per_step

        # اگر مرحله آخر است، فیلدهای باقی‌مانده را هم اضافه می‌کنیم
        if step == self.steps:
            end_idx = len(self.fields)

        return self.fields[start_idx:end_idx]

    def get_step_count(self) -> int:
        """
        دریافت تعداد مراحل فرم.

        Returns:
            تعداد مراحل.
        """
        return self.steps if self.is_multistep else 1

    def validate_response(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        اعتبارسنجی پاسخ‌های ارسال‌شده برای فرم.

        Args:
            data: دیکشنری شامل پاسخ‌ها (نام فیلد -> مقدار).

        Returns:
            لیست خطاها (هر خطا شامل field و message).
        """
        errors = []

        for field in self.fields:
            value = data.get(field.name)

            # بررسی فیلدهای اجباری
            if field.is_required and (value is None or value == ""):
                errors.append({
                    "field": field.name,
                    "message": f"فیلد '{field.label}' اجباری است."
                })
                continue

            # اعتبارسنجی نوع و مقدار (اگر مقدار وجود داشته باشد)
            if value is not None and value != "":
                validation_error = field.validate(value)
                if validation_error:
                    errors.append({
                        "field": field.name,
                        "message": validation_error
                    })

        return errors

    def increment_submission_count(self) -> None:
        """
        افزایش تعداد ارسال‌های فرم.

        Raises:
            ValidationError: اگر فرم غیرفعال باشد یا به حد مجاز رسیده باشد.
        """
        if not self.is_active:
            raise ValidationError(
                message="فرم غیرفعال است و نمی‌توان آن را ارسال کرد.",
                context={"form_id": self.id},
            )

        if self.max_submissions is not None and self.submission_count >= self.max_submissions:
            raise ValidationError(
                message="حداکثر تعداد ارسال فرم به پایان رسیده است.",
                context={"form_id": self.id, "max_submissions": self.max_submissions},
            )

        self.submission_count += 1
        self.updated_at = datetime.now()
        logger.debug(f"Form {self.id} submission count increased to {self.submission_count}")

    def publish(self) -> None:
        """انتشار فرم."""
        if not self.is_active:
            raise ValidationError(
                message="فرم غیرفعال است و نمی‌توان آن را منتشر کرد.",
                context={"form_id": self.id},
            )

        self.published_at = datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"Form {self.id} published at {self.published_at}")

    def activate(self) -> None:
        """فعال‌سازی فرم."""
        if not self.is_active:
            self.is_active = True
            self.updated_at = datetime.now()
            logger.info(f"Form {self.id} activated.")

    def deactivate(self, reason: Optional[str] = None) -> None:
        """
        غیرفعال‌سازی فرم.

        Args:
            reason: دلیل غیرفعال‌سازی (اختیاری).
        """
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.now()
            if reason:
                self.metadata["deactivation_reason"] = reason
            logger.info(f"Form {self.id} deactivated. Reason: {reason}")

    def add_field(self, field: FormField) -> None:
        """
        افزودن یک فیلد جدید به فرم.

        Args:
            field: فیلد جدید.

        Raises:
            ValidationError: اگر فیلدی با این نام از قبل وجود داشته باشد.
        """
        if self.get_field(field.name) is not None:
            raise ValidationError(
                message=f"فیلدی با نام '{field.name}' از قبل در فرم وجود دارد.",
                context={"form_id": self.id, "field_name": field.name},
            )

        self.fields.append(field)
        self.updated_at = datetime.now()
        logger.debug(f"Field '{field.name}' added to form {self.id}")

    def remove_field(self, field_name: str) -> bool:
        """
        حذف یک فیلد از فرم.

        Args:
            field_name: نام فیلد.

        Returns:
            True اگر فیلد حذف شد، False اگر فیلد وجود نداشت.
        """
        for i, field in enumerate(self.fields):
            if field.name == field_name:
                self.fields.pop(i)
                self.updated_at = datetime.now()
                logger.debug(f"Field '{field_name}' removed from form {self.id}")
                return True
        return False

    def update_field(self, field_name: str, updated_field: FormField) -> bool:
        """
        به‌روزرسانی یک فیلد در فرم.

        Args:
            field_name: نام فیلد فعلی.
            updated_field: فیلد جدید با اطلاعات به‌روز.

        Returns:
            True اگر فیلد به‌روزرسانی شد، False اگر فیلد وجود نداشت.
        """
        for i, field in enumerate(self.fields):
            if field.name == field_name:
                # اگر نام تغییر کرده، بررسی یکتایی
                if field_name != updated_field.name and self.get_field(updated_field.name) is not None:
                    raise ValidationError(
                        message=f"فیلدی با نام '{updated_field.name}' از قبل در فرم وجود دارد.",
                        context={"form_id": self.id, "field_name": updated_field.name},
                    )
                self.fields[i] = updated_field
                self.updated_at = datetime.now()
                logger.debug(f"Field '{field_name}' updated in form {self.id}")
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل موجودیت فرم به دیکشنری.

        Returns:
            دیکشنری شامل اطلاعات فرم.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "form_type": self.form_type.value,
            "fields": [field.to_dict() for field in self.fields],
            "is_active": self.is_active,
            "is_public": self.is_public,
            "requires_login": self.requires_login,
            "is_multistep": self.is_multistep,
            "steps": self.steps,
            "current_step": self.current_step,
            "submit_button_text": self.submit_button_text,
            "success_message": self.success_message,
            "redirect_url": self.redirect_url,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "max_submissions": self.max_submissions,
            "submission_count": self.submission_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Form":
        """
        ساخت موجودیت فرم از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات فرم.

        Returns:
            نمونه‌ای از کلاس Form.
        """
        # تبدیل فیلدها
        fields = []
        for field_data in data.get("fields", []):
            fields.append(FormField.from_dict(field_data))

        # تبدیل نوع فرم
        form_type = FormType.from_string(data.get("form_type", "custom"))
        if not form_type:
            form_type = FormType.CUSTOM

        # تبدیل تاریخ‌ها
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

        published_at = None
        if data.get("published_at"):
            try:
                published_at = datetime.fromisoformat(data["published_at"])
            except (ValueError, TypeError):
                pass

        expires_at = None
        if data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(data["expires_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data.get("description"),
            form_type=form_type,
            fields=fields,
            is_active=data.get("is_active", True),
            is_public=data.get("is_public", True),
            requires_login=data.get("requires_login", False),
            is_multistep=data.get("is_multistep", False),
            steps=data.get("steps", 1),
            current_step=data.get("current_step", 0),
            submit_button_text=data.get("submit_button_text", "✅ ارسال"),
            success_message=data.get("success_message"),
            redirect_url=data.get("redirect_url"),
            created_by=data["created_by"],
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            published_at=published_at,
            expires_at=expires_at,
            max_submissions=data.get("max_submissions"),
            submission_count=data.get("submission_count", 0),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """نمایش رشته‌ای فرم."""
        return f"Form({self.id}, {self.title}, type: {self.form_type.value}, fields: {len(self.fields)})"