# src/admin_panel/modules/ab_testing/handlers/list_tests.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.ab_testing.services import ABTestService
from admin_panel.modules.ab_testing.keyboards import ABTestFilterKeyboard

logger = get_logger(__name__)


@requires_admin
async def list_tests(query: CallbackQuery) -> None:
    """
    Display the list of A/B tests with pagination and filters.
    Callback data format:
        - "admin_ab_tests" (main menu)
        - "admin_ab_tests_list:{page}" (pagination)
        - "admin_ab_tests_list:{page}:{status}" (with status filter)
    """
    try:
        # Parse callback data
        parts = query.data.split(":")
        page = 1
        status = None

        if len(parts) >= 2:
            page = int(parts[1]) if parts[1].isdigit() else 1
        if len(parts) >= 3:
            status = parts[2] if parts[2] != "all" else None

        service = ABTestService()
        result = await service.list_tests(
            page=page,
            page_size=10,
            status=status,
        )

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        # Build text
        if not items:
            text = "🧪 **لیست تست‌های A/B**\n\nهیچ تستی یافت نشد."
            keyboard = ABTestFilterKeyboard.get_empty_keyboard(
                back_callback="admin_panel"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        status_names = {
            "draft": "📝 پیش‌نویس",
            "active": "🟢 فعال",
            "paused": "🟡 متوقف",
            "completed": "🔵 تکمیل شده",
            "archived": "📦 بایگانی",
        }

        text = f"🧪 **لیست تست‌های A/B** (صفحه {current_page} از {total_pages})\n\n"
        for idx, test in enumerate(items, start=(page-1)*10 + 1):
            test_id = test.get("id")
            name = test.get("name", "بدون نام")
            status = test.get("status", "draft")
            variants = test.get("variants", [])
            variant_count = len(variants)
            created_at = test.get("created_at", "نامشخص")

            status_display = status_names.get(status, status)

            text += f"{idx}. 🧪 **{name}**\n"
            text += f"   📋 {status_display} | 📊 {variant_count} متغیر\n"
            text += f"   🆔 {test_id} | 📅 {created_at[:10]}\n\n"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Pagination row
        nav_row = []
        if current_page > 1:
            prev_callback = f"admin_ab_tests_list:{current_page - 1}"
            if status:
                prev_callback += f":{status}"
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=prev_callback
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_ab_tests_noop"
            )
        )
        if current_page < total_pages:
            next_callback = f"admin_ab_tests_list:{current_page + 1}"
            if status:
                next_callback += f":{status}"
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=next_callback
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Filter row
        filter_row = []
        if status:
            filter_row.append(
                InlineKeyboardButton(
                    text="🧹 پاک کردن فیلتر",
                    callback_data="admin_ab_tests_list:1"
                )
            )
        else:
            filter_row.append(
                InlineKeyboardButton(
                    text="🔍 فیلتر بر اساس وضعیت",
                    callback_data="admin_ab_tests_filter"
                )
            )
        keyboard.inline_keyboard.append(filter_row)

        # Quick view buttons for first 5 tests
        for test in items[:5]:
            test_id = test.get("id")
            name = test.get("name", "بدون نام")[:20]
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🧪 {name}",
                    callback_data=f"admin_ab_tests_view:{test_id}"
                )
            ])

        # Action buttons
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="➕ ایجاد تست جدید",
                callback_data="admin_ab_tests_create"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="📊 آمار تست‌ها",
                callback_data="admin_ab_tests_stats"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به پنل مدیریت",
                callback_data="admin_panel"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in list_tests: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست تست‌ها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_tests: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش لیست تست‌ها.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)