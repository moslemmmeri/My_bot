# my_bot_project/src/my_bot/application/services/analytics/order_statistics.py
"""
سرویس آمار و تحلیل سفارشات (Order Statistics Service).

این سرویس مسئولیت محاسبه آمار و تحلیل‌های مربوط به سفارشات
در سیستم را بر عهده دارد. شامل محاسبه درآمد، تعداد سفارشات،
میانگین مبلغ، تحلیل روند و گزارش‌های دوره‌ای است.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple

from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class OrderStatisticsService:
    """
    سرویس آمار و تحلیل سفارشات.

    این کلاس مسئولیت محاسبه آمار و تحلیل‌های مربوط به سفارشات را بر عهده دارد.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        payment_repository: Optional[PaymentRepository] = None,
        user_repository: Optional[UserRepository] = None,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس آمار سفارشات.

        Args:
            order_repository: ریپازیتوری سفارش.
            payment_repository: ریپازیتوری پرداخت (اختیاری).
            user_repository: ریپازیتوری کاربر (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._order_repository = order_repository
        self._payment_repository = payment_repository
        self._user_repository = user_repository
        self._cache = cache
        self._cache_ttl = 3600  # 1 ساعت

    async def get_dashboard_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت آمار کلی داشبورد.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: آمار کلی شامل:
                - total_orders: تعداد کل سفارشات
                - total_revenue: مجموع درآمد
                - average_order_value: میانگین مبلغ هر سفارش
                - orders_by_status: تعداد سفارشات به‌تفکیک وضعیت
                - revenue_today: درآمد امروز
                - revenue_this_week: درآمد این هفته
                - revenue_this_month: درآمد این ماه
                - orders_today: تعداد سفارشات امروز
                - orders_this_week: تعداد سفارشات این هفته
                - orders_this_month: تعداد سفارشات این ماه
        """
        # بررسی کش
        cache_key = f"order_stats_dashboard:{start_date}:{end_date}"
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                return cached

        # دریافت آمار از ریپازیتوری
        stats = await self._order_repository.get_statistics(
            start_date=start_date,
            end_date=end_date,
        )

        # محاسبه آمار تکمیلی
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # دریافت درآمد در بازه‌های زمانی
        revenue_today = await self._payment_repository.get_total_amount_by_date_range(
            start_date=today_start,
            end_date=now,
        ) if self._payment_repository else Money(Decimal("0"), "IRR")

        revenue_this_week = await self._payment_repository.get_total_amount_by_date_range(
            start_date=week_start,
            end_date=now,
        ) if self._payment_repository else Money(Decimal("0"), "IRR")

        revenue_this_month = await self._payment_repository.get_total_amount_by_date_range(
            start_date=month_start,
            end_date=now,
        ) if self._payment_repository else Money(Decimal("0"), "IRR")

        # دریافت تعداد سفارشات در بازه‌های زمانی
        orders_today = await self._order_repository.count(
            filters={"created_at_gte": today_start, "created_at_lte": now}
        )
        orders_this_week = await self._order_repository.count(
            filters={"created_at_gte": week_start, "created_at_lte": now}
        )
        orders_this_month = await self._order_repository.count(
            filters={"created_at_gte": month_start, "created_at_lte": now}
        )

        # مجموع درآمد
        total_revenue = stats.get("total_revenue", 0)

        result = {
            "total_orders": stats.get("total_orders", 0),
            "total_revenue": total_revenue,
            "average_order_value": stats.get("average_order_value", 0),
            "orders_by_status": stats.get("orders_by_status", {}),
            "revenue_today": revenue_today.amount if revenue_today else 0,
            "revenue_this_week": revenue_this_week.amount if revenue_this_week else 0,
            "revenue_this_month": revenue_this_month.amount if revenue_this_month else 0,
            "orders_today": orders_today,
            "orders_this_week": orders_this_week,
            "orders_this_month": orders_this_month,
            "timestamp": now.isoformat(),
        }

        # ذخیره در کش
        if self._cache:
            await self._cache.set(cache_key, result, ttl=self._cache_ttl)

        return result

    async def get_revenue_report(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "day",
    ) -> List[Dict[str, Any]]:
        """
        دریافت گزارش درآمد به‌تفکیک بازه زمانی.

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            group_by: دسته‌بندی بر اساس ('day', 'week', 'month').

        Returns:
            List[Dict[str, Any]]: لیست گزارش‌های درآمد.

        Raises:
            ValidationError: اگر بازه زمانی نامعتبر باشد.
        """
        if start_date >= end_date:
            raise ValidationError(
                message="تاریخ شروع باید قبل از تاریخ پایان باشد.",
                context={"start_date": start_date, "end_date": end_date},
            )

        if group_by not in ("day", "week", "month"):
            raise ValidationError(
                message=f"دسته‌بندی '{group_by}' نامعتبر است.",
                context={"group_by": group_by, "valid_values": ["day", "week", "month"]},
            )

        # دریافت درآمد از ریپازیتوری
        revenue_data = await self._order_repository.get_revenue_by_date(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )

        return revenue_data

    async def get_top_products(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت محصولات پرفروش.

        Args:
            limit: حداکثر تعداد محصولات.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            List[Dict[str, Any]]: لیست محصولات پرفروش.
        """
        top_products = await self._order_repository.get_top_products(
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )
        return top_products

    async def get_customer_statistics(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت آمار یک مشتری خاص.

        Args:
            user_id: شناسه کاربر.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: آمار مشتری شامل:
                - total_orders: تعداد کل سفارشات
                - total_spent: مجموع پرداخت‌ها
                - average_order_value: میانگین مبلغ هر سفارش
                - last_order_date: تاریخ آخرین سفارش
                - first_order_date: تاریخ اولین سفارش
                - favorite_category: دسته‌بندی محبوب (در صورت وجود)
        """
        # دریافت سفارشات کاربر
        orders = await self._order_repository.get_by_user_id(
            user_id=user_id,
            skip=0,
            limit=10000,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            filtered = []
            for order in orders:
                if start_date and order.created_at < start_date:
                    continue
                if end_date and order.created_at > end_date:
                    continue
                filtered.append(order)
            orders = filtered

        total_orders = len(orders)

        if total_orders == 0:
            return {
                "user_id": user_id,
                "total_orders": 0,
                "total_spent": 0,
                "average_order_value": 0,
                "last_order_date": None,
                "first_order_date": None,
                "favorite_category": None,
            }

        # محاسبه مجموع پرداخت‌ها
        total_spent = sum(o.total_amount.amount for o in orders if o.status.is_paid())
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0

        # تاریخ اولین و آخرین سفارش
        first_order = min(orders, key=lambda o: o.created_at)
        last_order = max(orders, key=lambda o: o.created_at)

        # دسته‌بندی محبوب (در صورت وجود)
        favorite_category = None
        if hasattr(self, "_get_favorite_category"):
            favorite_category = await self._get_favorite_category(user_id)

        return {
            "user_id": user_id,
            "total_orders": total_orders,
            "total_spent": total_spent,
            "average_order_value": avg_order_value,
            "last_order_date": last_order.created_at.isoformat() if last_order.created_at else None,
            "first_order_date": first_order.created_at.isoformat() if first_order.created_at else None,
            "favorite_category": favorite_category,
        }

    async def get_customer_segmentation(self) -> Dict[str, Any]:
        """
        دریافت تقسیم‌بندی مشتریان بر اساس رفتار خرید.

        Returns:
            Dict[str, Any]: تقسیم‌بندی مشتریان شامل:
                - new_customers: مشتریان جدید (کمتر از یک ماه)
                - returning_customers: مشتریان بازگشتی
                - loyal_customers: مشتریان وفادار (بیش از ۵ خرید)
                - high_spenders: مشتریان با خرید بالا
                - inactive_customers: مشتریان غیرفعال (بیش از ۳ ماه)
        """
        result = {
            "new_customers": 0,
            "returning_customers": 0,
            "loyal_customers": 0,
            "high_spenders": 0,
            "inactive_customers": 0,
        }

        if not self._user_repository:
            logger.warning("User repository not available for customer segmentation.")
            return result

        # دریافت تمام کاربران
        users = await self._user_repository.get_all(skip=0, limit=10000)
        now = datetime.now()
        one_month_ago = now - timedelta(days=30)
        three_months_ago = now - timedelta(days=90)

        for user in users:
            if not user.id:
                continue

            # دریافت سفارشات کاربر
            orders = await self._order_repository.get_by_user_id(
                user_id=user.id,
                skip=0,
                limit=10000,
            )

            total_orders = len(orders)
            total_spent = sum(o.total_amount.amount for o in orders if o.status.is_paid())

            # تعیین دسته‌بندی
            is_new = user.created_at >= one_month_ago if user.created_at else False
            has_order = total_orders > 0
            is_loyal = total_orders >= 5
            is_high_spender = total_spent > 500000  # ۵۰۰,۰۰۰ تومان

            # آخرین فعالیت
            last_order = max(orders, key=lambda o: o.created_at) if orders else None
            last_activity = last_order.created_at if last_order else user.last_activity or user.created_at
            is_inactive = last_activity and last_activity < three_months_ago if last_activity else True

            if is_new and has_order:
                result["new_customers"] += 1
            elif is_loyal and is_high_spender:
                result["loyal_customers"] += 1
            elif is_high_spender:
                result["high_spenders"] += 1
            elif has_order:
                result["returning_customers"] += 1
            elif is_inactive:
                result["inactive_customers"] += 1

        return result

    async def get_order_forecast(
        self,
        days_ahead: int = 30,
    ) -> Dict[str, Any]:
        """
        پیش‌بینی تعداد و درآمد سفارشات برای روزهای آینده.

        Args:
            days_ahead: تعداد روزهای آینده برای پیش‌بینی.

        Returns:
            Dict[str, Any]: پیش‌بینی شامل:
                - predicted_orders: تعداد سفارشات پیش‌بینی‌شده
                - predicted_revenue: درآمد پیش‌بینی‌شده
                - confidence_interval: فاصله اطمینان
                - based_on: تعداد روزهای استفاده‌شده برای پیش‌بینی
        """
        # دریافت سفارشات ۹۰ روز گذشته
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        orders = await self._order_repository.get_orders_by_date_range(
            start_date=start_date,
            end_date=end_date,
            skip=0,
            limit=10000,
        )

        # محاسبه میانگین روزانه
        total_orders = len(orders)
        daily_average = total_orders / 90 if total_orders > 0 else 0

        # محاسبه میانگین درآمد روزانه
        total_revenue = sum(o.total_amount.amount for o in orders if o.status.is_paid())
        daily_revenue_avg = total_revenue / 90 if total_revenue > 0 else 0

        # پیش‌بینی
        predicted_orders = daily_average * days_ahead
        predicted_revenue = daily_revenue_avg * days_ahead

        # فاصله اطمینان (ساده: ۲۰٪ نوسان)
        confidence_interval = {
            "lower": predicted_orders * 0.8,
            "upper": predicted_orders * 1.2,
            "revenue_lower": predicted_revenue * 0.8,
            "revenue_upper": predicted_revenue * 1.2,
        }

        return {
            "predicted_orders": round(predicted_orders, 2),
            "predicted_revenue": round(predicted_revenue, 2),
            "confidence_interval": confidence_interval,
            "based_on": {
                "total_orders": total_orders,
                "days_analyzed": 90,
                "daily_average": round(daily_average, 2),
                "daily_revenue_avg": round(daily_revenue_avg, 2),
            },
            "forecast_period_days": days_ahead,
        }

    async def get_cancellation_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        محاسبه نرخ لغو سفارشات.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: نرخ لغو شامل:
                - total_orders: تعداد کل سفارشات
                - cancelled_orders: تعداد سفارشات لغو‌شده
                - cancellation_rate: نرخ لغو (درصد)
                - refunded_orders: تعداد سفارشات بازگشت‌وجه
                - refund_rate: نرخ بازگشت وجه (درصد)
                - cancellation_by_reason: لغو به‌تفکیک دلیل (در صورت وجود)
        """
        # دریافت سفارشات در بازه زمانی
        if start_date and end_date:
            orders = await self._order_repository.get_orders_by_date_range(
                start_date=start_date,
                end_date=end_date,
                skip=0,
                limit=10000,
            )
        else:
            # دریافت تمام سفارشات
            orders = await self._order_repository.get_all(skip=0, limit=10000)

        total_orders = len(orders)
        cancelled_orders = sum(1 for o in orders if o.status == OrderStatus.CANCELED)
        refunded_orders = sum(1 for o in orders if o.status == OrderStatus.REFUNDED)

        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        refund_rate = (refunded_orders / total_orders * 100) if total_orders > 0 else 0

        return {
            "total_orders": total_orders,
            "cancelled_orders": cancelled_orders,
            "cancellation_rate": round(cancellation_rate, 2),
            "refunded_orders": refunded_orders,
            "refund_rate": round(refund_rate, 2),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    async def clear_cache(self) -> None:
        """پاک کردن کش آمار سفارشات."""
        if self._cache:
            await self._cache.delete_pattern("order_stats:*")
            logger.info("Order statistics cache cleared.")