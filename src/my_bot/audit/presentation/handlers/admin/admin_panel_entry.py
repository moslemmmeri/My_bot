# my_bot_project/src/my_bot/presentation/handlers/admin/admin_panel_entry.py
"""
هندلر ورود به پنل مدیریت (Admin Panel Entry Handler).

این هندلر مسئولیت ورود به پنل مدیریت، بررسی دسترسی کاربر
و نمایش منوی اصلی مدیریت را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.core.constants.user_roles import UserRole
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.admin.admin_keyboards import get_admin_main_keyboard
from my_bot.presentation.keyboards.common.back_buttons import get_back_to_main_button
from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard

logger = get_logger(__name__)


class AdminPanelEntryHandler:
    """
    هندلر ورود به پنل مدیریت.

    این کلاس مسئولیت ورود به پنل مدیریت و بررسی دسترسی کاربر را بر عهده دارد.
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

    async def enter_admin_panel(self, callback: CallbackQuery) -> None:
        """
        ورود به پنل مدیریت.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # بررسی دسترسی کاربر
            is_admin = await self._check_admin_permission(user_id)

            if not is_admin:
                await callback.answer(
                    "⛔ شما دسترسی به پنل مدیریت را ندارید.",
                    show_alert=True,
                )
                return

            # نمایش منوی مدیریت
            text = self._build_admin_panel_text()
            keyboard = get_admin_main_keyboard()

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer("🔐 ورود به پنل مدیریت")

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for user {callback.from_user.id}: {e}")
            await callback.answer("⛔ شما دسترسی به پنل مدیریت را ندارید.", show_alert=True)

        except Exception as e:
            logger.error(f"Error entering admin panel: {e}")
            await callback.answer("⚠️ خطا در ورود به پنل مدیریت.", show_alert=True)

    async def exit_admin_panel(self, callback: CallbackQuery) -> None:
        """
        خروج از پنل مدیریت و بازگشت به منوی اصلی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            await callback.message.edit_text(
                text="🏠 **بازگشت به منوی اصلی**\n\n"
                "از گزینه‌های زیر انتخاب کنید:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("🚪 خروج از پنل مدیریت")

        except Exception as e:
            logger.error(f"Error exiting admin panel: {e}")
            await callback.answer("⚠️ خطا در خروج از پنل مدیریت.", show_alert=True)

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
            # در عمل، باید از سرویس کاربر استفاده کرد
            # برای امنیت، فقط برخی کاربران خاص اجازه دارند
            admin_ids = [123456789]  # لیست ادمین‌ها (در عمل از دیتابیس خوانده می‌شود)
            if user_id in admin_ids:
                return True
            raise PermissionDeniedError(
                message="شما دسترسی به پنل مدیریت را ندارید.",
                context={"user_id": user_id},
            )

        try:
            # دریافت اطلاعات کاربر
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