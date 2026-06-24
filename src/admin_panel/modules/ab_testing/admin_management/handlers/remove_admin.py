# src/admin_panel/modules/admin_management/handlers/remove_admin.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.exceptions import DatabaseError, NotFoundError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.admin_management.services import AdminCRUDService
from admin_panel.modules.admin_management.keyboards import AdminActionsKeyboard

logger = get_logger(__name__)


@requires_admin
async def remove_admin(query: CallbackQuery) -> None:
    """
    Show confirmation dialog for removing an admin.
    Callback data format: "admin_admins_remove_confirm:{admin_id}"
    """
    try:
        _, admin_id_str = query.data.split(":", 1)
        admin_id = int(admin_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه ادمین نامعتبر است.", show_alert=True)
        return

    try:
        service = AdminCRUDService()
        admin = await service.get_admin(admin_id)

        if not admin:
            await query.message.edit_text(
                "❌ ادمین مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_admins")
            )
            await query.answer("ادمین یافت نشد!", show_alert=True)
            return

        # Check if trying to remove self
        if admin.get("user_id") == query.from_user.id:
            await query.message.edit_text(
                "⚠️ **هشدار**\n\n"
                "شما نمی‌توانید خودتان را از لیست ادمین‌ها حذف کنید.\n"
                "برای حذف خود، ابتدا ادمین دیگری را به عنوان مدیر اصلی اضافه کنید.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
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
            await query.answer("نمی‌توانید خود را حذف کنید!", show_alert=True)
            return

        text = (
            f"⚠️ **تأیید حذف ادمین**\n\n"
            f"👤 کاربر: {admin.get('username', 'بدون نام')}\n"
            f"🆔 شناسه: `{admin.get('user_id')}`\n"
            f"📋 نقش: {admin.get('role', 'admin')}\n\n"
            f"آیا از حذف این کاربر از لیست ادمین‌ها اطمینان دارید؟\n"
            f"این عمل **غیرقابل بازگشت** است."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_admins_remove_execute:{admin_id}"
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
        logger.error(f"Database error in remove_admin: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات ادمین.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in remove_admin: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def execute_remove_admin(query: CallbackQuery) -> None:
    """
    Execute the removal of an admin.
    Callback data format: "admin_admins_remove_execute:{admin_id}"
    """
    try:
        _, admin_id_str = query.data.split(":", 1)
        admin_id = int(admin_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه ادمین نامعتبر است.", show_alert=True)
        return

    try:
        service = AdminCRUDService()
        admin = await service.get_admin(admin_id)

        if not admin:
            await query.message.edit_text(
                "❌ ادمین مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_admins")
            )
            await query.answer("ادمین یافت نشد!", show_alert=True)
            return

        # Execute removal
        await service.remove_admin(admin_id, removed_by=query.from_user.id)

        await query.message.edit_text(
            f"✅ **ادمین با موفقیت حذف شد!**\n\n"
            f"👤 کاربر: {admin.get('username', 'بدون نام')}\n"
            f"🆔 شناسه: `{admin.get('user_id')}`\n"
            f"📋 نقش: {admin.get('role', 'admin')}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
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
        logger.info(f"Admin {admin_id} removed by admin {query.from_user.id}")
        await query.answer("ادمین حذف شد!")
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied removing admin {admin_id}: {e}")
        await query.message.edit_text(
            "❌ شما مجوز حذف این ادمین را ندارید.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except NotFoundError as e:
        logger.warning(f"Admin not found: {e}")
        await query.message.edit_text(
            "❌ ادمین مورد نظر قبلاً حذف شده یا وجود ندارد.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("ادمین یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error removing admin: {e}")
        await query.message.edit_text(
            "❌ خطا در حذف ادمین. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطا در حذف ادمین!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error removing admin: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در حذف ادمین.",
            reply_markup=get_back_button("admin_admins")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)