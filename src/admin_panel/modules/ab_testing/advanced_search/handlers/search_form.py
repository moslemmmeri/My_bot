# src/admin_panel/modules/advanced_search/handlers/search_form.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.advanced_search.keyboards import SearchFiltersKeyboard

logger = get_logger(__name__)


@requires_admin
async def search_form(query: CallbackQuery) -> None:
    """
    Display the advanced search form with search type selection.
    Callback data: "admin_search" or "admin_search_form"
    """
    try:
        text = (
            "🔍 **جستجوی پیشرفته**\n\n"
            "نوع جستجوی مورد نظر را انتخاب کنید:\n\n"
            "👤 جستجوی کاربران\n"
            "🛒 جستجوی سفارشات\n"
            "📝 جستجوی محتوا\n"
            "📊 جستجوی گزارش‌ها\n"
            "🔎 جستجوی عمومی"
        )

        keyboard = SearchFiltersKeyboard.get_search_type_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in search_form: {e}")
        await query.message.edit_text(
            "❌ خطا در نمایش فرم جستجو.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in search_form: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش فرم جستجو.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def search_type_selected(query: CallbackQuery) -> None:
    """
    Handle selection of search type and show appropriate input prompt.
    Callback data format: "admin_search_type:{search_type}"
    """
    try:
        _, search_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ نوع جستجو نامعتبر است.", show_alert=True)
        return

    # Map search type to display name
    type_names = {
        "users": "کاربران",
        "orders": "سفارشات",
        "content": "محتوا",
        "reports": "گزارش‌ها",
        "general": "عمومی",
    }

    display_name = type_names.get(search_type, search_type)

    # Ask for search query
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_search"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"🔍 **جستجوی {display_name}**\n\n"
        f"لطفاً عبارت جستجو را وارد کنید:\n"
        f"(برای جستجوی پیشرفته از فیلترهای جداگانه استفاده کنید)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def search_advanced_menu(query: CallbackQuery) -> None:
    """
    Show advanced search filters (e.g., date range, status, etc.)
    Callback data: "admin_search_advanced"
    """
    try:
        text = (
            "🔍 **جستجوی پیشرفته با فیلتر**\n\n"
            "یکی از فیلترهای زیر را انتخاب کنید:\n"
        )
        keyboard = SearchFiltersKeyboard.get_advanced_filters_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error in search_advanced_menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش فیلترهای پیشرفته.",
            reply_markup=get_back_button("admin_search")
        )
        await query.answer("خطا!", show_alert=True)