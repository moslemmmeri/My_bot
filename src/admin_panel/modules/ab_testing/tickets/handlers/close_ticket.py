# src/admin_panel/modules/tickets/handlers/close_ticket.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, DatabaseError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.tickets.services import TicketService
from admin_panel.modules.tickets.keyboards import TicketActionsKeyboard

logger = get_logger(__name__)


@requires_admin
async def close_ticket(query: CallbackQuery) -> None:
    """
    Show confirmation dialog for closing a ticket.
    Callback data format: "admin_tickets_close:{ticket_id}"
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

        # Check if already closed
        if ticket.get("status") == "closed":
            await query.message.edit_text(
                "ℹ️ این تیکت قبلاً بسته شده است.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 بازگشت به تیکت",
                                callback_data=f"admin_tickets_view:{ticket_id}"
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown"
            )
            await query.answer("تیکت قبلاً بسته شده است.")
            return

        text = (
            f"⚠️ **تأیید بستن تیکت**\n\n"
            f"🆔 شناسه: `{ticket_id}`\n"
            f"📝 عنوان: {ticket.get('title', 'بدون عنوان')}\n"
            f"👤 کاربر: {ticket.get('user_name', 'نامشخص')}\n"
            f"📋 وضعیت فعلی: {ticket.get('status', 'نامشخص')}\n\n"
            f"آیا از بستن این تیکت اطمینان دارید؟\n"
            f"پس از بستن، کاربر نمی‌تواند پاسخ جدیدی ارسال کند."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، بسته شود",
                        callback_data=f"admin_tickets_close_execute:{ticket_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"admin_tickets_view:{ticket_id}"
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
    except DatabaseError as e:
        logger.error(f"Database error in close_ticket: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات تیکت.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in close_ticket: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش تأییدیه بستن.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def execute_close_ticket(query: CallbackQuery) -> None:
    """
    Execute closing the ticket.
    Callback data format: "admin_tickets_close_execute:{ticket_id}"
    """
    try:
        _, ticket_id_str = query.data.split(":", 1)
        ticket_id = int(ticket_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه تیکت نامعتبر است.", show_alert=True)
        return

    try:
        service = TicketService()
        result = await service.close_ticket(
            ticket_id=ticket_id,
            closed_by=query.from_user.id,
        )

        text = (
            f"✅ **تیکت با موفقیت بسته شد!**\n\n"
            f"🆔 شناسه: `{ticket_id}`\n"
            f"📝 عنوان: {result.get('title', 'بدون عنوان')}\n"
            f"👤 بسته شده توسط: {query.from_user.full_name}\n"
            f"📅 تاریخ بسته شدن: {result.get('closed_at', 'نامشخص')}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 مشاهده تیکت",
                        callback_data=f"admin_tickets_view:{ticket_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست تیکت‌ها",
                        callback_data="admin_tickets_list:1"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Ticket {ticket_id} closed by admin {query.from_user.id}")
        await query.answer("تیکت بسته شد!")
    except NotFoundError as e:
        logger.warning(f"Ticket {ticket_id} not found: {e}")
        await query.message.edit_text(
            "❌ تیکت مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("تیکت یافت نشد!", show_alert=True)
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied closing ticket {ticket_id}: {e}")
        await query.message.edit_text(
            "❌ شما مجوز بستن این تیکت را ندارید.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error closing ticket {ticket_id}: {e}")
        await query.message.edit_text(
            "❌ خطا در بستن تیکت. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error closing ticket {ticket_id}: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در بستن تیکت.",
            reply_markup=get_back_button("admin_tickets_list:1")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)