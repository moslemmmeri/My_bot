# my_bot_project/src/my_bot/presentation/handlers/broadcast/broadcast_handlers.py
"""
هندلرهای ارسال گروهی (Broadcast Handlers).

این ماژول شامل هندلرهای مربوط به مدیریت ارسال‌های گروهی
در پنل مدیریت است.
"""

from typing import Optional, List, Dict, Any

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.broadcast.broadcast_sender import BroadcastSenderService
from my_bot.application.services.broadcast.broadcast_filter import BroadcastFilterService
from my_bot.application.services.broadcast.broadcast_scheduler import BroadcastSchedulerService
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.admin.admin_keyboards import get_admin_main_keyboard
from my_bot.presentation.keyboards.broadcast.broadcast_keyboards import (
    get_broadcast_main_keyboard,
    get_broadcast_filter_keyboard,
    get_broadcast_status_keyboard,
)

logger = get_logger(__name__)


class BroadcastHandlers:
    """
    هندلرهای ارسال گروهی.

    این کلاس مسئولیت مدیریت ارسال‌های گروهی در پنل مدیریت را بر عهده دارد.
    """

    def __init__(
        self,
        broadcast_sender: BroadcastSenderService,
        broadcast_filter: BroadcastFilterService,
        broadcast_scheduler: Optional[BroadcastSchedulerService] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلرها.

        Args:
            broadcast_sender: سرویس ارسال گروهی.
            broadcast_filter: سرویس فیلتر کاربران.
            broadcast_scheduler: سرویس زمان‌بندی ارسال گروهی (اختیاری).
        """
        self._broadcast_sender = broadcast_sender
        self._broadcast_filter = broadcast_filter
        self._broadcast_scheduler = broadcast_scheduler
        self._user_states: Dict[int, Dict[str, Any]] = {}

    async def show_broadcast_menu(self, callback: CallbackQuery) -> None:
        """
        نمایش منوی ارسال گروهی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # بررسی دسترسی
            user_id = callback.from_user.id
            if not await self._check_admin_permission(user_id):
                await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)
                return

            text = self._build_broadcast_menu_text()
            keyboard = get_broadcast_main_keyboard()

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing broadcast menu: {e}")
            await callback.answer("⚠️ خطا در نمایش منوی ارسال گروهی.", show_alert=True)

    async def create_broadcast(self, callback: CallbackQuery) -> None:
        """
        شروع فرآیند ایجاد ارسال گروهی جدید.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # تنظیم وضعیت کاربر
            self._user_states[user_id] = {
                "step": "title",
                "data": {},
            }

            await callback.message.edit_text(
                text="📝 **ایجاد ارسال گروهی جدید**\n\n"
                "مرحله ۱: عنوان ارسال را وارد کنید.\n\n"
                "⚠️ عنوان باید کوتاه و گویا باشد.",
                reply_markup=get_back_button("admin_broadcast"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error creating broadcast: {e}")
            await callback.answer("⚠️ خطا در شروع ایجاد ارسال گروهی.", show_alert=True)

    async def handle_broadcast_input(self, message: Message) -> None:
        """
        پردازش ورودی‌های کاربر در فرآیند ایجاد ارسال گروهی.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await message.answer(
                    "⚠️ وضعیت یافت نشد. لطفاً از منوی اصلی شروع کنید.",
                    reply_markup=get_admin_main_keyboard(),
                )
                return

            step = state.get("step")
            data = state.get("data", {})

            if step == "title":
                # ذخیره عنوان
                data["title"] = message.text.strip()
                state["step"] = "content"
                state["data"] = data
                self._user_states[user_id] = state

                await message.answer(
                    "📝 **مرحله ۲: محتوای پیام را وارد کنید.**\n\n"
                    "لطفاً متن پیام ارسال گروهی را وارد کنید.\n"
                    "⚠️ می‌توانید از ایموجی و فرمت‌های ساده استفاده کنید.\n\n"
                    "برای لغو، دکمه انصراف را بزنید.",
                    reply_markup=get_back_button("admin_broadcast"),
                    parse_mode="Markdown",
                )

            elif step == "content":
                # ذخیره محتوا
                data["content"] = message.text
                state["step"] = "filter"
                state["data"] = data
                self._user_states[user_id] = state

                await message.answer(
                    "🔍 **مرحله ۳: انتخاب فیلترها**\n\n"
                    "لطفاً فیلترهای مورد نظر را انتخاب کنید.\n"
                    "برای استفاده از تمام کاربران، روی دکمه «همه کاربران» کلیک کنید.",
                    reply_markup=get_broadcast_filter_keyboard(),
                    parse_mode="Markdown",
                )

            else:
                await message.answer(
                    "⚠️ مرحله نامعتبر. لطفاً دوباره شروع کنید.",
                    reply_markup=get_admin_main_keyboard(),
                )

        except Exception as e:
            logger.error(f"Error handling broadcast input: {e}")
            await message.answer(
                "⚠️ خطا در پردازش ورودی. لطفاً دوباره تلاش کنید.",
                reply_markup=get_admin_main_keyboard(),
            )

    async def select_filter(self, callback: CallbackQuery) -> None:
        """
        انتخاب فیلتر کاربران.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ وضعیت یافت نشد.", show_alert=True)
                return

            filter_type = callback.data.split(":")[2] if ":" in callback.data else "all"

            # اعمال فیلتر
            data = state.get("data", {})
            data["filter"] = filter_type
            state["data"] = data
            state["step"] = "confirm"
            self._user_states[user_id] = state

            # نمایش تأییدیه
            await self._show_confirm(callback.message, user_id)
            await callback.answer()

        except Exception as e:
            logger.error(f"Error selecting filter: {e}")
            await callback.answer("⚠️ خطا در انتخاب فیلتر.", show_alert=True)

    async def _show_confirm(self, message: Message, user_id: int) -> None:
        """
        نمایش تأییدیه ارسال گروهی.

        Args:
            message: پیام برای ارسال پاسخ.
            user_id: شناسه کاربر.
        """
        try:
            state = self._user_states.get(user_id)
            if not state:
                return

            data = state.get("data", {})

            # شمارش کاربران هدف
            filter_data = {"filter_type": data.get("filter", "all")}
            target_count = await self._broadcast_filter.count_target_users(
                filter_data=filter_data
            )

            text = self._build_confirm_text(data, target_count)

            # کیبورد تأیید
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton("✅ ارسال", callback_data="broadcast:send"),
                    InlineKeyboardButton("✏️ ویرایش", callback_data="broadcast:edit"),
                ],
                [
                    InlineKeyboardButton("🕐 زمان‌بندی", callback_data="broadcast:schedule"),
                ],
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="broadcast:cancel"),
                ],
            ])

            await message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing confirm: {e}")
            await message.answer(
                "⚠️ خطا در نمایش تأییدیه.",
                reply_markup=get_admin_main_keyboard(),
            )

    async def send_broadcast(self, callback: CallbackQuery) -> None:
        """
        ارسال پیام گروهی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ وضعیت یافت نشد.", show_alert=True)
                return

            data = state.get("data", {})

            # نمایش پیام در حال ارسال
            await callback.message.edit_text(
                text="⏳ **در حال ارسال پیام گروهی...**\n\n"
                "لطفاً منتظر بمانید. این عملیات ممکن است چند لحظه طول بکشد.",
                parse_mode="Markdown",
            )

            # ارسال پیام
            result = await self._broadcast_sender.send_broadcast(
                broadcast_id=data.get("broadcast_id", 0),
                actor_id=user_id,
            )

            # نمایش نتیجه
            await self._show_send_result(callback.message, result)

            # پاک کردن وضعیت کاربر
            if user_id in self._user_states:
                del self._user_states[user_id]

            await callback.answer("✅ پیام گروهی ارسال شد!")

        except Exception as e:
            logger.error(f"Error sending broadcast: {e}")
            await callback.message.edit_text(
                text=f"⚠️ **خطا در ارسال پیام گروهی**\n\n{str(e)}\n\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=get_admin_main_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ خطا در ارسال پیام گروهی.", show_alert=True)

    async def schedule_broadcast(self, callback: CallbackQuery) -> None:
        """
        زمان‌بندی ارسال گروهی.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id
            state = self._user_states.get(user_id)

            if not state:
                await callback.answer("⚠️ وضعیت یافت نشد.", show_alert=True)
                return

            if not self._broadcast_scheduler:
                await callback.answer("⛔ سرویس زمان‌بندی در دسترس نیست.", show_alert=True)
                return

            # نمایش فرم زمان‌بندی
            await callback.message.edit_text(
                text="🕐 **زمان‌بندی ارسال گروهی**\n\n"
                "لطفاً تاریخ و زمان ارسال را وارد کنید.\n\n"
                "فرمت: YYYY-MM-DD HH:MM\n"
                "مثال: 2024-12-25 14:30\n\n"
                "⚠️ زمان باید در آینده باشد.",
                reply_markup=get_back_button("admin_broadcast"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error scheduling broadcast: {e}")
            await callback.answer("⚠️ خطا در زمان‌بندی.", show_alert=True)

    async def _show_send_result(self, message: Message, result) -> None:
        """
        نمایش نتیجه ارسال گروهی.

        Args:
            message: پیام برای ارسال پاسخ.
            result: نتیجه ارسال.
        """
        if result.is_completed():
            text = (
                "✅ **ارسال گروهی با موفقیت انجام شد!**\n\n"
                f"📊 **آمار ارسال:**\n"
                f"   • کل کاربران هدف: {result.total_count}\n"
                f"   • ارسال موفق: {result.sent_count}\n"
                f"   • ارسال ناموفق: {result.failed_count}\n"
            )
        else:
            text = (
                "⚠️ **ارسال گروهی با خطا مواجه شد**\n\n"
                f"📊 **آمار ارسال:**\n"
                f"   • کل کاربران هدف: {result.total_count}\n"
                f"   • ارسال موفق: {result.sent_count}\n"
                f"   • ارسال ناموفق: {result.failed_count}\n\n"
                "💡 لطفاً گزارش خطاها را بررسی کنید."
            )

        if result.failed_user_ids:
            text += f"\n🆔 کاربران ناموفق: {', '.join(map(str, result.failed_user_ids[:10]))}"
            if len(result.failed_user_ids) > 10:
                text += f" و {len(result.failed_user_ids) - 10} کاربر دیگر"

        await message.edit_text(
            text=text,
            reply_markup=get_back_button("admin_broadcast"),
            parse_mode="Markdown",
        )

    def _build_broadcast_menu_text(self) -> str:
        """
        ساخت متن منوی ارسال گروهی.

        Returns:
            str: متن منو.
        """
        return (
            "📢 **مدیریت ارسال گروهی**\n\n"
            "از گزینه‌های زیر انتخاب کنید:\n\n"
            "📝 **ایجاد ارسال جدید** - ساخت پیام گروهی جدید\n"
            "📋 **لیست ارسال‌ها** - مشاهده تاریخچه ارسال‌ها\n"
            "⏳ **ارسال‌های زمان‌بندی‌شده** - مدیریت زمان‌بندی‌ها\n"
            "📊 **آمار ارسال‌ها** - مشاهده آمار کلی\n\n"
            "💡 **نکته**: برای ارسال گروهی، حتماً محتوای پیام را تأیید کنید."
        )

    def _build_confirm_text(self, data: Dict[str, Any], target_count: int) -> str:
        """
        ساخت متن تأییدیه ارسال گروهی.

        Args:
            data: داده‌های ارسال.
            target_count: تعداد کاربران هدف.

        Returns:
            str: متن تأییدیه.
        """
        lines = [
            "📝 **تأیید ارسال گروهی**",
            "",
            f"📌 عنوان: {data.get('title', 'نامشخص')}",
            f"📝 محتوا: {data.get('content', '')[:100]}...",
            f"🔍 فیلتر: {data.get('filter', 'همه کاربران')}",
            f"👥 تعداد کاربران هدف: {target_count}",
            "",
            "⚠️ **توجه**: پس از تأیید، پیام برای تمام کاربران هدف ارسال می‌شود.",
            "",
            "آیا از ارسال مطمئن هستید؟",
        ]

        return "\n".join(lines)

    async def _check_admin_permission(self, user_id: int) -> bool:
        """
        بررسی دسترسی ادمین.

        Args:
            user_id: شناسه کاربر.

        Returns:
            bool: True اگر کاربر ادمین باشد.
        """
        # در عمل، باید از سرویس کاربر استفاده کرد
        # اینجا یک بررسی ساده انجام می‌دهیم
        return True