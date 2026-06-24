# my_bot_project/src/my_bot/presentation/keyboards/user/user_actions.py
"""
کیبوردهای اقدامات کاربری (User Actions Keyboards).

این ماژول شامل توابع ساخت کیبوردهای مربوط به اقدامات کاربری مانند
پروفایل، سفارشات، سطح، ویرایش اطلاعات و ... است.
"""

from typing import Optional, List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_user_actions_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اقدامات کاربری (نمایش در پروفایل).

    Returns:
        InlineKeyboardMarkup: کیبورد اقدامات کاربری.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 سفارشات من", callback_data="orders"),
        ],
        [
            InlineKeyboardButton(text="⭐ امتیاز و سطح", callback_data="level_info"),
        ],
        [
            InlineKeyboardButton(text="✏️ ویرایش پروفایل", callback_data="edit_profile"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main"),
        ],
    ])


def get_profile_actions_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اقدامات پروفایل (نمایش در پروفایل).

    Returns:
        InlineKeyboardMarkup: کیبورد اقدامات پروفایل.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 سفارشات", callback_data="orders"),
            InlineKeyboardButton(text="⭐ سطح و امتیاز", callback_data="level_info"),
        ],
        [
            InlineKeyboardButton(text="✏️ ویرایش اطلاعات", callback_data="edit_profile"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="profile"),
        ],
    ])


def get_edit_profile_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد ویرایش پروفایل.

    Returns:
        InlineKeyboardMarkup: کیبورد ویرایش پروفایل.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📛 ویرایش نام", callback_data="edit_name"),
            InlineKeyboardButton(text="📞 ویرایش تلفن", callback_data="edit_phone"),
        ],
        [
            InlineKeyboardButton(text="📧 ویرایش ایمیل", callback_data="edit_email"),
            InlineKeyboardButton(text="👤 ویرایش نام کاربری", callback_data="edit_username"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به پروفایل", callback_data="profile"),
        ],
    ])


def get_edit_field_keyboard(field_name: str) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد ویرایش یک فیلد خاص.

    Args:
        field_name: نام فیلد (برای callback).

    Returns:
        InlineKeyboardMarkup: کیبورد ویرایش فیلد.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأیید", callback_data=f"confirm_edit:{field_name}"),
            InlineKeyboardButton(text="❌ انصراف", callback_data="profile"),
        ],
    ])


def get_user_stats_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد آمار کاربر.

    Returns:
        InlineKeyboardMarkup: کیبورد آمار کاربر.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 آمار کامل", callback_data="user_full_stats"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="profile"),
        ],
    ])


def get_user_level_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اطلاعات سطح کاربر.

    Returns:
        InlineKeyboardMarkup: کیبورد اطلاعات سطح.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 آمار امتیاز", callback_data="user_points_history"),
            InlineKeyboardButton(text="🏆 جدول برترین‌ها", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="profile"),
        ],
    ])


def get_user_actions_with_custom(
    custom_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اقدامات کاربری با دکمه‌های سفارشی.

    Args:
        custom_buttons: دکمه‌های سفارشی برای اضافه کردن (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد اقدامات کاربری با دکمه‌های سفارشی.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🛒 سفارشات من", callback_data="orders"),
            InlineKeyboardButton(text="⭐ امتیاز و سطح", callback_data="level_info"),
        ],
        [
            InlineKeyboardButton(text="✏️ ویرایش پروفایل", callback_data="edit_profile"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main"),
        ],
    ]

    if custom_buttons:
        keyboard.extend(custom_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)