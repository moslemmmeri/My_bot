# my_bot_project/src/my_bot/presentation/web_api/web_app.py
"""
برنامه وب (Web App) برای پشتیبانی از وب‌هوک و APIهای HTTP.

این ماژول شامل کلاس `WebApp` است که یک سرویس وب با استفاده از aiohttp
راه‌اندازی می‌کند و مسیرهای مربوط به وب‌هوک، سلامت و متریک‌ها را ثبت می‌کند.
"""

import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable

from aiohttp import web, ClientTimeout, TCPConnector
from aiohttp.web import Application, Request, Response, json_response

from my_bot.core.config.app_config import AppConfig
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.web_api.routes.webhook import WebhookRouter
from my_bot.presentation.web_api.routes.health import HealthRouter
from my_bot.presentation.web_api.routes.metrics import MetricsRouter
from my_bot.infrastructure.health_check.health_checker import HealthChecker
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.cache.cache_manager import CacheManager

logger = get_logger(__name__)


class WebApp:
    """
    سرویس وب برای مدیریت وب‌هوک و APIهای HTTP.

    این کلاس با استفاده از aiohttp، یک وب‌سرویس راه‌اندازی می‌کند
    و مسیرهای مختلف را ثبت می‌نماید.

    Attributes:
        config: پیکربندی برنامه.
        health_checker: بررسی کننده سلامت سیستم.
        db_manager: مدیر جلسات دیتابیس.
        cache_manager: مدیر کش.
        webhook_router: مسیریاب وب‌هوک.
        health_router: مسیریاب سلامت.
        metrics_router: مسیریاب متریک‌ها.
        _app: نمونه aiohttp Application.
        _runner: نمونه aiohttp AppRunner.
        _site: نمونه aiohttp TCPSite.
        _is_running: وضعیت اجرای سرویس.
    """

    def __init__(
        self,
        config: AppConfig,
        health_checker: Optional[HealthChecker] = None,
        db_manager: Optional[DatabaseSessionManager] = None,
        cache_manager: Optional[CacheManager] = None,
        webhook_router: Optional[WebhookRouter] = None,
        health_router: Optional[HealthRouter] = None,
        metrics_router: Optional[MetricsRouter] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس وب.

        Args:
            config: پیکربندی برنامه.
            health_checker: بررسی کننده سلامت (اختیاری).
            db_manager: مدیر دیتابیس (اختیاری).
            cache_manager: مدیر کش (اختیاری).
            webhook_router: مسیریاب وب‌هوک (اختیاری).
            health_router: مسیریاب سلامت (اختیاری).
            metrics_router: مسیریاب متریک‌ها (اختیاری).
        """
        self.config = config
        self.health_checker = health_checker
        self.db_manager = db_manager
        self.cache_manager = cache_manager

        # ایجاد مسیریاب‌ها (اگر ارائه نشده باشند)
        self.webhook_router = webhook_router or WebhookRouter()
        self.health_router = health_router or HealthRouter(health_checker)
        self.metrics_router = metrics_router or MetricsRouter()

        # نمونه aiohttp
        self._app: Optional[Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._is_running = False

        logger.info(
            f"WebApp initialized: webhook_port={config.webhook_port}, "
            f"enable_webhook={config.enable_webhook}"
        )

    def _create_app(self) -> Application:
        """
        ایجاد نمونه aiohttp Application و ثبت مسیرها.

        Returns:
            Application: نمونه aiohttp Application.
        """
        app = web.Application()

        # ثبت مسیرها
        app.router.add_post("/webhook", self.webhook_router.handle_webhook)
        app.router.add_get("/health", self.health_router.handle_health)
        app.router.add_get("/health/ready", self.health_router.handle_readiness)
        app.router.add_get("/health/live", self.health_router.handle_liveness)
        app.router.add_get("/metrics", self.metrics_router.handle_metrics)
        app.router.add_get("/", self._handle_root)

        # میدلورهای عمومی
        app.middlewares.append(self._error_middleware)
        app.middlewares.append(self._logging_middleware)

        # رویدادهای startup/shutdown
        app.on_startup.append(self._on_startup)
        app.on_shutdown.append(self._on_shutdown)

        self._app = app
        return app

    async def _on_startup(self, app: Application) -> None:
        """
        عملیات راه‌اندازی سرویس وب.

        Args:
            app: نمونه aiohttp Application.
        """
        logger.info("Starting web application...")
        # در صورت نیاز، می‌توان عملیات اولیه مانند اتصال به دیتابیس را انجام داد
        # اما این کار معمولاً در bootstrap انجام می‌شود

    async def _on_shutdown(self, app: Application) -> None:
        """
        عملیات خاموش‌سازی سرویس وب.

        Args:
            app: نمونه aiohttp Application.
        """
        logger.info("Shutting down web application...")
        # آزادسازی منابع در صورت نیاز

    @web.middleware
    async def _error_middleware(self, request: Request, handler: Callable) -> Response:
        """
        میدلور مدیریت خطاهای سراسری.

        Args:
            request: درخواست HTTP.
            handler: هندلر بعدی.

        Returns:
            Response: پاسخ HTTP.
        """
        try:
            return await handler(request)
        except Exception as e:
            logger.error(f"Unhandled error in web request: {e}", exc_info=True)
            return json_response(
                status=500,
                data={"error": "Internal server error", "message": str(e)},
            )

    @web.middleware
    async def _logging_middleware(self, request: Request, handler: Callable) -> Response:
        """
        میدلور ثبت لاگ درخواست‌ها.

        Args:
            request: درخواست HTTP.
            handler: هندلر بعدی.

        Returns:
            Response: پاسخ HTTP.
        """
        logger.info(
            f"Web request: {request.method} {request.path} "
            f"from {request.remote}"
        )
        return await handler(request)

    async def _handle_root(self, request: Request) -> Response:
        """
        هندلر مسیر ریشه (برای نمایش اطلاعات سرویس).

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ JSON.
        """
        return json_response({
            "service": "my_bot_web_api",
            "version": "1.0.0",
            "status": "running",
            "endpoints": [
                "/webhook",
                "/health",
                "/health/ready",
                "/health/live",
                "/metrics",
            ],
        })

    async def start(self) -> None:
        """
        راه‌اندازی سرویس وب.

        Raises:
            RuntimeError: اگر سرویس قبلاً راه‌اندازی شده باشد.
        """
        if self._is_running:
            raise RuntimeError("Web application is already running.")

        if not self.config.enable_webhook:
            logger.info("Webhook is disabled. Web application will not start.")
            return

        # ایجاد نمونه Application
        app = self._create_app()

        # ایجاد Runner
        self._runner = web.AppRunner(app)
        await self._runner.setup()

        # ایجاد Site
        self._site = web.TCPSite(
            self._runner,
            host="0.0.0.0",  # گوش دادن به تمام interfaces
            port=self.config.webhook_port,
        )
        await self._site.start()

        self._is_running = True
        logger.info(
            f"Web application started on port {self.config.webhook_port}"
        )

    async def stop(self) -> None:
        """
        توقف سرویس وب.

        Raises:
            RuntimeError: اگر سرویس در حال اجرا نباشد.
        """
        if not self._is_running:
            logger.warning("Web application is not running.")
            return

        # توقف Site
        if self._site:
            await self._site.stop()
            self._site = None

        # توقف Runner
        if self._runner:
            await self._runner.cleanup()
            self._runner = None

        self._is_running = False
        logger.info("Web application stopped.")

    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس وب.

        Returns:
            bool: True اگر سرویس سالم باشد.
        """
        if not self._is_running:
            return False

        # بررسی اینکه آیا وب‌سرویس به درخواست‌ها پاسخ می‌دهد
        try:
            # درخواست تست به خودمان (از طریق localhost)
            # این کار ممکن است در برخی محیط‌ها ممکن نباشد، بنابراین یک بررسی ساده انجام می‌دهیم
            return True
        except Exception as e:
            logger.error(f"Web app health check failed: {e}")
            return False

    def is_running(self) -> bool:
        """
        بررسی در حال اجرا بودن سرویس وب.

        Returns:
            bool: True اگر سرویس در حال اجرا باشد.
        """
        return self._is_running

    async def wait_for_shutdown(self) -> None:
        """
        منتظر ماندن تا زمانی که سرویس وب متوقف شود.
        """
        while self._is_running:
            await asyncio.sleep(1)

    def get_app(self) -> Optional[Application]:
        """
        دریافت نمونه aiohttp Application (برای استفاده در تست‌ها).

        Returns:
            Optional[Application]: نمونه Application یا None.
        """
        return self._app

    async def run_forever(self) -> None:
        """
        اجرای سرویس وب تا زمانی که متوقف شود.

        این متد برای اجرای مستقل وب‌سرویس در یک تابع اصلی استفاده می‌شود.
        """
        await self.start()
        try:
            await self.wait_for_shutdown()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal.")
        finally:
            await self.stop()