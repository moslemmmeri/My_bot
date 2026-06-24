# my_bot_project/src/my_bot/presentation/keyboards/common/main_menu.py
"""
منوی اصلی (Main Menu Keyboard).

این ماژول شامل توابع ساخت کیبورد منوی اصلی است که برای تمام کاربران
نمایش داده می‌شود. در صورت ادمین بودن کاربر، دکمه‌ی ورود به پنل مدیریت
نیز به منو اضافه می‌شود.
"""

from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.constants.user_roles import UserRole


def get_main_menu_keyboard(
    is_admin: bool = False,
    custom_buttons: Optional[list[list[InlineKeyboardButton]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد منوی اصلی.

    Args:
        is_admin: آیا کاربر ادمین است (در صورت True، دکمه پنل مدیریت اضافه می‌شود).
        custom_buttons: دکمه‌های سفارشی برای اضافه کردن به انتهای کیبورد (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد منوی اصلی.
    """
    # دکمه‌های اصلی منو
    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="📋 فرم‌ها", callback_data="forms_list"),
            InlineKeyboardButton(text="👤 پروفایل", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="📞 تماس با ما", callback_data="contact"),
            InlineKeyboardButton(text="❓ راهنما", callback_data="help"),
        ],
    ]

    # اگر کاربر ادمین است، دکمه پنل مدیریت را اضافه کن
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(text="⚙️ پنل مدیریت", callback_data="admin_panel"),
        ])

    # اضافه کردن دکمه‌های سفارشی (در صورت وجود)
    if custom_buttons:
        keyboard.extend(custom_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_main_menu_with_admin_button(
    user_role: Optional[UserRole] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد منوی اصلی با دکمه ادمین بر اساس نقش کاربر.

    Args:
        user_role: نقش کاربر (در صورت None یا USER، دکمه ادمین نمایش داده نمی‌شود).

    Returns:
        InlineKeyboardMarkup: کیبورد منوی اصلی.
    """
    is_admin = user_role in (UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)
    return get_main_menu_keyboard(is_admin=is_admin)