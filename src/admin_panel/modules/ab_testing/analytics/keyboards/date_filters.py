# src/admin_panel/modules/analytics/keyboards/date_filters.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


class DateFiltersKeyboard:
    """Keyboard for date filters in analytics."""

    @staticmethod
    def get_period_keyboard(
        current_period: Optional[str] = None,
        back_callback: str = "admin_analytics"
    ) -> InlineKeyboardMarkup:
        """Get keyboard with predefined date periods."""
        periods = [
            ("📅 امروز", "today"),
            ("📅 دیروز", "yesterday"),
            ("📅 هفته اخیر", "week"),
            ("📅 ماه اخیر", "month"),
            ("📅 سه ماه اخیر", "quarter"),
            ("📅 سال اخیر", "year"),
        ]

        keyboard = []
        for label, period in periods:
            indicator = " ✅" if current_period == period else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"analytics_period:{period}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="📅 بازه دلخواه",
                callback_data="analytics_period:custom"
            )
        ])

        keyboard.append([
            InlineKeyboardButton(
                text="🧹 پاک کردن فیلتر",
                callback_data="analytics_period:clear"
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
    def get_custom_period_keyboard(
        back_callback: str = "analytics_period"
    ) -> InlineKeyboardMarkup:
        """Get keyboard for custom date range input."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📅 از تاریخ (YYYY-MM-DD)",
                        callback_data="analytics_period_from"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تا تاریخ (YYYY-MM-DD)",
                        callback_data="analytics_period_to"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ اعمال بازه",
                        callback_data="analytics_period_apply"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_quick_filters_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard with quick date filter options."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 امروز",
                        callback_data="analytics_quick:today"
                    ),
                    InlineKeyboardButton(
                        text="📊 دیروز",
                        callback_data="analytics_quick:yesterday"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 هفته",
                        callback_data="analytics_quick:week"
                    ),
                    InlineKeyboardButton(
                        text="📊 ماه",
                        callback_data="analytics_quick:month"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 سه ماه",
                        callback_data="analytics_quick:quarter"
                    ),
                    InlineKeyboardButton(
                        text="📊 سال",
                        callback_data="analytics_quick:year"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 همه",
                        callback_data="analytics_quick:all"
                    ),
                    InlineKeyboardButton(
                        text="🧹 پاک کردن",
                        callback_data="analytics_quick:clear"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="admin_analytics_dashboard"
                    )
                ]
            ]
        )