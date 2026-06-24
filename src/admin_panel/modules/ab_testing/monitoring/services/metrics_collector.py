# src/admin_panel/modules/monitoring/services/metrics_collector.py
import asyncio
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from my_bot.core.exceptions import DatabaseError, CacheError
from my_bot.core.logger import get_logger
from my_bot.core.config import Config
from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
from my_bot.infrastructure.cache.cache_manager import CacheManager

try:
    import psutil
except ImportError:
    psutil = None

logger = get_logger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data."""
    cpu_percent: float = 0.0
    cpu_cores: int = 0
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0
    network_in: int = 0
    network_out: int = 0
    process_count: int = 0
    thread_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "cpu_cores": self.cpu_cores,
            "memory_total": self.memory_total,
            "memory_available": self.memory_available,
            "memory_used": self.memory_used,
            "memory_percent": self.memory_percent,
            "disk_total": self.disk_total,
            "disk_used": self.disk_used,
            "disk_free": self.disk_free,
            "disk_percent": self.disk_percent,
            "network_in": self.network_in,
            "network_out": self.network_out,
            "process_count": self.process_count,
            "thread_count": self.thread_count,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    """Service for collecting system and application metrics."""

    def __init__(
        self,
        config: Optional[Config] = None,
        db_manager: Optional[DatabaseSessionManager] = None,
        cache_manager: Optional[CacheManager] = None,
    ) -> None:
        self.config = config or Config.from_env()
        self.db_manager = db_manager or DatabaseSessionManager(
            self.config.db_url,
            self.config.db_pool_size,
            self.config.db_max_overflow,
        )
        self.cache_manager = cache_manager or CacheManager(
            self.config.redis_url,
            self.config.cache_ttl_seconds,
        )
        self._last_metrics: Optional[SystemMetrics] = None

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        if psutil is None:
            logger.warning("psutil not installed. System metrics may be incomplete.")
            return SystemMetrics()

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_cores = psutil.cpu_count(logical=True) or 0

            # Memory
            mem = psutil.virtual_memory()
            memory_total = mem.total
            memory_available = mem.available
            memory_used = mem.used
            memory_percent = mem.percent

            # Disk
            disk = psutil.disk_usage('/')
            disk_total = disk.total
            disk_used = disk.used
            disk_free = disk.free
            disk_percent = disk.percent

            # Network (since last call)
            net = psutil.net_io_counters()
            network_in = net.bytes_recv
            network_out = net.bytes_sent

            # Process
            process_count = len(psutil.pids())
            thread_count = 0
            for pid in psutil.pids():
                try:
                    proc = psutil.Process(pid)
                    thread_count += proc.num_threads()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_cores=cpu_cores,
                memory_total=memory_total,
                memory_available=memory_available,
                memory_used=memory_used,
                memory_percent=memory_percent,
                disk_total=disk_total,
                disk_used=disk_used,
                disk_free=disk_free,
                disk_percent=disk_percent,
                network_in=network_in,
                network_out=network_out,
                process_count=process_count,
                thread_count=thread_count,
                timestamp=datetime.now(),
            )
            self._last_metrics = metrics
            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}", exc_info=True)
            raise DatabaseError("Failed to collect system metrics.") from e

    async def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database connection pool and query statistics."""
        try:
            # Get pool stats
            pool_stats = await self.db_manager.get_pool_stats()

            # Get database size
            db_size = await self._get_database_size()

            return {
                "pool_connections": pool_stats.get("connections", 0),
                "pool_active": pool_stats.get("active", 0),
                "pool_idle": pool_stats.get("idle", 0),
                "pool_max": pool_stats.get("max", 0),
                "db_size_mb": db_size,
                "status": "healthy",
            }
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}", exc_info=True)
            return {
                "pool_connections": 0,
                "pool_active": 0,
                "pool_idle": 0,
                "pool_max": 0,
                "db_size_mb": 0,
                "status": "error",
                "error": str(e),
            }

    async def _get_database_size(self) -> float:
        """Get database size in MB."""
        try:
            db_url = self.config.db_url
            if "sqlite" in db_url:
                db_path = db_url.replace("sqlite:///", "")
                import os
                size = os.path.getsize(db_path) / (1024 * 1024)
                return size
            elif "postgresql" in db_url or "postgres" in db_url:
                # Query for database size
                async with self.db_manager.get_session() as session:
                    result = await session.execute(
                        "SELECT pg_database_size(current_database()) / (1024*1024) as size"
                    )
                    row = result.first()
                    return float(row[0]) if row else 0
            else:
                return 0
        except Exception as e:
            logger.warning(f"Failed to get database size: {e}")
            return 0

    async def collect_cache_metrics(self) -> Dict[str, Any]:
        """Collect cache statistics."""
        try:
            status = await self.cache_manager.get_status()
            return {
                "type": status.get("type", "local"),
                "connected": status.get("connected", False),
                "keys_count": status.get("keys_count", 0),
                "memory_usage": status.get("memory_usage", 0),
                "hit_rate": status.get("hit_rate", 0.0),
                "status": "healthy" if status.get("connected") else "unhealthy",
            }
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}", exc_info=True)
            return {
                "type": "unknown",
                "connected": False,
                "keys_count": 0,
                "memory_usage": 0,
                "hit_rate": 0.0,
                "status": "error",
                "error": str(e),
            }

    async def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics (requests, errors, etc.)."""
        # In a real implementation, you might get this from a metrics registry
        # For now, we'll return dummy data
        return {
            "uptime_seconds": int(time.time() - self._get_start_time()),
            "total_requests": 0,  # Could be tracked via middleware
            "requests_per_second": 0,
            "total_errors": 0,
            "error_rate": 0.0,
            "avg_response_time_ms": 0,
        }

    def _get_start_time(self) -> float:
        """Get process start time."""
        try:
            if psutil:
                proc = psutil.Process(os.getpid())
                return proc.create_time()
            return time.time()
        except Exception:
            return time.time()

    async def get_full_metrics(self) -> Dict[str, Any]:
        """Collect all metrics and return a comprehensive dictionary."""
        system = await self.collect_system_metrics()
        db = await self.collect_database_metrics()
        cache = await self.collect_cache_metrics()
        app = await self.collect_application_metrics()

        return {
            "system": system.to_dict(),
            "database": db,
            "cache": cache,
            "application": app,
            "collected_at": datetime.now().isoformat(),
        }