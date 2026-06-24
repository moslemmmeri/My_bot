# src/admin_panel/modules/backup_restore/keyboards/backup_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional


class BackupMenuKeyboard:
    """Keyboard for backup menu in admin panel."""

    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main backup menu keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🆕 ایجاد پشتیبان جدید",
                        callback_data="admin_backup_now"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📂 لیست پشتیبان‌ها",
                        callback_data="admin_backup_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 بازیابی پشتیبان",
                        callback_data="admin_restore_backup"
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
    def get_confirm_keyboard() -> InlineKeyboardMarkup:
        """Get confirmation keyboard for creating backup."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، ایجاد شود",
                        callback_data="admin_backup_confirm"
                    ),
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_backup"
                    )
                ]
            ]
        )

    @staticmethod
    def get_backup_list_keyboard(
        backups: List[Dict[str, Any]],
        page: int = 1,
        page_size: int = 10,
    ) -> InlineKeyboardMarkup:
        """Get keyboard with list of backup files."""
        keyboard = []

        # Show backup items (limited to page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        for backup in backups[start_idx:end_idx]:
            filename = backup.get("filename", "")
            size = backup.get("size", 0)
            display_name = filename[:30] + "..." if len(filename) > 30 else filename
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📁 {display_name} ({size/1024:.1f}KB)",
                    callback_data=f"admin_backup_action:{filename}"
                )
            ])

        # Pagination row
        total_pages = (len(backups) + page_size - 1) // page_size
        if total_pages > 1:
            nav_row = []
            if page > 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="⬅️ قبلی",
                        callback_data=f"admin_backup_list_page:{page - 1}"
                    )
                )
            nav_row.append(
                InlineKeyboardButton(
                    text=f"{page}/{total_pages}",
                    callback_data="admin_backup_list"
                )
            )
            if page < total_pages:
                nav_row.append(
                    InlineKeyboardButton(
                        text="➡️ بعدی",
                        callback_data=f"admin_backup_list_page:{page + 1}"
                    )
                )
            keyboard.append(nav_row)

        keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به منوی پشتیبان",
                callback_data="admin_backup"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_action_keyboard(filename: str) -> InlineKeyboardMarkup:
        """Get keyboard with actions for a specific backup."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 بازیابی",
                        callback_data=f"admin_restore_confirm:{filename}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="ℹ️ اطلاعات",
                        callback_data=f"admin_backup_info:{filename}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ حذف",
                        callback_data=f"admin_backup_delete_confirm:{filename}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست",
                        callback_data="admin_backup_list"
                    )
                ]
            ]
        )

    @staticmethod
    def get_delete_confirm_keyboard(filename: str) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for deleting a backup."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_backup_delete_execute:{filename}"
                    ),
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"admin_backup_action:{filename}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_restore_confirm_keyboard(filename: str) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for restoring a backup."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚠️ بله، بازیابی شود",
                        callback_data=f"admin_restore_execute:{filename}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"admin_backup_action:{filename}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_backup") -> InlineKeyboardMarkup:
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