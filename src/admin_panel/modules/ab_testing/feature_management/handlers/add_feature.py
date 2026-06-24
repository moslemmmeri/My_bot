# src/admin_panel/modules/feature_management/handlers/add_feature.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.feature_management.services import FeatureService
from admin_panel.modules.feature_management.keyboards import FeatureActionsKeyboard
from admin_panel.modules.feature_management.validators import FeatureValidator

logger = get_logger(__name__)


@requires_admin
async def add_feature(query: CallbackQuery) -> None:
    """
    Start the feature addition process.
    Callback data: "admin_features_add"
    """
    try:
        text = (
            "➕ **افزودن فیچر جدید**\n\n"
            "لطفاً **نام** فیچر را وارد کنید:"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data="admin_features"
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
    except Exception as e:
        logger.error(f"Error in add_feature: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در شروع افزودن فیچر.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def add_feature_name(query: CallbackQuery) -> None:
    """
    Handle feature name input and ask for description.
    Callback data format: "admin_features_add_name:{name}"
    """
    try:
        _, name = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ نام فیچر نامعتبر است.", show_alert=True)
        return

    # Validate name (basic)
    if not name or len(name.strip()) == 0:
        await query.answer("❌ نام فیچر نمی‌تواند خالی باشد.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش نام",
                    callback_data="admin_features_add_retry_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_features"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"➕ **افزودن فیچر جدید**\n\n"
        f"🏷️ نام: `{name}`\n\n"
        f"لطفاً **توضیحات** فیچر را وارد کنید:\n"
        f"(اختیاری - برای رد کردن، روی دکمه رد کردن کلیک کنید)",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏭️ رد کردن توضیحات",
                        callback_data=f"admin_features_add_description_skip:{name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به ویرایش نام",
                        callback_data="admin_features_add_retry_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data="admin_features"
                    )
                ]
            ]
        ),
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def add_feature_description(query: CallbackQuery) -> None:
    """
    Handle description input and ask for status.
    Callback data format: "admin_features_add_description:{name}:{description}"
    or "admin_features_add_description_skip:{name}" for skipping.
    """
    try:
        parts = query.data.split(":", 2)
        if parts[0] == "admin_features_add_description_skip":
            _, name = parts[0], parts[1]
            description = ""
        else:
            _, name, description = parts[0], parts[1], parts[2]
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Show status selection
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ فعال",
                    callback_data=f"admin_features_add_status:{name}:{description}:true"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ غیرفعال",
                    callback_data=f"admin_features_add_status:{name}:{description}:false"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش توضیحات",
                    callback_data=f"admin_features_add_retry_description:{name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_features"
                )
            ]
        ]
    )

    desc_display = description[:100] + "..." if len(description) > 100 else description
    await query.message.edit_text(
        f"➕ **افزودن فیچر جدید**\n\n"
        f"🏷️ نام: `{name}`\n"
        f"📝 توضیحات: {desc_display if desc_display else '(ندارد)'}\n\n"
        f"لطفاً **وضعیت اولیه** فیچر را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def add_feature_status(query: CallbackQuery) -> None:
    """
    Handle status selection and show confirmation.
    Callback data format: "admin_features_add_status:{name}:{description}:{is_enabled}"
    """
    try:
        _, name, description, is_enabled_str = query.data.split(":", 3)
        is_enabled = is_enabled_str.lower() == "true"
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Show confirmation
    status_text = "فعال" if is_enabled else "غیرفعال"
    desc_display = description[:100] + "..." if len(description) > 100 else description

    text = (
        f"✅ **تأیید نهایی ایجاد فیچر**\n\n"
        f"🏷️ نام: `{name}`\n"
        f"📝 توضیحات: {desc_display if desc_display else '(ندارد)'}\n"
        f"📋 وضعیت: {status_text}\n\n"
        f"آیا از ایجاد این فیچر اطمینان دارید؟"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، ایجاد شود",
                    callback_data=f"admin_features_add_save:{name}:{description}:{is_enabled_str}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش وضعیت",
                    callback_data=f"admin_features_add_retry_status:{name}:{description}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_features"
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


@requires_admin
async def save_feature(query: CallbackQuery) -> None:
    """
    Save the feature to database.
    Callback data format: "admin_features_add_save:{name}:{description}:{is_enabled}"
    """
    try:
        _, name, description, is_enabled_str = query.data.split(":", 3)
        is_enabled = is_enabled_str.lower() == "true"
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        # Validate data
        validator = FeatureValidator()
        validated = validator.validate_create({
            "name": name,
            "description": description,
            "is_enabled": is_enabled,
            "created_by": query.from_user.id,
        })

        # Save feature
        service = FeatureService()
        feature = await service.add_feature(**validated)

        status_icon = "✅" if feature.get("is_enabled") else "❌"
        status_text = "فعال" if feature.get("is_enabled") else "غیرفعال"

        text = (
            f"✅ **فیچر با موفقیت ایجاد شد!**\n\n"
            f"🏷️ نام: `{feature.get('name')}`\n"
            f"📝 توضیحات: {feature.get('description', '(ندارد)')}\n"
            f"📋 وضعیت: {status_text}\n"
            f"🆔 شناسه: `{feature.get('id')}`"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 مشاهده فیچر",
                        callback_data=f"admin_features_view:{feature.get('id')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ افزودن فیچر جدید",
                        callback_data="admin_features_add"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست فیچرها",
                        callback_data="admin_features"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Feature created: {feature.get('name')} by admin {query.from_user.id}")
        await query.answer("فیچر ایجاد شد!")
    except ValidationError as e:
        logger.warning(f"Validation error in save_feature: {e}")
        await query.message.edit_text(
            f"❌ خطای اعتبارسنجی:\n{str(e)}",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in save_feature: {e}")
        await query.message.edit_text(
            "❌ خطا در ایجاد فیچر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in save_feature: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در ایجاد فیچر.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def retry_name(query: CallbackQuery) -> None:
    """
    Retry entering feature name.
    Callback data: "admin_features_add_retry_name"
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_features"
                )
            ]
        ]
    )

    await query.message.edit_text(
        "✏️ **ویرایش نام فیچر**\n\n"
        "لطفاً نام فیچر را وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def retry_description(query: CallbackQuery) -> None:
    """
    Retry entering feature description.
    Callback data format: "admin_features_add_retry_description:{name}"
    """
    try:
        _, name = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش نام",
                    callback_data="admin_features_add_retry_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_features"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **ویرایش توضیحات فیچر**\n\n"
        f"🏷️ نام: `{name}`\n\n"
        f"لطفاً توضیحات فیچر را وارد کنید:\n"
        f"(اختیاری - برای رد کردن، روی دکمه رد کردن کلیک کنید)",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏭️ رد کردن توضیحات",
                        callback_data=f"admin_features_add_description_skip:{name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به ویرایش نام",
                        callback_data="admin_features_add_retry_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data="admin_features"
                    )
                ]
            ]
        ),
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def retry_status(query: CallbackQuery) -> None:
    """
    Retry selecting status.
    Callback data format: "admin_features_add_retry_status:{name}:{description}"
    """
    try:
        _, name, description = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ فعال",
                    callback_data=f"admin_features_add_status:{name}:{description}:true"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ غیرفعال",
                    callback_data=f"admin_features_add_status:{name}:{description}:false"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش توضیحات",
                    callback_data=f"admin_features_add_retry_description:{name}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_features"
                )
            ]
        ]
    )

    desc_display = description[:100] + "..." if len(description) > 100 else description
    await query.message.edit_text(
        f"✏️ **ویرایش وضعیت فیچر**\n\n"
        f"🏷️ نام: `{name}`\n"
        f"📝 توضیحات: {desc_display if desc_display else '(ندارد)'}\n\n"
        f"لطفاً وضعیت اولیه فیچر را انتخاب کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()