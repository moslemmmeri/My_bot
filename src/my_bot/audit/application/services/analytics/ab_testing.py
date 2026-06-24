# my_bot_project/src/my_bot/application/services/analytics/ab_testing.py
"""
سرویس تست A/B (AB Testing Service).

این سرویس مسئولیت مدیریت تست‌های A/B، ثبت نمایش‌ها و تبدیل‌ها،
محاسبه نتایج آماری و تحلیل عملکرد نسخه‌های مختلف را بر عهده دارد.
"""

import random
import math
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from my_bot.application.dtos.ab_test_dto import (
    ABTestCreateDTO,
    ABTestUpdateDTO,
    ABTestResponseDTO,
    ABTestVariantDTO,
    ABTestResultDTO,
)
from my_bot.core.exceptions.not_found_errors import NotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.ab_test import ABTest, ABTestStatus, ABTestType, ABTestMetric, ABTestVariant
from my_bot.domain.interfaces.repositories.ab_test_repository import ABTestRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class ABTestingService:
    """
    سرویس تست A/B.

    این کلاس مسئولیت مدیریت تست‌های A/B، ثبت نمایش‌ها و تبدیل‌ها،
    محاسبه نتایج آماری و تحلیل عملکرد نسخه‌های مختلف را بر عهده دارد.
    """

    def __init__(
        self,
        ab_test_repository: ABTestRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس تست A/B.

        Args:
            ab_test_repository: ریپازیتوری تست A/B.
            user_repository: ریپازیتوری کاربر.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._ab_test_repository = ab_test_repository
        self._user_repository = user_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._cache_ttl = 300  # 5 دقیقه

    async def create_test(
        self,
        data: ABTestCreateDTO,
        created_by: int,
    ) -> ABTestResponseDTO:
        """
        ایجاد یک تست A/B جدید.

        Args:
            data: اطلاعات تست (DTO).
            created_by: شناسه کاربر ایجادکننده.

        Returns:
            ABTestResponseDTO: اطلاعات تست ایجادشده.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(created_by)
        if not user or not user.can_manage_content():
            raise PermissionDeniedError(
                message="شما مجاز به ایجاد تست A/B نیستید.",
                context={"user_id": created_by},
            )

        # اعتبارسنجی
        if not data.name or not data.name.strip():
            raise ValidationError(
                message="نام تست نمی‌تواند خالی باشد.",
                context={"created_by": created_by},
            )

        if len(data.variants) < 2:
            raise ValidationError(
                message="تست A/B باید حداقل ۲ نسخه داشته باشد.",
                context={"variants_count": len(data.variants)},
            )

        # تبدیل نوع تست و معیار
        try:
            test_type = ABTestType(data.test_type)
        except ValueError:
            raise ValidationError(
                message=f"نوع تست '{data.test_type}' نامعتبر است.",
                context={"test_type": data.test_type},
            )

        try:
            metric = ABTestMetric(data.metric)
        except ValueError:
            raise ValidationError(
                message=f"معیار '{data.metric}' نامعتبر است.",
                context={"metric": data.metric},
            )

        # ایجاد نسخه‌ها
        variants = []
        has_control = False
        for v_data in data.variants:
            variant = ABTestVariant(
                name=v_data.name,
                description=v_data.description,
                config=v_data.config,
                weight=v_data.weight,
                is_control=v_data.is_control,
                metadata=v_data.metadata,
            )
            if v_data.is_control:
                has_control = True
            variants.append(variant)

        if not has_control:
            raise ValidationError(
                message="حداقل یکی از نسخه‌ها باید به‌عنوان کنترل انتخاب شود.",
                context={"variants": data.variants},
            )

        # ایجاد موجودیت تست
        test = ABTest(
            name=data.name,
            test_type=test_type,
            metric=metric,
            variants=variants,
            created_by=created_by,
            description=data.description,
            status=ABTestStatus.DRAFT,
            target_audience=data.target_audience,
            sample_size=data.sample_size,
            confidence_level=data.confidence_level or 0.95,
            minimum_effect=data.minimum_effect,
            metadata=data.metadata,
        )

        # ذخیره در دیتابیس
        saved_test = await self._ab_test_repository.save(test)

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ab_test.created",
                event_data={
                    "test_id": saved_test.id,
                    "name": saved_test.name,
                    "test_type": saved_test.test_type.value,
                    "created_by": created_by,
                },
                source="ABTestingService",
            )

        logger.info(f"AB Test created: id={saved_test.id}, name={saved_test.name}")
        return ABTestResponseDTO.from_entity(saved_test)

    async def get_test(
        self,
        test_id: int,
    ) -> ABTestResponseDTO:
        """
        دریافت اطلاعات یک تست A/B.

        Args:
            test_id: شناسه تست.

        Returns:
            ABTestResponseDTO: اطلاعات تست.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
        """
        # تلاش از کش
        if self._cache:
            cached = await self._cache.get(f"ab_test:{test_id}")
            if cached:
                try:
                    test = ABTest.from_dict(cached)
                    return ABTestResponseDTO.from_entity(test)
                except Exception:
                    pass

        # دریافت از دیتابیس
        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"ab_test:{test_id}",
                test.to_dict(),
                ttl=self._cache_ttl,
            )

        return ABTestResponseDTO.from_entity(test)

    async def get_all_tests(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ABTestStatus] = None,
        test_type: Optional[ABTestType] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[ABTestResponseDTO]:
        """
        دریافت لیست تست‌های A/B.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).
            test_type: فیلتر بر اساس نوع تست (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            List[ABTestResponseDTO]: لیست تست‌ها.
        """
        tests = await self._ab_test_repository.get_all(
            skip=skip,
            limit=limit,
            status=status,
            test_type=test_type,
            order_by=order_by,
            order_desc=order_desc,
        )
        return [ABTestResponseDTO.from_entity(test) for test in tests]

    async def start_test(
        self,
        test_id: int,
        started_by: int,
    ) -> ABTestResponseDTO:
        """
        شروع اجرای تست A/B.

        Args:
            test_id: شناسه تست.
            started_by: شناسه کاربر شروع‌کننده.

        Returns:
            ABTestResponseDTO: اطلاعات تست شروع‌شده.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
            ValidationError: اگر تست قابل شروع نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(started_by)
        if not user or not user.can_manage_content():
            raise PermissionDeniedError(
                message="شما مجاز به شروع تست A/B نیستید.",
                context={"user_id": started_by},
            )

        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status != ABTestStatus.DRAFT:
            raise ValidationError(
                message=f"فقط تست‌های در وضعیت DRAFT قابل شروع هستند. وضعیت فعلی: {test.status.value}",
                context={"test_id": test_id, "status": test.status.value},
            )

        test.start()
        saved_test = await self._ab_test_repository.save(test)

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ab_test.started",
                event_data={
                    "test_id": saved_test.id,
                    "name": saved_test.name,
                    "started_by": started_by,
                },
                source="ABTestingService",
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ab_test:{test_id}")

        logger.info(f"AB Test started: id={test_id}, by={started_by}")
        return ABTestResponseDTO.from_entity(saved_test)

    async def pause_test(
        self,
        test_id: int,
        paused_by: int,
    ) -> ABTestResponseDTO:
        """
        توقف موقت تست A/B.

        Args:
            test_id: شناسه تست.
            paused_by: شناسه کاربر توقف‌دهنده.

        Returns:
            ABTestResponseDTO: اطلاعات تست متوقف‌شده.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
            ValidationError: اگر تست قابل توقف نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        user = await self._user_repository.get_by_id(paused_by)
        if not user or not user.can_manage_content():
            raise PermissionDeniedError(
                message="شما مجاز به توقف تست A/B نیستید.",
                context={"user_id": paused_by},
            )

        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status != ABTestStatus.ACTIVE:
            raise ValidationError(
                message=f"فقط تست‌های در وضعیت ACTIVE قابل توقف هستند. وضعیت فعلی: {test.status.value}",
                context={"test_id": test_id, "status": test.status.value},
            )

        test.pause()
        saved_test = await self._ab_test_repository.save(test)

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ab_test:{test_id}")

        logger.info(f"AB Test paused: id={test_id}, by={paused_by}")
        return ABTestResponseDTO.from_entity(saved_test)

    async def resume_test(
        self,
        test_id: int,
        resumed_by: int,
    ) -> ABTestResponseDTO:
        """
        ادامه دادن تست A/B پس از توقف.

        Args:
            test_id: شناسه تست.
            resumed_by: شناسه کاربر ادامه‌دهنده.

        Returns:
            ABTestResponseDTO: اطلاعات تست ادامه‌یافته.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
            ValidationError: اگر تست قابل ادامه نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        user = await self._user_repository.get_by_id(resumed_by)
        if not user or not user.can_manage_content():
            raise PermissionDeniedError(
                message="شما مجاز به ادامه تست A/B نیستید.",
                context={"user_id": resumed_by},
            )

        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status != ABTestStatus.PAUSED:
            raise ValidationError(
                message=f"فقط تست‌های در وضعیت PAUSED قابل ادامه هستند. وضعیت فعلی: {test.status.value}",
                context={"test_id": test_id, "status": test.status.value},
            )

        test.resume()
        saved_test = await self._ab_test_repository.save(test)

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ab_test:{test_id}")

        logger.info(f"AB Test resumed: id={test_id}, by={resumed_by}")
        return ABTestResponseDTO.from_entity(saved_test)

    async def complete_test(
        self,
        test_id: int,
        completed_by: int,
    ) -> ABTestResponseDTO:
        """
        تکمیل تست A/B.

        Args:
            test_id: شناسه تست.
            completed_by: شناسه کاربر تکمیل‌کننده.

        Returns:
            ABTestResponseDTO: اطلاعات تست تکمیل‌شده.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
            ValidationError: اگر تست قابل تکمیل نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        user = await self._user_repository.get_by_id(completed_by)
        if not user or not user.can_manage_content():
            raise PermissionDeniedError(
                message="شما مجاز به تکمیل تست A/B نیستید.",
                context={"user_id": completed_by},
            )

        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status not in (ABTestStatus.ACTIVE, ABTestStatus.PAUSED):
            raise ValidationError(
                message=f"فقط تست‌های در وضعیت ACTIVE یا PAUSED قابل تکمیل هستند. وضعیت فعلی: {test.status.value}",
                context={"test_id": test_id, "status": test.status.value},
            )

        test.complete()
        saved_test = await self._ab_test_repository.save(test)

        # محاسبه نتایج نهایی
        results = await self.get_test_results(test_id)

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="ab_test.completed",
                event_data={
                    "test_id": saved_test.id,
                    "name": saved_test.name,
                    "completed_by": completed_by,
                    "winner": results.get("winner"),
                },
                source="ABTestingService",
            )

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ab_test:{test_id}")

        logger.info(f"AB Test completed: id={test_id}, by={completed_by}")
        return ABTestResponseDTO.from_entity(saved_test)

    async def archive_test(
        self,
        test_id: int,
        archived_by: int,
    ) -> ABTestResponseDTO:
        """
        بایگانی کردن تست A/B.

        Args:
            test_id: شناسه تست.
            archived_by: شناسه کاربر بایگانی‌کننده.

        Returns:
            ABTestResponseDTO: اطلاعات تست بایگانی‌شده.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
            ValidationError: اگر تست قابل بایگانی نباشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        user = await self._user_repository.get_by_id(archived_by)
        if not user or not user.can_manage_content():
            raise PermissionDeniedError(
                message="شما مجاز به بایگانی تست A/B نیستید.",
                context={"user_id": archived_by},
            )

        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status == ABTestStatus.DRAFT:
            raise ValidationError(
                message="تست‌های پیش‌نویس قابل بایگانی نیستند. ابتدا تست را کامل یا لغو کنید.",
                context={"test_id": test_id, "status": test.status.value},
            )

        test.archive()
        saved_test = await self._ab_test_repository.save(test)

        # حذف کش
        if self._cache:
            await self._cache.delete(f"ab_test:{test_id}")

        logger.info(f"AB Test archived: id={test_id}, by={archived_by}")
        return ABTestResponseDTO.from_entity(saved_test)

    async def record_impression(
        self,
        test_id: int,
        variant_name: str,
        user_id: Optional[int] = None,
    ) -> None:
        """
        ثبت یک نمایش برای یک نسخه از تست.

        Args:
            test_id: شناسه تست.
            variant_name: نام نسخه.
            user_id: شناسه کاربر (اختیاری).

        Raises:
            NotFoundError: اگر تست یا نسخه وجود نداشته باشد.
            ValidationError: اگر تست فعال نباشد.
        """
        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status != ABTestStatus.ACTIVE:
            raise ValidationError(
                message=f"فقط تست‌های فعال قابل ثبت نمایش هستند. وضعیت فعلی: {test.status.value}",
                context={"test_id": test_id, "status": test.status.value},
            )

        variant = test.get_variant(variant_name)
        if not variant:
            raise NotFoundError(
                message=f"نسخهٔ '{variant_name}' در تست یافت نشد.",
                context={"test_id": test_id, "variant_name": variant_name},
            )

        # ثبت نمایش
        test.add_impression(variant_name)
        await self._ab_test_repository.save(test)

        # ذخیره در کش برای کاربر (برای جلوگیری از نمایش مجدد)
        if user_id and self._cache:
            user_key = f"ab_test_user:{test_id}:{user_id}"
            await self._cache.set(user_key, variant_name, ttl=3600)

        logger.debug(f"Impression recorded: test={test_id}, variant={variant_name}")

    async def record_conversion(
        self,
        test_id: int,
        variant_name: str,
        user_id: Optional[int] = None,
    ) -> None:
        """
        ثبت یک تبدیل برای یک نسخه از تست.

        Args:
            test_id: شناسه تست.
            variant_name: نام نسخه.
            user_id: شناسه کاربر (اختیاری).

        Raises:
            NotFoundError: اگر تست یا نسخه وجود نداشته باشد.
            ValidationError: اگر تست فعال نباشد.
        """
        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status != ABTestStatus.ACTIVE:
            raise ValidationError(
                message=f"فقط تست‌های فعال قابل ثبت تبدیل هستند. وضعیت فعلی: {test.status.value}",
                context={"test_id": test_id, "status": test.status.value},
            )

        variant = test.get_variant(variant_name)
        if not variant:
            raise NotFoundError(
                message=f"نسخهٔ '{variant_name}' در تست یافت نشد.",
                context={"test_id": test_id, "variant_name": variant_name},
            )

        # ثبت تبدیل
        test.add_conversion(variant_name)
        await self._ab_test_repository.save(test)

        logger.info(f"Conversion recorded: test={test_id}, variant={variant_name}")

    async def get_test_results(
        self,
        test_id: int,
    ) -> Dict[str, Any]:
        """
        دریافت نتایج آماری تست A/B.

        Args:
            test_id: شناسه تست.

        Returns:
            Dict[str, Any]: نتایج تست شامل:
                - statistics: آمار هر نسخه
                - winner: نسخه برنده (در صورت تکمیل تست)
                - is_significant: آیا تفاوت معنی‌دار است؟
                - confidence_level: سطح اطمینان
                - p_value: مقدار P
                - sample_size_reached: آیا حجم نمونه به حد نصاب رسیده است؟

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
        """
        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        stats = test.get_statistics()
        winner = None

        # اگر تست کامل شده باشد، برنده را تعیین می‌کنیم
        if test.status == ABTestStatus.COMPLETED:
            winner_variant = test.get_winner()
            if winner_variant:
                winner = winner_variant.name

        # محاسبه معنی‌داری آماری (ساده)
        is_significant = False
        p_value = 1.0

        # محاسبه حجم نمونه
        sample_size_reached = test.is_sample_size_reached()

        # محاسبه P-Value با استفاده از آزمون تی (ساده)
        if len(stats) >= 2:
            control = None
            variants = []
            for name, data in stats.items():
                if data.get("is_control"):
                    control = data
                else:
                    variants.append((name, data))

            if control and variants:
                # محاسبه P-Value ساده (فقط برای مقایسه)
                control_rate = control.get("conversion_rate", 0)
                for name, data in variants:
                    rate = data.get("conversion_rate", 0)
                    if control_rate > 0 and rate > 0:
                        # محاسبه نسبت تبدیل و معنی‌داری ساده
                        p_value = self._calculate_p_value(
                            control.get("conversions", 0),
                            control.get("impressions", 0),
                            data.get("conversions", 0),
                            data.get("impressions", 0),
                        )
                        if p_value < (1 - test.confidence_level):
                            is_significant = True
                            break

        return {
            "test_id": test_id,
            "test_name": test.name,
            "status": test.status.value,
            "statistics": stats,
            "winner": winner,
            "is_significant": is_significant,
            "confidence_level": test.confidence_level,
            "p_value": p_value,
            "sample_size_reached": sample_size_reached,
            "sample_size": test.sample_size,
            "current_sample": test.current_sample,
        }

    def _calculate_p_value(
        self,
        conversions_a: int,
        impressions_a: int,
        conversions_b: int,
        impressions_b: int,
    ) -> float:
        """
        محاسبه P-Value برای مقایسه دو نسخه (آزمون تی ساده).

        Args:
            conversions_a: تعداد تبدیل‌های نسخه A.
            impressions_a: تعداد نمایش‌های نسخه A.
            conversions_b: تعداد تبدیل‌های نسخه B.
            impressions_b: تعداد نمایش‌های نسخه B.

        Returns:
            float: مقدار P-Value.
        """
        if impressions_a == 0 or impressions_b == 0:
            return 1.0

        rate_a = conversions_a / impressions_a
        rate_b = conversions_b / impressions_b

        # محاسبه خطای استاندارد
        se_a = math.sqrt(rate_a * (1 - rate_a) / impressions_a)
        se_b = math.sqrt(rate_b * (1 - rate_b) / impressions_b)
        se = math.sqrt(se_a ** 2 + se_b ** 2)

        if se == 0:
            return 1.0

        # محاسبه آماره Z
        z = abs(rate_a - rate_b) / se

        # محاسبه P-Value (تقریب نرمال)
        p = 1 - self._normal_cdf(z)
        return round(p, 4)

    def _normal_cdf(self, x: float) -> float:
        """
        تابع توزیع تجمعی نرمال (تقریب).

        Args:
            x: مقدار Z.

        Returns:
            float: احتمال.
        """
        # تقریب ساده برای CDF نرمال
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2.0)

        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
        return 0.5 * (1.0 + sign * (y - 0.5))

    async def get_variant_for_user(
        self,
        test_id: int,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        دریافت نسخه‌ای که باید به یک کاربر نمایش داده شود.

        Args:
            test_id: شناسه تست.
            user_id: شناسه کاربر.

        Returns:
            Optional[Dict[str, Any]]: اطلاعات نسخه انتخابی یا None در صورت عدم وجود.

        Raises:
            NotFoundError: اگر تست وجود نداشته باشد.
        """
        test = await self._ab_test_repository.get_by_id(test_id)
        if not test:
            raise NotFoundError(
                message=f"تست A/B با شناسه {test_id} یافت نشد.",
                context={"test_id": test_id},
            )

        if test.status != ABTestStatus.ACTIVE:
            return None

        # بررسی کش کاربر
        if self._cache:
            user_key = f"ab_test_user:{test_id}:{user_id}"
            cached = await self._cache.get(user_key)
            if cached:
                variant = test.get_variant(cached)
                if variant:
                    return {
                        "variant_name": variant.name,
                        "is_control": variant.is_control,
                        "config": variant.config,
                    }

        # انتخاب نسخه بر اساس وزن‌ها
        random_value = random.random()
        selected = test.get_variant_by_weight(random_value)

        if not selected:
            return None

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"ab_test_user:{test_id}:{user_id}",
                selected.name,
                ttl=3600,
            )

        return {
            "variant_name": selected.name,
            "is_control": selected.is_control,
            "config": selected.config,
        }

    async def clear_cache(self, test_id: Optional[int] = None) -> None:
        """
        پاک کردن کش تست‌های A/B.

        Args:
            test_id: شناسه تست (اختیاری).
        """
        if self._cache:
            if test_id:
                await self._cache.delete(f"ab_test:{test_id}")
                await self._cache.delete_pattern(f"ab_test_user:{test_id}:*")
            else:
                await self._cache.delete_pattern("ab_test:*")
            logger.info(f"AB Test cache cleared for {'test ' + str(test_id) if test_id else 'all tests'}")