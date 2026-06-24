# my_bot_project/src/my_bot/presentation/keyboards/form/form_navigation.py
"""
کیبورد ناوبری فرم (Form Navigation Keyboard).

این ماژول شامل توابع ساخت کیبوردهای ناوبری در فرم‌های چند مرحله‌ای است.
شامل دکمه‌های رفتن به مرحله قبلی/بعدی، لغو و نمایش پیشرفت است.
"""

from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_form_navigation_keyboard(
    current_step: int,
    total_steps: int,
    has_previous: bool = False,
    has_next: bool = True,
    show_progress: bool = True,
    cancel_callback: str = "form:cancel",
    previous_callback: str = "form:previous",
    next_callback: str = "form:next",
    submit_callback: str = "form:submit",
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد ناوبری برای فرم‌های چند مرحله‌ای.

    Args:
        current_step: شماره مرحله فعلی (از ۱ شروع می‌شود).
        total_steps: تعداد کل مراحل.
        has_previous: آیا دکمه قبلی نمایش داده شود.
        has_next: آیا دکمه بعدی نمایش داده شود.
        show_progress: نمایش پیشرفت (پیش‌فرض True).
        cancel_callback: داده‌ی کالبک برای دکمه انصراف.
        previous_callback: داده‌ی کالبک برای دکمه قبلی.
        next_callback: داده‌ی کالبک برای دکمه بعدی.
        submit_callback: داده‌ی کالبک برای دکمه ارسال.

    Returns:
        InlineKeyboardMarkup: کیبورد ناوبری فرم.
    """
    keyboard = []

    # دکمه‌های ناوبری اصلی
    nav_buttons = []

    if has_previous:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ قبلی", callback_data=previous_callback)
        )

    if has_next and current_step < total_steps:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ بعدی", callback_data=next_callback)
        )

    # اگر مرحله آخر است، دکمه ارسال نمایش داده می‌شود
    if current_step == total_steps and has_next:
        nav_buttons.append(
            InlineKeyboardButton(text="✅ ارسال", callback_data=submit_callback)
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # نمایش پیشرفت
    if show_progress and total_steps > 1:
        progress_text = _get_progress_bar(current_step, total_steps)
        keyboard.append([
            InlineKeyboardButton(
                text=progress_text,
                callback_data="form:progress"  # غیرفعال (بدون عملکرد)
            )
        ])

    # دکمه انصراف
    keyboard.append([
        InlineKeyboardButton(text="❌ انصراف", callback_data=cancel_callback)
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_form_step_keyboard(
    step: int,
    total_steps: int,
    has_options: bool = False,
    options: Optional[list] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد برای یک مرحله خاص از فرم (با گزینه‌ها).

    Args:
        step: شماره مرحله.
        total_steps: تعداد کل مراحل.
        has_options: آیا گزینه‌های انتخابی وجود دارد.
        options: لیست گزینه‌ها (هر گزینه شامل value و label).

    Returns:
        InlineKeyboardMarkup: کیبورد مرحله فرم.
    """
    keyboard = []

    # اگر گزینه‌ها وجود داشته باشند، دکمه‌های انتخاب را اضافه کن
    if has_options and options:
        for option in options:
            keyboard.append([
                InlineKeyboardButton(
                    text=option.get("label", option.get("value", "گزینه")),
                    callback_data=f"form:answer:{option.get('value')}"
                )
            ])

    # دکمه‌های ناوبری
    nav_buttons = []

    if step > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ قبلی", callback_data="form:previous")
        )

    if step < total_steps:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ بعدی", callback_data="form:next")
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="✅ ارسال", callback_data="form:submit")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # نمایش پیشرفت
    if total_steps > 1:
        progress_text = _get_progress_bar(step, total_steps)
        keyboard.append([
            InlineKeyboardButton(
                text=progress_text,
                callback_data="form:progress"  # غیرفعال
            )
        ])

    # دکمه انصراف
    keyboard.append([
        InlineKeyboardButton(text="❌ انصراف", callback_data="form:cancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_form_confirm_keyboard(
    step: int,
    total_steps: int,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تأیید ارسال فرم.

    Args:
        step: شماره مرحله (معمولاً آخرین مرحله).
        total_steps: تعداد کل مراحل.

    Returns:
        InlineKeyboardMarkup: کیبورد تأیید ارسال.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✅ تأیید و ارسال", callback_data="form:submit"),
            InlineKeyboardButton(text="✏️ ویرایش", callback_data="form:edit"),
        ],
        [
            InlineKeyboardButton(text="⬅️ قبلی", callback_data="form:previous"),
        ],
        [
            InlineKeyboardButton(text="❌ انصراف", callback_data="form:cancel"),
        ]
    ]

    # نمایش پیشرفت
    if total_steps > 1:
        progress_text = _get_progress_bar(step, total_steps)
        keyboard.insert(0, [
            InlineKeyboardButton(
                text=progress_text,
                callback_data="form:progress"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_form_cancel_only_keyboard(
    cancel_callback: str = "form:cancel",
    back_callback: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد با فقط دکمه انصراف (و دکمه بازگشت اختیاری).

    Args:
        cancel_callback: داده‌ی کالبک برای دکمه انصراف.
        back_callback: داده‌ی کالبک برای دکمه بازگشت (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد با دکمه انصراف.
    """
    keyboard = []

    if back_callback:
        keyboard.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data=back_callback),
            InlineKeyboardButton(text="❌ انصراف", callback_data=cancel_callback),
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="❌ انصراف", callback_data=cancel_callback),
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _get_progress_bar(current_step: int, total_steps: int) -> str:
    """
    ساخت نوار پیشرفت برای نمایش در کیبورد.

    Args:
        current_step: شماره مرحله فعلی.
        total_steps: تعداد کل مراحل.

    Returns:
        str: نوار پیشرفت به‌صورت متن.
    """
    filled = "●" * current_step
    empty = "○" * (total_steps - current_step)
    return f"پیشرفت: {filled}{empty} ({current_step}/{total_steps})"