# src/admin_panel/modules/logs_viewer/handlers/view_logs.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.logs_viewer.services import LogReaderService
from admin_panel.modules.logs_viewer.keyboards import LogsViewerMenuKeyboard, LogFiltersKeyboard

logger = get_logger(__name__)


@requires_admin
async def view_logs(query: CallbackQuery) -> None:
    """
    Display the main logs viewer menu.
    Callback data: "admin_logs"
    """
    try:
        text = (
            "📑 **مشاهده لاگ‌ها**\n\n"
            "مدیریت و مشاهده لاگ‌های سیستم.\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = LogsViewerMenuKeyboard.get_main_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing logs viewer: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش پنل لاگ‌ها.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def view_log_file(query: CallbackQuery) -> None:
    """
    View the contents of a specific log file.
    Callback data format: "admin_logs_view:{log_file}:{page}"
    """
    try:
        parts = query.data.split(":")
        if len(parts) >= 3:
            _, log_file, page_str = parts[0], parts[1], parts[2]
            page = int(page_str) if page_str.isdigit() else 1
        else:
            _, log_file = query.data.split(":", 1)
            page = 1
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = LogReaderService()
        result = await service.read_log_file(
            filename=log_file,
            page=page,
            page_size=50,
        )

        lines = result.get("lines", [])
        total_lines = result.get("total_lines", 0)
        current_page = result.get("page", 1)
        total_pages = result.get("total_pages", 1)

        if not lines:
            text = f"📑 **لاگ: {log_file}**\n\n"
            text += "هیچ خطی یافت نشد یا فایل خالی است."
            keyboard = LogFiltersKeyboard.get_empty_keyboard(
                back_callback="admin_logs"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = f"📑 **لاگ: {log_file}** (صفحه {current_page} از {total_pages})\n\n"
        text += "```\n"
        for line in lines:
            text += line + "\n"
        text += "```"

        # Build pagination keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[]
        )
        nav_row = []
        if current_page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=f"admin_logs_view:{log_file}:{current_page - 1}"
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
                    callback_data=f"admin_logs_view:{log_file}:{current_page + 1}"
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Additional actions
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔄 بروزرسانی",
                callback_data=f"admin_logs_view:{log_file}:{current_page}"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔍 جستجو در لاگ",
                callback_data=f"admin_logs_search:{log_file}"
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
    except NotFoundError as e:
        logger.warning(f"Log file not found: {e}")
        await query.message.edit_text(
            f"❌ فایل لاگ `{log_file}` یافت نشد.",
            reply_markup=get_back_button("admin_logs")
        )
        await query.answer("فایل لاگ یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Error reading log file: {e}")
        await query.message.edit_text(
            "❌ خطا در خواندن لاگ. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_logs")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in view_log_file: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش لاگ.",
            reply_markup=get_back_button("admin_logs")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def list_log_files(query: CallbackQuery) -> None:
    """
    List all available log files.
    Callback data: "admin_logs_list"
    """
    try:
        service = LogReaderService()
        files = await service.list_log_files()

        if not files:
            text = "📑 **لیست لاگ‌ها**\n\nهیچ فایل لاگی یافت نشد."
            keyboard = LogFiltersKeyboard.get_empty_keyboard(
                back_callback="admin_logs"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = "📑 **لیست لاگ‌ها**\n\n"
        for idx, log_file in enumerate(files, start=1):
            filename = log_file.get("name")
            size = log_file.get("size", 0)
            modified = log_file.get("modified", "نامشخص")
            text += f"{idx}. 📄 `{filename}` ({size/1024:.1f} KB) - {modified}\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[]
        )
        # Add buttons for each log file (limit to 10 for readability)
        for log_file in files[:10]:
            filename = log_file.get("name")
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📄 {filename[:30]}...",
                    callback_data=f"admin_logs_view:{filename}:1"
                )
            ])

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به منوی لاگ‌ها",
                callback_data="admin_logs"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Error listing log files: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست لاگ‌ها.",
            reply_markup=get_back_button("admin_logs")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_log_files: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره.",
            reply_markup=get_back_button("admin_logs")
        )
        await query.answer("خطا!", show_alert=True)