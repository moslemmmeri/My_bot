# src/admin_panel/modules/admin_management/handlers/add_admin.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.exceptions import DatabaseError, ValidationError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.admin_management.services import AdminCRUDService
from admin_panel.modules.admin_management.keyboards import AdminRoleKeyboard
from admin_panel.modules.admin_management.validators import AdminValidator

logger = get_logger(__name__)


@requires_admin
async def add_admin(query: CallbackQuery) -> None:
    """
    Start the add admin process.
    Show role selection.
    Callback data: "admin_admins_add"
    """
    try:
        text = (
            "👤 **افزودن ادمین جدید**\n\n"
            "لطفاً نقش ادمین جدید را انتخاب کنید:"
        )
        keyboard = AdminRoleKeyboard.get_role_selection_keyboard(
            back_callback="admin_admins"
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing add admin menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش فرم افزودن ادمین.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def add_admin_role(query: CallbackQuery) -> None:
    """
    Handle role selection and ask for user ID.
    Callback data format: "admin_admins_add_role:{role}"
    """
    try:
        _, role = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ نقش نامعتبر است.", show_alert=True)
        return

    # Store role in callback data for next step
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_admins"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"👤 **افزودن ادمین جدید**\n\n"
        f"📋 نقش انتخاب شده: {role}\n\n"
        f"لطفاً **شناسه عددی** کاربر مورد نظر را وارد کنید:\n"
        f"(می‌توانید از /id در ربات استفاده کنید)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def add_admin_confirm(query: CallbackQuery) -> None:
    """
    Show confirmation before adding admin.
    Callback data format: "admin_admins_add_confirm:{role}:{user_id}"
    """
    try:
        _, role, user_id_str = query.data.split(":", 2)
        user_id = int(user_id_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = AdminCRUDService()
        user_info = await service.get_user_info(user_id)

        if not user_info:
            await query.message.edit_text(
                f"❌ کاربر با شناسه `{user_id}` یافت نشد.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔄 تلاش مجدد",
                                callback_data="admin_admins_add"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔙 بازگشت به لیست ادمین‌ها",
                                callback_data="admin_admins"
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown"
            )
            await query.answer("کاربر یافت نشد!", show_alert=True)
            return

        text = (
            f"✅ **تأیید افزودن ادمین**\n\n"
            f"👤 کاربر: {user_info.get('username', 'بدون نام')}\n"
            f"🆔 شناسه: `{user_id}`\n"
            f"📋 نقش: {role}\n\n"
            f"آیا از افزودن این کاربر به عنوان ادمین اطمینان دارید؟"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، افزوده شود",
                        callback_data=f"admin_admins_add_execute:{role}:{user_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_admins"
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
    except DatabaseError as e:
        logger.error(f"Database error in add_admin_confirm: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات کاربر.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in add_admin_confirm: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def add_admin_execute(query: CallbackQuery) -> None:
    """
    Execute adding the admin.
    Callback data format: "admin_admins_add_execute:{role}:{user_id}"
    """
    try:
        _, role, user_id_str = query.data.split(":", 2)
        user_id = int(user_id_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = AdminCRUDService()
        admin = await service.add_admin(
            user_id=user_id,
            role=role,
            added_by=query.from_user.id,
        )

        await query.message.edit_text(
            f"✅ **ادمین با موفقیت افزوده شد!**\n\n"
            f"👤 کاربر: {admin.get('username', 'بدون نام')}\n"
            f"🆔 شناسه: `{admin.get('user_id')}`\n"
            f"📋 نقش: {admin.get('role')}\n"
            f"📅 تاریخ: {admin.get('created_at', 'نامشخص')}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👤 مشاهده ادمین",
                            callback_data=f"admin_admins_view:{admin.get('id')}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="➕ افزودن ادمین دیگر",
                            callback_data="admin_admins_add"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به لیست ادمین‌ها",
                            callback_data="admin_admins"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Admin added: user {user_id} as {role} by admin {query.from_user.id}")
        await query.answer("ادمین افزوده شد!")
    except ValidationError as e:
        logger.warning(f"Validation error in add_admin_execute: {e}")
        await query.message.edit_text(
            f"❌ خطای اعتبارسنجی:\n{str(e)}",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except NotFoundError as e:
        logger.warning(f"User not found: {e}")
        await query.message.edit_text(
            f"❌ کاربر با شناسه `{user_id}` یافت نشد.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("کاربر یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in add_admin_execute: {e}")
        await query.message.edit_text(
            "❌ خطا در افزودن ادمین. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا در افزودن ادمین!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in add_admin_execute: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در افزودن ادمین.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)