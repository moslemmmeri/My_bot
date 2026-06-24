# src/admin_panel/modules/feedback_management/keyboards/feedback_actions_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional


class FeedbackActionsKeyboard:
    """Keyboard for feedback actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        feedback_id: int,
        current_status: str,
        back_callback: str = "admin_feedback_list:1",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with all actions for a specific feedback."""
        keyboard = []

        # View details (already viewing, but keep for navigation)
        keyboard.append([
            InlineKeyboardButton(
                text="📄 مشاهده مجدد",
                callback_data=f"admin_feedback_view:{feedback_id}"
            )
        ])

        # Reply
        keyboard.append([
            InlineKeyboardButton(
                text="💬 پاسخ",
                callback_data=f"admin_feedback_reply:{feedback_id}"
            )
        ])

        # Status actions
        if current_status == "pending":
            keyboard.append([
                InlineKeyboardButton(
                    text="🔵 پاسخ داده شده",
                    callback_data=f"admin_feedback_set_status:{feedback_id}:replied"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    text="🟢 حل شده",
                    callback_data=f"admin_feedback_set_status:{feedback_id}:resolved"
                )
            ])
        elif current_status == "replied":
            keyboard.append([
                InlineKeyboardButton(
                    text="🟢 حل شده",
                    callback_data=f"admin_feedback_set_status:{feedback_id}:resolved"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    text="🟡 بازگشت به در انتظار",
                    callback_data=f"admin_feedback_set_status:{feedback_id}:pending"
                )
            ])
        elif current_status == "resolved":
            keyboard.append([
                InlineKeyboardButton(
                    text="🟡 بازگشت به در انتظار",
                    callback_data=f"admin_feedback_set_status:{feedback_id}:pending"
                )
            ])

        # Delete (with confirmation)
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ حذف بازخورد",
                callback_data=f"admin_feedback_delete_confirm:{feedback_id}"
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
    def get_reply_keyboard(
        feedback_id: int,
        back_callback: str = "admin_feedback_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for replying with cancel option."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"{back_callback}:{feedback_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_delete_confirmation_keyboard(
        feedback_id: int,
        back_callback: str = "admin_feedback_view",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for deleting a feedback."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_feedback_delete_execute:{feedback_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"{back_callback}:{feedback_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_status_keyboard(
        feedback_id: int,
        current_status: str,
        back_callback: str = "admin_feedback_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for changing feedback status."""
        statuses = [
            ("🟡 در انتظار", "pending"),
            ("🔵 پاسخ داده شده", "replied"),
            ("🟢 حل شده", "resolved"),
        ]
        keyboard = []
        for label, status in statuses:
            indicator = " ✅" if status == current_status else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_feedback_set_status:{feedback_id}:{status}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=f"{back_callback}:{feedback_id}"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_feedback_list:1") -> InlineKeyboardMarkup:
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

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_feedback_list:1") -> InlineKeyboardMarkup:
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