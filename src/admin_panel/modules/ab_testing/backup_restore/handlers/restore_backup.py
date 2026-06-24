# src/admin_panel/modules/backup_restore/handlers/restore_backup.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.backup_restore.services import RestoreService

logger = get_logger(__name__)


@requires_admin
async def restore_backup(query: CallbackQuery) -> None:
    """
    Show list of available backups for restoration.
    Callback data: "admin_restore_backup"
    """
    try:
        service = RestoreService()
        backups = await service.list_backups()

        if not backups:
            await query.message.edit_text(
                "📂 **بازیابی پشتیبان**\n\n"
                "هیچ فایل پشتیبان موجود نیست.\n"
                "ابتدا یک پشتیبان ایجاد کنید.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 بازگشت به منوی پشتیبان",
                                callback_data="admin_backup"
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown"
            )
            await query.answer()
            return

        text = "📂 **بازیابی پشتیبان**\n\n"
        text += "یکی از فایل‌های پشتیبان زیر را برای بازیابی انتخاب کنید:\n\n"

        keyboard = []
        for idx, backup in enumerate(backups[:20], 1):  # Limit to 20
            filename = backup.get("filename")
            size = backup.get("size", 0)
            created = backup.get("created", "نامشخص")
            text += f"{idx}. 📁 `{filename}` ({size/1024:.1f} KB) - {created}\n"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{idx}. {filename[:30]}...",
                    callback_data=f"admin_restore_confirm:{filename}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به منوی پشتیبان",
                callback_data="admin_backup"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error while listing backups: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست پشتیبان‌ها.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in restore_backup: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def confirm_restore(query: CallbackQuery) -> None:
    """
    Show confirmation dialog before restoring a backup.
    Callback data format: "admin_restore_confirm:{filename}"
    """
    try:
        _, filename = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ بله، بازیابی شود",
                    callback_data=f"admin_restore_execute:{filename}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="admin_restore_backup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به لیست",
                    callback_data="admin_restore_backup"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"⚠️ **تأیید بازیابی پشتیبان**\n\n"
        f"فایل: `{filename}`\n\n"
        f"آیا از بازیابی این پشتیبان اطمینان دارید؟\n"
        f"**توجه:** تمام داده‌های فعلی با داده‌های پشتیبان جایگزین خواهند شد.\n"
        f"این عمل غیرقابل بازگشت است.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def execute_restore(query: CallbackQuery) -> None:
    """
    Execute the restoration of the selected backup.
    Callback data format: "admin_restore_execute:{filename}"
    """
    try:
        _, filename = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        # Show processing message
        await query.message.edit_text(
            "⏳ در حال بازیابی پشتیبان... لطفاً صبر کنید.",
            reply_markup=None,
            parse_mode="Markdown"
        )

        # Restore backup
        service = RestoreService()
        result = await service.restore_backup(filename)

        if result.get("success"):
            await query.message.edit_text(
                f"✅ **پشتیبان با موفقیت بازیابی شد!**\n\n"
                f"📁 فایل: {filename}\n"
                f"⏱️ زمان بازیابی: {result.get('duration', 'نامشخص')} ثانیه\n"
                f"📊 تعداد رکوردهای بازیابی‌شده: {result.get('records_restored', 0)}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 بازگشت به منوی پشتیبان",
                                callback_data="admin_backup"
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown"
            )
            logger.info(f"Backup restored by admin {query.from_user.id}: {filename}")
            await query.answer("پشتیبان بازیابی شد!")
        else:
            raise DatabaseError(result.get("error", "Unknown error"))

    except NotFoundError as e:
        logger.warning(f"Backup file not found: {filename}")
        await query.message.edit_text(
            f"❌ فایل پشتیبان `{filename}` یافت نشد.",
            reply_markup=get_back_button("admin_restore_backup")
        )
        await query.answer("فایل یافت نشد!", show_alert=True)
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied for admin {query.from_user.id}: {e}")
        await query.message.edit_text(
            "❌ شما مجوز بازیابی پشتیبان را ندارید.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error while restoring backup: {e}")
        await query.message.edit_text(
            f"❌ خطا در بازیابی پشتیبان: {str(e)}",
            reply_markup=get_back_button("admin_restore_backup")
        )
        await query.answer("خطا در بازیابی!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error while restoring backup: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در بازیابی پشتیبان.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)