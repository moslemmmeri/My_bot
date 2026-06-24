# my_bot_project/src/my_bot/presentation/web_api/routes/health.py
"""
مسیریاب سلامت (Health Router).

این ماژول شامل کلاس `HealthRouter` است که مسیرهای مربوط به بررسی سلامت
سیستم را فراهم می‌کند. این مسیرها برای مانیتورینگ، کشف سرویس و
بررسی وضعیت سرویس‌های مختلف استفاده می‌شوند.

مسیرهای موجود:
- /health: بررسی سلامت کلی سیستم
- /health/ready: بررسی آمادگی سرویس (برای Kubernetes readiness probe)
- /health/live: بررسی زنده بودن سرویس (برای Kubernetes liveness probe)
"""

import asyncio
from typing import Optional, Dict, Any, List

from aiohttp import web
from aiohttp.web import Request, Response, json_response

from my_bot.core.logger.logger_setup import get_logger
from my_bot.infrastructure.health_check.health_checker import (
    HealthChecker,
    HealthCheckResult,
)

logger = get_logger(__name__)


class HealthRouter:
    """
    مسیریاب بررسی سلامت سیستم.

    این کلاس با استفاده از HealthChecker، وضعیت سلامت سرویس‌های مختلف
    را بررسی کرده و نتایج را به‌صورت JSON بازمی‌گرداند.

    Attributes:
        health_checker: بررسی کننده سلامت سیستم.
        service_name: نام سرویس برای نمایش در پاسخ‌ها.
        version: نسخه سرویس.
    """

    def __init__(
        self,
        health_checker: Optional[HealthChecker] = None,
        service_name: str = "my_bot",
        version: str = "1.0.0",
    ) -> None:
        """
        مقداردهی اولیه مسیریاب سلامت.

        Args:
            health_checker: بررسی کننده سلامت (اختیاری).
            service_name: نام سرویس (پیش‌فرض: "my_bot").
            version: نسخه سرویس (پیش‌فرض: "1.0.0").
        """
        self.health_checker = health_checker
        self.service_name = service_name
        self.version = version

        logger.info(
            f"HealthRouter initialized: service_name={service_name}, "
            f"version={version}, health_checker={health_checker is not None}"
        )

    async def handle_health(self, request: Request) -> Response:
        """
        هندلر مسیر /health برای بررسی سلامت کلی سیستم.

        این متد تمام سرویس‌های ثبت‌شده در HealthChecker را بررسی کرده
        و وضعیت کلی سیستم را به‌صورت JSON بازمی‌گرداند.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ JSON شامل وضعیت سلامت.
        """
        try:
            # اگر HealthChecker وجود دارد، از آن استفاده می‌کنیم
            if self.health_checker:
                result = await self.health_checker.check()

                # استخراج وضعیت کلی
                is_healthy = result.get("status", False)
                status_code = 200 if is_healthy else 503

                # ساخت پاسخ
                response_data = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "service": self.service_name,
                    "version": self.version,
                    "timestamp": result.get("timestamp"),
                    "checks": result.get("results", []),
                    "summary": {
                        "total": result.get("total_checks", 0),
                        "healthy": result.get("healthy", 0),
                        "unhealthy": result.get("unhealthy", 0),
                    },
                }

                return json_response(data=response_data, status=status_code)

            # اگر HealthChecker وجود ندارد، یک بررسی ساده انجام می‌دهیم
            return json_response(
                data={
                    "status": "healthy",
                    "service": self.service_name,
                    "version": self.version,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                    "message": "Health checker not configured, basic check passed.",
                },
                status=200,
            )

        except Exception as e:
            logger.error(f"Error in health check: {e}", exc_info=True)
            return json_response(
                data={
                    "status": "unhealthy",
                    "service": self.service_name,
                    "version": self.version,
                    "error": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                status=503,
            )

    async def handle_readiness(self, request: Request) -> Response:
        """
        هندلر مسیر /health/ready برای بررسی آمادگی سرویس.

        این متد بررسی می‌کند که آیا سرویس آماده پذیرش ترافیک است یا خیر.
        معمولاً در Kubernetes به‌عنوان readiness probe استفاده می‌شود.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ JSON شامل وضعیت آمادگی.
        """
        try:
            # بررسی آمادگی: دیتابیس و کش باید در دسترس باشند
            readiness_checks = []

            if self.health_checker:
                # اجرای بررسی‌های آمادگی
                # در اینجا فقط دیتابیس و کش را بررسی می‌کنیم
                db_check = await self._check_database()
                cache_check = await self._check_cache()

                readiness_checks = [db_check, cache_check]

                # فیلتر کردن بررسی‌های ناموفق
                failed_checks = [c for c in readiness_checks if not c.get("status", False)]

                is_ready = len(failed_checks) == 0
                status_code = 200 if is_ready else 503

                return json_response(
                    data={
                        "status": "ready" if is_ready else "not_ready",
                        "service": self.service_name,
                        "version": self.version,
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                        "checks": readiness_checks,
                        "failed_checks": len(failed_checks),
                    },
                    status=status_code,
                )

            # اگر HealthChecker وجود ندارد، فرض می‌کنیم آماده است
            return json_response(
                data={
                    "status": "ready",
                    "service": self.service_name,
                    "version": self.version,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                    "message": "Health checker not configured, assuming ready.",
                },
                status=200,
            )

        except Exception as e:
            logger.error(f"Error in readiness check: {e}", exc_info=True)
            return json_response(
                data={
                    "status": "not_ready",
                    "service": self.service_name,
                    "version": self.version,
                    "error": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                status=503,
            )

    async def handle_liveness(self, request: Request) -> Response:
        """
        هندلر مسیر /health/live برای بررسی زنده بودن سرویس.

        این متد بررسی می‌کند که آیا سرویس هنوز در حال اجرا است یا خیر.
        معمولاً در Kubernetes به‌عنوان liveness probe استفاده می‌شود.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ JSON شامل وضعیت زنده بودن.
        """
        try:
            # بررسی زنده بودن: فقط بررسی می‌کنیم که برنامه در حال اجرا است
            # و به درخواست‌ها پاسخ می‌دهد

            # اگر HealthChecker وجود دارد، یک بررسی سریع انجام می‌دهیم
            if self.health_checker:
                # فقط بررسی می‌کنیم که آیا سرویس پاسخ می‌دهد
                # از یک تایم‌اوت کوتاه استفاده می‌کنیم
                try:
                    # بررسی با تایم‌اوت ۲ ثانیه
                    result = await asyncio.wait_for(
                        self.health_checker.check(),
                        timeout=2.0,
                    )
                    is_live = True
                except asyncio.TimeoutError:
                    is_live = False
                    logger.warning("Liveness check timeout.")
                except Exception as e:
                    is_live = False
                    logger.error(f"Liveness check error: {e}")

                status_code = 200 if is_live else 503

                return json_response(
                    data={
                        "status": "alive" if is_live else "dead",
                        "service": self.service_name,
                        "version": self.version,
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                    },
                    status=status_code,
                )

            # اگر HealthChecker وجود ندارد، فقط پاسخ می‌دهیم
            return json_response(
                data={
                    "status": "alive",
                    "service": self.service_name,
                    "version": self.version,
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                status=200,
            )

        except Exception as e:
            logger.error(f"Error in liveness check: {e}", exc_info=True)
            return json_response(
                data={
                    "status": "dead",
                    "service": self.service_name,
                    "version": self.version,
                    "error": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat(),
                },
                status=503,
            )

    async def _check_database(self) -> Dict[str, Any]:
        """
        بررسی سلامت دیتابیس.

        Returns:
            Dict[str, Any]: نتیجه بررسی دیتابیس.
        """
        try:
            # اگر HealthChecker و چک‌کننده دیتابیس موجود است
            if self.health_checker:
                # بررسی دیتابیس از طریق HealthChecker
                # در اینجا یک بررسی ساده انجام می‌دهیم
                result = await self.health_checker.check_service("database")
                if result:
                    return {
                        "name": "database",
                        "status": result.status,
                        "message": result.message,
                        "details": result.details,
                    }

            return {
                "name": "database",
                "status": True,
                "message": "Database check not configured, assuming healthy.",
            }

        except Exception as e:
            logger.error(f"Database check error: {e}")
            return {
                "name": "database",
                "status": False,
                "message": f"Database check failed: {str(e)}",
            }

    async def _check_cache(self) -> Dict[str, Any]:
        """
        بررسی سلامت کش.

        Returns:
            Dict[str, Any]: نتیجه بررسی کش.
        """
        try:
            # اگر HealthChecker و چک‌کننده کش موجود است
            if self.health_checker:
                result = await self.health_checker.check_service("cache")
                if result:
                    return {
                        "name": "cache",
                        "status": result.status,
                        "message": result.message,
                        "details": result.details,
                    }

            return {
                "name": "cache",
                "status": True,
                "message": "Cache check not configured, assuming healthy.",
            }

        except Exception as e:
            logger.error(f"Cache check error: {e}")
            return {
                "name": "cache",
                "status": False,
                "message": f"Cache check failed: {str(e)}",
            }

    async def get_detailed_health(self) -> Dict[str, Any]:
        """
        دریافت وضعیت دقیق سلامت برای استفاده در پنل مدیریت.

        Returns:
            Dict[str, Any]: وضعیت دقیق سلامت.
        """
        if self.health_checker:
            return await self.health_checker.check()

        return {
            "status": True,
            "service": self.service_name,
            "version": self.version,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "results": [],
            "total_checks": 0,
            "healthy": 0,
            "unhealthy": 0,
            "message": "Health checker not configured.",
        }

    def set_health_checker(self, health_checker: HealthChecker) -> None:
        """
        تنظیم HealthChecker.

        Args:
            health_checker: بررسی کننده سلامت.
        """
        self.health_checker = health_checker
        logger.info("HealthChecker set in HealthRouter.")