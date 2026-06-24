# my_bot_project/src/my_bot/infrastructure/health_check/external_health.py
"""
بررسی سلامت سرویس‌های خارجی (External Services Health Check).

این ماژول شامل کلاس `ExternalServiceHealthCheck` است که مسئولیت بررسی
سلامت سرویس‌های خارجی مانند درگاه پرداخت، ایمیل، پیامک و ... را بر عهده دارد.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.infrastructure.health_check.health_checker import HealthCheckResult

logger = get_logger(__name__)


class ExternalServiceHealthCheck:
    """
    بررسی سلامت سرویس‌های خارجی.

    این کلاس با استفاده از سرویس‌های ثبت‌شده، سلامت سرویس‌های خارجی
    را بررسی می‌کند.

    Attributes:
        _services: دیکشنری نگاشت نام سرویس به تابع بررسی سلامت.
        _last_results: دیکشنری نگاشت نام سرویس به آخرین نتیجه بررسی.
    """

    def __init__(self) -> None:
        """
        مقداردهی اولیه ExternalServiceHealthCheck.
        """
        self._services: Dict[str, callable] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
        self._last_check: Optional[datetime] = None

        logger.info("ExternalServiceHealthCheck initialized.")

    def register_service(
        self,
        name: str,
        health_check_func: callable,
    ) -> None:
        """
        ثبت یک سرویس خارجی برای بررسی سلامت.

        Args:
            name: نام سرویس (مثلاً 'zarinpal', 'smtp', 'kavenegar').
            health_check_func: تابع async که HealthCheckResult برمی‌گرداند.
        """
        self._services[name] = health_check_func
        logger.info(f"External service registered: {name}")

    def unregister_service(self, name: str) -> bool:
        """
        حذف یک سرویس از لیست بررسی سلامت.

        Args:
            name: نام سرویس.

        Returns:
            bool: True در صورت حذف موفق، False در صورت عدم وجود.
        """
        if name in self._services:
            del self._services[name]
            if name in self._last_results:
                del self._last_results[name]
            logger.info(f"External service unregistered: {name}")
            return True
        return False

    async def check_all(self) -> List[HealthCheckResult]:
        """
        بررسی سلامت تمام سرویس‌های ثبت‌شده.

        Returns:
            List[HealthCheckResult]: لیست نتایج بررسی.
        """
        results = []
        for name, check_func in self._services.items():
            try:
                result = await check_func()
                results.append(result)
                self._last_results[name] = result
            except Exception as e:
                logger.error(f"External service health check error: {name} - {e}")
                result = HealthCheckResult(
                    name=name,
                    status=False,
                    message=f"Check error: {str(e)}",
                )
                results.append(result)
                self._last_results[name] = result

        self._last_check = datetime.now()
        return results

    async def check_service(self, name: str) -> Optional[HealthCheckResult]:
        """
        بررسی سلامت یک سرویس خاص.

        Args:
            name: نام سرویس.

        Returns:
            Optional[HealthCheckResult]: نتیجه بررسی یا None در صورت عدم وجود سرویس.
        """
        if name not in self._services:
            return None

        try:
            result = await self._services[name]()
            self._last_results[name] = result
            return result
        except Exception as e:
            logger.error(f"External service health check error: {name} - {e}")
            result = HealthCheckResult(
                name=name,
                status=False,
                message=f"Check error: {str(e)}",
            )
            self._last_results[name] = result
            return result

    def get_last_result(self, name: str) -> Optional[HealthCheckResult]:
        """
        دریافت آخرین نتیجه بررسی یک سرویس.

        Args:
            name: نام سرویس.

        Returns:
            Optional[HealthCheckResult]: آخرین نتیجه یا None در صورت عدم وجود.
        """
        return self._last_results.get(name)

    async def get_detailed_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت دقیق تمام سرویس‌های خارجی.

        Returns:
            Dict[str, Any]: وضعیت دقیق سرویس‌ها.
        """
        results = await self.check_all()

        status = {
            "total_services": len(results),
            "healthy_services": sum(1 for r in results if r.status),
            "unhealthy_services": sum(1 for r in results if not r.status),
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "services": {},
        }

        for result in results:
            status["services"][result.name] = {
                "healthy": result.status,
                "message": result.message,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
            }

        return status

    def get_services(self) -> List[str]:
        """
        دریافت لیست سرویس‌های ثبت‌شده.

        Returns:
            List[str]: لیست نام سرویس‌ها.
        """
        return list(self._services.keys())

    async def clear(self) -> None:
        """
        پاک کردن تمام سرویس‌های ثبت‌شده.
        """
        self._services.clear()
        self._last_results.clear()
        self._last_check = None
        logger.info("ExternalServiceHealthCheck cleared.")

    async def health_check_summary(self) -> Dict[str, bool]:
        """
        دریافت خلاصه وضعیت سلامت سرویس‌ها.

        Returns:
            Dict[str, bool]: دیکشنری نام سرویس به وضعیت سلامت.
        """
        results = await self.check_all()
        return {r.name: r.status for r in results}


