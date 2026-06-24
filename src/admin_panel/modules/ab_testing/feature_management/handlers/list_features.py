# src/admin_panel/modules/feature_management/handlers/list_features.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.feature_management.services import FeatureService
from admin_panel.modules.feature_management.keyboards import FeatureListKeyboard

logger = get_logger(__name__)


@requires_admin
async def list_features(query: CallbackQuery) -> None:
    """
    Display the list of feature flags with pagination.
    Callback data format: "admin_features" or "admin_features_list:{page}"
    """
    try:
        # Parse page number from callback data
        page = 1
        if ":" in query.data:
            try:
                page = int(query.data.split(":", 1)[1])
            except ValueError:
                page = 1

        service = FeatureService()
        result = await service.list_features(page=page, page_size=10)

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        if not items:
            text = "🏷️ **مدیریت فیچرها**\n\nهیچ فیچری یافت نشد."
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ افزودن فیچر جدید",
                            callback_data="admin_features_add"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به پنل مدیریت",
                            callback_data="admin_panel"
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
            return

        text = f"🏷️ **مدیریت فیچرها** (صفحه {current_page} از {total_pages})\n\n"
        for idx, feature in enumerate(items, start=(page-1)*10 + 1):
            feature_id = feature.get("id")
            name = feature.get("name", "بدون نام")
            is_enabled = feature.get("is_enabled", False)
            description = feature.get("description", "")
            status_icon = "✅" if is_enabled else "❌"
            status_text = "فعال" if is_enabled else "غیرفعال"

            text += f"{idx}. {status_icon} **{name}**\n"
            text += f"   📋 وضعیت: {status_text}\n"
            if description:
                text += f"   📝 {description[:50]}{'...' if len(description) > 50 else ''}\n"
            text += f"   🆔 {feature_id}\n\n"

        # Build keyboard using FeatureListKeyboard
        keyboard = FeatureListKeyboard.get_list_keyboard(
            features=items,
            page=current_page,
            total_pages=total_pages,
        )

        # Add action buttons
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="➕ افزودن فیچر جدید",
                callback_data="admin_features_add"
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
        logger.error(f"Database error in list_features: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست فیچرها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا در دریافت لیست فیچرها!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_features: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)