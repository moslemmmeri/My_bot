# src/admin_panel/modules/behavior_analytics/keyboards/behavior_filter_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List, Dict, Any


class BehaviorFilterKeyboard:
    """Keyboard for behavior analytics filters in admin panel."""

    @staticmethod
    def get_period_keyboard(
        current_period: Optional[str] = None,
        back_callback: str = "admin_behavior",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with predefined time periods."""
        periods = [
            ("📅 امروز", "today"),
            ("📅 هفته اخیر", "week"),
            ("📅 ماه اخیر", "month"),
            ("📅 سه ماه اخیر", "quarter"),
            ("📅 سال اخیر", "year"),
            ("📅 همه", "all"),
        ]
        keyboard = []
        for label, period in periods:
            indicator = " ✅" if current_period == period else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_behavior_period:{period}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="📅 بازه دلخواه",
                callback_data="admin_behavior_period_custom"
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
    def get_filter_menu_keyboard() -> InlineKeyboardMarkup:
        """Get main filter menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👥 فیلتر کاربران",
                        callback_data="admin_behavior_filter_users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 فیلتر رفتار",
                        callback_data="admin_behavior_filter_behavior"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📈 فیلتر تعاملات",
                        callback_data="admin_behavior_filter_interactions"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔍 فیلتر مسیرها",
                        callback_data="admin_behavior_filter_paths"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧹 پاک کردن فیلترها",
                        callback_data="admin_behavior_filters_clear"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی رفتار",
                        callback_data="admin_behavior"
                    )
                ]
            ]
        )

    @staticmethod
    def get_user_filter_keyboard(
        current_filters: Optional[Dict[str, Any]] = None,
    ) -> InlineKeyboardMarkup:
        """Get keyboard for user filters."""
        current = current_filters or {}
        keyboard = []

        # Status filter
        status_options = [
            ("✅ فعال", "active"),
            ("❌ غیرفعال", "inactive"),
            ("🌐 همه", "all"),
        ]
        status_row = []
        for label, status in status_options:
            indicator = " ✓" if current.get("status") == status else ""
            status_row.append(
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_behavior_filter_user_status:{status}"
                )
            )
        keyboard.append(status_row)

        # Level filter
        level_options = [
            ("🥇 طلایی", "gold"),
            ("🥈 نقره‌ای", "silver"),
            ("🥉 برنزی", "bronze"),
            ("⚪ معمولی", "normal"),
        ]
        level_row = []
        for label, level in level_options:
            indicator = " ✓" if current.get("level") == level else ""
            level_row.append(
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_behavior_filter_user_level:{level}"
                )
            )
        keyboard.append(level_row)

        # Action buttons
        keyboard.append([
            InlineKeyboardButton(
                text="🔍 اعمال فیلترها",
                callback_data="admin_behavior_apply_filters"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="admin_behavior_filter"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_behavior_filter_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for behavior filters."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 نرخ بازگشت",
                        callback_data="admin_behavior_filter_return_rate"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 نرخ تبدیل",
                        callback_data="admin_behavior_filter_conversion"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⏱️ مدت جلسه",
                        callback_data="admin_behavior_filter_session_duration"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔢 تعداد جلسات",
                        callback_data="admin_behavior_filter_session_count"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="admin_behavior_filter"
                    )
                ]
            ]
        )

    @staticmethod
    def get_interaction_filter_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for interaction filters."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 پیام‌ها",
                        callback_data="admin_behavior_filter_messages"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛒 سفارشات",
                        callback_data="admin_behavior_filter_orders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⭐ بازخوردها",
                        callback_data="admin_behavior_filter_feedback"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎫 تیکت‌ها",
                        callback_data="admin_behavior_filter_tickets"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="admin_behavior_filter"
                    )
                ]
            ]
        )

    @staticmethod
    def get_path_filter_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for path filters."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📍 مسیرهای پرتکرار",
                        callback_data="admin_behavior_filter_common_paths"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚪 نقاط خروج",
                        callback_data="admin_behavior_filter_exit_points"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎯 مسیرهای تبدیل",
                        callback_data="admin_behavior_filter_conversion_paths"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📉 مسیرهای ریزش",
                        callback_data="admin_behavior_filter_dropoff_paths"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="admin_behavior_filter"
                    )
                ]
            ]
        )

    @staticmethod
    def get_empty_keyboard(back_callback: str = "admin_behavior") -> InlineKeyboardMarkup:
        """Get keyboard when no data found."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_clear_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Get confirmation keyboard for clearing filters."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، پاک شود",
                        callback_data="admin_behavior_filters_clear_confirm"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_behavior_filter"
                    )
                ]
            ]
        )

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_behavior") -> InlineKeyboardMarkup:
        """Get simple cancel/back keyboard."""
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