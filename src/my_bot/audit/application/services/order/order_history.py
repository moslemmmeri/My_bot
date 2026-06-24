# my_bot_project/src/my_bot/application/services/order/order_history.py
"""
سرویس تاریخچه سفارشات (Order History Service).

این سرویس مسئولیت دریافت و مدیریت تاریخچه سفارشات کاربران را بر عهده دارد.
شامل عملیات‌های دریافت لیست سفارشات، فیلتر کردن بر اساس وضعیت،
دریافت جزئیات سفارش و دریافت آمار سفارشات کاربر است.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from my_bot.application.dtos.order_dto import OrderResponseDTO
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.not_found_errors import OrderNotFoundError, UserNotFoundError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.entities.order import Order

logger = get_logger(__name__)


class OrderHistoryService:
    """
    سرویس تاریخچه سفارشات.

    این کلاس مسئولیت دریافت و مدیریت تاریخچه سفارشات کاربران را بر عهده دارد.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
    ) -> None:
        """
        مقداردهی اولیه سرویس تاریخچه سفارشات.

        Args:
            order_repository: ریپازیتوری سفارش.
            user_repository: ریپازیتوری کاربر.
        """
        self._order_repository = order_repository
        self._user_repository = user_repository

    async def get_user_orders(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[OrderStatus] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[OrderResponseDTO]:
        """
        دریافت لیست سفارشات یک کاربر با فیلترهای اختیاری.

        Args:
            user_id: شناسه کاربر.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.
            status: فیلتر بر اساس وضعیت (اختیاری).
            order_by: نام ستون برای مرتب‌سازی.
            order_desc: True برای مرتب‌سازی نزولی، False برای صعودی.

        Returns:
            List[OrderResponseDTO]: لیست سفارشات کاربر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        # بررسی وجود کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت سفارشات
        if status:
            orders = await self._order_repository.get_by_status(
                status=status,
                skip=skip,
                limit=limit,
            )
            # فیلتر بر اساس user_id (چون get_by_status فیلتر کاربر ندارد)
            orders = [o for o in orders if o.user_id == user_id]
        else:
            orders = await self._order_repository.get_by_user_id(
                user_id=user_id,
                skip=skip,
                limit=limit,
            )

        return [OrderResponseDTO.from_entity(order) for order in orders]

    async def get_order_details(
        self,
        order_id: int,
        user_id: Optional[int] = None,
    ) -> OrderResponseDTO:
        """
        دریافت جزئیات کامل یک سفارش.

        Args:
            order_id: شناسه سفارش.
            user_id: شناسه کاربر (اختیاری، برای بررسی دسترسی).

        Returns:
            OrderResponseDTO: اطلاعات کامل سفارش.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز به مشاهده سفارش نباشد.
        """
        order = await self._order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id)

        # بررسی دسترسی (اگر user_id ارائه شده باشد)
        if user_id is not None and order.user_id != user_id:
            # می‌توان بررسی کرد که کاربر ادمین است یا خیر
            from my_bot.core.exceptions.permission_errors import PermissionDeniedError
            raise PermissionDeniedError(
                message="شما مجاز به مشاهده این سفارش نیستید.",
                context={"order_id": order_id, "user_id": user_id},
            )

        return OrderResponseDTO.from_entity(order)

    async def get_order_by_number(
        self,
        order_number: str,
        user_id: Optional[int] = None,
    ) -> OrderResponseDTO:
        """
        دریافت سفارش با شماره سفارش.

        Args:
            order_number: شماره سفارش.
            user_id: شناسه کاربر (اختیاری، برای بررسی دسترسی).

        Returns:
            OrderResponseDTO: اطلاعات کامل سفارش.

        Raises:
            OrderNotFoundError: اگر سفارش وجود نداشته باشد.
            PermissionDeniedError: اگر کاربر مجاز به مشاهده سفارش نباشد.
        """
        order = await self._order_repository.get_by_order_number(order_number)
        if not order:
            raise OrderNotFoundError(order_id=order_number)

        # بررسی دسترسی
        if user_id is not None and order.user_id != user_id:
            from my_bot.core.exceptions.permission_errors import PermissionDeniedError
            raise PermissionDeniedError(
                message="شما مجاز به مشاهده این سفارش نیستید.",
                context={"order_number": order_number, "user_id": user_id},
            )

        return OrderResponseDTO.from_entity(order)

    async def get_order_summary(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت خلاصه‌ای از سفارشات کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Dict[str, Any]: خلاصه سفارشات شامل:
                - total_orders: تعداد کل سفارشات
                - orders_by_status: تعداد سفارشات به‌تفکیک وضعیت
                - last_order: آخرین سفارش (اختیاری)
                - total_spent: مجموع مبلغ پرداختی

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت تمام سفارشات کاربر (با محدودیت بالا)
        orders = await self._order_repository.get_by_user_id(
            user_id=user_id,
            skip=0,
            limit=1000,
        )

        # محاسبه آمار
        total_orders = len(orders)
        orders_by_status = {status.value: 0 for status in OrderStatus}
        total_spent = 0
        last_order = None

        for order in orders:
            status_key = order.status.value
            orders_by_status[status_key] = orders_by_status.get(status_key, 0) + 1

            # جمع مبلغ سفارشات موفق
            if order.status.is_paid():
                total_spent += order.total_amount.amount

            # آخرین سفارش
            if last_order is None or order.created_at > last_order.created_at:
                last_order = order

        return {
            "total_orders": total_orders,
            "orders_by_status": orders_by_status,
            "last_order": OrderResponseDTO.from_entity(last_order) if last_order else None,
            "total_spent": total_spent,
        }

    async def get_orders_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OrderResponseDTO]:
        """
        دریافت سفارشات کاربر در بازه زمانی مشخص.

        Args:
            user_id: شناسه کاربر.
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[OrderResponseDTO]: لیست سفارشات در بازه زمانی.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # دریافت سفارشات در بازه زمانی
        orders = await self._order_repository.get_orders_by_date_range(
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )

        # فیلتر بر اساس user_id
        orders = [o for o in orders if o.user_id == user_id]

        return [OrderResponseDTO.from_entity(order) for order in orders]

    async def get_recent_orders(
        self,
        user_id: int,
        limit: int = 5,
    ) -> List[OrderResponseDTO]:
        """
        دریافت آخرین سفارشات کاربر.

        Args:
            user_id: شناسه کاربر.
            limit: حداکثر تعداد سفارشات.

        Returns:
            List[OrderResponseDTO]: لیست آخرین سفارشات.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        orders = await self._order_repository.get_by_user_id(
            user_id=user_id,
            skip=0,
            limit=limit,
        )
        return [OrderResponseDTO.from_entity(order) for order in orders]

    async def get_pending_orders(
        self,
        user_id: int,
        older_than_minutes: Optional[int] = None,
    ) -> List[OrderResponseDTO]:
        """
        دریافت سفارشات در انتظار پرداخت کاربر.

        Args:
            user_id: شناسه کاربر.
            older_than_minutes: سفارشات قدیمی‌تر از این دقیقه (اختیاری).

        Returns:
            List[OrderResponseDTO]: لیست سفارشات در انتظار پرداخت.
        """
        # دریافت سفارشات در انتظار پرداخت
        orders = await self._order_repository.get_pending_orders(
            older_than_minutes=older_than_minutes,
            skip=0,
            limit=100,
        )

        # فیلتر بر اساس user_id
        orders = [o for o in orders if o.user_id == user_id]

        return [OrderResponseDTO.from_entity(order) for order in orders]

    async def get_orders_needing_action(
        self,
        user_id: int,
    ) -> List[OrderResponseDTO]:
        """
        دریافت سفارشاتی که نیاز به اقدام دارند (وضعیت‌های PENDING, ON_HOLD).

        Args:
            user_id: شناسه کاربر.

        Returns:
            List[OrderResponseDTO]: لیست سفارشات نیازمند اقدام.
        """
        orders = await self._order_repository.get_orders_needing_action(
            skip=0,
            limit=100,
        )

        # فیلتر بر اساس user_id
        orders = [o for o in orders if o.user_id == user_id]

        return [OrderResponseDTO.from_entity(order) for order in orders]

    async def count_user_orders(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
    ) -> int:
        """
        شمارش تعداد سفارشات کاربر.

        Args:
            user_id: شناسه کاربر.
            status: فیلتر بر اساس وضعیت (اختیاری).

        Returns:
            int: تعداد سفارشات.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # از ریپازیتوری شمارش می‌کنیم
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status.value

        return await self._order_repository.count(filters=filters)

    async def get_orders_summary_by_status(
        self,
        user_id: int,
    ) -> Dict[str, int]:
        """
        دریافت تعداد سفارشات کاربر به‌تفکیک وضعیت.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Dict[str, int]: دیکشنری با کلید وضعیت و مقدار تعداد.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        orders = await self._order_repository.get_by_user_id(
            user_id=user_id,
            skip=0,
            limit=10000,
        )

        summary = {}
        for status in OrderStatus:
            count = sum(1 for o in orders if o.status == status)
            summary[status.value] = count

        return summary