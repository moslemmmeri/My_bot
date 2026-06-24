# src/admin_panel/modules/broadcast/handlers/preview_broadcast.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, ValidationError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.broadcast.services import BroadcastSenderService, BroadcastFilterService
from admin_panel.modules.broadcast.keyboards import BroadcastConfirmKeyboard

logger = get_logger(__name__)


@requires_admin
async def preview_broadcast(query: CallbackQuery) -> None:
    """
    Show a preview of the broadcast message with recipient count.
    Callback data: "admin_broadcast_preview"
    """
    try:
        # In real implementation, retrieve from cache/state
        # For demo, use dummy data
        message_text = "پیام آزمایشی"
        message_type = "text"
        filters = {"level": "gold", "is_active": True}
        media_file_id = None

        # Get recipient count with filters
        filter_service = BroadcastFilterService()
        recipient_count = await filter_service.count_recipients(filters)

        # Build preview text
        text = (
            "✉️ **پیش‌نمایش پیام گروهی**\n\n"
            f"📊 تعداد گیرندگان: {recipient_count:,} نفر\n"
            f"📝 نوع پیام: {message_type}\n\n"
            "📄 **متن پیام:**\n"
            "---\n"
            f"{message_text}\n"
            "---\n\n"
            "⚠️ **توجه**: این پیام به تمام کاربرانی که شرایط فیلتر را دارند ارسال خواهد شد."
        )

        # Add filter info
        if filters:
            text += "\n🔍 **فیلترهای اعمال‌شده:**\n"
            for key, value in filters.items():
                text += f"  • {key}: {value}\n"

        keyboard = BroadcastConfirmKeyboard.get_preview_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except ValidationError as e:
        logger.warning(f"Validation error in preview_broadcast: {e}")
        await query.message.edit_text(
            f"❌ خطا: {str(e)}",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطا!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in preview_broadcast: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت آمار گیرندگان. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in preview_broadcast: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش پیش‌نمایش.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def preview_with_media(query: CallbackQuery) -> None:
    """
    Preview a broadcast with media (photo, video, document).
    Callback data: "admin_broadcast_preview_media"
    """
    try:
        # In real implementation, retrieve media from state
        media_type = "photo"
        media_file_id = "AgACAgQAAxkBAA..."
        caption = "متن همراه با رسانه"

        text = (
            "✉️ **پیش‌نمایش پیام با رسانه**\n\n"
            f"📷 نوع رسانه: {media_type}\n"
            f"📝 توضیحات: {caption}\n\n"
            "🔍 برای مشاهده دقیق رسانه، روی دکمه زیر کلیک کنید."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📷 مشاهده رسانه",
                        callback_data=f"admin_broadcast_view_media:{media_file_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ ارسال پیام",
                        callback_data="admin_broadcast_send"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش",
                        callback_data="admin_broadcast_compose"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_broadcast"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error in preview_with_media: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش پیش‌نمایش رسانه.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def preview_edit(query: CallbackQuery) -> None:
    """
    Go back to compose to edit the message.
    Callback data: "admin_broadcast_preview_edit"
    """
    await compose_broadcast(query)


@requires_admin
async def preview_confirm(query: CallbackQuery) -> None:
    """
    Proceed to send confirmation from preview.
    Callback data: "admin_broadcast_preview_confirm"
    """
    # Redirect to send confirmation
    await send_broadcast(query)