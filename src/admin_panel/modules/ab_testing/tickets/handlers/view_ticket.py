# src/admin_panel/modules/tickets/handlers/view_ticket.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.tickets.services import TicketService
from admin_panel.modules.tickets.keyboards import TicketActionsKeyboard

logger = get_logger(__name__)


@requires_admin
async def view_ticket(query: CallbackQuery) -> None:
    """
    Display detailed information about a ticket.
    Callback data format: "admin_tickets_view:{ticket_id}"
    """
    try:
        _, ticket_id_str = query.data.split(":", 1)
        ticket_id = int(ticket_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه تیکت نامعتبر است.", show_alert=True)
        return

    try:
        service = TicketService()
        ticket = await service.get_ticket(ticket_id)

        if not ticket:
            await query.message.edit_text(
                "❌ تیکت مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_tickets_list:1")
            )
            await query.answer("تیکت یافت نشد!", show_alert=True)
            return

        # Status and priority labels
        status_names = {
            "open": "🟢 باز",
            "in_progress": "🟡 در حال بررسی",
            "resolved": "🔵 حل شده",
            "closed": "⚪ بسته",
        }
        priority_names = {
            "low": "🟢 کم",
            "medium": "🟡 متوسط",
            "high": "🔴 بالا",
            "critical": "🚨 بحرانی",
        }

        # Build ticket details text
        text = (
            f"🎫 **جزئیات تیکت**\n\n"
            f"🆔 شناسه: `{ticket.get('id')}`\n"
            f"📝 عنوان: {ticket.get('title', 'بدون عنوان')}\n"
            f"📋 وضعیت: {status_names.get(ticket.get('status'), ticket.get('status'))}\n"
            f"🔴 اولویت: {priority_names.get(ticket.get('priority'), ticket.get('priority'))}\n"
            f"👤 کاربر: {ticket.get('user_name', 'نامشخص')}\n"
            f"🆔 کاربر: `{ticket.get('user_id', 'نامشخص')}`\n"
            f"📅 ایجاد: {ticket.get('created_at', 'نامشخص')}\n"
            f"📅 آخرین بروزرسانی: {ticket.get('updated_at', 'نامشخص')}\n"
        )

        if ticket.get('assigned_to'):
            text += f"👤 تخصیص داده شده به: {ticket.get('assigned_to_name', ticket.get('assigned_to'))}\n"

        text += f"\n📄 **متن تیکت:**\n---\n{ticket.get('body', 'بدون متن')}\n---\n"

        # Show replies if any
        replies = ticket.get('replies', [])
        if replies:
            text += f"\n💬 **پاسخ‌ها** ({len(replies)}):\n"
            for reply in replies[-3:]:  # Show last 3 replies
                reply_user = reply.get('user_name', 'نامشخص')
                reply_text = reply.get('text', 'بدون متن')[:100]
                reply_date = reply.get('created_at', 'نامشخص')[:16]
                text += f"  • {reply_user} ({reply_date}): {reply_text}{'...' if len(reply.get('text', '')) > 100 else ''}\n"
            if len(replies) > 3:
                text += f"\n  ... و {len(replies) - 3} پاسخ دیگر\n"

        # Build keyboard
        keyboard = TicketActionsKeyboard.get_action_keyboard(
            ticket_id=ticket_id,
            current_status=ticket.get('status', 'open'),
            back_callback="admin_tickets_list:1",
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except NotFoundError as e:
        logger.warning(f"Ticket {ticket_id} not found: {e}")
        await query.message.edit_text(
            "❌ تیکت مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("تیکت یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error viewing ticket {ticket_id}: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات تیکت. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error viewing ticket {ticket_id}: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش تیکت.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)