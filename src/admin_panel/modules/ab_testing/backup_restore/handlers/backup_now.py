# src/admin_panel/modules/backup_restore/handlers/backup_now.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.backup_restore.services import BackupService

logger = get_logger(__name__)


@requires_admin
async def backup_now(query: CallbackQuery) -> None:
    """
    Show confirmation dialog for creating a new backup.
    Callback data: "admin_backup_now"
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، ایجاد پشتیبان",
                    callback_data="admin_backup_confirm"
                ),
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="admin_backup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به منوی پشتیبان",
                    callback_data="admin_backup"
                )
            ]
        ]
    )

    await query.message.edit_text(
        "⚠️ **ایجاد پشتیبان جدید**\n\n"
        "آیا از ایجاد پشتیبان از دیتابیس و فایل‌ها اطمینان دارید؟\n"
        "این عمل ممکن است چند لحظه طول بکشد.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def confirm_backup(query: CallbackQuery) -> None:
    """
    Execute backup creation and send the file.
    Callback data: "admin_backup_confirm"
    """
    try:
        # Show processing message
        await query.message.edit_text(
            "⏳ در حال ایجاد پشتیبان... لطفاً صبر کنید.",
            reply_markup=None,
            parse_mode="Markdown"
        )

        # Create backup
        service = BackupService()
        result = await service.create_backup()

        backup_file = result.get("file_path")
        filename = result.get("filename", "backup.zip")
        size = result.get("size", 0)
        timestamp = result.get("timestamp", "")

        if not backup_file:
            raise DatabaseError("Backup file not created.")

        # Send the backup file
        with open(backup_file, "rb") as f:
            await query.message.answer_document(
                document=InputFile(f, filename=filename),
                caption=(
                    f"✅ **پشتیبان با موفقیت ایجاد شد**\n\n"
                    f"📅 تاریخ: {timestamp}\n"
                    f"📦 حجم: {size / 1024:.2f} KB\n"
                    f"📁 فایل: {filename}"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 بازگشت به منوی پشتیبان",
                                callback_data="admin_backup"
                            )
                        ]
                    ]
                )
            )

        # Update original message to indicate completion (optional)
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass  # Message might already be deleted

        logger.info(f"Backup created by admin {query.from_user.id}: {filename}")
        await query.answer("پشتیبان ایجاد شد!")

    except PermissionDeniedError as e:
        logger.warning(f"Permission denied for admin {query.from_user.id}: {e}")
        await query.message.edit_text(
            "❌ شما مجوز ایجاد پشتیبان را ندارید.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error while creating backup: {e}")
        await query.message.edit_text(
            "❌ خطا در ایجاد پشتیبان. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("خطا در ایجاد پشتیبان!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error while creating backup: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در ایجاد پشتیبان. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=get_back_button("admin_backup")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)