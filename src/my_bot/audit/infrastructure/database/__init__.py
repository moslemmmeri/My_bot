# my_bot_project/src/my_bot/infrastructure/database/__init__.py
"""
ماژول دیتابیس (Database).

این ماژول شامل مدیریت اتصال به دیتابیس، Connection Pool،
مدل‌های SQLAlchemy و ابزارهای مهاجرت (Migration) است.

اجزای اصلی:
- DatabaseSessionManager: مدیریت جلسات (Sessions) دیتابیس
- ConnectionPool: مدیریت Connection Pool
- Models: مدل‌های SQLAlchemy برای هر موجودیت
- Migrations: اسکریپت‌های مهاجرت Alembic
"""

# Import core database components
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.database.connection_pool import ConnectionPool

# Import models (optional, for convenience)
# from my_bot.infrastructure.database.models import (
#     UserModel,
#     OrderModel,
#     PaymentModel,
#     CouponModel,
#     FormModel,
#     TicketModel,
# )

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "DatabaseSessionManager",
    "ConnectionPool",
    # "UserModel",
    # "OrderModel",
    # "PaymentModel",
    # "CouponModel",
    # "FormModel",
    # "TicketModel",
]