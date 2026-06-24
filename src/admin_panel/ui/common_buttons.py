# src/admin_panel/ui/common_buttons.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_button(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Get a back button with custom callback data."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data=callback_data
                )
            ]
        ]
    )


def get_cancel_button(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """Get a cancel button with custom callback data."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data=callback_data
                )
            ]
        ]
    )


def get_main_menu_button(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Get a main menu button with custom callback data."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 منوی اصلی",
                    callback_data=callback_data
                )
            ]
        ]
    )