# my_bot_project/src/my_bot/infrastructure/external/email/__init__.py
"""
ماژول سرویس‌های ایمیل (Email Services).

این ماژول شامل پیاده‌سازی سرویس‌های ارسال ایمیل برای اتصال به
سرورهای SMTP و ارسال ایمیل‌های سیستمی، اطلاع‌رسانی و گزارش است.

سرویس‌های موجود:
- SMTPSender: ارسال ایمیل از طریق SMTP
"""

# ----------------------------------------------
# Import Email Services
# ----------------------------------------------
from my_bot.infrastructure.external.email.smtp_sender import SMTPSender

# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    "SMTPSender",
]