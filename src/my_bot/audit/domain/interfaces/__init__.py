# my_bot_project/src/my_bot/domain/interfaces/__init__.py
"""
ماژول اینترفیس‌های دامنه (Domain Interfaces).

این ماژول شامل قراردادها (Contracts) و اینترفیس‌هایی است که لایه‌های
بالاتر (Application و Infrastructure) برای تعامل با دامنه از آنها استفاده می‌کنند.
اینترفیس‌ها وابستگی‌ها را معکوس کرده و به ما اجازه می‌دهند پیاده‌سازی‌های
مختلف را جایگزین کنیم.

اینترفیس‌های موجود:
- UserRepository: ذخیره‌سازی و بازیابی کاربران
- OrderRepository: ذخیره‌سازی و بازیابی سفارشات
- PaymentRepository: ذخیره‌سازی و بازیابی تراکنش‌های پرداخت
- CouponRepository: ذخیره‌سازی و بازیابی کوپن‌های تخفیف
- FormRepository: ذخیره‌سازی و بازیابی فرم‌ها
- TicketRepository: ذخیره‌سازی و بازیابی تیکت‌های پشتیبانی
- AuditRepository: ذخیره‌سازی و بازیابی لاگ‌های حسابرسی
- CacheInterface: رابط کش (ذخیره‌سازی موقت)
- MessagePublisher: رابط انتشار پیام (برای ارتباطات ناهمگام)
"""

# ----------------------------------------------
# Import Interfaces from submodules
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