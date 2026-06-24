# my_bot_project/src/my_bot/presentation/web_api/routes/metrics.py
"""
مسیریاب متریک‌ها (Metrics Router).

این ماژول شامل کلاس `MetricsRouter` است که مسیر /metrics را برای
نمایش متریک‌های سیستم (مانند تعداد درخواست‌ها، زمان پاسخ، خطاها و ...)
فراهم می‌کند. این متریک‌ها برای مانیتورینگ و نظارت بر عملکرد سیستم
استفاده می‌شوند.

متریک‌های ارائه‌شده:
- تعداد درخواست‌های دریافتی
- تعداد خطاها
- میانگین زمان پاسخ
- تعداد درخواست‌های فعال
- متریک‌های سفارشی قابل توسعه
"""

import time
import json
from typing import Dict, Any, Optional, List
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from aiohttp import web
from aiohttp.web import Request, Response, json_response

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass
class MetricsCollector:
    """
    جمع‌آوری‌کننده متریک‌ها.

    این کلاس مسئولیت جمع‌آوری و نگهداری متریک‌های سیستم را بر عهده دارد.

    Attributes:
        request_count: تعداد کل درخواست‌ها.
        error_count: تعداد کل خطاها.
        total_response_time: مجموع زمان پاسخ‌ها (میلی‌ثانیه).
        active_requests: تعداد درخواست‌های فعال.
        endpoint_stats: آمار به‌تفکیک endpoint.
        start_time: زمان شروع جمع‌آوری متریک‌ها.
    """

    request_count: int = 0
    error_count: int = 0
    total_response_time: float = 0.0
    active_requests: int = 0
    endpoint_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float) -> None:
        """
        ثبت یک درخواست جدید.

        Args:
            endpoint: آدرس endpoint.
            method: متد HTTP.
            status_code: کد وضعیت پاسخ.
            duration_ms: زمان پاسخ بر حسب میلی‌ثانیه.
        """
        self.request_count += 1
        self.total_response_time += duration_ms

        # آمار endpoint
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                "count": 0,
                "errors": 0,
                "total_time": 0.0,
                "methods": defaultdict(int),
                "status_codes": defaultdict(int),
            }

        stats = self.endpoint_stats[endpoint]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["methods"][method] += 1
        stats["status_codes"][status_code] += 1

        if status_code >= 400:
            self.error_count += 1
            stats["errors"] += 1

    def start_request(self) -> None:
        """افزایش تعداد درخواست‌های فعال."""
        self.active_requests += 1

    def finish_request(self) -> None:
        """کاهش تعداد درخواست‌های فعال."""
        if self.active_requests > 0:
            self.active_requests -= 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        دریافت تمام متریک‌های جمع‌آوری‌شده.

        Returns:
            Dict[str, Any]: متریک‌ها.
        """
        uptime_seconds = time.time() - self.start_time
        avg_response_time = self.total_response_time / self.request_count if self.request_count > 0 else 0

        # آماده‌سازی آمار endpointها
        endpoints = {}
        for name, stats in self.endpoint_stats.items():
            endpoints[name] = {
                "count": stats["count"],
                "errors": stats["errors"],
                "avg_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0,
                "methods": dict(stats["methods"]),
                "status_codes": dict(stats["status_codes"]),
            }

        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            "active_requests": self.active_requests,
            "average_response_time_ms": round(avg_response_time, 2),
            "total_response_time_ms": round(self.total_response_time, 2),
            "uptime_seconds": round(uptime_seconds, 2),
            "endpoints": endpoints,
            "timestamp": datetime.now().isoformat(),
        }


class MetricsRouter:
    """
    مسیریاب متریک‌ها.

    این کلاس با استفاده از MetricsCollector، متریک‌های سیستم را
    جمع‌آوری کرده و در مسیر /metrics به‌صورت JSON یا Prometheus
    در دسترس قرار می‌دهد.

    Attributes:
        collector: جمع‌آوری‌کننده متریک‌ها.
        format: فرمت خروجی ('json' یا 'prometheus').
    """

    def __init__(self, format: str = "json") -> None:
        """
        مقداردهی اولیه مسیریاب متریک‌ها.

        Args:
            format: فرمت خروجی ('json' یا 'prometheus') (پیش‌فرض 'json').
        """
        self.collector = MetricsCollector()
        self.format = format

        # میدلور برای ثبت خودکار درخواست‌ها
        self._middleware = self._create_middleware()

        logger.info(f"MetricsRouter initialized with format={format}")

    def _create_middleware(self):
        """
        ایجاد میدلور برای ثبت خودکار متریک‌ها.

        Returns:
            Callable: میدلور aiohttp.
        """
        @web.middleware
        async def metrics_middleware(request: Request, handler):
            # ثبت شروع درخواست
            self.collector.start_request()
            start_time = time.time()

            try:
                # پردازش درخواست
                response = await handler(request)

                # محاسبه زمان پاسخ
                duration_ms = (time.time() - start_time) * 1000

                # ثبت متریک‌ها
                endpoint = request.path
                method = request.method
                status_code = response.status

                self.collector.record_request(endpoint, method, status_code, duration_ms)

                return response

            except Exception as e:
                # ثبت خطا
                duration_ms = (time.time() - start_time) * 1000
                endpoint = request.path
                method = request.method

                self.collector.record_request(endpoint, method, 500, duration_ms)

                # propagate خطا به بالا
                raise

            finally:
                # کاهش تعداد درخواست‌های فعال
                self.collector.finish_request()

        return metrics_middleware

    def get_middleware(self):
        """
        دریافت میدلور ثبت متریک‌ها.

        Returns:
            Callable: میدلور aiohttp.
        """
        return self._middleware

    async def handle_metrics(self, request: Request) -> Response:
        """
        هندلر مسیر /metrics برای نمایش متریک‌ها.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ با متریک‌ها در فرمت درخواستی.
        """
        # دریافت پارامتر format از query string (در صورت وجود)
        format_param = request.query.get("format", self.format)

        if format_param == "prometheus":
            return await self._handle_prometheus(request)
        else:
            return await self._handle_json(request)

    async def _handle_json(self, request: Request) -> Response:
        """
        نمایش متریک‌ها به‌صورت JSON.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ JSON.
        """
        metrics = self.collector.get_metrics()
        return json_response(data=metrics, status=200)

    async def _handle_prometheus(self, request: Request) -> Response:
        """
        نمایش متریک‌ها به‌صورت فرمت Prometheus.

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ با فرمت Prometheus.
        """
        metrics = self.collector.get_metrics()

        # ساخت رشته Prometheus
        lines = [
            "# HELP http_requests_total Total number of HTTP requests",
            "# TYPE http_requests_total counter",
            f"http_requests_total {metrics['total_requests']}",
            "",
            "# HELP http_errors_total Total number of HTTP errors",
            "# TYPE http_errors_total counter",
            f"http_errors_total {metrics['total_errors']}",
            "",
            "# HELP http_active_requests Current number of active requests",
            "# TYPE http_active_requests gauge",
            f"http_active_requests {metrics['active_requests']}",
            "",
            "# HELP http_request_duration_seconds HTTP request duration in seconds",
            "# TYPE http_request_duration_seconds summary",
            f"http_request_duration_seconds_count {metrics['total_requests']}",
            f"http_request_duration_seconds_sum {metrics['total_response_time_ms'] / 1000}",
            "",
            "# HELP http_average_response_time_ms Average response time in milliseconds",
            "# TYPE http_average_response_time_ms gauge",
            f"http_average_response_time_ms {metrics['average_response_time_ms']}",
            "",
            "# HELP process_uptime_seconds Process uptime in seconds",
            "# TYPE process_uptime_seconds gauge",
            f"process_uptime_seconds {metrics['uptime_seconds']}",
            "",
            "# HELP endpoint_requests_total Total requests per endpoint",
            "# TYPE endpoint_requests_total counter",
        ]

        # متریک‌های endpoint
        for endpoint, stats in metrics["endpoints"].items():
            for method, count in stats["methods"].items():
                lines.append(
                    f'endpoint_requests_total{{endpoint="{endpoint}",method="{method}"}} {count}'
                )

        lines.append("")

        lines.append("# HELP endpoint_errors_total Total errors per endpoint")
        lines.append("# TYPE endpoint_errors_total counter")
        for endpoint, stats in metrics["endpoints"].items():
            lines.append(
                f'endpoint_errors_total{{endpoint="{endpoint}"}} {stats["errors"]}'
            )

        lines.append("")

        lines.append("# HELP endpoint_avg_time_ms Average response time per endpoint")
        lines.append("# TYPE endpoint_avg_time_ms gauge")
        for endpoint, stats in metrics["endpoints"].items():
            lines.append(
                f'endpoint_avg_time_ms{{endpoint="{endpoint}"}} {stats["avg_time"]}'
            )

        # پاسخ
        return web.Response(
            text="\n".join(lines),
            content_type="text/plain; version=0.0.4; charset=utf-8",
            status=200,
        )

    async def clear_metrics(self, request: Request) -> Response:
        """
        پاک کردن متریک‌ها (برای استفاده در تست یا مدیریت).

        Args:
            request: درخواست HTTP.

        Returns:
            Response: پاسخ تأیید.
        """
        # بازنشانی collector
        self.collector = MetricsCollector()
        logger.info("Metrics cleared.")

        return json_response(
            data={"status": "success", "message": "Metrics cleared"},
            status=200,
        )

    def get_collector(self) -> MetricsCollector:
        """
        دریافت جمع‌آوری‌کننده متریک‌ها (برای استفاده در سایر بخش‌ها).

        Returns:
            MetricsCollector: جمع‌آوری‌کننده متریک‌ها.
        """
        return self.collector

    async def get_metrics_dict(self) -> Dict[str, Any]:
        """
        دریافت متریک‌ها به‌صورت دیکشنری (برای استفاده در پنل مدیریت).

        Returns:
            Dict[str, Any]: متریک‌ها.
        """
        return self.collector.get_metrics()

    def reset_metrics(self) -> None:
        """
        بازنشانی متریک‌ها.
        """
        self.collector = MetricsCollector()
        logger.info("Metrics collector reset.")


# ----------------------------------------------
# تابع کمکی برای ایجاد مسیریاب با میدلور
# ----------------------------------------------

def create_metrics_middleware(metrics_router: MetricsRouter):
    """
    ایجاد میدلور ثبت متریک‌ها برای استفاده در aiohttp Application.

    Args:
        metrics_router: نمونه MetricsRouter.

    Returns:
        Callable: میدلور aiohttp.
    """
    return metrics_router.get_middleware()