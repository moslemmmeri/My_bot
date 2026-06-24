# src/admin_panel/ui/main_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Get the main admin panel keyboard with all management options."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 مدیریت کاربران",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 مدیریت سفارشات",
                    callback_data="admin_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 آمار و تحلیل",
                    callback_data="admin_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✉️ ارسال گروهی",
                    callback_data="admin_broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 مدیریت محتوا",
                    callback_data="admin_content"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ تنظیمات",
                    callback_data="admin_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📑 لاگ‌ها",
                    callback_data="admin_logs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚨 خطاها",
                    callback_data="admin_errors"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏷️ مدیریت فیچرها",
                    callback_data="admin_features"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎫 مدیریت تیکت‌ها",
                    callback_data="admin_tickets"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 مدیریت کوپن‌ها",
                    callback_data="admin_coupons"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 پشتیبان‌گیری",
                    callback_data="admin_backup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💚 سلامت سیستم",
                    callback_data="admin_health"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧪 مدیریت تست‌ها",
                    callback_data="admin_ab_tests"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 تحلیل رفتار",
                    callback_data="admin_behavior"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 مستندات",
                    callback_data="admin_docs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به منوی اصلی",
                    callback_data="back_to_main"
                )
            ]
        ]
    )