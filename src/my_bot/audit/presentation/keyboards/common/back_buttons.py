# my_bot_project/src/my_bot/presentation/keyboards/common/back_buttons.py
"""
دکمه‌های بازگشت (Back Buttons).

این ماژول شامل توابع ساخت دکمه‌های شیشه‌ای برای بازگشت به صفحات قبلی
یا بازگشت به منوی اصلی است. این دکمه‌ها در سراسر ربات استفاده می‌شوند.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه بازگشت ساده.

    Args:
        callback_data: داده‌ی کالبک برای دکمه (پیش‌فرض: "back").

    Returns:
        InlineKeyboardMarkup: کیبورد شامل یک دکمه بازگشت.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data)]
    ])


def get_back_to_main_button(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه بازگشت به منوی اصلی.

    Args:
        callback_data: داده‌ی کالبک برای دکمه (پیش‌فرض: "back_to_main").

    Returns:
        InlineKeyboardMarkup: کیبورد شامل یک دکمه بازگشت به منوی اصلی.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_data)]
    ])


def get_back_button_with_text(
    text: str = "🔙 بازگشت",
    callback_data: str = "back",
) -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه بازگشت با متن سفارشی.

    Args:
        text: متن دکمه.
        callback_data: داده‌ی کالبک برای دکمه.

    Returns:
        InlineKeyboardMarkup: کیبورد شامل یک دکمه بازگشت.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback_data)]
    ])