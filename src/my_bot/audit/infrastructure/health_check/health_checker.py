# my_bot_project/src/my_bot/infrastructure/health_check/health_checker.py
"""
بررسی سلامت سیستم (Health Checker).

این ماژول شامل کلاس `HealthChecker` است که مسئولیت بررسی سلامت
سرویس‌های مختلف سیستم (دیتابیس، کش، سرویس‌های خارجی و ...) را بر عهده دارد.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.cache.cache_manager import CacheManager

logger = get_logger(__name__)


@dataclass
class HealthCheckResult:
    """
    نتیجه یک بررسی سلامت.

    Attributes:
        name: نام سرویس.
        status: وضعیت (True: سالم، False: ناسالم).
        message: پیام توضیحی.
        timestamp: زمان بررسی.
        details: جزئیات اضافی.
    """
    name: str
    status: bool
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


class HealthChecker:
    """
    بررسی سلامت سرویس‌های سیستم.

    این کلاس با استفاده از چک‌کننده‌های ثبت‌شده، سلامت سرویس‌های
    مختلف را بررسی می‌کند و نتایج را به‌صورت خلاصه بازمی‌گرداند.

    Attributes:
        _checks: لیست چک‌کننده‌های ثبت‌شده.
        _timeout: زمان timeout برای هر چک (ثانیه).
    """

    def __init__(self, timeout: float = 5.0) -> None:
        """
        مقداردهی اولیه HealthChecker.

        Args:
            timeout: زمان timeout برای هر چک بر حسب ثانیه (پیش‌فرض ۵).
        """
        self._checks: List[Callable[[], Awaitable[HealthCheckResult]]] = []
        self._timeout = timeout

        logger.info(f"HealthChecker initialized with timeout={timeout}s")

    def register_check(
        self,
        check_func: Callable[[], Awaitable[HealthCheckResult]],
    ) -> None:
        """
        ثبت یک چک‌کننده جدید.

        Args:
            check_func: تابع async که یک HealthCheckResult برمی‌گرداند.
        """
        self._checks.append(check_func)
        logger.debug(f"Health check registered: {check_func.__name__}")

    async def check_all(self) -> List[HealthCheckResult]:
        """
        اجرای تمام چک‌کننده‌های ثبت‌شده.

        Returns:
            List[HealthCheckResult]: لیست نتایج بررسی.
        """
        results = []
        for check_func in self._checks:
            try:
                # اجرا با timeout
                result = await asyncio.wait_for(
                    check_func(),
                    timeout=self._timeout,
                )
                results.append(result)

            except asyncio.TimeoutError:
                logger.warning(f"Health check timeout: {check_func.__name__}")
                results.append(
                    HealthCheckResult(
                        name=check_func.__name__,
                        status=False,
                        message=f"Timeout after {self._timeout}s",
                    )
                )
            except Exception as e:
                logger.error(f"Health check error: {check_func.__name__} - {e}")
                results.append(
                    HealthCheckResult(
                        name=check_func.__name__,
                        status=False,
                        message=f"Error: {str(e)}",
                    )
                )

        return results

    async def check(self) -> Dict[str, Any]:
        """
        دریافت خلاصه وضعیت سلامت سیستم.

        Returns:
            Dict[str, Any]: خلاصه وضعیت شامل:
                - status: وضعیت کلی (True اگر همه سالم باشند)
                - results: لیست نتایج
                - timestamp: زمان بررسی
                - total_checks: تعداد کل چک‌ها
                - healthy: تعداد چک‌های سالم
                - unhealthy: تعداد چک‌های ناسالم
        """
        results = await self.check_all()

        healthy_count = sum(1 for r in results if r.status)
        total_count = len(results)
        overall_status = healthy_count == total_count

        return {
            "status": overall_status,
            "results": [r.to_dict() for r in results],
            "timestamp": datetime.now().isoformat(),
            "total_checks": total_count,
            "healthy": healthy_count,
            "unhealthy": total_count - healthy_count,
        }

    async def check_service(self, service_name: str) -> Optional[HealthCheckResult]:
        """
        بررسی سلامت یک سرویس خاص با نام.

        Args:
            service_name: نام سرویس.

        Returns:
            Optional[HealthCheckResult]: نتیجه بررسی یا None در صورت عدم وجود.
        """
        for check_func in self._checks:
            if check_func.__name__ == service_name:
                try:
                    return await asyncio.wait_for(
                        check_func(),
                        timeout=self._timeout,
                    )
                except asyncio.TimeoutError:
                    return HealthCheckResult(
                        name=service_name,
                        status=False,
                        message=f"Timeout after {self._timeout}s",
                    )
                except Exception as e:
                    return HealthCheckResult(
                        name=service_name,
                        status=False,
                        message=f"Error: {str(e)}",
                    )

        return None


# ----------------------------------------------
# چک‌کننده‌های پیش‌فرض
# ----------------------------------------------

async def check_database(db_manager: DatabaseSessionManager) -> HealthCheckResult:
    """
    چک‌کننده سلامت دیتابیس.

    Args:
        db_manager: مدیر جلسات دیتابیس.

    Returns:
        HealthCheckResult: نتیجه بررسی.
    """
    try:
        is_healthy = await db_manager.health_check()
        status = await db_manager.get_pool_status()

        return HealthCheckResult(
            name="database",
            status=is_healthy,
            message="Database is healthy" if is_healthy else "Database is unhealthy",
            details=status,
        )
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return HealthCheckResult(
            name="database",
            status=False,
            message=f"Database check failed: {str(e)}",
            details={"error": str(e)},
        )


async def check_cache(cache_manager: CacheManager) -> HealthCheckResult:
    """
    چک‌کننده سلامت کش.

    Args:
        cache_manager: مدیر کش.

    Returns:
        HealthCheckResult: نتیجه بررسی.
    """
    try:
        is_healthy = await cache_manager.health_check()
        stats = await cache_manager.get_stats()

        return HealthCheckResult(
            name="cache",
            status=is_healthy,
            message="Cache is healthy" if is_healthy else "Cache is unhealthy",
            details=stats,
        )
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return HealthCheckResult(
            name="cache",
            status=False,
            message=f"Cache check failed: {str(e)}",
            details={"error": str(e)},
        )


async def check_redis(cache_manager: CacheManager) -> HealthCheckResult:
    """
    چک‌کننده سلامت Redis.

    Args:
        cache_manager: مدیر کش (با Redis).

    Returns:
        HealthCheckResult: نتیجه بررسی.
    """
    try:
        status = await cache_manager.get_redis_status()
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


def create_default_health_checker(
    db_manager: DatabaseSessionManager,
    cache_manager: Optional[CacheManager] = None,
) -> HealthChecker:
    """
    ایجاد HealthChecker با چک‌کننده‌های پیش‌فرض.

    Args:
        db_manager: مدیر جلسات دیتابیس.
        cache_manager: مدیر کش (اختیاری).

    Returns:
        HealthChecker: نمونه HealthChecker با چک‌کننده‌های ثبت‌شده.
    """
    checker = HealthChecker()

    # ثبت چک‌کننده دیتابیس
    checker.register_check(
        lambda: check_database(db_manager)
    )

    # ثبت چک‌کننده کش (در صورت وجود)
    if cache_manager:
        checker.register_check(
            lambda: check_cache(cache_manager)
        )
        checker.register_check(
            lambda: check_redis(cache_manager)
        )

    return checker