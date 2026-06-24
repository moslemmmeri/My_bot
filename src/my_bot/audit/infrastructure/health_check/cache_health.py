# my_bot_project/src/my_bot/infrastructure/health_check/cache_health.py
"""
بررسی سلامت کش (Cache Health Check).

این ماژول شامل کلاس `CacheHealthCheck` است که مسئولیت بررسی
سلامت سرویس کش (Redis و Local Cache) را بر عهده دارد.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.infrastructure.cache.cache_manager import CacheManager
from my_bot.infrastructure.health_check.health_checker import HealthCheckResult

logger = get_logger(__name__)


class CacheHealthCheck:
    """
    بررسی سلامت کش.

    این کلاس با استفاده از CacheManager، سلامت Redis و Local Cache را بررسی می‌کند.

    Attributes:
        cache_manager: مدیر کش.
        _last_check: زمان آخرین بررسی.
        _last_result: آخرین نتیجه بررسی.
    """

    def __init__(self, cache_manager: CacheManager) -> None:
        """
        مقداردهی اولیه CacheHealthCheck.

        Args:
            cache_manager: مدیر کش.
        """
        self.cache_manager = cache_manager
        self._last_check: Optional[datetime] = None
        self._last_result: Optional[HealthCheckResult] = None

        logger.info("CacheHealthCheck initialized.")

    async def check(self) -> HealthCheckResult:
        """
        بررسی سلامت کش.

        Returns:
            HealthCheckResult: نتیجه بررسی.
        """
        try:
            # بررسی سلامت کلی کش
            is_healthy = await self.cache_manager.health_check()

            # دریافت آمار کش
            stats = await self.cache_manager.get_stats()

            # دریافت وضعیت Redis
            redis_status = await self.cache_manager.get_redis_status()

            result = HealthCheckResult(
                name="cache",
                status=is_healthy,
                message="Cache is healthy" if is_healthy else "Cache is unhealthy",
                details={
                    "redis_status": redis_status,
                    "stats": stats,
                },
            )

            # ذخیره نتیجه
            self._last_check = datetime.now()
            self._last_result = result

            return result

        except Exception as e:
            logger.error(f"Cache health check error: {e}")
            result = HealthCheckResult(
                name="cache",
                status=False,
                message=f"Cache check failed: {str(e)}",
                details={"error": str(e)},
            )

            self._last_check = datetime.now()
            self._last_result = result

            return result

    async def check_redis(self) -> HealthCheckResult:
        """
        بررسی سلامت Redis.

        Returns:
            HealthCheckResult: نتیجه بررسی Redis.
        """
        try:
            status = await self.cache_manager.get_redis_status()
            is_healthy = status.get("available", False)

            return HealthCheckResult(
                name="redis",
                status=is_healthy,
                message="Redis is healthy" if is_healthy else "Redis is unhealthy",
                details=status,
            )

        except Exception as e:
            logger.error(f"Redis health check error: {e}")
            return HealthCheckResult(
                name="redis",
                status=False,
                message=f"Redis check failed: {str(e)}",
                details={"error": str(e)},
            )

    async def check_local(self) -> HealthCheckResult:
        """
        بررسی سلامت Local Cache.

        Returns:
            HealthCheckResult: نتیجه بررسی Local Cache.
        """
        try:
            stats = await self.cache_manager.get_stats()
            local_stats = stats.get("local", {})

            # Local Cache همیشه در دسترس است (مگر اینکه خطای داخلی داشته باشد)
            is_healthy = True

            return HealthCheckResult(
                name="local_cache",
                status=is_healthy,
                message="Local cache is healthy",
                details=local_stats,
            )

        except Exception as e:
            logger.error(f"Local cache health check error: {e}")
            return HealthCheckResult(
                name="local_cache",
                status=False,
                message=f"Local cache check failed: {str(e)}",
                details={"error": str(e)},
            )

    def get_last_result(self) -> Optional[HealthCheckResult]:
        """
        دریافت آخرین نتیجه بررسی کش.

        Returns:
            Optional[HealthCheckResult]: آخرین نتیجه یا None در صورت عدم وجود.
        """
        return self._last_result

    async def get_detailed_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت دقیق کش.

        Returns:
            Dict[str, Any]: وضعیت دقیق شامل اطلاعات Redis و Local Cache.
        """
        stats = await self.cache_manager.get_stats()
        redis_status = await self.cache_manager.get_redis_status()
        is_healthy = await self.cache_manager.health_check()

        return {
            "healthy": is_healthy,
            "redis": redis_status,
            "stats": stats,
            "last_check": self._last_check.isoformat() if self._last_check else None,
        }

    async def check_and_auto_recover(self) -> HealthCheckResult:
        """
        بررسی سلامت کش با تلاش برای بازیابی خودکار.

        Returns:
            HealthCheckResult: نتیجه بررسی.
        """
        result = await self.check()

        # اگر کش ناسالم است، سعی می‌کنیم بازیابی کنیم
        if not result.status:
            logger.warning("Cache is unhealthy. Attempting auto-recovery...")

            try:
                # تلاش برای بازسازی اتصال Redis
                if hasattr(self.cache_manager, "_redis_adapter"):
                    redis_adapter = self.cache_manager._redis_adapter
                    if redis_adapter:
                        try:
                            await redis_adapter.close()
                            await redis_adapter.initialize()
                            logger.info("Redis connection re-established.")
                        except Exception as e:
                            logger.error(f"Failed to re-establish Redis connection: {e}")

                # بررسی مجدد
                result = await self.check()

            except Exception as e:
                logger.error(f"Auto-recovery failed: {e}")

        return result