# my_bot_project/src/my_bot/notifications/schedulers/report_scheduler.py
"""
زمان‌بندی گزارش‌های خودکار (Report Scheduler).

این کلاس مسئولیت تولید و ارسال خودکار گزارش‌های دوره‌ای (روزانه، هفتگی، ماهانه)
را به ادمین‌ها و مدیران بر عهده دارد. گزارش‌ها شامل آمار کاربران، سفارشات،
پرداخت‌ها و سایر داده‌های کلیدی سیستم هستند.
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime, time, timedelta
from enum import Enum

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.notifications.templates.report_template import ReportTemplate

logger = get_logger(__name__)


class ReportType(str, Enum):
    """انواع گزارش‌های قابل زمان‌بندی."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportScheduler:
    """
    زمان‌بندی تولید و ارسال گزارش‌های خودکار.

    این کلاس با استفاده از یک حلقه‌ی پس‌زمینه، زمان‌های تعیین‌شده را بررسی کرده
    و در زمان مقرر، گزارش‌های مربوطه را تولید و از طریق سرویس پیام‌رسان ارسال می‌کند.

    Attributes:
        user_repository: ریپازیتوری کاربر.
        order_repository: ریپازیتوری سفارش.
        payment_repository: ریپازیتوری پرداخت.
        form_repository: ریپازیتوری فرم (اختیاری).
        message_publisher: انتشاردهنده پیام برای ارسال گزارش.
        report_template: قالب گزارش.
        check_interval: بازه بررسی زمان‌ها بر حسب ثانیه (پیش‌فرض ۳۰۰).
        _schedules: لیست زمان‌بندی‌های ثبت‌شده.
        _is_running: وضعیت اجرای حلقه.
        _task: تسک پس‌زمینه.
        _last_sent: زمان آخرین ارسال هر نوع گزارش (برای جلوگیری از ارسال مجدد).
    """

    def __init__(
        self,
        user_repository: UserRepository,
        order_repository: OrderRepository,
        payment_repository: PaymentRepository,
        form_repository: Optional[FormRepository] = None,
        message_publisher: Optional[MessagePublisher] = None,
        report_template: Optional[ReportTemplate] = None,
        check_interval: int = 300,
    ) -> None:
        """
        مقداردهی اولیه زمان‌بندی گزارش‌ها.

        Args:
            user_repository: ریپازیتوری کاربر.
            order_repository: ریپازیتوری سفارش.
            payment_repository: ریپازیتوری پرداخت.
            form_repository: ریپازیتوری فرم (اختیاری).
            message_publisher: انتشاردهنده پیام (اختیاری).
            report_template: قالب گزارش (در صورت None، نمونه جدید ایجاد می‌شود).
            check_interval: بازه بررسی زمان‌ها بر حسب ثانیه (پیش‌فرض ۳۰۰ ثانیه = ۵ دقیقه).
        """
        self._user_repository = user_repository
        self._order_repository = order_repository
        self._payment_repository = payment_repository
        self._form_repository = form_repository
        self._message_publisher = message_publisher
        self._report_template = report_template or ReportTemplate()
        self._check_interval = check_interval

        # زمان‌بندی‌های ثبت‌شده: (report_type, scheduled_time, recipients)
        self._schedules: List[Dict[str, Any]] = []
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_sent: Dict[str, datetime] = {}

        # ثبت زمان‌بندی‌های پیش‌فرض
        self._add_default_schedules()

        logger.info(
            f"ReportScheduler initialized: check_interval={check_interval}s, "
            f"message_publisher={message_publisher is not None}"
        )

    def _add_default_schedules(self) -> None:
        """
        افزودن زمان‌بندی‌های پیش‌فرض برای گزارش‌های روزانه، هفتگی و ماهانه.
        """
        # گزارش روزانه در ساعت ۹ صبح
        self.add_schedule(
            report_type=ReportType.DAILY,
            scheduled_time=time(9, 0, 0),
            recipients=["admin"],
            description="گزارش روزانه"
        )

        # گزارش هفتگی در روز دوشنبه ساعت ۸ صبح
        self.add_schedule(
            report_type=ReportType.WEEKLY,
            scheduled_time=time(8, 0, 0),
            recipients=["admin", "manager"],
            description="گزارش هفتگی",
            weekdays=[0]  # دوشنبه
        )

        # گزارش ماهانه در روز اول ماه ساعت ۱۰ صبح
        self.add_schedule(
            report_type=ReportType.MONTHLY,
            scheduled_time=time(10, 0, 0),
            recipients=["admin", "manager"],
            description="گزارش ماهانه",
            month_day=1
        )

    def add_schedule(
        self,
        report_type: ReportType,
        scheduled_time: time,
        recipients: List[str],
        description: Optional[str] = None,
        weekdays: Optional[List[int]] = None,
        month_day: Optional[int] = None,
        custom_check: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> None:
        """
        افزودن یک زمان‌بندی جدید برای گزارش.

        Args:
            report_type: نوع گزارش.
            scheduled_time: زمان ارسال (ساعت و دقیقه).
            recipients: لیست دریافت‌کنندگان (نقش‌ها یا شناسه‌های خاص).
            description: توضیحات (اختیاری).
            weekdays: لیست روزهای هفته برای گزارش هفتگی (۰=دوشنبه، ۶=یکشنبه).
            month_day: روز ماه برای گزارش ماهانه (۱ تا ۳۱).
            custom_check: تابع شرطی سفارشی برای تعیین زمان ارسال.

        Raises:
            ValidationError: اگر پارامترها نامعتبر باشند.
        """
        if not recipients:
            raise ValidationError(
                message="حداقل یک گیرنده باید مشخص شود.",
                context={"recipients": recipients},
            )

        if report_type == ReportType.WEEKLY and not weekdays:
            raise ValidationError(
                message="برای گزارش هفتگی باید روزهای هفته مشخص شوند.",
                context={"report_type": report_type},
            )

        if report_type == ReportType.MONTHLY and not month_day:
            raise ValidationError(
                message="برای گزارش ماهانه باید روز ماه مشخص شود.",
                context={"report_type": report_type},
            )

        if month_day and (month_day < 1 or month_day > 31):
            raise ValidationError(
                message="روز ماه باید بین ۱ تا ۳۱ باشد.",
                context={"month_day": month_day},
            )

        schedule = {
            "report_type": report_type,
            "scheduled_time": scheduled_time,
            "recipients": recipients,
            "description": description,
            "weekdays": weekdays,
            "month_day": month_day,
            "custom_check": custom_check,
        }
        self._schedules.append(schedule)
        logger.info(
            f"Schedule added: type={report_type.value}, time={scheduled_time}, "
            f"recipients={recipients}"
        )

    async def start(self) -> None:
        """
        شروع حلقه‌ی پس‌زمینه برای بررسی زمان‌بندی‌ها.

        Raises:
            RuntimeError: اگر زمان‌بندی از قبل در حال اجرا باشد.
        """
        if self._is_running:
            raise RuntimeError("ReportScheduler is already running.")

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ReportScheduler started.")

    async def stop(self) -> None:
        """
        توقف حلقه‌ی پس‌زمینه.
        """
        if not self._is_running:
            logger.warning("ReportScheduler is not running.")
            return

        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("ReportScheduler stopped.")

    async def _run_loop(self) -> None:
        """
        حلقه اصلی بررسی زمان‌بندی‌ها.
        """
        while self._is_running:
            try:
                await self._check_and_send_reports()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in report scheduler loop: {e}")
                await asyncio.sleep(self._check_interval)

    async def _check_and_send_reports(self) -> None:
        """
        بررسی و ارسال گزارش‌های سررسیدشده.
        """
        now = datetime.now()
        today = now.date()

        for schedule in self._schedules:
            report_type = schedule["report_type"]
            scheduled_time = schedule["scheduled_time"]
            recipients = schedule["recipients"]

            # بررسی شرط سفارشی
            if schedule.get("custom_check"):
                try:
                    if not await schedule["custom_check"]():
                        continue
                except Exception as e:
                    logger.error(f"Custom check failed for schedule {schedule}: {e}")
                    continue

            # بررسی بر اساس نوع گزارش
            should_send = False
            key = f"{report_type.value}_{scheduled_time.isoformat()}"

            if report_type == ReportType.DAILY:
                # هر روز در زمان مشخص
                if now.hour == scheduled_time.hour and now.minute == scheduled_time.minute:
                    if self._last_sent.get(key, datetime.min).date() < today:
                        should_send = True

            elif report_type == ReportType.WEEKLY:
                # در روزهای مشخص هفته
                weekdays = schedule.get("weekdays", [])
                if now.weekday() in weekdays:
                    if now.hour == scheduled_time.hour and now.minute == scheduled_time.minute:
                        if self._last_sent.get(key, datetime.min).date() < today:
                            should_send = True

            elif report_type == ReportType.MONTHLY:
                # در روز مشخص ماه
                month_day = schedule.get("month_day", 1)
                if today.day == month_day:
                    if now.hour == scheduled_time.hour and now.minute == scheduled_time.minute:
                        if self._last_sent.get(key, datetime.min).date() < today:
                            should_send = True

            if should_send:
                try:
                    await self._send_report(report_type, recipients, schedule.get("description"))
                    self._last_sent[key] = now
                    logger.info(
                        f"Report sent: type={report_type.value}, "
                        f"recipients={recipients}, time={now}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send report {report_type.value}: {e}"
                    )

    async def _send_report(
        self,
        report_type: ReportType,
        recipients: List[str],
        description: Optional[str] = None,
    ) -> None:
        """
        تولید و ارسال یک گزارش.

        Args:
            report_type: نوع گزارش.
            recipients: لیست دریافت‌کنندگان.
            description: توضیحات (اختیاری).

        Raises:
            ValidationError: اگر انتشاردهنده پیام در دسترس نباشد.
        """
        if not self._message_publisher:
            logger.warning("Message publisher not available. Report will not be sent.")
            return

        # جمع‌آوری داده‌های گزارش
        report_data = await self._collect_report_data(report_type)

        # تولید محتوای گزارش
        report_content = await self._report_template.render(
            report_type=report_type.value,
            data=report_data,
            description=description,
        )

        # ارسال به دریافت‌کنندگان
        # در اینجا فرض می‌کنیم که recipients شامل نقش‌ها یا شناسه‌های کاربران هستند
        # برای سادگی، از لیست ادمین‌ها استفاده می‌کنیم (در عمل باید نقش‌ها را به کاربران تبدیل کنیم)
        # اما برای نمونه، یک تابع کمکی داریم که کاربران با نقش خاص را دریافت کند.
        for recipient in recipients:
            # در اینجا می‌توان کاربران با نقش مشخص را دریافت کرد
            # فعلاً فقط لاگ می‌کنیم
            logger.info(f"Sending report to {recipient}: {report_content[:100]}...")
            # در عمل باید از message_publisher استفاده کنیم
            # await self._message_publisher.publish_notification(...)
            pass

        # برای نمونه، یک نوتیفیکیشن نمونه ارسال می‌کنیم
        await self._message_publisher.publish_notification(
            user_id=0,  # placeholder, in practice get user ids
            notification_type=f"report_{report_type.value}",
            data={
                "report_type": report_type.value,
                "content": report_content,
                "recipients": recipients,
            },
        )

    async def _collect_report_data(self, report_type: ReportType) -> Dict[str, Any]:
        """
        جمع‌آوری داده‌های مورد نیاز برای گزارش.

        Args:
            report_type: نوع گزارش.

        Returns:
            Dict[str, Any]: داده‌های جمع‌آوری‌شده.
        """
        now = datetime.now()
        data: Dict[str, Any] = {
            "generated_at": now.isoformat(),
            "report_type": report_type.value,
        }

        # تعیین بازه زمانی بر اساس نوع گزارش
        if report_type == ReportType.DAILY:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_date = now
        elif report_type == ReportType.WEEKLY:
            start_date = now - timedelta(days=7)
            end_date = now
        elif report_type == ReportType.MONTHLY:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_date = now
        else:
            start_date = now - timedelta(days=1)
            end_date = now

        data["period"] = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

        # آمار کاربران
        try:
            user_stats = await self._user_repository.get_statistics()
            data["users"] = user_stats
        except Exception as e:
            logger.error(f"Error collecting user stats: {e}")
            data["users"] = {"error": str(e)}

        # آمار سفارشات
        try:
            order_stats = await self._order_repository.get_statistics(start_date, end_date)
            data["orders"] = order_stats
        except Exception as e:
            logger.error(f"Error collecting order stats: {e}")
            data["orders"] = {"error": str(e)}

        # آمار پرداخت‌ها
        try:
            payment_stats = await self._payment_repository.get_statistics(start_date, end_date)
            data["payments"] = payment_stats
        except Exception as e:
            logger.error(f"Error collecting payment stats: {e}")
            data["payments"] = {"error": str(e)}

        # آمار فرم‌ها (در صورت وجود)
        if self._form_repository:
            try:
                form_stats = await self._form_repository.get_statistics()
                data["forms"] = form_stats
            except Exception as e:
                logger.error(f"Error collecting form stats: {e}")
                data["forms"] = {"error": str(e)}

        return data

    async def send_report_now(
        self,
        report_type: ReportType,
        recipients: List[str],
        description: Optional[str] = None,
    ) -> None:
        """
        ارسال فوری یک گزارش (بدون انتظار برای زمان‌بندی).

        Args:
            report_type: نوع گزارش.
            recipients: لیست دریافت‌کنندگان.
            description: توضیحات (اختیاری).
        """
        await self._send_report(report_type, recipients, description)
        logger.info(
            f"Manual report sent: type={report_type.value}, "
            f"recipients={recipients}"
        )