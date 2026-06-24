# src/admin_panel/modules/feedback_management/handlers/view_feedback.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.feedback_management.services import FeedbackService
from admin_panel.modules.feedback_management.keyboards import FeedbackActionsKeyboard

logger = get_logger(__name__)


@requires_admin
async def view_feedback(query: CallbackQuery) -> None:
    """
    Display detailed information about a feedback.
    Callback data format: "admin_feedback_view:{feedback_id}"
    """
    try:
        _, feedback_id_str = query.data.split(":", 1)
        feedback_id = int(feedback_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه بازخورد نامعتبر است.", show_alert=True)
        return

    try:
        service = FeedbackService()
        feedback = await service.get_feedback(feedback_id)

        if not feedback:
            await query.message.edit_text(
                "❌ بازخورد مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_feedback_list:1")
            )
            await query.answer("بازخورد یافت نشد!", show_alert=True)
            return

        # Status names
        status_names = {
            "pending": "🟡 در انتظار",
            "replied": "🔵 پاسخ داده شده",
            "resolved": "🟢 حل شده",
        }

        # Build rating stars
        rating = feedback.get('rating', 0)
        rating_stars = "⭐" * rating + "☆" * (5 - rating)

        # Build feedback details text
        text = (
            f"💬 **جزئیات بازخورد**\n\n"
            f"🆔 شناسه: `{feedback.get('id')}`\n"
            f"👤 کاربر: {feedback.get('user_name', 'نامشخص')}\n"
            f"🆔 کاربر: `{feedback.get('user_id', 'نامشخص')}`\n"
            f"⭐ امتیاز: {rating_stars} ({rating}/5)\n"
            f"📋 وضعیت: {status_names.get(feedback.get('status'), feedback.get('status'))}\n"
            f"📅 تاریخ: {feedback.get('created_at', 'نامشخص')}\n"
        )

        if feedback.get('updated_at'):
            text += f"📅 آخرین بروزرسانی: {feedback.get('updated_at', 'نامشخص')}\n"

        text += f"\n📝 **متن بازخورد:**\n---\n{feedback.get('message', 'بدون متن')}\n---\n"

        # Show reply if exists
        reply = feedback.get('reply')
        if reply:
            text += f"\n💬 **پاسخ ادمین:**\n---\n{reply}\n---\n"
            if feedback.get('replied_at'):
                text += f"📅 تاریخ پاسخ: {feedback.get('replied_at', 'نامشخص')}\n"

        # Build keyboard
        keyboard = FeedbackActionsKeyboard.get_action_keyboard(
            feedback_id=feedback_id,
            current_status=feedback.get('status', 'pending'),
            back_callback="admin_feedback_list:1",
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except NotFoundError as e:
        logger.warning(f"Feedback {feedback_id} not found: {e}")
        await query.message.edit_text(
            "❌ بازخورد مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_feedback_list:1")
        )
        await query.answer("بازخورد یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error viewing feedback {feedback_id}: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات بازخورد. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_feedback_list:1")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error viewing feedback {feedback_id}: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش بازخورد.",
            reply_markup=get_back_button("admin_feedback_list:1")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)