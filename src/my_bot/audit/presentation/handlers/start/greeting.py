# my_bot_project/src/my_bot/presentation/handlers/start/greeting.py
"""
هندلر پیام‌های خوش‌آمدگویی و منوی اصلی.

این هندلر مسئولیت نمایش منوی اصلی و پیام‌های خوش‌آمدگویی
به کاربران در شرایط مختلف را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


class GreetingHandler:
    """
    هندلر پیام‌های خوش‌آمدگویی.

    این کلاس مسئولیت نمایش منوی اصلی و پیام‌های خوش‌آمدگویی
    به کاربران را بر عهده دارد.
    """

    def __init__(self) -> None:
        """مقداردهی اولیه هندلر."""
        pass

    async def show_main_menu(
        self,
        message: Message,
        user_name: Optional[str] = None,
        custom_text: Optional[str] = None,
    ) -> None:
        """
        نمایش منوی اصلی به کاربر.

        Args:
            message: پیام دریافتی از تلگرام.
            user_name: نام کاربر (اختیاری).
            custom_text: متن سفارشی برای نمایش (اختیاری).
        """
        try:
            if custom_text:
                text = custom_text
            else:
                greeting = MessagePool.get_random_greeting()
                name = user_name or "کاربر عزیز"
                text = self._build_main_menu_text(greeting, name)

            await message.answer(
                text=text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )

        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            await message.answer(
                "⚠️ خطا در نمایش منوی اصلی. لطفاً دوباره تلاش کنید."
            )

    async def show_main_menu_by_callback(
        self,
        callback: CallbackQuery,
        user_name: Optional[str] = None,
        custom_text: Optional[str] = None,
    ) -> None:
        """
        نمایش منوی اصلی از طریق کالبک.

        Args:
            callback: کالبک دریافتی از تلگرام.
            user_name: نام کاربر (اختیاری).
            custom_text: متن سفارشی برای نمایش (اختیاری).
        """
        try:
            if custom_text:
                text = custom_text
            else:
                greeting = MessagePool.get_random_greeting()
                name = user_name or "کاربر عزیز"
                text = self._build_main_menu_text(greeting, name)

            await callback.message.edit_text(
                text=text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing main menu by callback: {e}")
            await callback.answer("⚠️ خطا در نمایش منوی اصلی.", show_alert=True)

    def _build_main_menu_text(self, greeting: str, user_name: str) -> str:
        """
        ساخت متن منوی اصلی.

        Args:
            greeting: پیام خوش‌آمدگویی.
            user_name: نام کاربر.

        Returns:
            str: متن منوی اصلی.
        """
        return (
            f"{greeting} {hbold(user_name)} 👋\n\n"
            "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:\n\n"
            f"{hitalic('📋 فرم‌ها')} - پر کردن فرم‌های مختلف\n"
            f"{hitalic('👤 پروفایل')} - مشاهده و ویرایش اطلاعات شخصی\n"
            f"{hitalic('📞 تماس با ما')} - ارتباط با پشتیبانی\n"
            f"{hitalic('❓ راهنما')} - راهنمای کامل استفاده از ربات"
        )

    async def handle_help(self, message: Message) -> None:
        """
        نمایش راهنمای سریع به کاربر.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            help_text = (
                "❓ **راهنمای سریع**\n\n"
                "🟢 **فرم‌ها**: برای پر کردن فرم‌های مختلف (ثبت‌نام، سفارش، نظرخواهی و ...) "
                "روی دکمه «📋 فرم‌ها» کلیک کنید.\n\n"
                "🟢 **پروفایل**: برای مشاهده و ویرایش اطلاعات شخصی، امتیاز و سطح خود، "
                "روی دکمه «👤 پروفایل» کلیک کنید.\n\n"
                "🟢 **تماس با ما**: برای ارتباط با پشتیبانی، روی دکمه «📞 تماس با ما» کلیک کنید.\n\n"
                "🟢 **راهنما**: برای مشاهده راهنمای کامل، روی دکمه «❓ راهنما» کلیک کنید.\n\n"
                "---\n"
                "💡 **نکته**: تمام عملیات‌ها از طریق دکمه‌ها انجام می‌شود و نیازی به تایپ دستور نیست."
            )

            await message.answer(
                text=help_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing help: {e}")
            await message.answer(
                "⚠️ خطا در نمایش راهنما. لطفاً دوباره تلاش کنید."
            )

    async def handle_cancel(self, callback: CallbackQuery) -> None:
        """
        لغو عملیات در حال انجام و بازگشت به منوی اصلی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            text = (
                "❌ عملیات لغو شد.\n\n"
                "به منوی اصلی بازگشتید. از گزینه‌های زیر انتخاب کنید:"
            )

            await callback.message.edit_text(
                text=text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML",
            )
            await callback.answer("عملیات لغو شد.")

        except Exception as e:
            logger.error(f"Error handling cancel: {e}")
            await callback.answer("⚠️ خطا در لغو عملیات.", show_alert=True)