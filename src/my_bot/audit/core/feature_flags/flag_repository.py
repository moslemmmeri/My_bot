# my_bot_project/src/my_bot/core/feature_flags/flag_repository.py
"""
ذخیره‌سازی و بازیابی Feature Flags در دیتابیس.

این ماژول شامل کلاس `FlagRepository` است که مسئولیت ذخیره‌سازی دائمی
و بازیابی وضعیت ویژگی‌ها در دیتابیس را بر عهده دارد.
"""

import json
from typing import Any, Dict, Optional

from my_bot.core.exceptions.db_errors import DatabaseError, QueryError
from my_bot.core.exceptions.feature_errors import FeatureStorageError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class FlagRepository:
    """
    ریپازیتوری برای ذخیره‌سازی و بازیابی Feature Flags در دیتابیس.

    این کلاس با استفاده از یک Session دیتابیس، عملیات CRUD را روی
    جدول feature_flags انجام می‌دهد.

    Attributes:
        session_factory: تابع یا کلاسی که Session دیتابیس را تولید می‌کند.
    """

    def __init__(self, session_factory):
        """
        مقداردهی اولیه ریپازیتوری.

        Args:
            session_factory: تابعی که یک Session دیتابیس برمی‌گرداند.
        """
        self._session_factory = session_factory

    async def get(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک ویژگی خاص از دیتابیس.

        Args:
            feature_name: نام ویژگی.

        Returns:
            دیکشنری اطلاعات ویژگی یا None در صورت عدم وجود.

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
        """
        try:
            async with self._session_factory() as session:
                # فرض بر این است که مدل FeatureFlag با فیلدهای name و data تعریف شده است
                # data به صورت JSON ذخیره می‌شود
                result = await session.execute(
                    "SELECT name, data FROM feature_flags WHERE name = :name",
                    {"name": feature_name}
                )
                row = result.fetchone()
                if row is None:
                    return None
                # داده‌ها به صورت JSON ذخیره شده‌اند
                data = row["data"]
                if isinstance(data, str):
                    return json.loads(data)
                return data
        except Exception as e:
            logger.error(f"Error getting feature flag '{feature_name}': {e}")
            raise FeatureStorageError("get", feature_name, str(e))

    async def save(self, feature_name: str, data: Dict[str, Any]) -> None:
        """
        ذخیره یا به‌روزرسانی یک ویژگی در دیتابیس.

        Args:
            feature_name: نام ویژگی.
            data: دیکشنری اطلاعات ویژگی.

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
        """
        try:
            # تبدیل داده‌ها به JSON برای ذخیره‌سازی
            json_data = json.dumps(data, ensure_ascii=False, default=str)

            async with self._session_factory() as session:
                # استفاده از UPSERT (INSERT OR REPLACE) برای سادگی
                await session.execute(
                    """
                    INSERT INTO feature_flags (name, data, updated_at)
                    VALUES (:name, :data, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO UPDATE
                    SET data = :data, updated_at = CURRENT_TIMESTAMP
                    """,
                    {"name": feature_name, "data": json_data}
                )
                await session.commit()
                logger.debug(f"Feature flag '{feature_name}' saved successfully.")
        except Exception as e:
            logger.error(f"Error saving feature flag '{feature_name}': {e}")
            raise FeatureStorageError("save", feature_name, str(e))

    async def delete(self, feature_name: str) -> None:
        """
        حذف یک ویژگی از دیتابیس.

        Args:
            feature_name: نام ویژگی.

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
            FeatureNotFoundError: اگر ویژگی وجود نداشته باشد (اختیاری).
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    "DELETE FROM feature_flags WHERE name = :name RETURNING name",
                    {"name": feature_name}
                )
                deleted = result.fetchone()
                if deleted is None:
                    # در صورت نیاز می‌توان NotFoundError پرتاب کرد
                    logger.warning(f"Feature flag '{feature_name}' not found for deletion.")
                else:
                    await session.commit()
                    logger.debug(f"Feature flag '{feature_name}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting feature flag '{feature_name}': {e}")
            raise FeatureStorageError("delete", feature_name, str(e))

    async def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        دریافت تمام ویژگی‌های موجود در دیتابیس.

        Returns:
            دیکشنری با کلید نام ویژگی و مقدار اطلاعات آن.

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    "SELECT name, data FROM feature_flags"
                )
                rows = result.fetchall()
                flags = {}
                for row in rows:
                    name = row["name"]
                    data = row["data"]
                    if isinstance(data, str):
                        data = json.loads(data)
                    flags[name] = data
                return flags
        except Exception as e:
            logger.error(f"Error getting all feature flags: {e}")
            raise FeatureStorageError("get_all", None, str(e))

    async def exists(self, feature_name: str) -> bool:
        """
        بررسی وجود یک ویژگی در دیتابیس.

        Args:
            feature_name: نام ویژگی.

        Returns:
            True اگر ویژگی وجود داشته باشد.

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    "SELECT 1 FROM feature_flags WHERE name = :name LIMIT 1",
                    {"name": feature_name}
                )
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking existence of feature flag '{feature_name}': {e}")
            raise FeatureStorageError("exists", feature_name, str(e))

    async def get_enabled_flags(self) -> Dict[str, Dict[str, Any]]:
        """
        دریافت تمام ویژگی‌های فعال.

        Returns:
            دیکشنری با کلید نام ویژگی و مقدار اطلاعات آن.

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    "SELECT name, data FROM feature_flags"
                )
                rows = result.fetchall()
                flags = {}
                for row in rows:
                    name = row["name"]
                    data = row["data"]
                    if isinstance(data, str):
                        data = json.loads(data)
                    if data.get("enabled", False):
                        flags[name] = data
                return flags
        except Exception as e:
            logger.error(f"Error getting enabled feature flags: {e}")
            raise FeatureStorageError("get_enabled", None, str(e))

    async def update_usage(self, feature_name: str, increment: int = 1) -> None:
        """
        افزایش شمارش استفاده از یک ویژگی.

        Args:
            feature_name: نام ویژگی.
            increment: مقدار افزایش (پیش‌فرض ۱).

        Raises:
            FeatureStorageError: در صورت بروز خطا در دیتابیس.
        """
        try:
            # ابتدا مقدار فعلی را می‌خوانیم
            flag = await self.get(feature_name)
            if flag is None:
                logger.warning(f"Feature '{feature_name}' not found for usage update.")
                return

            current_usage = flag.get("current_usage", 0)
            flag["current_usage"] = current_usage + increment

            await self.save(feature_name, flag)
            logger.debug(f"Feature '{feature_name}' usage updated to {flag['current_usage']}.")
        except Exception as e:
            logger.error(f"Error updating usage for feature '{feature_name}': {e}")
            raise FeatureStorageError("update_usage", feature_name, str(e))