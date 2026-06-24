# src/admin_panel/modules/system_health/handlers/show_health.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError, NotFoundError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.system_health.services import HealthCheckService
from admin_panel.modules.system_health.keyboards import HealthMenuKeyboard

logger = get_logger(__name__)


@requires_admin
async def show_health(query: CallbackQuery) -> None:
    """
    Display the main system health menu.
    Callback data: "admin_health"
    """
    try:
        text = (
            "💚 **سلامت سیستم**\n\n"
            "بررسی وضعیت سلامت سرویس‌ها و اجزای مختلف سیستم.\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = HealthMenuKeyboard.get_main_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing system health menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش پنل سلامت سیستم.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def show_full_health(query: CallbackQuery) -> None:
    """
    Display full system health status with all services.
    Callback data: "admin_health_check"
    """
    try:
        service = HealthCheckService()
        health_status = await service.check_all_services()

        overall_status = health_status.get("overall", "unknown")
        status_icon = "🟢" if overall_status == "healthy" else "🔴" if overall_status == "unhealthy" else "🟡"

        text = (
            f"{status_icon} **وضعیت سلامت سیستم**\n\n"
            f"📊 وضعیت کلی: **{overall_status.upper()}**\n"
            f"⏱️ زمان بررسی: {health_status.get('checked_at', 'نامشخص')}\n\n"
            f"🔍 **جزئیات سرویس‌ها**\n"
        )

        services = health_status.get("services", {})
        for name, data in services.items():
            status = data.get("status", "unknown")
            icon = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "⚠️"
            text += f"  {icon} **{name}**: {status}\n"
            if data.get("message"):
                text += f"      - {data.get('message')}\n"
            if data.get("latency"):
                text += f"      - زمان پاسخ: {data.get('latency')}ms\n"

        # Database details
        db = health_status.get("database", {})
        text += f"\n🗄️ **دیتابیس**\n"
        text += f"  وضعیت: {'✅' if db.get('status') == 'healthy' else '❌'} {db.get('status', 'unknown')}\n"
        text += f"  اتصالات: {db.get('connections', 0)}/{db.get('max_connections', 0)}\n"
        if db.get("latency"):
            text += f"  زمان پاسخ: {db.get('latency')}ms\n"

        # Cache details
        cache = health_status.get("cache", {})
        text += f"\n⚡ **کش**\n"
        text += f"  وضعیت: {'✅' if cache.get('status') == 'healthy' else '❌'} {cache.get('status', 'unknown')}\n"
        text += f"  نوع: {cache.get('type', 'local')}\n"
        text += f"  کلیدها: {cache.get('keys', 0)}\n"

        # External services
        external = health_status.get("external", {})
        if external:
            text += f"\n🌐 **سرویس‌های خارجی**\n"
            for name, data in external.items():
                status = data.get("status", "unknown")
                icon = "✅" if status == "healthy" else "❌"
                text += f"  {icon} {name}: {status}\n"

        keyboard = HealthMenuKeyboard.get_health_keyboard()

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in show_full_health: {e}")
        await query.message.edit_text(
            "❌ خطا در بررسی سلامت سیستم. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_health")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in show_full_health: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در بررسی سلامت سیستم.",
            reply_markup=get_back_button("admin_health")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def refresh_health(query: CallbackQuery) -> None:
    """
    Refresh health status and show updated results.
    Callback data: "admin_health_refresh"
    """
    await show_full_health(query)