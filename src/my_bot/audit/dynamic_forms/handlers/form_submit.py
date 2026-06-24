# my_bot_project/src/my_bot/dynamic_forms/handlers/form_submit.py
"""
هندلر ارسال فرم پویا (Dynamic Form Submit Handler).

این هندلر مسئولیت ارسال نهایی فرم تکمیل‌شده، اعتبارسنجی نهایی،
ثبت پاسخ‌ها در دیتابیس و نمایش پیام موفقیت یا خطا به کاربر را بر عهده دارد.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.not_found_errors import FormNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError, MultipleValidationErrors
from my_bot.core.exceptions.form_errors import (
    FormValidationError,
    FormSubmissionError,
    FormDuplicateError,
    FormExpiredError,
)
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.dynamic_forms.engine.form_state_manager import FormStateManager
from my_bot.dynamic_forms.engine.form_validator import FormValidator
from my_bot.dynamic_forms.engine.form_renderer import FormRenderer
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


class FormSubmitHandler:
    """
    هندلر ارسال فرم پویا.

    این کلاس مسئولیت ارسال نهایی فرم تکمیل‌شده، اعتبارسنجی نهایی
    و ثبت پاسخ‌ها در دیتابیس را بر عهده دارد.
    """

    def __init__(
        self,
        form_repository: FormRepository,
        form_submission_service: FormSubmissionService,
        state_manager: FormStateManager,
        validator: Optional[FormValidator] = None,
        renderer: Optional[FormRenderer] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            form_repository: ریپازیتوری فرم.
            form_submission_service: سرویس ثبت پاسخ فرم.
            state_manager: مدیریت وضعیت فرم.
            validator: اعتبارسنج فرم (در صورت None، نمونه جدید ایجاد می‌شود).
            renderer: رندر فرم (در صورت None، نمونه جدید ایجاد می‌شود).
        """
        self._form_repository = form_repository
        self._form_submission_service = form_submission_service
        self._state_manager = state_manager
        self._validator = validator or FormValidator()
        self._renderer = renderer or FormRenderer()

        logger.info("FormSubmitHandler initialized.")

    async def submit_form(self, callback: CallbackQuery) -> None:
        """
        ارسال نهایی فرم تکمیل‌شده.

        Args:
            callback: کالبک دریافتی از تلگرام (با داده‌ی `form:submit`).
        """
        try:
            user_id = callback.from_user.id

            # دریافت وضعیت کاربر
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await self._state_manager.clear_state(state.form_id, user_id)
                await callback.answer("⚠️ فرم مورد نظر یافت نشد.", show_alert=True)
                return

            # بررسی در دسترس بودن فرم
            if not form_definition.is_available():
                if form_definition.is_expired():
                    raise FormExpiredError(form_id=str(state.form_id))
                else:
                    raise FormValidationError(
                        form_id=str(state.form_id),
                        errors=[{"field": "form", "message": "فرم در دسترس نیست."}],
                    )

            # بررسی تکراری بودن ارسال
            if await self._has_user_submitted(state.form_id, user_id):
                raise FormDuplicateError(
                    form_id=str(state.form_id),
                    user_id=user_id,
                )

            # نمایش پیام در حال پردازش
            await callback.message.edit_text(
                text="⏳ **در حال ارسال فرم...**\n\nلطفاً منتظر بمانید.",
                parse_mode="Markdown",
            )

            # اعتبارسنجی نهایی تمام فیلدها
            errors = self._validator.validate(form_definition, state.answers)
            if errors:
                await self._show_validation_errors(callback.message, errors, form_definition)
                await callback.answer("⚠️ خطاهای اعتبارسنجی وجود دارد.", show_alert=True)
                return

            # ارسال فرم به سرویس ثبت
            try:
                # تبدیل وضعیت به داده‌های ارسال
                submit_data = {
                    "form_id": state.form_id,
                    "answers": state.answers,
                    "user_id": user_id,
                    "metadata": {
                        "started_at": state.started_at.isoformat() if state.started_at else None,
                        "completed_at": datetime.now().isoformat(),
                        "total_steps": state.total_steps,
                        "source": "telegram",
                        **state.metadata,
                    },
                }

                # ثبت پاسخ در دیتابیس
                response = await self._form_submission_service.submit_form(
                    form_id=state.form_id,
                    user_id=user_id,
                    answers=state.answers,
                    metadata=submit_data["metadata"],
                )

                # افزایش تعداد ارسال‌های فرم
                form_definition.increment_submission_count()

                # اجرای کالبک پس از ارسال (در صورت وجود)
                if form_definition.on_submit:
                    try:
                        await form_definition.on_submit(state)
                    except Exception as e:
                        logger.error(f"Error in form submit callback: {e}")

                # پاک کردن وضعیت کاربر
                await self._state_manager.clear_state(state.form_id, user_id)

                # نمایش پیام موفقیت
                await self._show_success_message(
                    callback.message,
                    form_definition,
                    response,
                )
                await callback.answer("✅ فرم با موفقیت ارسال شد!")

            except FormDuplicateError as e:
                logger.warning(f"Duplicate form submission: {e}")
                await self._show_error_message(
                    callback.message,
                    "⚠️ شما قبلاً این فرم را ارسال کرده‌اید.",
                    "امکان ارسال مجدد وجود ندارد.",
                )
                await callback.answer("⚠️ شما قبلاً این فرم را ارسال کرده‌اید.", show_alert=True)

            except FormValidationError as e:
                logger.warning(f"Validation error in form submission: {e}")
                await self._show_validation_errors(callback.message, e.errors, form_definition)
                await callback.answer("⚠️ خطاهای اعتبارسنجی وجود دارد.", show_alert=True)

            except FormSubmissionError as e:
                logger.error(f"Submission error: {e}")
                await self._show_error_message(
                    callback.message,
                    "⚠️ خطا در ارسال فرم",
                    str(e.message) if hasattr(e, "message") else "لطفاً دوباره تلاش کنید.",
                )
                await callback.answer("⚠️ خطا در ارسال فرم.", show_alert=True)

            except Exception as e:
                logger.error(f"Unexpected error in form submission: {e}")
                await self._show_error_message(
                    callback.message,
                    "⚠️ خطای غیرمنتظره",
                    "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                )
                await callback.answer("⚠️ خطا در ارسال فرم.", show_alert=True)

        except FormExpiredError as e:
            logger.warning(f"Form expired: {e}")
            await callback.message.edit_text(
                text="⚠️ **فرم منقضی شده است.**\n\n"
                     "زمان مجاز برای پر کردن این فرم به پایان رسیده است.",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ فرم منقضی شده است.", show_alert=True)

        except FormNotFoundError as e:
            logger.warning(f"Form not found: {e}")
            await callback.message.edit_text(
                text="⚠️ **فرم مورد نظر یافت نشد.**",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ فرم یافت نشد.", show_alert=True)

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.message.edit_text(
                text="⛔ **شما دسترسی به این فرم را ندارید.**",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("⛔ دسترسی غیرمجاز.", show_alert=True)

        except Exception as e:
            logger.error(f"Error submitting form: {e}", exc_info=True)
            await callback.message.edit_text(
                text="⚠️ **خطا در ارسال فرم**\n\n"
                     "متأسفانه خطایی در ارسال فرم رخ داد. لطفاً دوباره تلاش کنید.\n\n"
                     "در صورت تکرار خطا، با پشتیبانی تماس بگیرید.",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ خطا در ارسال فرم.", show_alert=True)

    async def confirm_submission(self, callback: CallbackQuery) -> None:
        """
        نمایش خلاصه پاسخ‌ها برای تأیید نهایی قبل از ارسال.

        Args:
            callback: کالبک دریافتی از تلگرام (با داده‌ی `form:confirm`).
        """
        try:
            user_id = callback.from_user.id

            # دریافت وضعیت کاربر
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم مورد نظر یافت نشد.", show_alert=True)
                return

            # ساخت خلاصه پاسخ‌ها
            summary_text = self._build_summary_text(form_definition, state.answers)

            # کیبورد تأیید
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton("✅ تأیید و ارسال", callback_data="form:submit"),
                    InlineKeyboardButton("✏️ ویرایش", callback_data="form:edit"),
                ],
                [
                    InlineKeyboardButton("⬅️ بازگشت به فرم", callback_data="form:previous"),
                ],
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="form:cancel"),
                ],
            ])

            await callback.message.edit_text(
                text=summary_text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer("لطفاً پاسخ‌ها را بررسی کنید.")

        except Exception as e:
            logger.error(f"Error showing confirm submission: {e}")
            await callback.answer("⚠️ خطا در نمایش تأییدیه.", show_alert=True)

    async def edit_form(self, callback: CallbackQuery) -> None:
        """
        بازگشت به فرم برای ویرایش پاسخ‌ها.

        Args:
            callback: کالبک دریافتی از تلگرام (با داده‌ی `form:edit`).
        """
        try:
            user_id = callback.from_user.id

            # دریافت وضعیت کاربر
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم مورد نظر یافت نشد.", show_alert=True)
                return

            # بازگشت به آخرین مرحله
            last_step = state.current_step
            if last_step > 1:
                # به مرحله قبلی برو
                await self._state_manager.update_state(
                    form_id=state.form_id,
                    user_id=user_id,
                    current_step=last_step - 1,
                )
                updated_state = await self._get_current_state(user_id)

                # رندر مرحله
                rendered = self._renderer.render_for_telegram(
                    form=form_definition,
                    current_step=updated_state.current_step,
                    answers=updated_state.answers,
                    include_metadata=True,
                )

                await callback.message.edit_text(
                    text=rendered["text"],
                    reply_markup=rendered["keyboard"],
                    parse_mode=rendered["parse_mode"],
                )
                await callback.answer("بازگشت به فرم برای ویرایش.")

            else:
                # اگر در مرحله اول هستیم، از ابتدا نمایش بده
                rendered = self._renderer.render_for_telegram(
                    form=form_definition,
                    current_step=1,
                    answers=state.answers,
                    include_metadata=True,
                )
                await callback.message.edit_text(
                    text=rendered["text"],
                    reply_markup=rendered["keyboard"],
                    parse_mode=rendered["parse_mode"],
                )
                await callback.answer("بازگشت به ابتدای فرم.")

        except Exception as e:
            logger.error(f"Error editing form: {e}")
            await callback.answer("⚠️ خطا در ویرایش فرم.", show_alert=True)

    async def _show_success_message(
        self,
        message: Message,
        form_definition: Any,
        response: Any,
    ) -> None:
        """
        نمایش پیام موفقیت ارسال فرم.

        Args:
            message: پیام برای ارسال پاسخ.
            form_definition: تعریف فرم.
            response: پاسخ ثبت‌شده.
        """
        success_message = form_definition.success_message or MessagePool.get_random_form_completed()

        text = f"✅ {success_message}\n\n"
        text += f"📋 **فرم**: {form_definition.title}\n"
        text += f"🆔 **شناسه پاسخ**: {response.id if response else 'نامشخص'}\n"
        text += f"📅 **تاریخ ارسال**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        text += "از مشارکت شما سپاسگزاریم! 🙏"

        if form_definition.redirect_url:
            text += f"\n\n🔗 [مشاهده ادامه]({form_definition.redirect_url})"

        await message.edit_text(
            text=text,
            reply_markup=get_back_button("forms_list"),
            parse_mode="Markdown",
        )

    async def _show_error_message(
        self,
        message: Message,
        title: str,
        description: str,
    ) -> None:
        """
        نمایش پیام خطا به کاربر.

        Args:
            message: پیام برای ارسال پاسخ.
            title: عنوان خطا.
            description: توضیحات خطا.
        """
        text = f"{title}\n\n{description}\n\n"
        text += "در صورت تکرار خطا، با پشتیبانی تماس بگیرید."

        await message.edit_text(
            text=text,
            reply_markup=get_back_button("forms_list"),
            parse_mode="Markdown",
        )

    async def _show_validation_errors(
        self,
        message: Message,
        errors: List[Dict[str, str]],
        form_definition: Any,
    ) -> None:
        """
        نمایش خطاهای اعتبارسنجی به کاربر.

        Args:
            message: پیام برای ارسال پاسخ.
            errors: لیست خطاها.
            form_definition: تعریف فرم.
        """
        error_text = "⚠️ **خطاهای اعتبارسنجی فرم:**\n\n"

        for error in errors:
            field_name = error.get("field", "نامشخص")
            field = form_definition.get_field(field_name)
            field_label = field.label if field else field_name
            error_text += f"• **{field_label}**: {error.get('message', 'خطای ناشناخته')}\n"

        error_text += "\nلطفاً خطاها را اصلاح کرده و دوباره تلاش کنید."

        # کیبورد بازگشت به فرم
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✏️ بازگشت به فرم", callback_data="form:edit")],
            [InlineKeyboardButton("❌ انصراف", callback_data="form:cancel")],
        ])

        await message.edit_text(
            text=error_text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    def _build_summary_text(self, form_definition: Any, answers: Dict[str, Any]) -> str:
        """
        ساخت خلاصه پاسخ‌ها برای تأیید نهایی.

        Args:
            form_definition: تعریف فرم.
            answers: پاسخ‌های کاربر.

        Returns:
            str: متن خلاصه.
        """
        lines = [
            "📝 **خلاصه پاسخ‌ها**",
            "",
            "لطفاً پاسخ‌های خود را بررسی کنید:",
            "",
        ]

        for field in form_definition.fields:
            value = answers.get(field.name)
            display_value = self._format_value_for_summary(value)

            lines.append(f"**{field.label}**: {display_value}")

        lines.extend([
            "",
            "⚠️ **توجه**: پس از تأیید، امکان ویرایش پاسخ‌ها وجود ندارد.",
            "",
            "آیا از ارسال فرم مطمئن هستید؟",
        ])

        return "\n".join(lines)

    def _format_value_for_summary(self, value: Any) -> str:
        """
        فرمت‌سازی مقدار برای نمایش در خلاصه.

        Args:
            value: مقدار.

        Returns:
            str: مقدار فرمت‌شده.
        """
        if value is None:
            return "❌ بدون پاسخ"
        if isinstance(value, bool):
            return "✅" if value else "❌"
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        if isinstance(value, dict):
            return str(value)
        return str(value)

    async def _get_current_state(self, user_id: int) -> Optional[Any]:
        """
        دریافت وضعیت فعلی کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[Any]: وضعیت فرم یا None.
        """
        states = await self._state_manager.get_all_user_states(user_id)
        if not states:
            return None
        return max(states, key=lambda s: s.last_updated_at)

    async def _get_form_definition(self, form_id: int) -> Optional[Any]:
        """
        دریافت تعریف فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            Optional[Any]: تعریف فرم یا None.
        """
        try:
            from my_bot.dynamic_forms.models.form_definition import FormDefinition
            from my_bot.dynamic_forms.models.form_field import DynamicFormField

            form_entity = await self._form_repository.get_by_id(form_id)
            if not form_entity:
                return None

            fields = []
            for field in form_entity.fields:
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
                status="active",
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
        except Exception as e:
            logger.error(f"Error getting form definition: {e}")
            return None

    async def _has_user_submitted(self, form_id: int, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر قبلاً این فرم را ارسال کرده است.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            bool: True اگر قبلاً ارسال کرده باشد.
        """
        try:
            # از سرویس ثبت پاسخ استفاده می‌کنیم
            return await self._form_submission_service.has_user_submitted(form_id, user_id)
        except Exception as e:
            logger.error(f"Error checking user submission: {e}")
            return False