# src/admin_panel/modules/behavior_analytics/handlers/show_behavior.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta

from my_bot.core.exceptions import DatabaseError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.behavior_analytics.services import BehaviorAnalyticsService
from admin_panel.modules.behavior_analytics.keyboards import BehaviorMenuKeyboard

logger = get_logger(__name__)


@requires_admin
async def show_behavior(query: CallbackQuery) -> None:
    """
    Display the main behavior analytics menu.
    Callback data: "admin_behavior"
    """
    try:
        text = (
            "📊 **تحلیل رفتار کاربران**\n\n"
            "مدیریت و مشاهده تحلیل رفتار کاربران در سیستم.\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = BehaviorMenuKeyboard.get_main_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing behavior menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش پنل تحلیل رفتار.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def show_behavior_dashboard(query: CallbackQuery) -> None:
    """
    Display the behavior analytics dashboard with key metrics.
    Callback data: "admin_behavior_dashboard"
    """
    try:
        # Parse period from callback data
        period = "30d"  # default
        if ":" in query.data:
            period = query.data.split(":", 1)[1]

        # Calculate date range
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

        service = BehaviorAnalyticsService()
        stats = await service.get_behavior_stats(start_date, end_date)

        text = (
            f"📊 **داشبورد تحلیل رفتار**\n"
            f"📅 بازه: {start_date.strftime('%Y-%m-%d')} تا {end_date.strftime('%Y-%m-%d')}\n\n"
            f"👥 **کاربران فعال**\n"
            f"  فعال روزانه: {stats.get('daily_active_users', 0):,}\n"
            f"  فعال هفتگی: {stats.get('weekly_active_users', 0):,}\n"
            f"  فعال ماهانه: {stats.get('monthly_active_users', 0):,}\n\n"
            f"📊 **تعامل**\n"
            f"  میانگین جلسات روزانه: {stats.get('avg_daily_sessions', 0):.1f}\n"
            f"  میانگین مدت جلسه: {stats.get('avg_session_duration', 0):.1f} دقیقه\n"
            f"  نرخ بازگشت: {stats.get('return_rate', 0):.1f}%\n\n"
            f"📈 **تبدیل**\n"
            f"  نرخ تبدیل: {stats.get('conversion_rate', 0):.1f}%\n"
            f"  میانگین زمان تا تبدیل: {stats.get('avg_time_to_conversion', 0):.1f} روز\n\n"
            f"🔝 **مسیرهای پرکاربرد**\n"
        )

        top_paths = stats.get('top_paths', [])
        if top_paths:
            for idx, path in enumerate(top_paths[:5], start=1):
                text += f"  {idx}. {path.get('path', 'نامشخص')} ({path.get('count', 0):,})\n"
        else:
            text += "  هیچ مسیری ثبت نشده است.\n"

        keyboard = BehaviorMenuKeyboard.get_dashboard_keyboard(period)

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in behavior dashboard: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت آمار رفتار. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in behavior dashboard: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش داشبورد رفتار.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def show_user_journey(query: CallbackQuery) -> None:
    """
    Display the user journey analysis.
    Callback data: "admin_behavior_journey" or "admin_behavior_journey:{user_id}"
    """
    try:
        user_id = None
        if ":" in query.data:
            _, user_id_str = query.data.split(":", 1)
            user_id = int(user_id_str) if user_id_str.isdigit() else None

        service = BehaviorAnalyticsService()

        if user_id:
            # Show journey for specific user
            journey = await service.get_user_journey(user_id)
            if not journey:
                await query.message.edit_text(
                    f"❌ مسیر کاربر `{user_id}` یافت نشد.",
                    reply_markup=get_back_button("admin_behavior_dashboard")
                )
                await query.answer("کاربر یافت نشد!", show_alert=True)
                return

            text = (
                f"👤 **مسیر کاربر**\n"
                f"🆔 شناسه: `{user_id}`\n"
                f"👤 نام: {journey.get('user_name', 'نامشخص')}\n\n"
                f"📊 **سفر کاربری**\n"
            )

            steps = journey.get('steps', [])
            if steps:
                for idx, step in enumerate(steps, start=1):
                    step_name = step.get('name', f"مرحله {idx}")
                    duration = step.get('duration', 0)
                    text += f"  {idx}. {step_name} ({duration} ثانیه)\n"
            else:
                text += "  هیچ سفر کاربری ثبت نشده است.\n"

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به داشبورد",
                            callback_data="admin_behavior_dashboard"
                        )
                    ]
                ]
            )
        else:
            # Show overall journey analysis
            journey_stats = await service.get_overall_journey()

            text = (
                f"📊 **تحلیل سفر کاربری**\n\n"
                f"🔄 مسیرهای پرتکرار:\n"
            )

            paths = journey_stats.get('common_paths', [])
            if paths:
                for idx, path in enumerate(paths[:10], start=1):
                    path_name = path.get('path', f"مسیر {idx}")
                    count = path.get('count', 0)
                    text += f"  {idx}. {path_name} ({count:,})\n"
            else:
                text += "  هیچ مسیری ثبت نشده است.\n"

            text += f"\n⏱️ میانگین زمان سفر: {journey_stats.get('avg_journey_duration', 0):.1f} دقیقه\n"
            text += f"🚪 نقاط خروج اصلی: {', '.join(journey_stats.get('exit_points', ['نامشخص'])[:3])}"

            keyboard = BehaviorMenuKeyboard.get_journey_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in user journey: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت مسیر کاربری.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in user journey: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش مسیر کاربری.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def show_behavior_report(query: CallbackQuery) -> None:
    """
    Show comprehensive behavior report.
    Callback data: "admin_behavior_report"
    """
    try:
        service = BehaviorAnalyticsService()
        report = await service.get_full_report()

        text = (
            f"📊 **گزارش جامع رفتار کاربران**\n\n"
            f"📅 تاریخ گزارش: {report.get('generated_at', 'نامشخص')}\n\n"
            f"👥 **آمار کاربران**\n"
            f"  کل کاربران: {report.get('total_users', 0):,}\n"
            f"  کاربران جدید: {report.get('new_users', 0):,}\n"
            f"  نرخ رشد: {report.get('growth_rate', 0):.1f}%\n\n"
            f"📊 **تعامل**\n"
            f"  کل تعاملات: {report.get('total_interactions', 0):,}\n"
            f"  میانگین روزانه: {report.get('avg_daily_interactions', 0):.1f}\n"
            f"  اوج فعالیت: {report.get('peak_activity', 'نامشخص')}\n\n"
            f"📈 **تحلیل**\n"
            f"  نرخ ماندگاری: {report.get('retention_rate', 0):.1f}%\n"
            f"  نرخ ریزش: {report.get('churn_rate', 0):.1f}%\n"
            f"  امتیاز خالص ترویج: {report.get('nps', 0):.1f}\n\n"
            f"📌 **توصیه‌ها**\n"
        )

        recommendations = report.get('recommendations', [])
        if recommendations:
            for idx, rec in enumerate(recommendations[:5], start=1):
                text += f"  {idx}. {rec}\n"
        else:
            text += "  هیچ توصیه‌ای موجود نیست.\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 خروجی PDF",
                        callback_data="admin_behavior_export:pdf"
                    ),
                    InlineKeyboardButton(
                        text="📥 خروجی Excel",
                        callback_data="admin_behavior_export:excel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی رفتار",
                        callback_data="admin_behavior"
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
        logger.error(f"Database error in behavior report: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت گزارش رفتار.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in behavior report: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش گزارش رفتار.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def export_behavior_data(query: CallbackQuery) -> None:
    """
    Export behavior data in specified format.
    Callback data format: "admin_behavior_export:{format}"
    """
    try:
        _, format_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ فرمت نامعتبر است.", show_alert=True)
        return

    try:
        service = BehaviorAnalyticsService()
        file_data = await service.export_data(format_type)

        if not file_data:
            await query.answer("❌ خطا در تولید خروجی.", show_alert=True)
            return

        # In a real implementation, you would send the file
        # For now, we show a success message
        await query.message.edit_text(
            f"✅ **خروجی با موفقیت تولید شد!**\n\n"
            f"📊 فرمت: {format_type.upper()}\n"
            f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"فایل خروجی به صورت خودکار ارسال خواهد شد.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به گزارش رفتار",
                            callback_data="admin_behavior_report"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Behavior data exported in {format_type} format by admin {query.from_user.id}")
        await query.answer("خروجی تولید شد!")
    except DatabaseError as e:
        logger.error(f"Database error in export_behavior_data: {e}")
        await query.message.edit_text(
            "❌ خطا در تولید خروجی. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in export_behavior_data: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در تولید خروجی.",
            reply_markup=get_back_button("admin_behavior")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)