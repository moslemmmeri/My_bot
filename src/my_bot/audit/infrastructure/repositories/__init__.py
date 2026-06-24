# my_bot_project/src/my_bot/infrastructure/repositories/__init__.py
"""
ماژول پیاده‌سازی ریپازیتوری‌ها (Repository Implementations).

این ماژول شامل پیاده‌سازی‌های عینی (Concrete Implementations) اینترفیس‌های
ریپازیتوری لایه دامنه است. هر ریپازیتوری مسئولیت ذخیره‌سازی و بازیابی
یک موجودیت خاص را در دیتابیس بر عهده دارد.

ریپازیتوری‌های موجود:
- UserRepositoryImpl: مدیریت کاربران
- OrderRepositoryImpl: مدیریت سفارشات
- PaymentRepositoryImpl: مدیریت تراکنش‌های پرداخت
- CouponRepositoryImpl: مدیریت کوپن‌های تخفیف
- FormRepositoryImpl: مدیریت فرم‌ها
- TicketRepositoryImpl: مدیریت تیکت‌های پشتیبانی
- AuditRepositoryImpl: مدیریت لاگ‌های حسابرسی
"""

# ----------------------------------------------
# Import Repository Implementations
# ----------------------------------------------
from my_bot.infrastructure.repositories.user_repo_impl import UserRepositoryImpl
from my_bot.infrastructure.repositories.order_repo_impl import OrderRepositoryImpl
from my_bot.infrastructure.repositories.payment_repo_impl import PaymentRepositoryImpl
from my_bot.infrastructure.repositories.coupon_repo_impl import CouponRepositoryImpl
from my_bot.infrastructure.repositories.form_repo_impl import FormRepositoryImpl
from my_bot.infrastructure.repositories.ticket_repo_impl import TicketRepositoryImpl
from my_bot.infrastructure.repositories.audit_repo_impl import AuditRepositoryImpl

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "UserRepositoryImpl",
    "OrderRepositoryImpl",
    "PaymentRepositoryImpl",
    "CouponRepositoryImpl",
    "FormRepositoryImpl",
    "TicketRepositoryImpl",
    "AuditRepositoryImpl",
]