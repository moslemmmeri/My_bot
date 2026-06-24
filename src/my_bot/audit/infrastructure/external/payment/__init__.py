# my_bot_project/src/my_bot/infrastructure/external/payment/__init__.py
"""
ماژول درگاه‌های پرداخت (Payment Gateways).

این ماژول شامل پیاده‌سازی درگاه‌های پرداخت مختلف برای اتصال به
سیستم‌های پرداخت خارجی و مدیریت تراکنش‌های مالی است.

درگاه‌های موجود:
- ZarinpalGateway: درگاه پرداخت زرین‌پال
- MockPaymentGateway: درگاه پرداخت شبیه‌سازی‌شده برای تست و توسعه
"""

# ----------------------------------------------
# Import Payment Gateways
# ----------------------------------------------
from my_bot.infrastructure.external.payment.zarinpal import ZarinpalGateway
from my_bot.infrastructure.external.payment.mock_gateway import MockPaymentGateway

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "ZarinpalGateway",
    "MockPaymentGateway",
]