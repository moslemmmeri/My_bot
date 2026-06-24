# my_bot_project/src/admin_panel/modules/order_management/handlers/view_order.py
"""
هندلر مشاهده سفارش (View Order Handler).

این هندلر مسئولیت نمایش اطلاعات کامل یک سفارش خاص در پنل مدیریت را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import CallbackQuery

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.modules.order_management.keyboards.order_actions import get_order_actions_keyboard
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.not_found_errors import OrderNotFoundError
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.core.constants.order_statuses import OrderStatus

logger = get_logger(__name__)


class ViewOrderHandler:
    """
    هندلر مشاهده اطلاعات سفارش.

    این کلاس با استفاده از OrderRepository و UserRepository،
    اطلاعات کامل یک سفارش را دریافت و در پنل مدیریت نمایش می‌دهد.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        permission_checker: PermissionChecker,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            order_repository: ریپازیتوری سفارش.
            user_repository: ریپازیتوری کاربر.
            permission_checker: بررسی‌کننده دسترسی‌ها.
        """
        self._order_repository = order_repository
        self._user_repository = user_repository
        self._permission_checker = permission_checker

        logger.info("ViewOrderHandler initialized.")

    async def view_order(self, callback: CallbackQuery) -> None:
        """
        نمایش اطلاعات کامل یک سفارش.

        Args:
            callback: کالبک با داده‌ی `admin_order_view:{order_id}`.
        """
        try:
            # استخراج شناسه سفارش
            order_id = int(callback.data.split(":")[1]) if ":" in callback.data else 0
            if order_id <= 0:
                await callback.answer("⚠️ شناسه سفارش نامعتبر است.", show_alert=True)
                return

            # بررسی دسترسی کاربر جاری
            current_user = await self._get_user_from_callback(callback)
            if not current_user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(current_user, "orders.view")

            # دریافت سفارش
            order = await self._order_repository.get_by_id(order_id)
            if not order:
                raise OrderNotFoundError(order_id=str(order_id))

            # دریافت اطلاعات کاربر (در صورت وجود)
            user = await self._user_repository.get_by_id(order.user_id)
            user_name = user.full_name if user else f"کاربر {order.user_id}"
            user_username = f"@{user.username}" if user and user.username else "ندارد"

            # ساخت متن و کیبورد
            text = self._build_order_detail_text(order, user_name, user_username)
            keyboard = get_order_actions_keyboard(order_id, order.status)

            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer()

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied: {e}")
            await callback.answer("⛔ شما دسترسی به این بخش را ندارید.", show_alert=True)

        except OrderNotFoundError as e:
            logger.warning(f"Order not found: {e}")
            await callback.answer("⚠️ سفارش مورد نظر یافت نشد.", show_alert=True)

        except Exception as e:
            logger.error(f"Error viewing order {order_id}: {e}")
            await callback.answer("⚠️ خطا در نمایش اطلاعات سفارش.", show_alert=True)

    def _build_order_detail_text(self, order, user_name: str, user_username: str) -> str:
        """
        ساخت متن اطلاعات کامل سفارش.

        Args:
            order: موجودیت سفارش.
            user_name: نام کاربر.
            user_username: نام کاربری.

        Returns:
            str: متن اطلاعات سفارش.
        """
        status_emoji = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.PAID: "✅",
            OrderStatus.PROCESSING: "🔄",
            OrderStatus.SHIPPED: "🚚",
            OrderStatus.DELIVERED: "📦",
            OrderStatus.CANCELED: "❌",
            OrderStatus.REFUNDED: "💰",
            OrderStatus.ON_HOLD: "🔍",
            OrderStatus.FAILED: "⚠️",
        }.get(order.status, "❓")

        status_display = order.status.get_display_name() if order.status else "نامشخص"

        lines = [
            f"🧾 **جزئیات سفارش**",
            "",
            f"🆔 شناسه: `{order.id}`",
            f"📋 شماره سفارش: `{order.order_number}`",
            f"📌 وضعیت: {status_emoji} {status_display}",
            "",
            f"👤 کاربر: {user_name} ({user_username})",
            f"🆔 شناسه کاربر: `{order.user_id}`",
            "",
            "🛒 **آیتم‌ها:**",
        ]

        # نمایش آیتم‌های سفارش
        if order.items:
            for idx, item in enumerate(order.items, 1):
                unit_price = float(item.unit_price.amount) if item.unit_price else 0
                total_price = float(item.total_price.amount) if item.total_price else 0
                lines.append(
                    f"{idx}. {item.product_name} × {item.quantity} = "
                    f"{total_price:,.0f} تومان (قیمت واحد: {unit_price:,.0f} تومان)"
                )
        else:
            lines.append("هیچ آیتمی در این سفارش وجود ندارد.")

        lines.extend([
            "",
            "💰 **مبالغ:**",
            f"مبلغ پایه: {float(order.subtotal.amount):,.0f} تومان" if order.subtotal else "مبلغ پایه: ۰",
        ])

        if order.discount_amount and float(order.discount_amount.amount) > 0:
            lines.append(f"تخفیف: -{float(order.discount_amount.amount):,.0f} تومان")

        lines.append(f"**مبلغ کل: {float(order.total_amount.amount):,.0f} تومان**")

        if order.coupon_code:
            lines.append(f"🎫 کد تخفیف: `{order.coupon_code}`")

        if order.payment_id:
            lines.append(f"💳 شناسه پرداخت: `{order.payment_id}`")

        if order.shipping_address:
            lines.extend([
                "",
                "📮 **آدرس تحویل:**",
                f"{order.shipping_address}",
            ])

        if order.tracking_code:
            lines.extend([
                "",
                "📦 **کد رهگیری:**",
                f"`{order.tracking_code}`",
            ])

        if order.notes:
            lines.extend([
                "",
                "📝 **یادداشت:**",
                f"{order.notes}",
            ])

        lines.extend([
            "",
            f"📅 تاریخ ایجاد: {order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'نامشخص'}",
            f"🔄 آخرین به‌روزرسانی: {order.updated_at.strftime('%Y-%m-%d %H:%M') if order.updated_at else 'نامشخص'}",
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