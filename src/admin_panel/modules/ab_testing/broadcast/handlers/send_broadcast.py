# src/admin_panel/modules/broadcast/handlers/send_broadcast.py
import asyncio
from typing import Optional

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

from my_bot.core.exceptions import DatabaseError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.broadcast.services import BroadcastSenderService
from admin_panel.modules.broadcast.keyboards import BroadcastConfirmKeyboard

logger = get_logger(__name__)


@requires_admin
async def send_broadcast(query: CallbackQuery) -> None:
    """
    Show confirmation dialog before sending broadcast.
    Callback data: "admin_broadcast_send"
    """
    try:
        # In real implementation, we'd retrieve composed message from cache/state
        # For now, we assume it's stored in a context manager
        text = (
            "✉️ **تأیید ارسال پیام گروهی**\n\n"
            "آیا از ارسال این پیام به کاربران انتخاب‌شده اطمینان دارید؟\n\n"
            "⚠️ **توجه**: این عمل غیرقابل بازگشت است و پیام به تمام کاربران فیلترشده ارسال خواهد شد."
        )
        keyboard = BroadcastConfirmKeyboard.get_send_confirmation_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error in send_broadcast confirmation: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش تأییدیه ارسال.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def confirm_send_broadcast(query: CallbackQuery) -> None:
    """
    Execute sending the broadcast.
    Callback data: "admin_broadcast_send_confirm"
    """
    try:
        # Show processing message
        await query.message.edit_text(
            "⏳ در حال ارسال پیام گروهی... لطفاً صبر کنید.\n"
            "این فرآیند ممکن است چند دقیقه طول بکشد.",
            reply_markup=None,
            parse_mode="Markdown"
        )

        # In real implementation, get the composed message and filters from state
        # For demo, we'll use dummy data
        message_text = "پیام آزمایشی"
        filters = {}  # e.g., {"level": "gold", "is_active": True}

        # Send broadcast
        sender = BroadcastSenderService()
        result = await sender.send_broadcast(
            message_text=message_text,
            filters=filters,
            admin_id=query.from_user.id,
        )

        total_sent = result.get("sent", 0)
        total_failed = result.get("failed", 0)
        total_users = result.get("total", 0)
        duration = result.get("duration", 0)

        # Prepare result message
        text = (
            f"✅ **ارسال پیام گروهی با موفقیت انجام شد!**\n\n"
            f"📊 **آمار ارسال**\n"
            f"👥 کاربران هدف: {total_users:,}\n"
            f"✅ ارسال موفق: {total_sent:,}\n"
            f"❌ ارسال ناموفق: {total_failed:,}\n"
            f"⏱️ زمان اجرا: {duration:.2f} ثانیه"
        )

        if total_failed > 0:
            text += "\n\n⚠️ برخی از ارسال‌ها ناموفق بودند. لطفاً لاگ‌ها را بررسی کنید."

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی ارسال گروهی",
                        callback_data="admin_broadcast"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 مشاهده جزئیات",
                        callback_data="admin_broadcast_logs"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Broadcast sent by admin {query.from_user.id}: {total_sent} sent, {total_failed} failed")
        await query.answer("پیام گروهی ارسال شد!")

    except PermissionDeniedError as e:
        logger.warning(f"Permission denied in send_broadcast: {e}")
        await query.message.edit_text(
            "❌ شما مجوز ارسال پیام گروهی را ندارید.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in send_broadcast: {e}")
        await query.message.edit_text(
            "❌ خطا در ارسال پیام گروهی. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in send_broadcast: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در ارسال پیام گروهی.",
            reply_markup=get_back_button("admin_broadcast")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def cancel_send_broadcast(query: CallbackQuery) -> None:
    """
    Cancel the broadcast sending process.
    Callback data: "admin_broadcast_send_cancel"
    """
    await query.message.edit_text(
        "❌ ارسال پیام گروهی لغو شد.",
        reply_markup=get_back_button("admin_broadcast")
    )
    await query.answer("لغو شد.")