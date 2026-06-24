# my_bot_project/src/admin_panel/modules/user_management/keyboards/user_edit_keyboard.py
"""
کیبوردهای ویرایش کاربر (User Edit Keyboards).

این ماژول شامل توابع ساخت کیبوردهای شیشه‌ای برای ویرایش اطلاعات
کاربران در پنل مدیریت است.
"""

from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_user_edit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اصلی ویرایش کاربر.

    Args:
        user_id: شناسه کاربر برای ویرایش.

    Returns:
        InlineKeyboardMarkup: کیبورد ویرایش.
    """
    # فیلدهای قابل ویرایش
    fields = [
        ("first_name", "نام"),
        ("last_name", "نام خانوادگی"),
        ("username", "نام کاربری"),
        ("phone_number", "شماره تلفن"),
        ("email", "ایمیل"),
        ("role", "نقش"),
        ("level", "سطح"),
        ("points", "امتیاز"),
        ("is_active", "وضعیت فعال بودن"),
        ("is_banned", "وضعیت مسدود بودن"),
    ]

    keyboard = []

    # دکمه‌های فیلدها (دو تا در هر ردیف)
    row = []
    for i, (field, label) in enumerate(fields):
        row.append(
            InlineKeyboardButton(
                text=f"✏️ {label}",
                callback_data=f"admin_user_edit_field:{user_id}:{field}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # دکمه‌های عملیاتی
    keyboard.append([
        InlineKeyboardButton("✅ تأیید تغییرات", callback_data=f"admin_user_confirm:{user_id}"),
        InlineKeyboardButton("❌ لغو", callback_data=f"admin_user_cancel:{user_id}"),
    ])

    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"admin_user_view:{user_id}"),
        InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="admin_users"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_edit_field_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد برای ویرایش یک فیلد خاص (نمایش در حین ویرایش).

    Args:
        user_id: شناسه کاربر.

    Returns:
        InlineKeyboardMarkup: کیبورد ویرایش فیلد.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("❌ انصراف از ویرایش", callback_data=f"admin_user_cancel:{user_id}"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به فرم ویرایش", callback_data=f"admin_user_edit:{user_id}"),
        ],
    ])


def get_edit_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تأیید تغییرات کاربر.

    Args:
        user_id: شناسه کاربر.

    Returns:
        InlineKeyboardMarkup: کیبورد تأیید.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ تأیید و ذخیره", callback_data=f"admin_user_confirm:{user_id}"),
            InlineKeyboardButton("❌ لغو و بازگشت", callback_data=f"admin_user_cancel:{user_id}"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به فرم ویرایش", callback_data=f"admin_user_edit:{user_id}"),
        ],
    ])


def get_edit_success_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد پس از ذخیره موفق تغییرات.

    Args:
        user_id: شناسه کاربر ویرایش‌شده.

    Returns:
        InlineKeyboardMarkup: کیبورد موفقیت.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("👤 مشاهده کاربر", callback_data=f"admin_user_view:{user_id}"),
            InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


def get_edit_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد پس از لغو ویرایش.

    Returns:
        InlineKeyboardMarkup: کیبورد لغو.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data="admin_users"),
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


def get_user_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اقدامات روی کاربر (مشاهده، ویرایش، حذف).

    Args:
        user_id: شناسه کاربر.

    Returns:
        InlineKeyboardMarkup: کیبورد اقدامات.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"admin_user_edit:{user_id}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"admin_user_delete:{user_id}"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="admin_users"),
        ],
    ])