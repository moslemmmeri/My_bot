# my_bot_project/src/my_bot/presentation/handlers/form/form_list_handler.py
"""
هندلر لیست فرم‌ها (Form List Handler).

این هندلر مسئولیت نمایش لیست فرم‌های موجود برای کاربر
و مدیریت انتخاب فرم برای پر کردن را بر عهده دارد.
"""

from typing import Optional, List

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.core.constants.form_types import FormType
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_to_main_button
from my_bot.presentation.keyboards.form.form_choice import get_form_choice_keyboard

logger = get_logger(__name__)


class FormListHandler:
    """
    هندلر لیست فرم‌ها.

    این کلاس مسئولیت نمایش لیست فرم‌های موجود برای کاربر را بر عهده دارد.
    """

    def __init__(self, form_builder_service: FormBuilderService) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            form_builder_service: سرویس ساخت فرم.
        """
        self._form_builder_service = form_builder_service

    async def show_forms(self, callback: CallbackQuery) -> None:
        """
        نمایش لیست فرم‌های موجود.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # دریافت فرم‌های فعال
            forms = await self._form_builder_service.get_active_forms()

            if not forms:
                text = "📋 **فرم‌ها**\n\n"
                text += "در حال حاضر هیچ فرم فعالی برای پر کردن وجود ندارد."
                text += "\n\n🔜 به زودی فرم‌های جدید اضافه می‌شوند."

                await callback.message.edit_text(
                    text=text,
                    reply_markup=get_back_to_main_button(),
                    parse_mode="Markdown",
                )
                await callback.answer()
                return

            # ساخت متن و کیبورد
            text = self._build_forms_text(forms)
            keyboard = get_form_choice_keyboard(forms)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing forms list: {e}")
            await callback.answer("⚠️ خطا در نمایش لیست فرم‌ها.", show_alert=True)

    async def show_form_categories(self, callback: CallbackQuery) -> None:
        """
        نمایش دسته‌بندی فرم‌ها.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # دریافت فرم‌های فعال
            forms = await self._form_builder_service.get_active_forms()

            if not forms:
                await self.show_forms(callback)
                return

            # دسته‌بندی فرم‌ها بر اساس نوع
            categories = self._categorize_forms(forms)

            text = "📋 **دسته‌بندی فرم‌ها**\n\n"
            for category, category_forms in categories.items():
                text += f"**{category}**\n"
                for form in category_forms:
                    text += f"  • {form.title}\n"
                text += "\n"

            keyboard = get_form_choice_keyboard(forms)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing form categories: {e}")
            await callback.answer("⚠️ خطا در نمایش دسته‌بندی فرم‌ها.", show_alert=True)

    def _build_forms_text(self, forms: List) -> str:
        """
        ساخت متن لیست فرم‌ها.

        Args:
            forms: لیست فرم‌ها.

        Returns:
            str: متن لیست فرم‌ها.
        """
        lines = ["📋 **فرم‌های موجود**", ""]

        if not forms:
            lines.append("در حال حاضر هیچ فرم فعالی وجود ندارد.")
            return "\n".join(lines)

        for i, form in enumerate(forms, 1):
            status = "✅ فعال" if form.is_active else "⏸️ غیرفعال"
            type_display = FormType(form.form_type).display_name if form.form_type else "سایر"

            lines.extend([
                f"{i}. **{form.title}**",
                f"   📌 نوع: {type_display}",
                f"   📊 وضعیت: {status}",
            ])

            if form.description:
                lines.append(f"   📝 {form.description[:100]}...")
            if form.submission_count:
                lines.append(f"   📤 تعداد ارسال: {form.submission_count}")

            lines.append("")

        lines.append("💡 **نکته**: برای شروع پر کردن هر فرم، روی دکمه مربوطه کلیک کنید.")

        return "\n".join(lines)

    def _categorize_forms(self, forms: List) -> dict:
        """
        دسته‌بندی فرم‌ها بر اساس نوع.

        Args:
            forms: لیست فرم‌ها.

        Returns:
            dict: دیکشنری دسته‌بندی‌شده.
        """
        categories = {
            "📝 ثبت‌نام": [],
            "🛒 سفارشات": [],
            "📊 نظرسنجی": [],
            "💬 بازخورد": [],
            "🎫 پشتیبانی": [],
            "⚙️ سایر": [],
        }

        type_mapping = {
            "registration": "📝 ثبت‌نام",
            "registration_event": "📝 ثبت‌نام",
            "order": "🛒 سفارشات",
            "survey": "📊 نظرسنجی",
            "feedback": "💬 بازخورد",
            "suggestion": "💬 بازخورد",
            "ticket": "🎫 پشتیبانی",
            "complaint": "🎫 پشتیبانی",
            "contact": "🎫 پشتیبانی",
            "application": "📝 ثبت‌نام",
            "reservation": "🛒 سفارشات",
        }

        for form in forms:
            category = type_mapping.get(form.form_type, "⚙️ سایر")
            categories[category].append(form)

        # حذف دسته‌بندی‌های خالی
        return {k: v for k, v in categories.items() if v}

    async def select_form(self, callback: CallbackQuery) -> None:
        """
        پردازش انتخاب فرم توسط کاربر.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # استخراج شناسه فرم از کالبک
            form_id = int(callback.data.split(":")[1])

            # ذخیره شناسه فرم در حالت (state) کاربر
            # این کار توسط FormStartHandler انجام می‌شود
            # redirect به FormStartHandler

            # ارسال به هندلر شروع فرم
            from my_bot.presentation.handlers.form.form_start_handler import FormStartHandler
            # در عمل، این کار از طریق دیسپچر انجام می‌شود
            # اینجا فقط یک پیام ارسال می‌کنیم

            await callback.message.edit_text(
                text=f"📝 **شروع فرم**\n\n"
                f"فرم مورد نظر انتخاب شد. لطفاً منتظر بمانید...",
                reply_markup=get_back_to_main_button(),
                parse_mode="Markdown",
            )
            await callback.answer("فرم انتخاب شد. در حال انتقال...")

        except Exception as e:
            logger.error(f"Error selecting form: {e}")
            await callback.answer("⚠️ خطا در انتخاب فرم.", show_alert=True)