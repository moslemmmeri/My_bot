# my_bot_project/src/my_bot/presentation/handlers/form/form_submit_handler.py
"""
هندلر ارسال فرم (Form Submit Handler).

این هندلر مسئولیت ارسال و ثبت نهایی فرم تکمیل‌شده،
اعتبارسنجی نهایی و نمایش پیام موفقیت یا خطا را بر عهده دارد.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.application.dtos.form_dto import FormSubmitDTO
from my_bot.core.exceptions.form_errors import FormValidationError, FormSubmissionError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button, get_back_to_main_button
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


class FormSubmitHandler:
    """
    هندلر ارسال فرم.

    این کلاس مسئولیت ارسال و ثبت نهایی فرم تکمیل‌شده را بر عهده دارد.
    """

    def __init__(
        self,
        form_submission_service: FormSubmissionService,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            form_submission_service: سرویس ثبت پاسخ فرم.
        """
        self._form_submission_service = form_submission_service
        self._user_states: Dict[int, Dict[str, Any]] = {}

    async def submit_form(self, callback: CallbackQuery) -> None:
        """
        ارسال فرم تکمیل‌شده.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer(
                    "⚠️ اطلاعات فرم یافت نشد. لطفاً دوباره شروع کنید.",
                    show_alert=True,
                )
                return

            # نمایش پیام در حال پردازش
            await callback.message.edit_text(
                text="⏳ **در حال ارسال فرم...**\n\nلطفاً منتظر بمانید.",
                parse_mode="Markdown",
            )

            # آماده‌سازی داده‌ها برای ارسال
            submit_dto = FormSubmitDTO(
                form_id=state["form_id"],
                answers=state["answers"],
                metadata={
                    "started_at": state.get("started_at"),
                    "completed_at": datetime.now().isoformat(),
                    "total_steps": state.get("total_steps", 0),
                    "user_agent": callback.from_user.full_name,
                },
            )

            # ارسال فرم به سرویس
            try:
                response = await self._form_submission_service.submit_form(
                    data=submit_dto,
                    user_id=user_id,
                )

                # نمایش پیام موفقیت
                success_message = self._build_success_message(response, state)
                await callback.message.edit_text(
                    text=success_message,
                    reply_markup=get_back_button("forms_list"),
                    parse_mode="Markdown",
                )

                # پاک کردن وضعیت کاربر
                if user_id in self._user_states:
                    del self._user_states[user_id]

                await callback.answer("✅ فرم با موفقیت ارسال شد!")

            except FormValidationError as e:
                # نمایش خطاهای اعتبارسنجی
                error_message = self._build_validation_error(e)
                await callback.message.edit_text(
                    text=error_message,
                    reply_markup=get_back_button("forms_list"),
                    parse_mode="Markdown",
                )
                await callback.answer("⚠️ خطاهای اعتبارسنجی فرم.", show_alert=True)

            except FormSubmissionError as e:
                # نمایش خطای ارسال
                await callback.message.edit_text(
                    text=self._build_submission_error(e),
                    reply_markup=get_back_button("forms_list"),
                    parse_mode="Markdown",
                )
                await callback.answer("⚠️ خطا در ارسال فرم.", show_alert=True)

        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            await callback.message.edit_text(
                text="⚠️ **خطا در ارسال فرم**\n\n"
                "متأسفانه خطایی در ارسال فرم رخ داد. لطفاً دوباره تلاش کنید.\n\n"
                "در صورت تکرار خطا، با پشتیبانی تماس بگیرید.",
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ خطا در ارسال فرم.", show_alert=True)

    async def confirm_submit(self, callback: CallbackQuery) -> None:
        """
        نمایش پیام تأیید قبل از ارسال نهایی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ اطلاعات فرم یافت نشد.", show_alert=True)
                return

            # نمایش خلاصه پاسخ‌ها
            summary = self._build_summary_text(state)

            await callback.message.edit_text(
                text=summary,
                reply_markup=self._get_confirm_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing confirm submission: {e}")
            await callback.answer("⚠️ خطا در نمایش تأییدیه.", show_alert=True)

    def set_user_state(
        self,
        user_id: int,
        form_id: int,
        answers: Dict[str, Any],
        current_step: int = 0,
        total_steps: int = 1,
    ) -> None:
        """
        تنظیم وضعیت کاربر برای ارسال فرم.

        Args:
            user_id: شناسه کاربر.
            form_id: شناسه فرم.
            answers: پاسخ‌های فرم.
            current_step: مرحله فعلی.
            total_steps: تعداد کل مراحل.
        """
        self._user_states[user_id] = {
            "form_id": form_id,
            "answers": answers,
            "current_step": current_step,
            "total_steps": total_steps,
            "started_at": datetime.now(),
        }
        logger.debug(f"User state set for {user_id}, form {form_id}")

    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت وضعیت کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[Dict[str, Any]]: وضعیت کاربر یا None.
        """
        return self._user_states.get(user_id)

    def clear_user_state(self, user_id: int) -> None:
        """
        پاک کردن وضعیت کاربر.

        Args:
            user_id: شناسه کاربر.
        """
        if user_id in self._user_states:
            del self._user_states[user_id]
            logger.debug(f"User state cleared for {user_id}")

    def _build_success_message(self, response, state: Dict[str, Any]) -> str:
        """
        ساخت پیام موفقیت ارسال فرم.

        Args:
            response: پاسخ سرویس (FormResponseDTO).
            state: وضعیت کاربر.

        Returns:
            str: پیام موفقیت.
        """
        random_message = MessagePool.get_random_form_completed()

        lines = [
            f"✅ {random_message}",
            "",
            f"📋 **فرم**: با موفقیت ارسال شد",
            f"🆔 شناسه پاسخ: {response.id}",
            f"📅 تاریخ ارسال: {response.submitted_at.strftime('%Y-%m-%d %H:%M')}",
        ]

        if response.is_valid:
            lines.append("✅ وضعیت: معتبر")
        else:
            lines.append("⚠️ وضعیت: نیاز به بررسی")

        if response.validation_errors:
            lines.extend([
                "",
                "⚠️ **تعداد خطاها:**",
                f"   {len(response.validation_errors)} خطا",
            ])

        if state.get("total_steps", 0) > 1:
            lines.append(f"📊 تعداد مراحل: {state['total_steps']}")

        lines.extend([
            "",
            "💡 **نکته**: پاسخ شما با موفقیت ثبت شد.",
            "از مشارکت شما سپاسگزاریم! 🙏",
        ])

        return "\n".join(lines)

    def _build_validation_error(self, error: FormValidationError) -> str:
        """
        ساخت پیام خطای اعتبارسنجی.

        Args:
            error: خطای اعتبارسنجی.

        Returns:
            str: پیام خطا.
        """
        lines = [
            "⚠️ **خطاهای اعتبارسنجی فرم**",
            "",
            "لطفاً خطاهای زیر را اصلاح کنید:",
            "",
        ]

        for field_error in error.context.get("errors", []):
            field = field_error.get("field", "نامشخص")
            message = field_error.get("message", "خطای ناشناخته")
            lines.append(f"• **{field}**: {message}")

        lines.extend([
            "",
            "📌 پس از اصلاح خطاها، دوباره تلاش کنید.",
        ])

        return "\n".join(lines)

    def _build_submission_error(self, error: FormSubmissionError) -> str:
        """
        ساخت پیام خطای ارسال.

        Args:
            error: خطای ارسال.

        Returns:
            str: پیام خطا.
        """
        return (
            "⚠️ **خطا در ارسال فرم**\n\n"
            f"{error.message}\n\n"
            "در صورت تکرار خطا، لطفاً با پشتیبانی تماس بگیرید."
        )

    def _build_summary_text(self, state: Dict[str, Any]) -> str:
        """
        ساخت متن خلاصه پاسخ‌ها برای تأیید.

        Args:
            state: وضعیت کاربر.

        Returns:
            str: متن خلاصه.
        """
        lines = [
            "📝 **تأیید ارسال فرم**",
            "",
            "لطفاً پاسخ‌های خود را بررسی کنید:",
            "",
        ]

        for key, value in state["answers"].items():
            if isinstance(value, list):
                value = ", ".join(value)
            elif isinstance(value, bool):
                value = "✅" if value else "❌"
            elif value is None:
                value = "❌ بدون پاسخ"
            lines.append(f"• **{key}**: {value}")

        lines.extend([
            "",
            "⚠️ **توجه**: پس از تأیید، امکان ویرایش پاسخ‌ها وجود ندارد.",
            "",
            "آیا از ارسال فرم مطمئن هستید؟",
        ])

        return "\n".join(lines)

    def _get_confirm_keyboard(self) -> types.InlineKeyboardMarkup:
        """
        دریافت کیبورد تأیید ارسال.

        Returns:
            types.InlineKeyboardMarkup: کیبورد تأیید.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ تأیید و ارسال", callback_data="form:submit"),
                InlineKeyboardButton("✏️ ویرایش", callback_data="form:edit"),
            ],
            [
                InlineKeyboardButton("❌ انصراف", callback_data="form:cancel"),
            ],
        ])