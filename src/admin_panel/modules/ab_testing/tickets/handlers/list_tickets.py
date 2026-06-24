# src/admin_panel/modules/tickets/handlers/list_tickets.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.tickets.services import TicketService
from admin_panel.modules.tickets.keyboards import TicketFilterKeyboard

logger = get_logger(__name__)


@requires_admin
async def list_tickets(query: CallbackQuery) -> None:
    """
    Display the list of tickets with pagination and filters.
    Callback data format: 
        - "admin_tickets" (main menu)
        - "admin_tickets_list:{page}" (pagination)
        - "admin_tickets_list:{page}:{status}" (with status filter)
    """
    try:
        # Parse callback data
        parts = query.data.split(":")
        page = 1
        status = None
        
        if len(parts) >= 2:
            page = int(parts[1]) if parts[1].isdigit() else 1
        if len(parts) >= 3:
            status = parts[2] if parts[2] != "all" else None

        service = TicketService()
        result = await service.list_tickets(
            page=page,
            page_size=10,
            status=status,
        )

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        # Build text
        if not items:
            text = "🎫 **لیست تیکت‌ها**\n\nهیچ تیکتی یافت نشد."
            keyboard = TicketFilterKeyboard.get_empty_keyboard(
                back_callback="admin_panel"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        status_names = {
            "open": "🟢 باز",
            "in_progress": "🟡 در حال بررسی",
            "resolved": "🔵 حل شده",
            "closed": "⚪ بسته",
        }
        priority_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
            "critical": "🚨",
        }

        text = f"🎫 **لیست تیکت‌ها** (صفحه {current_page} از {total_pages})\n\n"
        for idx, ticket in enumerate(items, start=(page-1)*10 + 1):
            ticket_id = ticket.get("id")
            title = ticket.get("title", "بدون عنوان")
            status = ticket.get("status", "open")
            priority = ticket.get("priority", "medium")
            user = ticket.get("user_name", "نامشخص")
            created_at = ticket.get("created_at", "نامشخص")
            status_display = status_names.get(status, status)
            priority_icon = priority_emoji.get(priority, "🟡")

            text += f"{idx}. {priority_icon} **{title}**\n"
            text += f"   📋 {status_display} | 👤 {user} | 📅 {created_at[:10]}\n"
            text += f"   🆔 {ticket_id}\n\n"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Pagination row
        nav_row = []
        if current_page > 1:
            prev_callback = f"admin_tickets_list:{current_page - 1}"
            if status:
                prev_callback += f":{status}"
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=prev_callback
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_tickets_noop"
            )
        )
        if current_page < total_pages:
            next_callback = f"admin_tickets_list:{current_page + 1}"
            if status:
                next_callback += f":{status}"
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=next_callback
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Filter by status (show only if not already filtered)
        filter_row = []
        if status:
            filter_row.append(
                InlineKeyboardButton(
                    text="🧹 پاک کردن فیلتر",
                    callback_data="admin_tickets_list:1"
                )
            )
        else:
            filter_row.append(
                InlineKeyboardButton(
                    text="🔍 فیلتر بر اساس وضعیت",
                    callback_data="admin_tickets_filter_status"
                )
            )
        keyboard.inline_keyboard.append(filter_row)

        # Quick view buttons for first 5 tickets
        for ticket in items[:5]:
            ticket_id = ticket.get("id")
            title = ticket.get("title", "بدون عنوان")[:20]
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📄 {title}",
                    callback_data=f"admin_tickets_view:{ticket_id}"
                )
            ])

        # Stats and actions
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="📊 آمار تیکت‌ها",
                callback_data="admin_tickets_stats"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به پنل مدیریت",
                callback_data="admin_panel"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in list_tickets: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست تیکت‌ها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_tickets: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش لیست تیکت‌ها.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)