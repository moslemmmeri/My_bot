# my_bot_project/src/my_bot/application/services/broadcast/broadcast_sender.py
"""
سرویس ارسال گروهی پیام (Broadcast Sender Service).

این سرویس مسئولیت ارسال پیام‌های گروهی به کاربران هدف را بر عهده دارد.
شامل عملیات‌های ارسال پیام، مدیریت وضعیت ارسال، محاسبه آمار
و مدیریت خطاهای ارسال است.
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime

from my_bot.application.dtos.broadcast_dto import (
    BroadcastCreateDTO,
    BroadcastResponseDTO,
    BroadcastFilterDTO,
)
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.not_found_errors import BroadcastNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.broadcast_errors import (
    BroadcastSendingError,
    BroadcastRateLimitError,
    BroadcastTargetError,
)
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.broadcast import Broadcast, BroadcastStatus, BroadcastType, BroadcastFilter
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.broadcast_repository import BroadcastRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class BroadcastSenderService:
    """
    سرویس ارسال گروهی پیام.

    این کلاس مسئولیت ارسال پیام‌های گروهی به کاربران هدف را بر عهده دارد.
    """

    def __init__(
        self,
        broadcast_repository: BroadcastRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
        telegram_sender: Optional[Callable[[int, str, Dict], Awaitable[bool]]] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس ارسال گروهی.

        Args:
            broadcast_repository: ریپازیتوری ارسال گروهی.
            user_repository: ریپازیتوری کاربر.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
            telegram_sender: تابع ارسال پیام به تلگرام (اختیاری).
        """
        self._broadcast_repository = broadcast_repository
        self._user_repository = user_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._telegram_sender = telegram_sender
        self._rate_limit_per_second = 5  # حداکثر ۵ پیام در ثانیه
        self._max_retry_count = 3

    async def create_broadcast(
        self,
        data: BroadcastCreateDTO,
        created_by: int,
    ) -> BroadcastResponseDTO:
        """
        ایجاد یک ارسال گروهی جدید.

        Args:
            data: اطلاعات ارسال گروهی (DTO).
            created_by: شناسه کاربر ایجادکننده (ادمین).

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی ایجادشده.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(created_by)
        if not user or not user.can_send_broadcast():
            raise PermissionDeniedError(
                message="شما مجاز به ارسال پیام گروهی نیستید.",
                context={"user_id": created_by},
            )

        # اعتبارسنجی محتوا
        if not data.content or not data.content.strip():
            raise ValidationError(
                message="محتوای پیام نمی‌تواند خالی باشد.",
                context={"created_by": created_by},
            )

        # ایجاد فیلتر
        broadcast_filter = BroadcastFilter(
            user_ids=data.filter.user_ids,
            roles=data.filter.roles,
            levels=data.filter.levels,
            min_points=data.filter.min_points,
            max_points=data.filter.max_points,
            is_active=data.filter.is_active,
            is_banned=data.filter.is_banned,
            created_after=data.filter.created_after,
            created_before=data.filter.created_before,
            last_activity_after=data.filter.last_activity_after,
            tags=data.filter.tags,
            exclude_user_ids=data.filter.exclude_user_ids,
        )

        # ایجاد موجودیت
        broadcast = Broadcast(
            title=data.title,
            content_type=BroadcastType(data.content_type),
            content=data.content,
            created_by=created_by,
            filter=broadcast_filter,
            media_url=data.media_url,
            media_group=data.media_group,
            caption=data.caption,
            keyboard=data.keyboard,
            priority=BroadcastPriority(data.priority) if data.priority else BroadcastPriority.NORMAL,
            scheduled_at=data.scheduled_at,
            is_draft=data.is_draft,
            metadata=data.metadata,
        )

        # ذخیره در دیتابیس
        saved_broadcast = await self._broadcast_repository.save(broadcast)

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="broadcast.created",
                event_data={
                    "broadcast_id": saved_broadcast.id,
                    "title": saved_broadcast.title,
                    "created_by": created_by,
                },
                source="BroadcastSenderService",
            )

        logger.info(f"Broadcast created: id={saved_broadcast.id}, title={saved_broadcast.title}")
        return BroadcastResponseDTO.from_entity(saved_broadcast)

    async def send_broadcast(
        self,
        broadcast_id: int,
        actor_id: Optional[int] = None,
    ) -> BroadcastResponseDTO:
        """
        ارسال یک پیام گروهی به کاربران هدف.

        Args:
            broadcast_id: شناسه ارسال گروهی.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
            BroadcastSendingError: در صورت بروز خطا در ارسال.
            BroadcastTargetError: اگر کاربران هدفی وجود نداشته باشند.
        """
        # دریافت ارسال گروهی
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        # بررسی قابلیت ارسال
        if not broadcast.can_send():
            raise BroadcastSendingError(
                broadcast_id=str(broadcast_id),
                target_count=0,
                failed_count=0,
                reason=f"Broadcast is in status: {broadcast.status.value}",
            )

        # اگر پیش‌نویس است، شروع به ارسال می‌کنیم
        if broadcast.status == BroadcastStatus.DRAFT:
            broadcast.start_sending()
            await self._broadcast_repository.save(broadcast)

        # دریافت کاربران هدف
        target_users = await self._get_target_users(broadcast)

        if not target_users:
            broadcast.status = BroadcastStatus.FAILED
            await self._broadcast_repository.save(broadcast)
            raise BroadcastTargetError(
                broadcast_id=str(broadcast_id),
                reason="هیچ کاربر هدفی برای ارسال یافت نشد.",
            )

        # ارسال پیام به کاربران
        try:
            result = await self._send_to_users(
                broadcast=broadcast,
                users=target_users,
                actor_id=actor_id,
            )

            # به‌روزرسانی وضعیت
            broadcast.mark_as_sent(
                total_count=result["total"],
                sent_count=result["sent"],
                failed_count=result["failed"],
                failed_user_ids=result["failed_user_ids"],
            )
            updated_broadcast = await self._broadcast_repository.save(broadcast)

            # انتشار رویداد اتمام ارسال
            if self._message_publisher:
                await self._message_publisher.publish_event(
                    event_type="broadcast.sent",
                    event_data={
                        "broadcast_id": updated_broadcast.id,
                        "title": updated_broadcast.title,
                        "total": result["total"],
                        "sent": result["sent"],
                        "failed": result["failed"],
                        "actor_id": actor_id,
                    },
                    source="BroadcastSenderService",
                )

            logger.info(
                f"Broadcast {broadcast_id} sent: "
                f"total={result['total']}, sent={result['sent']}, failed={result['failed']}"
            )

            return BroadcastResponseDTO.from_entity(updated_broadcast)

        except Exception as e:
            logger.error(f"Error sending broadcast {broadcast_id}: {e}")
            broadcast.status = BroadcastStatus.FAILED
            await self._broadcast_repository.save(broadcast)
            raise BroadcastSendingError(
                broadcast_id=str(broadcast_id),
                target_count=len(target_users),
                failed_count=0,
                reason=str(e),
            )

    async def send_scheduled_broadcasts(self) -> Dict[str, int]:
        """
        ارسال پیام‌های گروهی زمان‌بندی‌شده (برای اجرا توسط Scheduler).

        Returns:
            Dict[str, int]: آمار ارسال‌ها (total, sent, failed).
        """
        # دریافت ارسال‌های زمان‌بندی‌شده
        scheduled = await self._broadcast_repository.get_scheduled_broadcasts()
        total = len(scheduled)
        sent = 0
        failed = 0

        for broadcast in scheduled:
            try:
                await self.send_broadcast(broadcast.id or 0)
                sent += 1
            except Exception as e:
                logger.error(f"Failed to send scheduled broadcast {broadcast.id}: {e}")
                failed += 1

        return {"total": total, "sent": sent, "failed": failed}

    async def cancel_broadcast(
        self,
        broadcast_id: int,
        actor_id: int,
        reason: Optional[str] = None,
    ) -> BroadcastResponseDTO:
        """
        لغو یک ارسال گروهی.

        Args:
            broadcast_id: شناسه ارسال گروهی.
            actor_id: شناسه کاربر لغوکننده.
            reason: دلیل لغو (اختیاری).

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی لغو‌شده.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
            BroadcastSendingError: اگر ارسال گروهی قابل لغو نباشد.
        """
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        if not broadcast.can_cancel():
            raise BroadcastSendingError(
                broadcast_id=str(broadcast_id),
                target_count=0,
                failed_count=0,
                reason="Broadcast cannot be cancelled.",
            )

        broadcast.cancel(reason)
        updated_broadcast = await self._broadcast_repository.save(broadcast)

        logger.info(f"Broadcast {broadcast_id} cancelled by {actor_id}")
        return BroadcastResponseDTO.from_entity(updated_broadcast)

    async def get_broadcast_status(self, broadcast_id: int) -> Dict[str, Any]:
        """
        دریافت وضعیت یک ارسال گروهی.

        Args:
            broadcast_id: شناسه ارسال گروهی.

        Returns:
            Dict[str, Any]: وضعیت ارسال گروهی.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
        """
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        return {
            "id": broadcast.id,
            "title": broadcast.title,
            "status": broadcast.status.value,
            "total_count": broadcast.total_count,
            "sent_count": broadcast.sent_count,
            "failed_count": broadcast.failed_count,
            "progress": broadcast.progress_percentage(),
            "is_completed": broadcast.is_completed(),
            "is_pending": broadcast.is_pending(),
            "scheduled_at": broadcast.scheduled_at.isoformat() if broadcast.scheduled_at else None,
            "sent_at": broadcast.sent_at.isoformat() if broadcast.sent_at else None,
        }

    async def get_broadcast_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی ارسال‌های گروهی.

        Returns:
            Dict[str, Any]: آمار ارسال‌های گروهی.
        """
        stats = await self._broadcast_repository.get_statistics()
        return stats

    async def _get_target_users(self, broadcast: Broadcast) -> List[int]:
        """
        دریافت لیست کاربران هدف بر اساس فیلترها.

        Args:
            broadcast: موجودیت ارسال گروهی.

        Returns:
            List[int]: لیست شناسه‌های کاربران هدف.
        """
        filter_data = broadcast.filter
        target_user_ids = []

        # اگر کاربران مشخص شده‌اند
        if filter_data.user_ids:
            target_user_ids = filter_data.user_ids

        # دریافت کاربران بر اساس فیلترها
        users = await self._user_repository.get_all(limit=10000)

        for user in users:
            # اگر کاربر در لیست حذف است، رد می‌کنیم
            if filter_data.exclude_user_ids and user.id in filter_data.exclude_user_ids:
                continue

            # فیلتر بر اساس نقش
            if filter_data.roles and user.role.value not in filter_data.roles:
                continue

            # فیلتر بر اساس سطح
            if filter_data.levels and user.level.value not in filter_data.levels:
                continue

            # فیلتر بر اساس امتیاز
            if filter_data.min_points is not None and user.points < filter_data.min_points:
                continue
            if filter_data.max_points is not None and user.points > filter_data.max_points:
                continue

            # فیلتر بر اساس وضعیت فعال بودن
            if filter_data.is_active is not None and user.is_active != filter_data.is_active:
                continue

            # فیلتر بر اساس مسدود بودن
            if filter_data.is_banned is not None and user.is_banned != filter_data.is_banned:
                continue

            # فیلتر بر اساس تاریخ ایجاد
            if filter_data.created_after and user.created_at < filter_data.created_after:
                continue
            if filter_data.created_before and user.created_at > filter_data.created_before:
                continue

            # فیلتر بر اساس آخرین فعالیت
            if filter_data.last_activity_after:
                if not user.last_activity or user.last_activity < filter_data.last_activity_after:
                    continue

            # اگر کاربران خاصی مشخص نشده بودند، اضافه می‌کنیم
            if not filter_data.user_ids:
                if user.telegram_id:
                    target_user_ids.append(user.id)
            # اگر کاربران خاصی مشخص شده بودند، فقط آنها را اضافه می‌کنیم
            elif filter_data.user_ids and user.id in filter_data.user_ids:
                target_user_ids.append(user.id)

        # حذف تکراری‌ها
        return list(set(target_user_ids))

    async def _send_to_users(
        self,
        broadcast: Broadcast,
        users: List[int],
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        ارسال پیام به لیست کاربران با مدیریت نرخ و Retry.

        Args:
            broadcast: موجودیت ارسال گروهی.
            users: لیست شناسه‌های کاربران.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Dict[str, Any]: آمار ارسال.
        """
        total = len(users)
        sent_count = 0
        failed_count = 0
        failed_user_ids = []

        # محدودیت نرخ ارسال
        semaphore = asyncio.Semaphore(self._rate_limit_per_second)
        delay = 1.0 / self._rate_limit_per_second

        async def send_to_user(user_id: int) -> bool:
            async with semaphore:
                # ارسال پیام به کاربر
                success = await self._send_single_message(broadcast, user_id)
                if success:
                    return True
                else:
                    # تلاش مجدد
                    for retry in range(self._max_retry_count - 1):
                        await asyncio.sleep(delay * (retry + 1))
                        success = await self._send_single_message(broadcast, user_id)
                        if success:
                            return True
                    return False

        # ارسال به تمام کاربران
        tasks = [send_to_user(user_id) for user_id in users]
        results = await asyncio.gather(*tasks)

        for i, success in enumerate(results):
            if success:
                sent_count += 1
            else:
                failed_count += 1
                failed_user_ids.append(users[i])

        return {
            "total": total,
            "sent": sent_count,
            "failed": failed_count,
            "failed_user_ids": failed_user_ids,
        }

    async def _send_single_message(
        self,
        broadcast: Broadcast,
        user_id: int,
    ) -> bool:
        """
        ارسال یک پیام به یک کاربر خاص.

        Args:
            broadcast: موجودیت ارسال گروهی.
            user_id: شناسه کاربر.

        Returns:
            bool: True در صورت ارسال موفق.
        """
        # دریافت کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user or not user.telegram_id:
            return False

        try:
            # ارسال از طریق تابع ارسال تلگرام (در صورت وجود)
            if self._telegram_sender:
                success = await self._telegram_sender(
                    user.telegram_id,
                    broadcast.content,
                    {
                        "caption": broadcast.caption,
                        "media_url": broadcast.media_url,
                        "media_group": broadcast.media_group,
                        "keyboard": broadcast.keyboard,
                    },
                )
                if success:
                    return True

            # در غیر این صورت، از طریق انتشاردهنده پیام
            if self._message_publisher:
                await self._message_publisher.publish_notification(
                    user_id=user_id,
                    notification_type="broadcast",
                    data={
                        "content": broadcast.content,
                        "caption": broadcast.caption,
                        "media_url": broadcast.media_url,
                        "media_group": broadcast.media_group,
                        "keyboard": broadcast.keyboard,
                    },
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            return False

    async def get_broadcast_history(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[BroadcastStatus] = None,
    ) -> List[BroadcastResponseDTO]:
        """
        دریافت تاریخچه ارسال‌های گروهی.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            List[BroadcastResponseDTO]: لیست ارسال‌های گروهی.
        """
        broadcasts = await self._broadcast_repository.get_all(
            skip=skip,
            limit=limit,
            status=status,
            order_by="created_at",
            order_desc=True,
        )
        return [BroadcastResponseDTO.from_entity(b) for b in broadcasts]

    async def get_broadcast_by_id(
        self,
        broadcast_id: int,
    ) -> BroadcastResponseDTO:
        """
        دریافت اطلاعات یک ارسال گروهی با شناسه.

        Args:
            broadcast_id: شناسه ارسال گروهی.

        Returns:
            BroadcastResponseDTO: اطلاعات ارسال گروهی.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
        """
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))
        return BroadcastResponseDTO.from_entity(broadcast)

    async def delete_broadcast(
        self,
        broadcast_id: int,
        deleted_by: int,
    ) -> bool:
        """
        حذف یک ارسال گروهی.

        Args:
            broadcast_id: شناسه ارسال گروهی.
            deleted_by: شناسه کاربر حذف‌کننده.

        Returns:
            bool: True در صورت حذف موفق.

        Raises:
            BroadcastNotFoundError: اگر ارسال گروهی وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        broadcast = await self._broadcast_repository.get_by_id(broadcast_id)
        if not broadcast:
            raise BroadcastNotFoundError(broadcast_id=str(broadcast_id))

        # بررسی دسترسی
        if broadcast.created_by != deleted_by:
            user = await self._user_repository.get_by_id(deleted_by)
            if not user or not user.can_manage_settings():
                raise PermissionDeniedError(
                    message="شما مجاز به حذف این ارسال گروهی نیستید.",
                    context={"broadcast_id": broadcast_id, "deleted_by": deleted_by},
                )

        result = await self._broadcast_repository.delete(broadcast_id)
        logger.info(f"Broadcast {broadcast_id} deleted by {deleted_by}")
        return result