# src/admin_panel/modules/content_management/keyboards/content_actions.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List


class ContentActionsKeyboard:
    """Keyboard for content actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        content_id: int,
        current_status: str,
        back_callback: str = "admin_content",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with all actions for a specific content item."""
        keyboard = []

        # View details
        keyboard.append([
            InlineKeyboardButton(
                text="📄 مشاهده جزئیات",
                callback_data=f"admin_content_view:{content_id}"
            )
        ])

        # Edit title
        keyboard.append([
            InlineKeyboardButton(
                text="✏️ ویرایش عنوان",
                callback_data=f"admin_content_edit_title:{content_id}"
            )
        ])

        # Edit body
        keyboard.append([
            InlineKeyboardButton(
                text="📝 ویرایش متن",
                callback_data=f"admin_content_edit_body:{content_id}"
            )
        ])

        # Status management
        status_buttons = []
        if current_status == "published":
            status_buttons.append(
                InlineKeyboardButton(
                    text="📝 تبدیل به پیش‌نویس",
                    callback_data=f"admin_content_set_status:{content_id}:draft"
                )
            )
        else:
            status_buttons.append(
                InlineKeyboardButton(
                    text="✅ انتشار",
                    callback_data=f"admin_content_set_status:{content_id}:published"
                )
            )

        status_buttons.append(
            InlineKeyboardButton(
                text="📦 آرشیو",
                callback_data=f"admin_content_set_status:{content_id}:archived"
            )
        )

        if len(status_buttons) == 2:
            keyboard.append(status_buttons)
        else:
            keyboard.append(status_buttons[:1])
            keyboard.append(status_buttons[1:])

        # Change type
        keyboard.append([
            InlineKeyboardButton(
                text="📂 تغییر نوع",
                callback_data=f"admin_content_edit_type:{content_id}"
            )
        ])

        # Delete (with confirmation)
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ حذف محتوا",
                callback_data=f"admin_content_delete_confirm:{content_id}"
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
        content_id: int,
        back_callback: str = "admin_content",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for deleting content."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_content_delete_execute:{content_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=back_callback
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
    def get_type_edit_keyboard(
        content_id: int,
        current_type: str,
        back_callback: str = "admin_content",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for editing content type."""
        types = [
            ("📄 مقاله", "article"),
            ("📰 خبر", "news"),
            ("📝 صفحه", "page"),
            ("🎯 لندینگ", "landing"),
        ]

        keyboard = []
        for label, type_name in types:
            indicator = " ✅" if type_name == current_type else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_content_set_type:{content_id}:{type_name}"
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
    def get_status_edit_keyboard(
        content_id: int,
        current_status: str,
        back_callback: str = "admin_content",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for editing content status."""
        statuses = [
            ("📝 پیش‌نویس", "draft"),
            ("✅ منتشر شده", "published"),
            ("📦 آرشیو", "archived"),
        ]

        keyboard = []
        for label, status in statuses:
            indicator = " ✅" if status == current_status else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_content_set_status:{content_id}:{status}"
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
        back_callback: str = "admin_content",
    ) -> InlineKeyboardMarkup:
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