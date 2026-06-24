# my_bot_project/src/my_bot/application/services/form/form_submission.py
"""
سرویس ثبت پاسخ فرم (Form Submission Service).

این سرویس مسئولیت ثبت، اعتبارسنجی و ذخیره‌سازی پاسخ‌های ارسال‌شده
برای فرم‌های پویا را بر عهده دارد.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from my_bot.application.dtos.form_dto import FormSubmitDTO, FormResponseDTO, FormAnswerDTO
from my_bot.core.exceptions.not_found_errors import FormNotFoundError, UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError, MultipleValidationErrors
from my_bot.core.exceptions.form_errors import FormSubmissionError, FormExpiredError, FormDuplicateError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.form import Form
from my_bot.domain.entities.form_response import FormResponse
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class FormSubmissionService:
    """
    سرویس ثبت پاسخ فرم.

    این کلاس مسئولیت ثبت، اعتبارسنجی و ذخیره‌سازی پاسخ‌های ارسال‌شده
    برای فرم‌های پویا را بر عهده دارد.
    """

    def __init__(
        self,
        form_repository: FormRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس ثبت پاسخ فرم.

        Args:
            form_repository: ریپازیتوری فرم.
            user_repository: ریپازیتوری کاربر.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._form_repository = form_repository
        self._user_repository = user_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._cache_ttl = 300  # 5 دقیقه

    async def submit_form(
        self,
        data: FormSubmitDTO,
        user_id: Optional[int] = None,
    ) -> FormResponseDTO:
        """
        ثبت پاسخ‌های ارسال‌شده برای یک فرم.

        Args:
            data: داده‌های پاسخ فرم (DTO).
            user_id: شناسه کاربر ارسال‌کننده (اختیاری).

        Returns:
            FormResponseDTO: اطلاعات پاسخ ثبت‌شده.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            FormExpiredError: اگر فرم منقضی شده باشد.
            FormDuplicateError: اگر کاربر قبلاً این فرم را ارسال کرده باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
            FormSubmissionError: در صورت بروز خطا در ثبت.
        """
        # دریافت فرم
        form = await self._get_form(data.form_id)

        # بررسی در دسترس بودن فرم
        if not form.is_available():
            if form.is_expired():
                raise FormExpiredError(
                    form_id=str(data.form_id),
                    expired_at=form.expires_at.isoformat() if form.expires_at else None,
                )
            raise FormSubmissionError(
                form_id=str(data.form_id),
                reason="فرم در دسترس نیست.",
            )

        # بررسی نیاز به لاگین
        if form.requires_login and user_id is None:
            raise ValidationError(
                message="برای پر کردن این فرم باید وارد شوید.",
                context={"form_id": data.form_id},
            )

        # بررسی وجود کاربر (در صورت نیاز)
        if user_id is not None:
            user = await self._user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id=user_id)

        # بررسی تکراری بودن ارسال
        if await self._has_user_submitted(data.form_id, user_id):
            raise FormDuplicateError(
                form_id=str(data.form_id),
                user_id=user_id or 0,
            )

        # اعتبارسنجی پاسخ‌ها
        validation_errors = form.validate_response(data.answers)
        if validation_errors:
            raise MultipleValidationErrors(
                errors=[ValidationError(
                    message=err["message"],
                    context={"field": err["field"]},
                ) for err in validation_errors]
            )

        # ایجاد موجودیت پاسخ
        response = FormResponse(
            form_id=data.form_id,
            user_id=user_id,
            answers=data.answers,
            is_valid=True,
            metadata=data.metadata,
        )

        # ذخیره پاسخ در دیتابیس
        try:
            saved_response = await self._form_repository.save_response(response)

            # افزایش تعداد ارسال‌های فرم
            await self._form_repository.increment_submission_count(data.form_id)

            # به‌روزرسانی کش (پاک کردن کش فرم)
            if self._cache:
                await self._cache.delete(f"form:{data.form_id}")

            logger.info(
                f"Form submitted: form_id={data.form_id}, "
                f"user_id={user_id}, response_id={saved_response.id}"
            )

            # انتشار رویداد ارسال فرم
            if self._message_publisher:
                await self._message_publisher.publish_event(
                    event_type="form.submitted",
                    event_data={
                        "form_id": data.form_id,
                        "response_id": saved_response.id,
                        "user_id": user_id,
                        "answers_count": len(data.answers),
                    },
                    source="FormSubmissionService",
                )

                # ارسال نوتیفیکیشن به ادمین (در صورت نیاز)
                if form.created_by:
                    await self._message_publisher.publish_notification(
                        user_id=form.created_by,
                        notification_type="form_submission",
                        data={
                            "form_id": data.form_id,
                            "form_title": form.title,
                            "user_id": user_id,
                            "response_id": saved_response.id,
                        },
                    )

            return FormResponseDTO.from_entity(saved_response)

        except Exception as e:
            logger.error(f"Error submitting form {data.form_id}: {e}")
            raise FormSubmissionError(
                form_id=str(data.form_id),
                user_id=user_id,
                reason=str(e),
            )

    async def get_response(
        self,
        response_id: int,
        user_id: Optional[int] = None,
    ) -> FormResponseDTO:
        """
        دریافت یک پاسخ فرم با شناسه.

        Args:
            response_id: شناسه پاسخ.
            user_id: شناسه کاربر (برای بررسی دسترسی، اختیاری).

        Returns:
            FormResponseDTO: اطلاعات پاسخ فرم.

        Raises:
            FormNotFoundError: اگر پاسخ وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        response = await self._form_repository.get_response_by_id(response_id)
        if not response:
            raise FormNotFoundError(form_id=str(response_id))

        # بررسی دسترسی (فقط ادمین یا خود کاربر می‌توانند پاسخ را ببینند)
        if user_id is not None and response.user_id != user_id:
            # می‌توان بررسی کرد که کاربر ادمین است یا خیر
            user = await self._user_repository.get_by_id(user_id)
            if not user or not user.is_admin():
                from my_bot.core.exceptions.permission_errors import PermissionDeniedError
                raise PermissionDeniedError(
                    message="شما مجاز به مشاهده این پاسخ نیستید.",
                    context={"response_id": response_id, "user_id": user_id},
                )

        return FormResponseDTO.from_entity(response)

    async def get_user_responses(
        self,
        user_id: int,
        form_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FormResponseDTO]:
        """
        دریافت پاسخ‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.
            form_id: فیلتر بر اساس فرم (اختیاری).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[FormResponseDTO]: لیست پاسخ‌های کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        responses = await self._form_repository.get_responses_by_user(
            user_id=user_id,
            form_id=form_id,
            skip=skip,
            limit=limit,
        )

        return [FormResponseDTO.from_entity(response) for response in responses]

    async def get_form_responses(
        self,
        form_id: int,
        skip: int = 0,
        limit: int = 100,
        include_invalid: bool = False,
    ) -> List[FormResponseDTO]:
        """
        دریافت تمام پاسخ‌های یک فرم.

        Args:
            form_id: شناسه فرم.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            include_invalid: شامل پاسخ‌های نامعتبر (پیش‌فرض False).

        Returns:
            List[FormResponseDTO]: لیست پاسخ‌های فرم.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        # بررسی وجود فرم
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=skip,
            limit=limit,
            include_invalid=include_invalid,
        )

        return [FormResponseDTO.from_entity(response) for response in responses]

    async def get_form_response_statistics(
        self,
        form_id: int,
    ) -> Dict[str, Any]:
        """
        دریافت آمار پاسخ‌های یک فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            Dict[str, Any]: آمار پاسخ‌ها.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # دریافت آمار از ریپازیتوری
        stats = await self._form_repository.get_response_statistics(form_id)

        return {
            "form_id": form_id,
            "form_title": form.title,
            "total_responses": stats.get("total_responses", 0),
            "valid_responses": stats.get("valid_responses", 0),
            "invalid_responses": stats.get("invalid_responses", 0),
            "unique_users": stats.get("unique_users", 0),
            "responses_today": stats.get("responses_today", 0),
            "responses_this_week": stats.get("responses_this_week", 0),
            "responses_this_month": stats.get("responses_this_month", 0),
            "last_response_at": stats.get("last_response_at"),
            "field_statistics": stats.get("field_statistics", {}),
        }

    async def get_form_export_data(
        self,
        form_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت داده‌های پاسخ‌های فرم برای خروجی (Export).

        Args:
            form_id: شناسه فرم.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            List[Dict[str, Any]]: لیست داده‌های پاسخ‌ها.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,  # حداکثر برای خروجی
            include_invalid=True,
        )

        # فیلتر بر اساس تاریخ (اگر مشخص شده باشد)
        if start_date or end_date:
            filtered = []
            for response in responses:
                if start_date and response.submitted_at < start_date:
                    continue
                if end_date and response.submitted_at > end_date:
                    continue
                filtered.append(response)
            responses = filtered

        # تبدیل به دیکشنری برای خروجی
        export_data = []
        for response in responses:
            row = {
                "response_id": response.id,
                "user_id": response.user_id,
                "submitted_at": response.submitted_at.isoformat() if response.submitted_at else None,
                "is_valid": response.is_valid,
            }
            # اضافه کردن پاسخ‌های فیلدها
            for field in form.fields:
                row[field.name] = response.answers.get(field.name)
            export_data.append(row)

        return export_data

    async def delete_response(
        self,
        response_id: int,
        deleted_by: int,
    ) -> bool:
        """
        حذف یک پاسخ فرم.

        Args:
            response_id: شناسه پاسخ.
            deleted_by: شناسه کاربر حذف‌کننده.

        Returns:
            bool: True در صورت حذف موفق.

        Raises:
            FormNotFoundError: اگر پاسخ وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        response = await self._form_repository.get_response_by_id(response_id)
        if not response:
            raise FormNotFoundError(form_id=str(response_id))

        # بررسی دسترسی (فقط ادمین یا خود کاربر)
        if deleted_by != response.user_id:
            user = await self._user_repository.get_by_id(deleted_by)
            if not user or not user.is_admin():
                from my_bot.core.exceptions.permission_errors import PermissionDeniedError
                raise PermissionDeniedError(
                    message="شما مجاز به حذف این پاسخ نیستید.",
                    context={"response_id": response_id, "deleted_by": deleted_by},
                )

        # حذف پاسخ
        result = await self._form_repository.delete_response(response_id)

        # کاهش تعداد ارسال‌های فرم (در صورت موفق)
        if result:
            form = await self._form_repository.get_by_id(response.form_id)
            if form:
                form.submission_count = max(0, form.submission_count - 1)
                await self._form_repository.save(form)

        logger.info(f"Response deleted: id={response_id}, by={deleted_by}")
        return result

    async def _has_user_submitted(
        self,
        form_id: int,
        user_id: Optional[int],
    ) -> bool:
        """
        بررسی اینکه آیا کاربر قبلاً این فرم را ارسال کرده است.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            bool: True اگر کاربر قبلاً ارسال کرده باشد.
        """
        if user_id is None:
            return False

        # از ریپازیتوری بررسی می‌کنیم
        return await self._form_repository.has_user_submitted(form_id, user_id)

    async def _get_form(self, form_id: int) -> Form:
        """
        دریافت فرم از دیتابیس یا کش.

        Args:
            form_id: شناسه فرم.

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
                    return Form.from_dict(cached)
                except Exception:
                    # اگر داده‌های کش نامعتبر بود، از دیتابیس می‌خوانیم
                    pass

        # دریافت از دیتابیس
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"form:{form_id}",
                form.to_dict(),
                ttl=self._cache_ttl,
            )

        return form