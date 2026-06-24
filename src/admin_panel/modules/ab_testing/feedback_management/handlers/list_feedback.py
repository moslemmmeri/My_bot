# src/admin_panel/modules/feedback_management/handlers/list_feedback.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.feedback_management.services import FeedbackService
from admin_panel.modules.feedback_management.keyboards import FeedbackFilterKeyboard

logger = get_logger(__name__)


@requires_admin
async def list_feedback(query: CallbackQuery) -> None:
    """
    Display the list of feedback entries with pagination and filters.
    Callback data format:
        - "admin_feedback" (main menu)
        - "admin_feedback_list:{page}" (pagination)
        - "admin_feedback_list:{page}:{status}" (with status filter)
        - "admin_feedback_list:{page}:{status}:{rating}" (with rating filter)
    """
    try:
        # Parse callback data
        parts = query.data.split(":")
        page = 1
        status = None
        rating = None

        if len(parts) >= 2:
            page = int(parts[1]) if parts[1].isdigit() else 1
        if len(parts) >= 3:
            status = parts[2] if parts[2] != "all" else None
        if len(parts) >= 4:
            rating = parts[3] if parts[3] != "all" else None

        service = FeedbackService()
        result = await service.list_feedback(
            page=page,
            page_size=10,
            status=status,
            rating=rating,
        )

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        # Build text
        if not items:
            text = "💬 **لیست بازخوردها**\n\nهیچ بازخوردی یافت نشد."
            keyboard = FeedbackFilterKeyboard.get_empty_keyboard(
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
            "pending": "🟡 در انتظار",
            "replied": "🔵 پاسخ داده شده",
            "resolved": "🟢 حل شده",
        }

        text = f"💬 **لیست بازخوردها** (صفحه {current_page} از {total_pages})\n\n"
        for idx, feedback in enumerate(items, start=(page-1)*10 + 1):
            feedback_id = feedback.get("id")
            user_name = feedback.get("user_name", "نامشخص")
            rating = feedback.get("rating", 0)
            status = feedback.get("status", "pending")
            message = feedback.get("message", "بدون پیام")[:50]
            created_at = feedback.get("created_at", "نامشخص")

            rating_stars = "⭐" * rating + "☆" * (5 - rating)
            status_display = status_names.get(status, status)

            text += f"{idx}. {rating_stars} **{user_name}**\n"
            text += f"   💬 {message}{'...' if len(feedback.get('message', '')) > 50 else ''}\n"
            text += f"   📋 {status_display} | 📅 {created_at[:10]}\n"
            text += f"   🆔 {feedback_id}\n\n"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Pagination row
        nav_row = []
        if current_page > 1:
            prev_callback = f"admin_feedback_list:{current_page - 1}"
            if status:
                prev_callback += f":{status}"
            if rating:
                prev_callback += f":{rating}"
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=prev_callback
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_feedback_noop"
            )
        )
        if current_page < total_pages:
            next_callback = f"admin_feedback_list:{current_page + 1}"
            if status:
                next_callback += f":{status}"
            if rating:
                next_callback += f":{rating}"
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=next_callback
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Filter row
        filter_row = []
        if status or rating:
            filter_row.append(
                InlineKeyboardButton(
                    text="🧹 پاک کردن فیلترها",
                    callback_data="admin_feedback_list:1"
                )
            )
        else:
            filter_row.append(
                InlineKeyboardButton(
                    text="🔍 فیلتر",
                    callback_data="admin_feedback_filter"
                )
            )
        keyboard.inline_keyboard.append(filter_row)

        # Quick view buttons for first 5 feedback
        for feedback in items[:5]:
            feedback_id = feedback.get("id")
            user_name = feedback.get("user_name", "کاربر")[:15]
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"💬 {user_name}",
                    callback_data=f"admin_feedback_view:{feedback_id}"
                )
            ])

        # Action buttons
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="📊 آمار بازخوردها",
                callback_data="admin_feedback_stats"
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
        logger.error(f"Database error in list_feedback: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست بازخوردها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_feedback: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش لیست بازخوردها.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)