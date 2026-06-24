# src/admin_panel/modules/content_management/handlers/list_content.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.content_management.services import ContentCRUDService

logger = get_logger(__name__)


@requires_admin
async def list_content(query: CallbackQuery) -> None:
    """Display list of content items with pagination."""
    try:
        # Parse page from callback data
        page = 1
        if ":" in query.data:
            try:
                page = int(query.data.split(":", 1)[1])
            except ValueError:
                page = 1

        service = ContentCRUDService()
        result = await service.list_content(page=page, page_size=10)

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        if not items:
            text = "📝 **مدیریت محتوا**\n\nهیچ محتوایی یافت نشد."
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ افزودن محتوای جدید",
                            callback_data="admin_content_add"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به پنل مدیریت",
                            callback_data="admin_panel"
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
            return

        text = f"📝 **مدیریت محتوا** (صفحه {current_page} از {total_pages})\n\n"
        for idx, item in enumerate(items, start=1):
            content_id = item.get("id")
            title = item.get("title", "بدون عنوان")
            content_type = item.get("type", "unknown")
            status = item.get("status", "draft")
            status_icon = "✅" if status == "published" else "📝"
            text += f"{idx}. {status_icon} **{title}**\n"
            text += f"   🆔 {content_id} | 📂 {content_type}\n\n"

        # Build pagination keyboard
        keyboard = []
        nav_row = []
        if current_page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=f"admin_content_list:{current_page - 1}"
                )
            )
        if current_page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=f"admin_content_list:{current_page + 1}"
                )
            )
        if nav_row:
            keyboard.append(nav_row)

        # Action buttons for each content item (show first 5)
        for item in items[:5]:
            content_id = item.get("id")
            title = item.get("title", "بدون عنوان")
            if len(title) > 20:
                title = title[:18] + "..."
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📄 {title}",
                    callback_data=f"admin_content_view:{content_id}"
                )
            ])

        # Add action buttons
        keyboard.append([
            InlineKeyboardButton(
                text="➕ افزودن محتوای جدید",
                callback_data="admin_content_add"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔍 جستجو",
                callback_data="admin_content_search"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به پنل مدیریت",
                callback_data="admin_panel"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in list_content: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست محتوا. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا در دریافت لیست محتوا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_content: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)