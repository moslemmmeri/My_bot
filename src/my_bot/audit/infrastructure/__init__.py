# my_bot_project/src/my_bot/infrastructure/__init__.py
"""
ماژول زیرساخت (Infrastructure).

این ماژول شامل پیاده‌سازی‌های عینی (Concrete Implementations) اینترفیس‌های
لایه دامنه و ابزارهای مورد نیاز برای اتصال به سرویس‌های خارجی است.
لایه زیرساخت کاملاً وابسته به لایه دامنه است و قراردادهای آن را پیاده‌سازی می‌کند.

اجزای اصلی:
- Database: اتصال به دیتابیس (PostgreSQL/SQLite) با Connection Pool
- Repositories: پیاده‌سازی ریپازیتوری‌های دامنه
- Cache: سیستم کش با Redis و Local Fallback
- External: اتصال به سرویس‌های خارجی (درگاه پرداخت، ایمیل، SMS)
- Health Check: بررسی سلامت سرویس‌های زیرساخت
"""

# ----------------------------------------------
# Import Database Components
# ----------------------------------------------
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.database.connection_pool import ConnectionPool

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
# Import Cache Components
# ----------------------------------------------
from my_bot.infrastructure.cache.cache_manager import CacheManager
from my_bot.infrastructure.cache.redis_adapter import RedisAdapter
from my_bot.infrastructure.cache.local_adapter import LocalAdapter
from my_bot.infrastructure.cache.cache_fallback import CacheFallback

# ----------------------------------------------
# Import External Services
# ----------------------------------------------
from my_bot.infrastructure.external.payment.zarinpal import ZarinpalGateway
from my_bot.infrastructure.external.payment.mock_gateway import MockPaymentGateway
from my_bot.infrastructure.external.email.smtp_sender import SMTPSender
from my_bot.infrastructure.external.sms.kavenegar import KavenegarSMS

# ----------------------------------------------
# Import Health Check Components
# ----------------------------------------------
from my_bot.infrastructure.health_check.health_checker import HealthChecker
from my_bot.infrastructure.health_check.db_health import DatabaseHealthCheck
from my_bot.infrastructure.health_check.cache_health import CacheHealthCheck
from my_bot.infrastructure.health_check.external_health import ExternalServiceHealthCheck


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Database
    "DatabaseSessionManager",
    "ConnectionPool",

    # Repositories
    "UserRepositoryImpl",
    "OrderRepositoryImpl",
    "PaymentRepositoryImpl",
    "CouponRepositoryImpl",
    "FormRepositoryImpl",
    "TicketRepositoryImpl",
    "AuditRepositoryImpl",

    # Cache
    "CacheManager",
    "RedisAdapter",
    "LocalAdapter",
    "CacheFallback",

    # External
    "ZarinpalGateway",
    "MockPaymentGateway",
    "SMTPSender",
    "KavenegarSMS",

    # Health Check
    "HealthChecker",
    "DatabaseHealthCheck",
    "CacheHealthCheck",
    "ExternalServiceHealthCheck",
]