# src/admin_panel/modules/tickets/keyboards/ticket_actions_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional


class TicketActionsKeyboard:
    """Keyboard for ticket actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        ticket_id: int,
        current_status: str,
        back_callback: str = "admin_tickets_list:1",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with all actions for a specific ticket."""
        keyboard = []

        # View details (already viewing, but keep for navigation)
        keyboard.append([
            InlineKeyboardButton(
                text="📄 مشاهده مجدد",
                callback_data=f"admin_tickets_view:{ticket_id}"
            )
        ])

        # Reply
        keyboard.append([
            InlineKeyboardButton(
                text="💬 پاسخ",
                callback_data=f"admin_tickets_reply:{ticket_id}"
            )
        ])

        # Assign
        keyboard.append([
            InlineKeyboardButton(
                text="👤 تخصیص",
                callback_data=f"admin_tickets_assign:{ticket_id}"
            )
        ])

        # Status actions
        if current_status == "open":
            keyboard.append([
                InlineKeyboardButton(
                    text="🟡 در حال بررسی",
                    callback_data=f"admin_tickets_set_status:{ticket_id}:in_progress"
                )
            ])
        elif current_status == "in_progress":
            keyboard.append([
                InlineKeyboardButton(
                    text="🔵 حل شده",
                    callback_data=f"admin_tickets_set_status:{ticket_id}:resolved"
                )
            ])

        if current_status not in ["closed", "resolved"]:
            keyboard.append([
                InlineKeyboardButton(
                    text="🔒 بستن تیکت",
                    callback_data=f"admin_tickets_close:{ticket_id}"
                )
            ])

        # Priority change (optional)
        keyboard.append([
            InlineKeyboardButton(
                text="🔴 تغییر اولویت",
                callback_data=f"admin_tickets_change_priority:{ticket_id}"
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
    def get_close_confirmation_keyboard(
        ticket_id: int,
        back_callback: str = "admin_tickets_view",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for closing a ticket."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، بسته شود",
                        callback_data=f"admin_tickets_close_execute:{ticket_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"{back_callback}:{ticket_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_assign_keyboard(
        ticket_id: int,
        available_admins: List[Dict[str, Any]],
        back_callback: str = "admin_tickets_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for assigning a ticket to an admin."""
        keyboard = []
        for admin in available_admins[:10]:  # Limit to 10 for display
            admin_id = admin.get("id")
            username = admin.get("username", f"ادمین {admin_id}")
            keyboard.append([
                InlineKeyboardButton(
                    text=f"👤 {username}",
                    callback_data=f"admin_tickets_assign_execute:{ticket_id}:{admin_id}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=f"{back_callback}:{ticket_id}"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_priority_keyboard(
        ticket_id: int,
        current_priority: str,
        back_callback: str = "admin_tickets_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for changing ticket priority."""
        priorities = [
            ("🟢 کم", "low"),
            ("🟡 متوسط", "medium"),
            ("🔴 بالا", "high"),
            ("🚨 بحرانی", "critical"),
        ]
        keyboard = []
        for label, priority in priorities:
            indicator = " ✅" if priority == current_priority else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_tickets_set_priority:{ticket_id}:{priority}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=f"{back_callback}:{ticket_id}"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_status_keyboard(
        ticket_id: int,
        current_status: str,
        back_callback: str = "admin_tickets_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for changing ticket status."""
        statuses = [
            ("🟢 باز", "open"),
            ("🟡 در حال بررسی", "in_progress"),
            ("🔵 حل شده", "resolved"),
            ("⚪ بسته", "closed"),
        ]
        keyboard = []
        for label, status in statuses:
            indicator = " ✅" if status == current_status else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_tickets_set_status:{ticket_id}:{status}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data=f"{back_callback}:{ticket_id}"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_reply_keyboard(
        ticket_id: int,
        back_callback: str = "admin_tickets_view",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for replying (with cancel option)."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=f"{back_callback}:{ticket_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_tickets_list:1") -> InlineKeyboardMarkup:
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
    def get_cancel_keyboard(back_callback: str = "admin_tickets") -> InlineKeyboardMarkup:
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