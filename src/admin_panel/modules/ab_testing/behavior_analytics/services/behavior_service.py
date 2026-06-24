# src/admin_panel/modules/behavior_analytics/services/behavior_service.py
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from my_bot.core.exceptions import DatabaseError, NotFoundError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.behavior_repository import BehaviorRepository

logger = get_logger(__name__)


class BehaviorAnalyticsService:
    """Service for analyzing user behavior."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        order_repo: Optional[OrderRepository] = None,
        behavior_repo: Optional[BehaviorRepository] = None,
    ) -> None:
        self.user_repo = user_repo
        self.order_repo = order_repo
        self.behavior_repo = behavior_repo

    async def get_behavior_stats(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get behavior statistics for a date range."""
        try:
            stats = {}

            # User activity
            if self.user_repo:
                stats["daily_active_users"] = await self.user_repo.count_active_in_range(
                    start_date, end_date, "daily"
                )
                stats["weekly_active_users"] = await self.user_repo.count_active_in_range(
                    start_date, end_date, "weekly"
                )
                stats["monthly_active_users"] = await self.user_repo.count_active_in_range(
                    start_date, end_date, "monthly"
                )

            # Sessions
            if self.behavior_repo:
                stats["avg_daily_sessions"] = await self.behavior_repo.get_avg_daily_sessions(
                    start_date, end_date
                )
                stats["avg_session_duration"] = await self.behavior_repo.get_avg_session_duration(
                    start_date, end_date
                )
                stats["return_rate"] = await self.behavior_repo.get_return_rate(
                    start_date, end_date
                )

            # Conversions
            if self.order_repo:
                total_users = await self.user_repo.count() if self.user_repo else 0
                users_with_orders = await self.user_repo.count_with_orders() if self.user_repo else 0
                stats["conversion_rate"] = (
                    (users_with_orders / total_users * 100) if total_users > 0 else 0
                )
                stats["avg_time_to_conversion"] = await self.order_repo.get_avg_time_to_first_order()

            # Top paths
            if self.behavior_repo:
                stats["top_paths"] = await self.behavior_repo.get_top_paths(
                    start_date, end_date, limit=5
                )

            return stats
        except Exception as e:
            logger.error(f"Error getting behavior stats: {e}", exc_info=True)
            raise DatabaseError("Failed to get behavior statistics.") from e

    async def get_user_journey(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the journey of a specific user."""
        try:
            if not self.behavior_repo:
                raise DatabaseError("Behavior repository not available")

            user = await self.user_repo.find_by_id(user_id) if self.user_repo else None
            if not user:
                raise NotFoundError(f"User {user_id} not found.")

            steps = await self.behavior_repo.get_user_steps(user_id)

            return {
                "user_id": user_id,
                "user_name": user.username if user else "نامشخص",
                "steps": [
                    {
                        "name": step.get("name", f"مرحله {idx + 1}"),
                        "duration": step.get("duration", 0),
                        "timestamp": step.get("timestamp"),
                    }
                    for idx, step in enumerate(steps)
                ],
            }
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting user journey for {user_id}: {e}", exc_info=True)
            raise DatabaseError("Failed to get user journey.") from e

    async def get_overall_journey(self) -> Dict[str, Any]:
        """Get overall user journey analysis."""
        try:
            if not self.behavior_repo:
                raise DatabaseError("Behavior repository not available")

            common_paths = await self.behavior_repo.get_common_paths(limit=10)
            avg_duration = await self.behavior_repo.get_avg_journey_duration()
            exit_points = await self.behavior_repo.get_exit_points(limit=5)

            return {
                "common_paths": [
                    {"path": p.get("path", "نامشخص"), "count": p.get("count", 0)}
                    for p in common_paths
                ],
                "avg_journey_duration": avg_duration / 60 if avg_duration else 0,  # Convert to minutes
                "exit_points": [p.get("name", "نامشخص") for p in exit_points],
            }
        except Exception as e:
            logger.error(f"Error getting overall journey: {e}", exc_info=True)
            raise DatabaseError("Failed to get overall journey.") from e

    async def get_full_report(self) -> Dict[str, Any]:
        """Get a comprehensive behavior report."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            report = {
                "generated_at": datetime.now().isoformat(),
            }

            # User stats
            if self.user_repo:
                total_users = await self.user_repo.count()
                new_users = await self.user_repo.count_by_date_range(start_date, end_date)
                report["total_users"] = total_users
                report["new_users"] = new_users
                report["growth_rate"] = (
                    (new_users / (total_users - new_users) * 100) if total_users > new_users else 0
                )

            # Interactions
            if self.behavior_repo:
                total_interactions = await self.behavior_repo.count_interactions(start_date, end_date)
                avg_daily = await self.behavior_repo.get_avg_daily_interactions(start_date, end_date)
                peak_activity = await self.behavior_repo.get_peak_activity_time(start_date, end_date)
                report["total_interactions"] = total_interactions
                report["avg_daily_interactions"] = avg_daily
                report["peak_activity"] = peak_activity

            # Retention and churn
            if self.user_repo:
                retention = await self.user_repo.get_retention_rate()
                churn = await self.user_repo.get_churn_rate()
                report["retention_rate"] = retention
                report["churn_rate"] = churn

            # NPS (Net Promoter Score)
            if self.behavior_repo:
                report["nps"] = await self.behavior_repo.get_nps()

            # Recommendations
            report["recommendations"] = await self._generate_recommendations(report)

            return report
        except Exception as e:
            logger.error(f"Error getting full report: {e}", exc_info=True)
            raise DatabaseError("Failed to get full report.") from e

    async def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on behavior data."""
        recommendations = []

        retention = report.get("retention_rate", 0)
        if retention < 30:
            recommendations.append("نرخ ماندگاری پایین است. پیشنهاد می‌شود برنامه وفاداری کاربران تقویت شود.")

        churn = report.get("churn_rate", 0)
        if churn > 20:
            recommendations.append("نرخ ریزش بالا است. بررسی دلایل خروج کاربران توصیه می‌شود.")

        conversion = report.get("conversion_rate", 0)
        if conversion < 10:
            recommendations.append("نرخ تبدیل پایین است. بهینه‌سازی مسیر خرید و کاهش مراحل ثبت سفارش پیشنهاد می‌شود.")

        nps = report.get("nps", 0)
        if nps < 30:
            recommendations.append("امتیاز خالص ترویج (NPS) پایین است. بهبود کیفیت خدمات و محصولات توصیه می‌شود.")

        if not recommendations:
            recommendations.append("همه شاخص‌ها در وضعیت مطلوب قرار دارند. ادامه روند فعلی توصیه می‌شود.")

        return recommendations

    async def export_data(self, format_type: str) -> Optional[Dict[str, Any]]:
        """Export behavior data in specified format."""
        try:
            if format_type not in ["pdf", "excel"]:
                raise ValidationError(f"Invalid export format: {format_type}")

            # In a real implementation, generate the file
            # For now, return metadata
            return {
                "format": format_type,
                "filename": f"behavior_report_{datetime.now().strftime('%Y%m%d')}.{format_type}",
                "size": 1024,  # Placeholder
                "generated_at": datetime.now().isoformat(),
            }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error exporting behavior data: {e}", exc_info=True)
            raise DatabaseError("Failed to export behavior data.") from e

    async def get_behavior_summary(self) -> Dict[str, Any]:
        """Get a quick summary of user behavior (for dashboard)."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            summary = {}

            if self.user_repo:
                summary["total_users"] = await self.user_repo.count()
                summary["active_users"] = await self.user_repo.count_active_in_range(
                    start_date, end_date, "daily"
                )

            if self.behavior_repo:
                summary["total_interactions"] = await self.behavior_repo.count_interactions(
                    start_date, end_date
                )
                summary["avg_daily"] = await self.behavior_repo.get_avg_daily_interactions(
                    start_date, end_date
                )

            if self.order_repo:
                summary["total_orders"] = await self.order_repo.count()
                summary["avg_order_value"] = await self.order_repo.get_avg_order_value()

            return summary
        except Exception as e:
            logger.error(f"Error getting behavior summary: {e}", exc_info=True)
            raise DatabaseError("Failed to get behavior summary.") from e