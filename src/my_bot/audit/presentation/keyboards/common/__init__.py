# my_bot_project/src/my_bot/presentation/keyboards/common/__init__.py
"""
ماژول کیبوردهای عمومی (Common Keyboards).

این ماژول شامل کیبوردهای پرکاربرد و عمومی است که در سراسر ربات استفاده می‌شوند:
- main_menu: منوی اصلی
- back_buttons: دکمه‌های بازگشت
- cancel_buttons: دکمه‌های انصراف
"""

from my_bot.presentation.keyboards.common.main_menu import get_main_menu_keyboard
from my_bot.presentation.keyboards.common.back_buttons import (
    get_back_button,
    get_back_to_main_button,
)
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button

__all__ = [
    "get_main_menu_keyboard",
    "get_back_button",
    "get_back_to_main_button",
    "get_cancel_button",
]