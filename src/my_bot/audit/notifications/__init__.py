# my_bot_project/src/my_bot/notifications/__init__.py
"""
ماژول نوتیفیکیشن‌ها و یادآوری‌ها (Notifications).

این ماژول شامل ابزارهای ارسال نوتیفیکیشن، زمان‌بندی یادآوری‌ها
و گزارش‌های خودکار است:
- Schedulers: زمان‌بندی ارسال نوتیفیکیشن‌ها (یادآوری، گزارش)
- Senders: ارسال نوتیفیکیشن از طریق کانال‌های مختلف (تلگرام، ایمیل)
- Templates: قالب‌های پیام برای نوتیفیکیشن‌ها
"""

from my_bot.notifications.schedulers.reminder_scheduler import ReminderScheduler
from my_bot.notifications.schedulers.report_scheduler import ReportScheduler
from my_bot.notifications.senders.telegram_sender import TelegramSender
from my_bot.notifications.senders.email_sender import EmailSender
from my_bot.notifications.templates.reminder_template import ReminderTemplate
from my_bot.notifications.templates.report_template import ReportTemplate

__all__ = [
    "ReminderScheduler",
    "ReportScheduler",
    "TelegramSender",
    "EmailSender",
    "ReminderTemplate",
    "ReportTemplate",
]