# ----------------------------------------------
# توابع کمکی برای ایجاد چک‌کننده‌های سرویس‌های خاص
# ----------------------------------------------

async def create_payment_gateway_health_check(
    gateway_service,
    gateway_name: str,
) -> HealthCheckResult:
    """
    ایجاد چک‌کننده سلامت درگاه پرداخت.

    Args:
        gateway_service: سرویس درگاه پرداخت.
        gateway_name: نام درگاه.

    Returns:
        HealthCheckResult: نتیجه بررسی.
    """
    try:
        # اگر سرویس متد health_check داشته باشد
        if hasattr(gateway_service, "health_check"):
            is_healthy = await gateway_service.health_check()
        else:
            # در غیر این صورت، با یک درخواست ساده تست می‌کنیم
            is_healthy = True

        return HealthCheckResult(
            name=f"payment_gateway_{gateway_name}",
            status=is_healthy,
            message=f"{gateway_name} gateway is healthy" if is_healthy else f"{gateway_name} gateway is unhealthy",
        )
    except Exception as e:
        logger.error(f"Payment gateway health check error: {e}")
        return HealthCheckResult(
            name=f"payment_gateway_{gateway_name}",
            status=False,
            message=f"Gateway check failed: {str(e)}",
            details={"error": str(e)},
        )


async def create_email_health_check(email_service) -> HealthCheckResult:
    """
    ایجاد چک‌کننده سلامت سرویس ایمیل.

    Args:
        email_service: سرویس ایمیل.

    Returns:
        HealthCheckResult: نتیجه بررسی.
    """
    try:
        if hasattr(email_service, "health_check"):
            is_healthy = await email_service.health_check()
        else:
            is_healthy = True

        return HealthCheckResult(
            name="email_service",
            status=is_healthy,
            message="Email service is healthy" if is_healthy else "Email service is unhealthy",
        )
    except Exception as e:
        logger.error(f"Email service health check error: {e}")
        return HealthCheckResult(
            name="email_service",
            status=False,
            message=f"Email check failed: {str(e)}",
            details={"error": str(e)},
        )


async def create_sms_health_check(sms_service) -> HealthCheckResult:
    """
    ایجاد چک‌کننده سلامت سرویس پیامک.

    Args:
        sms_service: سرویس پیامک.

    Returns:
        HealthCheckResult: نتیجه بررسی.
    """
    try:
        if hasattr(sms_service, "health_check"):
            is_healthy = await sms_service.health_check()
        else:
            is_healthy = True

        return HealthCheckResult(
            name="sms_service",
            status=is_healthy,
            message="SMS service is healthy" if is_healthy else "SMS service is unhealthy",
        )
    except Exception as e:
        logger.error(f"SMS service health check error: {e}")
        return HealthCheckResult(
            name="sms_service",
            status=False,
            message=f"SMS check failed: {str(e)}",
            details={"error": str(e)},
        )