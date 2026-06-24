# src/admin_panel/modules/admin_management/keyboards/admin_actions.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List


class AdminActionsKeyboard:
    """Keyboard for admin actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        admin_id: int,
        current_role: str,
        is_active: bool,
        back_callback: str = "admin_admins",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with all actions for a specific admin."""
        keyboard = []

        # View details
        keyboard.append([
            InlineKeyboardButton(
                text="👤 مشاهده جزئیات",
                callback_data=f"admin_admins_view:{admin_id}"
            )
        ])

        # Edit role
        keyboard.append([
            InlineKeyboardButton(
                text="📋 تغییر نقش",
                callback_data=f"admin_admins_edit_role:{admin_id}"
            )
        ])

        # Toggle active status
        status_text = "❌ غیرفعال کردن" if is_active else "✅ فعال کردن"
        keyboard.append([
            InlineKeyboardButton(
                text=status_text,
                callback_data=f"admin_admins_toggle_status:{admin_id}"
            )
        ])

        # Remove admin (dangerous)
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ حذف از ادمین‌ها",
                callback_data=f"admin_admins_remove_confirm:{admin_id}"
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
    def get_remove_confirmation_keyboard(
        admin_id: int,
        back_callback: str = "admin_admins",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for removing an admin."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_admins_remove_execute:{admin_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_role_edit_keyboard(
        admin_id: int,
        current_role: str,
        back_callback: str = "admin_admins",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for editing admin role."""
        roles = [
            ("🔱 سوپر ادمین", "super_admin"),
            ("👤 ادمین", "admin"),
            ("🛡️ مدیر", "moderator"),
            ("💬 پشتیبان", "support"),
        ]

        keyboard = []
        for label, role in roles:
            indicator = " ✅" if role == current_role else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_admins_set_role:{admin_id}:{role}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=back_callback
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_toggle_status_keyboard(
        admin_id: int,
        is_active: bool,
        back_callback: str = "admin_admins",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for toggling admin status."""
        text = "❌ غیرفعال کردن" if is_active else "✅ فعال کردن"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=text,
                        callback_data=f"admin_admins_toggle_execute:{admin_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_admins") -> InlineKeyboardMarkup:
        """Get simple cancel/back keyboard."""
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