# src/admin_panel/modules/error_logs/handlers/view_errors.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.error_logs.services import ErrorLogService
from admin_panel.modules.error_logs.keyboards import ErrorLogsMenuKeyboard, ErrorFiltersKeyboard

logger = get_logger(__name__)


@requires_admin
async def view_errors(query: CallbackQuery) -> None:
    """
    Display the main error logs menu.
    Callback data: "admin_errors"
    """
    try:
        text = (
            "🚨 **مشاهده خطاها**\n\n"
            "مدیریت و مشاهده خطاهای ثبت‌شده در سیستم.\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = ErrorLogsMenuKeyboard.get_main_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing error logs menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش پنل خطاها.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def view_error_list(query: CallbackQuery) -> None:
    """
    Display list of error logs with pagination and filters.
    Callback data format: "admin_errors_list:{page}" or "admin_errors_list:{page}:{level}"
    """
    try:
        # Parse callback data
        parts = query.data.split(":")
        page = 1
        level = None
        if len(parts) >= 2:
            page = int(parts[1]) if parts[1].isdigit() else 1
        if len(parts) >= 3:
            level = parts[2] if parts[2] != "all" else None

        service = ErrorLogService()
        result = await service.list_errors(
            page=page,
            page_size=20,
            level=level,
        )

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 19) // 20 if total > 0 else 1

        if not items:
            text = "🚨 **لیست خطاها**\n\nهیچ خطایی یافت نشد."
            keyboard = ErrorFiltersKeyboard.get_empty_keyboard(
                back_callback="admin_errors"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = f"🚨 **لیست خطاها** (صفحه {current_page} از {total_pages})\n\n"
        for idx, error in enumerate(items, start=(page-1)*20 + 1):
            error_id = error.get("id")
            level = error.get("level", "UNKNOWN")
            message = error.get("message", "بدون پیام")
            timestamp = error.get("created_at", "نامشخص")
            source = error.get("source", "نامشخص")

            # Emoji based on level
            level_emoji = {
                "ERROR": "❌",
                "CRITICAL": "🚨",
                "WARNING": "⚠️",
                "INFO": "ℹ️",
            }.get(level, "📌")

            text += f"{idx}. {level_emoji} **{level}** - {timestamp}\n"
            text += f"   📝 {message[:80]}{'...' if len(message) > 80 else ''}\n"
            text += f"   📂 {source}\n"
            text += f"   🆔 {error_id}\n\n"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[]
        )

        # Pagination
        nav_row = []
        if current_page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=f"admin_errors_list:{current_page - 1}"
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_errors_noop"
            )
        )
        if current_page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=f"admin_errors_list:{current_page + 1}"
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Filter by level
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔍 فیلتر بر اساس سطح",
                callback_data="admin_errors_filter_level"
            )
        ])

        # Add view detail buttons for first 5 errors
        for error in items[:5]:
            error_id = error.get("id")
            level = error.get("level", "UNKNOWN")
            message = error.get("message", "بدون پیام")[:20]
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📄 {level}: {message}",
                    callback_data=f"admin_errors_detail:{error_id}"
                )
            ])

        # Action buttons
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🧹 پاک کردن خطاها",
                callback_data="admin_errors_clear_confirm"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="📊 آمار خطاها",
                callback_data="admin_errors_stats"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به منوی خطاها",
                callback_data="admin_errors"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in view_error_list: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست خطاها.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in view_error_list: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش لیست خطاها.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)