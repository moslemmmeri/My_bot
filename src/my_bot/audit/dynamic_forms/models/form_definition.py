# my_bot_project/src/my_bot/dynamic_forms/models/form_definition.py
"""
تعریف فرم پویا (Form Definition).

این ماژول شامل کلاس `FormDefinition` است که ساختار یک فرم پویا را تعریف می‌کند.
یک فرم شامل عنوان، توضیحات، لیست فیلدها، تنظیمات نمایش، اعتبارسنجی‌ها و منطق شرطی است.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.dynamic_forms.models.form_field import DynamicFormField

logger = get_logger(__name__)


class FormStatus(str, Enum):
    """وضعیت‌های مختلف فرم."""
    DRAFT = "draft"          # پیش‌نویس
    ACTIVE = "active"        # فعال
    PAUSED = "paused"        # متوقف
    EXPIRED = "expired"      # منقضی
    ARCHIVED = "archived"    # بایگانی


class FormRenderMode(str, Enum):
    """حالت‌های نمایش فرم."""
    STEPPED = "stepped"      # مرحله‌ای (چند مرحله‌ای)
    SCROLLABLE = "scrollable"  # یک‌صفحه‌ای با اسکرول
    PAGINATED = "paginated"    # صفحه‌بندی‌شده


@dataclass
class FormDefinition:
    """
    تعریف یک فرم پویا.

    Attributes:
        id: شناسه یکتای فرم (اختیاری).
        title: عنوان فرم.
        description: توضیحات فرم (اختیاری).
        fields: لیست فیلدهای فرم.
        status: وضعیت فرم (پیش‌فرض: DRAFT).
        render_mode: حالت نمایش فرم (پیش‌فرض: STEPPED).
        steps: تعداد مراحل (برای حالت STEPPED).
        submit_button_text: متن دکمه ارسال (پیش‌فرض: "ارسال").
        success_message: پیام موفقیت پس از ارسال (اختیاری).
        redirect_url: آدرس هدایت پس از ارسال (اختیاری).
        webhook_url: آدرس وب‌هوک برای ارسال داده‌ها (اختیاری).
        is_public: عمومی بودن فرم (پیش‌فرض: True).
        requires_login: نیاز به احراز هویت (پیش‌فرض: False).
        allowed_roles: نقش‌های مجاز برای پر کردن فرم (خالی یعنی همه).
        max_submissions: حداکثر تعداد ارسال (اختیاری).
        submission_count: تعداد ارسال‌های ثبت‌شده (پیش‌فرض: ۰).
        created_by: شناسه کاربر سازنده (اختیاری).
        created_at: زمان ایجاد (پیش‌فرض: زمان حال).
        updated_at: زمان آخرین به‌روزرسانی (پیش‌فرض: زمان حال).
        published_at: زمان انتشار (اختیاری).
        expires_at: زمان انقضا (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
        on_submit: تابع callback پس از ارسال (اختیاری).
        on_validate: تابع اعتبارسنجی سفارشی (اختیاری).
    """

    title: str
    fields: List[DynamicFormField]
    id: Optional[int] = None
    description: Optional[str] = None
    status: FormStatus = FormStatus.DRAFT
    render_mode: FormRenderMode = FormRenderMode.STEPPED
    steps: int = 1
    submit_button_text: str = "✅ ارسال"
    success_message: Optional[str] = None
    redirect_url: Optional[str] = None
    webhook_url: Optional[str] = None
    is_public: bool = True
    requires_login: bool = False
    allowed_roles: List[str] = field(default_factory=list)
    max_submissions: Optional[int] = None
    submission_count: int = 0
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    on_submit: Optional[Callable] = None
    on_validate: Optional[Callable] = None

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_title()
        self._validate_fields()
        self._validate_steps()
        self._validate_dates()

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

        # اعتبارسنجی هر فیلد (با فرض اینکه فیلدها خودشان اعتبارسنجی می‌شوند)
        for field in self.fields:
            if not field.name or not field.label:
                raise ValidationError(
                    message="تمام فیلدها باید دارای نام و برچسب باشند.",
                    context={"form_id": self.id, "field": field},
                )

    def _validate_steps(self) -> None:
        """اعتبارسنجی تعداد مراحل."""
        if self.render_mode == FormRenderMode.STEPPED:
            if self.steps < 1:
                self.steps = 1
            if self.steps > len(self.fields):
                self.steps = len(self.fields)

            # اگر مراحل بیشتر از ۱ است ولی فیلدها کافی نیست
            if self.steps > 1 and len(self.fields) < self.steps:
                self.steps = len(self.fields)
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

    def get_field(self, field_name: str) -> Optional[DynamicFormField]:
        """
        دریافت یک فیلد با نام مشخص.

        Args:
            field_name: نام فیلد.

        Returns:
            Optional[DynamicFormField]: فیلد مورد نظر یا None.
        """
        for field in self.fields:
            if field.name == field_name:
                return field
        return None

    def get_fields_by_step(self, step: int) -> List[DynamicFormField]:
        """
        دریافت فیلدهای یک مرحله خاص (برای فرم‌های مرحله‌ای).

        Args:
            step: شماره مرحله (از ۱ شروع می‌شود).

        Returns:
            List[DynamicFormField]: لیست فیلدهای آن مرحله.
        """
        if self.render_mode != FormRenderMode.STEPPED:
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
            int: تعداد مراحل.
        """
        if self.render_mode == FormRenderMode.STEPPED:
            return self.steps
        return 1

    def is_available(self) -> bool:
        """
        بررسی در دسترس بودن فرم.

        Returns:
            bool: True اگر فرم در دسترس باشد.
        """
        if self.status != FormStatus.ACTIVE:
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

    def can_submit(self, user_id: Optional[int] = None, user_role: Optional[str] = None) -> bool:
        """
        بررسی اینکه آیا کاربر می‌تواند فرم را پر کند.

        Args:
            user_id: شناسه کاربر (اختیاری).
            user_role: نقش کاربر (اختیاری).

        Returns:
            bool: True اگر کاربر مجاز به پر کردن فرم باشد.
        """
        # بررسی در دسترس بودن فرم
        if not self.is_available():
            return False

        # بررسی نیاز به لاگین
        if self.requires_login and user_id is None:
            return False

        # بررسی نقش‌های مجاز
        if self.allowed_roles and user_role and user_role not in self.allowed_roles:
            return False

        return True

    def validate_response(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        اعتبارسنجی پاسخ‌های ارسال‌شده برای فرم.

        Args:
            data: دیکشنری شامل پاسخ‌ها (نام فیلد -> مقدار).

        Returns:
            List[Dict[str, str]]: لیست خطاها (هر خطا شامل field و message).

        Raises:
            ValidationError: در صورت بروز خطا در اعتبارسنجی سفارشی (در صورت وجود).
        """
        errors = []

        for field in self.fields:
            value = data.get(field.name)

            # بررسی فیلدهای اجباری
            if field.is_required and (value is None or value == "" or value == []):
                errors.append({
                    "field": field.name,
                    "message": f"فیلد '{field.label}' اجباری است."
                })
                continue

            # اعتبارسنجی نوع و مقدار (اگر مقدار وجود داشته باشد)
            if value is not None and value != "" and value != []:
                validation_error = field.validate(value)
                if validation_error:
                    errors.append({
                        "field": field.name,
                        "message": validation_error
                    })

        # اگر تابع اعتبارسنجی سفارشی وجود دارد، اجرا کن
        if self.on_validate:
            try:
                custom_errors = self.on_validate(data)
                if custom_errors:
                    if isinstance(custom_errors, list):
                        errors.extend(custom_errors)
                    elif isinstance(custom_errors, dict):
                        for field, message in custom_errors.items():
                            errors.append({"field": field, "message": message})
            except Exception as e:
                logger.error(f"Error in custom validation: {e}")
                raise ValidationError(
                    message=f"خطا در اعتبارسنجی سفارشی: {str(e)}",
                    context={"form_id": self.id},
                )

        return errors

    def increment_submission_count(self) -> None:
        """
        افزایش تعداد ارسال‌های فرم.

        Raises:
            ValidationError: اگر فرم غیرفعال باشد یا به حد مجاز رسیده باشد.
        """
        if self.status != FormStatus.ACTIVE:
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

    def add_field(self, field: DynamicFormField, position: Optional[int] = None) -> None:
        """
        افزودن یک فیلد جدید به فرم.

        Args:
            field: فیلد جدید.
            position: موقعیت درج (اختیاری، در صورت None به انتها اضافه می‌شود).

        Raises:
            ValidationError: اگر فیلدی با این نام از قبل وجود داشته باشد.
        """
        if self.get_field(field.name) is not None:
            raise ValidationError(
                message=f"فیلدی با نام '{field.name}' از قبل در فرم وجود دارد.",
                context={"form_id": self.id, "field_name": field.name},
            )

        if position is None:
            self.fields.append(field)
        else:
            self.fields.insert(position, field)

        self.updated_at = datetime.now()
        logger.debug(f"Field '{field.name}' added to form {self.id}")

    def remove_field(self, field_name: str) -> bool:
        """
        حذف یک فیلد از فرم.

        Args:
            field_name: نام فیلد.

        Returns:
            bool: True اگر فیلد حذف شد، False اگر فیلد وجود نداشت.
        """
        for i, field in enumerate(self.fields):
            if field.name == field_name:
                self.fields.pop(i)
                self.updated_at = datetime.now()
                logger.debug(f"Field '{field_name}' removed from form {self.id}")
                return True
        return False

    def update_field(self, field_name: str, updated_field: DynamicFormField) -> bool:
        """
        به‌روزرسانی یک فیلد در فرم.

        Args:
            field_name: نام فیلد فعلی.
            updated_field: فیلد جدید با اطلاعات به‌روز.

        Returns:
            bool: True اگر فیلد به‌روزرسانی شد، False اگر فیلد وجود نداشت.

        Raises:
            ValidationError: اگر نام جدید تکراری باشد.
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
        تبدیل فرم به دیکشنری برای سریال‌سازی.

        Returns:
            Dict[str, Any]: دیکشنری فرم.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "fields": [field.to_dict() for field in self.fields],
            "status": self.status.value,
            "render_mode": self.render_mode.value,
            "steps": self.steps,
            "submit_button_text": self.submit_button_text,
            "success_message": self.success_message,
            "redirect_url": self.redirect_url,
            "webhook_url": self.webhook_url,
            "is_public": self.is_public,
            "requires_login": self.requires_login,
            "allowed_roles": self.allowed_roles,
            "max_submissions": self.max_submissions,
            "submission_count": self.submission_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormDefinition":
        """
        ساخت فرم از دیکشنری.

        Args:
            data: دیکشنری فرم.

        Returns:
            FormDefinition: نمونه فرم.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        # تبدیل فیلدها
        fields = []
        for field_data in data.get("fields", []):
            fields.append(DynamicFormField.from_dict(field_data))

        # تبدیل وضعیت و حالت نمایش
        status = FormStatus(data.get("status", "draft"))
        render_mode = FormRenderMode(data.get("render_mode", "stepped"))

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
            fields=fields,
            status=status,
            render_mode=render_mode,
            steps=data.get("steps", 1),
            submit_button_text=data.get("submit_button_text", "✅ ارسال"),
            success_message=data.get("success_message"),
            redirect_url=data.get("redirect_url"),
            webhook_url=data.get("webhook_url"),
            is_public=data.get("is_public", True),
            requires_login=data.get("requires_login", False),
            allowed_roles=data.get("allowed_roles", []),
            max_submissions=data.get("max_submissions"),
            submission_count=data.get("submission_count", 0),
            created_by=data.get("created_by"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            published_at=published_at,
            expires_at=expires_at,
            metadata=data.get("metadata", {}),
        )