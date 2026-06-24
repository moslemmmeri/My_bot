# my_bot_project/src/my_bot/infrastructure/health_check/db_health.py
"""
بررسی سلامت دیتابیس (Database Health Check).

این ماژول شامل کلاس `DatabaseHealthCheck` است که مسئولیت بررسی
سلامت اتصال به دیتابیس و وضعیت Connection Pool را بر عهده دارد.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.health_check.health_checker import HealthCheckResult

logger = get_logger(__name__)


class DatabaseHealthCheck:
    """
    بررسی سلامت دیتابیس.

    این کلاس با استفاده از DatabaseSessionManager، سلامت اتصال به دیتابیس
    و وضعیت Connection Pool را بررسی می‌کند.

    Attributes:
        db_manager: مدیر جلسات دیتابیس.
        _last_check: زمان آخرین بررسی.
        _last_result: آخرین نتیجه بررسی.
    """

    def __init__(self, db_manager: DatabaseSessionManager) -> None:
        """
        مقداردهی اولیه DatabaseHealthCheck.

        Args:
            db_manager: مدیر جلسات دیتابیس.
        """
        self.db_manager = db_manager
        self._last_check: Optional[datetime] = None
        self._last_result: Optional[HealthCheckResult] = None

        logger.info("DatabaseHealthCheck initialized.")

    async def check(self) -> HealthCheckResult:
        """
        بررسی سلامت دیتابیس.

        Returns:
            HealthCheckResult: نتیجه بررسی.
        """
        try:
            # بررسی اتصال
            is_healthy = await self.db_manager.health_check()

            # دریافت وضعیت Pool
            pool_status = await self.db_manager.get_pool_status()

            # اطلاعات دیتابیس
            db_info = {
                "db_type": self.db_manager.config.db_type(),
                "pool_size": self.db_manager.config.pool_size,
                "max_overflow": self.db_manager.config.max_overflow,
                "is_initialized": self.db_manager._is_initialized,
                "pool_status": pool_status.get("pool_status", {}),
            }

            result = HealthCheckResult(
                name="database",
                status=is_healthy,
                message="Database is healthy" if is_healthy else "Database is unhealthy",
                details=db_info,
            )

            # ذخیره نتیجه
            self._last_check = datetime.now()
            self._last_result = result

            return result

        except Exception as e:
            logger.error(f"Database health check error: {e}")
            result = HealthCheckResult(
                name="database",
                status=False,
                message=f"Database check failed: {str(e)}",
                details={"error": str(e)},
            )

            self._last_check = datetime.now()
            self._last_result = result

            return result

    async def check_connection(self) -> bool:
        """
        بررسی ساده اتصال به دیتابیس (بدون جزئیات).

        Returns:
            bool: True اگر اتصال برقرار باشد.
        """
        try:
            return await self.db_manager.health_check()
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    async def check_pool_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت Connection Pool.

        Returns:
            Dict[str, Any]: وضعیت Pool.
        """
        try:
            return await self.db_manager.get_pool_status()
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {"error": str(e), "is_initialized": False}

    def get_last_result(self) -> Optional[HealthCheckResult]:
        """
        دریافت آخرین نتیجه بررسی.

        Returns:
            Optional[HealthCheckResult]: آخرین نتیجه یا None در صورت عدم وجود.
        """
        return self._last_result

    async def get_detailed_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت دقیق دیتابیس.

        Returns:
            Dict[str, Any]: وضعیت دقیق شامل اطلاعات اتصال و Pool.
        """
        pool_status = await self.check_pool_status()
        is_healthy = await self.check_connection()

        return {
            "healthy": is_healthy,
            "db_type": self.db_manager.config.db_type(),
            "url": self.db_manager.config.url[:30] + "...",
            "pool_size": self.db_manager.config.pool_size,
            "max_overflow": self.db_manager.config.max_overflow,
            "pool_timeout": self.db_manager.config.pool_timeout,
            "pool_recycle": self.db_manager.config.pool_recycle,
            "is_initialized": self.db_manager._is_initialized,
            "pool_status": pool_status.get("pool_status", {}),
            "last_check": self._last_check.isoformat() if self._last_check else None,
        }