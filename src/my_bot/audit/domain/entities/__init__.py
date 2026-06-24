# my_bot_project/src/my_bot/domain/entities/__init__.py
"""
ماژول موجودیت‌های دامنه (Domain Entities).

این ماژول شامل تمام موجودیت‌های اصلی سیستم است که هستهٔ بیزینس را تشکیل می‌دهند.
هر موجودیت دارای هویت (Identity) و رفتارهای خاص خود است و قوانین دامنه را پیاده‌سازی می‌کند.

موجودیت‌های اصلی:
- User: کاربران سیستم (ادمین، اپراتور، کاربر عادی و مهمان)
- Order: سفارش‌های ثبت‌شده توسط کاربران
- Payment: تراکنش‌های پرداخت
- Coupon: کدهای تخفیف
- Form: فرم‌های پویا
- FormResponse: پاسخ‌های ثبت‌شده برای فرم‌ها
- Ticket: تیکت‌های پشتیبانی
- Broadcast: پیام‌های گروهی
- Feedback: بازخوردهای کاربران
- ABTest: تست‌های A/B
- AuditLog: لاگ‌های حسابرسی
"""

# ----------------------------------------------
# Import Entities
# ----------------------------------------------
from my_bot.domain.entities.user import User
from my_bot.domain.entities.order import Order
from my_bot.domain.entities.payment import Payment
from my_bot.domain.entities.coupon import Coupon
from my_bot.domain.entities.form import Form
from my_bot.domain.entities.form_response import FormResponse
from my_bot.domain.entities.ticket import Ticket
from my_bot.domain.entities.broadcast import Broadcast
from my_bot.domain.entities.feedback import Feedback
from my_bot.domain.entities.ab_test import ABTest
from my_bot.domain.entities.audit_log import AuditLog


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "User",
    "Order",
    "Payment",
    "Coupon",
    "Form",
    "FormResponse",
    "Ticket",
    "Broadcast",
    "Feedback",
    "ABTest",
    "AuditLog",
]