# src/admin_panel/modules/order_management/keyboards/order_filters.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional, Dict, Any


class OrderFiltersKeyboard:
    """Keyboard for filtering orders in admin panel."""

    @staticmethod
    def get_status_filter_keyboard(
        current_status: Optional[str] = None,
        back_callback: str = "admin_orders",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with status filter options."""
        statuses = [
            ("📋 همه", "all"),
            ("⏳ در انتظار", "pending"),
            ("✅ پرداخت شده", "paid"),
            ("📦 ارسال شده", "shipped"),
            ("🚚 تحویل شده", "delivered"),
            ("❌ لغو شده", "cancelled"),
            ("⚠️ ناموفق", "failed"),
        ]

        keyboard = []
        row = []
        for label, status in statuses:
            display = f"{label} {'✓' if current_status == status else ''}"
            row.append(
                InlineKeyboardButton(
                    text=display,
                    callback_data=f"order_filter_status:{status}"
                )
            )
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_date_filter_keyboard(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        back_callback: str = "admin_orders",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with date filter options."""
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📅 امروز",
                    callback_data="order_filter_date:today"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 دیروز",
                    callback_data="order_filter_date:yesterday"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 هفته اخیر",
                    callback_data="order_filter_date:week"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 ماه اخیر",
                    callback_data="order_filter_date:month"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 بازه دلخواه",
                    callback_data="order_filter_date:custom"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data=back_callback
                )
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_filter_menu_keyboard() -> InlineKeyboardMarkup:
        """Get main filter menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 فیلتر بر اساس وضعیت",
                        callback_data="order_filters_status"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 فیلتر بر اساس تاریخ",
                        callback_data="order_filters_date"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👤 فیلتر بر اساس کاربر",
                        callback_data="order_filters_user"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔍 جستجو",
                        callback_data="order_filters_search"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧹 پاک کردن همه فیلترها",
                        callback_data="order_filters_clear"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست سفارشات",
                        callback_data="admin_orders"
                    )
                ]
            ]
        )