# my_bot_project/src/my_bot/application/services/coupon/coupon_generation.py
"""
سرویس تولید و مدیریت کوپن (Coupon Generation Service).

این سرویس مسئولیت ایجاد، ویرایش، حذف و مدیریت کوپن‌های تخفیف
در سیستم را بر عهده دارد.
"""

import random
import string
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from my_bot.application.dtos.coupon_dto import (
    CouponCreateDTO,
    CouponUpdateDTO,
    CouponResponseDTO,
)
from my_bot.core.exceptions.not_found_errors import CouponNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.coupon import Coupon, CouponType
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class CouponGenerationService:
    """
    سرویس تولید و مدیریت کوپن.

    این کلاس مسئولیت ایجاد، ویرایش، حذف و مدیریت کوپن‌های تخفیف را بر عهده دارد.
    """

    def __init__(
        self,
        coupon_repository: CouponRepository,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس تولید کوپن.

        Args:
            coupon_repository: ریپازیتوری کوپن.
            user_repository: ریپازیتوری کاربر.
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._coupon_repository = coupon_repository
        self._user_repository = user_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._cache_ttl = 3600  # 1 ساعت

    async def create_coupon(
        self,
        data: CouponCreateDTO,
        created_by: int,
    ) -> CouponResponseDTO:
        """
        ایجاد یک کوپن جدید در سیستم.

        Args:
            data: اطلاعات کوپن (DTO).
            created_by: شناسه کاربر ایجادکننده (ادمین).

        Returns:
            CouponResponseDTO: اطلاعات کوپن ایجادشده.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(created_by)
        if not user or not user.can_manage_orders():
            raise PermissionDeniedError(
                message="شما مجاز به ایجاد کوپن نیستید.",
                context={"user_id": created_by},
            )

        # اعتبارسنجی
        if data.code:
            if await self._coupon_repository.exists_by_code(data.code):
                raise ValidationError(
                    message=f"کد کوپن '{data.code}' قبلاً وجود دارد.",
                    context={"code": data.code},
                )
        else:
            # تولید کد خودکار
            data.code = self._generate_coupon_code()

        # تبدیل نوع تخفیف
        try:
            discount_type = CouponType(data.discount_type)
        except ValueError:
            raise ValidationError(
                message=f"نوع تخفیف '{data.discount_type}' نامعتبر است.",
                context={"discount_type": data.discount_type},
            )

        # اعتبارسنجی مقدار تخفیف
        if discount_type == CouponType.PERCENTAGE and data.discount_value > 100:
            raise ValidationError(
                message="تخفیف درصدی نمی‌تواند بیشتر از ۱۰۰ باشد.",
                context={"discount_value": data.discount_value},
            )

        if data.discount_value <= 0:
            raise ValidationError(
                message="مقدار تخفیف باید مثبت باشد.",
                context={"discount_value": data.discount_value},
            )

        # ایجاد موجودیت کوپن
        coupon = Coupon(
            code=data.code,
            discount_type=discount_type,
            discount_value=data.discount_value,
            currency=data.currency,
            description=data.description,
            min_order_amount=Money(data.min_order_amount, data.currency) if data.min_order_amount else None,
            max_discount_amount=Money(data.max_discount_amount, data.currency) if data.max_discount_amount else None,
            usage_limit=data.usage_limit,
            user_usage_limit=data.user_usage_limit or 1,
            valid_from=data.valid_from or datetime.now(),
            valid_until=data.valid_until,
            is_active=data.is_active,
            applicable_products=data.applicable_products or [],
            applicable_users=data.applicable_users or [],
            metadata=data.metadata,
        )

        # ذخیره در دیتابیس
        saved_coupon = await self._coupon_repository.save(coupon)

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="coupon.created",
                event_data={
                    "coupon_id": saved_coupon.id,
                    "code": saved_coupon.code,
                    "discount_value": saved_coupon.discount_value,
                    "created_by": created_by,
                },
                source="CouponGenerationService",
            )

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"coupon:{saved_coupon.code}",
                saved_coupon.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Coupon created: code={saved_coupon.code}, by={created_by}")
        return CouponResponseDTO.from_entity(saved_coupon)

    async def update_coupon(
        self,
        coupon_id: int,
        data: CouponUpdateDTO,
        updated_by: int,
    ) -> CouponResponseDTO:
        """
        ویرایش یک کوپن موجود.

        Args:
            coupon_id: شناسه کوپن.
            data: اطلاعات جدید کوپن.
            updated_by: شناسه کاربر ویرایش‌کننده (ادمین).

        Returns:
            CouponResponseDTO: اطلاعات کوپن به‌روزرسانی‌شده.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(updated_by)
        if not user or not user.can_manage_orders():
            raise PermissionDeniedError(
                message="شما مجاز به ویرایش کوپن نیستید.",
                context={"user_id": updated_by},
            )

        # دریافت کوپن
        coupon = await self._coupon_repository.get_by_id(coupon_id)
        if not coupon:
            raise CouponNotFoundError(coupon_code=str(coupon_id))

        # اعتبارسنجی و به‌روزرسانی
        updated = False

        if data.code is not None and data.code != coupon.code:
            if await self._coupon_repository.exists_by_code(data.code):
                raise ValidationError(
                    message=f"کد کوپن '{data.code}' قبلاً وجود دارد.",
                    context={"code": data.code},
                )
            coupon.code = data.code
            updated = True

        if data.description is not None:
            coupon.description = data.description
            updated = True

        if data.discount_type is not None:
            try:
                coupon.discount_type = CouponType(data.discount_type)
                updated = True
            except ValueError:
                raise ValidationError(
                    message=f"نوع تخفیف '{data.discount_type}' نامعتبر است.",
                    context={"discount_type": data.discount_type},
                )

        if data.discount_value is not None:
            if data.discount_value <= 0:
                raise ValidationError(
                    message="مقدار تخفیف باید مثبت باشد.",
                    context={"discount_value": data.discount_value},
                )
            if coupon.discount_type == CouponType.PERCENTAGE and data.discount_value > 100:
                raise ValidationError(
                    message="تخفیف درصدی نمی‌تواند بیشتر از ۱۰۰ باشد.",
                    context={"discount_value": data.discount_value},
                )
            coupon.discount_value = data.discount_value
            updated = True

        if data.currency is not None:
            coupon.currency = data.currency
            updated = True

        if data.min_order_amount is not None:
            coupon.min_order_amount = Money(data.min_order_amount, coupon.currency)
            updated = True

        if data.max_discount_amount is not None:
            coupon.max_discount_amount = Money(data.max_discount_amount, coupon.currency)
            updated = True

        if data.usage_limit is not None:
            coupon.usage_limit = data.usage_limit
            updated = True

        if data.user_usage_limit is not None:
            coupon.user_usage_limit = data.user_usage_limit
            updated = True

        if data.valid_from is not None:
            coupon.valid_from = data.valid_from
            updated = True

        if data.valid_until is not None:
            coupon.valid_until = data.valid_until
            updated = True

        if data.is_active is not None:
            coupon.is_active = data.is_active
            updated = True

        if data.applicable_products is not None:
            coupon.applicable_products = data.applicable_products
            updated = True

        if data.applicable_users is not None:
            coupon.applicable_users = data.applicable_users
            updated = True

        if data.metadata is not None:
            coupon.metadata = data.metadata
            updated = True

        if not updated:
            logger.debug(f"No changes to update for coupon {coupon_id}")
            return CouponResponseDTO.from_entity(coupon)

        # ذخیره در دیتابیس
        coupon.updated_at = datetime.now()
        saved_coupon = await self._coupon_repository.save(coupon)

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="coupon.updated",
                event_data={
                    "coupon_id": saved_coupon.id,
                    "code": saved_coupon.code,
                    "updated_by": updated_by,
                },
                source="CouponGenerationService",
            )

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"coupon:{saved_coupon.code}",
                saved_coupon.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Coupon updated: code={saved_coupon.code}, by={updated_by}")
        return CouponResponseDTO.from_entity(saved_coupon)

    async def delete_coupon(
        self,
        coupon_id: int,
        deleted_by: int,
    ) -> bool:
        """
        حذف یک کوپن از سیستم.

        Args:
            coupon_id: شناسه کوپن.
            deleted_by: شناسه کاربر حذف‌کننده (ادمین).

        Returns:
            bool: True در صورت حذف موفق.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(deleted_by)
        if not user or not user.can_manage_orders():
            raise PermissionDeniedError(
                message="شما مجاز به حذف کوپن نیستید.",
                context={"user_id": deleted_by},
            )

        # دریافت کوپن
        coupon = await self._coupon_repository.get_by_id(coupon_id)
        if not coupon:
            raise CouponNotFoundError(coupon_code=str(coupon_id))

        # حذف از دیتابیس
        result = await self._coupon_repository.delete(coupon_id)

        # حذف از کش
        if self._cache:
            await self._cache.delete(f"coupon:{coupon.code}")

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="coupon.deleted",
                event_data={
                    "coupon_id": coupon_id,
                    "code": coupon.code,
                    "deleted_by": deleted_by,
                },
                source="CouponGenerationService",
            )

        logger.info(f"Coupon deleted: code={coupon.code}, by={deleted_by}")
        return result

    async def get_coupon(
        self,
        coupon_code: str,
        include_inactive: bool = False,
    ) -> CouponResponseDTO:
        """
        دریافت اطلاعات یک کوپن با کد.

        Args:
            coupon_code: کد کوپن.
            include_inactive: شامل کوپن‌های غیرفعال (پیش‌فرض False).

        Returns:
            CouponResponseDTO: اطلاعات کوپن.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
        """
        # تلاش از کش
        if self._cache:
            cached = await self._cache.get(f"coupon:{coupon_code}")
            if cached:
                try:
                    coupon = Coupon.from_dict(cached)
                    if include_inactive or coupon.is_active:
                        return CouponResponseDTO.from_entity(coupon)
                except Exception:
                    pass

        # دریافت از دیتابیس
        coupon = await self._coupon_repository.get_by_code(coupon_code)
        if not coupon:
            raise CouponNotFoundError(coupon_code=coupon_code)

        if not include_inactive and not coupon.is_active:
            raise CouponNotFoundError(
                coupon_code=coupon_code,
                context={"is_active": coupon.is_active},
            )

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                f"coupon:{coupon_code}",
                coupon.to_dict(),
                ttl=self._cache_ttl,
            )

        return CouponResponseDTO.from_entity(coupon)

    async def get_all_coupons(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[CouponResponseDTO]:
        """
        دریافت لیست تمام کوپن‌ها.

        Args:
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            is_active: فیلتر بر اساس فعال بودن (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            List[CouponResponseDTO]: لیست کوپن‌ها.
        """
        coupons = await self._coupon_repository.get_all(
            skip=skip,
            limit=limit,
            is_active=is_active,
            order_by=order_by,
            order_desc=order_desc,
        )
        return [CouponResponseDTO.from_entity(coupon) for coupon in coupons]

    async def activate_coupon(
        self,
        coupon_code: str,
        activated_by: int,
    ) -> CouponResponseDTO:
        """
        فعال‌سازی یک کوپن.

        Args:
            coupon_code: کد کوپن.
            activated_by: شناسه کاربر فعال‌کننده (ادمین).

        Returns:
            CouponResponseDTO: اطلاعات کوپن فعال‌شده.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(activated_by)
        if not user or not user.can_manage_orders():
            raise PermissionDeniedError(
                message="شما مجاز به فعال‌سازی کوپن نیستید.",
                context={"user_id": activated_by},
            )

        coupon = await self._coupon_repository.get_by_code(coupon_code)
        if not coupon:
            raise CouponNotFoundError(coupon_code=coupon_code)

        coupon.activate()
        saved_coupon = await self._coupon_repository.save(coupon)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"coupon:{coupon_code}",
                saved_coupon.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Coupon activated: code={coupon_code}, by={activated_by}")
        return CouponResponseDTO.from_entity(saved_coupon)

    async def deactivate_coupon(
        self,
        coupon_code: str,
        deactivated_by: int,
        reason: Optional[str] = None,
    ) -> CouponResponseDTO:
        """
        غیرفعال‌سازی یک کوپن.

        Args:
            coupon_code: کد کوپن.
            deactivated_by: شناسه کاربر غیرفعال‌کننده (ادمین).
            reason: دلیل غیرفعال‌سازی (اختیاری).

        Returns:
            CouponResponseDTO: اطلاعات کوپن غیرفعال‌شده.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        # بررسی دسترسی
        user = await self._user_repository.get_by_id(deactivated_by)
        if not user or not user.can_manage_orders():
            raise PermissionDeniedError(
                message="شما مجاز به غیرفعال‌سازی کوپن نیستید.",
                context={"user_id": deactivated_by},
            )

        coupon = await self._coupon_repository.get_by_code(coupon_code)
        if not coupon:
            raise CouponNotFoundError(coupon_code=coupon_code)

        coupon.deactivate(reason)
        saved_coupon = await self._coupon_repository.save(coupon)

        # به‌روزرسانی کش
        if self._cache:
            await self._cache.set(
                f"coupon:{coupon_code}",
                saved_coupon.to_dict(),
                ttl=self._cache_ttl,
            )

        logger.info(f"Coupon deactivated: code={coupon_code}, by={deactivated_by}")
        return CouponResponseDTO.from_entity(saved_coupon)

    async def generate_bulk_coupons(
        self,
        count: int,
        data: CouponCreateDTO,
        created_by: int,
    ) -> List[CouponResponseDTO]:
        """
        تولید انبوه کوپن.

        Args:
            count: تعداد کوپن‌ها.
            data: اطلاعات پایه کوپن.
            created_by: شناسه کاربر ایجادکننده (ادمین).

        Returns:
            List[CouponResponseDTO]: لیست کوپن‌های ایجادشده.

        Raises:
            ValidationError: اگر تعداد نامعتبر باشد.
            PermissionDeniedError: اگر کاربر مجاز نباشد.
        """
        if count <= 0 or count > 1000:
            raise ValidationError(
                message="تعداد کوپن‌ها باید بین ۱ تا ۱۰۰۰ باشد.",
                context={"count": count},
            )

        # بررسی دسترسی
        user = await self._user_repository.get_by_id(created_by)
        if not user or not user.can_manage_orders():
            raise PermissionDeniedError(
                message="شما مجاز به تولید انبوه کوپن نیستید.",
                context={"user_id": created_by},
            )

        created_coupons = []
        for _ in range(count):
            # ایجاد کد یکتا
            new_code = self._generate_coupon_code()
            # اطمینان از یکتا بودن
            while await self._coupon_repository.exists_by_code(new_code):
                new_code = self._generate_coupon_code()

            # کپی داده‌ها و تنظیم کد جدید
            coupon_data = data.copy()
            coupon_data.code = new_code

            # ایجاد کوپن
            coupon = await self.create_coupon(coupon_data, created_by)
            created_coupons.append(coupon)

        logger.info(f"Bulk coupons created: {count} coupons by {created_by}")
        return created_coupons

    async def get_coupon_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی کوپن‌ها.

        Returns:
            Dict[str, Any]: آمار کوپن‌ها.
        """
        return await self._coupon_repository.get_statistics()

    async def search_coupons(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CouponResponseDTO]:
        """
        جستجوی کوپن‌ها با استفاده از کد یا توضیحات.

        Args:
            query: عبارت جستجو.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[CouponResponseDTO]: لیست کوپن‌های مطابق با جستجو.
        """
        # دریافت تمام کوپن‌ها و فیلتر دستی (در صورت عدم وجود متد search)
        coupons = await self._coupon_repository.get_all(skip=0, limit=1000)
        query_lower = query.lower()

        filtered = [
            c for c in coupons
            if query_lower in c.code.lower()
            or (c.description and query_lower in c.description.lower())
        ]

        # صفحه‌بندی
        filtered = filtered[skip:skip + limit]

        return [CouponResponseDTO.from_entity(coupon) for coupon in filtered]

    def _generate_coupon_code(self, length: int = 8) -> str:
        """
        تولید کد کوپن تصادفی.

        Args:
            length: طول کد (پیش‌فرض ۸).

        Returns:
            str: کد کوپن تولیدشده.
        """
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choices(characters, k=length))

    async def clear_cache(self) -> None:
        """پاک کردن کش کوپن‌ها."""
        if self._cache:
            await self._cache.delete_pattern("coupon:*")
            logger.info("Coupon cache cleared.")