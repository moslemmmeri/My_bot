# my_bot_project/src/my_bot/presentation/keyboards/common/cancel_buttons.py
"""
دکمه‌های انصراف (Cancel Buttons).

این ماژول شامل توابع ساخت دکمه‌های شیشه‌ای برای انصراف از عملیات‌های در حال انجام
و بازگشت به حالت قبلی یا منوی اصلی است. این دکمه‌ها در فرم‌ها، پرداخت‌ها و
سایر عملیات‌های طولانی استفاده می‌شوند.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_cancel_button(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه انصراف ساده.

    Args:
        callback_data: داده‌ی کالبک برای دکمه (پیش‌فرض: "cancel").

    Returns:
        InlineKeyboardMarkup: کیبورد شامل یک دکمه انصراف.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data=callback_data)]
    ])


def get_cancel_with_back_button(
    cancel_callback: str = "cancel",
    back_callback: str = "back",
) -> InlineKeyboardMarkup:
    """
    ساخت دکمه‌های انصراف و بازگشت.

    Args:
        cancel_callback: داده‌ی کالبک برای دکمه انصراف (پیش‌فرض: "cancel").
        back_callback: داده‌ی کالبک برای دکمه بازگشت (پیش‌فرض: "back").

    Returns:
        InlineKeyboardMarkup: کیبورد شامل دکمه‌های انصراف و بازگشت.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_callback),
            InlineKeyboardButton(text="❌ انصراف", callback_data=cancel_callback),
        ]
    ])


def get_cancel_to_main_button(
    cancel_callback: str = "cancel_to_main",
) -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه انصراف و بازگشت به منوی اصلی.

    Args:
        cancel_callback: داده‌ی کالبک برای دکمه (پیش‌فرض: "cancel_to_main").

    Returns:
        InlineKeyboardMarkup: کیبورد شامل یک دکمه انصراف به منوی اصلی.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف و بازگشت به منوی اصلی", callback_data=cancel_callback)]
    ])


def get_cancel_with_text(
    text: str = "❌ انصراف",
    callback_data: str = "cancel",
) -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه انصراف با متن سفارشی.

    Args:
        text: متن دکمه.
        callback_data: داده‌ی کالبک برای دکمه.

    Returns:
        InlineKeyboardMarkup: کیبورد شامل یک دکمه انصراف.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback_data)]
    ])