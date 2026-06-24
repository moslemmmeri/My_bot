# src/admin_panel/modules/ab_testing/keyboards/ab_test_menu_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List, Dict, Any


class ABTestMenuKeyboard:
    """Keyboard for A/B test menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main A/B test menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🧪 لیست تست‌ها",
                        callback_data="admin_ab_tests_list:1"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ ایجاد تست جدید",
                        callback_data="admin_ab_tests_create"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 آمار تست‌ها",
                        callback_data="admin_ab_tests_stats"
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

    @staticmethod
    def get_actions_keyboard(
        test_id: int,
        current_status: str,
        back_callback: str = "admin_ab_tests_list:1",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with actions for a specific test."""
        keyboard = []

        # View details
        keyboard.append([
            InlineKeyboardButton(
                text="📄 مشاهده جزئیات",
                callback_data=f"admin_ab_tests_view:{test_id}"
            )
        ])

        # View results
        keyboard.append([
            InlineKeyboardButton(
                text="📊 مشاهده نتایج",
                callback_data=f"admin_ab_tests_results:{test_id}"
            )
        ])

        # Edit
        keyboard.append([
            InlineKeyboardButton(
                text="✏️ ویرایش تست",
                callback_data=f"admin_ab_tests_edit:{test_id}"
            )
        ])

        # Status actions
        if current_status == "draft":
            keyboard.append([
                InlineKeyboardButton(
                    text="▶️ شروع تست",
                    callback_data=f"admin_ab_tests_start:{test_id}"
                )
            ])
        elif current_status == "active":
            keyboard.append([
                InlineKeyboardButton(
                    text="⏸️ توقف موقت",
                    callback_data=f"admin_ab_tests_pause:{test_id}"
                )
            ])
        elif current_status == "paused":
            keyboard.append([
                InlineKeyboardButton(
                    text="▶️ ادامه تست",
                    callback_data=f"admin_ab_tests_resume:{test_id}"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    text="⏹️ پایان تست",
                    callback_data=f"admin_ab_tests_complete:{test_id}"
                )
            ])
        elif current_status == "active":
            keyboard.append([
                InlineKeyboardButton(
                    text="⏹️ پایان تست",
                    callback_data=f"admin_ab_tests_complete:{test_id}"
                )
            ])

        # Delete (only for draft or archived)
        if current_status in ["draft", "archived"]:
            keyboard.append([
                InlineKeyboardButton(
                    text="🗑️ حذف تست",
                    callback_data=f"admin_ab_tests_delete_confirm:{test_id}"
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
    def get_filter_keyboard(
        current_status: Optional[str] = None,
        back_callback: str = "admin_ab_tests",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for filtering tests by status."""
        statuses = [
            ("📝 پیش‌نویس", "draft"),
            ("🟢 فعال", "active"),
            ("🟡 متوقف", "paused"),
            ("🔵 تکمیل شده", "completed"),
            ("📦 بایگانی", "archived"),
        ]
        keyboard = []
        for label, status in statuses:
            indicator = " ✅" if current_status == status else ""
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{label}{indicator}",
                    callback_data=f"admin_ab_tests_list:1:{status}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text="🧹 پاک کردن فیلتر",
                callback_data="admin_ab_tests_list:1"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به لیست",
                callback_data=back_callback
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_stats_keyboard(back_callback: str = "admin_ab_tests") -> InlineKeyboardMarkup:
        """Get keyboard for stats page."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی",
                        callback_data="admin_ab_tests_stats_refresh"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست تست‌ها",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_delete_confirmation_keyboard(
        test_id: int,
        back_callback: str = "admin_ab_tests_view",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for deleting a test."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_ab_tests_delete_execute:{test_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"{back_callback}:{test_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_ab_tests") -> InlineKeyboardMarkup:
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
    def get_cancel_keyboard(back_callback: str = "admin_ab_tests") -> InlineKeyboardMarkup:
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