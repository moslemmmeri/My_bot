# my_bot_project/src/my_bot/application/services/analytics/__init__.py
"""
ماژول سرویس‌های تحلیل داده (Analytics Services).

این ماژول شامل سرویس‌های مربوط به تحلیل داده‌ها و گزارش‌گیری در سیستم است:
- UserBehaviorAnalyticsService: تحلیل رفتار کاربران
- OrderStatisticsService: آمار و تحلیل سفارشات
- ABTestingService: مدیریت و تحلیل تست‌های A/B
"""

from my_bot.application.services.analytics.user_behavior import UserBehaviorAnalyticsService
from my_bot.application.services.analytics.order_statistics import OrderStatisticsService
from my_bot.application.services.analytics.ab_testing import ABTestingService

__all__ = [
    "UserBehaviorAnalyticsService",
    "OrderStatisticsService",
    "ABTestingService",
]