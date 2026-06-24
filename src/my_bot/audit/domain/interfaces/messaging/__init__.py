# my_bot_project/src/my_bot/domain/interfaces/messaging/__init__.py
"""
ماژول اینترفیس‌های پیام‌رسانی (Messaging Interfaces).

این ماژول شامل اینترفیس‌های مربوط به انتشار پیام‌ها و ارتباطات
ناهمگام در سیستم است.
"""

from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher

__all__ = [
    "MessagePublisher",
]