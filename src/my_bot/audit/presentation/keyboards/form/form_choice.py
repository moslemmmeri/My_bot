# my_bot_project/src/my_bot/presentation/keyboards/form/form_choice.py
"""
کیبورد انتخاب فرم (Form Choice Keyboard).

این ماژول شامل توابع ساخت کیبورد برای نمایش لیست فرم‌های موجود
و انتخاب فرم مورد نظر برای پر کردن است.
"""

from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_form_choice_keyboard(
    forms: List,
    page: int = 0,
    per_page: int = 5,
    show_categories: bool = False,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب فرم از لیست فرم‌ها.

    Args:
        forms: لیست فرم‌ها (هر فرم باید دارای id و title باشد).
        page: شماره صفحه (برای صفحه‌بندی).
        per_page: تعداد فرم در هر صفحه.
        show_categories: نمایش دسته‌بندی فرم‌ها (پیش‌فرض False).

    Returns:
        InlineKeyboardMarkup: کیبورد انتخاب فرم.
    """
    keyboard: List[List[InlineKeyboardButton]] = []

    # محاسبه محدوده فرم‌های این صفحه
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(forms))

    # فرم‌های این صفحه
    page_forms = forms[start_idx:end_idx]

    # اضافه کردن دکمه‌های فرم‌ها
    for form in page_forms:
        # نمایش عنوان فرم با ایموجی مناسب
        emoji = _get_form_type_emoji(form.form_type) if hasattr(form, "form_type") else "📝"
        status = "🔒" if not getattr(form, "is_active", True) else ""
        label = f"{emoji} {form.title} {status}"

        keyboard.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"form:start:{form.id}"
            )
        ])

    # دکمه‌های ناوبری (صفحه‌بندی)
    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ قبلی",
                callback_data=f"forms:page:{page - 1}"
            )
        )

    if end_idx < len(forms):
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ بعدی",
                callback_data=f"forms:page:{page + 1}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # دکمه‌های کمکی
    help_buttons = []

    if show_categories:
        help_buttons.append(
            InlineKeyboardButton(
                text="📂 دسته‌بندی",
                callback_data="forms:categories"
            )
        )

    help_buttons.append(
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_main"
        )
    )

    if help_buttons:
        keyboard.append(help_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_form_categories_keyboard(categories: dict) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد دسته‌بندی فرم‌ها.

    Args:
        categories: دیکشنری دسته‌بندی‌ها (کلید: نام دسته، مقدار: لیست فرم‌ها).

    Returns:
        InlineKeyboardMarkup: کیبورد دسته‌بندی فرم‌ها.
    """
    keyboard: List[List[InlineKeyboardButton]] = []

    for category_name, forms in categories.items():
        count = len(forms)
        keyboard.append([
            InlineKeyboardButton(
                text=f"{category_name} ({count})",
                callback_data=f"forms:category:{category_name}"
            )
        ])

    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت به لیست فرم‌ها",
            callback_data="forms_list"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_form_choice_simple(forms: List) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد ساده انتخاب فرم (بدون صفحه‌بندی و دسته‌بندی).

    Args:
        forms: لیست فرم‌ها.

    Returns:
        InlineKeyboardMarkup: کیبورد ساده انتخاب فرم.
    """
    keyboard: List[List[InlineKeyboardButton]] = []

    for form in forms:
        emoji = _get_form_type_emoji(form.form_type) if hasattr(form, "form_type") else "📝"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {form.title}",
                callback_data=f"form:start:{form.id}"
            )
        ])

    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _get_form_type_emoji(form_type: str) -> str:
    """
    دریافت ایموجی مناسب برای نوع فرم.

    Args:
        form_type: نوع فرم.

    Returns:
        str: ایموجی مربوط به نوع فرم.
    """
    emoji_map = {
        "survey": "📊",
        "registration": "📝",
        "order": "🛒",
        "feedback": "💬",
        "contact": "📞",
        "ticket": "🎫",
        "application": "👔",
        "reservation": "📅",
        "registration_event": "🎪",
        "complaint": "⚠️",
        "suggestion": "💡",
        "custom": "⚙️",
    }
    return emoji_map.get(form_type, "📋")