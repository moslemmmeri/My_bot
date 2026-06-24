# my_bot_project/src/my_bot/domain/__init__.py
"""
ماژول Domain (لایه دامنه).

این ماژول شامل هستهٔ بیزینس پروژه است و مستقل از هرگونه فریم‌ورک یا زیرساخت خارجی می‌باشد.
لایهٔ دامنه شامل موجودیت‌های اصلی (Entities)، ارزش‌مقادیر (Value Objects) و
اینترفیس‌های مورد نیاز برای لایه‌های بالاتر است.

اجزای اصلی:
- Entities: موجودیت‌های اصلی سیستم (User, Order, Payment, Form, Ticket, ...)
- Value Objects: اشیاء ارزشی مانند Email, Phone, Money, UserLevel, ...
- Interfaces: قراردادهای مورد نیاز برای ریپازیتوری‌ها، کش، پیام‌رسانی و ...
"""

# ----------------------------------------------
# Import Entities (موجودیت‌ها)
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
# Import Value Objects (ارزش‌مقادیر)
# ----------------------------------------------
from my_bot.domain.value_objects.email import Email
from my_bot.domain.value_objects.phone import Phone
from my_bot.domain.value_objects.money import Money
from my_bot.domain.value_objects.rate_limit import RateLimit
from my_bot.domain.value_objects.form_field import FormField
from my_bot.domain.value_objects.user_level import UserLevel

# ----------------------------------------------
# Import Interfaces (اینترفیس‌ها)
# ----------------------------------------------
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.repositories.ticket_repository import TicketRepository
from my_bot.domain.interfaces.repositories.audit_repository import AuditRepository
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Entities
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

    # Value Objects
    "Email",
    "Phone",
    "Money",
    "RateLimit",
    "FormField",
    "UserLevel",

    # Interfaces
    "UserRepository",
    "OrderRepository",
    "PaymentRepository",
    "CouponRepository",
    "FormRepository",
    "TicketRepository",
    "AuditRepository",
    "CacheInterface",
    "MessagePublisher",
]