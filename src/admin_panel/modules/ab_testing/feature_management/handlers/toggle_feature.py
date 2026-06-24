# src/admin_panel/modules/feature_management/handlers/toggle_feature.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from my_bot.core.exceptions import DatabaseError, NotFoundError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.feature_management.services import FeatureService
from admin_panel.modules.feature_management.keyboards import FeatureListKeyboard

logger = get_logger(__name__)


@requires_admin
async def toggle_feature(query: CallbackQuery) -> None:
    """
    Toggle the status of a feature flag (enable/disable).
    Callback data format: "admin_features_toggle:{feature_id}"
    """
    try:
        _, feature_id_str = query.data.split(":", 1)
        feature_id = int(feature_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه فیچر نامعتبر است.", show_alert=True)
        return

    try:
        service = FeatureService()
        feature = await service.get_feature(feature_id)

        if not feature:
            await query.message.edit_text(
                "❌ فیچر مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_features")
            )
            await query.answer("فیچر یافت نشد!", show_alert=True)
            return

        # Toggle the feature
        new_status = not feature.get("is_enabled", False)
        await service.toggle_feature(
            feature_id=feature_id,
            is_enabled=new_status,
            updated_by=query.from_user.id,
        )

        status_icon = "✅" if new_status else "❌"
        status_text = "فعال" if new_status else "غیرفعال"

        # Show success message
        await query.message.edit_text(
            f"{status_icon} **وضعیت فیچر با موفقیت تغییر یافت!**\n\n"
            f"🏷️ نام: `{feature.get('name')}`\n"
            f"📋 وضعیت جدید: {status_text}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به لیست فیچرها",
                            callback_data="admin_features"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Feature {feature_id} toggled to {new_status} by admin {query.from_user.id}")
        await query.answer(f"فیچر {status_text} شد!")

    except NotFoundError as e:
        logger.warning(f"Feature {feature_id} not found: {e}")
        await query.message.edit_text(
            "❌ فیچر مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("فیچر یافت نشد!", show_alert=True)
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied toggling feature {feature_id}: {e}")
        await query.message.edit_text(
            "❌ شما مجوز تغییر وضعیت این فیچر را ندارید.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error toggling feature {feature_id}: {e}")
        await query.message.edit_text(
            "❌ خطا در تغییر وضعیت فیچر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("خطا در تغییر وضعیت!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error toggling feature {feature_id}: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در تغییر وضعیت فیچر.",
            reply_markup=get_back_button("admin_features")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)