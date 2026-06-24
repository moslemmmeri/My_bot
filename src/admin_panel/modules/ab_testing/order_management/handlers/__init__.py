# my_bot_project/src/admin_panel/modules/order_management/handlers/__init__.py
"""
ماژول هندلرهای مدیریت سفارشات (Order Management Handlers).

این ماژول شامل هندلرهای مربوط به مدیریت سفارشات در پنل مدیریت است:
- ListOrdersHandler: نمایش لیست سفارشات با صفحه‌بندی و فیلتر
- ViewOrderHandler: نمایش اطلاعات کامل یک سفارش
- EditOrderHandler: ویرایش اطلاعات سفارش
- DeleteOrderHandler: حذف سفارش
"""

from admin_panel.modules.order_management.handlers.list_orders import ListOrdersHandler
from admin_panel.modules.order_management.handlers.view_order import ViewOrderHandler
from admin_panel.modules.order_management.handlers.edit_order import EditOrderHandler
from admin_panel.modules.order_management.handlers.delete_order import DeleteOrderHandler

__all__ = [
    "ListOrdersHandler",
    "ViewOrderHandler",
    "EditOrderHandler",
    "DeleteOrderHandler",
]