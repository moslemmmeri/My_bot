# my_bot_project/src/admin_panel/modules/user_management/handlers/delete_user.py
"""
هندلر حذف کاربر (Delete User Handler).

این هندلر مسئولیت حذف کاربران از سیستم را در پنل مدیریت بر عهده دارد.
شامل نمایش تأییدیه حذف، انجام عملیات حذف و نمایش نتیجه است.
"""

from typing import Optional

from aiogram import types
from aiogram.types import CallbackQuery

from admin_panel.core.permissions.permission_checker import PermissionChecker
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.domain.interfaces.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class DeleteUserHandler:
    """
    هندلر حذف کاربر.

    این کلاس با استفاده از UserRepository و PermissionChecker،
    عملیات حذف کاربران را در پنل مدیریت انجام می‌دهد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        permission_checker: PermissionChecker,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            user_repository: ریپازیتوری کاربر.
            permission_checker: بررسی‌کننده دسترسی‌ها.
        """
        self._user_repository = user_repository
        self._permission_checker = permission_checker

        logger.info("DeleteUserHandler initialized.")

    async def confirm_delete(self, callback: CallbackQuery) -> None:
        """
        نمایش تأییدیه حذف کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_delete:{user_id}`.
        """
        try:
            # استخراج شناسه کاربر
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.delete")

            # دریافت کاربر هدف
            target_user = await self._user_repository.get_by_id(user_id)
            if not target_user:
                raise UserNotFoundError(user_id=user_id)

            # نمایش تأییدیه
            text = self._build_confirm_text(target_user)
            keyboard = self._get_confirm_keyboard(user_id)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except UserNotFoundError as e:
            logger.warning(f"User not found: {e}")
            await callback.answer("⚠️ کاربر مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error showing delete confirmation for user {user_id}: {e}")
            await callback.answer("⚠️ خطا در نمایش تأییدیه حذف.", show_alert=True)

    async def delete_user(self, callback: CallbackQuery) -> None:
        """
        انجام عملیات حذف کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_confirm_delete:{user_id}`.
        """
        try:
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.delete")

            # دریافت کاربر هدف
            target_user = await self._user_repository.get_by_id(user_id)
            if not target_user:
                raise UserNotFoundError(user_id=user_id)

            # جلوگیری از حذف خود
            if current_user.id == user_id:
                await callback.answer("⚠️ شما نمی‌توانید خودتان را حذف کنید.", show_alert=True)
                return

            # انجام حذف
            result = await self._user_repository.delete(user_id)

            if result:
                # نمایش پیام موفقیت
                await callback.message.edit_text(
                    text=f"✅ **کاربر با موفقیت حذف شد.**\n\n"
                         f"👤 کاربر: {target_user.full_name} (@{target_user.username or 'ندارد'})\n"
                         f"🆔 شناسه: `{target_user.id}`",
                    reply_markup=self._get_back_keyboard(),
                    parse_mode="Markdown",
                )
                await callback.answer("✅ کاربر حذف شد.")

                logger.info(f"User {user_id} deleted by admin {current_user.id}")

            else:
                await callback.answer("⚠️ کاربر حذف نشد. لطفاً دوباره تلاش کنید.", show_alert=True)

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except UserNotFoundError as e:
            logger.warning(f"User not found: {e}")
            await callback.answer("⚠️ کاربر مورد نظر یافت نشد.", show_alert=True)

        except DatabaseError as e:
            logger.error(f"Database error deleting user {user_id}: {e}")
            await callback.answer("⚠️ خطا در حذف کاربر از دیتابیس.", show_alert=True)

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            await callback.answer("⚠️ خطا در حذف کاربر.", show_alert=True)

    async def cancel_delete(self, callback: CallbackQuery) -> None:
        """
        لغو عملیات حذف کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_cancel_delete:{user_id}`.
        """
        try:
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            await callback.message.edit_text(
                text="❌ **حذف کاربر لغو شد.**\n\n"
                     "هیچ تغییری در اطلاعات کاربر ایجاد نشد.",
                reply_markup=self._get_back_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("حذف کاربر لغو شد.")

        except Exception as e:
            logger.error(f"Error cancelling delete for user {user_id}: {e}")
            await callback.answer("⚠️ خطا در لغو حذف.", show_alert=True)

    def _build_confirm_text(self, user) -> str:
        """
        ساخت متن تأییدیه حذف کاربر.

        Args:
            user: موجودیت کاربر.

        Returns:
            str: متن تأییدیه.
        """
        return (
            f"⚠️ **تأیید حذف کاربر**\n\n"
            f"آیا از حذف کاربر زیر مطمئن هستید؟\n\n"
            f"👤 کاربر: {user.full_name} (@{user.username or 'ندارد'})\n"
            f"🆔 شناسه: `{user.id}`\n"
            f"📧 ایمیل: {user.email or 'ندارد'}\n"
            f"📞 تلفن: {user.phone_number or 'ندارد'}\n\n"
            f"❌ **توجه**: این عملیات غیرقابل بازگشت است و تمام اطلاعات مرتبط با کاربر حذف خواهد شد."
        )

    def _get_confirm_keyboard(self, user_id: int) -> types.InlineKeyboardMarkup:
        """
        دریافت کیبورد تأیید حذف.

        Args:
            user_id: شناسه کاربر.

        Returns:
            types.InlineKeyboardMarkup: کیبورد تأیید حذف.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"admin_user_confirm_delete:{user_id}"),
                InlineKeyboardButton("❌ لغو", callback_data=f"admin_user_cancel_delete:{user_id}"),
            ],
        ])

    def _get_back_keyboard(self) -> types.InlineKeyboardMarkup:
        """
        دریافت کیبورد بازگشت به لیست کاربران.

        Returns:
            types.InlineKeyboardMarkup: کیبورد بازگشت.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data="admin_users")],
        ])

    async def _get_user_from_callback(self, callback: CallbackQuery):
        """
        دریافت کاربر از کالبک.

        Args:
            callback: کالبک دریافتی.

        Returns:
            User یا None.
        """
        telegram_id = callback.from_user.id
        return await self._user_repository.get_by_telegram_id(telegram_id)