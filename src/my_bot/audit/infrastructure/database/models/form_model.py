# my_bot_project/src/my_bot/infrastructure/database/models/form_model.py
"""
مدل SQLAlchemy برای جدول فرم‌ها (FormModel).

این مدل معادل موجودیت Form در لایه دامنه است و نگاشت به جدول forms را انجام می‌دهد.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from my_bot.infrastructure.database.models import Base
from my_bot.core.constants.form_types import FormType
from my_bot.domain.entities.form import Form
from my_bot.domain.value_objects.form_field import FormField


class FormModel(Base):
    """
    مدل SQLAlchemy برای جدول forms.

    Attributes:
        id: شناسه یکتای فرم (Primary Key)
        title: عنوان فرم
        description: توضیحات فرم
        form_type: نوع فرم
        fields: لیست فیلدهای فرم (JSON)
        is_active: وضعیت فعال بودن فرم
        is_public: عمومی بودن فرم
        requires_login: نیاز به احراز هویت
        is_multistep: چند مرحله‌ای بودن
        steps: تعداد مراحل
        submit_button_text: متن دکمه ارسال
        success_message: پیام موفقیت
        redirect_url: آدرس هدایت پس از ارسال
        created_by: شناسه کاربر سازنده (ادمین)
        created_at: زمان ایجاد
        updated_at: زمان آخرین به‌روزرسانی
        published_at: زمان انتشار
        expires_at: زمان انقضا
        max_submissions: حداکثر تعداد ارسال
        submission_count: تعداد ارسال‌های ثبت‌شده
        submission_message: پیام پس از ارسال (مهاجرت ۰۰۲)
        is_editable: اجازه ویرایش پس از ارسال (مهاجرت ۰۰۲)
        save_progress: ذخیره خودکار پیشرفت (مهاجرت ۰۰۲)
        notification_emails: ایمیل‌های نوتیفیکیشن (JSON) (مهاجرت ۰۰۲)
        webhook_url: وب‌هوک پس از ارسال (مهاجرت ۰۰۲)
        metadata: داده‌های اضافی (JSON)

    Relationships:
        creator: کاربر سازنده فرم
        fields_models: فیلدهای فرم (جدول form_fields)
        responses: پاسخ‌های فرم
        submission_logs: لاگ‌های ارسال فرم
    """

    __tablename__ = "forms"

    # ----------------------------------------------
    # ستون‌های اصلی
    # ----------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # نوع و ساختار
    form_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fields: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=False)  # لیست فیلدها (ساختار قدیمی)

    # تنظیمات
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true", index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    requires_login: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_multistep: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    steps: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # متن‌ها
    submit_button_text: Mapped[str] = mapped_column(String(50), nullable=False, server_default="✅ ارسال")
    success_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    redirect_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # اطلاعات ایجاد و انتشار
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # محدودیت‌ها
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    max_submissions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    submission_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # ----------------------------------------------
    # فیلدهای اضافه‌شده در مهاجرت ۰۰۲
    # ----------------------------------------------
    submission_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    save_progress: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    notification_emails: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # داده‌های اضافی
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ----------------------------------------------
    # روابط (Relationships)
    # ----------------------------------------------
    # کاربر سازنده
    creator: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[created_by],
        back_populates="forms_created",
        lazy="selectin",
    )

    # فیلدهای فرم (جدول form_fields)
    fields_models: Mapped[List["FormFieldModel"]] = relationship(
        "FormFieldModel",
        back_populates="form",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # پاسخ‌های فرم
    responses: Mapped[List["FormResponseModel"]] = relationship(
        "FormResponseModel",
        back_populates="form",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # لاگ‌های ارسال فرم
    submission_logs: Mapped[List["FormSubmissionLogModel"]] = relationship(
        "FormSubmissionLogModel",
        back_populates="form",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ----------------------------------------------
    # ایندکس‌های اضافی
    # ----------------------------------------------
    __table_args__ = (
        Index("ix_forms_title", "title"),
        Index("ix_forms_form_type", "form_type"),
        Index("ix_forms_is_active", "is_active"),
        Index("ix_forms_created_by", "created_by"),
    )

    # ----------------------------------------------
    # متدهای تبدیل به/از دامنه
    # ----------------------------------------------
    def to_domain(self) -> Form:
        """
        تبدیل مدل SQLAlchemy به موجودیت دامنه Form.

        Returns:
            Form: موجودیت دامنه.
        """
        from my_bot.infrastructure.database.models.form_field_model import FormFieldModel

        # تبدیل فیلدها
        fields = []
        if self.fields_models:
            for field_model in self.fields_models:
                fields.append(field_model.to_domain())
        elif self.fields:
            # اگر از ساختار JSON قدیمی استفاده می‌شود
            for field_data in self.fields:
                fields.append(FormField.from_dict(field_data))

        return Form(
            id=self.id,
            title=self.title,
            description=self.description,
            form_type=FormType(self.form_type) if self.form_type else FormType.CUSTOM,
            fields=fields,
            is_active=self.is_active,
            is_public=self.is_public,
            requires_login=self.requires_login,
            is_multistep=self.is_multistep,
            steps=self.steps,
            submit_button_text=self.submit_button_text,
            success_message=self.success_message or self.submission_message,
            redirect_url=self.redirect_url,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
            published_at=self.published_at,
            expires_at=self.expires_at,
            max_submissions=self.max_submissions,
            submission_count=self.submission_count,
            metadata=self.metadata or {},
        )

    @classmethod
    def from_domain(cls, form: Form) -> "FormModel":
        """
        ساخت مدل SQLAlchemy از موجودیت دامنه Form.

        Args:
            form: موجودیت دامنه.

        Returns:
            FormModel: مدل SQLAlchemy.
        """
        from my_bot.infrastructure.database.models.form_field_model import FormFieldModel

        # تبدیل فیلدها به مدل‌های جداگانه (در صورت وجود)
        fields_models = []
        if form.fields:
            for field in form.fields:
                fields_models.append(FormFieldModel.from_domain(field))

        # همچنین fields را به‌صورت JSON برای سازگاری با نسخه‌های قدیمی ذخیره می‌کنیم
        fields_json = [field.to_dict() for field in form.fields] if form.fields else []

        return cls(
            id=form.id,
            title=form.title,
            description=form.description,
            form_type=form.form_type.value if form.form_type else FormType.CUSTOM.value,
            fields=fields_json,
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
            submission_message=form.success_message,  # فیلد جدید
            is_editable=False,  # مقدار پیش‌فرض
            save_progress=False,  # مقدار پیش‌فرض
            notification_emails=None,
            webhook_url=None,
            metadata=form.metadata,
            fields_models=fields_models,
        )

    def __repr__(self) -> str:
        """نمایش رشته‌ای مدل."""
        return f"<FormModel(id={self.id}, title={self.title}, type={self.form_type}, is_active={self.is_active})>"