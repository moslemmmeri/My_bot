# my_bot_project/src/my_bot/notifications/schedulers/reminder_scheduler.py
"""
زمان‌بندی یادآوری‌ها (Reminder Scheduler).

این کلاس مسئولیت بررسی و ارسال یادآوری‌های زمان‌بندی‌شده به کاربران را بر عهده دارد.
یادآوری‌ها می‌توانند برای موارد مختلف مانند پرداخت نشدن سفارش، عدم فعالیت کاربر،
یا رویدادهای خاص تنظیم شوند.
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


@dataclass
class Reminder:
    """
    تعریف یک یادآوری.

    Attributes:
        id: شناسه یکتای یادآوری (اختیاری).
        user_id: شناسه کاربر هدف.
        reminder_type: نوع یادآوری (مانند 'order_pending', 'inactivity', 'custom').
        scheduled_at: زمان برنامه‌ریزی‌شده برای ارسال.
        sent: آیا یادآوری ارسال شده است.
        data: داده‌های اضافی مرتبط با یادآوری (اختیاری).
        created_at: زمان ایجاد.
    """
    user_id: int
    reminder_type: str
    scheduled_at: datetime
    id: Optional[int] = None
    sent: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class ReminderScheduler:
    """
    زمان‌بندی و ارسال یادآوری‌ها.

    این کلاس با استفاده از یک حلقه‌ی پس‌زمینه، یادآوری‌های سررسیدشده را
    بررسی کرده و از طریق سرویس پیام‌رسان ارسال می‌کند.

    Attributes:
        user_repository: ریپازیتوری کاربر.
        order_repository: ریپازیتوری سفارش (برای یادآوری سفارشات).
        message_publisher: انتشاردهنده پیام برای ارسال نوتیفیکیشن.
        check_interval: بازه بررسی یادآوری‌ها بر حسب ثانیه (پیش‌فرض ۶۰).
        _reminders: لیست یادآوری‌های ثبت‌شده (در حافظه).
        _is_running: وضعیت اجرای حلقه.
        _task: تسک پس‌زمینه.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        order_repository: Optional[OrderRepository] = None,
        message_publisher: Optional[MessagePublisher] = None,
        check_interval: int = 60,
    ) -> None:
        """
        مقداردهی اولیه زمان‌بندی یادآوری‌ها.

        Args:
            user_repository: ریپازیتوری کاربر.
            order_repository: ریپازیتوری سفارش (اختیاری).
            message_publisher: انتشاردهنده پیام (اختیاری، در صورت عدم وجود از لاگ استفاده می‌شود).
            check_interval: بازه بررسی یادآوری‌ها بر حسب ثانیه.
        """
        self._user_repository = user_repository
        self._order_repository = order_repository
        self._message_publisher = message_publisher
        self._check_interval = check_interval
        self._reminders: List[Reminder] = []
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

        logger.info(
            f"ReminderScheduler initialized: check_interval={check_interval}s, "
            f"message_publisher={message_publisher is not None}"
        )

    def add_reminder(self, reminder: Reminder) -> None:
        """
        افزودن یک یادآوری جدید به لیست.

        Args:
            reminder: شیء یادآوری.
        """
        self._reminders.append(reminder)
        logger.debug(
            f"Reminder added: user_id={reminder.user_id}, "
            f"type={reminder.reminder_type}, scheduled={reminder.scheduled_at}"
        )

    def add_reminder_for_order(
        self,
        user_id: int,
        order_id: int,
        delay_minutes: int = 60,
    ) -> Reminder:
        """
        افزودن یادآوری برای سفارش در انتظار پرداخت.

        Args:
            user_id: شناسه کاربر.
            order_id: شناسه سفارش.
            delay_minutes: تأخیر پس از ایجاد سفارش برای ارسال یادآوری (پیش‌فرض ۶۰ دقیقه).

        Returns:
            Reminder: یادآوری ایجادشده.
        """
        scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
        reminder = Reminder(
            user_id=user_id,
            reminder_type="order_pending",
            scheduled_at=scheduled_at,
            data={"order_id": order_id},
        )
        self.add_reminder(reminder)
        return reminder

    def add_inactivity_reminder(
        self,
        user_id: int,
        days_inactive: int = 7,
    ) -> Reminder:
        """
        افزودن یادآوری برای کاربران غیرفعال.

        Args:
            user_id: شناسه کاربر.
            days_inactive: تعداد روزهای عدم فعالیت.

        Returns:
            Reminder: یادآوری ایجادشده.
        """
        scheduled_at = datetime.now() + timedelta(days=days_inactive)
        reminder = Reminder(
            user_id=user_id,
            reminder_type="inactivity",
            scheduled_at=scheduled_at,
            data={"days_inactive": days_inactive},
        )
        self.add_reminder(reminder)
        return reminder

    async def start(self) -> None:
        """
        شروع حلقه‌ی پس‌زمینه برای بررسی یادآوری‌ها.

        Raises:
            RuntimeError: اگر زمان‌بندی از قبل در حال اجرا باشد.
        """
        if self._is_running:
            raise RuntimeError("ReminderScheduler is already running.")

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ReminderScheduler started.")

    async def stop(self) -> None:
        """
        توقف حلقه‌ی پس‌زمینه.
        """
        if not self._is_running:
            logger.warning("ReminderScheduler is not running.")
            return

        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("ReminderScheduler stopped.")

    async def _run_loop(self) -> None:
        """
        حلقه اصلی بررسی یادآوری‌ها.

        این حلقه تا زمانی که `_is_running` True باشد، به‌طور مداوم
        یادآوری‌های سررسیدشده را بررسی و ارسال می‌کند.
        """
        while self._is_running:
            try:
                await self._check_and_send_reminders()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reminder scheduler loop: {e}")
                await asyncio.sleep(self._check_interval)

    async def _check_and_send_reminders(self) -> None:
        """
        بررسی و ارسال یادآوری‌های سررسیدشده.
        """
        now = datetime.now()
        due_reminders = [
            r for r in self._reminders
            if not r.sent and r.scheduled_at <= now
        ]

        if not due_reminders:
            return

        for reminder in due_reminders:
            try:
                await self._send_reminder(reminder)
                reminder.sent = True
                logger.info(
                    f"Reminder sent: user_id={reminder.user_id}, "
                    f"type={reminder.reminder_type}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to send reminder for user {reminder.user_id}: {e}"
                )

    async def _send_reminder(self, reminder: Reminder) -> None:
        """
        ارسال یک یادآوری به کاربر.

        Args:
            reminder: شیء یادآوری.

        Raises:
            ValidationError: اگر کاربر وجود نداشته باشد.
        """
        # دریافت کاربر
        user = await self._user_repository.get_by_id(reminder.user_id)
        if not user:
            raise ValidationError(
                message=f"User with id {reminder.user_id} not found.",
                context={"user_id": reminder.user_id},
            )

        # ساخت پیام بر اساس نوع یادآوری
        message = await self._build_reminder_message(user, reminder)

        # ارسال از طریق انتشاردهنده پیام
        if self._message_publisher:
            await self._message_publisher.publish_notification(
                user_id=user.id or 0,
                notification_type=f"reminder_{reminder.reminder_type}",
                data={
                    "message": message,
                    "reminder_type": reminder.reminder_type,
                    "reminder_data": reminder.data,
                },
            )
        else:
            # در صورت عدم وجود انتشاردهنده، فقط لاگ می‌کنیم
            logger.info(
                f"Reminder (no publisher): user={user.telegram_id}, "
                f"type={reminder.reminder_type}, message={message[:100]}..."
            )

    async def _build_reminder_message(self, user: User, reminder: Reminder) -> str:
        """
        ساخت متن پیام یادآوری بر اساس نوع.

        Args:
            user: کاربر هدف.
            reminder: شیء یادآوری.

        Returns:
            str: متن پیام.
        """
        greeting = MessagePool.get_random_greeting()
        user_name = user.full_name or "کاربر عزیز"

        if reminder.reminder_type == "order_pending":
            order_id = reminder.data.get("order_id")
            return (
                f"{greeting} {user_name} 👋\n\n"
                f"📌 **یادآوری سفارش**\n"
                f"سفارش شما با شناسه {order_id} هنوز تکمیل نشده است.\n"
                "لطفاً برای پرداخت و تکمیل سفارش اقدام کنید.\n\n"
                "💡 در صورت نیاز به کمک، با پشتیبانی تماس بگیرید."
            )

        elif reminder.reminder_type == "inactivity":
            days = reminder.data.get("days_inactive", 7)
            return (
                f"{greeting} {user_name} 👋\n\n"
                f"⏳ **یادآوری عدم فعالیت**\n"
                f"شما بیش از {days} روز است که از ربات استفاده نکرده‌اید.\n"
                "ما منتظر شما هستیم! برای مشاهده خدمات جدید، به ربات سر بزنید.\n\n"
                "🌟 با کلیک روی دکمه زیر به منوی اصلی بروید."
            )

        else:
            # پیام عمومی
            return (
                f"{greeting} {user_name} 👋\n\n"
                f"📌 **یادآوری**\n"
                f"این یک یادآوری از طرف ربات است.\n\n"
                "💡 برای مشاهده منوی اصلی، روی دکمه زیر کلیک کنید."
            )

    async def get_pending_reminders_count(self) -> int:
        """
        دریافت تعداد یادآوری‌های در انتظار ارسال.

        Returns:
            int: تعداد یادآوری‌های ارسال‌نشده.
        """
        return sum(1 for r in self._reminders if not r.sent)

    async def clear_sent_reminders(self) -> int:
        """
        پاک کردن یادآوری‌های ارسال‌شده از حافظه.

        Returns:
            int: تعداد یادآوری‌های حذف‌شده.
        """
        before = len(self._reminders)
        self._reminders = [r for r in self._reminders if not r.sent]
        removed = before - len(self._reminders)
        if removed:
            logger.info(f"Cleared {removed} sent reminders.")
        return removed

    async def get_reminders_for_user(self, user_id: int) -> List[Reminder]:
        """
        دریافت یادآوری‌های یک کاربر خاص.

        Args:
            user_id: شناسه کاربر.

        Returns:
            List[Reminder]: لیست یادآوری‌های کاربر.
        """
        return [r for r in self._reminders if r.user_id == user_id]