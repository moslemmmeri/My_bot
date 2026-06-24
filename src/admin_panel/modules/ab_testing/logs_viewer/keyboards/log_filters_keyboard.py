# src/admin_panel/modules/logs_viewer/keyboards/log_filters_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List


class LogFiltersKeyboard:
    """Keyboard for filtering log files in admin panel."""

    @staticmethod
    def get_filter_keyboard(back_callback: str = "admin_logs") -> InlineKeyboardMarkup:
        """Get main filter selection keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 فیلتر بر اساس سطح",
                        callback_data="admin_logs_filter_level"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 فیلتر بر اساس تاریخ",
                        callback_data="admin_logs_filter_date"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔍 جستجو در لاگ",
                        callback_data="admin_logs_search"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧹 پاک کردن همه فیلترها",
                        callback_data="admin_logs_clear_filters"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_level_filter_keyboard(
        current_level: Optional[str] = None,
        back_callback: str = "admin_logs_filter",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for selecting log level."""
        levels = [
            ("🚨 ERROR", "ERROR"),
            ("⚠️ WARNING", "WARNING"),
            ("ℹ️ INFO", "INFO"),
            ("🐛 DEBUG", "DEBUG"),
            ("📋 همه", "ALL"),
        ]
        keyboard = []
        for label, level in levels:
            indicator = " ✅" if current_level == level else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_logs_set_level:{level}"
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
        back_callback: str = "admin_logs_filter",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for selecting date range."""
        ranges = [
            ("📅 امروز", "today"),
            ("📅 دیروز", "yesterday"),
            ("📅 هفته اخیر", "week"),
            ("📅 ماه اخیر", "month"),
            ("📅 همه", "all"),
        ]
        keyboard = []
        for label, range_name in ranges:
            indicator = " ✅" if current_range == range_name else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_logs_set_date:{range_name}"
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
    def get_search_keyboard(back_callback: str = "admin_logs_filter") -> InlineKeyboardMarkup:
        """Get keyboard for search action."""
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

    @staticmethod
    def get_empty_keyboard(back_callback: str = "admin_logs") -> InlineKeyboardMarkup:
        """Get keyboard when no logs found."""
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
    def get_clear_filter_keyboard(back_callback: str = "admin_logs") -> InlineKeyboardMarkup:
        """Get keyboard confirming clear filters."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، پاک شود",
                        callback_data="admin_logs_clear_filters_confirm"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_logs") -> InlineKeyboardMarkup:
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