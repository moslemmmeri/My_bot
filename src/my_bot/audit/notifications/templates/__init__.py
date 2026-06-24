# my_bot_project/src/my_bot/notifications/templates/__init__.py
"""
ماژول قالب‌های نوتیفیکیشن (Notification Templates).

این ماژول شامل قالب‌های مختلف برای ساخت پیام‌های نوتیفیکیشن است:
- ReminderTemplate: قالب‌های یادآوری
- ReportTemplate: قالب‌های گزارش
"""

from my_bot.notifications.templates.reminder_template import ReminderTemplate
from my_bot.notifications.templates.report_template import ReportTemplate

__all__ = [
    "ReminderTemplate",
    "ReportTemplate",
]