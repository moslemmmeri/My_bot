# src/admin_panel/modules/settings/handlers/edit_setting.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.settings.services import SettingsCRUDService
from admin_panel.modules.settings.keyboards import SettingsActionsKeyboard
from admin_panel.modules.settings.validators import SettingsValidator

logger = get_logger(__name__)


@requires_admin
async def edit_setting(query: CallbackQuery) -> None:
    """
    Start the edit setting process.
    Callback data format: "admin_settings_edit:{category}:{key}"
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

        current_value = setting.get('value', '')
        setting_type = setting.get('type', 'string')

        text = (
            f"✏️ **ویرایش تنظیم**\n\n"
            f"📂 دسته‌بندی: {category}\n"
            f"🔑 کلید: `{key}`\n"
            f"📊 مقدار فعلی: `{current_value}`\n"
            f"📝 توضیحات: {setting.get('description', 'بدون توضیح')}\n\n"
            f"لطفاً مقدار جدید را وارد کنید:"
        )

        # Store context in a temporary keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"admin_settings_detail:{category}:{key}"
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
    except NotFoundError as e:
        logger.warning(f"Setting not found: {e}")
        await query.message.edit_text(
            f"❌ تنظیم `{key}` یافت نشد.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("تنظیم یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in edit_setting: {e}")
        await query.answer("❌ خطا در دریافت تنظیم!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in edit_setting: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def update_setting(query: CallbackQuery) -> None:
    """
    Update the setting with new value.
    Callback data format: "admin_settings_update:{category}:{key}:{value}"
    """
    try:
        _, category, key, value = query.data.split(":", 3)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        # Validate input
        validator = SettingsValidator()
        validated = validator.validate_setting_value(
            category=category,
            key=key,
            value=value,
        )

        # Update setting
        service = SettingsCRUDService()
        updated = await service.update_setting(
            category=category,
            key=key,
            value=validated["value"],
            updated_by=query.from_user.id,
        )

        text = (
            f"✅ **تنظیم با موفقیت بروزرسانی شد!**\n\n"
            f"📂 دسته‌بندی: {category}\n"
            f"🔑 کلید: `{key}`\n"
            f"📊 مقدار جدید: `{updated.get('value')}`\n"
            f"👤 بروزرسانی توسط: {query.from_user.id}\n"
            f"📅 زمان: {updated.get('updated_at', 'نامشخص')}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به جزئیات",
                        callback_data=f"admin_settings_detail:{category}:{key}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست تنظیمات",
                        callback_data=f"admin_settings_category:{category}"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Setting {category}:{key} updated to {validated['value']} by admin {query.from_user.id}")
        await query.answer("تنظیم بروزرسانی شد!")
    except ValidationError as e:
        logger.warning(f"Validation error in update_setting: {e}")
        await query.message.edit_text(
            f"❌ خطای اعتبارسنجی:\n{str(e)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔄 تلاش مجدد",
                            callback_data=f"admin_settings_edit:{category}:{key}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت",
                            callback_data=f"admin_settings_detail:{category}:{key}"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except NotFoundError as e:
        logger.warning(f"Setting not found: {e}")
        await query.message.edit_text(
            f"❌ تنظیم `{key}` یافت نشد.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("تنظیم یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in update_setting: {e}")
        await query.message.edit_text(
            "❌ خطا در بروزرسانی تنظیم. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("خطا در بروزرسانی!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in update_setting: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در بروزرسانی تنظیم.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def reset_setting(query: CallbackQuery) -> None:
    """
    Reset a setting to its default value.
    Callback data format: "admin_settings_reset:{category}:{key}"
    """
    try:
        _, category, key = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Show confirmation
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، بازنشانی شود",
                    callback_data=f"admin_settings_reset_confirm:{category}:{key}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data=f"admin_settings_detail:{category}:{key}"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"⚠️ **تأیید بازنشانی تنظیم**\n\n"
        f"📂 دسته‌بندی: {category}\n"
        f"🔑 کلید: `{key}`\n\n"
        f"آیا از بازنشانی این تنظیم به مقدار پیش‌فرض اطمینان دارید؟\n"
        f"این عمل غیرقابل بازگشت است.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def reset_setting_confirm(query: CallbackQuery) -> None:
    """
    Execute reset setting to default.
    Callback data format: "admin_settings_reset_confirm:{category}:{key}"
    """
    try:
        _, category, key = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = SettingsCRUDService()
        reset = await service.reset_setting(
            category=category,
            key=key,
            reset_by=query.from_user.id,
        )

        text = (
            f"✅ **تنظیم با موفقیت بازنشانی شد!**\n\n"
            f"📂 دسته‌بندی: {category}\n"
            f"🔑 کلید: `{key}`\n"
            f"📊 مقدار جدید: `{reset.get('value')}`\n"
            f"👤 بازنشانی توسط: {query.from_user.id}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به جزئیات",
                        callback_data=f"admin_settings_detail:{category}:{key}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست تنظیمات",
                        callback_data=f"admin_settings_category:{category}"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Setting {category}:{key} reset to default by admin {query.from_user.id}")
        await query.answer("تنظیم بازنشانی شد!")
    except NotFoundError as e:
        logger.warning(f"Setting not found: {e}")
        await query.message.edit_text(
            f"❌ تنظیم `{key}` یافت نشد.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("تنظیم یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in reset_setting: {e}")
        await query.message.edit_text(
            "❌ خطا در بازنشانی تنظیم. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("خطا در بازنشانی!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in reset_setting: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در بازنشانی تنظیم.",
            reply_markup=get_back_button(f"admin_settings_category:{category}")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)