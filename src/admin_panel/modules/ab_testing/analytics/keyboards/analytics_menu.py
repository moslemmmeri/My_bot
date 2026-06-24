# src/admin_panel/modules/analytics/keyboards/analytics_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class AnalyticsMenuKeyboard:
    """Keyboard for analytics menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main analytics menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 داشبورد",
                        callback_data="admin_analytics_dashboard"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📈 گزارش فروش",
                        callback_data="admin_analytics_reports:sales"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 گزارش کاربران",
                        callback_data="admin_analytics_reports:users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💳 گزارش پرداخت‌ها",
                        callback_data="admin_analytics_reports:payments"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📦 گزارش سفارشات",
                        callback_data="admin_analytics_reports:orders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 گزارش رفتار کاربران",
                        callback_data="admin_analytics_reports:behavior"
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
    def get_dashboard_keyboard() -> InlineKeyboardMarkup:
        """Get dashboard keyboard with quick actions."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_analytics_dashboard_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📥 خروجی PDF",
                        callback_data="admin_analytics_dashboard_export_pdf"
                    ),
                    InlineKeyboardButton(
                        text="📥 خروجی Excel",
                        callback_data="admin_analytics_dashboard_export_excel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 گزارش‌های کامل",
                        callback_data="admin_analytics_reports"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی تحلیل",
                        callback_data="admin_analytics"
                    )
                ]
            ]
        )

    @staticmethod
    def get_report_keyboard(report_type: str) -> InlineKeyboardMarkup:
        """Get keyboard for specific report with export options."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 خروجی Excel",
                        callback_data=f"admin_analytics_export_excel:{report_type}"
                    ),
                    InlineKeyboardButton(
                        text="📥 خروجی PDF",
                        callback_data=f"admin_analytics_export_pdf:{report_type}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تغییر بازه زمانی",
                        callback_data=f"admin_analytics_period:{report_type}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست گزارش‌ها",
                        callback_data="admin_analytics_reports"
                    )
                ]
            ]
        )

    @staticmethod
    def get_period_keyboard(report_type: str) -> InlineKeyboardMarkup:
        """Get period selection keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📅 امروز",
                        callback_data=f"admin_analytics_report:{report_type}:today"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 دیروز",
                        callback_data=f"admin_analytics_report:{report_type}:yesterday"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 هفته اخیر",
                        callback_data=f"admin_analytics_report:{report_type}:week"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 ماه اخیر",
                        callback_data=f"admin_analytics_report:{report_type}:month"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 سه ماه اخیر",
                        callback_data=f"admin_analytics_report:{report_type}:quarter"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 سال اخیر",
                        callback_data=f"admin_analytics_report:{report_type}:year"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به گزارش",
                        callback_data=f"admin_analytics_reports:{report_type}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_export_keyboard(report_type: str, format_type: str) -> InlineKeyboardMarkup:
        """Get export keyboard with confirmation."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ تایید خروجی {format_type.upper()}",
                        callback_data=f"admin_analytics_export_confirm:{report_type}:{format_type}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"admin_analytics_reports:{report_type}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی تحلیل",
                        callback_data="admin_analytics"
                    )
                ]
            ]
        )