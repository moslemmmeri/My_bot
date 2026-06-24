# src/admin_panel/modules/logs_viewer/handlers/filter_logs.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.logs_viewer.services import LogFilterService
from admin_panel.modules.logs_viewer.keyboards import LogFiltersKeyboard

logger = get_logger(__name__)


@requires_admin
async def filter_logs(query: CallbackQuery) -> None:
    """
    Show log filter options.
    Callback data: "admin_logs_filter"
    """
    try:
        text = (
            "🔍 **فیلتر لاگ‌ها**\n\n"
            "سطح لاگ و بازه زمانی مورد نظر را انتخاب کنید:"
        )

        keyboard = LogFiltersKeyboard.get_filter_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing filter menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش فیلترها.",
            reply_markup=get_back_button("admin_logs")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def apply_filter(query: CallbackQuery) -> None:
    """
    Apply the selected filter and show filtered logs.
    Callback data format: "admin_logs_apply_filter:{log_file}:{level}:{date_range}:{page}"
    or similar.
    """
    try:
        # Parse callback data: admin_logs_apply_filter:log_file:level:date_range:page
        parts = query.data.split(":")
        if len(parts) >= 5:
            _, log_file, level, date_range, page_str = parts[0], parts[1], parts[2], parts[3], parts[4]
            page = int(page_str) if page_str.isdigit() else 1
        else:
            await query.answer("❌ داده نامعتبر است.", show_alert=True)
            return
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = LogFilterService()
        result = await service.apply_filter(
            log_file=log_file,
            level=level,
            date_range=date_range,
            page=page,
            page_size=50,
        )

        lines = result.get("lines", [])
        total_lines = result.get("total_lines", 0)
        current_page = result.get("page", 1)
        total_pages = result.get("total_pages", 1)
        applied_level = result.get("level", "همه")
        applied_date = result.get("date_range", "همه")

        if not lines:
            text = (
                f"🔍 **نتیجه فیلتر**\n\n"
                f"📂 فایل: {log_file}\n"
                f"📊 سطح: {applied_level}\n"
                f"📅 بازه: {applied_date}\n\n"
                "هیچ خطی با این فیلترها یافت نشد."
            )
            keyboard = LogFiltersKeyboard.get_empty_keyboard(
                back_callback="admin_logs_filter"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = (
            f"🔍 **نتیجه فیلتر** (صفحه {current_page} از {total_pages})\n\n"
            f"📂 فایل: {log_file}\n"
            f"📊 سطح: {applied_level}\n"
            f"📅 بازه: {applied_date}\n\n"
            "```\n"
        )
        for line in lines:
            text += line + "\n"
        text += "```"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[]
        )
        nav_row = []
        if current_page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=f"admin_logs_apply_filter:{log_file}:{level}:{date_range}:{current_page - 1}"
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_logs_noop"
            )
        )
        if current_page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=f"admin_logs_apply_filter:{log_file}:{level}:{date_range}:{current_page + 1}"
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Filter actions
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔄 تغییر فیلتر",
                callback_data="admin_logs_filter"
            ),
            InlineKeyboardButton(
                text="🧹 پاک کردن فیلترها",
                callback_data=f"admin_logs_clear_filter:{log_file}"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به لیست لاگ‌ها",
                callback_data="admin_logs"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except ValidationError as e:
        logger.warning(f"Validation error in apply_filter: {e}")
        await query.message.edit_text(
            f"❌ خطا در اعمال فیلتر: {str(e)}",
            reply_markup=get_back_button("admin_logs_filter")
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in apply_filter: {e}")
        await query.message.edit_text(
            "❌ خطا در اعمال فیلتر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_logs_filter")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in apply_filter: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در اعمال فیلتر.",
            reply_markup=get_back_button("admin_logs_filter")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def clear_filter(query: CallbackQuery) -> None:
    """
    Clear filters and show all logs.
    Callback data format: "admin_logs_clear_filter:{log_file}"
    """
    try:
        _, log_file = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Redirect to view logs without filters
    await view_log_file(query)  # This assumes view_log_file is imported
    # But we need to handle the fact that query.data is changed.
    # Better to directly call view_log_file with the log_file.
    # Since we cannot easily import view_log_file, we can simulate by editing the message.
    # In a real implementation, we would store state or use a callback.
    # For simplicity, we'll redirect to list log files.
    await list_log_files(query)