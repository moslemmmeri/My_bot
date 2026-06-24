# my_bot_project/src/my_bot/presentation/handlers/user/order_history_handler.py
"""
هندلر تاریخچه سفارشات (Order History Handler).

این هندلر مسئولیت نمایش تاریخچه سفارشات کاربر، فیلتر کردن بر اساس وضعیت
و نمایش جزئیات هر سفارش را بر عهده دارد.
"""

from typing import Optional, List

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.order.order_history import OrderHistoryService
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.order.order_filters import get_order_filters_keyboard
from my_bot.presentation.keyboards.order.order_actions import get_order_actions_keyboard

logger = get_logger(__name__)


class OrderHistoryHandler:
    """
    هندلر تاریخچه سفارشات.

    این کلاس مسئولیت نمایش تاریخچه سفارشات کاربر را بر عهده دارد.
    """

    def __init__(self, order_history_service: OrderHistoryService) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            order_history_service: سرویس تاریخچه سفارشات.
        """
        self._order_history_service = order_history_service

    async def show_orders(
        self,
        callback: CallbackQuery,
        status: Optional[OrderStatus] = None,
        page: int = 0,
    ) -> None:
        """
        نمایش لیست سفارشات کاربر.

        Args:
            callback: کالبک دریافتی از تلگرام.
            status: فیلتر بر اساس وضعیت (اختیاری).
            page: شماره صفحه (پیش‌فرض ۰).
        """
        try:
            user_id = callback.from_user.id
            limit = 5
            skip = page * limit

            # دریافت سفارشات
            orders = await self._order_history_service.get_user_orders(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status=status,
            )

            if not orders:
                text = "🛒 **تاریخچه سفارشات**\n\n"
                text += "شما هنوز هیچ سفارشی ثبت نکرده‌اید."
                if status:
                    text += f"\n\nفیلتر: {status.display_name}"

                await callback.message.edit_text(
                    text=text,
                    reply_markup=get_back_button("profile"),
                    parse_mode="Markdown",
                )
                await callback.answer()
                return

            # ساخت متن سفارشات
            text = self._build_orders_text(orders, status, page)

            # ساخت کیبورد
            keyboard = self._build_keyboard(status, page, len(orders) == limit)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing orders: {e}")
            await callback.answer("⚠️ خطا در نمایش سفارشات.", show_alert=True)

    async def show_order_detail(self, callback: CallbackQuery) -> None:
        """
        نمایش جزئیات یک سفارش خاص.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            # استخراج شناسه سفارش از کالبک
            order_id = int(callback.data.split(":")[1])
            user_id = callback.from_user.id

            # دریافت جزئیات سفارش
            order = await self._order_history_service.get_order_details(
                order_id=order_id,
                user_id=user_id,
            )

            # ساخت متن جزئیات
            text = self._build_order_detail_text(order)

            # دکمه‌های اقدام
            keyboard = get_order_actions_keyboard(order_id, order.status)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing order detail: {e}")
            await callback.answer("⚠️ خطا در نمایش جزئیات سفارش.", show_alert=True)

    async def filter_orders(self, callback: CallbackQuery) -> None:
        """
        نمایش فیلترهای سفارشات.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            await callback.message.edit_text(
                text="🔍 **فیلتر سفارشات**\n\n"
                "وضعیت مورد نظر را انتخاب کنید:",
                reply_markup=get_order_filters_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing order filters: {e}")
            await callback.answer("⚠️ خطا در نمایش فیلترها.", show_alert=True)

    async def back_to_orders(
        self,
        callback: CallbackQuery,
        status: Optional[OrderStatus] = None,
        page: int = 0,
    ) -> None:
        """
        بازگشت به لیست سفارشات.

        Args:
            callback: کالبک دریافتی از تلگرام.
            status: وضعیت فیلتر (اختیاری).
            page: شماره صفحه (اختیاری).
        """
        await self.show_orders(callback, status, page)

    def _build_orders_text(
        self,
        orders: List,
        status: Optional[OrderStatus] = None,
        page: int = 0,
    ) -> str:
        """
        ساخت متن لیست سفارشات.

        Args:
            orders: لیست سفارشات.
            status: وضعیت فیلتر.
            page: شماره صفحه.

        Returns:
            str: متن لیست سفارشات.
        """
        lines = ["🛒 **تاریخچه سفارشات**", ""]

        if status:
            lines.append(f"📌 فیلتر: {status.display_name}\n")

        for i, order in enumerate(orders, 1):
            status_emoji = {
                "pending": "⏳",
                "paid": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "canceled": "❌",
                "refunded": "💰",
                "on_hold": "🔍",
                "failed": "⚠️",
            }.get(order.status.value, "❓")

            items_summary = ", ".join([
                f"{item.product_name} (x{item.quantity})"
                for item in order.items[:2]
            ])
            if len(order.items) > 2:
                items_summary += f" و {len(order.items) - 2} آیتم دیگر"

            lines.extend([
                f"{i}. **سفارش #{order.order_number}**",
                f"   📦 {items_summary}",
                f"   💰 {order.get_formatted_total()}",
                f"   📌 {status_emoji} {order.status.display_name}",
                f"   📅 {order.created_at.strftime('%Y-%m-%d %H:%M')}",
                "",
            ])

        if page > 0:
            lines.append(f"📄 صفحه {page + 1}")

        return "\n".join(lines)

    def _build_order_detail_text(self, order) -> str:
        """
        ساخت متن جزئیات سفارش.

        Args:
            order: اطلاعات سفارش.

        Returns:
            str: متن جزئیات سفارش.
        """
        lines = [
            f"🧾 **جزئیات سفارش #{order.order_number}**",
            "",
            "📌 **اطلاعات کلی**",
            f"   وضعیت: {order.status.emoji} {order.status.display_name}",
            f"   تاریخ: {order.created_at.strftime('%Y-%m-%d %H:%M')}",
        ]

        if order.payment_id:
            lines.append(f"   💳 شناسه پرداخت: `{order.payment_id}`")
        if order.tracking_code:
            lines.append(f"   📦 کد رهگیری: `{order.tracking_code}`")

        lines.extend([
            "",
            "🛒 **آیتم‌ها**",
        ])

        for item in order.items:
            lines.append(
                f"   • {item.product_name} × {item.quantity} = "
                f"{item.total_price:,.0f} تومان"
            )

        lines.extend([
            "",
            "💰 **مبالغ**",
            f"   مبلغ پایه: {order.subtotal:,.0f} تومان",
        ])

        if order.discount_amount > 0:
            lines.append(f"   تخفیف: -{order.discount_amount:,.0f} تومان")

        lines.append(f"   **مبلغ کل: {order.total_amount:,.0f} تومان**")

        if order.coupon_code:
            lines.append(f"   🎫 کد تخفیف: `{order.coupon_code}`")

        if order.shipping_address:
            lines.extend([
                "",
                "📮 **آدرس تحویل**",
                f"   {order.shipping_address}",
            ])

        if order.notes:
            lines.extend([
                "",
                "📝 **یادداشت**",
                f"   {order.notes}",
            ])

        return "\n".join(lines)

    def _build_keyboard(
        self,
        status: Optional[OrderStatus] = None,
        page: int = 0,
        has_more: bool = False,
    ) -> types.InlineKeyboardMarkup:
        """
        ساخت کیبورد برای لیست سفارشات.

        Args:
            status: وضعیت فیلتر.
            page: شماره صفحه.
            has_more: آیا صفحات بعدی وجود دارد.

        Returns:
            types.InlineKeyboardMarkup: کیبورد ساخته‌شده.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        buttons = []

        # دکمه‌های صفحه‌بندی
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    "⬅️ قبلی",
                    callback_data=f"orders:page:{status.value if status else 'all'}:{page - 1}"
                )
            )
        if has_more:
            nav_buttons.append(
                InlineKeyboardButton(
                    "➡️ بعدی",
                    callback_data=f"orders:page:{status.value if status else 'all'}:{page + 1}"
                )
            )
        if nav_buttons:
            buttons.append(nav_buttons)

        # دکمه‌های فیلتر
        buttons.append([
            InlineKeyboardButton("🔍 فیلتر", callback_data="orders:filter"),
        ])

        # دکمه بازگشت
        buttons.append([
            InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile"),
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)