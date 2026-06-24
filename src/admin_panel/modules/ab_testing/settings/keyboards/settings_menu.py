# src/admin_panel/modules/settings/keyboards/settings_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class SettingsMenuKeyboard:
    """Keyboard for settings menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main settings menu keyboard with categories."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚙️ تنظیمات عمومی",
                        callback_data="admin_settings_category:general"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔐 تنظیمات امنیتی",
                        callback_data="admin_settings_category:security"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📧 تنظیمات ایمیلی",
                        callback_data="admin_settings_category:email"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💳 تنظیمات پرداخت",
                        callback_data="admin_settings_category:payment"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 تنظیمات گزارش‌گیری",
                        callback_data="admin_settings_category:reporting"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔔 تنظیمات اعلان‌ها",
                        callback_data="admin_settings_category:notifications"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🌐 تنظیمات چندزبانی",
                        callback_data="admin_settings_category:i18n"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚡ تنظیمات کش",
                        callback_data="admin_settings_category:cache"
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
    def get_back_keyboard(back_callback: str = "admin_settings") -> InlineKeyboardMarkup:
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