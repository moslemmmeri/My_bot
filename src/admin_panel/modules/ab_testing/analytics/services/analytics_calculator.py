# src/admin_panel/modules/analytics/services/analytics_calculator.py
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository

logger = get_logger(__name__)


class AnalyticsCalculator:
    """Service for calculating analytics statistics."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        order_repo: Optional[OrderRepository] = None,
        payment_repo: Optional[PaymentRepository] = None,
    ) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo
        self.payment_repo = payment_repo

    async def get_dashboard_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get main dashboard statistics."""
        try:
            stats = {}

            # User stats
            if self.user_repo:
                stats["total_users"] = await self.user_repo.count()
                stats["new_users"] = await self.user_repo.count_by_date_range(start_date, end_date)

            # Order stats
            if self.order_repo:
                stats["total_orders"] = await self.order_repo.count()
                stats["today_orders"] = await self.order_repo.count_by_date(
                    datetime.now().replace(hour=0, minute=0, second=0)
                )
                stats["pending_orders"] = await self.order_repo.count_by_status("pending")
                stats["paid_orders"] = await self.order_repo.count_by_status("paid")
                stats["shipped_orders"] = await self.order_repo.count_by_status("shipped")
                stats["delivered_orders"] = await self.order_repo.count_by_status("delivered")
                stats["cancelled_orders"] = await self.order_repo.count_by_status("cancelled")
                stats["total_revenue"] = await self.order_repo.sum_total_by_date_range(start_date, end_date)
                stats["today_revenue"] = await self.order_repo.sum_total_by_date(
                    datetime.now().replace(hour=0, minute=0, second=0)
                )

            # Payment stats
            if self.payment_repo:
                stats["successful_payments"] = await self.payment_repo.count_by_status("success")
                stats["failed_payments"] = await self.payment_repo.count_by_status("failed")

            return stats
        except Exception as e:
            logger.error(f"Error calculating dashboard stats: {e}", exc_info=True)
            raise DatabaseError("Failed to calculate dashboard statistics.") from e

    async def get_sales_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed sales report."""
        try:
            report = {}

            if self.order_repo:
                report["total_orders"] = await self.order_repo.count_by_date_range(start_date, end_date)
                report["total_revenue"] = await self.order_repo.sum_total_by_date_range(start_date, end_date)

                # Average order value
                if report["total_orders"] > 0:
                    report["average_order_value"] = report["total_revenue"] / report["total_orders"]
                else:
                    report["average_order_value"] = 0

                # Status breakdown
                report["paid_orders"] = await self.order_repo.count_by_status_and_date_range(
                    "paid", start_date, end_date
                )
                report["shipped_orders"] = await self.order_repo.count_by_status_and_date_range(
                    "shipped", start_date, end_date
                )
                report["delivered_orders"] = await self.order_repo.count_by_status_and_date_range(
                    "delivered", start_date, end_date
                )
                report["cancelled_orders"] = await self.order_repo.count_by_status_and_date_range(
                    "cancelled", start_date, end_date
                )

                # Daily revenue stats
                daily_revenue = await self.order_repo.get_daily_revenue(start_date, end_date)
                if daily_revenue:
                    report["max_daily_revenue"] = max(daily_revenue)
                    report["min_daily_revenue"] = min(daily_revenue)
                else:
                    report["max_daily_revenue"] = 0
                    report["min_daily_revenue"] = 0

            return report
        except Exception as e:
            logger.error(f"Error calculating sales report: {e}", exc_info=True)
            raise DatabaseError("Failed to calculate sales report.") from e

    async def get_user_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed user report."""
        try:
            report = {}

            if self.user_repo:
                report["total_users"] = await self.user_repo.count()
                report["new_users"] = await self.user_repo.count_by_date_range(start_date, end_date)

                # Growth rate
                previous_end = start_date
                previous_start = start_date - (end_date - start_date)
                previous_new = await self.user_repo.count_by_date_range(previous_start, previous_end)
                if previous_new > 0:
                    report["growth_rate"] = ((report["new_users"] - previous_new) / previous_new) * 100
                else:
                    report["growth_rate"] = 0 if report["new_users"] == 0 else 100

                # Activity stats
                report["active_users"] = await self.user_repo.count_active()
                report["inactive_users"] = report["total_users"] - report["active_users"]

                # Level distribution
                report["gold_users"] = await self.user_repo.count_by_level("gold")
                report["silver_users"] = await self.user_repo.count_by_level("silver")
                report["bronze_users"] = await self.user_repo.count_by_level("bronze")
                report["normal_users"] = await self.user_repo.count_by_level("normal")

                # Average points
                report["average_points"] = await self.user_repo.average_points()

            return report
        except Exception as e:
            logger.error(f"Error calculating user report: {e}", exc_info=True)
            raise DatabaseError("Failed to calculate user report.") from e

    async def get_payment_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed payment report."""
        try:
            report = {}

            if self.payment_repo:
                report["successful_payments"] = await self.payment_repo.count_by_status_and_date_range(
                    "success", start_date, end_date
                )
                report["failed_payments"] = await self.payment_repo.count_by_status_and_date_range(
                    "failed", start_date, end_date
                )
                report["total_transactions"] = report["successful_payments"] + report["failed_payments"]

                # Success rate
                if report["total_transactions"] > 0:
                    report["success_rate"] = (report["successful_payments"] / report["total_transactions"]) * 100
                else:
                    report["success_rate"] = 0

                # Amounts
                report["total_successful_amount"] = await self.payment_repo.sum_amount_by_status_and_date_range(
                    "success", start_date, end_date
                )
                report["total_failed_amount"] = await self.payment_repo.sum_amount_by_status_and_date_range(
                    "failed", start_date, end_date
                )

                # Gateway breakdown
                gateways = await self.payment_repo.get_gateway_breakdown(start_date, end_date)
                report["gateway_breakdown"] = gateways

            return report
        except Exception as e:
            logger.error(f"Error calculating payment report: {e}", exc_info=True)
            raise DatabaseError("Failed to calculate payment report.") from e

    async def get_behavior_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get user behavior analytics."""
        try:
            report = {}

            if self.user_repo and self.order_repo:
                # User engagement
                report["total_users"] = await self.user_repo.count()
                report["users_with_orders"] = await self.user_repo.count_with_orders()
                report["conversion_rate"] = (
                    (report["users_with_orders"] / report["total_users"]) * 100
                    if report["total_users"] > 0 else 0
                )

                # Order frequency
                total_orders = await self.order_repo.count_by_date_range(start_date, end_date)
                report["orders_per_user"] = (
                    total_orders / report["users_with_orders"]
                    if report["users_with_orders"] > 0 else 0
                )

                # Return rate
                returning_users = await self.user_repo.count_returning_users(start_date, end_date)
                report["returning_users"] = returning_users
                report["return_rate"] = (
                    (returning_users / report["users_with_orders"]) * 100
                    if report["users_with_orders"] > 0 else 0
                )

                # Peak activity times
                report["peak_hours"] = await self.order_repo.get_peak_hours(start_date, end_date)

            return report
        except Exception as e:
            logger.error(f"Error calculating behavior report: {e}", exc_info=True)
            raise DatabaseError("Failed to calculate behavior report.") from e

    async def get_order_statistics(self) -> Dict[str, Any]:
        """Get comprehensive order statistics."""
        try:
            stats = {}

            if self.order_repo:
                stats["total"] = await self.order_repo.count()
                stats["by_status"] = {
                    "pending": await self.order_repo.count_by_status("pending"),
                    "paid": await self.order_repo.count_by_status("paid"),
                    "shipped": await self.order_repo.count_by_status("shipped"),
                    "delivered": await self.order_repo.count_by_status("delivered"),
                    "cancelled": await self.order_repo.count_by_status("cancelled"),
                    "failed": await self.order_repo.count_by_status("failed"),
                }
                stats["total_revenue"] = await self.order_repo.sum_total_all()
                stats["average_order_value"] = (
                    stats["total_revenue"] / stats["total"]
                    if stats["total"] > 0 else 0
                )

            return stats
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}", exc_info=True)
            raise DatabaseError("Failed to get order statistics.") from e