# my_bot_project/src/my_bot/presentation/keyboards/user/user_menu.py
"""
کیبورد منوی کاربری (User Menu Keyboard).

این ماژول شامل توابع ساخت کیبورد منوی کاربری است که برای کاربران عادی
نمایش داده می‌شود و شامل دکمه‌های دسترسی به بخش‌های مختلف ربات است.
"""

from typing import Optional, List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_user_menu_keyboard(
    show_profile: bool = True,
    show_orders: bool = True,
    show_forms: bool = True,
    show_help: bool = True,
    show_contact: bool = True,
    custom_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد منوی کاربری.

    Args:
        show_profile: نمایش دکمه پروفایل (پیش‌فرض True).
        show_orders: نمایش دکمه سفارشات (پیش‌فرض True).
        show_forms: نمایش دکمه فرم‌ها (پیش‌فرض True).
        show_help: نمایش دکمه راهنما (پیش‌فرض True).
        show_contact: نمایش دکمه تماس با ما (پیش‌فرض True).
        custom_buttons: دکمه‌های سفارشی برای اضافه کردن (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد منوی کاربری.
    """
    keyboard: List[List[InlineKeyboardButton]] = []

    # ردیف اول: پروفایل و سفارشات
    row1 = []
    if show_profile:
        row1.append(InlineKeyboardButton(text="👤 پروفایل", callback_data="profile"))
    if show_orders:
        row1.append(InlineKeyboardButton(text="🛒 سفارشات", callback_data="orders"))
    if row1:
        keyboard.append(row1)

    # ردیف دوم: فرم‌ها و راهنما
    row2 = []
    if show_forms:
        row2.append(InlineKeyboardButton(text="📋 فرم‌ها", callback_data="forms_list"))
    if show_help:
        row2.append(InlineKeyboardButton(text="❓ راهنما", callback_data="help"))
    if row2:
        keyboard.append(row2)

    # ردیف سوم: تماس با ما (تک دکمه)
    if show_contact:
        keyboard.append([
            InlineKeyboardButton(text="📞 تماس با ما", callback_data="contact")
        ])

    # اضافه کردن دکمه‌های سفارشی
    if custom_buttons:
        keyboard.extend(custom_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_user_menu_with_back(
    back_callback: str = "back_to_main",
    show_profile: bool = True,
    show_orders: bool = True,
    show_forms: bool = True,
    show_help: bool = True,
    show_contact: bool = True,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد منوی کاربری با دکمه بازگشت.

    Args:
        back_callback: داده‌ی کالبک برای دکمه بازگشت.
        show_profile: نمایش دکمه پروفایل.
        show_orders: نمایش دکمه سفارشات.
        show_forms: نمایش دکمه فرم‌ها.
        show_help: نمایش دکمه راهنما.
        show_contact: نمایش دکمه تماس با ما.

    Returns:
        InlineKeyboardMarkup: کیبورد منوی کاربری با دکمه بازگشت.
    """
    keyboard = get_user_menu_keyboard(
        show_profile=show_profile,
        show_orders=show_orders,
        show_forms=show_forms,
        show_help=show_help,
        show_contact=show_contact,
    )

    # اضافه کردن دکمه بازگشت
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_callback)
    ])

    return keyboard


def get_user_quick_actions_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اقدامات سریع کاربری.

    Returns:
        InlineKeyboardMarkup: کیبورد اقدامات سریع.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ امتیاز من", callback_data="user_points"),
            InlineKeyboardButton(text="🏅 سطح من", callback_data="user_level"),
        ],
        [
            InlineKeyboardButton(text="📊 آمار من", callback_data="user_stats"),
            InlineKeyboardButton(text="✏️ ویرایش پروفایل", callback_data="edit_profile"),
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="profile"),
        ],
    ])