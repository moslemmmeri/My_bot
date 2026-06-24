# src/admin_panel/modules/monitoring/handlers/show_monitoring.py
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.monitoring.services import SystemMonitorService, PerformanceMonitorService
from admin_panel.modules.monitoring.keyboards import MonitoringMenuKeyboard

logger = get_logger(__name__)


@requires_admin
async def show_monitoring(query: CallbackQuery) -> None:
    """
    Display the main monitoring dashboard.
    Callback data: "admin_monitoring"
    """
    try:
        # Show main monitoring menu
        text = (
            "📊 **پایش سیستم**\n\n"
            "وضعیت کلی سیستم و سرویس‌ها را بررسی کنید.\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = MonitoringMenuKeyboard.get_main_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing monitoring: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش پنل پایش.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def show_system_status(query: CallbackQuery) -> None:
    """
    Display detailed system status information.
    Callback data: "admin_monitoring_status"
    """
    try:
        monitor = SystemMonitorService()
        status = await monitor.get_system_status()

        text = (
            "🖥️ **وضعیت سیستم**\n\n"
            f"🟢 وضعیت کلی: {status.get('overall', 'نامشخص')}\n"
            f"⏱️ زمان فعالیت: {status.get('uptime', 'نامشخص')}\n"
            f"🔄 آخرین بروزرسانی: {status.get('last_update', 'نامشخص')}\n\n"
            f"📊 **سرویس‌ها**\n"
        )

        # Service status
        services = status.get('services', {})
        for name, data in services.items():
            status_icon = "✅" if data.get('status') == "healthy" else "❌"
            text += f"  {status_icon} {name}: {data.get('status', 'unknown')}\n"
            if data.get('message'):
                text += f"      - {data.get('message')}\n"

        # Database status
        db = status.get('database', {})
        text += f"\n🗄️ **دیتابیس**\n"
        text += f"  وضعیت: {'✅' if db.get('status') == 'healthy' else '❌'} {db.get('status', 'unknown')}\n"
        text += f"  اتصالات: {db.get('connections', 0)}\n"

        # Cache status
        cache = status.get('cache', {})
        text += f"\n⚡ **کش**\n"
        text += f"  وضعیت: {'✅' if cache.get('status') == 'healthy' else '❌'} {cache.get('status', 'unknown')}\n"
        text += f"  نوع: {cache.get('type', 'local')}\n"

        keyboard = MonitoringMenuKeyboard.get_status_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in system status: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت وضعیت سیستم.",
            reply_markup=get_back_button("admin_monitoring")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in system status: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در دریافت وضعیت سیستم.",
            reply_markup=get_back_button("admin_monitoring")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def show_performance(query: CallbackQuery) -> None:
    """
    Display performance metrics.
    Callback data: "admin_monitoring_performance"
    """
    try:
        monitor = PerformanceMonitorService()
        perf = await monitor.get_performance_metrics()

        text = (
            "⚡ **عملکرد سیستم**\n\n"
            f"💻 **CPU**\n"
            f"  استفاده: {perf.get('cpu_usage', 0):.1f}%\n"
            f"  هسته‌ها: {perf.get('cpu_cores', 0)}\n"
            f"  بار: {perf.get('cpu_load', 0):.2f}\n\n"
            f"🧠 **حافظه**\n"
            f"  کل: {perf.get('memory_total', 0) / 1024 / 1024:.1f} MB\n"
            f"  استفاده شده: {perf.get('memory_used', 0) / 1024 / 1024:.1f} MB\n"
            f"  درصد: {perf.get('memory_percent', 0):.1f}%\n\n"
            f"💾 **دیسک**\n"
            f"  کل: {perf.get('disk_total', 0) / 1024 / 1024 / 1024:.2f} GB\n"
            f"  استفاده شده: {perf.get('disk_used', 0) / 1024 / 1024 / 1024:.2f} GB\n"
            f"  درصد: {perf.get('disk_percent', 0):.1f}%\n"
        )

        keyboard = MonitoringMenuKeyboard.get_performance_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing performance: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات عملکرد.",
            reply_markup=get_back_button("admin_monitoring")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def show_resource_usage(query: CallbackQuery) -> None:
    """
    Display detailed resource usage.
    Callback data: "admin_monitoring_resources"
    """
    try:
        monitor = SystemMonitorService()
        resources = await monitor.get_resource_usage()

        text = (
            "📊 **مصرف منابع**\n\n"
            f"📈 **درخواست‌ها**\n"
            f"  کل درخواست‌ها: {resources.get('total_requests', 0):,}\n"
            f"  درخواست‌های امروز: {resources.get('today_requests', 0):,}\n"
            f"  میانگین پاسخ: {resources.get('avg_response_time', 0):.2f}ms\n\n"
            f"📊 **خطاها**\n"
            f"  کل خطاها: {resources.get('total_errors', 0):,}\n"
            f"  خطاهای امروز: {resources.get('today_errors', 0):,}\n"
            f"  نرخ خطا: {resources.get('error_rate', 0):.2f}%\n\n"
            f"⚡ **نرخ درخواست**\n"
            f"  میانگین: {resources.get('req_per_second', 0):.2f} req/s\n"
            f"  اوج: {resources.get('peak_req_per_second', 0):.2f} req/s\n"
        )

        keyboard = MonitoringMenuKeyboard.get_resource_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing resource usage: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در دریافت مصرف منابع.",
            reply_markup=get_back_button("admin_monitoring")
        )
        await query.answer("خطا!", show_alert=True)