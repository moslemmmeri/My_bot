# my_bot_project/src/admin_panel/modules/user_management/keyboards/user_list_keyboard.py
"""
کیبوردهای لیست کاربران (User List Keyboards).

این ماژول شامل توابع ساخت کیبوردهای شیشه‌ای برای نمایش لیست کاربران
با صفحه‌بندی، فیلتر و عملیات مدیریتی در پنل مدیریت است.
"""

from typing import List, Optional, Dict, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_user_list_keyboard(
    users: List[Any],
    current_page: int,
    total_pages: int,
    filters: Optional[Dict[str, Any]] = None,
    active_filter: str = "all",
    search_query: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد لیست کاربران با صفحه‌بندی و فیلتر.

    Args:
        users: لیست کاربران برای نمایش.
        current_page: شماره صفحه فعلی (از ۰ شروع می‌شود).
        total_pages: تعداد کل صفحات.
        filters: فیلترهای اعمال‌شده (اختیاری).
        active_filter: نام فیلتر فعال (پیش‌فرض: 'all').
        search_query: عبارت جستجو (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد ساخته‌شده.
    """
    keyboard = []

    # دکمه‌های کاربران (هر کاربر یک دکمه)
    if users:
        for user in users:
            username = user.username or user.full_name or f"کاربر {user.id}"
            role_emoji = _get_role_emoji(user.role.value if user.role else "user")
            status = "✅" if user.is_active else "⛔"
            banned = "🚫" if user.is_banned else ""

            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status} {role_emoji} {username} {banned}",
                    callback_data=f"admin_user_view:{user.id}"
                )
            ])

    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ قبلی",
                callback_data=_get_page_callback(current_page - 1, active_filter, search_query)
            )
        )

    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ بعدی",
                callback_data=_get_page_callback(current_page + 1, active_filter, search_query)
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # دکمه‌های فیلتر
    filter_buttons = _get_filter_buttons(active_filter, search_query)
    if filter_buttons:
        keyboard.append(filter_buttons)

    # دکمه‌های جستجو و خروجی
    keyboard.extend([
        [
            InlineKeyboardButton("🔍 جستجو", callback_data="admin_user_search"),
            InlineKeyboardButton("📥 خروجی", callback_data="admin_user_export"),
        ],
        [
            InlineKeyboardButton("➕ افزودن کاربر", callback_data="admin_user_add"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _get_role_emoji(role: str) -> str:
    """
    دریافت ایموجی مناسب برای نقش کاربر.

    Args:
        role: نام نقش.

    Returns:
        str: ایموجی نقش.
    """
    emojis = {
        "admin": "👑",
        "manager": "💼",
        "operator": "🛠️",
        "user": "👤",
    }
    return emojis.get(role, "👤")


def _get_filter_buttons(active_filter: str, search_query: Optional[str] = None) -> List[InlineKeyboardButton]:
    """
    دریافت دکمه‌های فیلتر.

    Args:
        active_filter: نام فیلتر فعال.
        search_query: عبارت جستجو (اختیاری).

    Returns:
        List[InlineKeyboardButton]: لیست دکمه‌های فیلتر.
    """
    filters = [
        ("all", "همه"),
        ("active", "فعال"),
        ("banned", "مسدود"),
        ("admin", "ادمین"),
        ("manager", "مدیر"),
        ("operator", "اپراتور"),
        ("user", "کاربر"),
    ]

    buttons = []
    for filter_name, label in filters:
        is_active = filter_name == active_filter
        prefix = "✅ " if is_active else ""
        callback = _get_filter_callback(filter_name, search_query)
        buttons.append(
            InlineKeyboardButton(
                text=f"{prefix}{label}",
                callback_data=callback
            )
        )

    # اگر فیلترهای زیادی باشند، دو ردیف می‌شوند
    if len(buttons) > 4:
        # تقسیم به دو ردیف
        mid = len(buttons) // 2
        return buttons[:mid] + buttons[mid:]
    return buttons


def _get_filter_callback(filter_name: str, search_query: Optional[str] = None) -> str:
    """
    تولید callback برای اعمال فیلتر.

    Args:
        filter_name: نام فیلتر.
        search_query: عبارت جستجو (اختیاری).

    Returns:
        str: رشته callback.
    """
    if search_query:
        return f"admin_users_filter:{filter_name}:{search_query}"
    return f"admin_users_filter:{filter_name}"


def _get_page_callback(page: int, active_filter: str, search_query: Optional[str] = None) -> str:
    """
    تولید callback برای تغییر صفحه.

    Args:
        page: شماره صفحه.
        active_filter: نام فیلتر فعال.
        search_query: عبارت جستجو (اختیاری).

    Returns:
        str: رشته callback.
    """
    if search_query:
        return f"admin_users_page:{page}:{active_filter}:{search_query}"
    return f"admin_users_page:{page}:{active_filter}"


def get_user_list_simple_keyboard(
    current_page: int,
    total_pages: int,
    active_filter: str = "all",
    search_query: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد ساده لیست کاربران (بدون دکمه‌های کاربران).

    Args:
        current_page: شماره صفحه فعلی.
        total_pages: تعداد کل صفحات.
        active_filter: نام فیلتر فعال.
        search_query: عبارت جستجو (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد ساده.
    """
    keyboard = []

    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ قبلی",
                callback_data=_get_page_callback(current_page - 1, active_filter, search_query)
            )
        )

    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ بعدی",
                callback_data=_get_page_callback(current_page + 1, active_filter, search_query)
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # دکمه‌های فیلتر
    filter_buttons = _get_filter_buttons(active_filter, search_query)
    if filter_buttons:
        keyboard.append(filter_buttons)

    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)