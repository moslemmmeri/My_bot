# src/admin_panel/modules/error_logs/handlers/clear_errors.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.error_logs.services import ErrorLogService

logger = get_logger(__name__)


@requires_admin
async def clear_errors(query: CallbackQuery) -> None:
    """
    Show confirmation dialog before clearing error logs.
    Callback data: "admin_errors_clear_confirm"
    """
    try:
        text = (
            "🧹 **پاک کردن خطاها**\n\n"
            "آیا از پاک کردن تمام خطاهای ثبت‌شده اطمینان دارید؟\n"
            "⚠️ این عمل **غیرقابل بازگشت** است.\n\n"
            "برای پاک کردن خطاهای قدیمی‌تر از تاریخ مشخص، گزینه مربوطه را انتخاب کنید."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️ پاک کردن همه خطاها",
                        callback_data="admin_errors_clear_all"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 پاک کردن خطاهای قدیمی‌تر از ۷ روز",
                        callback_data="admin_errors_clear_older:7"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 پاک کردن خطاهای قدیمی‌تر از ۳۰ روز",
                        callback_data="admin_errors_clear_older:30"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_errors"
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
        logger.error(f"Error showing clear confirmation: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش تأییدیه پاک کردن.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def execute_clear_all(query: CallbackQuery) -> None:
    """
    Execute clearing all error logs.
    Callback data: "admin_errors_clear_all"
    """
    try:
        service = ErrorLogService()
        count = await service.clear_all_errors()

        text = (
            f"✅ **همه خطاها با موفقیت پاک شدند!**\n\n"
            f"📊 تعداد خطاهای پاک‌شده: {count:,}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست خطاها",
                        callback_data="admin_errors_list:1"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی خطاها",
                        callback_data="admin_errors"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"All error logs cleared by admin {query.from_user.id}")
        await query.answer("خطاها پاک شدند!")
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied clearing errors: {e}")
        await query.message.edit_text(
            "❌ شما مجوز پاک کردن خطاها را ندارید.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error clearing errors: {e}")
        await query.message.edit_text(
            "❌ خطا در پاک کردن خطاها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error clearing errors: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در پاک کردن خطاها.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def execute_clear_older(query: CallbackQuery) -> None:
    """
    Execute clearing errors older than a certain number of days.
    Callback data format: "admin_errors_clear_older:{days}"
    """
    try:
        _, days_str = query.data.split(":", 1)
        days = int(days_str)
    except ValueError:
        await query.answer("❌ تعداد روز نامعتبر است.", show_alert=True)
        return

    try:
        service = ErrorLogService()
        count = await service.clear_errors_older_than(days)

        text = (
            f"✅ **خطاهای قدیمی‌تر از {days} روز با موفقیت پاک شدند!**\n\n"
            f"📊 تعداد خطاهای پاک‌شده: {count:,}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست خطاها",
                        callback_data="admin_errors_list:1"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی خطاها",
                        callback_data="admin_errors"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Errors older than {days} days cleared by admin {query.from_user.id}")
        await query.answer("خطاهای قدیمی پاک شدند!")
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied clearing old errors: {e}")
        await query.message.edit_text(
            "❌ شما مجوز پاک کردن خطاها را ندارید.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error clearing old errors: {e}")
        await query.message.edit_text(
            "❌ خطا در پاک کردن خطاهای قدیمی. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error clearing old errors: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در پاک کردن خطاهای قدیمی.",
            reply_markup=get_back_button("admin_errors")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def cancel_clear(query: CallbackQuery) -> None:
    """
    Cancel clearing errors and return to error list.
    Callback data: "admin_errors_clear_cancel"
    """
    await query.message.edit_text(
        "❌ عملیات پاک کردن خطاها لغو شد.",
        reply_markup=get_back_button("admin_errors_list:1")
    )
    await query.answer("لغو شد.")