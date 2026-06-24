# my_bot_project/src/admin_panel/modules/user_management/handlers/view_user.py
"""
هندلر مشاهده کاربر (View User Handler).

این هندلر مسئولیت نمایش اطلاعات کامل یک کاربر خاص در پنل مدیریت را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import CallbackQuery

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.modules.user_management.services.user_list_service import UserListService
from admin_panel.modules.user_management.keyboards.user_edit_keyboard import get_user_edit_keyboard
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.application.services.user.user_profile import UserProfileService

logger = get_logger(__name__)


class ViewUserHandler:
    """
    هندلر مشاهده اطلاعات کاربر.

    این کلاس با استفاده از UserRepository و UserProfileService،
    اطلاعات کامل یک کاربر را دریافت و در پنل مدیریت نمایش می‌دهد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        user_profile_service: UserProfileService,
        permission_checker: PermissionChecker,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            user_repository: ریپازیتوری کاربر.
            user_profile_service: سرویس پروفایل کاربر.
            permission_checker: بررسی‌کننده دسترسی‌ها.
        """
        self._user_repository = user_repository
        self._user_profile_service = user_profile_service
        self._permission_checker = permission_checker
        self._service = UserListService(user_repository)

        logger.info("ViewUserHandler initialized.")

    async def view_user(self, callback: CallbackQuery) -> None:
        """
        نمایش اطلاعات کامل یک کاربر.

        Args:
            callback: کالبک با داده‌ی `admin_user_view:{user_id}`.
        """
        try:
            # استخراج شناسه کاربر از کالبک
            user_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if user_id <= 0:
                await callback.answer("⚠️ شناسه کاربر نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی کاربر جاری
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.view")

            # دریافت اطلاعات کاربر هدف
            target_user = await self._user_repository.get_by_id(user_id)
            if not target_user:
                raise UserNotFoundError(user_id=user_id)

            # دریافت پروفایل کامل با آمار
            profile = await self._user_profile_service.get_profile(user_id)

            # ساخت متن و کیبورد
            text = self._build_user_detail_text(profile)
            keyboard = get_user_edit_keyboard(user_id)

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
            logger.error(f"Error viewing user {user_id}: {e}")
            await callback.answer("⚠️ خطا در نمایش اطلاعات کاربر.", show_alert=True)

    async def view_user_by_telegram(self, callback: CallbackQuery) -> None:
        """
        نمایش اطلاعات کاربر با شناسه تلگرام.

        Args:
            callback: کالبک با داده‌ی `admin_user_view_telegram:{telegram_id}`.
        """
        try:
            telegram_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if telegram_id <= 0:
                await callback.answer("⚠️ شناسه تلگرام نامعتبر است.", show_alert=True)
                return

            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "users.view")

            target_user = await self._user_repository.get_by_telegram_id(telegram_id)
            if not target_user:
                raise UserNotFoundError(telegram_id=telegram_id)

            profile = await self._user_profile_service.get_profile(target_user.id or 0)

            text = self._build_user_detail_text(profile)
            keyboard = get_user_edit_keyboard(target_user.id or 0)

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
            logger.error(f"Error viewing user by telegram {telegram_id}: {e}")
            await callback.answer("⚠️ خطا در نمایش اطلاعات کاربر.", show_alert=True)

    def _build_user_detail_text(self, profile) -> str:
        """
        ساخت متن اطلاعات کامل کاربر.

        Args:
            profile: اطلاعات پروفایل کاربر.

        Returns:
            str: متن اطلاعات کاربر.
        """
        lines = [
            "👤 **اطلاعات کاربر**",
            "",
            f"🆔 شناسه: `{profile.id}`",
            f"📛 نام: {profile.full_name or 'نامشخص'}",
            f"👤 نام کاربری: @{profile.username or 'ندارد'}",
        ]

        if profile.phone_number:
            lines.append(f"📞 تلفن: {profile.phone_number}")
        if profile.email:
            lines.append(f"📧 ایمیل: {profile.email}")

        lines.extend([
            "",
            f"🔑 نقش: {profile.role.get_display_name() if profile.role else 'کاربر'}",
            f"🏅 سطح: {profile.level.emoji} {profile.level.display_name}",
            f"⭐ امتیاز: {profile.points}",
        ])

        lines.extend([
            "",
            "📊 **آمار**",
            f"🛒 تعداد سفارشات: {profile.total_orders}",
            f"💰 مجموع پرداخت‌ها: {profile.total_spent:,.0f} تومان",
        ])

        if profile.average_order_value:
            lines.append(f"📈 میانگین هر سفارش: {profile.average_order_value:,.0f} تومان")

        if profile.last_order_date:
            lines.append(f"📅 آخرین سفارش: {profile.last_order_date.strftime('%Y-%m-%d %H:%M')}")

        lines.extend([
            "",
            "📌 **وضعیت**",
            f"🟢 فعال: {'✅' if profile.is_active else '❌'}",
            f"🚫 مسدود: {'✅' if profile.is_banned else '❌'}",
        ])

        if profile.last_activity:
            lines.append(f"⏰ آخرین فعالیت: {profile.last_activity.strftime('%Y-%m-%d %H:%M')}")

        lines.extend([
            "",
            f"📅 تاریخ عضویت: {profile.created_at.strftime('%Y-%m-%d %H:%M')}",
        ])

        return "\n".join(lines)

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

    async def get_user_statistics(self, user_id: int) -> dict:
        """
        دریافت آمار یک کاربر (برای استفاده در سایر بخش‌ها).

        Args:
            user_id: شناسه کاربر.

        Returns:
            dict: آمار کاربر.
        """
        try:
            return await self._user_profile_service.get_user_stats(user_id)
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}