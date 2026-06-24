# src/admin_panel/modules/ab_testing/handlers/view_results.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.ab_testing.services import ABTestStatsService
from admin_panel.modules.ab_testing.keyboards import ABTestActionsKeyboard

logger = get_logger(__name__)


@requires_admin
async def view_results(query: CallbackQuery) -> None:
    """
    Display detailed results of an A/B test.
    Callback data format: "admin_ab_tests_results:{test_id}"
    """
    try:
        _, test_id_str = query.data.split(":", 1)
        test_id = int(test_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه تست نامعتبر است.", show_alert=True)
        return

    try:
        service = ABTestStatsService()
        stats = await service.get_test_results(test_id)

        if not stats:
            await query.message.edit_text(
                "❌ تست مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_ab_tests")
            )
            await query.answer("تست یافت نشد!", show_alert=True)
            return

        test_name = stats.get("test_name", "بدون نام")
        status = stats.get("status", "draft")
        variants = stats.get("variants", [])
        total_views = stats.get("total_views", 0)
        total_conversions = stats.get("total_conversions", 0)

        status_names = {
            "draft": "📝 پیش‌نویس",
            "active": "🟢 فعال",
            "paused": "🟡 متوقف",
            "completed": "🔵 تکمیل شده",
            "archived": "📦 بایگانی",
        }

        text = (
            f"📊 **نتایج تست A/B**\n\n"
            f"🧪 نام: `{test_name}`\n"
            f"📋 وضعیت: {status_names.get(status, status)}\n"
            f"👁️ کل بازدیدها: {total_views:,}\n"
            f"🎯 کل تبدیل‌ها: {total_conversions:,}\n"
            f"📈 نرخ تبدیل کلی: {(total_conversions / total_views * 100) if total_views > 0 else 0:.2f}%\n\n"
        )

        if not variants:
            text += "📊 هیچ داده‌ای برای این تست موجود نیست.\n"
        else:
            text += "📊 **نتایج به تفکیک متغیرها**\n\n"
            for idx, variant in enumerate(variants, start=1):
                variant_name = variant.get("name", f"متغیر {idx}")
                views = variant.get("views", 0)
                conversions = variant.get("conversions", 0)
                conversion_rate = (conversions / views * 100) if views > 0 else 0
                is_winner = variant.get("is_winner", False)
                winner_emoji = "🏆 " if is_winner else ""

                text += f"{winner_emoji}**{variant_name}**\n"
                text += f"   👁️ بازدید: {views:,}\n"
                text += f"   🎯 تبدیل: {conversions:,}\n"
                text += f"   📈 نرخ تبدیل: {conversion_rate:.2f}%\n\n"

            # Show confidence intervals if available
            if stats.get("has_significance", False):
                text += f"📊 **اهمیت آماری**\n"
                text += f"   {stats.get('significance_text', '')}\n"
                if stats.get("winner"):
                    text += f"   🏆 برنده: `{stats.get('winner')}`\n"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data=f"admin_ab_tests_results_refresh:{test_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 خروجی گزارش",
                        callback_data=f"admin_ab_tests_export:{test_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به تست",
                        callback_data=f"admin_ab_tests_view:{test_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست تست‌ها",
                        callback_data="admin_ab_tests"
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
    except NotFoundError as e:
        logger.warning(f"Test {test_id} not found: {e}")
        await query.message.edit_text(
            "❌ تست مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_ab_tests")
        )
        await query.answer("تست یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error viewing results for test {test_id}: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت نتایج تست. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_ab_tests")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error viewing results for test {test_id}: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش نتایج تست.",
            reply_markup=get_back_button("admin_ab_tests")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def refresh_results(query: CallbackQuery) -> None:
    """
    Refresh test results.
    Callback data format: "admin_ab_tests_results_refresh:{test_id}"
    """
    # Redirect to view_results with the same test_id
    await view_results(query)