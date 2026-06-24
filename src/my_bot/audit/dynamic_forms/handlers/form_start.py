# my_bot_project/src/my_bot/dynamic_forms/handlers/form_start.py
"""
هندلر شروع فرم پویا (Dynamic Form Start Handler).

این هندلر مسئولیت شروع فرآیند پر کردن یک فرم پویا،
بررسی دسترسی کاربر، مقداردهی اولیه وضعیت و نمایش اولین مرحله را بر عهده دارد.
"""

from typing import Optional, Dict, Any

from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.not_found_errors import FormNotFoundError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.form_errors import FormExpiredError, FormInactiveError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.dynamic_forms.engine.form_state_manager import FormStateManager
from my_bot.dynamic_forms.engine.form_renderer import FormRenderer
from my_bot.dynamic_forms.engine.form_validator import FormValidator
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


class FormStartHandler:
    """
    هندلر شروع فرم پویا.

    این کلاس مسئولیت شروع فرآیند پر کردن یک فرم پویا را بر عهده دارد.
    """

    def __init__(
        self,
        form_repository: FormRepository,
        state_manager: FormStateManager,
        renderer: Optional[FormRenderer] = None,
        validator: Optional[FormValidator] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            form_repository: ریپازیتوری فرم برای دریافت تعریف فرم.
            state_manager: مدیریت وضعیت فرم.
            renderer: رندر فرم (در صورت None، نمونه جدید ایجاد می‌شود).
            validator: اعتبارسنج فرم (در صورت None، نمونه جدید ایجاد می‌شود).
        """
        self._form_repository = form_repository
        self._state_manager = state_manager
        self._renderer = renderer or FormRenderer()
        self._validator = validator or FormValidator()

        logger.info("FormStartHandler initialized.")

    async def start_form(self, callback: CallbackQuery) -> None:
        """
        شروع فرآیند پر کردن فرم.

        این متد از کالبک شناسه فرم را استخراج کرده، فرم را دریافت،
        دسترسی کاربر را بررسی، وضعیت را ایجاد و مرحله اول را نمایش می‌دهد.

        Args:
            callback: کالبک دریافتی از تلگرام (با داده‌ی فرمت `form:start:{form_id}`).
        """
        try:
            # استخراج شناسه فرم از کالبک
            form_id = self._extract_form_id(callback.data)
            user_id = callback.from_user.id

            logger.info(f"User {user_id} starting form {form_id}")

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم مورد نظر یافت نشد.", show_alert=True)
                return

            # بررسی در دسترس بودن فرم
            if not form_definition.is_available():
                if form_definition.is_expired():
                    raise FormExpiredError(form_id=str(form_id))
                else:
                    raise FormInactiveError(form_id=str(form_id))

            # بررسی نیاز به لاگین و دسترسی
            if not form_definition.can_submit(
                user_id=user_id,
                user_role=await self._get_user_role(user_id)
            ):
                raise PermissionDeniedError(
                    message="شما دسترسی به این فرم را ندارید.",
                    context={"form_id": form_id, "user_id": user_id},
                )

            # بررسی تکراری بودن ارسال (اگر قبلاً ارسال شده باشد)
            if await self._has_user_submitted(form_id, user_id):
                await callback.message.edit_text(
                    text="⚠️ **شما قبلاً این فرم را ارسال کرده‌اید.**\n\n"
                         "امکان ارسال مجدد وجود ندارد.",
                    reply_markup=get_back_button("forms_list"),
                    parse_mode="Markdown",
                )
                await callback.answer("شما قبلاً این فرم را ارسال کرده‌اید.", show_alert=True)
                return

            # ایجاد وضعیت جدید برای کاربر
            state = await self._state_manager.create_state(
                form_id=form_id,
                user_id=user_id,
                total_steps=form_definition.get_step_count(),
                metadata={
                    "username": callback.from_user.username,
                    "first_name": callback.from_user.first_name,
                    "last_name": callback.from_user.last_name,
                },
            )

            # نمایش مرحله اول
            await self._show_step(callback.message, state, form_definition)

            await callback.answer(f"شروع فرم: {form_definition.title}")

        except FormNotFoundError as e:
            logger.warning(f"Form not found: {e}")
            await callback.answer("⚠️ فرم مورد نظر یافت نشد.", show_alert=True)

        except FormExpiredError as e:
            logger.warning(f"Form expired: {e}")
            await callback.answer("⚠️ فرم منقضی شده است.", show_alert=True)

        except FormInactiveError as e:
            logger.warning(f"Form inactive: {e}")
            await callback.answer("⚠️ فرم غیرفعال است.", show_alert=True)

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این فرم را ندارید.", show_alert=True)

        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            await callback.answer(f"⚠️ {e.message}", show_alert=True)

        except Exception as e:
            logger.error(f"Error starting form: {e}", exc_info=True)
            await callback.message.edit_text(
                text="⚠️ **خطا در شروع فرم**\n\n"
                     "متأسفانه خطایی در شروع فرم رخ داد. لطفاً دوباره تلاش کنید.\n\n"
                     "در صورت تکرار خطا، با پشتیبانی تماس بگیرید.",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ خطا در شروع فرم.", show_alert=True)

    async def _show_step(
        self,
        message: Message,
        state: Any,
        form_definition: Any,
    ) -> None:
        """
        نمایش یک مرحله از فرم به کاربر.

        Args:
            message: پیام برای ارسال پاسخ.
            state: وضعیت فرم.
            form_definition: تعریف فرم.
        """
        try:
            # رندر مرحله
            rendered = self._renderer.render_for_telegram(
                form=form_definition,
                current_step=state.current_step,
                answers=state.answers,
                include_metadata=True,
            )

            # ارسال پیام
            await message.answer(
                text=rendered["text"],
                reply_markup=rendered["keyboard"],
                parse_mode=rendered["parse_mode"],
            )

        except Exception as e:
            logger.error(f"Error showing step: {e}")
            await message.answer(
                "⚠️ خطا در نمایش مرحله فرم. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
            )

    def _extract_form_id(self, callback_data: str) -> int:
        """
        استخراج شناسه فرم از داده‌ی کالبک.

        Args:
            callback_data: رشته کالبک (فرمت: `form:start:{form_id}`).

        Returns:
            int: شناسه فرم.

        Raises:
            ValidationError: اگر فرمت کالبک نامعتبر باشد.
        """
        parts = callback_data.split(":")
        if len(parts) != 3 or parts[0] != "form" or parts[1] != "start":
            raise ValidationError(
                message="فرمت کالبک نامعتبر است.",
                context={"callback_data": callback_data},
            )

        try:
            return int(parts[2])
        except ValueError:
            raise ValidationError(
                message="شناسه فرم نامعتبر است.",
                context={"callback_data": callback_data},
            )

    async def _get_form_definition(self, form_id: int) -> Optional[Any]:
        """
        دریافت تعریف فرم از ریپازیتوری.

        Args:
            form_id: شناسه فرم.

        Returns:
            Optional[Any]: تعریف فرم یا None در صورت عدم وجود.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        # دریافت فرم از ریپازیتوری (موجودیت دامنه)
        form_entity = await self._form_repository.get_by_id(form_id)
        if not form_entity:
            return None

        # تبدیل به تعریف فرم پویا (اگر لازم باشد)
        # در اینجا فرض می‌کنیم که فرم موجودیت دارای متد to_definition است
        # یا اینکه مستقیماً از FormDefinition استفاده می‌کنیم.
        # برای سادگی، از یک تابع کمکی استفاده می‌کنیم که موجودیت را به تعریف تبدیل کند.
        from my_bot.dynamic_forms.models.form_definition import FormDefinition
        from my_bot.dynamic_forms.models.form_field import DynamicFormField

        # ساخت تعریف از موجودیت
        fields = []
        for field in form_entity.fields:
            # تبدیل فیلدهای موجودیت به DynamicFormField
            fields.append(DynamicFormField(
                name=field.name,
                label=field.label,
                field_type=field.field_type,
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
                is_hidden=False,
                is_readonly=False,
                metadata=field.metadata,
            ))

        return FormDefinition(
            id=form_entity.id,
            title=form_entity.title,
            description=form_entity.description,
            fields=fields,
            status=form_entity.status if hasattr(form_entity, "status") else "active",
            render_mode="stepped" if form_entity.is_multistep else "scrollable",
            steps=form_entity.steps,
            submit_button_text=form_entity.submit_button_text,
            success_message=form_entity.success_message,
            redirect_url=form_entity.redirect_url,
            is_public=form_entity.is_public,
            requires_login=form_entity.requires_login,
            max_submissions=form_entity.max_submissions,
            submission_count=form_entity.submission_count,
            created_by=form_entity.created_by,
            created_at=form_entity.created_at,
            updated_at=form_entity.updated_at,
            published_at=form_entity.published_at,
            expires_at=form_entity.expires_at,
            metadata=form_entity.metadata,
        )

    async def _get_user_role(self, user_id: int) -> Optional[str]:
        """
        دریافت نقش کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[str]: نقش کاربر یا None در صورت عدم وجود.
        """
        # در عمل، باید از سرویس کاربر استفاده کرد
        # اینجا یک پیاده‌سازی ساده برای نمونه
        # فرض می‌کنیم کاربر با شناسه ۱ ادمین است
        if user_id == 1:
            return "admin"
        return "user"

    async def _has_user_submitted(self, form_id: int, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر قبلاً این فرم را ارسال کرده است.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            bool: True اگر قبلاً ارسال کرده باشد.
        """
        # در عمل، از ریپازیتوری پاسخ‌ها استفاده می‌کنیم
        # اینجا یک پیاده‌سازی ساده که همیشه False برمی‌گرداند
        # (برای نمونه)
        return False

    async def cancel_form(self, callback: CallbackQuery) -> None:
        """
        لغو پر کردن فرم و حذف وضعیت.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # پاک کردن وضعیت کاربر (برای تمام فرم‌ها)
            await self._state_manager.clear_all_user_states(user_id)

            await callback.message.edit_text(
                text="❌ **پر کردن فرم لغو شد.**\n\n"
                     "به منوی اصلی بازگشتید.",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("پر کردن فرم لغو شد.")

        except Exception as e:
            logger.error(f"Error cancelling form: {e}")
            await callback.answer("⚠️ خطا در لغو فرم.", show_alert=True)