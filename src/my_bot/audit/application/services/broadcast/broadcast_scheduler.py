# my_bot_project/src/my_bot/application/services/broadcast/broadcast_scheduler.py
"""
سرویس زمان‌بندی ارسال گروهی (Broadcast Scheduler Service).

این سرویس مسئولیت زمان‌بندی، مدیریت و اجرای ارسال‌های گروهی زمان‌بندی‌شده
را بر عهده دارد. شامل عملیات‌های زمان‌بندی، لغو زمان‌بندی،
بررسی کارهای زمان‌بندی‌شده و دریافت وضعیت است.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from my_bot.application.dtos.broadcast_dto import BroadcastResponseDTO
from my_bot.application.services.broadcast.broadcast_sender import BroadcastSenderService
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.not_found_errors import BroadcastNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.broadcast_errors import (
    BroadcastScheduleError,
    BroadcastCancelError,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.broadcast import Broadcast, BroadcastStatus
from my_bot.domain.interfaces.repositories.broadcast_repository import BroadcastRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class BroadcastSchedulerService:
    """
    سرویس زمان‌بندی ارسال گروهی.

    این کلاس مسئولیت زمان‌بندی، مدیریت و اجرای ارسال‌های گروهی
    زمان‌بندی‌شده را بر عهده دارد.
    """

    def __init__(
        self,
        broadcast_repository: BroadcastRepository,
        broadcast_sender: BroadcastSenderService,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس زمان‌بندی.

        Args:
            broadcast_repository: ریپازیتوری ارسال گروهی.
            broadcast_sender: سرویس ارسال گروهی.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._broadcast_repository = broadcast_repository
        self._broadcast_sender = broadcast_sender
        self._message_publisher = message_publisher
        self._cache = cache
        self._check_interval_seconds = 60  # بررسی هر ۶۰ ثانیه
        self._is_running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def schedule_broadcast(
        self,
        broadcast_id: int,
        scheduled_at: datetime,
        actor_id: Optional[int] = None,
    ) -> BroadcastResponseDTO:
        """
        زمان‌بندی یک ارسال گروهی برای زمان مشخص.

        Args:
            broadcast_id: شناسه ارسال گروهی.
            scheduled_at: زمان ارسال.
            actor_id: شناسه کاربر زمان‌بندی‌کننده (اختیاری).

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی زمان‌بندی‌شده.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
            BroadcastScheduleError: در صورت بروز خطا در زمان‌بندی.
            ValidationError: اگر زمان نامعتبر باشد.
        """
        # دریافت ارسال گروهی
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        # بررسی وضعیت
        if broadcast.status not in (BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED):
            raise BroadcastScheduleError(
                broadcast_id=str(broadcast_id),
                scheduled_time=scheduled_at.isoformat(),
                reason=f"Broadcast is in status: {broadcast.status.value}",
            )

        # اعتبارسنجی زمان
        if scheduled_at <= datetime.now():
            raise ValidationError(
                message="زمان ارسال باید در آینده باشد.",
                context={"broadcast_id": broadcast_id, "scheduled_at": scheduled_at.isoformat()},
            )

        # زمان‌بندی
        broadcast.schedule(scheduled_at)
        updated_broadcast = await self._broadcast_repository.save(broadcast)

        # ذخیره در کش (برای دسترسی سریع)
        if self._cache:
            await self._cache.set(
                f"broadcast_scheduled:{broadcast_id}",
                {
                    "broadcast_id": broadcast_id,
                    "scheduled_at": scheduled_at.isoformat(),
                    "title": broadcast.title,
                },
                ttl=self._check_interval_seconds * 10,
            )

        # انتشار رویداد زمان‌بندی
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="broadcast.scheduled",
                event_data={
                    "broadcast_id": broadcast_id,
                    "title": broadcast.title,
                    "scheduled_at": scheduled_at.isoformat(),
                    "actor_id": actor_id,
                },
                source="BroadcastSchedulerService",
            )

        logger.info(
            f"Broadcast {broadcast_id} scheduled at {scheduled_at.isoformat()} "
            f"by {actor_id}"
        )
        return BroadcastResponseDTO.from_entity(updated_broadcast)

    async def cancel_scheduled_broadcast(
        self,
        broadcast_id: int,
        actor_id: int,
        reason: Optional[str] = None,
    ) -> BroadcastResponseDTO:
        """
        لغو زمان‌بندی یک ارسال گروهی (بازگشت به وضعیت پیش‌نویس).

        Args:
            broadcast_id: شناسه ارسال گروهی.
            actor_id: شناسه کاربر لغوکننده.
            reason: دلیل لغو (اختیاری).

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی لغو‌شده.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
            BroadcastCancelError: در صورت بروز خطا در لغو زمان‌بندی.
        """
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        # بررسی وضعیت
        if broadcast.status != BroadcastStatus.SCHEDULED:
            raise BroadcastCancelError(
                broadcast_id=str(broadcast_id),
                status=broadcast.status.value,
                reason="Only scheduled broadcasts can be cancelled.",
            )

        # لغو زمان‌بندی (بازگشت به وضعیت DRAFT)
        broadcast.status = BroadcastStatus.DRAFT
        broadcast.scheduled_at = None
        broadcast.is_draft = True
        broadcast.updated_at = datetime.now()
        if reason:
            broadcast.metadata["cancel_reason"] = reason
        updated_broadcast = await self._broadcast_repository.save(broadcast)

        # حذف از کش
        if self._cache:
            await self._cache.delete(f"broadcast_scheduled:{broadcast_id}")

        # انتشار رویداد لغو زمان‌بندی
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="broadcast.schedule_cancelled",
                event_data={
                    "broadcast_id": broadcast_id,
                    "title": broadcast.title,
                    "actor_id": actor_id,
                    "reason": reason,
                },
                source="BroadcastSchedulerService",
            )

        logger.info(f"Broadcast {broadcast_id} schedule cancelled by {actor_id}")
        return BroadcastResponseDTO.from_entity(updated_broadcast)

    async def get_scheduled_broadcasts(
        self,
        skip: int = 0,
        limit: int = 100,
        include_past: bool = False,
    ) -> List[BroadcastResponseDTO]:
        """
        دریافت لیست ارسال‌های گروهی زمان‌بندی‌شده.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            include_past: شامل زمان‌بندی‌های گذشته (پیش‌فرض False).

        Returns:
            List[BroadcastResponseDTO]: لیست ارسال‌های زمان‌بندی‌شده.
        """
        scheduled = await self._broadcast_repository.get_scheduled_broadcasts()

        # فیلتر بر اساس زمان
        now = datetime.now()
        filtered = []
        for broadcast in scheduled:
            if not include_past and broadcast.scheduled_at and broadcast.scheduled_at < now:
                continue
            filtered.append(broadcast)

        # صفحه‌بندی
        filtered = filtered[skip:skip + limit]

        return [BroadcastResponseDTO.from_entity(b) for b in filtered]

    async def get_upcoming_broadcasts(
        self,
        limit: int = 10,
    ) -> List[BroadcastResponseDTO]:
        """
        دریافت ارسال‌های گروهی زمان‌بندی‌شده در آینده نزدیک.

        Args:
            limit: حداکثر تعداد ارسال‌ها.

        Returns:
            List[BroadcastResponseDTO]: لیست ارسال‌های آینده.
        """
        now = datetime.now()
        scheduled = await self._broadcast_repository.get_scheduled_broadcasts()

        # فیلتر کردن زمان‌بندی‌های آینده و مرتب‌سازی
        upcoming = [
            b for b in scheduled
            if b.scheduled_at and b.scheduled_at > now
        ]
        upcoming.sort(key=lambda b: b.scheduled_at or datetime.max)
        upcoming = upcoming[:limit]

        return [BroadcastResponseDTO.from_entity(b) for b in upcoming]

    async def get_schedule_status(self, broadcast_id: int) -> Dict[str, Any]:
        """
        دریافت وضعیت زمان‌بندی یک ارسال گروهی.

        Args:
            broadcast_id: شناسه ارسال گروهی.

        Returns:
            Dict[str, Any]: وضعیت زمان‌بندی.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
        """
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        now = datetime.now()
        is_scheduled = broadcast.status == BroadcastStatus.SCHEDULED
        is_past = False
        time_remaining = None

        if is_scheduled and broadcast.scheduled_at:
            is_past = broadcast.scheduled_at < now
            if not is_past:
                time_remaining = (broadcast.scheduled_at - now).total_seconds()

        return {
            "broadcast_id": broadcast_id,
            "title": broadcast.title,
            "status": broadcast.status.value,
            "is_scheduled": is_scheduled,
            "scheduled_at": broadcast.scheduled_at.isoformat() if broadcast.scheduled_at else None,
            "is_past": is_past,
            "time_remaining_seconds": time_remaining,
            "estimated_execution": broadcast.scheduled_at.isoformat() if broadcast.scheduled_at else None,
        }

    async def start_scheduler(self) -> None:
        """
        شروع سرویس زمان‌بندی (اجرای پس‌زمینه).

        این متد یک تسک پس‌زمینه برای بررسی و اجرای ارسال‌های زمان‌بندی‌شده
        راه‌اندازی می‌کند.
        """
        if self._is_running:
            logger.warning("Scheduler is already running.")
            return

        self._is_running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler_loop())
        logger.info("Broadcast scheduler started.")

    async def stop_scheduler(self) -> None:
        """
        توقف سرویس زمان‌بندی.

        این متد تسک پس‌زمینه را متوقف می‌کند.
        """
        if not self._is_running:
            logger.warning("Scheduler is not running.")
            return

        self._is_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None

        logger.info("Broadcast scheduler stopped.")

    async def _run_scheduler_loop(self) -> None:
        """
        حلقه اصلی سرویس زمان‌بندی.

        این متد به‌طور مداوم زمان‌بندی‌ها را بررسی و ارسال‌های
        زمان‌بندی‌شده را اجرا می‌کند.
        """
        while self._is_running:
            try:
                await self._check_and_execute_scheduled_broadcasts()
                await asyncio.sleep(self._check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self._check_interval_seconds)

    async def _check_and_execute_scheduled_broadcasts(self) -> None:
        """
        بررسی و اجرای ارسال‌های زمان‌بندی‌شده.

        این متد زمان‌بندی‌های فعلی را بررسی می‌کند و ارسال‌هایی که
        زمان آنها رسیده را اجرا می‌کند.
        """
        try:
            # دریافت ارسال‌های زمان‌بندی‌شده
            scheduled = await self._broadcast_repository.get_scheduled_broadcasts()

            now = datetime.now()
            executed = 0
            failed = 0

            for broadcast in scheduled:
                if not broadcast.scheduled_at:
                    continue

                # اگر زمان ارسال رسیده یا گذشته است
                if broadcast.scheduled_at <= now:
                    try:
                        # ارسال پیام گروهی
                        await self._broadcast_sender.send_broadcast(
                            broadcast_id=broadcast.id or 0,
                            actor_id=None,
                        )
                        executed += 1
                        logger.info(f"Scheduled broadcast {broadcast.id} executed.")
                    except Exception as e:
                        failed += 1
                        logger.error(f"Failed to execute scheduled broadcast {broadcast.id}: {e}")

            if executed > 0 or failed > 0:
                logger.info(
                    f"Scheduler executed {executed} broadcasts, failed {failed}."
                )

        except Exception as e:
            logger.error(f"Error checking scheduled broadcasts: {e}")

    async def get_next_scheduled_time(self) -> Optional[datetime]:
        """
        دریافت زمان ارسال بعدی (نزدیک‌ترین زمان‌بندی).

        Returns:
            Optional[datetime]: زمان ارسال بعدی یا None در صورت عدم وجود.
        """
        upcoming = await self.get_upcoming_broadcasts(limit=1)
        if upcoming and upcoming[0].scheduled_at:
            return upcoming[0].scheduled_at
        return None

    async def get_scheduled_count(self) -> int:
        """
        دریافت تعداد ارسال‌های زمان‌بندی‌شده.

        Returns:
            int: تعداد ارسال‌های زمان‌بندی‌شده.
        """
        scheduled = await self._broadcast_repository.get_scheduled_broadcasts()
        now = datetime.now()
        return sum(1 for b in scheduled if b.scheduled_at and b.scheduled_at > now)

    async def reschedule_broadcast(
        self,
        broadcast_id: int,
        new_scheduled_at: datetime,
        actor_id: Optional[int] = None,
    ) -> BroadcastResponseDTO:
        """
        تغییر زمان ارسال یک ارسال گروهی زمان‌بندی‌شده.

        Args:
            broadcast_id: شناسه ارسال گروهی.
            new_scheduled_at: زمان جدید.
            actor_id: شناسه کاربر تغییردهنده (اختیاری).

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی به‌روزرسانی‌شده.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
            ValidationError: اگر زمان نامعتبر باشد.
        """
        # دریافت ارسال گروهی
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        # بررسی وضعیت
        if broadcast.status != BroadcastStatus.SCHEDULED:
            raise ValidationError(
                message="فقط ارسال‌های گروهی زمان‌بندی‌شده قابل تغییر زمان هستند.",
                context={"broadcast_id": broadcast_id, "status": broadcast.status.value},
            )

        # اعتبارسنجی زمان جدید
        if new_scheduled_at <= datetime.now():
            raise ValidationError(
                message="زمان جدید باید در آینده باشد.",
                context={"broadcast_id": broadcast_id, "scheduled_at": new_scheduled_at.isoformat()},
            )

        # به‌روزرسانی زمان
        old_time = broadcast.scheduled_at
        broadcast.scheduled_at = new_scheduled_at
        broadcast.updated_at = datetime.now()
        if actor_id:
            broadcast.metadata["rescheduled_by"] = actor_id
            broadcast.metadata["old_scheduled_at"] = old_time.isoformat() if old_time else None

        updated_broadcast = await self._broadcast_repository.save(broadcast)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"broadcast_scheduled:{broadcast_id}",
                {
                    "broadcast_id": broadcast_id,
                    "scheduled_at": new_scheduled_at.isoformat(),
                    "title": broadcast.title,
                },
                ttl=self._check_interval_seconds * 10,
            )

        # انتشار رویداد تغییر زمان‌بندی
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="broadcast.rescheduled",
                event_data={
                    "broadcast_id": broadcast_id,
                    "title": broadcast.title,
                    "old_time": old_time.isoformat() if old_time else None,
                    "new_time": new_scheduled_at.isoformat(),
                    "actor_id": actor_id,
                },
                source="BroadcastSchedulerService",
            )

        logger.info(
            f"Broadcast {broadcast_id} rescheduled from {old_time} "
            f"to {new_scheduled_at} by {actor_id}"
        )
        return BroadcastResponseDTO.from_entity(updated_broadcast)

    async def get_schedule_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار زمان‌بندی ارسال‌های گروهی.

        Returns:
            Dict[str, Any]: آمار زمان‌بندی.
        """
        scheduled = await self._broadcast_repository.get_scheduled_broadcasts()
        now = datetime.now()

        total = len(scheduled)
        upcoming = sum(1 for b in scheduled if b.scheduled_at and b.scheduled_at > now)
        past = sum(1 for b in scheduled if b.scheduled_at and b.scheduled_at <= now)

        # زمان‌بندی‌های امروز، این هفته، این ماه
        today = now.date()
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1)

        today_count = sum(
            1 for b in scheduled
            if b.scheduled_at and b.scheduled_at.date() == today
        )
        week_count = sum(
            1 for b in scheduled
            if b.scheduled_at and b.scheduled_at >= week_start
        )
        month_count = sum(
            1 for b in scheduled
            if b.scheduled_at and b.scheduled_at >= month_start
        )

        return {
            "total_scheduled": total,
            "upcoming": upcoming,
            "past": past,
            "today": today_count,
            "this_week": week_count,
            "this_month": month_count,
            "next_time": await self.get_next_scheduled_time(),
        }

    async def clear_cache(self) -> None:
        """
        پاک کردن کش زمان‌بندی.
        """
        if self._cache:
            await self._cache.delete_pattern("broadcast_scheduled:*")
            logger.info("Broadcast scheduler cache cleared.")