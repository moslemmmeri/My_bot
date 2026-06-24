# my_bot_project/src/my_bot/application/services/coupon/coupon_validation.py
"""
سرویس اعتبارسنجی کوپن (Coupon Validation Service).

این سرویس مسئولیت اعتبارسنجی کوپن‌های تخفیف، بررسی شرایط استفاده
و اعمال تخفیف روی سفارشات را بر عهده دارد.
"""

from typing import Optional, Dict, Any, Tuple
from decimal import Decimal

from my_bot.application.dtos.coupon_dto import CouponValidateDTO, CouponResponseDTO
from my_bot.core.exceptions.not_found_errors import CouponNotFoundError, UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.coupon import Coupon
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class CouponValidationService:
    """
    سرویس اعتبارسنجی و اعمال کوپن.

    این کلاس مسئولیت اعتبارسنجی کوپن‌ها، بررسی شرایط استفاده
    و اعمال تخفیف روی سفارشات را بر عهده دارد.
    """

    def __init__(
        self,
        coupon_repository: CouponRepository,
        user_repository: UserRepository,
        order_repository: Optional[OrderRepository] = None,
        message_publisher: Optional[MessagePublisher] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس اعتبارسنجی کوپن.

        Args:
            coupon_repository: ریپازیتوری کوپن.
            user_repository: ریپازیتوری کاربر.
            order_repository: ریپازیتوری سفارش (اختیاری).
            message_publisher: انتشاردهنده پیام (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._coupon_repository = coupon_repository
        self._user_repository = user_repository
        self._order_repository = order_repository
        self._message_publisher = message_publisher
        self._cache = cache
        self._cache_ttl = 300  # 5 دقیقه

    async def validate_coupon(
        self,
        coupon_code: str,
        user_id: int,
        order_amount: Money,
        product_ids: Optional[list[str]] = None,
    ) -> CouponValidateDTO:
        """
        اعتبارسنجی یک کوپن برای کاربر و مبلغ سفارش مشخص.

        Args:
            coupon_code: کد کوپن.
            user_id: شناسه کاربر.
            order_amount: مبلغ سفارش.
            product_ids: لیست شناسه محصولات سفارش (اختیاری).

        Returns:
            CouponValidateDTO: نتیجه اعتبارسنجی شامل:
                - is_valid: آیا کوپن معتبر است؟
                - discount_amount: مبلغ تخفیف قابل اعمال
                - message: پیام توضیحی
                - coupon: اطلاعات کوپن (در صورت معتبر بودن)

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت کوپن (از کش یا دیتابیس)
        coupon = await self._get_coupon(coupon_code)

        if not coupon:
            raise CouponNotFoundError(coupon_code=coupon_code)

        # بررسی اعتبار کوپن (بدون محصولات خاص)
        is_valid = coupon.is_valid(
            user_id=user_id,
            order_amount=order_amount,
        )

        if not is_valid:
            # پیدا کردن دلیل نامعتبر بودن
            reason = self._get_invalid_reason(coupon, user_id, order_amount)
            return CouponValidateDTO(
                is_valid=False,
                discount_amount=Money(Decimal("0"), order_amount.currency),
                message=reason,
                coupon=None,
            )

        # بررسی محصولات (اگر مشخص شده باشند)
        if product_ids and coupon.applicable_products:
            for product_id in product_ids:
                if not coupon.is_applicable_to_product(product_id):
                    return CouponValidateDTO(
                        is_valid=False,
                        discount_amount=Money(Decimal("0"), order_amount.currency),
                        message=f"این کوپن برای محصول '{product_id}' قابل استفاده نیست.",
                        coupon=None,
                    )

        # محاسبه مبلغ تخفیف
        discount_amount = self._calculate_discount(coupon, order_amount)

        return CouponValidateDTO(
            is_valid=True,
            discount_amount=discount_amount,
            message="کوپن معتبر است.",
            coupon=CouponResponseDTO.from_entity(coupon),
        )

    async def apply_coupon(
        self,
        coupon_code: str,
        user_id: int,
        order_amount: Money,
        order_id: Optional[str] = None,
        product_ids: Optional[list[str]] = None,
    ) -> Tuple[Money, CouponResponseDTO]:
        """
        اعمال کوپن روی سفارش و ثبت استفاده.

        Args:
            coupon_code: کد کوپن.
            user_id: شناسه کاربر.
            order_amount: مبلغ سفارش.
            order_id: شناسه سفارش (اختیاری).
            product_ids: لیست شناسه محصولات (اختیاری).

        Returns:
            Tuple[Money, CouponResponseDTO]: مبلغ نهایی پس از تخفیف و اطلاعات کوپن.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            ValidationError: اگر کوپن معتبر نباشد یا قابل استفاده نباشد.
        """
        # اعتبارسنجی کوپن
        validation = await self.validate_coupon(
            coupon_code=coupon_code,
            user_id=user_id,
            order_amount=order_amount,
            product_ids=product_ids,
        )

        if not validation.is_valid:
            raise ValidationError(
                message=validation.message or "کوپن معتبر نیست.",
                context={"coupon_code": coupon_code, "user_id": user_id},
            )

        if not validation.coupon:
            raise ValidationError(
                message="اطلاعات کوپن یافت نشد.",
                context={"coupon_code": coupon_code},
            )

        # دریافت موجودیت کوپن
        coupon = await self._get_coupon(coupon_code)
        if not coupon:
            raise CouponNotFoundError(coupon_code=coupon_code)

        # ثبت استفاده از کوپن
        try:
            coupon.use(user_id)
            await self._coupon_repository.save(coupon)
        except Exception as e:
            logger.error(f"Failed to use coupon {coupon_code} for user {user_id}: {e}")
            raise ValidationError(
                message="خطا در ثبت استفاده از کوپن.",
                context={"coupon_code": coupon_code, "user_id": user_id},
            )

        # محاسبه مبلغ نهایی
        final_amount = order_amount - validation.discount_amount
        if final_amount.amount < 0:
            final_amount = Money(Decimal("0"), order_amount.currency)

        # به‌روزرسانی سفارش (در صورت وجود شناسه سفارش)
        if order_id and self._order_repository:
            try:
                await self._order_repository.apply_coupon(
                    order_id=int(order_id),
                    coupon_code=coupon_code,
                    discount_amount=validation.discount_amount,
                )
                logger.info(f"Coupon {coupon_code} applied to order {order_id}")
            except Exception as e:
                logger.error(f"Failed to apply coupon to order {order_id}: {e}")

        # انتشار رویداد استفاده از کوپن
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="coupon.used",
                event_data={
                    "coupon_code": coupon_code,
                    "user_id": user_id,
                    "order_id": order_id,
                    "discount_amount": validation.discount_amount.amount,
                    "currency": validation.discount_amount.currency,
                    "final_amount": final_amount.amount,
                },
                source="CouponValidationService",
            )

        logger.info(
            f"Coupon {coupon_code} applied for user {user_id}: "
            f"discount={validation.discount_amount.amount}, final={final_amount.amount}"
        )

        return final_amount, CouponResponseDTO.from_entity(coupon)

    async def get_coupon_discount(
        self,
        coupon_code: str,
        user_id: int,
        order_amount: Money,
        product_ids: Optional[list[str]] = None,
    ) -> Money:
        """
        محاسبه مبلغ تخفیف کوپن بدون ثبت استفاده.

        Args:
            coupon_code: کد کوپن.
            user_id: شناسه کاربر.
            order_amount: مبلغ سفارش.
            product_ids: لیست شناسه محصولات (اختیاری).

        Returns:
            Money: مبلغ تخفیف.

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            ValidationError: اگر کوپن معتبر نباشد.
        """
        validation = await self.validate_coupon(
            coupon_code=coupon_code,
            user_id=user_id,
            order_amount=order_amount,
            product_ids=product_ids,
        )

        if not validation.is_valid:
            raise ValidationError(
                message=validation.message or "کوپن معتبر نیست.",
                context={"coupon_code": coupon_code, "user_id": user_id},
            )

        return validation.discount_amount

    async def get_valid_coupons_for_user(
        self,
        user_id: int,
        order_amount: Money,
        product_ids: Optional[list[str]] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CouponResponseDTO]:
        """
        دریافت کوپن‌های معتبر برای یک کاربر و سفارش خاص.

        Args:
            user_id: شناسه کاربر.
            order_amount: مبلغ سفارش.
            product_ids: لیست شناسه محصولات (اختیاری).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            list[CouponResponseDTO]: لیست کوپن‌های معتبر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت کوپن‌های معتبر از ریپازیتوری
        coupons = await self._coupon_repository.get_valid_coupons(
            user_id=user_id,
            order_amount=order_amount,
            product_id=product_ids[0] if product_ids else None,
            skip=skip,
            limit=limit,
        )

        # فیلتر نهایی (بررسی محصولات)
        valid_coupons = []
        for coupon in coupons:
            if product_ids and coupon.applicable_products:
                applicable = all(
                    coupon.is_applicable_to_product(pid)
                    for pid in product_ids
                )
                if not applicable:
                    continue
            valid_coupons.append(coupon)

        return [CouponResponseDTO.from_entity(c) for c in valid_coupons]

    async def check_coupon_usage(
        self,
        coupon_code: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        بررسی وضعیت استفاده از کوپن توسط یک کاربر خاص.

        Args:
            coupon_code: کد کوپن.
            user_id: شناسه کاربر.

        Returns:
            Dict[str, Any]: اطلاعات استفاده شامل:
                - total_usage: تعداد کل استفاده‌ها
                - user_usage: تعداد استفاده‌های این کاربر
                - max_user_usage: حداکثر مجاز برای هر کاربر
                - remaining: تعداد دفعات باقی‌مانده برای این کاربر
                - coupon_active: وضعیت فعال بودن کوپن

        Raises:
            CouponNotFoundError: اگر کوپن وجود نداشته باشد.
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت کوپن
        coupon = await self._get_coupon(coupon_code)
        if not coupon:
            raise CouponNotFoundError(coupon_code=coupon_code)

        user_usage = coupon.user_usage_count.get(user_id, 0)
        total_usage = coupon.usage_count

        return {
            "coupon_code": coupon.code,
            "total_usage": total_usage,
            "user_usage": user_usage,
            "max_user_usage": coupon.user_usage_limit,
            "remaining_for_user": max(0, coupon.user_usage_limit - user_usage),
            "coupon_active": coupon.is_active,
            "expired": coupon.is_expired(),
            "valid_until": coupon.valid_until.isoformat() if coupon.valid_until else None,
        }

    async def _get_coupon(self, coupon_code: str) -> Optional[Coupon]:
        """
        دریافت کوپن از کش یا دیتابیس.

        Args:
            coupon_code: کد کوپن.

        Returns:
            Optional[Coupon]: کوپن یا None در صورت عدم وجود.
        """
        # تلاش از کش
        if self._cache:
            cached = await self._cache.get(f"coupon:{coupon_code}")
            if cached:
                try:
                    return Coupon.from_dict(cached)
                except Exception:
                    pass

        # دریافت از دیتابیس
        coupon = await self._coupon_repository.get_by_code(coupon_code)

        # ذخیره در کش
        if coupon and self._cache:
            await self._cache.set(
                f"coupon:{coupon_code}",
                coupon.to_dict(),
                ttl=self._cache_ttl,
            )

        return coupon

    def _calculate_discount(self, coupon: Coupon, order_amount: Money) -> Money:
        """
        محاسبه مبلغ تخفیف کوپن.

        Args:
            coupon: موجودیت کوپن.
            order_amount: مبلغ سفارش.

        Returns:
            Money: مبلغ تخفیف.
        """
        if coupon.discount_type.value == "percentage":
            discount = order_amount * (coupon.discount_value / 100)
            # اعمال حداکثر تخفیف (در صورت وجود)
            if coupon.max_discount_amount:
                discount = min(discount, coupon.max_discount_amount)
            return discount
        else:  # fixed
            discount = Money(coupon.discount_value, order_amount.currency)
            # تخفیف نباید از مبلغ اصلی بیشتر شود
            if discount.amount > order_amount.amount:
                discount = order_amount
            return discount

    def _get_invalid_reason(
        self,
        coupon: Coupon,
        user_id: int,
        order_amount: Money,
    ) -> str:
        """
        دریافت دلیل نامعتبر بودن کوپن.

        Args:
            coupon: موجودیت کوپن.
            user_id: شناسه کاربر.
            order_amount: مبلغ سفارش.

        Returns:
            str: دلیل نامعتبر بودن.
        """
        if not coupon.is_active:
            return "کوپن غیرفعال است."
        if coupon.is_expired():
            return "کوپن منقضی شده است."
        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            return "محدودیت استفاده از کوپن به پایان رسیده است."
        user_used = coupon.user_usage_count.get(user_id, 0)
        if user_used >= coupon.user_usage_limit:
            return "شما از این کوپن بیش از حد مجاز استفاده کرده‌اید."
        if coupon.min_order_amount and order_amount.amount < coupon.min_order_amount.amount:
            return f"حداقل مبلغ سفارش برای استفاده از این کوپن {coupon.min_order_amount.amount} {coupon.min_order_amount.currency} است."
        if coupon.applicable_users and user_id not in coupon.applicable_users:
            return "این کوپن برای کاربران خاصی در نظر گرفته شده است."
        return "کوپن معتبر نیست."

    async def clear_cache(self) -> None:
        """پاک کردن کش کوپن‌ها."""
        if self._cache:
            await self._cache.delete_pattern("coupon:*")
            logger.info("Coupon validation cache cleared.")