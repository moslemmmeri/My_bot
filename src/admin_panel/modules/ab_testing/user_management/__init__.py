# my_bot_project/src/admin_panel/modules/user_management/__init__.py
"""
ماژول مدیریت کاربران (User Management).

این ماژول شامل هندلرها و سرویس‌های مربوط به مدیریت کاربران در پنل مدیریت است:
- Handlers: لیست کاربران، مشاهده، ویرایش و حذف کاربر
- Services: منطق مدیریت کاربران (لیست، ویرایش)
- Keyboards: کیبوردهای مرتبط با مدیریت کاربران
- Validators: اعتبارسنجی داده‌های کاربران
"""

# ----------------------------------------------
# Import Handlers
# ----------------------------------------------
from admin_panel.modules.user_management.handlers.list_users import ListUsersHandler
from admin_panel.modules.user_management.handlers.view_user import ViewUserHandler
from admin_panel.modules.user_management.handlers.edit_user import EditUserHandler
from admin_panel.modules.user_management.handlers.delete_user import DeleteUserHandler

# ----------------------------------------------
# Import Services
# ----------------------------------------------
from admin_panel.modules.user_management.services.user_list_service import UserListService
from admin_panel.modules.user_management.services.user_edit_service import UserEditService

# ----------------------------------------------
# Import Keyboards
# ----------------------------------------------
from admin_panel.modules.user_management.keyboards.user_list_keyboard import get_user_list_keyboard
from admin_panel.modules.user_management.keyboards.user_edit_keyboard import get_user_edit_keyboard

# ----------------------------------------------
# Import Validators
# ----------------------------------------------
from admin_panel.modules.user_management.validators.user_validator import UserValidator


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Handlers
    "ListUsersHandler",
    "ViewUserHandler",
    "EditUserHandler",
    "DeleteUserHandler",

    # Services
    "UserListService",
    "UserEditService",

    # Keyboards
    "get_user_list_keyboard",
    "get_user_edit_keyboard",

    # Validators
    "UserValidator",
]