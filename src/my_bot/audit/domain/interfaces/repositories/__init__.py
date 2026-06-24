# my_bot_project/src/my_bot/domain/interfaces/repositories/__init__.py
"""
ماژول اینترفیس‌های ریپازیتوری (Repository Interfaces).

این ماژول شامل قراردادهای مربوط به ذخیره‌سازی و بازیابی موجودیت‌های دامنه است.
هر ریپازیتوری مسئولیت مدیریت یک نوع موجودیت خاص را بر عهده دارد و
متدهای CRUD (ایجاد، خواندن، به‌روزرسانی، حذف) و جستجو را تعریف می‌کند.

اینترفیس‌های موجود:
- UserRepository: مدیریت کاربران
- OrderRepository: مدیریت سفارشات
- PaymentRepository: مدیریت تراکنش‌های پرداخت
- CouponRepository: مدیریت کوپن‌های تخفیف
- FormRepository: مدیریت فرم‌ها
- TicketRepository: مدیریت تیکت‌های پشتیبانی
- AuditRepository: مدیریت لاگ‌های حسابرسی
"""

# ----------------------------------------------
# Import Repository Interfaces
# ----------------------------------------------
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.interfaces.repositories.audit_repository import AuditRepository

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "UserRepository",
    "OrderRepository",
    "PaymentRepository",
    "CouponRepository",
    "FormRepository",
    "TicketRepository",
    "AuditRepository",
]