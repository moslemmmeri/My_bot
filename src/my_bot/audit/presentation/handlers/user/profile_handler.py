# my_bot_project/src/my_bot/presentation/handlers/user/profile_handler.py
"""
هندلر پروفایل کاربر (Profile Handler).

این هندلر مسئولیت نمایش و مدیریت پروفایل کاربر، شامل اطلاعات شخصی،
امتیاز، سطح، و آمار سفارشات را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.user.user_profile import UserProfileService
from my_bot.application.services.user.user_level_upgrade import UserLevelUpgradeService
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.user.user_actions import get_user_actions_keyboard
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


class ProfileHandler:
    """
    هندلر پروفایل کاربر.

    این کلاس مسئولیت نمایش و مدیریت پروفایل کاربر را بر عهده دارد.
    """

    def __init__(
        self,
        profile_service: UserProfileService,
        level_upgrade_service: Optional[UserLevelUpgradeService] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            profile_service: سرویس پروفایل کاربر.
            level_upgrade_service: سرویس ارتقاء سطح کاربر (اختیاری).
        """
        self._profile_service = profile_service
        self._level_upgrade_service = level_upgrade_service

    async def show_profile(self, callback: CallbackQuery) -> None:
        """
        نمایش پروفایل کاربر.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # دریافت پروفایل کاربر
            profile = await self._profile_service.get_profile_by_telegram_id(user_id)

            # ساخت متن پروفایل
            profile_text = self._build_profile_text(profile)

            # ارسال پیام با دکمه‌های اقدام
            await callback.message.edit_text(
                text=profile_text,
                reply_markup=get_user_actions_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing profile: {e}")
            await callback.answer("⚠️ خطا در نمایش پروفایل.", show_alert=True)

    async def show_orders(self, callback: CallbackQuery) -> None:
        """
        نمایش تاریخچه سفارشات کاربر.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # دریافت تاریخچه سفارشات
            orders = await self._profile_service.get_user_orders(user_id, limit=5)

            if not orders:
                await callback.message.edit_text(
                    text="🛒 **تاریخچه سفارشات**\n\nشما هنوز هیچ سفارشی ثبت نکرده‌اید.",
                    reply_markup=get_back_button("profile"),
                    parse_mode="Markdown",
                )
                await callback.answer()
                return

            # ساخت متن تاریخچه
            orders_text = self._build_orders_text(orders)

            await callback.message.edit_text(
                text=orders_text,
                reply_markup=get_back_button("profile"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing orders: {e}")
            await callback.answer("⚠️ خطا در نمایش سفارشات.", show_alert=True)

    async def show_level_info(self, callback: CallbackQuery) -> None:
        """
        نمایش اطلاعات سطح و امتیاز کاربر.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # دریافت اطلاعات سطح
            if self._level_upgrade_service:
                progress = await self._level_upgrade_service.get_upgrade_progress(user_id)
            else:
                profile = await self._profile_service.get_profile_by_telegram_id(user_id)
                progress = {
                    "current_level": profile.level.display_name,
                    "current_level_emoji": profile.level.emoji,
                    "next_level": None,
                    "points": profile.points,
                    "points_needed": None,
                    "progress_percentage": 100.0,
                }

            # ساخت متن اطلاعات سطح
            level_text = self._build_level_text(progress)

            await callback.message.edit_text(
                text=level_text,
                reply_markup=get_back_button("profile"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing level info: {e}")
            await callback.answer("⚠️ خطا در نمایش اطلاعات سطح.", show_alert=True)

    async def back_to_profile(self, callback: CallbackQuery) -> None:
        """
        بازگشت به پروفایل.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        await self.show_profile(callback)

    def _build_profile_text(self, profile) -> str:
        """
        ساخت متن پروفایل کاربر.

        Args:
            profile: اطلاعات پروفایل کاربر.

        Returns:
            str: متن پروفایل.
        """
        lines = [
            "👤 **پروفایل کاربری**",
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
            "⭐ **امتیاز و سطح**",
            f"⭐ امتیاز: {profile.points}",
            f"🏅 سطح: {profile.level.emoji} {profile.level.display_name}",
        ])

        if profile.next_level:
            lines.append(
                f"📈 پیشرفت به سطح بعدی: {profile.level_progress:.1f}%"
            )
            if profile.points_to_next_level:
                lines.append(
                    f"🎯 امتیاز مورد نیاز: {profile.points_to_next_level} امتیاز"
                )

        lines.extend([
            "",
            "📊 **آمار**",
            f"🛒 تعداد سفارشات: {profile.total_orders}",
            f"💰 مجموع پرداخت‌ها: {profile.total_spent:,.0f} تومان",
        ])

        if profile.average_order_value:
            lines.append(
                f"📈 میانگین هر سفارش: {profile.average_order_value:,.0f} تومان"
            )

        if profile.last_order_date:
            lines.append(
                f"📅 آخرین سفارش: {profile.last_order_date.strftime('%Y-%m-%d %H:%M')}"
            )

        return "\n".join(lines)

    def _build_orders_text(self, orders) -> str:
        """
        ساخت متن تاریخچه سفارشات.

        Args:
            orders: لیست سفارشات.

        Returns:
            str: متن تاریخچه.
        """
        lines = ["🛒 **تاریخچه سفارشات**", ""]

        for i, order in enumerate(orders, 1):
            status_emoji = {
                "pending": "⏳",
                "paid": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "canceled": "❌",
                "refunded": "💰",
            }.get(order.status.value, "❓")

            lines.extend([
                f"{i}. **سفارش #{order.order_number}**",
                f"   وضعیت: {status_emoji} {order.status.display_name}",
                f"   مبلغ: {order.get_formatted_total()}",
                f"   تاریخ: {order.created_at.strftime('%Y-%m-%d %H:%M')}",
                "",
            ])

        return "\n".join(lines)

    def _build_level_text(self, progress: dict) -> str:
        """
        ساخت متن اطلاعات سطح.

        Args:
            progress: اطلاعات پیشرفت سطح.

        Returns:
            str: متن اطلاعات سطح.
        """
        lines = [
            "🏅 **اطلاعات سطح و امتیاز**",
            "",
            f"سطح فعلی: {progress['current_level_emoji']} **{progress['current_level']}**",
            f"⭐ امتیاز: **{progress['points']}**",
            "",
        ]

        if progress.get("next_level"):
            lines.extend([
                f"🎯 سطح بعدی: {progress['next_level_emoji']} **{progress['next_level']}**",
                f"📈 پیشرفت: {progress['progress_percentage']:.1f}%",
                f"🎯 امتیاز مورد نیاز: {progress.get('points_needed', '???')} امتیاز",
                "",
                "💡 **نکته**: با تکمیل فرم‌ها و سفارشات، امتیاز بیشتری کسب کنید.",
            ])
        else:
            lines.append(
                "👑 **تبریک!** شما در بالاترین سطح هستید."
            )

        return "\n".join(lines)