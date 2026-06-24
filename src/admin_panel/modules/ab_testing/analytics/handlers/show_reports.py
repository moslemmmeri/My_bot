# src/admin_panel/modules/analytics/handlers/show_reports.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.analytics.services import AnalyticsCalculator, ChartGenerator
from admin_panel.modules.analytics.keyboards import ReportTypeKeyboard

logger = get_logger(__name__)


@requires_admin
async def show_reports(query: CallbackQuery) -> None:
    """Display the reports menu with available report types."""
    try:
        text = (
            "📊 **گزارش‌های تحلیلی**\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:\n"
            "📈 گزارش فروش\n"
            "👥 گزارش کاربران\n"
            "💳 گزارش پرداخت‌ها\n"
            "📦 گزارش سفارشات\n"
            "📊 گزارش رفتار کاربران\n"
            "📅 گزارش‌های دوره‌ای"
        )

        keyboard = ReportTypeKeyboard.get_report_menu_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing reports menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش گزارش‌ها.",
            reply_markup=get_back_button("admin_analytics")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def show_sales_report(query: CallbackQuery) -> None:
    """Display sales report with revenue and order statistics."""
    try:
        # Parse date range from callback or use default (last 30 days)
        parts = query.data.split(":")
        period = parts[1] if len(parts) > 1 else "30d"

        end_date = datetime.now()
        if period == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:  # default 30d
            start_date = end_date - timedelta(days=30)

        calculator = AnalyticsCalculator()
        report_data = await calculator.get_sales_report(start_date, end_date)

        text = (
            f"📈 **گزارش فروش**\n"
            f"📅 بازه: {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}\n\n"
            f"💰 درآمد کل: {report_data.get('total_revenue', 0):,} تومان\n"
            f"🛒 تعداد سفارشات: {report_data.get('total_orders', 0):,}\n"
            f"💳 میانگین ارزش هر سفارش: {report_data.get('average_order_value', 0):,} تومان\n"
            f"📊 بیشترین فروش روزانه: {report_data.get('max_daily_revenue', 0):,} تومان\n"
            f"📉 کمترین فروش روزانه: {report_data.get('min_daily_revenue', 0):,} تومان\n\n"
            f"📊 **توزیع وضعیت سفارشات**\n"
            f"✅ پرداخت شده: {report_data.get('paid_orders', 0):,}\n"
            f"📦 ارسال شده: {report_data.get('shipped_orders', 0):,}\n"
            f"🚚 تحویل شده: {report_data.get('delivered_orders', 0):,}\n"
            f"❌ لغو شده: {report_data.get('cancelled_orders', 0):,}\n"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 خروجی Excel",
                        callback_data="report_export_excel:sales"
                    ),
                    InlineKeyboardButton(
                        text="📥 خروجی PDF",
                        callback_data="report_export_pdf:sales"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تغییر بازه زمانی",
                        callback_data="report_period:sales"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست گزارش‌ها",
                        callback_data="admin_reports"
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
        logger.error(f"Database error in sales report: {e}")
        await query.answer("خطا در دریافت گزارش فروش!", show_alert=True)
    except Exception as e:
        logger.error(f"Error showing sales report: {e}", exc_info=True)
        await query.answer("خطا در نمایش گزارش!", show_alert=True)


@requires_admin
async def show_user_report(query: CallbackQuery) -> None:
    """Display user growth and engagement report."""
    try:
        parts = query.data.split(":")
        period = parts[1] if len(parts) > 1 else "30d"

        end_date = datetime.now()
        if period == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)

        calculator = AnalyticsCalculator()
        report_data = await calculator.get_user_report(start_date, end_date)

        text = (
            f"👥 **گزارش کاربران**\n"
            f"📅 بازه: {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}\n\n"
            f"👤 کل کاربران: {report_data.get('total_users', 0):,}\n"
            f"🆕 کاربران جدید: {report_data.get('new_users', 0):,}\n"
            f"📈 نرخ رشد: {report_data.get('growth_rate', 0):.1f}%\n"
            f"🟢 کاربران فعال: {report_data.get('active_users', 0):,}\n"
            f"⚪ کاربران غیرفعال: {report_data.get('inactive_users', 0):,}\n\n"
            f"📊 **سطح کاربران**\n"
            f"🥇 طلایی: {report_data.get('gold_users', 0):,}\n"
            f"🥈 نقره‌ای: {report_data.get('silver_users', 0):,}\n"
            f"🥉 برنزی: {report_data.get('bronze_users', 0):,}\n"
            f"⚪ معمولی: {report_data.get('normal_users', 0):,}\n\n"
            f"🎯 میانگین امتیاز: {report_data.get('average_points', 0):.1f}\n"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 خروجی Excel",
                        callback_data="report_export_excel:users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تغییر بازه زمانی",
                        callback_data="report_period:users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست گزارش‌ها",
                        callback_data="admin_reports"
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
        logger.error(f"Database error in user report: {e}")
        await query.answer("خطا در دریافت گزارش کاربران!", show_alert=True)
    except Exception as e:
        logger.error(f"Error showing user report: {e}", exc_info=True)
        await query.answer("خطا در نمایش گزارش!", show_alert=True)


@requires_admin
async def show_payment_report(query: CallbackQuery) -> None:
    """Display payment transactions report."""
    try:
        parts = query.data.split(":")
        period = parts[1] if len(parts) > 1 else "30d"

        end_date = datetime.now()
        if period == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)

        calculator = AnalyticsCalculator()
        report_data = await calculator.get_payment_report(start_date, end_date)

        text = (
            f"💳 **گزارش پرداخت‌ها**\n"
            f"📅 بازه: {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}\n\n"
            f"💰 کل تراکنش‌ها: {report_data.get('total_transactions', 0):,}\n"
            f"✅ پرداخت‌های موفق: {report_data.get('successful_payments', 0):,}\n"
            f"❌ پرداخت‌های ناموفق: {report_data.get('failed_payments', 0):,}\n"
            f"📊 نرخ موفقیت: {report_data.get('success_rate', 0):.1f}%\n"
            f"💰 مبلغ کل موفق: {report_data.get('total_successful_amount', 0):,} تومان\n"
            f"💰 مبلغ کل ناموفق: {report_data.get('total_failed_amount', 0):,} تومان\n\n"
            f"📈 **درگاه‌های پرداخت**\n"
        )

        # Add gateway breakdown
        gateways = report_data.get('gateway_breakdown', {})
        for gateway, data in gateways.items():
            text += f"  {gateway}: {data.get('count', 0):,} ({data.get('rate', 0):.1f}%)\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 خروجی Excel",
                        callback_data="report_export_excel:payments"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 تغییر بازه زمانی",
                        callback_data="report_period:payments"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست گزارش‌ها",
                        callback_data="admin_reports"
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
        logger.error(f"Database error in payment report: {e}")
        await query.answer("خطا در دریافت گزارش پرداخت‌ها!", show_alert=True)
    except Exception as e:
        logger.error(f"Error showing payment report: {e}", exc_info=True)
        await query.answer("خطا در نمایش گزارش!", show_alert=True)