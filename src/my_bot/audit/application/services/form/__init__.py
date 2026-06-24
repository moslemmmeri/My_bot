# my_bot_project/src/my_bot/application/services/form/__init__.py
"""
ماژول سرویس‌های فرم (Form Services).

این ماژول شامل سرویس‌های مربوط به مدیریت فرم‌های پویا در سیستم است:
- FormBuilderService: ساخت و مدیریت فرم‌ها
- FormSubmissionService: ثبت و پردازش پاسخ‌های فرم
- FormAnalyticsService: تحلیل و گزارش‌گیری از فرم‌ها
"""

from my_bot.application.services.form.form_builder import FormBuilderService
from my_bot.application.services.form.form_submission import FormSubmissionService
from my_bot.application.services.form.form_analytics import FormAnalyticsService

__all__ = [
    "FormBuilderService",
    "FormSubmissionService",
    "FormAnalyticsService",
]