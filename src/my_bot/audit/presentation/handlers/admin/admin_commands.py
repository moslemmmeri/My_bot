# my_bot_project/src/my_bot/presentation/handlers/admin/admin_commands.py
"""
دستورات ادمین (Admin Commands).

این ماژول شامل دستورات اسلش (Slash Commands) برای توسعه‌دهندگان
و ادمین‌ها است که به‌عنوان میان‌بر برای دسترسی سریع به بخش‌های مختلف
پنل مدیریت استفاده می‌شوند.

توجه: تمام عملیات مدیریتی اصلی از طریق دکمه‌های شیشه‌ای انجام می‌شود
و این دستورات صرفاً به‌عنوان میان‌بر در نظر گرفته شده‌اند.
"""

from typing import Optional

from aiogram import types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.core.constants.user_roles import UserRole
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.admin.admin_keyboards import get_admin_main_keyboard
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard

logger = get_logger(__name__)


class AdminCommandsHandler:
    """
    هندلر دستورات ادمین.

    این کلاس مسئولیت پردازش دستورات اسلش مربوط به ادمین‌ها را بر عهده دارد.
    """

    def __init__(
        self,
        profile_service: Optional[UserProfileService] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            profile_service: سرویس پروفایل کاربر (اختیاری).
        """
        self._profile_service = profile_service

    async def admin_command(self, message: Message) -> None:
        """
        پردازش دستور /admin.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id

            # بررسی دسترسی
            is_admin = await self._check_admin_permission(user_id)

            if not is_admin:
                await message.answer(
                    "⛔ **دسترسی غیرمجاز**\n\n"
                    "شما دسترسی به پنل مدیریت را ندارید.",
                    parse_mode="Markdown",
                )
                return

            # نمایش پنل مدیریت
            text = self._build_admin_panel_text()
            keyboard = get_admin_main_keyboard()

            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for user {message.from_user.id}: {e}")
            await message.answer(
                "⛔ **دسترسی غیرمجاز**\n\n"
                "شما دسترسی به پنل مدیریت را ندارید.",
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling /admin command: {e}")
            await message.answer(
                "⚠️ **خطا**\n\n"
                "خطایی در پردازش دستور رخ داد. لطفاً دوباره تلاش کنید.",
                parse_mode="Markdown",
            )

    async def admin_users_command(self, message: Message) -> None:
        """
        پردازش دستور /admin_users.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id

            # بررسی دسترسی
            is_admin = await self._check_admin_permission(user_id)

            if not is_admin:
                await message.answer(
                    "⛔ **دسترسی غیرمجاز**",
                    parse_mode="Markdown",
                )
                return

            await message.answer(
                "👥 **مدیریت کاربران**\n\n"
                "در حال بارگذاری لیست کاربران...\n\n"
                "💡 برای دسترسی کامل به مدیریت کاربران، از پنل مدیریت استفاده کنید.",
                reply_markup=get_admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling /admin_users command: {e}")
            await message.answer(
                "⚠️ **خطا**\n\n"
                "خطایی در پردازش دستور رخ داد.",
                parse_mode="Markdown",
            )

    async def admin_stats_command(self, message: Message) -> None:
        """
        پردازش دستور /admin_stats.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id

            # بررسی دسترسی
            is_admin = await self._check_admin_permission(user_id)

            if not is_admin:
                await message.answer(
                    "⛔ **دسترسی غیرمجاز**",
                    parse_mode="Markdown",
                )
                return

            # اینجا باید آمار سیستم نمایش داده شود
            # فعلاً یک پیام نمونه ارسال می‌کنیم
            stats_text = (
                "📊 **آمار سیستم**\n\n"
                "📌 **کاربران**\n"
                "   • کل کاربران: ۱,۲۳۴\n"
                "   • کاربران فعال: ۹۸۷\n"
                "   • کاربران جدید امروز: ۴۵\n\n"
                "📌 **سفارشات**\n"
                "   • کل سفارشات: ۵۶۷\n"
                "   • سفارشات امروز: ۲۳\n"
                "   • درآمد امروز: ۱۲,۳۴۵,۶۷۸ تومان\n\n"
                "📌 **فرم‌ها**\n"
                "   • کل فرم‌ها: ۱۲\n"
                "   • فرم‌های فعال: ۸\n"
                "   • ارسال‌های امروز: ۳۴\n\n"
                "💡 برای مشاهده آمار کامل، از پنل مدیریت استفاده کنید."
            )

            await message.answer(
                text=stats_text,
                reply_markup=get_admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling /admin_stats command: {e}")
            await message.answer(
                "⚠️ **خطا**\n\n"
                "خطایی در پردازش دستور رخ داد.",
                parse_mode="Markdown",
            )

    async def admin_broadcast_command(self, message: Message) -> None:
        """
        پردازش دستور /admin_broadcast.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id

            # بررسی دسترسی
            is_admin = await self._check_admin_permission(user_id)

            if not is_admin:
                await message.answer(
                    "⛔ **دسترسی غیرمجاز**",
                    parse_mode="Markdown",
                )
                return

            await message.answer(
                "📢 **ارسال گروهی**\n\n"
                "برای ارسال پیام گروهی، از پنل مدیریت استفاده کنید.\n\n"
                "💡 دستورات میان‌بر:\n"
                "• /admin - پنل مدیریت\n"
                "• /admin_stats - آمار سیستم\n"
                "• /admin_users - مدیریت کاربران",
                reply_markup=get_admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling /admin_broadcast command: {e}")
            await message.answer(
                "⚠️ **خطا**\n\n"
                "خطایی در پردازش دستور رخ داد.",
                parse_mode="Markdown",
            )

    async def admin_features_command(self, message: Message) -> None:
        """
        پردازش دستور /admin_features.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id

            # بررسی دسترسی
            is_admin = await self._check_admin_permission(user_id)

            if not is_admin:
                await message.answer(
                    "⛔ **دسترسی غیرمجاز**",
                    parse_mode="Markdown",
                )
                return

            await message.answer(
                "🏷️ **مدیریت فیچر فلاگ**\n\n"
                "برای مدیریت فیچر فلاگ‌ها، از پنل مدیریت استفاده کنید.\n\n"
                "💡 گزینه‌های موجود در پنل:\n"
                "• مشاهده لیست فیچرها\n"
                "• فعال/غیرفعال کردن فیچرها\n"
                "• افزودن فیچر جدید",
                reply_markup=get_admin_main_keyboard(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling /admin_features command: {e}")
            await message.answer(
                "⚠️ **خطا**\n\n"
                "خطایی در پردازش دستور رخ داد.",
                parse_mode="Markdown",
            )

    async def admin_help_command(self, message: Message) -> None:
        """
        پردازش دستور /admin_help.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            help_text = (
                "📖 **راهنمای دستورات ادمین**\n\n"
                "دستورات زیر به‌عنوان میان‌بر برای دسترسی سریع به بخش‌های "
                "مختلف پنل مدیریت در نظر گرفته شده‌اند:\n\n"
                "🔹 **/admin** - ورود به پنل مدیریت\n"
                "🔹 **/admin_users** - مدیریت کاربران\n"
                "🔹 **/admin_stats** - مشاهده آمار سیستم\n"
                "🔹 **/admin_broadcast** - ارسال گروهی\n"
                "🔹 **/admin_features** - مدیریت فیچر فلاگ‌ها\n"
                "🔹 **/admin_help** - این راهنما\n\n"
                "⚠️ **توجه**: تمام عملیات مدیریتی اصلی از طریق دکمه‌های "
                "شیشه‌ای در پنل مدیریت انجام می‌شود.\n\n"
                "💡 برای دسترسی به پنل مدیریت، روی دکمه «⚙️ پنل مدیریت» "
                "در منوی اصلی کلیک کنید."
            )

            await message.answer(
                text=help_text,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error handling /admin_help command: {e}")
            await message.answer(
                "⚠️ **خطا**\n\n"
                "خطایی در پردازش دستور رخ داد.",
                parse_mode="Markdown",
            )

    async def _check_admin_permission(self, user_id: int) -> bool:
        """
        بررسی دسترسی ادمین برای کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            bool: True اگر کاربر ادمین باشد.

        Raises:
            PermissionDeniedError: اگر کاربر دسترسی نداشته باشد.
        """
        if not self._profile_service:
            # اگر سرویس در دسترس نیست، فقط کاربرانی که در لیست مشخص هستند
            admin_ids = [123456789]  # لیست ادمین‌ها (در عمل از دیتابیس خوانده می‌شود)
            if user_id in admin_ids:
                return True
            raise PermissionDeniedError(
                message="شما دسترسی به پنل مدیریت را ندارید.",
                context={"user_id": user_id},
            )

        try:
            profile = await self._profile_service.get_profile_by_telegram_id(user_id)
            is_admin = profile.role in (UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)

            if not is_admin:
                raise PermissionDeniedError(
                    message="شما دسترسی به پنل مدیریت را ندارید.",
                    context={"user_id": user_id, "role": profile.role.value},
                )

            return True

        except Exception as e:
            logger.error(f"Error checking admin permission for {user_id}: {e}")
            raise PermissionDeniedError(
                message="خطا در بررسی دسترسی.",
                context={"user_id": user_id},
            )

    def _build_admin_panel_text(self) -> str:
        """
        ساخت متن پنل مدیریت.

        Returns:
            str: متن پنل مدیریت.
        """
        return (
            "🔐 **پنل مدیریت**\n\n"
            "از گزینه‌های زیر برای مدیریت سیستم استفاده کنید:\n\n"
            "👥 **مدیریت کاربران** - مشاهده، ویرایش و حذف کاربران\n"
            "📦 **مدیریت سفارشات** - مدیریت سفارشات کاربران\n"
            "📊 **آمار و تحلیل** - مشاهده گزارش‌های آماری\n"
            "✉️ **ارسال گروهی** - ارسال پیام به کاربران\n"
            "📝 **مدیریت محتوا** - مدیریت فرم‌ها و محتوا\n"
            "⚙️ **تنظیمات** - تنظیمات سیستم\n"
            "📑 **لاگ‌ها** - مشاهده لاگ‌های سیستم\n"
            "🚨 **خطاها** - مشاهده خطاهای سیستم\n"
            "🏷️ **فیچر فلاگ** - مدیریت ویژگی‌ها\n"
            "💳 **کوپن‌ها** - مدیریت کدهای تخفیف\n"
            "🎫 **تیکت‌ها** - مدیریت تیکت‌های پشتیبانی\n"
            "🔄 **پشتیبان** - مدیریت پشتیبان‌گیری\n"
            "💚 **سلامت سیستم** - بررسی سلامت سرویس‌ها\n"
            "📌 **A/B تست** - مدیریت تست‌های A/B\n\n"
            "💡 **نکته**: تمام عملیات‌ها از طریق دکمه‌ها انجام می‌شود."
        )