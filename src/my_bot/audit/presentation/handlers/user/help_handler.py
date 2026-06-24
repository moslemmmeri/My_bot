# my_bot_project/src/my_bot/presentation/handlers/user/help_handler.py
"""
هندلر راهنمای کاربر (Help Handler).

این هندلر مسئولیت نمایش راهنمای کامل، سوالات متداول (FAQ)
و اطلاعات تماس با پشتیبانی را بر عهده دارد.
"""

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode, hlink

from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_to_main_button
from my_bot.presentation.keyboards.help.help_keyboards import get_help_menu_keyboard

logger = get_logger(__name__)


class HelpHandler:
    """
    هندلر راهنمای کاربر.

    این کلاس مسئولیت نمایش راهنمای کامل، سوالات متداول
    و اطلاعات تماس با پشتیبانی را بر عهده دارد.
    """

    def __init__(self) -> None:
        """مقداردهی اولیه هندلر."""
        pass

    async def show_help(self, callback: CallbackQuery) -> None:
        """
        نمایش منوی راهنما.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            help_text = self._build_help_menu_text()

            await callback.message.edit_text(
                text=help_text,
                reply_markup=get_help_menu_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing help menu: {e}")
            await callback.answer("⚠️ خطا در نمایش راهنما.", show_alert=True)

    async def show_full_guide(self, callback: CallbackQuery) -> None:
        """
        نمایش راهنمای کامل.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            guide_text = self._build_full_guide_text()

            await callback.message.edit_text(
                text=guide_text,
                reply_markup=get_back_to_main_button("help"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing full guide: {e}")
            await callback.answer("⚠️ خطا در نمایش راهنمای کامل.", show_alert=True)

    async def show_faq(self, callback: CallbackQuery) -> None:
        """
        نمایش سوالات متداول.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            faq_text = self._build_faq_text()

            await callback.message.edit_text(
                text=faq_text,
                reply_markup=get_back_to_main_button("help"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing FAQ: {e}")
            await callback.answer("⚠️ خطا در نمایش سوالات متداول.", show_alert=True)

    async def show_contact(self, callback: CallbackQuery) -> None:
        """
        نمایش اطلاعات تماس با پشتیبانی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            contact_text = self._build_contact_text()

            await callback.message.edit_text(
                text=contact_text,
                reply_markup=get_back_to_main_button("help"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing contact info: {e}")
            await callback.answer("⚠️ خطا در نمایش اطلاعات تماس.", show_alert=True)

    async def back_to_help(self, callback: CallbackQuery) -> None:
        """
        بازگشت به منوی راهنما.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        await self.show_help(callback)

    def _build_help_menu_text(self) -> str:
        """
        ساخت متن منوی راهنما.

        Returns:
            str: متن منوی راهنما.
        """
        return (
            "❓ **راهنمای کاربر**\n\n"
            "از گزینه‌های زیر انتخاب کنید:\n\n"
            "📖 **راهنمای کامل** - راهنمای جامع استفاده از ربات\n"
            "❔ **سوالات متداول** - پاسخ به سوالات رایج\n"
            "📞 **تماس با ما** - راه‌های ارتباط با پشتیبانی\n\n"
            "💡 **نکته**: تمام عملیات‌ها از طریق دکمه‌ها انجام می‌شود "
            "و نیازی به تایپ دستور نیست."
        )

    def _build_full_guide_text(self) -> str:
        """
        ساخت متن راهنمای کامل.

        Returns:
            str: متن راهنمای کامل.
        """
        return (
            "📖 **راهنمای کامل استفاده از ربات**\n\n"
            "🟢 **1. ثبت‌نام و ورود**\n"
            "با ارسال دستور /start یا کلیک روی دکمه «شروع»، "
            "به‌صورت خودکار در سیستم ثبت‌نام می‌شوید.\n\n"

            "🟢 **2. منوی اصلی**\n"
            "پس از ثبت‌نام، منوی اصلی شامل گزینه‌های زیر نمایش داده می‌شود:\n"
            "• 📋 **فرم‌ها**: مشاهده و پر کردن فرم‌های موجود\n"
            "• 👤 **پروفایل**: مشاهده و ویرایش اطلاعات شخصی\n"
            "• 📞 **تماس با ما**: ارتباط با پشتیبانی\n"
            "• ❓ **راهنما**: راهنمای کامل\n\n"

            "🟢 **3. فرم‌ها**\n"
            "با کلیک روی دکمه «📋 فرم‌ها»، لیست فرم‌های موجود نمایش داده می‌شود. "
            "با انتخاب هر فرم، مراحل آن را تکمیل کنید.\n\n"

            "🟢 **4. پروفایل**\n"
            "در بخش پروفایل می‌توانید:\n"
            "• اطلاعات شخصی خود را مشاهده کنید\n"
            "• امتیاز و سطح خود را ببینید\n"
            "• تاریخچه سفارشات را مشاهده کنید\n\n"

            "🟢 **5. امتیاز و سطوح**\n"
            "با هر اقدام (تکمیل فرم، ثبت سفارش و ...) امتیاز دریافت می‌کنید. "
            "با جمع‌آوری امتیاز، سطح شما ارتقا می‌یابد.\n\n"

            "🟢 **6. پشتیبانی**\n"
            "برای ارتباط با پشتیبانی، از گزینه «📞 تماس با ما» استفاده کنید."
        )

    def _build_faq_text(self) -> str:
        """
        ساخت متن سوالات متداول.

        Returns:
            str: متن سوالات متداول.
        """
        return (
            "❔ **سوالات متداول (FAQ)**\n\n"
            "**۱. چگونه در ربات ثبت‌نام کنم؟**\n"
            "با ارسال دستور /start یا کلیک روی دکمه «شروع»، به‌صورت خودکار ثبت‌نام می‌شوید.\n\n"

            "**۲. چگونه امتیاز بیشتری کسب کنم؟**\n"
            "با تکمیل فرم‌ها، ثبت سفارش، ارسال بازخورد و فعالیت در ربات امتیاز کسب می‌کنید.\n\n"

            "**۳. سطوح کاربری چگونه تعیین می‌شوند؟**\n"
            "سطوح بر اساس امتیاز تعیین می‌شوند:\n"
            "• 🥉 برنز: ۰ تا ۹۹ امتیاز\n"
            "• 🥈 نقره: ۱۰۰ تا ۴۹۹ امتیاز\n"
            "• 🥇 طلا: ۵۰۰ تا ۹۹۹ امتیاز\n"
            "• 💎 پلاتین: ۱۰۰۰ تا ۴۹۹۹ امتیاز\n"
            "• 👑 الماس: ۵۰۰۰+ امتیاز\n\n"

            "**۴. چگونه می‌توانم سفارش ثبت کنم؟**\n"
            "از طریق فرم‌های موجود در بخش «📋 فرم‌ها» می‌توانید سفارش خود را ثبت کنید.\n\n"

            "**۵. چگونه با پشتیبانی تماس بگیرم؟**\n"
            "از گزینه «📞 تماس با ما» در منوی اصلی استفاده کنید.\n\n"

            "**۶. آیا اطلاعات من محفوظ است؟**\n"
            "بله، تمام اطلاعات کاربران با رعایت اصول امنیتی ذخیره می‌شود."
        )

    def _build_contact_text(self) -> str:
        """
        ساخت متن اطلاعات تماس.

        Returns:
            str: متن اطلاعات تماس.
        """
        return (
            "📞 **تماس با پشتیبانی**\n\n"
            "برای ارتباط با پشتیبانی از یکی از راه‌های زیر استفاده کنید:\n\n"

            "📱 **تلگرام**\n"
            "• @SupportBot (آیدی پشتیبانی)\n"
            "• با کلیک روی دکمه زیر می‌توانید پیام خود را ارسال کنید.\n\n"

            "📧 **ایمیل**\n"
            "• support@example.com\n\n"

            "🌐 **وبسایت**\n"
            "• https://example.com/contact\n\n"

            "🕐 **ساعات پاسخگویی**\n"
            "• شنبه تا چهارشنبه: ۹ تا ۱۸\n"
            "• پنجشنبه: ۹ تا ۱۳\n\n"

            "💡 **نکته**: برای دریافت پاسخ سریع‌تر، حتماً اطلاعات زیر را ذکر کنید:\n"
            "• شناسه کاربری\n"
            "• شماره سفارش (در صورت وجود)\n"
            "• شرح کامل مشکل یا درخواست"
        )