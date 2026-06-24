# my_bot_project/src/my_bot/notifications/senders/__init__.py
"""
ماژول فرستنده‌های نوتیفیکیشن (Notification Senders).

این ماژول شامل کلاس‌های ارسال نوتیفیکیشن از طریق کانال‌های مختلف است:
- TelegramSender: ارسال نوتیفیکیشن از طریق ربات تلگرام
- EmailSender: ارسال نوتیفیکیشن از طریق ایمیل
"""

from my_bot.notifications.senders.telegram_sender import TelegramSender
from my_bot.notifications.senders.email_sender import EmailSender

__all__ = [
    "TelegramSender",
    "EmailSender",
]