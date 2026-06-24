# src/admin_panel/modules/feature_management/keyboards/feature_actions_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


class FeatureActionsKeyboard:
    """Keyboard for feature actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        feature_id: int,
        is_enabled: bool,
        back_callback: str = "admin_features",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with all actions for a specific feature."""
        keyboard = []

        # View details (already viewing, but keep for navigation)
        keyboard.append([
            InlineKeyboardButton(
                text="📄 مشاهده مجدد",
                callback_data=f"admin_features_view:{feature_id}"
            )
        ])

        # Toggle status
        toggle_text = "❌ غیرفعال کردن" if is_enabled else "✅ فعال کردن"
        keyboard.append([
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=f"admin_features_toggle:{feature_id}"
            )
        ])

        # Edit
        keyboard.append([
            InlineKeyboardButton(
                text="✏️ ویرایش",
                callback_data=f"admin_features_edit:{feature_id}"
            )
        ])

        # Delete (with confirmation)
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ حذف فیچر",
                callback_data=f"admin_features_delete_confirm:{feature_id}"
            )
        ])

        # Back button
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به لیست",
                callback_data=back_callback
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_delete_confirmation_keyboard(
        feature_id: int,
        back_callback: str = "admin_features_view",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for deleting a feature."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_features_delete_execute:{feature_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"{back_callback}:{feature_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_edit_keyboard(
        feature_id: int,
        back_callback: str = "admin_features_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for editing a feature."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش نام",
                        callback_data=f"admin_features_edit_name:{feature_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش توضیحات",
                        callback_data=f"admin_features_edit_description:{feature_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=f"{back_callback}:{feature_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_toggle_keyboard(
        feature_id: int,
        is_enabled: bool,
        back_callback: str = "admin_features_view",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for toggling a feature."""
        status_text = "فعال" if is_enabled else "غیرفعال"
        new_status_text = "غیرفعال" if is_enabled else "فعال"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ تغییر به {new_status_text}",
                        callback_data=f"admin_features_toggle_confirm:{feature_id}:{not is_enabled}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"{back_callback}:{feature_id}"
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