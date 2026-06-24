# my_bot_project/src/my_bot/application/services/order/order_creation.py
"""
سرویس ایجاد سفارش (Order Creation Service).

این سرویس مسئولیت ایجاد سفارشات جدید در سیستم را بر عهده دارد.
شامل اعتبارسنجی محصولات، محاسبه قیمت‌ها، اعمال تخفیف‌ها و ذخیره‌سازی سفارش است.
"""

from typing import Optional, List
from decimal import Decimal

from my_bot.application.dtos.order_dto import OrderCreateDTO, OrderResponseDTO, OrderItemDTO
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.not_found_errors import UserNotFoundError, ProductNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.order import Order, OrderItem
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.coupon_repository import CouponRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class OrderCreationService:
    """
    سرویس ایجاد سفارش.

    این کلاس مسئولیت ایجاد سفارشات جدید در سیستم را بر عهده دارد.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        coupon_repository: Optional[CouponRepository] = None,
        message_publisher: Optional[MessagePublisher] = None,
        product_service: Optional[object] = None,  # برای دریافت اطلاعات محصول
    ) -> None:
        """
        مقداردهی اولیه سرویس ایجاد سفارش.

        Args:
            order_repository: ریپازیتوری سفارش.
            user_repository: ریپازیتوری کاربر.
            coupon_repository: ریپازیتوری کوپن (اختیاری).
            message_publisher: انتشاردهنده پیام (اختیاری).
            product_service: سرویس محصول برای دریافت اطلاعات محصولات (اختیاری).
        """
        self._order_repository = order_repository
        self._user_repository = user_repository
        self._coupon_repository = coupon_repository
        self._message_publisher = message_publisher
        self._product_service = product_service

    async def create_order(
        self,
        data: OrderCreateDTO,
        user_id: int,
    ) -> OrderResponseDTO:
        """
        ایجاد یک سفارش جدید در سیستم.

        Args:
            data: اطلاعات سفارش (DTO).
            user_id: شناسه کاربر.

        Returns:
            OrderResponseDTO: اطلاعات سفارش ایجادشده.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
            ProductNotFoundError: اگر محصولی وجود نداشته باشد.
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # اعتبارسنجی و دریافت اطلاعات محصولات
        items = await self._validate_and_get_items(data.items)

        # محاسبه مبلغ پایه (Subtotal)
        subtotal = self._calculate_subtotal(items)

        # اعمال تخفیف کوپن (در صورت وجود)
        discount_amount = Money(Decimal("0"), "IRR")
        if data.coupon_code:
            discount_amount = await self._apply_coupon(
                data.coupon_code,
                user_id,
                subtotal,
            )

        # محاسبه مبلغ کل
        total_amount = subtotal - discount_amount
        if total_amount.amount < 0:
            total_amount = Money(Decimal("0"), "IRR")

        # ایجاد شماره سفارش
        order_number = await self._generate_order_number()

        # ساخت موجودیت سفارش
        order = Order(
            user_id=user_id,
            order_number=order_number,
            items=items,
            subtotal=subtotal,
            total_amount=total_amount,
            discount_amount=discount_amount,
            coupon_code=data.coupon_code,
            status=OrderStatus.PENDING,
            shipping_address=data.shipping_address,
            notes=data.notes,
            metadata={
                "ip_address": data.ip_address,
                "user_agent": data.user_agent,
            },
        )

        # ذخیره‌سازی در دیتابیس
        saved_order = await self._order_repository.save(order)

        # انتشار رویداد ایجاد سفارش
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="order.created",
                event_data={
                    "order_id": saved_order.id,
                    "order_number": saved_order.order_number,
                    "user_id": user_id,
                    "total_amount": total_amount.amount,
                    "currency": total_amount.currency,
                },
                source="OrderCreationService",
            )

        logger.info(
            f"Order created: order_number={saved_order.order_number}, "
            f"user_id={user_id}, total={total_amount.amount}"
        )

        return OrderResponseDTO.from_entity(saved_order)

    async def create_order_from_cart(
        self,
        user_id: int,
        cart_items: List[dict],
        shipping_address: Optional[str] = None,
        notes: Optional[str] = None,
        coupon_code: Optional[str] = None,
    ) -> OrderResponseDTO:
        """
        ایجاد سفارش از سبد خرید.

        Args:
            user_id: شناسه کاربر.
            cart_items: لیست آیتم‌های سبد خرید.
            shipping_address: آدرس تحویل (اختیاری).
            notes: یادداشت (اختیاری).
            coupon_code: کد تخفیف (اختیاری).

        Returns:
            OrderResponseDTO: اطلاعات سفارش ایجادشده.
        """
        # تبدیل آیتم‌های سبد خرید به OrderItemDTO
        items_dto = [
            OrderItemDTO(
                product_id=item["product_id"],
                product_name=item.get("product_name", ""),
                quantity=item["quantity"],
                unit_price=Money(item["unit_price"], "IRR"),
                metadata=item.get("metadata", {}),
            )
            for item in cart_items
        ]

        data = OrderCreateDTO(
            items=items_dto,
            shipping_address=shipping_address,
            notes=notes,
            coupon_code=coupon_code,
        )

        return await self.create_order(data, user_id)

    async def _validate_and_get_items(self, items_dto: List[OrderItemDTO]) -> List[OrderItem]:
        """
        اعتبارسنجی و تبدیل آیتم‌های DTO به موجودیت OrderItem.

        Args:
            items_dto: لیست آیتم‌های DTO.

        Returns:
            List[OrderItem]: لیست آیتم‌های سفارش.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            ProductNotFoundError: اگر محصولی وجود نداشته باشد.
        """
        if not items_dto:
            raise ValidationError(
                message="سفارش باید حداقل یک آیتم داشته باشد.",
                context={"items_count": len(items_dto)},
            )

        items = []
        for item_dto in items_dto:
            # اعتبارسنجی تعداد
            if item_dto.quantity <= 0:
                raise ValidationError(
                    message=f"تعداد آیتم '{item_dto.product_id}' باید مثبت باشد.",
                    context={"product_id": item_dto.product_id, "quantity": item_dto.quantity},
                )

            # دریافت اطلاعات محصول (در صورت وجود سرویس)
            product_name = item_dto.product_name
            unit_price = item_dto.unit_price

            if self._product_service:
                try:
                    product = await self._product_service.get_product(item_dto.product_id)
                    if product:
                        product_name = product.get("name", product_name)
                        unit_price = Money(product.get("price", 0), "IRR")
                except Exception as e:
                    logger.warning(f"Could not fetch product {item_dto.product_id}: {e}")

            # ایجاد آیتم سفارش
            item = OrderItem(
                product_id=item_dto.product_id,
                product_name=product_name,
                quantity=item_dto.quantity,
                unit_price=unit_price,
                metadata=item_dto.metadata,
            )
            items.append(item)

        return items

    def _calculate_subtotal(self, items: List[OrderItem]) -> Money:
        """
        محاسبه مبلغ پایه (جمع قیمت کل آیتم‌ها).

        Args:
            items: لیست آیتم‌های سفارش.

        Returns:
            Money: مبلغ پایه.
        """
        total = Money(Decimal("0"), "IRR")
        for item in items:
            total = total + item.total_price
        return total

    async def _apply_coupon(
        self,
        coupon_code: str,
        user_id: int,
        subtotal: Money,
    ) -> Money:
        """
        اعمال کوپن تخفیف روی سفارش.

        Args:
            coupon_code: کد تخفیف.
            user_id: شناسه کاربر.
            subtotal: مبلغ پایه.

        Returns:
            Money: مبلغ تخفیف.

        Raises:
            ValidationError: اگر کوپن نامعتبر باشد.
        """
        if not self._coupon_repository:
            logger.warning("Coupon repository not available, skipping coupon validation.")
            return Money(Decimal("0"), "IRR")

        # دریافت کوپن
        coupon = await self._coupon_repository.get_by_code(coupon_code)
        if not coupon:
            raise ValidationError(
                message=f"کد تخفیف '{coupon_code}' معتبر نیست.",
                context={"coupon_code": coupon_code},
            )

        # اعتبارسنجی کوپن
        if not coupon.is_valid(user_id=user_id, order_amount=subtotal):
            raise ValidationError(
                message=f"کد تخفیف '{coupon_code}' قابل استفاده نیست.",
                context={"coupon_code": coupon_code, "user_id": user_id},
            )

        # محاسبه مبلغ تخفیف
        discounted_amount = coupon.apply_discount(subtotal)
        discount_amount = subtotal - discounted_amount

        # ثبت استفاده از کوپن
        try:
            await self._coupon_repository.use_coupon(coupon.id or 0, user_id)
        except Exception as e:
            logger.error(f"Failed to record coupon usage: {e}")

        logger.info(
            f"Coupon '{coupon_code}' applied: discount={discount_amount.amount}, "
            f"user_id={user_id}"
        )

        return discount_amount

    async def _generate_order_number(self) -> str:
        """
        تولید شماره سفارش یکتا.

        Returns:
            str: شماره سفارش.
        """
        import random
        import time

        # ترکیب timestamp و عدد تصادفی
        timestamp = int(time.time() * 1000)  # میلی‌ثانیه
        random_part = random.randint(1000, 9999)
        order_number = f"ORD-{timestamp}-{random_part}"

        # اطمینان از یکتا بودن (در صورت تکراری بودن، دوباره تولید می‌کنیم)
        existing = await self._order_repository.get_by_order_number(order_number)
        if existing:
            return await self._generate_order_number()

        return order_number

    async def cancel_order(self, order_id: int, user_id: int) -> bool:
        """
        لغو یک سفارش توسط کاربر (در صورت امکان).

        Args:
            order_id: شناسه سفارش.
            user_id: شناسه کاربر.

        Returns:
            bool: True در صورت لغو موفق.

        Raises:
            ValidationError: اگر سفارش قابل لغو نباشد یا کاربر مجاز نباشد.
        """
        order = await self._order_repository.get_by_id(order_id)
        if not order:
            raise ValidationError(
                message=f"سفارش با شناسه {order_id} یافت نشد.",
                context={"order_id": order_id},
            )

        # بررسی مالکیت سفارش
        if order.user_id != user_id:
            raise ValidationError(
                message="شما مجاز به لغو این سفارش نیستید.",
                context={"order_id": order_id, "user_id": user_id},
            )

        # بررسی قابلیت لغو
        if not order.status.can_cancel():
            raise ValidationError(
                message=f"سفارش در وضعیت '{order.status.display_name}' قابل لغو نیست.",
                context={"order_id": order_id, "status": order.status.value},
            )

        # لغو سفارش
        order.cancel("Cancelled by user")
        await self._order_repository.save(order)

        # انتشار رویداد لغو سفارش
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="order.cancelled",
                event_data={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "user_id": user_id,
                },
                source="OrderCreationService",
            )

        logger.info(f"Order {order_id} cancelled by user {user_id}")
        return True