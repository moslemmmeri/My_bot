# src/admin_panel/modules/feature_management/keyboards/feature_list_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional


class FeatureListKeyboard:
    """Keyboard for feature list in admin panel."""

    @staticmethod
    def get_list_keyboard(
        features: List[Dict[str, Any]],
        page: int = 1,
        total_pages: int = 1,
    ) -> InlineKeyboardMarkup:
        """Get keyboard with list of features and pagination."""
        keyboard = []

        # Feature items with toggle buttons
        for feature in features:
            feature_id = feature.get("id")
            name = feature.get("name", "بدون نام")
            is_enabled = feature.get("is_enabled", False)
            status_icon = "✅" if is_enabled else "❌"
            status_text = "فعال" if is_enabled else "غیرفعال"

            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status_icon} {name} ({status_text})",
                    callback_data=f"admin_features_view:{feature_id}"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    text="🔄 تغییر وضعیت" if is_enabled else "🔄 فعال کردن",
                    callback_data=f"admin_features_toggle:{feature_id}"
                ),
                InlineKeyboardButton(
                    text="🗑️ حذف",
                    callback_data=f"admin_features_delete_confirm:{feature_id}"
                )
            ])

        # Pagination row
        if total_pages > 1:
            nav_row = []
            if page > 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="⬅️ قبلی",
                        callback_data=f"admin_features_list:{page - 1}"
                    )
                )
            nav_row.append(
                InlineKeyboardButton(
                    text=f"{page}/{total_pages}",
                    callback_data="admin_features_noop"
                )
            )
            if page < total_pages:
                nav_row.append(
                    InlineKeyboardButton(
                        text="➡️ بعدی",
                        callback_data=f"admin_features_list:{page + 1}"
                    )
                )
            keyboard.append(nav_row)

        # Add feature button (handled in handler)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_empty_keyboard(back_callback: str = "admin_panel") -> InlineKeyboardMarkup:
        """Get keyboard when no features found."""
        return InlineKeyboardMarkup(
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
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_features") -> InlineKeyboardMarkup:
        """Get simple back keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_features") -> InlineKeyboardMarkup:
        """Get simple cancel keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=back_callback
                    )
                ]
            ]
        )