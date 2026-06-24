# my_bot_project/src/my_bot/application/services/broadcast/broadcast_filter.py
"""
سرویس فیلتر کاربران برای ارسال گروهی (Broadcast Filter Service).

این سرویس مسئولیت فیلتر کردن و انتخاب کاربران هدف برای ارسال پیام‌های گروهی
را بر عهده دارد. شامل عملیات‌های فیلتر بر اساس معیارهای مختلف،
اعتبارسنجی فیلترها و محاسبه تعداد کاربران هدف است.
"""

from typing import Optional, List, Dict, Any, Set
from datetime import datetime

from my_bot.application.dtos.broadcast_dto import BroadcastFilterDTO
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.broadcast_errors import BroadcastFilterError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface

logger = get_logger(__name__)


class BroadcastFilterService:
    """
    سرویس فیلتر کاربران برای ارسال گروهی.

    این کلاس مسئولیت فیلتر کردن و انتخاب کاربران هدف برای ارسال پیام‌های گروهی
    را بر عهده دارد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس فیلتر.

        Args:
            user_repository: ریپازیتوری کاربر.
            cache: کش برای ذخیره‌سازی موقت نتایج فیلتر (اختیاری).
        """
        self._user_repository = user_repository
        self._cache = cache
        self._cache_ttl = 300  # 5 دقیقه

    async def get_target_users(
        self,
        filter_data: BroadcastFilterDTO,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[int]:
        """
        دریافت لیست کاربران هدف بر اساس فیلترها.

        Args:
            filter_data: داده‌های فیلتر (DTO).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[int]: لیست شناسه‌های کاربران هدف.

        Raises:
            BroadcastFilterError: در صورت بروز خطا در فیلتر.
            ValidationError: اگر فیلترها نامعتبر باشند.
        """
        # اعتبارسنجی فیلترها
        self._validate_filters(filter_data)

        # ایجاد کلید کش (برای نتایج فیلتر)
        cache_key = self._generate_cache_key(filter_data, skip, limit)

        # بررسی کش
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                logger.debug(f"Returning cached filter results for key: {cache_key}")
                return cached

        try:
            # دریافت کاربران هدف
            target_users = await self._apply_filters(filter_data, skip, limit)

            # ذخیره در کش
            if self._cache:
                await self._cache.set(
                    cache_key,
                    target_users,
                    ttl=self._cache_ttl,
                )

            logger.info(f"Filter applied: found {len(target_users)} target users")
            return target_users

        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            raise BroadcastFilterError(
                broadcast_id="",
                filter_criteria=filter_data.to_dict(),
                reason=str(e),
            )

    async def count_target_users(
        self,
        filter_data: BroadcastFilterDTO,
    ) -> int:
        """
        شمارش تعداد کاربران هدف بر اساس فیلترها.

        Args:
            filter_data: داده‌های فیلتر (DTO).

        Returns:
            int: تعداد کاربران هدف.

        Raises:
            BroadcastFilterError: در صورت بروز خطا در فیلتر.
        """
        # اعتبارسنجی فیلترها
        self._validate_filters(filter_data)

        # دریافت کاربران هدف و شمارش
        target_users = await self._apply_filters(filter_data, skip=0, limit=10000)
        return len(target_users)

    async def get_filter_statistics(
        self,
        filter_data: BroadcastFilterDTO,
    ) -> Dict[str, Any]:
        """
        دریافت آمار فیلترها (تعداد کل، تعداد فعال، تعداد مسدود، و ...).

        Args:
            filter_data: داده‌های فیلتر (DTO).

        Returns:
            Dict[str, Any]: آمار فیلترها.

        Raises:
            BroadcastFilterError: در صورت بروز خطا در فیلتر.
        """
        # اعتبارسنجی فیلترها
        self._validate_filters(filter_data)

        try:
            # دریافت کاربران هدف
            target_users = await self._apply_filters(filter_data, skip=0, limit=10000)

            # دریافت اطلاعات کامل کاربران برای آمار
            users = []
            for user_id in target_users[:1000]:  # محدودیت برای جلوگیری از حجم بالا
                user = await self._user_repository.get_by_id(user_id)
                if user:
                    users.append(user)

            total = len(target_users)
            active = sum(1 for u in users if u.is_active)
            banned = sum(1 for u in users if u.is_banned)

            # توزیع نقش‌ها
            from collections import defaultdict
            roles = defaultdict(int)
            for u in users:
                roles[u.role.value] += 1

            # توزیع سطوح
            levels = defaultdict(int)
            for u in users:
                levels[u.level.value] += 1

            return {
                "total_users": total,
                "active_users": active,
                "banned_users": banned,
                "roles_distribution": dict(roles),
                "levels_distribution": dict(levels),
                "sample_users": [u.telegram_id for u in users[:10]],
            }

        except Exception as e:
            logger.error(f"Error getting filter statistics: {e}")
            raise BroadcastFilterError(
                broadcast_id="",
                filter_criteria=filter_data.to_dict(),
                reason=str(e),
            )

    async def validate_filter(
        self,
        filter_data: BroadcastFilterDTO,
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی فیلترها و بازگرداندن نتایج اعتبارسنجی.

        Args:
            filter_data: داده‌های فیلتر (DTO).

        Returns:
            Dict[str, Any]: نتایج اعتبارسنجی شامل:
                - is_valid: آیا فیلترها معتبر هستند؟
                - errors: لیست خطاها (در صورت وجود)
                - warnings: لیست هشدارها (اختیاری)
                - estimated_users: تعداد تخمینی کاربران هدف
        """
        errors = []
        warnings = []
        result = {"is_valid": True, "errors": [], "warnings": [], "estimated_users": 0}

        try:
            # اعتبارسنجی فیلترها
            self._validate_filters(filter_data)
        except ValidationError as e:
            result["is_valid"] = False
            result["errors"].append(str(e))
            return result

        # بررسی تعداد کاربران هدف (اگر خیلی کم یا خیلی زیاد باشد)
        try:
            count = await self.count_target_users(filter_data)
            result["estimated_users"] = count

            if count == 0:
                warnings.append("هیچ کاربری با این فیلترها پیدا نشد.")
            elif count > 10000:
                warnings.append(f"تعداد کاربران هدف ({count}) بسیار زیاد است. ارسال ممکن است زمان‌بر باشد.")
            elif count > 5000:
                warnings.append(f"تعداد کاربران هدف ({count}) زیاد است. لطفاً از فیلترهای دقیق‌تر استفاده کنید.")

        except Exception as e:
            warnings.append(f"خطا در تخمین تعداد کاربران: {e}")

        result["warnings"] = warnings
        return result

    async def get_suggested_filters(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        دریافت فیلترهای پیشنهادی بر اساس زمینه (context).

        Args:
            context: زمینه (مانند 'new_users', 'active_users', 'high_spenders').

        Returns:
            List[Dict[str, Any]]: لیست فیلترهای پیشنهادی.
        """
        suggestions = []

        # پیشنهاد: کاربران جدید (هفته گذشته)
        suggestions.append({
            "name": "کاربران جدید (هفته گذشته)",
            "description": "کاربرانی که در هفته گذشته ثبت‌نام کرده‌اند.",
            "filters": {
                "created_after": (datetime.now() - timedelta(days=7)).isoformat(),
                "is_active": True,
                "is_banned": False,
            },
        })

        # پیشنهاد: کاربران فعال
        suggestions.append({
            "name": "کاربران فعال",
            "description": "کاربرانی که در ۳۰ روز گذشته فعالیت داشته‌اند.",
            "filters": {
                "last_activity_after": (datetime.now() - timedelta(days=30)).isoformat(),
                "is_active": True,
                "is_banned": False,
            },
        })

        # پیشنهاد: کاربران با امتیاز بالا
        suggestions.append({
            "name": "کاربران با امتیاز بالا",
            "description": "کاربرانی با امتیاز بیشتر از ۱۰۰۰.",
            "filters": {
                "min_points": 1000,
                "is_active": True,
                "is_banned": False,
            },
        })

        # پیشنهاد: کاربران سطح طلا و بالاتر
        suggestions.append({
            "name": "کاربران سطح طلا و بالاتر",
            "description": "کاربرانی با سطح طلا، پلاتین یا الماس.",
            "filters": {
                "levels": ["gold", "platinum", "diamond"],
                "is_active": True,
                "is_banned": False,
            },
        })

        # پیشنهاد: کاربران ادمین
        suggestions.append({
            "name": "ادمین‌ها و مدیران",
            "description": "کاربران با نقش ADMIN یا MANAGER.",
            "filters": {
                "roles": ["admin", "manager"],
                "is_active": True,
                "is_banned": False,
            },
        })

        # پیشنهاد: کاربران غیرفعال
        suggestions.append({
            "name": "کاربران غیرفعال",
            "description": "کاربرانی که بیش از ۹۰ روز فعالیت نداشته‌اند.",
            "filters": {
                "last_activity_before": (datetime.now() - timedelta(days=90)).isoformat(),
                "is_active": True,
                "is_banned": False,
            },
        })

        return suggestions

    async def _apply_filters(
        self,
        filter_data: BroadcastFilterDTO,
        skip: int,
        limit: int,
    ) -> List[int]:
        """
        اعمال فیلترها و دریافت لیست کاربران هدف (داخلی).

        Args:
            filter_data: داده‌های فیلتر (DTO).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            List[int]: لیست شناسه‌های کاربران هدف.
        """
        target_users = set()

        # دریافت کاربران بر اساس فیلترها
        users = await self._user_repository.get_all(
            skip=0,
            limit=10000,
        )

        # اگر کاربران خاصی مشخص شده‌اند
        if filter_data.user_ids:
            target_users.update(filter_data.user_ids)

        # اعمال فیلترها
        for user in users:
            # اگر کاربر در لیست حذف است، رد می‌کنیم
            if filter_data.exclude_user_ids and user.id in filter_data.exclude_user_ids:
                continue

            # فیلتر بر اساس نقش
            if filter_data.roles and user.role.value not in filter_data.roles:
                continue

            # فیلتر بر اساس سطح
            if filter_data.levels and user.level.value not in filter_data.levels:
                continue

            # فیلتر بر اساس امتیاز
            if filter_data.min_points is not None and user.points < filter_data.min_points:
                continue
            if filter_data.max_points is not None and user.points > filter_data.max_points:
                continue

            # فیلتر بر اساس وضعیت فعال بودن
            if filter_data.is_active is not None and user.is_active != filter_data.is_active:
                continue

            # فیلتر بر اساس مسدود بودن
            if filter_data.is_banned is not None and user.is_banned != filter_data.is_banned:
                continue

            # فیلتر بر اساس تاریخ ایجاد
            if filter_data.created_after and user.created_at < filter_data.created_after:
                continue
            if filter_data.created_before and user.created_at > filter_data.created_before:
                continue

            # فیلتر بر اساس آخرین فعالیت
            if filter_data.last_activity_after:
                if not user.last_activity or user.last_activity < filter_data.last_activity_after:
                    continue
            if filter_data.last_activity_before:
                if user.last_activity and user.last_activity > filter_data.last_activity_before:
                    continue

            # اگر کاربران خاصی مشخص نشده بودند، اضافه می‌کنیم
            if not filter_data.user_ids:
                if user.telegram_id:
                    target_users.add(user.id)
            # اگر کاربران خاصی مشخص شده بودند، فقط آنها را اضافه می‌کنیم
            elif filter_data.user_ids and user.id in filter_data.user_ids:
                target_users.add(user.id)

        # تبدیل به لیست و اعمال صفحه‌بندی
        result = list(target_users)
        return result[skip:skip + limit] if skip > 0 or limit > 0 else result

    def _validate_filters(self, filter_data: BroadcastFilterDTO) -> None:
        """
        اعتبارسنجی فیلترها.

        Args:
            filter_data: داده‌های فیلتر (DTO).

        Raises:
            ValidationError: اگر فیلترها نامعتبر باشند.
        """
        errors = []

        # بررسی امتیاز
        if filter_data.min_points is not None:
            if filter_data.min_points < 0:
                errors.append("حداقل امتیاز نمی‌تواند منفی باشد.")
            if filter_data.max_points is not None and filter_data.min_points > filter_data.max_points:
                errors.append("حداقل امتیاز نمی‌تواند بیشتر از حداکثر امتیاز باشد.")

        # بررسی نقش‌ها
        if filter_data.roles:
            from my_bot.core.constants.user_roles import UserRole
            valid_roles = [r.value for r in UserRole]
            for role in filter_data.roles:
                if role not in valid_roles:
                    errors.append(f"نقش '{role}' نامعتبر است.")

        # بررسی سطوح
        if filter_data.levels:
            from my_bot.domain.value_objects.user_level import UserLevel
            valid_levels = [l.value for l in UserLevel]
            for level in filter_data.levels:
                if level not in valid_levels:
                    errors.append(f"سطح '{level}' نامعتبر است.")

        # بررسی تاریخ‌ها
        if filter_data.created_after and filter_data.created_before:
            if filter_data.created_after > filter_data.created_before:
                errors.append("تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")

        if filter_data.last_activity_after and filter_data.last_activity_before:
            if filter_data.last_activity_after > filter_data.last_activity_before:
                errors.append("تاریخ آخرین فعالیت شروع نمی‌تواند بعد از تاریخ پایان باشد.")

        # بررسی کاربران
        if filter_data.user_ids:
            if not all(isinstance(u, int) and u > 0 for u in filter_data.user_ids):
                errors.append("شناسه‌های کاربران باید اعداد صحیح مثبت باشند.")

        # اگر خطایی وجود دارد، پرتاب می‌کنیم
        if errors:
            raise ValidationError(
                message="فیلترها نامعتبر هستند.",
                context={"errors": errors},
            )

    def _generate_cache_key(
        self,
        filter_data: BroadcastFilterDTO,
        skip: int,
        limit: int,
    ) -> str:
        """
        تولید کلید کش برای فیلترها.

        Args:
            filter_data: داده‌های فیلتر (DTO).
            skip: تعداد رکوردهای نادیده گرفته شده.
            limit: حداکثر تعداد رکوردهای برگشتی.

        Returns:
            str: کلید کش.
        """
        # ایجاد یک رشته هش از فیلترها
        import hashlib
        import json

        filter_dict = filter_data.to_dict()
        # حذف فیلدهای خالی
        filter_dict = {k: v for k, v in filter_dict.items() if v is not None}
        # مرتب‌سازی کلیدها برای یکنواختی
        filter_str = json.dumps(filter_dict, sort_keys=True)
        hash_str = hashlib.md5(filter_str.encode()).hexdigest()

        return f"broadcast_filter:{hash_str}:{skip}:{limit}"

    async def clear_cache(self) -> None:
        """
        پاک کردن تمام کش‌های فیلتر.
        """
        if self._cache:
            await self._cache.delete_pattern("broadcast_filter:*")
            logger.info("Broadcast filter cache cleared.")