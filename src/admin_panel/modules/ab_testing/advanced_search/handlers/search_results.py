# src/admin_panel/modules/advanced_search/handlers/search_results.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, ValidationError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.advanced_search.services import SearchEngine
from admin_panel.modules.advanced_search.keyboards import SearchResultKeyboard

logger = get_logger(__name__)


@requires_admin
async def search_results(query: CallbackQuery) -> None:
    """
    Display search results for the given query.
    Callback data format: 
        - "admin_search_results:{query_type}:{query_text}:{page}"
        - or when called from text input, expect query stored in user state.
    For now, we handle callback with embedded query.
    """
    try:
        # Parse callback data: admin_search_results:type:query:page
        parts = query.data.split(":", 3)
        if len(parts) >= 4:
            _, search_type, query_text, page_str = parts[0], parts[1], parts[2], parts[3]
            page = int(page_str)
        else:
            # Fallback: only page provided, assume we have stored state
            # In real implementation, you'd retrieve query from user state
            await query.answer("عبارت جستجو مشخص نشده است.", show_alert=True)
            return

        if not query_text.strip():
            await query.message.edit_text(
                "❌ عبارت جستجو نمی‌تواند خالی باشد.",
                reply_markup=get_back_button("admin_search")
            )
            await query.answer()
            return

        # Perform search
        service = SearchEngine()
        result = await service.search(
            query_type=search_type,
            query=query_text,
            page=page,
            page_size=10,
        )

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        # Build result text
        if not items:
            text = f"🔍 **نتیجه جستجو**\n\n"
            text += f"عبارت: `{query_text}`\n"
            text += f"نوع: {search_type}\n"
            text += f"تعداد نتایج: {total}\n\n"
            text += "هیچ نتیجه‌ای یافت نشد."
            keyboard = SearchResultKeyboard.get_empty_keyboard(
                back_callback="admin_search"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = f"🔍 **نتیجه جستجو** (صفحه {current_page} از {total_pages})\n\n"
        text += f"عبارت: `{query_text}`\n"
        text += f"نوع: {search_type}\n"
        text += f"تعداد نتایج: {total}\n\n"

        # Display items with index
        for idx, item in enumerate(items, start=(page-1)*10 + 1):
            title = item.get("title") or item.get("name") or item.get("username") or "بدون عنوان"
            item_id = item.get("id")
            text += f"{idx}. **{title}** (🆔 {item_id})\n"
            # Add some extra info based on type
            if search_type == "users":
                username = item.get("username", "بدون نام")
                text += f"   👤 @{username}\n"
            elif search_type == "orders":
                total_amount = item.get("total_amount", 0)
                status = item.get("status", "نامشخص")
                text += f"   💰 {total_amount:,} تومان | 📊 {status}\n"
            elif search_type == "content":
                content_type = item.get("type", "unknown")
                status = item.get("status", "draft")
                text += f"   📂 {content_type} | 📊 {status}\n"
            text += "\n"

        # Build pagination keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[]
        )
        # Pagination row
        nav_row = []
        if current_page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=f"admin_search_results:{search_type}:{query_text}:{current_page - 1}"
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_search_results_noop"
            )
        )
        if current_page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=f"admin_search_results:{search_type}:{query_text}:{current_page + 1}"
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Action rows: each item can be clicked for view
        # Limit to 5 items per page for cleanliness
        for item in items[:5]:
            item_id = item.get("id")
            title = item.get("title") or item.get("name") or item.get("username") or "جزئیات"
            if len(title) > 20:
                title = title[:18] + "..."
            # Different callbacks based on type
            if search_type == "users":
                callback = f"admin_users_view:{item_id}"
            elif search_type == "orders":
                callback = f"admin_orders_view:{item_id}"
            elif search_type == "content":
                callback = f"admin_content_view:{item_id}"
            else:
                callback = f"admin_search_view:{item_id}"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📄 {title}",
                    callback_data=callback
                )
            ])

        # Bottom actions
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔄 جستجوی جدید",
                callback_data="admin_search"
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
    except ValidationError as e:
        logger.warning(f"Validation error in search_results: {e}")
        await query.message.edit_text(
            f"❌ خطا در جستجو: {str(e)}",
            reply_markup=get_back_button("admin_search")
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except NotFoundError as e:
        logger.warning(f"No results found: {e}")
        # Already handled via empty results
        pass
    except DatabaseError as e:
        logger.error(f"Database error in search_results: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت نتایج جستجو. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_search")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in search_results: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در جستجو. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=get_back_button("admin_search")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)