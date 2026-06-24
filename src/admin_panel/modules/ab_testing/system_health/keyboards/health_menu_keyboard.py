# src/admin_panel/modules/system_health/keyboards/health_menu_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class HealthMenuKeyboard:
    """Keyboard for system health menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main system health menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💚 بررسی سلامت",
                        callback_data="admin_health_check"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 مشاهده متریک‌ها",
                        callback_data="admin_health_metrics"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تاریخچه سلامت",
                        callback_data="admin_health_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به پنل مدیریت",
                        callback_data="admin_panel"
                    )
                ]
            ]
        )

    @staticmethod
    def get_health_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for health check page."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_health_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 مشاهده متریک‌ها",
                        callback_data="admin_health_metrics"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تاریخچه",
                        callback_data="admin_health_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی سلامت",
                        callback_data="admin_health"
                    )
                ]
            ]
        )

    @staticmethod
    def get_metrics_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for metrics page."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_health_metrics_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💚 بررسی سلامت",
                        callback_data="admin_health_check"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی سلامت",
                        callback_data="admin_health"
                    )
                ]
            ]
        )

    @staticmethod
    def get_history_keyboard(page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
        """Get keyboard for health history with pagination."""
        keyboard = []

        # Pagination row
        if total_pages > 1:
            nav_row = []
            if page > 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="⬅️ قبلی",
                        callback_data=f"admin_health_history:{page - 1}"
                    )
                )
            nav_row.append(
                InlineKeyboardButton(
                    text=f"{page}/{total_pages}",
                    callback_data="admin_health_noop"
                )
            )
            if page < total_pages:
                nav_row.append(
                    InlineKeyboardButton(
                        text="➡️ بعدی",
                        callback_data=f"admin_health_history:{page + 1}"
                    )
                )
            keyboard.append(nav_row)

        keyboard.append([
            InlineKeyboardButton(
                text="🔄 بروزرسانی",
                callback_data="admin_health_history_refresh"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🧹 پاک کردن تاریخچه",
                callback_data="admin_health_history_clear_confirm"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به منوی سلامت",
                callback_data="admin_health"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_clear_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Get confirmation keyboard for clearing history."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، پاک شود",
                        callback_data="admin_health_history_clear_execute"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_health_history"
                    )
                ]
            ]
        )

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_health") -> InlineKeyboardMarkup:
        """Get simple back keyboard."""
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