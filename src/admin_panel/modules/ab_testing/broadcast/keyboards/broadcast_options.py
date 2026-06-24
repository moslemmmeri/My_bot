# src/admin_panel/modules/broadcast/keyboards/broadcast_options.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List, Dict, Any


class BroadcastOptionsKeyboard:
    """Keyboard for broadcast options in admin panel."""

    @staticmethod
    def get_type_keyboard(back_callback: str = "admin_broadcast") -> InlineKeyboardMarkup:
        """Get keyboard for selecting message type."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 متن",
                        callback_data="admin_broadcast_type:text"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🖼️ عکس",
                        callback_data="admin_broadcast_type:photo"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎬 ویدیو",
                        callback_data="admin_broadcast_type:video"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📄 سند",
                        callback_data="admin_broadcast_type:document"
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
    def get_schedule_keyboard(back_callback: str = "admin_broadcast_preview") -> InlineKeyboardMarkup:
        """Get keyboard for selecting send time."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📤 ارسال فوری",
                        callback_data="admin_broadcast_schedule:now"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 زمان‌بندی شده",
                        callback_data="admin_broadcast_schedule:later"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به پیش‌نمایش",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_audience_keyboard(back_callback: str = "admin_broadcast_preview") -> InlineKeyboardMarkup:
        """Get keyboard for selecting audience."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🌐 همه کاربران",
                        callback_data="admin_broadcast_audience:all"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔍 کاربران فیلتر شده",
                        callback_data="admin_broadcast_audience:filtered"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧪 کاربران تستی",
                        callback_data="admin_broadcast_audience:test"
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
    def get_confirm_keyboard(
        broadcast_id: Optional[int] = None,
        back_callback: str = "admin_broadcast_preview",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for confirming broadcast send."""
        keyboard = [
            [
                InlineKeyboardButton(
                    text="✅ ارسال نهایی",
                    callback_data="admin_broadcast_send_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ ویرایش پیام",
                    callback_data="admin_broadcast_compose"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به پیش‌نمایش",
                    callback_data=back_callback
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_broadcast"
                )
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_schedule_time_keyboard(
        hours: List[int] = None,
        back_callback: str = "admin_broadcast_schedule",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for selecting scheduled time (hour presets)."""
        if hours is None:
            hours = [1, 2, 6, 12, 24, 48]
        keyboard = []
        row = []
        for hour in hours:
            row.append(
                InlineKeyboardButton(
                    text=f"{hour}h",
                    callback_data=f"admin_broadcast_schedule_time:{hour}"
                )
            )
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton(
                text="📅 انتخاب تاریخ و زمان دلخواه",
                callback_data="admin_broadcast_schedule_custom"
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
    def get_quick_actions_keyboard() -> InlineKeyboardMarkup:
        """Get keyboard with quick broadcast actions."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 ارسال پیام متنی",
                        callback_data="admin_broadcast_type:text"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🖼️ ارسال عکس",
                        callback_data="admin_broadcast_type:photo"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 ارسال به کاربران فیلتر شده",
                        callback_data="admin_broadcast_audience:filtered"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 ارسال به همه کاربران",
                        callback_data="admin_broadcast_audience:all"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📅 زمان‌بندی ارسال",
                        callback_data="admin_broadcast_schedule:later"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی اصلی",
                        callback_data="admin_broadcast"
                    )
                ]
            ]
        )