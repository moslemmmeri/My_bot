# my_bot_project/src/my_bot/application/services/order/order_status_update.py
"""
سرویس به‌روزرسانی وضعیت سفارش (Order Status Update Service).

این سرویس مسئولیت تغییر وضعیت سفارشات در سیستم را بر عهده دارد.
شامل عملیات‌هایی مانند تأیید پرداخت، شروع پردازش، ارسال، تحویل، لغو و بازگشت وجه است.
"""

from typing import Optional

from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.not_found_errors import OrderNotFoundError
from my_bot.core.exceptions.permission_errors import PermissionDeniedError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.entities.order import Order

logger = get_logger(__name__)


class OrderStatusUpdateService:
    """
    سرویس به‌روزرسانی وضعیت سفارش.

    این کلاس مسئولیت تغییر وضعیت سفارشات در سیستم را بر عهده دارد.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        message_publisher: Optional[MessagePublisher] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس به‌روزرسانی وضعیت.

        Args:
            order_repository: ریپازیتوری سفارش.
            message_publisher: انتشاردهنده پیام برای رویدادها (اختیاری).
        """
        self._order_repository = order_repository
        self._message_publisher = message_publisher

    async def mark_as_paid(
        self,
        order_id: int,
        payment_id: str,
        actor_id: Optional[int] = None,
    ) -> Order:
        """
        علامت‌گذاری سفارش به‌عنوان پرداخت‌شده.

        Args:
            order_id: شناسه سفارش.
            payment_id: شناسه تراکنش پرداخت.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            ValidationError: اگر وضعیت فعلی اجازه‌ی پرداخت را ندهد.
        """
        order = await self._get_order(order_id)

        try:
            order.mark_as_paid(payment_id)
            saved_order = await self._order_repository.save(order)

            await self._publish_event(
                event_type="order.paid",
                event_data={
                    "order_id": saved_order.id,
                    "order_number": saved_order.order_number,
                    "payment_id": payment_id,
                    "actor_id": actor_id,
                },
            )

            logger.info(f"Order {order_id} marked as PAID with payment_id={payment_id}")
            return saved_order

        except Exception as e:
            logger.error(f"Failed to mark order {order_id} as paid: {e}")
            raise

    async def mark_as_processing(
        self,
        order_id: int,
        actor_id: Optional[int] = None,
    ) -> Order:
        """
        علامت‌گذاری سفارش به‌عنوان در حال پردازش.

        Args:
            order_id: شناسه سفارش.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            ValidationError: اگر تغییر وضعیت مجاز نباشد.
        """
        order = await self._get_order(order_id)

        order.update_status(OrderStatus.PROCESSING, "Start processing")
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.processing",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "actor_id": actor_id,
            },
        )

        logger.info(f"Order {order_id} marked as PROCESSING")
        return saved_order

    async def mark_as_shipped(
        self,
        order_id: int,
        tracking_code: str,
        actor_id: Optional[int] = None,
    ) -> Order:
        """
        علامت‌گذاری سفارش به‌عنوان ارسال‌شده.

        Args:
            order_id: شناسه سفارش.
            tracking_code: کد رهگیری پستی.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            ValidationError: اگر تغییر وضعیت مجاز نباشد.
        """
        order = await self._get_order(order_id)

        order.update_status(OrderStatus.SHIPPED, "Shipped")
        order.tracking_code = tracking_code
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.shipped",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "tracking_code": tracking_code,
                "actor_id": actor_id,
            },
        )

        logger.info(f"Order {order_id} marked as SHIPPED with tracking_code={tracking_code}")
        return saved_order

    async def mark_as_delivered(
        self,
        order_id: int,
        actor_id: Optional[int] = None,
    ) -> Order:
        """
        علامت‌گذاری سفارش به‌عنوان تحویل‌داده‌شده.

        Args:
            order_id: شناسه سفارش.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            ValidationError: اگر تغییر وضعیت مجاز نباشد.
        """
        order = await self._get_order(order_id)

        order.update_status(OrderStatus.DELIVERED, "Delivered")
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.delivered",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "actor_id": actor_id,
            },
        )

        logger.info(f"Order {order_id} marked as DELIVERED")
        return saved_order

    async def cancel_order(
        self,
        order_id: int,
        actor_id: Optional[int] = None,
        reason: Optional[str] = None,
        is_admin: bool = False,
    ) -> Order:
        """
        لغو یک سفارش.

        Args:
            order_id: شناسه سفارش.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).
            reason: دلیل لغو (اختیاری).
            is_admin: آیا لغو توسط ادمین انجام می‌شود (اجازه‌ی لغو بیشتر).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            ValidationError: اگر تغییر وضعیت مجاز نباشد.
            PermissionDeniedError: اگر کاربر مجاز به لغو نباشد.
        """
        order = await self._get_order(order_id)

        # بررسی قابلیت لغو بر اساس نقش
        if not is_admin:
            if order.status not in OrderStatus.CANCELABLE_BY_USER_STATUSES:
                raise PermissionDeniedError(
                    message="شما مجاز به لغو این سفارش نیستید.",
                    context={"order_id": order_id, "status": order.status.value},
                )
        else:
            if order.status not in OrderStatus.CANCELABLE_BY_ADMIN_STATUSES:
                raise ValidationError(
                    message=f"سفارش در وضعیت '{order.status.display_name}' قابل لغو نیست.",
                    context={"order_id": order_id, "status": order.status.value},
                )

        order.cancel(reason or "Cancelled")
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.cancelled",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "actor_id": actor_id,
                "reason": reason,
                "is_admin": is_admin,
            },
        )

        logger.info(f"Order {order_id} cancelled by {'admin' if is_admin else 'user'} {actor_id}")
        return saved_order

    async def refund_order(
        self,
        order_id: int,
        actor_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Order:
        """
        بازگشت وجه سفارش.

        Args:
            order_id: شناسه سفارش.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).
            reason: دلیل بازگشت وجه (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            ValidationError: اگر تغییر وضعیت مجاز نباشد.
        """
        order = await self._get_order(order_id)

        order.refund(reason or "Refund requested")
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.refunded",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "actor_id": actor_id,
                "reason": reason,
            },
        )

        logger.info(f"Order {order_id} refunded by {actor_id}")
        return saved_order

    async def hold_order(
        self,
        order_id: int,
        reason: str,
        actor_id: Optional[int] = None,
    ) -> Order:
        """
        قرار دادن سفارش در حالت در انتظار بررسی.

        Args:
            order_id: شناسه سفارش.
            reason: دلیل نگه‌داری.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.
        """
        order = await self._get_order(order_id)

        order.update_status(OrderStatus.ON_HOLD, reason)
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.on_hold",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "reason": reason,
                "actor_id": actor_id,
            },
        )

        logger.info(f"Order {order_id} put on HOLD: {reason}")
        return saved_order

    async def release_from_hold(
        self,
        order_id: int,
        actor_id: Optional[int] = None,
    ) -> Order:
        """
        رها کردن سفارش از حالت در انتظار بررسی (بازگشت به وضعیت قبلی).

        Args:
            order_id: شناسه سفارش.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            ValidationError: اگر سفارش در حالت ON_HOLD نباشد.
        """
        order = await self._get_order(order_id)

        if order.status != OrderStatus.ON_HOLD:
            raise ValidationError(
                message="فقط سفارشات در وضعیت ON_HOLD قابل آزادسازی هستند.",
                context={"order_id": order_id, "status": order.status.value},
            )

        # بازگشت به وضعیت قبلی (با بررسی تاریخچه)
        previous_status = order.metadata.get("previous_status")
        if previous_status:
            order.update_status(OrderStatus(previous_status), "Released from hold")
        else:
            order.update_status(OrderStatus.PENDING, "Released from hold")

        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.released_from_hold",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "actor_id": actor_id,
            },
        )

        logger.info(f"Order {order_id} released from HOLD")
        return saved_order

    async def update_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        actor_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Order:
        """
        به‌روزرسانی عمومی وضعیت سفارش.

        Args:
            order_id: شناسه سفارش.
            new_status: وضعیت جدید.
            actor_id: شناسه کاربر انجام‌دهنده (اختیاری).
            reason: دلیل تغییر (اختیاری).

        Returns:
            Order: سفارش به‌روزرسانی‌شده.

        Raises:
            ValidationError: اگر تغییر وضعیت مجاز نباشد.
        """
        order = await self._get_order(order_id)

        # بررسی مجاز بودن تغییر وضعیت
        if not order._is_transition_allowed(new_status):
            raise ValidationError(
                message=f"تغییر وضعیت از '{order.status.value}' به '{new_status.value}' مجاز نیست.",
                context={"order_id": order_id, "current": order.status.value, "new": new_status.value},
            )

        order.update_status(new_status, reason)
        saved_order = await self._order_repository.save(order)

        await self._publish_event(
            event_type="order.status_changed",
            event_data={
                "order_id": saved_order.id,
                "order_number": saved_order.order_number,
                "old_status": order.status.value,
                "new_status": new_status.value,
                "actor_id": actor_id,
                "reason": reason,
            },
        )

        logger.info(f"Order {order_id} status changed to {new_status.value} by {actor_id}")
        return saved_order

    async def _get_order(self, order_id: int) -> Order:
        """
        دریافت سفارش با شناسه.

        Args:
            order_id: شناسه سفارش.

        Returns:
            Order: موجودیت سفارش.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
        """
        order = await self._order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id)
        return order

    async def _publish_event(self, event_type: str, event_data: dict) -> None:
        """
        انتشار رویداد در صورت وجود انتشاردهنده.

        Args:
            event_type: نوع رویداد.
            event_data: داده‌های رویداد.
        """
        if self._message_publisher:
            try:
                await self._message_publisher.publish_event(
                    event_type=event_type,
                    event_data=event_data,
                    source="OrderStatusUpdateService",
                )
            except Exception as e:
                logger.error(f"Failed to publish event {event_type}: {e}")