# my_bot_project/src/my_bot/application/services/analytics/user_behavior.py
"""
سرویس تحلیل رفتار کاربر (User Behavior Analytics Service).

این سرویس مسئولیت ثبت، تحلیل و گزارش‌گیری از رفتار کاربران در سیستم را بر عهده دارد.
شامل عملیات‌های ثبت رویدادهای کاربری، محاسبه آمار تعاملات،
تحلیل مسیرهای کاربری و تشخیص الگوهای رفتاری است.
"""

from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher

logger = get_logger(__name__)


class UserBehaviorAnalyticsService:
    """
    سرویس تحلیل رفتار کاربر.

    این کلاس مسئولیت ثبت، تحلیل و گزارش‌گیری از رفتار کاربران را بر عهده دارد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        order_repository: Optional[OrderRepository] = None,
        form_repository: Optional[FormRepository] = None,
        cache: Optional[CacheInterface] = None,
        message_publisher: Optional[MessagePublisher] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس تحلیل رفتار کاربر.

        Args:
            user_repository: ریپازیتوری کاربر.
            order_repository: ریپازیتوری سفارش (اختیاری).
            form_repository: ریپازیتوری فرم (اختیاری).
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
            message_publisher: انتشاردهنده پیام (اختیاری).
        """
        self._user_repository = user_repository
        self._order_repository = order_repository
        self._form_repository = form_repository
        self._cache = cache
        self._message_publisher = message_publisher
        self._cache_ttl = 3600  # 1 ساعت

    async def track_user_activity(
        self,
        user_id: int,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        ثبت یک فعالیت کاربری.

        Args:
            user_id: شناسه کاربر.
            action: نوع فعالیت (مانند 'view_form', 'submit_order', 'click_button').
            metadata: اطلاعات اضافی (اختیاری).
        """
        # به‌روزرسانی زمان آخرین فعالیت کاربر
        await self._user_repository.update_last_activity(user_id)

        # ذخیره در کش برای تحلیل سریع
        if self._cache:
            cache_key = f"user_activity:{user_id}"
            activities = await self._cache.get(cache_key) or []
            if not isinstance(activities, list):
                activities = []

            activities.append({
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            })

            # محدود کردن تعداد فعالیت‌های ذخیره‌شده در کش
            if len(activities) > 1000:
                activities = activities[-1000:]

            await self._cache.set(cache_key, activities, ttl=self._cache_ttl * 24)  # 24 ساعت

        # انتشار رویداد
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="user.activity",
                event_data={
                    "user_id": user_id,
                    "action": action,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata or {},
                },
                source="UserBehaviorAnalyticsService",
            )

        logger.debug(f"User activity tracked: user={user_id}, action={action}")

    async def get_user_activities(
        self,
        user_id: int,
        limit: int = 100,
        action_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت فعالیت‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.
            limit: حداکثر تعداد فعالیت‌ها.
            action_filter: فیلتر بر اساس نوع فعالیت (اختیاری).

        Returns:
            List[Dict[str, Any]]: لیست فعالیت‌ها.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # تلاش از کش
        if self._cache:
            cache_key = f"user_activity:{user_id}"
            activities = await self._cache.get(cache_key) or []
            if isinstance(activities, list):
                if action_filter:
                    activities = [a for a in activities if a.get("action") == action_filter]
                return activities[-limit:]

        # اگر در کش نبود، از دیتابیس یا سرویس‌های دیگر دریافت می‌کنیم
        # در اینجا یک لیست خالی برمی‌گردانیم، در عمل باید از یک سرویس ذخیره‌سازی استفاده کرد
        return []

    async def get_user_behavior_summary(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت خلاصه رفتار کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Dict[str, Any]: خلاصه رفتار شامل:
                - last_activity: آخرین فعالیت
                - total_activities: تعداد کل فعالیت‌ها
                - action_counts: تعداد هر نوع فعالیت
                - engagement_score: امتیاز تعامل (۰ تا ۱۰۰)
                - activity_trend: روند فعالیت (increasing, decreasing, stable)

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        activities = await self.get_user_activities(user_id, limit=1000)

        total_activities = len(activities)
        action_counts = Counter(a.get("action", "unknown") for a in activities)

        # محاسبه امتیاز تعامل
        engagement_score = min(100, total_activities * 2)

        # تحلیل روند فعالیت
        trend = "stable"
        if total_activities > 10:
            recent = len([a for a in activities[-20:] if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(days=7)])
            old = len([a for a in activities[:20] if datetime.fromisoformat(a["timestamp"]) < datetime.now() - timedelta(days=14)])
            if recent > old * 1.5:
                trend = "increasing"
            elif recent < old * 0.5:
                trend = "decreasing"

        # آخرین فعالیت
        last_activity = activities[-1] if activities else None

        return {
            "user_id": user_id,
            "last_activity": last_activity,
            "total_activities": total_activities,
            "action_counts": dict(action_counts),
            "engagement_score": engagement_score,
            "activity_trend": trend,
            "last_activity_time": user.last_activity.isoformat() if user.last_activity else None,
        }

    async def get_user_engagement_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day",  # day, week, month
    ) -> Dict[str, Any]:
        """
        دریافت گزارش تعامل کاربران.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).
            group_by: دسته‌بندی زمانی ('day', 'week', 'month').

        Returns:
            Dict[str, Any]: گزارش تعامل شامل:
                - total_users: تعداد کل کاربران
                - active_users: تعداد کاربران فعال
                - new_users: تعداد کاربران جدید
                - returning_users: تعداد کاربران بازگشتی
                - engagement_by_period: تعامل به‌تفکیک بازه‌ها
                - average_engagement: میانگین تعامل
        """
        # دریافت کاربران
        users = await self._user_repository.get_all(limit=10000)

        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active and not u.is_banned)

        # کاربران جدید در بازه زمانی
        now = datetime.now()
        if not start_date:
            start_date = now - timedelta(days=30)
        if not end_date:
            end_date = now

        new_users = sum(
            1 for u in users
            if u.created_at and start_date <= u.created_at <= end_date
        )

        # کاربران بازگشتی (با فعالیت در بازه زمانی)
        returning_users = sum(
            1 for u in users
            if u.last_activity and start_date <= u.last_activity <= end_date
        )

        # تعامل به‌تفکیک بازه
        engagement_by_period = await self._get_engagement_by_period(start_date, end_date, group_by)

        # میانگین تعامل
        avg_engagement = sum(e["engagement"] for e in engagement_by_period) / len(engagement_by_period) if engagement_by_period else 0

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users,
            "returning_users": returning_users,
            "engagement_by_period": engagement_by_period,
            "average_engagement": avg_engagement,
        }

    async def get_user_journey(
        self,
        user_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        دریافت مسیر کاربری (سفر کاربر در سیستم).

        Args:
            user_id: شناسه کاربر.
            limit: حداکثر تعداد رویدادها.

        Returns:
            List[Dict[str, Any]]: مسیر کاربری شامل دنباله‌ای از فعالیت‌ها.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        activities = await self.get_user_activities(user_id, limit=limit)

        # تحلیل مسیر: یافتن الگوهای تکراری
        actions = [a.get("action", "unknown") for a in activities]
        journey = []

        for i, activity in enumerate(activities):
            # اضافه کردن اطلاعات مسیر
            journey.append({
                "step": i + 1,
                "action": activity.get("action"),
                "timestamp": activity.get("timestamp"),
                "metadata": activity.get("metadata", {}),
                "next_action": actions[i + 1] if i + 1 < len(actions) else None,
            })

        return journey

    async def get_popular_actions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        دریافت محبوب‌ترین فعالیت‌های کاربران.

        Args:
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).
            limit: حداکثر تعداد فعالیت‌ها.

        Returns:
            List[Dict[str, Any]]: لیست فعالیت‌های محبوب با تعداد.
        """
        # دریافت کاربران
        users = await self._user_repository.get_all(limit=10000)

        action_counter = Counter()
        for user in users:
            activities = await self.get_user_activities(user.id, limit=100)
            for activity in activities:
                action = activity.get("action", "unknown")
                # فیلتر بر اساس تاریخ
                if start_date or end_date:
                    try:
                        ts = datetime.fromisoformat(activity.get("timestamp", ""))
                        if start_date and ts < start_date:
                            continue
                        if end_date and ts > end_date:
                            continue
                    except (ValueError, TypeError):
                        pass
                action_counter[action] += 1

        popular = [
            {"action": action, "count": count}
            for action, count in action_counter.most_common(limit)
        ]

        return popular

    async def get_user_retention(
        self,
        start_date: datetime,
        end_date: datetime,
        cohort_period: str = "day",  # day, week, month
    ) -> Dict[str, Any]:
        """
        محاسبه نرخ بازگشت کاربران (Retention Rate).

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            cohort_period: دوره cohort ('day', 'week', 'month').

        Returns:
            Dict[str, Any]: نرخ بازگشت برای هر cohort.
        """
        # دریافت کاربران در بازه زمانی
        users = await self._user_repository.get_all(limit=10000)

        # گروه‌بندی کاربران بر اساس تاریخ ثبت‌نام
        cohorts = defaultdict(list)
        for user in users:
            if not user.created_at or not (start_date <= user.created_at <= end_date):
                continue

            if cohort_period == "day":
                period = user.created_at.date().isoformat()
            elif cohort_period == "week":
                period = user.created_at.isocalendar()[0:2]
            else:  # month
                period = user.created_at.strftime("%Y-%m")

            cohorts[period].append(user)

        # محاسبه نرخ بازگشت
        retention = {}
        for period, cohort_users in cohorts.items():
            if not cohort_users:
                continue

            # کاربرانی که در دوره بعدی بازگشته‌اند
            returned = 0
            for user in cohort_users:
                if user.last_activity and user.last_activity > user.created_at + timedelta(days=1):
                    returned += 1

            retention[period] = {
                "total_users": len(cohort_users),
                "returned_users": returned,
                "retention_rate": (returned / len(cohort_users)) * 100 if cohort_users else 0,
            }

        return {
            "period": cohort_period,
            "cohorts": retention,
        }

    async def get_user_segments(
        self,
        segment_by: str = "activity",  # activity, engagement, level
    ) -> List[Dict[str, Any]]:
        """
        دسته‌بندی کاربران بر اساس معیارهای مختلف.

        Args:
            segment_by: معیار دسته‌بندی ('activity', 'engagement', 'level').

        Returns:
            List[Dict[str, Any]]: دسته‌بندی‌های کاربران.
        """
        users = await self._user_repository.get_all(limit=10000)
        segments = []

        if segment_by == "activity":
            # دسته‌بندی بر اساس میزان فعالیت
            active = []
            inactive = []
            dormant = []

            for user in users:
                if not user.last_activity:
                    dormant.append(user)
                elif user.last_activity > datetime.now() - timedelta(days=7):
                    active.append(user)
                elif user.last_activity > datetime.now() - timedelta(days=30):
                    inactive.append(user)
                else:
                    dormant.append(user)

            segments = [
                {
                    "name": "فعال",
                    "count": len(active),
                    "users": [u.id for u in active[:10]],
                    "percentage": (len(active) / len(users)) * 100 if users else 0,
                },
                {
                    "name": "غیرفعال (۷-۳۰ روز)",
                    "count": len(inactive),
                    "users": [u.id for u in inactive[:10]],
                    "percentage": (len(inactive) / len(users)) * 100 if users else 0,
                },
                {
                    "name": "خوابیده (بیش از ۳۰ روز)",
                    "count": len(dormant),
                    "users": [u.id for u in dormant[:10]],
                    "percentage": (len(dormant) / len(users)) * 100 if users else 0,
                },
            ]

        elif segment_by == "engagement":
            # دسته‌بندی بر اساس امتیاز تعامل
            high = []
            medium = []
            low = []

            for user in users:
                summary = await self.get_user_behavior_summary(user.id)
                score = summary.get("engagement_score", 0)
                if score >= 60:
                    high.append(user)
                elif score >= 30:
                    medium.append(user)
                else:
                    low.append(user)

            segments = [
                {
                    "name": "تعامل بالا",
                    "count": len(high),
                    "users": [u.id for u in high[:10]],
                    "percentage": (len(high) / len(users)) * 100 if users else 0,
                },
                {
                    "name": "تعامل متوسط",
                    "count": len(medium),
                    "users": [u.id for u in medium[:10]],
                    "percentage": (len(medium) / len(users)) * 100 if users else 0,
                },
                {
                    "name": "تعامل پایین",
                    "count": len(low),
                    "users": [u.id for u in low[:10]],
                    "percentage": (len(low) / len(users)) * 100 if users else 0,
                },
            ]

        elif segment_by == "level":
            # دسته‌بندی بر اساس سطح کاربری
            from my_bot.domain.value_objects.user_level import UserLevel

            level_counts = {level.value: 0 for level in UserLevel}
            for user in users:
                if user.level:
                    level_counts[user.level.value] = level_counts.get(user.level.value, 0) + 1

            segments = [
                {
                    "name": level,
                    "count": count,
                    "percentage": (count / len(users)) * 100 if users else 0,
                }
                for level, count in level_counts.items()
            ]

        return segments

    async def get_user_churn_prediction(self, user_id: int) -> Dict[str, Any]:
        """
        پیش‌بینی احتمال ترک سیستم توسط کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Dict[str, Any]: نتایج پیش‌بینی شامل:
                - churn_probability: احتمال ترک (۰ تا ۱)
                - risk_factors: عوامل خطر
                - recommendations: توصیه‌ها

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # عوامل خطر
        risk_factors = []
        risk_score = 0.0

        # ۱. عدم فعالیت
        if not user.last_activity:
            risk_factors.append("بدون فعالیت")
            risk_score += 0.3
        elif (datetime.now() - user.last_activity).days > 30:
            risk_factors.append("عدم فعالیت بیش از ۳۰ روز")
            risk_score += 0.4
        elif (datetime.now() - user.last_activity).days > 15:
            risk_factors.append("عدم فعالیت بیش از ۱۵ روز")
            risk_score += 0.2

        # ۲. تعداد کم سفارشات
        if self._order_repository:
            order_count = await self._order_repository.get_order_count_by_user(user_id)
            if order_count == 0:
                risk_factors.append("بدون سفارش")
                risk_score += 0.2
            elif order_count < 3:
                risk_factors.append("تعداد سفارش کم")
                risk_score += 0.1

        # ۳. عدم تعامل با فرم‌ها
        if self._form_repository:
            # تعداد ارسال فرم‌ها (در صورت وجود متد مناسب)
            # اینجا یک مقدار پیش‌فرض قرار می‌دهیم
            pass

        # ۴. امتیاز پایین
        if user.points < 100:
            risk_factors.append("امتیاز پایین")
            risk_score += 0.1

        # نرمال‌سازی
        churn_probability = min(1.0, risk_score)

        recommendations = []
        if "بدون سفارش" in risk_factors:
            recommendations.append("ارسال پیشنهادات ویژه برای اولین سفارش")
        if "بدون فعالیت" in risk_factors or "عدم فعالیت بیش از ۱۵ روز" in risk_factors:
            recommendations.append("ارسال پیام یادآوری و پیشنهادات جذاب")
        if "امتیاز پایین" in risk_factors:
            recommendations.append("ارائه راه‌های کسب امتیاز بیشتر")

        return {
            "user_id": user_id,
            "churn_probability": churn_probability,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "risk_level": "high" if churn_probability > 0.6 else "medium" if churn_probability > 0.3 else "low",
        }

    async def _get_engagement_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str,
    ) -> List[Dict[str, Any]]:
        """
        دریافت تعامل به‌تفکیک بازه‌ها (داخلی).

        Args:
            start_date: تاریخ شروع.
            end_date: تاریخ پایان.
            group_by: دسته‌بندی ('day', 'week', 'month').

        Returns:
            List[Dict[str, Any]]: تعامل به‌تفکیک بازه.
        """
        periods = []
        current = start_date

        while current <= end_date:
            if group_by == "day":
                period_start = current
                period_end = current + timedelta(days=1)
                key = current.date().isoformat()
            elif group_by == "week":
                period_start = current - timedelta(days=current.weekday())
                period_end = period_start + timedelta(days=7)
                key = f"week_{current.isocalendar()[0]}_{current.isocalendar()[1]}"
            else:  # month
                period_start = current.replace(day=1)
                if current.month == 12:
                    period_end = current.replace(day=1, month=1, year=current.year + 1)
                else:
                    period_end = current.replace(day=1, month=current.month + 1)
                key = current.strftime("%Y-%m")

            # دریافت کاربران فعال در این بازه
            users = await self._user_repository.get_all(limit=10000)
            active_users = sum(
                1 for u in users
                if u.last_activity and period_start <= u.last_activity < period_end
            )

            periods.append({
                "period": key,
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
                "engagement": active_users,
            })

            current = period_end

        return periods

    async def clear_cache(self) -> None:
        """پاک کردن کش فعالیت‌های کاربران."""
        if self._cache:
            await self._cache.delete_pattern("user_activity:*")
            logger.info("User behavior cache cleared.")