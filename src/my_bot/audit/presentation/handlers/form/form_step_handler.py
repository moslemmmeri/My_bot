# my_bot_project/src/my_bot/presentation/handlers/form/form_step_handler.py
"""
هندلر مرحله فرم (Form Step Handler).

این هندلر مسئولیت پردازش پاسخ‌های کاربر در هر مرحله از فرم،
اعتبارسنجی داده‌ها و مدیریت پیشرفت فرم را بر عهده دارد.
"""

from typing import Dict, Any, Optional

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button, get_cancel_button
from my_bot.presentation.keyboards.form.form_navigation import get_form_navigation_keyboard
from my_bot.domain.value_objects.form_field import FieldType

logger = get_logger(__name__)


class FormStepHandler:
    """
    هندلر مرحله فرم.

    این کلاس مسئولیت پردازش پاسخ‌های کاربر در هر مرحله از فرم را بر عهده دارد.
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

    async def handle_answer(self, message: Message) -> None:
        """
        پردازش پاسخ کاربر در یک مرحله از فرم.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await message.answer(
                    "⚠️ وضعیت فرم یافت نشد. لطفاً دوباره شروع کنید.",
                    reply_markup=get_back_button("forms_list"),
                )
                return

            # دریافت فرم و فیلدهای مرحله فعلی
            form = await self._form_builder_service.get_form(state["form_id"])
            current_step = state["current_step"]
            fields = form.get_fields_by_step(current_step)

            if not fields:
                # اگر فیلدی وجود نداشت، به مرحله بعد برو
                await self._next_step(message, user_id)
                return

            # اعتبارسنجی پاسخ‌ها (اگر چند فیلد در یک مرحله وجود داشته باشد)
            errors = []
            answers = {}

            for field in fields:
                # دریافت پاسخ برای این فیلد
                # برای سادگی، فرض می‌کنیم کاربر یک متن ارسال کرده است
                # در عمل، باید بر اساس نوع فیلد، پاسخ را استخراج کرد
                answer = message.text

                # اعتبارسنجی فیلد
                validation_error = field.validate(answer)
                if validation_error:
                    errors.append(f"• فیلد '{field.label}': {validation_error}")

                answers[field.name] = answer

            if errors:
                await message.answer(
                    "⚠️ **خطاهای اعتبارسنجی:**\n\n" + "\n".join(errors) +
                    "\n\nلطفاً پاسخ صحیح را وارد کنید.",
                    reply_markup=get_cancel_button(),
                    parse_mode="Markdown",
                )
                return

            # ذخیره پاسخ‌ها در وضعیت کاربر
            state["answers"].update(answers)

            # رفتن به مرحله بعد
            await self._next_step(message, user_id)

        except Exception as e:
            logger.error(f"Error handling form answer: {e}")
            await message.answer(
                "⚠️ خطا در پردازش پاسخ. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
            )

    async def handle_callback_answer(self, callback: CallbackQuery) -> None:
        """
        پردازش پاسخ انتخابی از کیبورد (برای فیلدهای انتخابی).

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # استخراج پاسخ از کالبک
            answer = callback.data.split(":")[2] if ":" in callback.data else callback.data

            # دریافت فرم و فیلدهای مرحله فعلی
            form = await self._form_builder_service.get_form(state["form_id"])
            current_step = state["current_step"]
            fields = form.get_fields_by_step(current_step)

            if not fields:
                await callback.answer("⚠️ فیلدی برای این مرحله یافت نشد.", show_alert=True)
                return

            # ذخیره پاسخ
            field = fields[0]  # برای سادگی، فقط یک فیلد در هر مرحله
            state["answers"][field.name] = answer

            # رفتن به مرحله بعد
            await self._next_step(callback.message, user_id)
            await callback.answer()

        except Exception as e:
            logger.error(f"Error handling callback answer: {e}")
            await callback.answer("⚠️ خطا در پردازش پاسخ.", show_alert=True)

    async def _next_step(self, message: Message, user_id: int) -> None:
        """
        رفتن به مرحله بعدی فرم.

        Args:
            message: پیام برای ارسال پاسخ.
            user_id: شناسه کاربر.
        """
        try:
            state = self._user_states.get(user_id)
            if not state:
                return

            state["current_step"] += 1

            if state["current_step"] > state["total_steps"]:
                # فرم تکمیل شده است
                await self._submit_form(message, user_id)
                return

            # نمایش مرحله بعد
            await self._show_step(message, user_id)

        except Exception as e:
            logger.error(f"Error going to next step: {e}")
            await message.answer(
                "⚠️ خطا در رفتن به مرحله بعد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
            )

    async def _show_step(self, message: Message, user_id: int) -> None:
        """
        نمایش یک مرحله از فرم با سوالات.

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

            # دریافت فیلدهای مرحله فعلی
            current_step = state["current_step"]
            fields = form.get_fields_by_step(current_step)

            if not fields:
                # اگر فیلدی وجود نداشت، به مرحله بعد برو
                await self._next_step(message, user_id)
                return

            # ساخت پیام مرحله
            text = self._build_step_question(form, current_step, fields)

            # ساخت کیبورد
            keyboard = self._build_step_keyboard(fields, current_step, state["total_steps"])

            # ارسال پیام
            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing step: {e}")
            await message.answer(
                "⚠️ خطا در نمایش مرحله فرم. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
            )

    def _build_step_question(self, form, step: int, fields: list) -> str:
        """
        ساخت متن سوالات مرحله.

        Args:
            form: اطلاعات فرم.
            step: شماره مرحله.
            fields: لیست فیلدهای مرحله.

        Returns:
            str: متن سوالات.
        """
        lines = [
            f"📝 **{form.title}**",
            "",
            f"مرحله {step} از {form.steps}",
            "",
        ]

        for i, field in enumerate(fields, 1):
            required = " ⚠️" if field.is_required else ""
            lines.append(f"**سوال {i}{required}:** {field.label}")

            if field.help_text:
                lines.append(f"💡 {field.help_text}")

            if field.field_type in (FieldType.SELECT, FieldType.RADIO):
                options = []
                for opt in field.options:
                    options.append(f"• {opt.get('label', opt.get('value'))}")
                lines.extend(["", "گزینه‌ها:", *options])

            elif field.field_type == FieldType.MULTI_SELECT:
                options = []
                for opt in field.options:
                    options.append(f"☑️ {opt.get('label', opt.get('value'))}")
                lines.extend(["", "گزینه‌ها (چند انتخابی):", *options])

            elif field.field_type == FieldType.CHECKBOX:
                options = []
                for opt in field.options:
                    options.append(f"☑️ {opt.get('label', opt.get('value'))}")
                lines.extend(["", "گزینه‌ها:", *options])

            lines.append("")

            # راهنمای ورودی
            input_guide = self._get_input_guide(field.field_type)
            if input_guide:
                lines.append(f"📌 {input_guide}")

        return "\n".join(lines)

    def _get_input_guide(self, field_type: str) -> str:
        """
        دریافت راهنمای ورودی برای نوع فیلد.

        Args:
            field_type: نوع فیلد.

        Returns:
            str: راهنمای ورودی.
        """
        guides = {
            FieldType.TEXT: "لطفاً متن مورد نظر را وارد کنید.",
            FieldType.TEXTAREA: "لطفاً متن کامل را وارد کنید.",
            FieldType.NUMBER: "لطفاً یک عدد وارد کنید.",
            FieldType.EMAIL: "لطفاً آدرس ایمیل را وارد کنید.",
            FieldType.PHONE: "لطفاً شماره تلفن را وارد کنید (با فرمت 09xxxxxxxxx).",
            FieldType.DATE: "لطفاً تاریخ را به فرمت YYYY-MM-DD وارد کنید.",
            FieldType.TIME: "لطفاً زمان را به فرمت HH:MM وارد کنید.",
            FieldType.DATETIME: "لطفاً تاریخ و زمان را به فرمت ISO وارد کنید.",
            FieldType.URL: "لطفاً آدرس اینترنتی را وارد کنید.",
            FieldType.COLOR: "لطفاً کد رنگ را به فرمت #RRGGBB وارد کنید.",
            FieldType.RATING: "لطفاً امتیاز را از ۱ تا ۵ وارد کنید.",
        }
        return guides.get(field_type, "لطفاً پاسخ خود را وارد کنید.")

    def _build_step_keyboard(self, fields: list, current_step: int, total_steps: int) -> types.InlineKeyboardMarkup:
        """
        ساخت کیبورد برای مرحله.

        Args:
            fields: لیست فیلدهای مرحله.
            current_step: شماره مرحله فعلی.
            total_steps: تعداد کل مراحل.

        Returns:
            types.InlineKeyboardMarkup: کیبورد ساخته‌شده.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        buttons = []

        # برای فیلدهای انتخابی، دکمه‌های گزینه‌ها را اضافه کن
        for field in fields:
            if field.field_type in (FieldType.SELECT, FieldType.RADIO):
                for opt in field.options:
                    buttons.append([
                        InlineKeyboardButton(
                            text=opt.get("label", opt.get("value")),
                            callback_data=f"form:answer:{field.name}:{opt.get('value')}"
                        )
                    ])

        # دکمه‌های ناوبری
        nav_buttons = []
        if current_step > 1:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ قبلی", callback_data="form:previous")
            )
        if current_step < total_steps:
            nav_buttons.append(
                InlineKeyboardButton("➡️ بعدی", callback_data="form:next")
            )
        if nav_buttons:
            buttons.append(nav_buttons)

        # دکمه لغو
        buttons.append([
            InlineKeyboardButton("❌ انصراف", callback_data="form:cancel")
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

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

            # ارسال پاسخ‌ها به سرویس
            # در عمل، پاسخ‌ها از state["answers"] گرفته می‌شوند
            # و به سرویس form_submission_service ارسال می‌شوند

            # پاک کردن وضعیت کاربر
            del self._user_states[user_id]

            # پیام موفقیت
            success_message = (
                "✅ **فرم با موفقیت ارسال شد!**\n\n"
                f"فرم: {form.title}\n"
                f"تعداد پاسخ‌ها: {len(state['answers'])}\n"
                f"تاریخ ارسال: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
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