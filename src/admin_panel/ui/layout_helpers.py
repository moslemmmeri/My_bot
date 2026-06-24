# src/admin_panel/ui/layout_helpers.py
from typing import List, Dict, Any, Optional, Callable, Union
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_action_row(
    buttons: List[Dict[str, str]],
    row_width: int = 1,
) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with buttons arranged in rows.
    Each button dict should contain 'text' and 'callback_data' keys.
    """
    keyboard = []
    row = []
    for idx, button in enumerate(buttons):
        row.append(
            InlineKeyboardButton(
                text=button.get("text", "button"),
                callback_data=button.get("callback_data", "noop"),
            )
        )
        if len(row) == row_width or idx == len(buttons) - 1:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_two_column_row(
    left_text: str,
    left_callback: str,
    right_text: str,
    right_callback: str,
) -> InlineKeyboardMarkup:
    """Create a two-column inline keyboard row."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=left_text, callback_data=left_callback),
                InlineKeyboardButton(text=right_text, callback_data=right_callback),
            ]
        ]
    )


def create_three_column_row(
    first_text: str,
    first_callback: str,
    second_text: str,
    second_callback: str,
    third_text: str,
    third_callback: str,
) -> InlineKeyboardMarkup:
    """Create a three-column inline keyboard row."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=first_text, callback_data=first_callback),
                InlineKeyboardButton(text=second_text, callback_data=second_callback),
                InlineKeyboardButton(text=third_text, callback_data=third_callback),
            ]
        ]
    )


def paginate_buttons(
    current_page: int,
    total_pages: int,
    base_callback: str,
    additional_data: Optional[Dict[str, str]] = None,
) -> InlineKeyboardMarkup:
    """
    Create pagination buttons for a list.
    base_callback should be a string with a placeholder like '{page}'.
    additional_data can be used to add extra params to the callback.
    """
    keyboard = []
    row = []

    if current_page > 1:
        prev_callback = base_callback.replace("{page}", str(current_page - 1))
        row.append(
            InlineKeyboardButton(
                text="⬅️ قبلی",
                callback_data=prev_callback,
            )
        )

    row.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop",
        )
    )

    if current_page < total_pages:
        next_callback = base_callback.replace("{page}", str(current_page + 1))
        row.append(
            InlineKeyboardButton(
                text="➡️ بعدی",
                callback_data=next_callback,
            )
        )

    keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_paginated_list_keyboard(
    items: List[Dict[str, Any]],
    item_callback_format: str,
    page: int,
    total_pages: int,
    base_callback: str,
    back_callback: str = "back_to_main",
) -> InlineKeyboardMarkup:
    """
    Create a paginated list keyboard with item buttons and pagination controls.
    """
    keyboard = []

    # Add item buttons
    for item in items:
        item_id = item.get("id")
        title = item.get("title") or item.get("name") or f"آیتم {item_id}"
        callback = item_callback_format.replace("{id}", str(item_id))
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=title[:30] + "..." if len(title) > 30 else title,
                    callback_data=callback,
                )
            ]
        )

    # Add pagination
    if total_pages > 1:
        pagination = paginate_buttons(page, total_pages, base_callback)
        keyboard.extend(pagination.inline_keyboard)

    # Add back button
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback,
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_action_buttons(
    actions: List[Dict[str, str]],
) -> InlineKeyboardMarkup:
    """
    Create a keyboard with action buttons.
    Each action dict should contain 'text' and 'callback_data'.
    """
    keyboard = []
    for action in actions:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=action.get("text", "action"),
                    callback_data=action.get("callback_data", "noop"),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_confirm_cancel_keyboard(
    confirm_callback: str,
    cancel_callback: str,
    confirm_text: str = "✅ بله",
    cancel_text: str = "❌ لغو",
) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard with confirm and cancel buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
                InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback),
            ]
        ]
    )


def create_toggle_keyboard(
    active_callback: str,
    inactive_callback: str,
    is_active: bool,
    active_text: str = "🟢 فعال",
    inactive_text: str = "🔴 غیرفعال",
) -> InlineKeyboardMarkup:
    """Create a toggle keyboard with status-specific buttons."""
    if is_active:
        callback = inactive_callback
        text = inactive_text
    else:
        callback = active_callback
        text = active_text

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=callback,
                )
            ]
        ]
    )