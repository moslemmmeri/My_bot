# my_bot_project/src/my_bot/core/constants/__init__.py
"""
ماژول ثابت‌ها (Constants): شامل Enumها و مقادیر ثابت مورد استفاده در سراسر پروژه.

این ماژول نقش مرکزی برای تعریف وضعیت‌ها، نقش‌ها و انواع داده‌های ثابت را ایفا می‌کند.
با استفاده از Enumها، از بروز خطاهای ناشی از استفاده از رشته‌های ساده جلوگیری می‌شود.
"""

from my_bot.core.constants.user_roles import UserRole
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.constants.form_types import FormType

__all__ = [
    "UserRole",
    "OrderStatus",
    "PaymentStatus",
    "FormType",
]