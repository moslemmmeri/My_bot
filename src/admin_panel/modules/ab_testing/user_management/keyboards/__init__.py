# my_bot_project/src/admin_panel/modules/user_management/keyboards/__init__.py
"""
ماژول کیبوردهای مدیریت کاربران (User Management Keyboards).

این ماژول شامل کیبوردهای مربوط به مدیریت کاربران در پنل مدیریت است:
- user_list_keyboard: کیبورد لیست کاربران با صفحه‌بندی و فیلتر
- user_edit_keyboard: کیبورد ویرایش کاربر
"""

from admin_panel.modules.user_management.keyboards.user_list_keyboard import get_user_list_keyboard
from admin_panel.modules.user_management.keyboards.user_edit_keyboard import get_user_edit_keyboard

__all__ = [
    "get_user_list_keyboard",
    "get_user_edit_keyboard",
]