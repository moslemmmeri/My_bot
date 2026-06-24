# src/admin_panel/modules/settings/handlers/view_settings.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.settings.services import SettingsCRUDService
from admin_panel.modules.settings.keyboards import SettingsMenuKeyboard, SettingsCategoryKeyboard

logger = get_logger(__name__)


@requires_admin
async def view_settings(query: CallbackQuery) -> None:
    """
    Display the main settings menu with categories.
    Callback data: "admin_settings" or "admin_settings_view"
    """
    try:
        text = (
            "⚙️ **تنظیمات سیستم**\n\n"
            "مدیریت تنظیمات و پیکربندی‌های سیستم.\n"
            "یکی از دسته‌بندی‌های زیر را انتخاب کنید:"
        )

        keyboard = SettingsMenuKeyboard.get_main_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in view_settings: {e}")
        await query.message.edit_text(
            "❌ خطا در نمایش تنظیمات. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in view_settings: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش تنظیمات.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def list_settings(query: CallbackQuery) -> None:
    """
    List settings by category.
    Callback data format: "admin_settings_category:{category}"
    """
    try:
        _, category = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ دسته‌بندی نامعتبر است.", show_alert=True)
        return

    try:
        service = SettingsCRUDService()
        settings = await service.list_settings_by_category(category)

        if not settings:
            text = f"⚙️ **تنظیمات - {category}**\n\n"
            text += "هیچ تنظیماتی در این دسته‌بندی یافت نشد."
            keyboard = SettingsCategoryKeyboard.get_empty_keyboard(
                back_callback="admin_settings"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = f"⚙️ **تنظیمات - {category}**\n\n"
        for key, value in settings.items():
            text += f"🔹 **{key}**: `{value}`\n"

        text += "\nبرای ویرایش هر تنظیم، روی دکمه مربوطه کلیک کنید."

        keyboard = SettingsCategoryKeyboard.get_category_keyboard(
            category=category,
            settings=settings,
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except NotFoundError as e:
        logger.warning(f"Category not found: {e}")
        await query.message.edit_text(
            f"❌ دسته‌بندی `{category}` یافت نشد.",
            reply_markup=get_back_button("admin_settings")
        )
        await query.answer("دسته‌بندی یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in list_settings: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت تنظیمات. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_settings")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_settings: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در دریافت تنظیمات.",
            reply_markup=get_back_button("admin_settings")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def view_setting_detail(query: CallbackQuery) -> None:
    """
    View detail of a specific setting.
    Callback data format: "admin_settings_detail:{category}:{key}"
    """
    try:
        _, category, key = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = SettingsCRUDService()
        setting = await service.get_setting(category, key)

        if not setting:
            await query.message.edit_text(
                f"❌ تنظیم `{key}` در دسته‌بندی `{category}` یافت نشد.",
                reply_markup=get_back_button(f"admin_settings_category:{category}")
            )
            await query.answer("تنظیم یافت نشد!", show_alert=True)
            return

        text = (
            f"⚙️ **جزئیات تنظیم**\n\n"
            f"📂 دسته‌بندی: {category}\n"
            f"🔑 کلید: `{key}`\n"
            f"📊 مقدار: `{setting.get('value')}`\n"
            f"📝 توضیحات: {setting.get('description', 'بدون توضیح')}\n"
            f"📅 آخرین بروزرسانی: {setting.get('updated_at', 'نامشخص')}\n"
            f"👤 بروزرسانی توسط: {setting.get('updated_by', 'نامشخص')}"
        )

        keyboard = SettingsActionsKeyboard.get_detail_keyboard(
            category=category,
            key=key,
            back_callback=f"admin_settings_category:{category}"
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except NotFoundError as e:
        logger.warning(f"Setting not found: {e}")
        await query.message.edit_text(
            f"❌ تنظیم `{key}` یافت نشد.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("تنظیم یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in view_setting_detail: {e}")
        await query.answer("❌ خطا در دریافت تنظیم!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in view_setting_detail: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)