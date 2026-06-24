# my_bot_project/src/my_bot/domain/interfaces/messaging/message_publisher.py
"""
اینترفیس انتشار پیام (Message Publisher Interface).

این اینترفیس قراردادهای لازم برای انتشار پیام‌ها در سیستم را تعریف می‌کند.
پیاده‌سازی این اینترفیس در لایه زیرساخت (Infrastructure) انجام می‌شود
و می‌تواند از سیستم‌های مختلفی مانند Redis Pub/Sub، RabbitMQ، Kafka یا
صرفاً یک سیستم ساده داخلی استفاده کند.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MessagePublisher(ABC):
    """
    اینترفیس انتشار پیام.

    این کلاس مسئولیت انتشار پیام‌ها (رویدادها، نوتیفیکیشن‌ها و ...)
    در سیستم را بر عهده دارد. تمام متدها به‌صورت async تعریف شده‌اند
    تا با معماری غیرهمگام پروژه سازگار باشند.
    """

    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Any,
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        انتشار یک پیام در یک تاپیک مشخص.

        Args:
            topic: نام تاپیک یا کانال برای انتشار.
            message: پیام برای انتشار (هر نوع قابل سریال‌سازی).
            key: کلید اختیاری برای پارتیشن‌بندی (در سیستم‌هایی مانند Kafka).
            headers: هدرهای اختیاری برای پیام.
        """
        pass

    @abstractmethod
    async def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        source: Optional[str] = None,
    ) -> None:
        """
        انتشار یک رویداد در سیستم.

        Args:
            event_type: نوع رویداد (مانند 'user.created', 'order.paid').
            event_data: داده‌های رویداد (دیکشنری).
            source: منبع رویداد (اختیاری، مانند نام سرویس یا کلاس).
        """
        pass

    @abstractmethod
    async def publish_notification(
        self,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        انتشار یک نوتیفیکیشن برای یک کاربر خاص.

        Args:
            user_id: شناسه کاربر مقصد.
            notification_type: نوع نوتیفیکیشن (مانند 'order_status', 'payment').
            data: داده‌های نوتیفیکیشن.
        """
        pass

    @abstractmethod
    async def publish_bulk(
        self,
        topic: str,
        messages: list[Any],
        keys: Optional[list[str]] = None,
    ) -> None:
        """
        انتشار چندین پیام به‌صورت یکجا (Bulk).

        Args:
            topic: نام تاپیک.
            messages: لیست پیام‌ها.
            keys: لیست کلیدهای اختیاری (به‌همان ترتیب پیام‌ها).
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس پیام‌رسانی.

        Returns:
            True اگر سرویس در دسترس باشد، در غیر این صورت False.
        """
        pass