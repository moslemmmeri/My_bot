# src/admin_panel/modules/order_management/keyboards/order_actions.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional


class OrderActionsKeyboard:
    """Keyboard for order actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        order_id: int,
        current_status: str,
        back_callback: str = "admin_orders",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with all actions for a specific order."""
        keyboard = []

        # View details
        keyboard.append([
            InlineKeyboardButton(
                text="📄 مشاهده جزئیات",
                callback_data=f"order_view:{order_id}"
            )
        ])

        # Edit status
        status_buttons = []
        statuses = [
            ("⏳ در انتظار", "pending"),
            ("✅ پرداخت شده", "paid"),
            ("📦 ارسال شده", "shipped"),
            ("🚚 تحویل شده", "delivered"),
            ("❌ لغو شده", "cancelled"),
            ("⚠️ ناموفق", "failed"),
        ]

        for label, status in statuses:
            if status != current_status:
                status_buttons.append(
                    InlineKeyboardButton(
                        text=f"🔄 {label}",
                        callback_data=f"order_status:{order_id}:{status}"
                    )
                )

        # Add status buttons in rows of 2
        for i in range(0, len(status_buttons), 2):
            row = status_buttons[i:i+2]
            if row:
                keyboard.append(row)

        # Edit fields
        keyboard.append([
            InlineKeyboardButton(
                text="✏️ ویرایش سفارش",
                callback_data=f"order_edit:{order_id}"
            )
        ])

        # Export
        keyboard.append([
            InlineKeyboardButton(
                text="📥 خروجی PDF",
                callback_data=f"order_export_pdf:{order_id}"
            )
        ])

        # Delete (with confirmation)
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ حذف سفارش",
                callback_data=f"delete_order_confirm:{order_id}"
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
    def get_confirmation_keyboard(
        order_id: int,
        action: str,
        confirm_callback: str,
        cancel_callback: str = "admin_orders",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for dangerous actions (delete, etc)."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، ادامه",
                        callback_data=confirm_callback
                    ),
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=cancel_callback
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=cancel_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_status_edit_keyboard(
        order_id: int,
        current_status: str,
        back_callback: str = "admin_orders",
    ) -> InlineKeyboardMarkup:
        """Keyboard specifically for editing status."""
        statuses = [
            ("⏳ در انتظار", "pending"),
            ("✅ پرداخت شده", "paid"),
            ("📦 ارسال شده", "shipped"),
            ("🚚 تحویل شده", "delivered"),
            ("❌ لغو شده", "cancelled"),
            ("⚠️ ناموفق", "failed"),
        ]

        keyboard = []
        for label, status in statuses:
            indicator = " ✅" if status == current_status else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"order_status_update:{order_id}:{status}"
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
    def get_cancel_keyboard(
        order_id: int,
        back_callback: str = "admin_orders",
    ) -> InlineKeyboardMarkup:
        """Keyboard for canceling an order with reason."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ لغو سفارش",
                        callback_data=f"order_cancel:{order_id}:user_request"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو به دلیل مشکل سیستم",
                        callback_data=f"order_cancel:{order_id}:system_error"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو به دلیل عدم پرداخت",
                        callback_data=f"order_cancel:{order_id}:payment_failed"
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