# src/admin_panel/modules/analytics/handlers/show_dashboard.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.analytics.services import AnalyticsCalculator
from admin_panel.modules.analytics.keyboards import AnalyticsMenuKeyboard

logger = get_logger(__name__)


@requires_admin
async def show_dashboard(query: CallbackQuery) -> None:
    """Display the main analytics dashboard with key metrics."""
    try:
        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Get analytics data
        calculator = AnalyticsCalculator()
        stats = await calculator.get_dashboard_stats(start_date, end_date)

        # Format dashboard text
        text = (
            f"📊 **داشبورد تحلیلی**\n"
            f"📅 بازه: {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}\n\n"
            f"👥 **کاربران**\n"
            f"  کل کاربران: {stats.get('total_users', 0):,}\n"
            f"  کاربران جدید: {stats.get('new_users', 0):,}\n\n"
            f"🛒 **سفارشات**\n"
            f"  کل سفارشات: {stats.get('total_orders', 0):,}\n"
            f"  سفارشات امروز: {stats.get('today_orders', 0):,}\n"
            f"  درآمد کل: {stats.get('total_revenue', 0):,} تومان\n"
            f"  درآمد امروز: {stats.get('today_revenue', 0):,} تومان\n\n"
            f"📊 **وضعیت سفارشات**\n"
            f"  در انتظار: {stats.get('pending_orders', 0):,}\n"
            f"  پرداخت شده: {stats.get('paid_orders', 0):,}\n"
            f"  ارسال شده: {stats.get('shipped_orders', 0):,}\n"
            f"  تحویل شده: {stats.get('delivered_orders', 0):,}\n"
            f"  لغو شده: {stats.get('cancelled_orders', 0):,}\n\n"
            f"💳 **پرداخت‌ها**\n"
            f"  موفق: {stats.get('successful_payments', 0):,}\n"
            f"  ناموفق: {stats.get('failed_payments', 0):,}\n"
        )

        keyboard = AnalyticsMenuKeyboard.get_dashboard_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in dashboard: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت آمار. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا در دریافت آمار!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in dashboard: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)