# src/admin_panel/modules/admin_management/handlers/list_admins.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.admin_management.services import AdminCRUDService
from admin_panel.modules.admin_management.keyboards import AdminListKeyboard

logger = get_logger(__name__)


@requires_admin
async def list_admins(query: CallbackQuery) -> None:
    """
    Display the list of admin users with pagination.
    Callback data format: "admin_admins" or "admin_admins_page:{page}"
    """
    try:
        # Parse page number from callback data
        page = 1
        if ":" in query.data:
            try:
                page = int(query.data.split(":", 1)[1])
            except ValueError:
                page = 1

        service = AdminCRUDService()
        result = await service.list_admins(page=page, page_size=10)

        admins = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        if not admins:
            text = "👤 **مدیریت ادمین‌ها**\n\nهیچ ادمینی یافت نشد."
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ افزودن ادمین جدید",
                            callback_data="admin_admins_add"
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

        text = f"👤 **مدیریت ادمین‌ها** (صفحه {current_page} از {total_pages})\n\n"
        for idx, admin in enumerate(admins, start=1):
            admin_id = admin.get("id")
            username = admin.get("username", "بدون نام")
            role = admin.get("role", "admin")
            is_active = admin.get("is_active", True)
            status_icon = "✅" if is_active else "❌"
            text += f"{idx}. {status_icon} **{username}**\n"
            text += f"   🆔 {admin_id} | 📋 {role}\n\n"

        # Build keyboard using AdminListKeyboard
        keyboard = AdminListKeyboard.get_list_keyboard(
            admins=admins,
            page=current_page,
            total_pages=total_pages,
        )

        # Add action buttons
        action_row = [
            InlineKeyboardButton(
                text="➕ افزودن ادمین جدید",
                callback_data="admin_admins_add"
            )
        ]
        keyboard.inline_keyboard.append(action_row)
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
        logger.error(f"Database error in list_admins: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست ادمین‌ها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا در دریافت لیست ادمین‌ها!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_admins: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)