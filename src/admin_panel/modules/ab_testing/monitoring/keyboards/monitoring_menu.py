# src/admin_panel/modules/monitoring/keyboards/monitoring_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


class MonitoringMenuKeyboard:
    """Keyboard for monitoring menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main monitoring menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🖥️ وضعیت سیستم",
                        callback_data="admin_monitoring_status"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚡ عملکرد سیستم",
                        callback_data="admin_monitoring_performance"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 مصرف منابع",
                        callback_data="admin_monitoring_resources"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_monitoring_refresh"
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
    def get_status_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for system status page."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_monitoring_status_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی پایش",
                        callback_data="admin_monitoring"
                    )
                ]
            ]
        )

    @staticmethod
    def get_performance_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for performance page."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_monitoring_performance_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 جزئیات بیشتر",
                        callback_data="admin_monitoring_performance_details"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی پایش",
                        callback_data="admin_monitoring"
                    )
                ]
            ]
        )

    @staticmethod
    def get_resource_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard for resource usage page."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_monitoring_resources_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 نمودار مصرف",
                        callback_data="admin_monitoring_resources_chart"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی پایش",
                        callback_data="admin_monitoring"
                    )
                ]
            ]
        )

    @staticmethod
    def get_refresh_keyboard() -> InlineKeyboardMarkup:
        """Get simple refresh keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_monitoring_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="admin_monitoring"
                    )
                ]
            ]
        )

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_monitoring") -> InlineKeyboardMarkup:
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