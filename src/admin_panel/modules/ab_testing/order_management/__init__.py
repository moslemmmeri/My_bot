# my_bot_project/src/admin_panel/modules/order_management/__init__.py
"""
ماژول مدیریت سفارشات (Order Management).

این ماژول شامل هندلرها و سرویس‌های مربوط به مدیریت سفارشات در پنل مدیریت است:
- Handlers: لیست سفارشات، مشاهده، ویرایش و حذف سفارش
- Services: منطق مدیریت سفارشات (لیست، به‌روزرسانی)
- Keyboards: کیبوردهای مرتبط با مدیریت سفارشات (فیلترها، اقدامات)
- Validators: اعتبارسنجی داده‌های سفارشات
"""

# ----------------------------------------------
# Import Handlers
# ----------------------------------------------
from admin_panel.modules.order_management.handlers.list_orders import ListOrdersHandler
from admin_panel.modules.order_management.handlers.view_order import ViewOrderHandler
from admin_panel.modules.order_management.handlers.edit_order import EditOrderHandler
from admin_panel.modules.order_management.handlers.delete_order import DeleteOrderHandler

# ----------------------------------------------
# Import Services
# ----------------------------------------------
from admin_panel.modules.order_management.services.order_list_service import OrderListService
from admin_panel.modules.order_management.services.order_update_service import OrderUpdateService

# ----------------------------------------------
# Import Keyboards
# ----------------------------------------------
from admin_panel.modules.order_management.keyboards.order_filters import get_order_filters_keyboard
from admin_panel.modules.order_management.keyboards.order_actions import get_order_actions_keyboard

# ----------------------------------------------
# Import Validators
# ----------------------------------------------
from admin_panel.modules.order_management.validators.order_validator import OrderValidator


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Handlers
    "ListOrdersHandler",
    "ViewOrderHandler",
    "EditOrderHandler",
    "DeleteOrderHandler",

    # Services
    "OrderListService",
    "OrderUpdateService",

    # Keyboards
    "get_order_filters_keyboard",
    "get_order_actions_keyboard",

    # Validators
    "OrderValidator",
]