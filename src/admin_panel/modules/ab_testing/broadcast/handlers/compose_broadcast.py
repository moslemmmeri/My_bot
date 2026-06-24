# src/admin_panel/modules/broadcast/handlers/compose_broadcast.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.broadcast.keyboards import BroadcastMenuKeyboard
from admin_panel.modules.broadcast.services import BroadcastFilterService

logger = get_logger(__name__)


@requires_admin
async def compose_broadcast(query: CallbackQuery) -> None:
    """
    Start the broadcast composition process.
    Callback data: "admin_broadcast_compose"
    """
    try:
        text = (
            "✉️ **ارسال پیام گروهی**\n\n"
            "لطفاً نوع پیام را انتخاب کنید:"
        )
        keyboard = BroadcastMenuKeyboard.get_compose_type_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error in compose_broadcast: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در شروع ساخت پیام گروهی.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def broadcast_type_selected(query: CallbackQuery) -> None:
    """
    Handle message type selection and ask for content.
    Callback data format: "admin_broadcast_type:{msg_type}"
    """
    try:
        _, msg_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ نوع پیام نامعتبر است.", show_alert=True)
        return

    # Store type in callback data for next step
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_broadcast"
                )
            ]
        ]
    )

    text = (
        f"✉️ **ساخت پیام گروهی**\n\n"
        f"📝 نوع: {msg_type}\n\n"
        f"لطفاً **متن** پیام را وارد کنید:\n"
        f"(برای پیام‌های تصویری/ویدیویی، بعداً فایل را ارسال کنید)"
    )

    await query.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def broadcast_content_received(query: CallbackQuery) -> None:
    """
    Handle content input (text or media) and proceed to filters.
    Callback data format: "admin_broadcast_content:{msg_type}:{text_preview}"
    This is called after user sends the text message.
    """
    try:
        _, msg_type, text_preview = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Show filter selection or skip
    text = (
        f"✉️ **پیام شما**\n\n"
        f"📝 نوع: {msg_type}\n"
        f"📄 متن: {text_preview[:100]}...\n\n"
        f"حالا می‌توانید فیلترهای ارسال را تنظیم کنید.\n"
        f"در غیر این صورت، پیام برای همه کاربران ارسال خواهد شد."
    )

    keyboard = BroadcastMenuKeyboard.get_filter_or_skip_keyboard()

    await query.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def broadcast_skip_filters(query: CallbackQuery) -> None:
    """
    Skip filters and go directly to confirmation.
    Callback data: "admin_broadcast_skip_filters"
    """
    # This will be handled in send_broadcast or preview.
    # For now, redirect to preview with no filters.
    await preview_broadcast(query)  # assuming imported


@requires_admin
async def broadcast_choose_filters(query: CallbackQuery) -> None:
    """
    Show available filter options.
    Callback data: "admin_broadcast_choose_filters"
    """
    try:
        text = (
            "🔍 **انتخاب فیلترهای ارسال**\n\n"
            "کاربرانی که شرایط زیر را داشته باشند، پیام را دریافت می‌کنند:\n"
            "می‌توانید ترکیبی از فیلترها را انتخاب کنید."
        )
        keyboard = BroadcastFilterKeyboard.get_filter_menu_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error in broadcast_choose_filters: {e}", exc_info=True)
        await query.answer("❌ خطا در نمایش فیلترها.", show_alert=True)


@requires_admin
async def broadcast_filter_selected(query: CallbackQuery) -> None:
    """
    Handle selection of a filter type (e.g., user level, status, date).
    Callback data format: "admin_broadcast_filter:{filter_type}"
    """
    try:
        _, filter_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ فیلتر نامعتبر است.", show_alert=True)
        return

    # Show options for the selected filter
    keyboard = BroadcastFilterKeyboard.get_filter_options_keyboard(filter_type)

    text = f"🔍 **انتخاب مقدار برای فیلتر {filter_type}**\n\n"
    text += "گزینه مورد نظر را انتخاب کنید:"

    await query.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def broadcast_filter_value_set(query: CallbackQuery) -> None:
    """
    Set a filter value and return to filter list.
    Callback data format: "admin_broadcast_set_filter:{filter_type}:{value}"
    """
    try:
        _, filter_type, value = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Store filter in service/state
    # For now, just acknowledge and show filter menu again
    await query.answer(f"فیلتر {filter_type} = {value} تنظیم شد.")

    # Go back to filter menu
    await broadcast_choose_filters(query)


@requires_admin
async def broadcast_clear_filters(query: CallbackQuery) -> None:
    """
    Clear all filters.
    Callback data: "admin_broadcast_clear_filters"
    """
    # Clear filters in service/state
    await query.answer("همه فیلترها پاک شدند.")

    # Go back to filter menu
    await broadcast_choose_filters(query)


@requires_admin
async def broadcast_preview_with_filters(query: CallbackQuery) -> None:
    """
    Preview the broadcast with applied filters.
    Callback data: "admin_broadcast_preview"
    """
    # This should redirect to preview_broadcast handler
    await preview_broadcast(query)  # assuming imported


@requires_admin
async def broadcast_cancel_compose(query: CallbackQuery) -> None:
    """
    Cancel composition and return to broadcast menu.
    Callback data: "admin_broadcast_cancel_compose"
    """
    await query.message.edit_text(
        "❌ ساخت پیام گروهی لغو شد.",
        reply_markup=get_back_button("admin_broadcast")
    )
    await query.answer("لغو شد.")