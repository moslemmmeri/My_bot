# src/admin_panel/modules/tickets/handlers/reply_ticket.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.tickets.services import TicketService
from admin_panel.modules.tickets.keyboards import TicketReplyKeyboard
from admin_panel.modules.tickets.validators import TicketValidator

logger = get_logger(__name__)


@requires_admin
async def reply_ticket(query: CallbackQuery) -> None:
    """
    Start the reply process for a ticket.
    Callback data format: "admin_tickets_reply:{ticket_id}"
    """
    try:
        _, ticket_id_str = query.data.split(":", 1)
        ticket_id = int(ticket_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه تیکت نامعتبر است.", show_alert=True)
        return

    try:
        # Verify ticket exists
        service = TicketService()
        ticket = await service.get_ticket(ticket_id)
        if not ticket:
            await query.message.edit_text(
                "❌ تیکت مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_tickets_list:1")
            )
            await query.answer("تیکت یافت نشد!", show_alert=True)
            return

        # Show prompt for reply text
        text = (
            f"💬 **پاسخ به تیکت**\n\n"
            f"🆔 شناسه: `{ticket_id}`\n"
            f"📝 عنوان: {ticket.get('title', 'بدون عنوان')}\n\n"
            f"لطفاً متن پاسخ را وارد کنید:\n"
            f"(برای انصراف روی دکمه لغو کلیک کنید)"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"admin_tickets_view:{ticket_id}"
                    )
                ]
            ]
        )

        # Store ticket_id in user state (in a real implementation)
        # For now, we'll store it in the callback data of the next step

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in reply_ticket: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات تیکت. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in reply_ticket: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در آماده‌سازی پاسخ.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def send_reply(query: CallbackQuery) -> None:
    """
    Process the reply text (this would be triggered from a message handler, but we'll keep it as a callback for demo).
    In reality, this would be handled by a message handler that reads the text input.
    We'll keep this as a placeholder if the bot receives the reply via callback (e.g., from a quick reply).
    """
    # This function is not used directly; we rely on a message handler.
    # But we include it for completeness.
    pass


# Note: In a real implementation, you would have a separate message handler
# that listens for text messages when the user is in "replying" state.
# That handler would call TicketService to add the reply.