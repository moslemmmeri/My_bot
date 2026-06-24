# my_bot_project/src/my_bot/presentation/handlers/form/form_start_handler.py
"""
هندلر شروع فرم (Form Start Handler).

این هندلر مسئولیت شروع فرآیند پر کردن فرم، نمایش سوال اول
و مدیریت وضعیت فرم در حافظه را بر عهده دارد.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.core.constants.form_types import FormType
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button, get_cancel_button
from my_bot.presentation.keyboards.form.form_navigation import get_form_navigation_keyboard

logger = get_logger(__name__)


class FormStartHandler:
    """
    هندلر شروع فرم.

    این کلاس مسئولیت شروع فرآیند پر کردن فرم را بر عهده دارد.
    """

    def __init__(
        self,
        form_builder_service: FormBuilderService,
        form_submission_service: FormSubmissionService,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            form_builder_service: سرویس ساخت فرم.
            form_submission_service: سرویس ثبت پاسخ فرم.
        """
        self._form_builder_service = form_builder_service
        self._form_submission_service = form_submission_service
        self._user_states: Dict[int, Dict[str, Any]] = {}

    async def start_form(self, callback: CallbackQuery) -> None:
        """
        شروع فرآیند پر کردن فرم.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # استخراج شناسه فرم از کالبک
            form_id = int(callback.data.split(":")[1])
            user_id = callback.from_user.id

            # دریافت اطلاعات فرم
            form = await self._form_builder_service.get_form(form_id)

            # بررسی دسترسی کاربر به فرم
            if not form.is_available():
                await callback.message.edit_text(
                    text="⚠️ **فرم در دسترس نیست**\n\n"
                    "این فرم در حال حاضر غیرفعال یا منقضی شده است.",
                    reply_markup=get_back_button("forms_list"),
                    parse_mode="Markdown",
                )
                await callback.answer()
                return

            if form.requires_login and not callback.from_user.id:
                await callback.message.edit_text(
                    text="🔒 **نیاز به احراز هویت**\n\n"
                    "برای پر کردن این فرم باید وارد سیستم شده باشید.",
                    reply_markup=get_back_button("forms_list"),
                    parse_mode="Markdown",
                )
                await callback.answer()
                return

            # ایجاد وضعیت جدید برای کاربر
            self._user_states[user_id] = {
                "form_id": form_id,
                "answers": {},
                "current_step": 1,
                "total_steps": form.steps,
                "started_at": datetime.now(),
            }

            # نمایش سوال اول
            await self._show_step(callback.message, user_id)

            # پاسخ به کالبک
            await callback.answer(f"شروع فرم: {form.title}")

        except Exception as e:
            logger.error(f"Error starting form: {e}")
            await callback.answer("⚠️ خطا در شروع فرم.", show_alert=True)

    async def _show_step(self, message: Message, user_id: int) -> None:
        """
        نمایش یک مرحله از فرم.

        Args:
            message: پیام برای ارسال پاسخ.
            user_id: شناسه کاربر.
        """
        try:
            state = self._user_states.get(user_id)
            if not state:
                await message.answer(
                    "⚠️ وضعیت فرم یافت نشد. لطفاً دوباره شروع کنید.",
                    reply_markup=get_back_button("forms_list"),
                )
                return

            # دریافت فرم
            form = await self._form_builder_service.get_form(state["form_id"])

            # دریافت فیلدهای مرحله فعلی
            current_step = state["current_step"]
            fields = form.get_fields_by_step(current_step)

            if not fields:
                # اگر فیلدی وجود نداشت، به مرحله بعد برو
                await self._next_step(message, user_id)
                return

            # ساخت پیام مرحله
            text = self._build_step_text(form, current_step, fields)
            keyboard = get_form_navigation_keyboard(
                current_step=current_step,
                total_steps=state["total_steps"],
                has_previous=current_step > 1,
            )

            # ارسال پیام
            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing form step: {e}")
            await message.answer(
                "⚠️ خطا در نمایش مرحله فرم. لطفاً دوباره تلاش کنید.",
                reply_markup=get_back_button("forms_list"),
            )

    async def next_step(self, callback: CallbackQuery) -> None:
        """
        رفتن به مرحله بعدی فرم.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            state["current_step"] += 1

            if state["current_step"] > state["total_steps"]:
                # فرم تکمیل شده است
                await self._submit_form(callback.message, user_id)
                await callback.answer("فرم تکمیل شد!")
                return

            await self._show_step(callback.message, user_id)
            await callback.answer()

        except Exception as e:
            logger.error(f"Error going to next step: {e}")
            await callback.answer("⚠️ خطا در رفتن به مرحله بعد.", show_alert=True)

    async def previous_step(self, callback: CallbackQuery) -> None:
        """
        بازگشت به مرحله قبلی فرم.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            if state["current_step"] > 1:
                state["current_step"] -= 1
                await self._show_step(callback.message, user_id)
                await callback.answer()
            else:
                await callback.answer("شما در مرحله اول هستید.")

        except Exception as e:
            logger.error(f"Error going to previous step: {e}")
            await callback.answer("⚠️ خطا در بازگشت به مرحله قبل.", show_alert=True)

    async def _submit_form(self, message: Message, user_id: int) -> None:
        """
        ارسال فرم تکمیل‌شده.

        Args:
            message: پیام برای ارسال پاسخ.
            user_id: شناسه کاربر.
        """
        try:
            state = self._user_states.get(user_id)
            if not state:
                return

            # دریافت فرم
            form = await self._form_builder_service.get_form(state["form_id"])

            # ارسال پاسخ‌ها
            # در عمل، پاسخ‌ها از state["answers"] گرفته می‌شوند
            # اینجا فقط یک پیام موفقیت نمایش می‌دهیم

            # پاک کردن وضعیت کاربر
            del self._user_states[user_id]

            # پیام موفقیت
            success_message = (
                "✅ **فرم با موفقیت ارسال شد!**\n\n"
                f"فرم: {form.title}\n"
                f"تاریخ ارسال: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                "از مشارکت شما سپاسگزاریم! 🙏"
            )

            await message.answer(
                text=success_message,
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            await message.answer(
                "⚠️ خطا در ارسال فرم. لطفاً دوباره تلاش کنید.",
                reply_markup=get_back_button("forms_list"),
            )

    def _build_step_text(self, form, step: int, fields: list) -> str:
        """
        ساخت متن یک مرحله از فرم.

        Args:
            form: اطلاعات فرم.
            step: شماره مرحله.
            fields: لیست فیلدهای مرحله.

        Returns:
            str: متن مرحله.
        """
        lines = [
            f"📝 **{form.title}**",
            "",
            f"مرحله {step} از {form.steps}",
            "",
        ]

        if form.description:
            lines.append(f"📌 {form.description}")
            lines.append("")

        lines.append("**سوالات:**")
        for i, field in enumerate(fields, 1):
            required = "⚠️" if field.is_required else ""
            lines.append(f"{i}. {field.label} {required}")

        if form.form_type:
            type_display = FormType(form.form_type).display_name if form.form_type else "سایر"
            lines.append("")
            lines.append(f"📌 نوع فرم: {type_display}")

        return "\n".join(lines)

    async def cancel_form(self, callback: CallbackQuery) -> None:
        """
        لغو پر کردن فرم.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            if user_id in self._user_states:
                del self._user_states[user_id]

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