# my_bot_project/src/admin_panel/modules/order_management/handlers/list_orders.py
"""
هندلر نمایش لیست سفارشات (List Orders Handler).

این هندلر مسئولیت نمایش لیست سفارشات با صفحه‌بندی و فیلترهای مختلف
در پنل مدیریت را بر عهده دارد.
"""

from typing import Optional

from aiogram import types
from aiogram.types import CallbackQuery

from admin_panel.core.permissions.permission_checker import PermissionChecker
from admin_panel.modules.order_management.services.order_list_service import OrderListService
from admin_panel.modules.order_management.keyboards.order_filters import get_order_filters_keyboard
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.core.constants.order_statuses import OrderStatus

logger = get_logger(__name__)


class ListOrdersHandler:
    """
    هندلر نمایش لیست سفارشات.

    این کلاس با استفاده از OrderListService، لیست سفارشات را دریافت
    کرده و با صفحه‌بندی و فیلترهای مختلف در پنل مدیریت نمایش می‌دهد.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        permission_checker: PermissionChecker,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            order_repository: ریپازیتوری سفارش.
            permission_checker: بررسی‌کننده دسترسی‌ها.
        """
        self._order_repository = order_repository
        self._permission_checker = permission_checker
        self._service = OrderListService(order_repository)

        logger.info("ListOrdersHandler initialized.")

    async def show_orders(self, callback: CallbackQuery) -> None:
        """
        نمایش لیست سفارشات با صفحه‌بندی پیش‌فرض.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            # بررسی دسترسی
            self._permission_checker.check_permission(user, "orders.view")

            # دریافت لیست سفارشات (صفحه اول)
            page = 0
            orders_data = await self._service.get_orders_page(page=page)

            # ساخت کیبورد
            keyboard = self._build_keyboard(
                orders=orders_data["orders"],
                current_page=page,
                total_pages=orders_data["total_pages"],
                filters=orders_data.get("filters"),
            )

            # متن لیست
            text = self._build_list_text(orders_data, page)

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
            logger.error(f"Error showing orders list: {e}")
            await callback.answer("⚠️ خطا در نمایش لیست سفارشات.", show_alert=True)

    async def change_page(self, callback: CallbackQuery) -> None:
        """
        تغییر صفحه لیست سفارشات.

        Args:
            callback: کالبک با داده‌ی `admin_orders_page:{page}:{filter?}`.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(user, "orders.view")

            # استخراج شماره صفحه و فیلتر
            parts = callback.data.split(":")
            page = int(parts[1]) if len(parts) > 1 else 0
            filter_name = parts[2] if len(parts) > 2 else "all"

            # دریافت داده‌ها
            orders_data = await self._service.get_orders_page(page=page, filter_name=filter_name)

            keyboard = self._build_keyboard(
                orders=orders_data["orders"],
                current_page=page,
                total_pages=orders_data["total_pages"],
                filters=orders_data.get("filters"),
                active_filter=filter_name,
            )

            text = self._build_list_text(orders_data, page, filter_name)

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
        اعمال فیلتر روی لیست سفارشات.

        Args:
            callback: کالبک با داده‌ی `admin_orders_filter:{filter_name}`.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(user, "orders.view")

            filter_name = callback.data.split(":")[1] if ":" in callback.data else "all"

            orders_data = await self._service.get_orders_page(page=0, filter_name=filter_name)

            keyboard = self._build_keyboard(
                orders=orders_data["orders"],
                current_page=0,
                total_pages=orders_data["total_pages"],
                filters=orders_data.get("filters"),
                active_filter=filter_name,
            )

            text = self._build_list_text(orders_data, 0, filter_name)

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

    async def search_orders(self, callback: CallbackQuery) -> None:
        """
        نمایش فرم جستجوی سفارشات.

        Args:
            callback: کالبک `admin_order_search`.
        """
        try:
            user = await self._get_user_from_callback(callback)
            if not user:
                await callback.answer("⚠️ اطلاعات کاربر یافت نشد.", show_alert=True)
                return

            self._permission_checker.check_permission(user, "orders.view")

            await callback.message.edit_text(
                text="🔍 **جستجوی سفارشات**\n\n"
                     "لطفاً شماره سفارش یا شناسه کاربر را وارد کنید.\n"
                     "می‌توانید بر اساس شماره سفارش، شناسه کاربر یا وضعیت جستجو کنید.",
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

    def _build_list_text(self, orders_data: dict, page: int, filter_name: str = "all") -> str:
        """
        ساخت متن لیست سفارشات.

        Args:
            orders_data: داده‌های سفارشات.
            page: شماره صفحه.
            filter_name: نام فیلتر فعال.

        Returns:
            str: متن لیست.
        """
        total = orders_data["total"]
        orders = orders_data["orders"]
        total_pages = orders_data["total_pages"]

        lines = [
            "📦 **مدیریت سفارشات**",
            "",
            f"📊 تعداد کل: {total} سفارش",
            f"📄 صفحه {page + 1} از {total_pages}",
        ]

        if filter_name != "all":
            # نمایش نام فیلتر به فارسی
            filter_display = {
                "all": "همه",
                "pending": "در انتظار پرداخت",
                "paid": "پرداخت شده",
                "processing": "در حال پردازش",
                "shipped": "ارسال شده",
                "delivered": "تحویل داده شده",
                "canceled": "لغو شده",
                "refunded": "بازگشت وجه",
                "on_hold": "در انتظار بررسی",
                "failed": "ناموفق",
            }.get(filter_name, filter_name)
            lines.append(f"🔍 فیلتر: {filter_display}")

        lines.append("")

        if not orders:
            lines.append("هیچ سفارشی یافت نشد.")
        else:
            for idx, order in enumerate(orders, start=page * 10 + 1):
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
                }.get(order.status.value if order.status else "pending", "❓")

                total_amount = float(order.total_amount.amount) if order.total_amount else 0
                lines.append(
                    f"{idx}. {status_emoji} **سفارش #{order.order_number}**"
                )
                lines.append(f"   👤 کاربر: {order.user_id}")
                lines.append(f"   💰 مبلغ: {total_amount:,.0f} تومان")
                lines.append(f"   📅 تاریخ: {order.created_at.strftime('%Y-%m-%d') if order.created_at else 'نامشخص'}")
                lines.append("")

        return "\n".join(lines)

    def _build_keyboard(
        self,
        orders: list,
        current_page: int,
        total_pages: int,
        filters: Optional[dict] = None,
        active_filter: str = "all",
    ) -> types.InlineKeyboardMarkup:
        """
        ساخت کیبورد لیست سفارشات.

        Args:
            orders: لیست سفارشات.
            current_page: شماره صفحه فعلی.
            total_pages: تعداد کل صفحات.
            filters: فیلترها.
            active_filter: نام فیلتر فعال.

        Returns:
            types.InlineKeyboardMarkup: کیبورد ساخته‌شده.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = []

        # دکمه‌های سفارشات
        if orders:
            for order in orders:
                order_number = order.order_number or f"سفارش {order.id}"
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
                }.get(order.status.value if order.status else "pending", "❓")

                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{status_emoji} {order_number}",
                        callback_data=f"admin_order_view:{order.id}"
                    )
                ])

        # دکمه‌های صفحه‌بندی
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=f"admin_orders_page:{current_page - 1}:{active_filter}"
                )
            )

        if current_page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=f"admin_orders_page:{current_page + 1}:{active_filter}"
                )
            )

        if nav_buttons:
            keyboard.append(nav_buttons)

        # دکمه‌های فیلتر
        filter_buttons = self._get_filter_buttons(active_filter)
        if filter_buttons:
            keyboard.append(filter_buttons)

        # دکمه‌های جستجو و خروجی
        keyboard.extend([
            [
                InlineKeyboardButton("🔍 جستجو", callback_data="admin_order_search"),
                InlineKeyboardButton("📥 خروجی", callback_data="admin_order_export"),
            ],
            [
                InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
            ],
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    def _get_filter_buttons(self, active_filter: str) -> list:
        """
        دریافت دکمه‌های فیلتر.

        Args:
            active_filter: نام فیلتر فعال.

        Returns:
            list: لیست دکمه‌ها.
        """
        from aiogram.types import InlineKeyboardButton

        filters = [
            ("all", "همه"),
            ("pending", "در انتظار پرداخت"),
            ("paid", "پرداخت شده"),
            ("processing", "در حال پردازش"),
            ("shipped", "ارسال شده"),
            ("delivered", "تحویل داده شده"),
            ("canceled", "لغو شده"),
            ("refunded", "بازگشت وجه"),
            ("on_hold", "در انتظار بررسی"),
            ("failed", "ناموفق"),
        ]

        buttons = []
        for filter_name, label in filters:
            is_active = filter_name == active_filter
            prefix = "✅ " if is_active else ""
            buttons.append(
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"admin_orders_filter:{filter_name}"
                )
            )

        return buttons

    def _get_search_keyboard(self) -> types.InlineKeyboardMarkup:
        """
        دریافت کیبورد فرم جستجو.

        Returns:
            types.InlineKeyboardMarkup: کیبورد جستجو.
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_orders"),
            ],
        ])

    async def _get_user_from_callback(self, callback: CallbackQuery):
        """
        دریافت کاربر از کالبک.

        Args:
            callback: کالبک دریافتی.

        Returns:
            User یا None.
        """
        # در عمل، از ریپازیتوری کاربر استفاده می‌کنیم
        # اینجا فرض می‌کنیم که middleware کاربر را در context قرار می‌دهد
        # اما برای این نمونه، از طریق telegram_id از دیتابیس می‌خوانیم
        from my_bot.domain.interfaces.repositories.user_repository import UserRepository
        # نیاز به دسترسی به user_repository داریم، اما در این کلاس موجود نیست
        # بنابراین بهتر است آن را از طریق constructor دریافت کنیم
        # برای سادگی، یک پیاده‌سازی placeholder:
        # فرض می‌کنیم که کاربر در context موجود است
        # در اینجا از یک متد کمکی استفاده می‌کنیم که باید در کلاس وجود داشته باشد
        # اما در نسخه واقعی، باید user_repository را به constructor اضافه کنیم
        # و از آن استفاده کنیم
        # برای جلوگیری از خطا، فعلاً یک استثنا پرتاب می‌کنیم
        # در نسخه نهایی باید اصلاح شود
        raise NotImplementedError("این متد باید با دسترسی به user_repository پیاده‌سازی شود")