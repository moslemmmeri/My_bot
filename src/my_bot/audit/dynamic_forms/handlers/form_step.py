# my_bot_project/src/my_bot/dynamic_forms/handlers/form_step.py
"""
هندلر مرحله فرم پویا (Dynamic Form Step Handler).

این هندلر مسئولیت پردازش پاسخ‌های کاربر در هر مرحله از فرم پویا،
اعتبارسنجی داده‌ها، به‌روزرسانی وضعیت و هدایت کاربر به مرحله بعدی را بر عهده دارد.
"""

from typing import Optional, Dict, Any, List

from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.not_found_errors import FormNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError, MultipleValidationErrors
from my_bot.core.exceptions.form_errors import FormValidationError
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.dynamic_forms.engine.form_state_manager import FormStateManager
from my_bot.dynamic_forms.engine.form_renderer import FormRenderer
from my_bot.dynamic_forms.engine.form_validator import FormValidator
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button
from my_bot.presentation.keyboards.form.form_navigation import get_form_navigation_keyboard
from my_bot.shared.utils.message_pool import MessagePool
from my_bot.dynamic_forms.models.form_field import FieldType

logger = get_logger(__name__)


class FormStepHandler:
    """
    هندلر مرحله فرم پویا.

    این کلاس مسئولیت پردازش پاسخ‌های کاربر در هر مرحله از فرم را بر عهده دارد.
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

        # ذخیره پاسخ‌های موقت برای فیلدهای چند مرحله‌ای (برای پردازش در کالبک)
        self._temp_answers: Dict[int, Dict[str, Any]] = {}

        logger.info("FormStepHandler initialized.")

    async def handle_message(self, message: Message) -> None:
        """
        پردازش پیام دریافتی به‌عنوان پاسخ یک مرحله از فرم.

        Args:
            message: پیام دریافتی از تلگرام (متن، شماره، ایمیل و ...).
        """
        try:
            user_id = message.from_user.id
            text = message.text

            if not text:
                await message.answer(
                    "⚠️ لطفاً پاسخ خود را به‌صورت متن وارد کنید.",
                    reply_markup=get_cancel_button(),
                )
                return

            # دریافت وضعیت فعلی کاربر
            state = await self._get_current_state(user_id)
            if not state:
                await message.answer(
                    "⚠️ وضعیت فرم یافت نشد. لطفاً دوباره فرم را شروع کنید.",
                    reply_markup=get_back_button("forms_list"),
                )
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await self._state_manager.clear_state(state.form_id, user_id)
                await message.answer(
                    "⚠️ فرم مورد نظر یافت نشد. لطفاً دوباره شروع کنید.",
                    reply_markup=get_back_button("forms_list"),
                )
                return

            # دریافت فیلدهای مرحله فعلی
            current_step = state.current_step
            fields = form_definition.get_fields_by_step(current_step)

            if not fields:
                # اگر فیلدی وجود نداشت، به مرحله بعد برو
                await self._go_to_next_step(message, state, form_definition)
                return

            # پردازش پاسخ برای هر فیلد
            answers = {}
            errors = []

            for field in fields:
                # اگر فیلد از نوع انتخابی است، نباید از طریق پیام متنی پردازش شود
                if field.field_type in FieldType.SELECTION_TYPES:
                    errors.append({
                        "field": field.name,
                        "message": f"فیلد '{field.label}' باید از طریق گزینه‌ها انتخاب شود."
                    })
                    continue

                # اعتبارسنجی مقدار
                validation_error = field.validate(text)
                if validation_error:
                    errors.append({
                        "field": field.name,
                        "message": validation_error
                    })
                else:
                    answers[field.name] = self._convert_value(field, text)

            # اگر خطای اعتبارسنجی وجود دارد، نمایش بده
            if errors:
                await self._show_validation_errors(message, errors, fields)
                return

            # به‌روزرسانی وضعیت با پاسخ‌ها
            await self._state_manager.save_answer(
                form_id=state.form_id,
                user_id=user_id,
                field_name=fields[0].name,  # برای سادگی، فقط یک فیلد در هر مرحله
                value=answers.get(fields[0].name),
            )

            # رفتن به مرحله بعد
            await self._go_to_next_step(message, state, form_definition)

        except ValidationError as e:
            logger.warning(f"Validation error in form step: {e}")
            await message.answer(
                f"⚠️ {e.message}\n\nلطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
            )

        except Exception as e:
            logger.error(f"Error handling form message: {e}", exc_info=True)
            await message.answer(
                "⚠️ **خطا در پردازش پاسخ**\n\n"
                "متأسفانه خطایی در پردازش پاسخ شما رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
                parse_mode="Markdown",
            )

    async def handle_callback(self, callback: CallbackQuery) -> None:
        """
        پردازش پاسخ‌های انتخابی از کیبورد (برای فیلدهای انتخابی).

        Args:
            callback: کالبک دریافتی از تلگرام (فرمت‌های مختلف).
        """
        try:
            user_id = callback.from_user.id
            data = callback.data

            # تشخیص نوع کالبک
            if data.startswith("form:answer:"):
                # پاسخ تک انتخابی: form:answer:{field_name}:{value}
                await self._handle_single_choice(callback)
            elif data.startswith("form:multi_answer:"):
                # پاسخ چند انتخابی: form:multi_answer:{field_name}:{value}
                await self._handle_multi_choice(callback)
            elif data == "form:next":
                # رفتن به مرحله بعد
                await self._handle_next_step(callback)
            elif data == "form:previous":
                # بازگشت به مرحله قبلی
                await self._handle_previous_step(callback)
            elif data == "form:cancel":
                # لغو فرم
                await self._handle_cancel(callback)
            else:
                await callback.answer("⚠️ گزینه نامعتبر.", show_alert=True)

        except Exception as e:
            logger.error(f"Error handling form callback: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در پردازش پاسخ.", show_alert=True)

    async def _handle_single_choice(self, callback: CallbackQuery) -> None:
        """
        پردازش پاسخ تک انتخابی.

        Args:
            callback: کالبک دریافتی (فرمت: `form:answer:{field_name}:{value}`).
        """
        try:
            user_id = callback.from_user.id
            parts = callback.data.split(":")
            if len(parts) != 4:
                await callback.answer("⚠️ فرمت کالبک نامعتبر.", show_alert=True)
                return

            field_name = parts[2]
            value = parts[3]

            # دریافت وضعیت
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم یافت نشد.", show_alert=True)
                return

            # اعتبارسنجی مقدار (بررسی اینکه در گزینه‌ها وجود دارد)
            field = form_definition.get_field(field_name)
            if not field:
                await callback.answer("⚠️ فیلد یافت نشد.", show_alert=True)
                return

            validation_error = field.validate(value)
            if validation_error:
                await callback.answer(f"⚠️ {validation_error}", show_alert=True)
                return

            # ذخیره پاسخ
            await self._state_manager.save_answer(
                form_id=state.form_id,
                user_id=user_id,
                field_name=field_name,
                value=value,
            )

            # نمایش پیام تأیید
            await callback.answer(f"✅ گزینه '{field.label}' انتخاب شد.")

            # رفتن به مرحله بعد (اگر مرحله فعلی کامل شده باشد)
            await self._go_to_next_step(callback.message, state, form_definition)

        except Exception as e:
            logger.error(f"Error handling single choice: {e}")
            await callback.answer("⚠️ خطا در پردازش انتخاب.", show_alert=True)

    async def _handle_multi_choice(self, callback: CallbackQuery) -> None:
        """
        پردازش پاسخ چند انتخابی (ذخیره موقت و نمایش گزینه‌ها).

        Args:
            callback: کالبک دریافتی (فرمت: `form:multi_answer:{field_name}:{value}`).
        """
        try:
            user_id = callback.from_user.id
            parts = callback.data.split(":")
            if len(parts) != 4:
                await callback.answer("⚠️ فرمت کالبک نامعتبر.", show_alert=True)
                return

            field_name = parts[2]
            value = parts[3]

            # دریافت وضعیت
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم یافت نشد.", show_alert=True)
                return

            # اعتبارسنجی مقدار
            field = form_definition.get_field(field_name)
            if not field:
                await callback.answer("⚠️ فیلد یافت نشد.", show_alert=True)
                return

            # ذخیره موقت در دیکشنری
            if user_id not in self._temp_answers:
                self._temp_answers[user_id] = {}
            if field_name not in self._temp_answers[user_id]:
                self._temp_answers[user_id][field_name] = []

            # اگر مقدار قبلاً انتخاب شده، حذف کن، در غیر این صورت اضافه کن
            temp_list = self._temp_answers[user_id][field_name]
            if value in temp_list:
                temp_list.remove(value)
                action = "حذف"
            else:
                temp_list.append(value)
                action = "افزودن"

            # نمایش وضعیت فعلی انتخاب‌ها
            selected = ", ".join(temp_list) if temp_list else "هیچ گزینه‌ای انتخاب نشده است."

            # ساخت کیبورد با گزینه‌های انتخاب‌شده
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            buttons = []
            for opt in field.options:
                opt_value = opt.get("value")
                opt_label = opt.get("label", opt_value)
                is_selected = opt_value in temp_list
                text = f"{'✅' if is_selected else '☑️'} {opt_label}"
                buttons.append([
                    InlineKeyboardButton(
                        text=text,
                        callback_data=f"form:multi_answer:{field_name}:{opt_value}"
                    )
                ])

            buttons.append([
                InlineKeyboardButton(
                    text="✅ تأیید و ادامه",
                    callback_data=f"form:multi_confirm:{field_name}"
                )
            ])
            buttons.append([
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="form:cancel"
                )
            ])

            await callback.message.edit_text(
                text=f"📌 **{field.label}** (چند انتخابی)\n\n"
                     f"گزینه‌های انتخاب‌شده: {selected}\n\n"
                     f"برای انتخاب/لغو هر گزینه کلیک کنید. پس از اتمام، «تأیید و ادامه» را بزنید.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="Markdown",
            )

            await callback.answer(f"{action} گزینه: {value}")

        except Exception as e:
            logger.error(f"Error handling multi choice: {e}")
            await callback.answer("⚠️ خطا در پردازش انتخاب.", show_alert=True)

    async def _handle_multi_confirm(self, callback: CallbackQuery) -> None:
        """
        تأیید و ذخیره پاسخ چند انتخابی.

        Args:
            callback: کالبک دریافتی (فرمت: `form:multi_confirm:{field_name}`).
        """
        try:
            user_id = callback.from_user.id
            parts = callback.data.split(":")
            if len(parts) != 3:
                await callback.answer("⚠️ فرمت کالبک نامعتبر.", show_alert=True)
                return

            field_name = parts[2]

            # دریافت پاسخ‌های موقت
            temp_answers = self._temp_answers.get(user_id, {})
            value = temp_answers.get(field_name, [])

            if not value:
                await callback.answer("⚠️ حداقل یک گزینه باید انتخاب شود.", show_alert=True)
                return

            # دریافت وضعیت
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم یافت نشد.", show_alert=True)
                return

            # ذخیره پاسخ
            await self._state_manager.save_answer(
                form_id=state.form_id,
                user_id=user_id,
                field_name=field_name,
                value=value,
            )

            # پاک کردن پاسخ موقت
            if user_id in self._temp_answers:
                self._temp_answers[user_id].pop(field_name, None)

            await callback.answer("✅ پاسخ ذخیره شد.")

            # رفتن به مرحله بعد
            await self._go_to_next_step(callback.message, state, form_definition)

        except Exception as e:
            logger.error(f"Error handling multi confirm: {e}")
            await callback.answer("⚠️ خطا در تأیید انتخاب.", show_alert=True)

    async def _handle_next_step(self, callback: CallbackQuery) -> None:
        """
        رفتن به مرحله بعدی فرم.

        Args:
            callback: کالبک دریافتی.
        """
        try:
            user_id = callback.from_user.id

            # دریافت وضعیت
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم یافت نشد.", show_alert=True)
                return

            await self._go_to_next_step(callback.message, state, form_definition)
            await callback.answer()

        except Exception as e:
            logger.error(f"Error going to next step: {e}")
            await callback.answer("⚠️ خطا در رفتن به مرحله بعد.", show_alert=True)

    async def _handle_previous_step(self, callback: CallbackQuery) -> None:
        """
        بازگشت به مرحله قبلی فرم.

        Args:
            callback: کالبک دریافتی.
        """
        try:
            user_id = callback.from_user.id

            # دریافت وضعیت
            state = await self._get_current_state(user_id)
            if not state:
                await callback.answer("⚠️ وضعیت فرم یافت نشد.", show_alert=True)
                return

            # دریافت تعریف فرم
            form_definition = await self._get_form_definition(state.form_id)
            if not form_definition:
                await callback.answer("⚠️ فرم یافت نشد.", show_alert=True)
                return

            if state.current_step > 1:
                # کاهش مرحله
                await self._state_manager.update_state(
                    form_id=state.form_id,
                    user_id=user_id,
                    current_step=state.current_step - 1,
                )

                # دریافت وضعیت به‌روز
                updated_state = await self._get_current_state(user_id)

                # رندر مرحله قبلی
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
                await callback.answer("بازگشت به مرحله قبلی.")

            else:
                await callback.answer("شما در مرحله اول هستید.")

        except Exception as e:
            logger.error(f"Error going to previous step: {e}")
            await callback.answer("⚠️ خطا در بازگشت به مرحله قبل.", show_alert=True)

    async def _handle_cancel(self, callback: CallbackQuery) -> None:
        """
        لغو پر کردن فرم.

        Args:
            callback: کالبک دریافتی.
        """
        try:
            user_id = callback.from_user.id

            # پاک کردن وضعیت
            await self._state_manager.clear_all_user_states(user_id)

            # پاک کردن پاسخ‌های موقت
            if user_id in self._temp_answers:
                del self._temp_answers[user_id]

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

    async def _go_to_next_step(
        self,
        message: Message,
        state: Any,
        form_definition: Any,
    ) -> None:
        """
        رفتن به مرحله بعدی فرم.

        Args:
            message: پیام برای ارسال پاسخ.
            state: وضعیت فعلی.
            form_definition: تعریف فرم.
        """
        try:
            # افزایش مرحله
            next_step = state.current_step + 1
            total_steps = form_definition.get_step_count()

            if next_step > total_steps:
                # فرم کامل شده است
                await self._complete_form(message, state, form_definition)
                return

            # به‌روزرسانی وضعیت
            await self._state_manager.update_state(
                form_id=state.form_id,
                user_id=state.user_id,
                current_step=next_step,
            )

            # دریافت وضعیت به‌روز
            updated_state = await self._get_current_state(state.user_id)

            # رندر مرحله بعد
            rendered = self._renderer.render_for_telegram(
                form=form_definition,
                current_step=updated_state.current_step,
                answers=updated_state.answers,
                include_metadata=True,
            )

            # ارسال پیام مرحله بعد
            await message.answer(
                text=rendered["text"],
                reply_markup=rendered["keyboard"],
                parse_mode=rendered["parse_mode"],
            )

        except Exception as e:
            logger.error(f"Error going to next step: {e}")
            await message.answer(
                "⚠️ خطا در رفتن به مرحله بعد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
            )

    async def _complete_form(
        self,
        message: Message,
        state: Any,
        form_definition: Any,
    ) -> None:
        """
        تکمیل فرم (همه مراحل پر شده است).

        Args:
            message: پیام برای ارسال پاسخ.
            state: وضعیت فرم.
            form_definition: تعریف فرم.
        """
        try:
            # اعتبارسنجی نهایی تمام فیلدها
            errors = self._validator.validate(form_definition, state.answers)
            if errors:
                await self._show_validation_errors(message, errors, form_definition.fields)
                return

            # افزایش تعداد ارسال‌های فرم
            form_definition.increment_submission_count()

            # ارسال رویداد تکمیل فرم (در صورت وجود)
            if form_definition.on_submit:
                try:
                    await form_definition.on_submit(state)
                except Exception as e:
                    logger.error(f"Error in form submit callback: {e}")

            # پاک کردن وضعیت کاربر
            await self._state_manager.clear_state(state.form_id, state.user_id)

            # پاک کردن پاسخ‌های موقت
            if state.user_id in self._temp_answers:
                del self._temp_answers[state.user_id]

            # پیام موفقیت
            success_message = form_definition.success_message or MessagePool.get_random_form_completed()

            text = f"✅ {success_message}\n\n"
            text += f"📋 فرم: {form_definition.title}\n"
            text += f"📅 تاریخ ارسال: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            text += "از مشارکت شما سپاسگزاریم! 🙏"

            await message.answer(
                text=text,
                reply_markup=get_back_button("forms_list"),
                parse_mode="Markdown",
            )

            logger.info(
                f"Form completed: form_id={state.form_id}, "
                f"user_id={state.user_id}, answers={len(state.answers)}"
            )

        except Exception as e:
            logger.error(f"Error completing form: {e}")
            await message.answer(
                "⚠️ **خطا در تکمیل فرم**\n\n"
                "متأسفانه خطایی در تکمیل فرم رخ داد. لطفاً دوباره تلاش کنید.",
                reply_markup=get_cancel_button(),
                parse_mode="Markdown",
            )

    async def _show_validation_errors(
        self,
        message: Message,
        errors: List[Dict[str, str]],
        fields: List[Any],
    ) -> None:
        """
        نمایش خطاهای اعتبارسنجی به کاربر.

        Args:
            message: پیام برای ارسال پاسخ.
            errors: لیست خطاها.
            fields: لیست فیلدهای مرحله.
        """
        error_text = "⚠️ **خطاهای اعتبارسنجی:**\n\n"
        for error in errors:
            field_name = error.get("field", "نامشخص")
            field = next((f for f in fields if f.name == field_name), None)
            field_label = field.label if field else field_name
            error_text += f"• {field_label}: {error['message']}\n"

        error_text += "\nلطفاً پاسخ صحیح را وارد کنید."

        await message.answer(
            text=error_text,
            reply_markup=get_cancel_button(),
            parse_mode="Markdown",
        )

    def _convert_value(self, field: Any, text: str) -> Any:
        """
        تبدیل مقدار ورودی به نوع مناسب بر اساس نوع فیلد.

        Args:
            field: فیلد فرم.
            text: متن ورودی.

        Returns:
            Any: مقدار تبدیل‌شده.
        """
        if field.field_type == FieldType.NUMBER:
            try:
                return float(text) if "." in text else int(text)
            except ValueError:
                return text
        elif field.field_type == FieldType.BOOLEAN:
            return text.lower() in ("true", "1", "yes", "بله")
        elif field.field_type in (FieldType.DATE, FieldType.TIME, FieldType.DATETIME):
            return text
        else:
            return text

    async def _get_current_state(self, user_id: int) -> Optional[Any]:
        """
        دریافت وضعیت فعلی کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[Any]: وضعیت فرم یا None در صورت عدم وجود.
        """
        # از آنجا که ممکن است کاربر چندین فرم را همزمان پر کند،
        # ما فقط آخرین فرم فعال را برمی‌گردانیم.
        # برای این کار، از state_manager.get_state استفاده می‌کنیم
        # و همه وضعیت‌های کاربر را دریافت می‌کنیم.
        states = await self._state_manager.get_all_user_states(user_id)
        if not states:
            return None

        # آخرین وضعیت به‌روز شده را برمی‌گردانیم
        return max(states, key=lambda s: s.last_updated_at)

    async def _get_form_definition(self, form_id: int) -> Optional[Any]:
        """
        دریافت تعریف فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            Optional[Any]: تعریف فرم یا None.
        """
        # در اینجا از همان روش FormStartHandler برای تبدیل استفاده می‌کنیم
        # برای جلوگیری از تکرار، می‌توان این تابع را در یک کلاس پایه قرار داد.
        # برای سادگی، اینجا یک پیاده‌سازی ساده داریم
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