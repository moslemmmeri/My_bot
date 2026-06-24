# my_bot_project/src/my_bot/infrastructure/external/__init__.py
"""
ماژول سرویس‌های خارجی (External Services).

این ماژول شامل اتصال به سرویس‌های خارجی و APIهای شخص ثالث است که
سیستم برای انجام وظایف خود به آنها نیاز دارد. این سرویس‌ها شامل
درگاه‌های پرداخت، سرویس‌های ایمیل، پیامک، و غیره هستند.

اجزای اصلی:
- Payment: درگاه‌های پرداخت (زرین‌پال، موک و ...)
- Email: ارسال ایمیل (SMTP)
- SMS: ارسال پیامک (کاوه‌نگار، سامانه پیامکی و ...)
"""

# ----------------------------------------------
# Import Payment Gateways
# ----------------------------------------------
from my_bot.infrastructure.external.payment.zarinpal import ZarinpalGateway
from my_bot.infrastructure.external.payment.mock_gateway import MockPaymentGateway

# ----------------------------------------------
# Import Email Services
# ----------------------------------------------
from my_bot.infrastructure.external.email.smtp_sender import SMTPSender

# ----------------------------------------------
# Import SMS Services
# ----------------------------------------------
from my_bot.infrastructure.external.sms.kavenegar import KavenegarSMS

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # Payment
    "ZarinpalGateway",
    "MockPaymentGateway",

    # Email
    "SMTPSender",

    # SMS
    "KavenegarSMS",
]