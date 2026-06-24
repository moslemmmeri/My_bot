# src/admin_panel/modules/error_logs/keyboards/error_logs_menu_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ErrorLogsMenuKeyboard:
    """Keyboard for error logs menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main error logs menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 لیست خطاها",
                        callback_data="admin_errors_list:1"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 آمار خطاها",
                        callback_data="admin_errors_stats"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📈 گزارش خطاها",
                        callback_data="admin_errors_report"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧹 پاک کردن خطاها",
                        callback_data="admin_errors_clear_confirm"
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
    def get_back_keyboard(back_callback: str = "admin_errors") -> InlineKeyboardMarkup:
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