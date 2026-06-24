# my_bot_project/src/my_bot/application/services/user/user_level_upgrade.py
"""
سرویس ارتقاء سطح کاربر (User Level Upgrade Service).

این سرویس مسئولیت مدیریت ارتقاء سطح کاربران بر اساس امتیاز را بر عهده دارد.
ارتقاء سطح شامل بررسی امتیاز کاربر، محاسبه سطح جدید، اعمال تغییرات
و ارسال نوتیفیکیشن‌های مربوطه است.
"""

from typing import Optional, Dict, Any

from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.value_objects.user_level import UserLevel

logger = get_logger(__name__)


class UserLevelUpgradeService:
    """
    سرویس ارتقاء سطح کاربر.

    این کلاس مسئولیت بررسی و ارتقاء سطح کاربران بر اساس امتیاز را بر عهده دارد.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        message_publisher: Optional[MessagePublisher] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس ارتقاء سطح.

        Args:
            user_repository: ریپازیتوری کاربر.
            message_publisher: انتشاردهنده پیام برای رویدادها (اختیاری).
        """
        self._user_repository = user_repository
        self._message_publisher = message_publisher

    async def upgrade_user_level(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        بررسی و ارتقاء سطح کاربر بر اساس امتیاز فعلی.

        این متد امتیاز کاربر را بررسی می‌کند و در صورت نیاز، سطح او را ارتقاء می‌دهد.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[Dict[str, Any]]: اطلاعات ارتقاء (سطح قدیم و جدید) در صورت تغییر،
            یا None در صورت عدم تغییر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        return await self._upgrade_user(user)

    async def upgrade_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        بررسی و ارتقاء سطح کاربر بر اساس شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام کاربر.

        Returns:
            Optional[Dict[str, Any]]: اطلاعات ارتقاء (سطح قدیم و جدید) در صورت تغییر،
            یا None در صورت عدم تغییر.

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFoundError(telegram_id=telegram_id)

        return await self._upgrade_user(user)

    async def _upgrade_user(self, user: User) -> Optional[Dict[str, Any]]:
        """
        انجام عملیات ارتقاء سطح کاربر (داخلی).

        Args:
            user: موجودیت کاربر.

        Returns:
            Optional[Dict[str, Any]]: اطلاعات ارتقاء در صورت تغییر، یا None.
        """
        old_level = user.level
        new_level = UserLevel.from_points(user.points)

        if new_level == old_level:
            logger.debug(f"User {user.id} level unchanged: {old_level.value}")
            return None

        # ذخیره سطح جدید در کاربر
        user.level = new_level
        saved_user = await self._user_repository.save(user)

        # ساخت اطلاعات ارتقاء
        upgrade_info = {
            "user_id": saved_user.id,
            "telegram_id": saved_user.telegram_id,
            "old_level": old_level.value,
            "old_level_display": old_level.display_name,
            "new_level": new_level.value,
            "new_level_display": new_level.display_name,
            "points": saved_user.points,
        }

        logger.info(
            f"User {saved_user.id} level upgraded from {old_level.value} "
            f"to {new_level.value} (points: {saved_user.points})"
        )

        # انتشار رویداد ارتقاء سطح
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="user.level_upgraded",
                event_data=upgrade_info,
                source="UserLevelUpgradeService",
            )

            # ارسال نوتیفیکیشن به کاربر (در صورت وجود انتشاردهنده)
            await self._message_publisher.publish_notification(
                user_id=saved_user.id or 0,
                notification_type="level_upgrade",
                data={
                    "old_level": old_level.display_name,
                    "new_level": new_level.display_name,
                    "old_level_emoji": old_level.emoji,
                    "new_level_emoji": new_level.emoji,
                    "points": saved_user.points,
                },
            )

        return upgrade_info

    async def check_and_upgrade_all_users(self, batch_size: int = 50) -> Dict[str, int]:
        """
        بررسی و ارتقاء سطح تمام کاربران (برای اجرای دستی یا زمان‌بندی‌شده).

        Args:
            batch_size: تعداد کاربران در هر بچ.

        Returns:
            Dict[str, int]: آمار ارتقاء (total_checked, total_upgraded).
        """
        total_checked = 0
        total_upgraded = 0
        skip = 0

        while True:
            # دریافت کاربران به‌صورت بچ
            users = await self._user_repository.get_all(skip=skip, limit=batch_size)
            if not users:
                break

            for user in users:
                total_checked += 1
                result = await self._upgrade_user(user)
                if result:
                    total_upgraded += 1

            skip += batch_size
            logger.info(f"Processed batch of {len(users)} users. Total checked: {total_checked}")

        logger.info(f"Level upgrade complete: checked {total_checked}, upgraded {total_upgraded}")
        return {
            "total_checked": total_checked,
            "total_upgraded": total_upgraded,
        }

    async def get_upgrade_progress(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت اطلاعات پیشرفت کاربر برای رسیدن به سطح بعدی.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Dict[str, Any]: اطلاعات پیشرفت شامل:
                - current_level: سطح فعلی
                - next_level: سطح بعدی (یا None در صورت آخرین سطح)
                - points: امتیاز فعلی
                - points_needed: امتیاز مورد نیاز برای ارتقاء
                - progress_percentage: درصد پیشرفت

        Raises:
            UserNotFoundError: اگر کاربر وجود نداشته باشد.
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        current_level = user.level
        next_level = current_level.next_level

        if next_level is None:
            # در بالاترین سطح
            return {
                "current_level": current_level.display_name,
                "current_level_emoji": current_level.emoji,
                "next_level": None,
                "points": user.points,
                "points_needed": None,
                "progress_percentage": 100.0,
                "is_max_level": True,
            }

        points_needed = current_level.points_to_next_level(user.points)
        progress = current_level.get_progress(user.points)

        return {
            "current_level": current_level.display_name,
            "current_level_emoji": current_level.emoji,
            "next_level": next_level.display_name,
            "next_level_emoji": next_level.emoji,
            "points": user.points,
            "points_needed": points_needed,
            "progress_percentage": progress,
            "is_max_level": False,
        }

    async def get_level_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار توزیع سطوح کاربران.

        Returns:
            Dict[str, Any]: آمار سطوح شامل تعداد کاربران در هر سطح.
        """
        stats = {
            UserLevel.BRONZE.value: 0,
            UserLevel.SILVER.value: 0,
            UserLevel.GOLD.value: 0,
            UserLevel.PLATINUM.value: 0,
            UserLevel.DIAMOND.value: 0,
            "total_users": 0,
        }

        # دریافت تمام کاربران (برای آمار دقیق)
        users = await self._user_repository.get_all(limit=10000)
        for user in users:
            stats[user.level.value] = stats.get(user.level.value, 0) + 1
            stats["total_users"] += 1

        return stats

    async def get_top_users_by_level(self, limit: int = 10) -> list[dict]:
        """
        دریافت کاربران برتر بر اساس سطح و امتیاز.

        Args:
            limit: تعداد کاربران برتر.

        Returns:
            list[dict]: لیست کاربران برتر.
        """
        users = await self._user_repository.get_top_by_points(limit=limit)

        result = []
        for user in users:
            result.append({
                "user_id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "level": user.level.display_name,
                "level_emoji": user.level.emoji,
                "points": user.points,
            })

        return result