# my_bot_project/src/admin_panel/modules/user_management/handlers/list_users.py
"""
هندلر نمایش لیست کاربران (List Users Handler).

این هندلر مسئولیت نمایش لیست کاربران با صفحه‌بندی و فیلترهای مختلف
در پنل مدیریت را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import CallbackQuery

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.modules.user_management.services.user_list_service import UserListService
from admin_panel.modules.user_management.keyboards.user_list_keyboard import get_user_list_keyboard
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.domain.interfaces.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class ListUsersHandler:
    """
    هندلر نمایش لیست کاربران.

    این کلاس با استفاده از UserListService، لیست کاربران را دریافت
    کرده و با صفحه‌بندی و فیلترهای مختلف در پنل مدیریت نمایش می‌دهد.
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
        self._service = UserListService(user_repository)

        logger.info("ListUsersHandler initialized.")

    async def show_users(self, callback: CallbackQuery) -> None:
        """
        نمایش لیست کاربران با صفحه‌بندی پیش‌فرض.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            # بررسی دسترسی
            self._permission_checker.check_permission(user, "users.view")

            # دریافت لیست کاربران (صفحه اول)
            page = 0
            users_data = await self._service.get_users_page(page=page)

            # ساخت کیبورد
            keyboard = get_user_list_keyboard(
                users=users_data["users"],
                current_page=page,
                total_pages=users_data["total_pages"],
                filters=users_data.get("filters"),
            )

            # متن لیست
            text = self._build_list_text(users_data, page)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except Exception as e:
            logger.error(f"Error showing users list: {e}")
            await callback.answer("⚠️ خطا در نمایش لیست کاربران.", show_alert=True)

    async def change_page(self, callback: CallbackQuery) -> None:
        """
        تغییر صفحه لیست کاربران.

        Args:
            callback: کالبک با داده‌ی `admin_users_page:{page}`.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(user, "users.view")

            # استخراج شماره صفحه
            page = int(callback.data.split(":")[1]) if ":" in callback.data else 0

            # دریافت داده‌ها
            users_data = await self._service.get_users_page(page=page)

            keyboard = get_user_list_keyboard(
                users=users_data["users"],
                current_page=page,
                total_pages=users_data["total_pages"],
                filters=users_data.get("filters"),
            )

            text = self._build_list_text(users_data, page)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except Exception as e:
            logger.error(f"Error changing page: {e}")
            await callback.answer("⚠️ خطا در تغییر صفحه.", show_alert=True)

    async def apply_filter(self, callback: CallbackQuery) -> None:
        """
        اعمال فیلتر روی لیست کاربران.

        Args:
            callback: کالبک با داده‌ی `admin_users_filter:{filter_name}`.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(user, "users.view")

            # استخراج نام فیلتر
            filter_name = callback.data.split(":")[1] if ":" in callback.data else "all"

            # دریافت داده‌ها با فیلتر
            users_data = await self._service.get_users_page(page=0, filter_name=filter_name)

            keyboard = get_user_list_keyboard(
                users=users_data["users"],
                current_page=0,
                total_pages=users_data["total_pages"],
                filters=users_data.get("filters"),
                active_filter=filter_name,
            )

            text = self._build_list_text(users_data, 0, filter_name)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            await callback.answer("⚠️ خطا در اعمال فیلتر.", show_alert=True)

    async def search_users(self, callback: CallbackQuery) -> None:
        """
        نمایش فرم جستجوی کاربران.

        Args:
            callback: کالبک `admin_user_search`.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(user, "users.view")

            await callback.message.edit_text(
                text="🔍 **جستجوی کاربران**\n\n"
                     "لطفاً عبارت جستجو را وارد کنید.\n"
                     "می‌توانید بر اساس نام، نام کاربری، ایمیل یا شماره تلفن جستجو کنید.",
                reply_markup=self._get_search_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except Exception as e:
            logger.error(f"Error showing search: {e}")
            await callback.answer("⚠️ خطا در نمایش جستجو.", show_alert=True)

    def _build_list_text(self, users_data: dict, page: int, filter_name: str = "all") -> str:
        """
        ساخت متن لیست کاربران.

        Args:
            users_data: داده‌های کاربران.
            page: شماره صفحه.
            filter_name: نام فیلتر فعال.

        Returns:
            str: متن لیست.
        """
        total = users_data["total"]
        users = users_data["users"]
        total_pages = users_data["total_pages"]

        lines = [
            "👥 **مدیریت کاربران**",
            "",
            f"📊 تعداد کل: {total} کاربر",
            f"📄 صفحه {page + 1} از {total_pages}",
        ]

        if filter_name != "all":
            lines.append(f"🔍 فیلتر: {filter_name}")

        lines.append("")

        if not users:
            lines.append("هیچ کاربری یافت نشد.")
        else:
            for idx, user in enumerate(users, start=page * 10 + 1):
                username = user.username or "بدون نام کاربری"
                full_name = user.full_name or "نامشخص"
                role = user.role.value if user.role else "کاربر"
                status = "✅" if user.is_active else "⛔"
                banned = "🚫" if user.is_banned else ""

                lines.append(
                    f"{idx}. {status} **{full_name}** (@{username}) {banned}"
                )
                lines.append(f"   🆔 {user.telegram_id} | نقش: {role}")
                lines.append("")

        return "\n".join(lines)

    def _get_search_keyboard(self) -> types.InlineKeyboardMarkup:
        """
        ساخت کیبورد برای فرم جستجو.

        Returns:
            types.InlineKeyboardMarkup: کیبورد جستجو.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users"),
            ],
        ])

    async def _get_user_from_callback(self, callback: CallbackQuery):
        """
        دریافت کاربر از کالبک (با فرض اینکه از طریق middleware شناسه کاربر در دسترس است).

        Args:
            callback: کالبک دریافتی.

        Returns:
            User یا None.
        """
        # در عمل، کاربر از طریق context یا از دیتابیس با telegram_id دریافت می‌شود
        # اینجا از ریپازیتوری استفاده می‌کنیم
        telegram_id = callback.from_user.id
        return await self._user_repository.get_by_telegram_id(telegram_id)