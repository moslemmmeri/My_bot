# src/admin_panel/modules/broadcast/keyboards/filter_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, Dict, Any, List


class FilterKeyboards:
    """Keyboard for broadcast filters in admin panel."""

    @staticmethod
    def get_filter_menu_keyboard() -> InlineKeyboardMarkup:
        """Get main filter menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 فیلتر سطح کاربر",
                        callback_data="admin_broadcast_filter_level"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 فیلتر وضعیت کاربر",
                        callback_data="admin_broadcast_filter_status"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 فیلتر تاریخ ثبت‌نام",
                        callback_data="admin_broadcast_filter_date"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐ فیلتر امتیاز",
                        callback_data="admin_broadcast_filter_points"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛒 فیلتر سفارش‌ها",
                        callback_data="admin_broadcast_filter_orders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧹 پاک کردن همه فیلترها",
                        callback_data="admin_broadcast_clear_filters"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به پیش‌نمایش",
                        callback_data="admin_broadcast_preview"
                    )
                ]
            ]
        )

    @staticmethod
    def get_level_filter_keyboard(
        current_level: Optional[str] = None,
        back_callback: str = "admin_broadcast_filters",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for filtering by user level."""
        levels = [
            ("🥇 طلایی", "gold"),
            ("🥈 نقره‌ای", "silver"),
            ("🥉 برنزی", "bronze"),
            ("⚪ معمولی", "normal"),
            ("🌐 همه", "all"),
        ]
        keyboard = []
        for label, level in levels:
            indicator = " ✅" if current_level == level else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_broadcast_set_level:{level}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_status_filter_keyboard(
        current_status: Optional[str] = None,
        back_callback: str = "admin_broadcast_filters",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for filtering by user status."""
        statuses = [
            ("✅ فعال", "active"),
            ("❌ غیرفعال", "inactive"),
            ("🌐 همه", "all"),
        ]
        keyboard = []
        for label, status in statuses:
            indicator = " ✅" if current_status == status else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_broadcast_set_status:{status}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_date_filter_keyboard(
        current_range: Optional[str] = None,
        back_callback: str = "admin_broadcast_filters",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for filtering by registration date."""
        ranges = [
            ("📅 امروز", "today"),
            ("📅 هفته اخیر", "week"),
            ("📅 ماه اخیر", "month"),
            ("📅 سه ماه اخیر", "quarter"),
            ("📅 سال اخیر", "year"),
            ("🌐 همه", "all"),
        ]
        keyboard = []
        for label, range_name in ranges:
            indicator = " ✅" if current_range == range_name else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_broadcast_set_date:{range_name}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_points_filter_keyboard(
        current_min: Optional[int] = None,
        current_max: Optional[int] = None,
        back_callback: str = "admin_broadcast_filters",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for filtering by points range."""
        keyboard = []
        if current_min is not None and current_max is not None:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"⭐ محدوده: {current_min} تا {current_max}",
                    callback_data="admin_broadcast_filters_points_noop"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    text="⭐ بدون فیلتر امتیاز",
                    callback_data="admin_broadcast_filters_points_noop"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="📈 ۰ تا ۱۰۰",
                callback_data="admin_broadcast_set_points:0:100"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="📈 ۱۰۱ تا ۵۰۰",
                callback_data="admin_broadcast_set_points:101:500"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="📈 ۵۰۱ تا ۱۰۰۰",
                callback_data="admin_broadcast_set_points:501:1000"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="📈 بیش از ۱۰۰۰",
                callback_data="admin_broadcast_set_points:1001:999999"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🧹 پاک کردن فیلتر امتیاز",
                callback_data="admin_broadcast_clear_points"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_orders_filter_keyboard(
        current_filter: Optional[str] = None,
        back_callback: str = "admin_broadcast_filters",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for filtering by order history."""
        filters = [
            ("🛒 دارای سفارش", "has_orders"),
            ("🛒 بدون سفارش", "no_orders"),
            ("🛒 بیش از ۳ سفارش", "orders_gt_3"),
            ("🌐 همه", "all"),
        ]
        keyboard = []
        for label, filter_name in filters:
            indicator = " ✅" if current_filter == filter_name else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_broadcast_set_orders:{filter_name}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_filter_summary_keyboard(
        filters: Dict[str, Any],
        back_callback: str = "admin_broadcast_filters",
    ) -> InlineKeyboardMarkup:
        """Get keyboard showing current filters with options to remove each."""
        keyboard = []

        for key, value in filters.items():
            label = {
                "level": "سطح",
                "status": "وضعیت",
                "date_range": "تاریخ",
                "min_points": "حداقل امتیاز",
                "max_points": "حداکثر امتیاز",
                "orders_filter": "سفارشات",
            }.get(key, key)

            display_value = value
            if key == "level":
                level_names = {"gold": "طلایی", "silver": "نقره‌ای", "bronze": "برنزی", "normal": "معمولی"}
                display_value = level_names.get(value, value)
            elif key == "status":
                status_names = {"active": "فعال", "inactive": "غیرفعال"}
                display_value = status_names.get(value, value)

            keyboard.append([
                InlineKeyboardButton(
                    text=f"❌ {label}: {display_value}",
                    callback_data=f"admin_broadcast_remove_filter:{key}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🧹 پاک کردن همه فیلترها",
                callback_data="admin_broadcast_clear_filters"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به فیلترها",
                callback_data=back_callback
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="✅ ادامه به پیش‌نمایش",
                callback_data="admin_broadcast_preview"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_broadcast") -> InlineKeyboardMarkup:
        """Get simple cancel keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=back_callback
                    )
                ]
            ]
        )