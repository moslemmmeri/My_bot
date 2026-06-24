# my_bot_project/src/my_bot/application/dtos/form_dto.py
"""
DTOهای مربوط به فرم (Form DTOs).

این ماژول شامل اشیاء انتقال داده (Data Transfer Objects) برای مدیریت
فرم‌های پویا در سیستم است. تمام DTOها از Pydantic برای اعتبارسنجی داده‌ها
استفاده می‌کنند و شامل نوع‌دهی کامل (Type Hints) هستند.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from my_bot.core.constants.form_types import FormType
from my_bot.domain.value_objects.form_field import FieldType


class FormFieldDTO(BaseModel):
    """
    DTO برای فیلد فرم.

    Attributes:
        name: نام فیلد (یکتا در فرم).
        label: برچسب نمایشی فیلد.
        type: نوع فیلد.
        is_required: آیا فیلد اجباری است.
        placeholder: متن راهنما (اختیاری).
        help_text: متن کمک (اختیاری).
        default_value: مقدار پیش‌فرض (اختیاری).
        options: لیست گزینه‌ها (برای فیلدهای انتخابی).
        validation_rules: قوانین اعتبارسنجی.
        order: ترتیب نمایش.
        group: گروه فیلد (اختیاری).
        css_class: کلاس CSS (اختیاری).
        width: عرض فیلد (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
    """
    name: str = Field(..., max_length=100, description="نام فیلد (یکتا در فرم)")
    label: str = Field(..., max_length=200, description="برچسب نمایشی فیلد")
    type: str = Field(..., description="نوع فیلد")
    is_required: bool = Field(False, description="آیا فیلد اجباری است")
    placeholder: Optional[str] = Field(None, max_length=200, description="متن راهنما")
    help_text: Optional[str] = Field(None, max_length=500, description="متن کمک")
    default_value: Optional[Any] = Field(None, description="مقدار پیش‌فرض")
    options: List[Dict[str, Any]] = Field(default_factory=list, description="گزینه‌ها")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="قوانین اعتبارسنجی")
    order: int = Field(0, description="ترتیب نمایش")
    group: Optional[str] = Field(None, max_length=100, description="گروه فیلد")
    css_class: Optional[str] = Field(None, max_length=100, description="کلاس CSS")
    width: Optional[str] = Field(None, max_length=20, description="عرض فیلد")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """اعتبارسنجی نوع فیلد."""
        valid_types = [
            FieldType.TEXT, FieldType.TEXTAREA, FieldType.NUMBER,
            FieldType.EMAIL, FieldType.PHONE, FieldType.DATE,
            FieldType.TIME, FieldType.DATETIME, FieldType.SELECT,
            FieldType.MULTI_SELECT, FieldType.RADIO, FieldType.CHECKBOX,
            FieldType.BOOLEAN, FieldType.RATING, FieldType.FILE,
            FieldType.URL, FieldType.COLOR, FieldType.RANGE,
            FieldType.HIDDEN, FieldType.BUTTON, FieldType.DIVIDER,
            FieldType.LABEL, FieldType.CUSTOM,
        ]
        if v not in valid_types:
            raise ValueError(f"نوع فیلد '{v}' نامعتبر است.")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[Dict[str, Any]], info) -> List[Dict[str, Any]]:
        """اعتبارسنجی گزینه‌ها (برای فیلدهای انتخابی)."""
        field_type = info.data.get("type")
        if field_type in [FieldType.SELECT, FieldType.MULTI_SELECT, FieldType.RADIO, FieldType.CHECKBOX]:
            if not v or len(v) < 2:
                raise ValueError("فیلدهای انتخابی باید حداقل ۲ گزینه داشته باشند.")
            for opt in v:
                if "value" not in opt or "label" not in opt:
                    raise ValueError("هر گزینه باید شامل 'value' و 'label' باشد.")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """اعتبارسنجی نام فیلد (فقط حروف، اعداد، خط تیره و زیرخط)."""
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("نام فیلد فقط می‌تواند شامل حروف، اعداد، '-' و '_' باشد.")
        return v

    @classmethod
    def from_entity(cls, field) -> "FormFieldDTO":
        """
        ساخت DTO از موجودیت FormField.

        Args:
            field: موجودیت FormField.

        Returns:
            FormFieldDTO: DTO ساخته‌شده.
        """
        return cls(
            name=field.name,
            label=field.label,
            type=field.field_type,
            is_required=field.is_required,
            placeholder=field.placeholder,
            help_text=field.help_text,
            default_value=field.default_value,
            options=field.options,
            validation_rules=field.validation_rules,
            order=field.order,
            group=field.group,
            css_class=field.css_class,
            width=field.width,
            metadata=field.metadata,
        )

    def to_entity(self) -> dict:
        """
        تبدیل DTO به دیکشنری برای ساخت موجودیت FormField.

        Returns:
            dict: دیکشنری اطلاعات فیلد.
        """
        return {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "is_required": self.is_required,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
            "default_value": self.default_value,
            "options": self.options,
            "validation_rules": self.validation_rules,
            "order": self.order,
            "group": self.group,
            "css_class": self.css_class,
            "width": self.width,
            "metadata": self.metadata,
        }


class FormCreateDTO(BaseModel):
    """
    DTO برای ایجاد فرم جدید.

    Attributes:
        title: عنوان فرم (اجباری، یکتا).
        description: توضیحات فرم (اختیاری).
        form_type: نوع فرم (اجباری).
        fields: لیست فیلدهای فرم (اجباری، حداقل ۱ فیلد).
        is_active: وضعیت فعال بودن (پیش‌فرض: True).
        is_public: عمومی بودن فرم (پیش‌فرض: True).
        requires_login: نیاز به احراز هویت (پیش‌فرض: False).
        is_multistep: چند مرحله‌ای بودن (پیش‌فرض: False).
        steps: تعداد مراحل (برای فرم‌های چند مرحله‌ای).
        submit_button_text: متن دکمه ارسال (پیش‌فرض: "✅ ارسال").
        success_message: پیام موفقیت (اختیاری).
        redirect_url: آدرس هدایت پس از ارسال (اختیاری).
        expires_at: زمان انقضا (اختیاری).
        max_submissions: حداکثر تعداد ارسال (اختیاری).
        metadata: داده‌های اضافی (اختیاری).
    """
    title: str = Field(..., max_length=200, description="عنوان فرم")
    description: Optional[str] = Field(None, max_length=1000, description="توضیحات فرم")
    form_type: str = Field(..., description="نوع فرم")
    fields: List[FormFieldDTO] = Field(..., min_length=1, description="لیست فیلدهای فرم")
    is_active: bool = Field(True, description="وضعیت فعال بودن")
    is_public: bool = Field(True, description="عمومی بودن فرم")
    requires_login: bool = Field(False, description="نیاز به احراز هویت")
    is_multistep: bool = Field(False, description="چند مرحله‌ای بودن")
    steps: int = Field(1, ge=1, description="تعداد مراحل")
    submit_button_text: str = Field("✅ ارسال", max_length=50, description="متن دکمه ارسال")
    success_message: Optional[str] = Field(None, max_length=500, description="پیام موفقیت")
    redirect_url: Optional[str] = Field(None, max_length=500, description="آدرس هدایت پس از ارسال")
    expires_at: Optional[datetime] = Field(None, description="زمان انقضا")
    max_submissions: Optional[int] = Field(None, gt=0, description="حداکثر تعداد ارسال")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("form_type")
    @classmethod
    def validate_form_type(cls, v: str) -> str:
        """اعتبارسنجی نوع فرم."""
        valid_types = [t.value for t in FormType]
        if v not in valid_types:
            raise ValueError(f"نوع فرم '{v}' نامعتبر است.")
        return v

    @model_validator(mode="after")
    def validate_steps(self) -> "FormCreateDTO":
        """اعتبارسنجی تعداد مراحل."""
        if self.is_multistep:
            if self.steps < 2:
                raise ValueError("فرم چند مرحله‌ای باید حداقل ۲ مرحله داشته باشد.")
            if self.steps > len(self.fields):
                raise ValueError("تعداد مراحل نمی‌تواند بیشتر از تعداد فیلدها باشد.")
        else:
            self.steps = 1
        return self

    @model_validator(mode="after")
    def validate_dates(self) -> "FormCreateDTO":
        """اعتبارسنجی تاریخ‌ها."""
        if self.expires_at and self.expires_at <= datetime.now():
            raise ValueError("تاریخ انقضا باید در آینده باشد.")
        return self


class FormUpdateDTO(BaseModel):
    """
    DTO برای به‌روزرسانی فرم.

    Attributes:
        title: عنوان جدید (اختیاری).
        description: توضیحات جدید (اختیاری).
        form_type: نوع جدید (اختیاری).
        fields: لیست فیلدهای جدید (اختیاری).
        is_active: وضعیت فعال بودن جدید (اختیاری).
        is_public: عمومی بودن جدید (اختیاری).
        requires_login: نیاز به احراز هویت جدید (اختیاری).
        is_multistep: چند مرحله‌ای بودن جدید (اختیاری).
        steps: تعداد مراحل جدید (اختیاری).
        submit_button_text: متن دکمه ارسال جدید (اختیاری).
        success_message: پیام موفقیت جدید (اختیاری).
        redirect_url: آدرس هدایت جدید (اختیاری).
        expires_at: زمان انقضا جدید (اختیاری).
        max_submissions: حداکثر تعداد ارسال جدید (اختیاری).
        metadata: داده‌های اضافی جدید (اختیاری).
    """
    title: Optional[str] = Field(None, max_length=200, description="عنوان جدید")
    description: Optional[str] = Field(None, max_length=1000, description="توضیحات جدید")
    form_type: Optional[str] = Field(None, description="نوع جدید")
    fields: Optional[List[FormFieldDTO]] = Field(None, description="لیست فیلدهای جدید")
    is_active: Optional[bool] = Field(None, description="وضعیت فعال بودن جدید")
    is_public: Optional[bool] = Field(None, description="عمومی بودن جدید")
    requires_login: Optional[bool] = Field(None, description="نیاز به احراز هویت جدید")
    is_multistep: Optional[bool] = Field(None, description="چند مرحله‌ای بودن جدید")
    steps: Optional[int] = Field(None, ge=1, description="تعداد مراحل جدید")
    submit_button_text: Optional[str] = Field(None, max_length=50, description="متن دکمه ارسال جدید")
    success_message: Optional[str] = Field(None, max_length=500, description="پیام موفقیت جدید")
    redirect_url: Optional[str] = Field(None, max_length=500, description="آدرس هدایت جدید")
    expires_at: Optional[datetime] = Field(None, description="زمان انقضا جدید")
    max_submissions: Optional[int] = Field(None, gt=0, description="حداکثر تعداد ارسال جدید")
    metadata: Optional[Dict[str, Any]] = Field(None, description="داده‌های اضافی جدید")

    @field_validator("form_type")
    @classmethod
    def validate_form_type(cls, v: Optional[str]) -> Optional[str]:
        """اعتبارسنجی نوع فرم."""
        if v is not None:
            valid_types = [t.value for t in FormType]
            if v not in valid_types:
                raise ValueError(f"نوع فرم '{v}' نامعتبر است.")
        return v

    @model_validator(mode="after")
    def validate_steps(self) -> "FormUpdateDTO":
        """اعتبارسنجی تعداد مراحل."""
        if self.is_multistep is not None and self.is_multistep:
            steps = self.steps or 1
            if steps < 2:
                raise ValueError("فرم چند مرحله‌ای باید حداقل ۲ مرحله داشته باشد.")
            if self.fields is not None and steps > len(self.fields):
                raise ValueError("تعداد مراحل نمی‌تواند بیشتر از تعداد فیلدها باشد.")
        return self


class FormResponseDTO(BaseModel):
    """
    DTO برای پاسخ اطلاعات فرم.

    Attributes:
        id: شناسه فرم.
        title: عنوان فرم.
        description: توضیحات فرم.
        form_type: نوع فرم.
        fields: لیست فیلدهای فرم.
        is_active: وضعیت فعال بودن.
        is_public: عمومی بودن فرم.
        requires_login: نیاز به احراز هویت.
        is_multistep: چند مرحله‌ای بودن.
        steps: تعداد مراحل.
        submit_button_text: متن دکمه ارسال.
        success_message: پیام موفقیت.
        redirect_url: آدرس هدایت.
        created_by: شناسه کاربر سازنده.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        published_at: زمان انتشار.
        expires_at: زمان انقضا.
        max_submissions: حداکثر تعداد ارسال.
        submission_count: تعداد ارسال‌های ثبت‌شده.
        metadata: داده‌های اضافی.
    """
    id: Optional[int] = Field(None, description="شناسه فرم")
    title: str = Field(..., description="عنوان فرم")
    description: Optional[str] = Field(None, description="توضیحات فرم")
    form_type: str = Field(..., description="نوع فرم")
    fields: List[FormFieldDTO] = Field(..., description="لیست فیلدهای فرم")
    is_active: bool = Field(True, description="وضعیت فعال بودن")
    is_public: bool = Field(True, description="عمومی بودن فرم")
    requires_login: bool = Field(False, description="نیاز به احراز هویت")
    is_multistep: bool = Field(False, description="چند مرحله‌ای بودن")
    steps: int = Field(1, description="تعداد مراحل")
    submit_button_text: str = Field("✅ ارسال", description="متن دکمه ارسال")
    success_message: Optional[str] = Field(None, description="پیام موفقیت")
    redirect_url: Optional[str] = Field(None, description="آدرس هدایت")
    created_by: int = Field(..., description="شناسه کاربر سازنده")
    created_at: datetime = Field(default_factory=datetime.now, description="زمان ایجاد")
    updated_at: datetime = Field(default_factory=datetime.now, description="زمان آخرین به‌روزرسانی")
    published_at: Optional[datetime] = Field(None, description="زمان انتشار")
    expires_at: Optional[datetime] = Field(None, description="زمان انقضا")
    max_submissions: Optional[int] = Field(None, description="حداکثر تعداد ارسال")
    submission_count: int = Field(0, description="تعداد ارسال‌های ثبت‌شده")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, form) -> "FormResponseDTO":
        """
        ساخت DTO از موجودیت فرم.

        Args:
            form: موجودیت Form.

        Returns:
            FormResponseDTO: DTO ساخته‌شده.
        """
        return cls(
            id=form.id,
            title=form.title,
            description=form.description,
            form_type=form.form_type.value,
            fields=[FormFieldDTO.from_entity(field) for field in form.fields],
            is_active=form.is_active,
            is_public=form.is_public,
            requires_login=form.requires_login,
            is_multistep=form.is_multistep,
            steps=form.steps,
            submit_button_text=form.submit_button_text,
            success_message=form.success_message,
            redirect_url=form.redirect_url,
            created_by=form.created_by,
            created_at=form.created_at,
            updated_at=form.updated_at,
            published_at=form.published_at,
            expires_at=form.expires_at,
            max_submissions=form.max_submissions,
            submission_count=form.submission_count,
            metadata=form.metadata,
        )

    def is_available(self) -> bool:
        """بررسی در دسترس بودن فرم."""
        if not self.is_active:
            return False
        if self.published_at and datetime.now() < self.published_at:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        if self.max_submissions is not None and self.submission_count >= self.max_submissions:
            return False
        return True


class FormSubmitDTO(BaseModel):
    """
    DTO برای ارسال پاسخ فرم.

    Attributes:
        form_id: شناسه فرم (اجباری).
        answers: دیکشنری پاسخ‌ها (نام فیلد -> مقدار).
        metadata: داده‌های اضافی (اختیاری).
    """
    form_id: int = Field(..., gt=0, description="شناسه فرم")
    answers: Dict[str, Any] = Field(..., description="پاسخ‌های فرم")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="داده‌های اضافی")

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی پاسخ‌ها (نباید خالی باشد)."""
        if not v:
            raise ValueError("پاسخ‌ها نمی‌توانند خالی باشند.")
        return v


class FormAnalyticsDTO(BaseModel):
    """
    DTO برای تحلیل فرم.

    Attributes:
        form_id: شناسه فرم.
        form_title: عنوان فرم.
        form_type: نوع فرم.
        total_responses: تعداد کل پاسخ‌ها.
        valid_responses: تعداد پاسخ‌های معتبر.
        invalid_responses: تعداد پاسخ‌های نامعتبر.
        unique_users: تعداد کاربران یکتا.
        completion_rate: نرخ تکمیل (درصد).
        daily_distribution: توزیع روزانه پاسخ‌ها.
        field_analytics: تحلیل فیلدها.
    """
    form_id: int = Field(..., description="شناسه فرم")
    form_title: str = Field(..., description="عنوان فرم")
    form_type: str = Field(..., description="نوع فرم")
    total_responses: int = Field(0, description="تعداد کل پاسخ‌ها")
    valid_responses: int = Field(0, description="تعداد پاسخ‌های معتبر")
    invalid_responses: int = Field(0, description="تعداد پاسخ‌های نامعتبر")
    unique_users: int = Field(0, description="تعداد کاربران یکتا")
    completion_rate: float = Field(0.0, description="نرخ تکمیل (درصد)")
    daily_distribution: Dict[str, int] = Field(default_factory=dict, description="توزیع روزانه پاسخ‌ها")
    field_analytics: List[Dict[str, Any]] = Field(default_factory=list, description="تحلیل فیلدها")

    class Config:
        from_attributes = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormAnalyticsDTO":
        """
        ساخت DTO از دیکشنری.

        Args:
            data: دیکشنری داده‌ها.

        Returns:
            FormAnalyticsDTO: DTO ساخته‌شده.
        """
        return cls(**data)