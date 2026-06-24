# my_bot_project/src/my_bot/application/services/form/form_builder.py
"""
سرویس ساخت فرم (Form Builder Service).

این سرویس مسئولیت ایجاد، ویرایش، حذف و مدیریت فرم‌های پویا در سیستم را بر عهده دارد.
شامل عملیات‌های CRUD، انتشار، فعال/غیرفعال‌سازی و مدیریت فیلدهای فرم است.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.application.dtos.form_dto import (
    FormCreateDTO,
    FormUpdateDTO,
    FormResponseDTO,
    FormFieldDTO,
)
from my_bot.core.constants.form_types import FormType
from my_bot.core.exceptions.not_found_errors import FormNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError, MultipleValidationErrors
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.form import Form
from my_bot.domain.value_objects.form_field import FormField, FieldType
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class FormBuilderService:
    """
    سرویس ساخت و مدیریت فرم‌ها.

    این کلاس مسئولیت ایجاد، ویرایش، حذف و مدیریت فرم‌های پویا را بر عهده دارد.
    """

    def __init__(
        self,
        form_repository: FormRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس ساخت فرم.

        Args:
            form_repository: ریپازیتوری فرم.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت فرم‌ها (اختیاری).
        """
        self._form_repository = form_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._cache_ttl = 300  # 5 دقیقه

    async def create_form(
        self,
        data: FormCreateDTO,
        created_by: int,
    ) -> FormResponseDTO:
        """
        ایجاد یک فرم جدید در سیستم.

        Args:
            data: اطلاعات فرم (DTO).
            created_by: شناسه کاربر سازنده (ادمین).

        Returns:
            FormResponseDTO: اطلاعات فرم ایجادشده.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PermissionDeniedError: اگر کاربر مجاز به ساخت فرم نباشد.
        """
        # اعتبارسنجی عنوان یکتا
        if await self._form_repository.exists_by_title(data.title):
            raise ValidationError(
                message=f"فرمی با عنوان '{data.title}' از قبل وجود دارد.",
                context={"title": data.title},
            )

        # اعتبارسنجی نوع فرم
        form_type = FormType.from_string(data.form_type)
        if not form_type:
            raise ValidationError(
                message=f"نوع فرم '{data.form_type}' نامعتبر است.",
                context={"form_type": data.form_type},
            )

        # ایجاد فیلدها
        fields = []
        field_errors = []
        for idx, field_data in enumerate(data.fields):
            try:
                field = self._create_field_from_dto(field_data, idx)
                fields.append(field)
            except ValidationError as e:
                field_errors.append({
                    "index": idx,
                    "field": field_data.get("name", f"field_{idx}"),
                    "error": str(e),
                })

        if field_errors:
            raise MultipleValidationErrors(
                errors=[ValidationError(
                    message=f"خطا در فیلد {fe['field']}: {fe['error']}",
                    context={"field_index": fe["index"]},
                ) for fe in field_errors]
            )

        # ایجاد موجودیت فرم
        form = Form(
            title=data.title,
            form_type=form_type,
            fields=fields,
            created_by=created_by,
            description=data.description,
            is_active=data.is_active,
            is_public=data.is_public,
            requires_login=data.requires_login,
            is_multistep=data.is_multistep,
            steps=data.steps if data.is_multistep else 1,
            submit_button_text=data.submit_button_text or "✅ ارسال",
            success_message=data.success_message,
            redirect_url=data.redirect_url,
            expires_at=data.expires_at,
            max_submissions=data.max_submissions,
            metadata=data.metadata,
        )

        # ذخیره در دیتابیس
        saved_form = await self._form_repository.save(form)

        # انتشار رویداد ایجاد فرم
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="form.created",
                event_data={
                    "form_id": saved_form.id,
                    "title": saved_form.title,
                    "form_type": saved_form.form_type.value,
                    "created_by": created_by,
                },
                source="FormBuilderService",
            )

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Form created: id={saved_form.id}, title={saved_form.title}, by={created_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def update_form(
        self,
        form_id: int,
        data: FormUpdateDTO,
        updated_by: int,
    ) -> FormResponseDTO:
        """
        به‌روزرسانی یک فرم موجود.

        Args:
            form_id: شناسه فرم.
            data: اطلاعات جدید فرم.
            updated_by: شناسه کاربر به‌روزرسانی‌کننده.

        Returns:
            FormResponseDTO: اطلاعات فرم به‌روزرسانی‌شده.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PermissionDeniedError: اگر کاربر مجاز به ویرایش فرم نباشد.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی (فقط سازنده یا ادمین)
        if form.created_by != updated_by:
            # می‌توان بررسی کرد که کاربر ادمین است یا خیر
            raise PermissionDeniedError(
                message="شما مجاز به ویرایش این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "updated_by": updated_by},
            )

        # به‌روزرسانی فیلدها
        updated = False

        if data.title is not None:
            if data.title != form.title:
                if await self._form_repository.exists_by_title(data.title, exclude_id=form_id):
                    raise ValidationError(
                        message=f"فرمی با عنوان '{data.title}' از قبل وجود دارد.",
                        context={"title": data.title},
                    )
                form.title = data.title
                updated = True

        if data.description is not None:
            form.description = data.description
            updated = True

        if data.form_type is not None:
            form_type = FormType.from_string(data.form_type)
            if not form_type:
                raise ValidationError(
                    message=f"نوع فرم '{data.form_type}' نامعتبر است.",
                    context={"form_type": data.form_type},
                )
            form.form_type = form_type
            updated = True

        if data.is_active is not None:
            form.is_active = data.is_active
            updated = True

        if data.is_public is not None:
            form.is_public = data.is_public
            updated = True

        if data.requires_login is not None:
            form.requires_login = data.requires_login
            updated = True

        if data.is_multistep is not None:
            form.is_multistep = data.is_multistep
            form.steps = data.steps if data.is_multistep else 1
            updated = True

        if data.submit_button_text is not None:
            form.submit_button_text = data.submit_button_text
            updated = True

        if data.success_message is not None:
            form.success_message = data.success_message
            updated = True

        if data.redirect_url is not None:
            form.redirect_url = data.redirect_url
            updated = True

        if data.expires_at is not None:
            form.expires_at = data.expires_at
            updated = True

        if data.max_submissions is not None:
            form.max_submissions = data.max_submissions
            updated = True

        if data.fields is not None:
            # به‌روزرسانی فیلدها
            new_fields = []
            field_errors = []
            for idx, field_data in enumerate(data.fields):
                try:
                    field = self._create_field_from_dto(field_data, idx)
                    new_fields.append(field)
                except ValidationError as e:
                    field_errors.append({
                        "index": idx,
                        "field": field_data.get("name", f"field_{idx}"),
                        "error": str(e),
                    })

            if field_errors:
                raise MultipleValidationErrors(
                    errors=[ValidationError(
                        message=f"خطا در فیلد {fe['field']}: {fe['error']}",
                        context={"field_index": fe["index"]},
                    ) for fe in field_errors]
                )

            form.fields = new_fields
            updated = True

        if not updated:
            logger.debug(f"No changes to update for form {form_id}")
            return FormResponseDTO.from_entity(form)

        # ذخیره در دیتابیس
        form.updated_at = datetime.now()
        saved_form = await self._form_repository.save(form)

        # انتشار رویداد به‌روزرسانی فرم
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="form.updated",
                event_data={
                    "form_id": saved_form.id,
                    "title": saved_form.title,
                    "updated_by": updated_by,
                },
                source="FormBuilderService",
            )

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Form updated: id={form_id}, by={updated_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def delete_form(
        self,
        form_id: int,
        deleted_by: int,
    ) -> bool:
        """
        حذف یک فرم از سیستم.

        Args:
            form_id: شناسه فرم.
            deleted_by: شناسه کاربر حذف‌کننده.

        Returns:
            bool: True در صورت حذف موفق.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز به حذف فرم نباشد.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی
        if form.created_by != deleted_by:
            raise PermissionDeniedError(
                message="شما مجاز به حذف این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "deleted_by": deleted_by},
            )

        # حذف از دیتابیس
        result = await self._form_repository.delete(form_id)

        # حذف از کش
        if self._cache:
            await self._cache.delete(f"form:{form_id}")

        # انتشار رویداد حذف فرم
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="form.deleted",
                event_data={
                    "form_id": form_id,
                    "title": form.title,
                    "deleted_by": deleted_by,
                },
                source="FormBuilderService",
            )

        logger.info(f"Form deleted: id={form_id}, title={form.title}, by={deleted_by}")
        return result

    async def get_form(
        self,
        form_id: int,
        include_inactive: bool = False,
    ) -> FormResponseDTO:
        """
        دریافت اطلاعات یک فرم.

        Args:
            form_id: شناسه فرم.
            include_inactive: شامل فرم‌های غیرفعال (پیش‌فرض False).

        Returns:
            FormResponseDTO: اطلاعات فرم.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._get_form(form_id, include_inactive)
        return FormResponseDTO.from_entity(form)

    async def get_all_forms(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        form_type: Optional[str] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[FormResponseDTO]:
        """
        دریافت لیست فرم‌ها با فیلترهای اختیاری.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            is_active: فیلتر بر اساس فعال بودن (اختیاری).
            is_public: فیلتر بر اساس عمومی بودن (اختیاری).
            form_type: فیلتر بر اساس نوع فرم (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            List[FormResponseDTO]: لیست فرم‌ها.
        """
        # اگر نوع فرم مشخص شده، اعتبارسنجی
        if form_type:
            if not FormType.from_string(form_type):
                raise ValidationError(
                    message=f"نوع فرم '{form_type}' نامعتبر است.",
                    context={"form_type": form_type},
                )

        # دریافت فرم‌ها از ریپازیتوری
        forms = await self._form_repository.get_all(
            skip=skip,
            limit=limit,
            is_active=is_active,
            is_public=is_public,
            order_by=order_by,
            order_desc=order_desc,
        )

        # فیلتر بر اساس نوع فرم (اگر مشخص شده باشد)
        if form_type:
            forms = [f for f in forms if f.form_type.value == form_type]

        return [FormResponseDTO.from_entity(form) for form in forms]

    async def get_active_forms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FormResponseDTO]:
        """
        دریافت فرم‌های فعال (قابل ارسال).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[FormResponseDTO]: لیست فرم‌های فعال.
        """
        forms = await self._form_repository.get_active_forms(
            skip=skip,
            limit=limit,
        )
        return [FormResponseDTO.from_entity(form) for form in forms]

    async def get_public_forms(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FormResponseDTO]:
        """
        دریافت فرم‌های عمومی (قابل مشاهده برای همه).

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[FormResponseDTO]: لیست فرم‌های عمومی.
        """
        forms = await self._form_repository.get_public_forms(
            skip=skip,
            limit=limit,
        )
        return [FormResponseDTO.from_entity(form) for form in forms]

    async def get_forms_by_creator(
        self,
        created_by: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FormResponseDTO]:
        """
        دریافت فرم‌های ساخته‌شده توسط یک ادمین خاص.

        Args:
            created_by: شناسه کاربر سازنده.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[FormResponseDTO]: لیست فرم‌های ساخته‌شده.
        """
        forms = await self._form_repository.get_forms_by_creator(
            created_by=created_by,
            skip=skip,
            limit=limit,
        )
        return [FormResponseDTO.from_entity(form) for form in forms]

    async def publish_form(
        self,
        form_id: int,
        published_by: int,
    ) -> FormResponseDTO:
        """
        انتشار یک فرم (قابل دسترس برای کاربران).

        Args:
            form_id: شناسه فرم.
            published_by: شناسه کاربر انتشاردهنده.

        Returns:
            FormResponseDTO: اطلاعات فرم منتشرشده.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            ValidationError: اگر فرم غیرفعال باشد.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی
        if form.created_by != published_by:
            raise PermissionDeniedError(
                message="شما مجاز به انتشار این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "published_by": published_by},
            )

        # انتشار فرم
        form.publish()
        saved_form = await self._form_repository.save(form)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        # انتشار رویداد انتشار فرم
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="form.published",
                event_data={
                    "form_id": saved_form.id,
                    "title": saved_form.title,
                    "published_by": published_by,
                },
                source="FormBuilderService",
            )

        logger.info(f"Form published: id={form_id}, by={published_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def activate_form(
        self,
        form_id: int,
        activated_by: int,
    ) -> FormResponseDTO:
        """
        فعال‌سازی یک فرم.

        Args:
            form_id: شناسه فرم.
            activated_by: شناسه کاربر فعال‌کننده.

        Returns:
            FormResponseDTO: اطلاعات فرم فعال‌شده.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی
        if form.created_by != activated_by:
            raise PermissionDeniedError(
                message="شما مجاز به فعال‌سازی این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "activated_by": activated_by},
            )

        form.activate()
        saved_form = await self._form_repository.save(form)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Form activated: id={form_id}, by={activated_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def deactivate_form(
        self,
        form_id: int,
        deactivated_by: int,
        reason: Optional[str] = None,
    ) -> FormResponseDTO:
        """
        غیرفعال‌سازی یک فرم.

        Args:
            form_id: شناسه فرم.
            deactivated_by: شناسه کاربر غیرفعال‌کننده.
            reason: دلیل غیرفعال‌سازی (اختیاری).

        Returns:
            FormResponseDTO: اطلاعات فرم غیرفعال‌شده.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی
        if form.created_by != deactivated_by:
            raise PermissionDeniedError(
                message="شما مجاز به غیرفعال‌سازی این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "deactivated_by": deactivated_by},
            )

        form.deactivate(reason)
        saved_form = await self._form_repository.save(form)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Form deactivated: id={form_id}, by={deactivated_by}, reason={reason}")
        return FormResponseDTO.from_entity(saved_form)

    async def add_field(
        self,
        form_id: int,
        field_data: Dict[str, Any],
        added_by: int,
    ) -> FormResponseDTO:
        """
        افزودن یک فیلد جدید به فرم.

        Args:
            form_id: شناسه فرم.
            field_data: اطلاعات فیلد جدید.
            added_by: شناسه کاربر افزاینده.

        Returns:
            FormResponseDTO: اطلاعات فرم به‌روزرسانی‌شده.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی
        if form.created_by != added_by:
            raise PermissionDeniedError(
                message="شما مجاز به افزودن فیلد به این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "added_by": added_by},
            )

        # ایجاد فیلد
        field = self._create_field_from_dto(field_data, len(form.fields))

        # افزودن به فرم
        form.add_field(field)

        # ذخیره
        saved_form = await self._form_repository.save(form)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Field added to form {form_id}: {field.name}, by={added_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def remove_field(
        self,
        form_id: int,
        field_name: str,
        removed_by: int,
    ) -> FormResponseDTO:
        """
        حذف یک فیلد از فرم.

        Args:
            form_id: شناسه فرم.
            field_name: نام فیلد.
            removed_by: شناسه کاربر حذف‌کننده.

        Returns:
            FormResponseDTO: اطلاعات فرم به‌روزرسانی‌شده.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        form = await self._get_form(form_id)

        # بررسی دسترسی
        if form.created_by != removed_by:
            raise PermissionDeniedError(
                message="شما مجاز به حذف فیلد از این فرم نیستید.",
                context={"form_id": form_id, "created_by": form.created_by, "removed_by": removed_by},
            )

        # حذف فیلد
        if not form.remove_field(field_name):
            raise ValidationError(
                message=f"فیلد '{field_name}' در فرم یافت نشد.",
                context={"form_id": form_id, "field_name": field_name},
            )

        # ذخیره
        saved_form = await self._form_repository.save(form)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Field removed from form {form_id}: {field_name}, by={removed_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def duplicate_form(
        self,
        form_id: int,
        new_title: str,
        duplicated_by: int,
    ) -> FormResponseDTO:
        """
        کپی کردن یک فرم.

        Args:
            form_id: شناسه فرم اصلی.
            new_title: عنوان فرم جدید.
            duplicated_by: شناسه کاربر کپی‌کننده.

        Returns:
            FormResponseDTO: اطلاعات فرم کپی‌شده.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            ValidationError: اگر عنوان تکراری باشد.
        """
        form = await self._get_form(form_id)

        # بررسی عنوان
        if await self._form_repository.exists_by_title(new_title):
            raise ValidationError(
                message=f"فرمی با عنوان '{new_title}' از قبل وجود دارد.",
                context={"title": new_title},
            )

        # ایجاد فرم جدید از روی فرم موجود
        new_form = Form(
            title=new_title,
            form_type=form.form_type,
            fields=form.fields.copy(),
            created_by=duplicated_by,
            description=form.description,
            is_active=False,  # فرم کپی‌شده به‌صورت پیش‌فرض غیرفعال است
            is_public=form.is_public,
            requires_login=form.requires_login,
            is_multistep=form.is_multistep,
            steps=form.steps,
            submit_button_text=form.submit_button_text,
            success_message=form.success_message,
            redirect_url=form.redirect_url,
            expires_at=form.expires_at,
            max_submissions=form.max_submissions,
            metadata=form.metadata.copy(),
        )

        # ذخیره
        saved_form = await self._form_repository.save(new_form)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"form:{saved_form.id}",
                saved_form.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Form duplicated: from {form_id} to {saved_form.id}, by={duplicated_by}")
        return FormResponseDTO.from_entity(saved_form)

    async def search_forms(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[FormResponseDTO]:
        """
        جستجوی فرم‌ها با استفاده از متن (عنوان، توضیحات).

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[FormResponseDTO]: لیست فرم‌های مطابق با جستجو.
        """
        forms = await self._form_repository.search_forms(
            query=query,
            skip=skip,
            limit=limit,
        )
        return [FormResponseDTO.from_entity(form) for form in forms]

    async def get_form_statistics(self, form_id: int) -> Dict[str, Any]:
        """
        دریافت آمار یک فرم (تعداد ارسال، نرخ تکمیل، و ...).

        Args:
            form_id: شناسه فرم.

        Returns:
            Dict[str, Any]: آمار فرم.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._get_form(form_id)

        # تعداد ارسال از خود فرم
        submission_count = form.submission_count

        # می‌توان آمار بیشتری از ریپازیتوری دریافت کرد
        # مثلاً تعداد ارسال‌های امروز، این هفته، و ...

        return {
            "form_id": form_id,
            "title": form.title,
            "submission_count": submission_count,
            "max_submissions": form.max_submissions,
            "is_active": form.is_active,
            "is_public": form.is_public,
            "created_at": form.created_at.isoformat() if form.created_at else None,
            "expires_at": form.expires_at.isoformat() if form.expires_at else None,
        }

    async def _get_form(self, form_id: int, include_inactive: bool = False) -> Form:
        """
        دریافت فرم از دیتابیس یا کش.

        Args:
            form_id: شناسه فرم.
            include_inactive: شامل فرم‌های غیرفعال.

        Returns:
            Form: موجودیت فرم.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        # تلاش از کش
        if self._cache:
            cached = await self._cache.get(f"form:{form_id}")
            if cached:
                try:
                    form = Form.from_dict(cached)
                    # اگر فقط فرم‌های فعال را می‌خواهیم و فرم غیرفعال است
                    if not include_inactive and not form.is_active:
                        # از کش حذف می‌کنیم و از دیتابیس می‌خوانیم
                        await self._cache.delete(f"form:{form_id}")
                    else:
                        return form
                except Exception:
                    # اگر داده‌های کش نامعتبر بود، از دیتابیس می‌خوانیم
                    pass

        # دریافت از دیتابیس
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # اگر فرم غیرفعال است و include_inactive False است
        if not include_inactive and not form.is_active:
            raise FormNotFoundError(
                form_id=str(form_id),
                context={"is_active": form.is_active},
            )

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"form:{form_id}",
                form.to_dict(),
                ttl=self._cache_ttl,
            )

        return form

    def _create_field_from_dto(self, field_data: Dict[str, Any], order: int) -> FormField:
        """
        ایجاد فیلد فرم از داده‌های DTO.

        Args:
            field_data: داده‌های فیلد.
            order: ترتیب فیلد.

        Returns:
            FormField: فیلد فرم.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        # اعتبارسنجی نام
        name = field_data.get("name", "")
        if not name:
            raise ValidationError(
                message="نام فیلد نمی‌تواند خالی باشد.",
                context={"field_data": field_data},
            )

        # اعتبارسنجی برچسب
        label = field_data.get("label", "")
        if not label:
            raise ValidationError(
                message=f"برچسب فیلد '{name}' نمی‌تواند خالی باشد.",
                context={"field_name": name},
            )

        # اعتبارسنجی نوع
        field_type = field_data.get("type", FieldType.TEXT)
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
        if field_type not in valid_types:
            raise ValidationError(
                message=f"نوع فیلد '{field_type}' نامعتبر است.",
                context={"field_name": name, "field_type": field_type},
            )

        # برای فیلدهای انتخابی، اعتبارسنجی گزینه‌ها
        options = field_data.get("options", [])
        if field_type in [FieldType.SELECT, FieldType.MULTI_SELECT, FieldType.RADIO, FieldType.CHECKBOX]:
            if not options or len(options) < 2:
                raise ValidationError(
                    message=f"فیلد '{name}' از نوع انتخابی است و باید حداقل ۲ گزینه داشته باشد.",
                    context={"field_name": name, "field_type": field_type},
                )
            for opt in options:
                if "value" not in opt or "label" not in opt:
                    raise ValidationError(
                        message=f"گزینه‌های فیلد '{name}' باید شامل 'value' و 'label' باشند.",
                        context={"field_name": name, "option": opt},
                    )

        # ایجاد فیلد
        return FormField(
            name=name,
            label=label,
            field_type=field_type,
            is_required=field_data.get("is_required", False),
            placeholder=field_data.get("placeholder"),
            help_text=field_data.get("help_text"),
            default_value=field_data.get("default_value"),
            options=options,
            validation_rules=field_data.get("validation_rules", {}),
            order=field_data.get("order", order),
            group=field_data.get("group"),
            css_class=field_data.get("css_class"),
            width=field_data.get("width"),
            metadata=field_data.get("metadata", {}),
        )