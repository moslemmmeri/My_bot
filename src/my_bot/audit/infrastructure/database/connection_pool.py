# my_bot_project/src/my_bot/infrastructure/database/connection_pool.py
"""
مدیریت Connection Pool دیتابیس (Connection Pool).

این ماژول شامل کلاس `ConnectionPool` است که مدیریت مستقیم Connection Pool
را با استفاده از SQLAlchemy انجام می‌دهد. این کلاس مکمل `DatabaseSessionManager`
است و کنترل بیشتری روی اتصالات فراهم می‌کند.
"""

import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from sqlalchemy import text

from my_bot.core.config.db_config import DBConfig
from my_bot.core.exceptions.db_errors import (
    DatabaseError,
    ConnectionError,
    PoolError,
)
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class ConnectionPool:
    """
    مدیریت Connection Pool دیتابیس.

    این کلاس مسئولیت مدیریت مستقیم Connection Pool را بر عهده دارد
    و امکان دریافت و بازگرداندن اتصالات، بررسی سلامت و وضعیت Pool را فراهم می‌کند.

    Attributes:
        config: پیکربندی دیتابیس.
        engine: موتور SQLAlchemy (AsyncEngine).
        _is_initialized: وضعیت مقداردهی اولیه.
        _pool_size: تعداد اتصالات اولیه.
        _max_overflow: حداکثر اتصالات اضافی.
        _pool_timeout: زمان انتظار برای گرفتن اتصال.
        _pool_recycle: زمان بازیابی اتصالات.
    """

    def __init__(self, config: DBConfig) -> None:
        """
        مقداردهی اولیه Connection Pool.

        Args:
            config: پیکربندی دیتابیس.
        """
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._is_initialized = False
        self._pool_size = config.pool_size
        self._max_overflow = config.max_overflow
        self._pool_timeout = config.pool_timeout
        self._pool_recycle = config.pool_recycle
        self._active_connections: int = 0
        self._connection_lock = asyncio.Lock()

        logger.info(
            f"ConnectionPool initialized: pool_size={self._pool_size}, "
            f"max_overflow={self._max_overflow}, timeout={self._pool_timeout}"
        )

    async def initialize(self) -> None:
        """
        مقداردهی اولیه Connection Pool.

        Raises:
            ConnectionError: در صورت بروز خطا در ایجاد Pool.
        """
        if self._is_initialized:
            logger.warning("ConnectionPool already initialized.")
            return

        try:
            # ایجاد موتور با استفاده از DatabaseSessionManager یا مستقیم
            from my_bot.infrastructure.database.session_manager import DatabaseSessionManager
            session_manager = DatabaseSessionManager(self.config)
            await session_manager.initialize()
            self._engine = session_manager._engine

            if not self._engine:
                raise ConnectionError(reason="Failed to create database engine.")

            # تست اتصال
            await self._test_connection()

            self._is_initialized = True
            logger.info("ConnectionPool initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize ConnectionPool: {e}")
            raise ConnectionError(reason=str(e))

    async def _test_connection(self) -> None:
        """
        تست اتصال به دیتابیس.

        Raises:
            ConnectionError: در صورت عدم موفقیت در تست اتصال.
        """
        if not self._engine:
            raise ConnectionError(reason="Engine not initialized.")

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.debug("Connection pool test successful.")

        except Exception as e:
            logger.error(f"Connection pool test failed: {e}")
            raise ConnectionError(reason=f"Connection test failed: {str(e)}")

    @asynccontextmanager
    async def get_connection(self) -> AsyncConnection:
        """
        دریافت یک اتصال از Connection Pool.

        این متد یک Context Manager است که یک اتصال async از Pool دریافت می‌کند
        و پس از اتمام کار، آن را به‌صورت خودکار بازمی‌گرداند.

        Yields:
            AsyncConnection: اتصال دیتابیس.

        Raises:
            PoolError: در صورت عدم موفقیت در دریافت اتصال.
        """
        if not self._is_initialized:
            await self.initialize()

        if not self._engine:
            raise PoolError(
                operation="get_connection",
                reason="Engine not initialized.",
            )

        connection: Optional[AsyncConnection] = None
        try:
            # دریافت اتصال از Pool
            async with self._connection_lock:
                connection = await self._engine.connect()
                self._active_connections += 1
                logger.debug(f"Connection acquired. Active: {self._active_connections}")

            yield connection

        except asyncio.TimeoutError:
            logger.error("Timeout while waiting for connection from pool.")
            raise PoolError(
                operation="get_connection",
                reason=f"Timeout waiting for connection (timeout={self._pool_timeout}s)",
            )

        except Exception as e:
            logger.error(f"Error acquiring connection: {e}")
            raise PoolError(
                operation="get_connection",
                reason=str(e),
            )

        finally:
            if connection:
                await connection.close()
                async with self._connection_lock:
                    self._active_connections -= 1
                    logger.debug(f"Connection released. Active: {self._active_connections}")

    async def get_raw_connection(self) -> AsyncConnection:
        """
        دریافت یک اتصال خام از Connection Pool (بدون Context Manager).

        توجه: در صورت استفاده از این متد، مسئولیت بستن اتصال بر عهده کاربر است.

        Returns:
            AsyncConnection: اتصال دیتابیس.

        Raises:
            PoolError: در صورت عدم موفقیت در دریافت اتصال.
        """
        if not self._is_initialized:
            await self.initialize()

        if not self._engine:
            raise PoolError(
                operation="get_raw_connection",
                reason="Engine not initialized.",
            )

        try:
            connection = await self._engine.connect()
            async with self._connection_lock:
                self._active_connections += 1
                logger.debug(f"Raw connection acquired. Active: {self._active_connections}")
            return connection

        except Exception as e:
            logger.error(f"Error acquiring raw connection: {e}")
            raise PoolError(
                operation="get_raw_connection",
                reason=str(e),
            )

    async def release_connection(self, connection: AsyncConnection) -> None:
        """
        بازگرداندن یک اتصال به Pool.

        Args:
            connection: اتصال برای بازگرداندن.

        Raises:
            PoolError: در صورت بروز خطا در بازگرداندن اتصال.
        """
        try:
            await connection.close()
            async with self._connection_lock:
                self._active_connections = max(0, self._active_connections - 1)
                logger.debug(f"Connection released manually. Active: {self._active_connections}")

        except Exception as e:
            logger.error(f"Error releasing connection: {e}")
            raise PoolError(
                operation="release_connection",
                reason=str(e),
            )

    async def health_check(self) -> bool:
        """
        بررسی سلامت Connection Pool.

        Returns:
            bool: True در صورت سالم بودن Pool.
        """
        if not self._is_initialized:
            return False

        try:
            async with self.get_connection() as conn:
                await conn.execute(text("SELECT 1"))
            return True

        except Exception as e:
            logger.warning(f"Connection pool health check failed: {e}")
            return False

    async def get_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت Connection Pool.

        Returns:
            Dict[str, Any]: اطلاعات وضعیت Pool.
        """
        status = {
            "is_initialized": self._is_initialized,
            "pool_size": self._pool_size,
            "max_overflow": self._max_overflow,
            "pool_timeout": self._pool_timeout,
            "pool_recycle": self._pool_recycle,
            "active_connections": self._active_connections,
            "db_type": self.config.db_type(),
            "url": self.config.url[:30] + "...",
        }

        if self._engine:
            try:
                pool = self._engine.pool
                if pool:
                    status["pool_stats"] = {
                        "size": pool.size(),
                        "checkedin": pool.checkedin(),
                        "overflow": pool.overflow(),
                        "total": pool.total(),
                        "checkedout": pool.checkedout(),
                    }
            except Exception as e:
                logger.warning(f"Could not get pool stats: {e}")
                status["pool_stats_error"] = str(e)

        return status

    async def clear_pool(self) -> None:
        """
        پاک کردن (بازنشانی) Connection Pool.

        تمام اتصالات موجود در Pool بسته می‌شوند.
        """
        if self._engine:
            await self._engine.dispose()
            self._active_connections = 0
            logger.info("Connection pool cleared.")

    async def close(self) -> None:
        """
        بستن کامل Connection Pool و آزادسازی منابع.
        """
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._is_initialized = False
            self._active_connections = 0
            logger.info("Connection pool closed successfully.")

    def get_pool_size(self) -> int:
        """
        دریافت اندازه فعلی Pool.

        Returns:
            int: اندازه Pool.
        """
        if self._engine and self._engine.pool:
            try:
                return self._engine.pool.size()
            except Exception:
                pass
        return self._pool_size

    def get_active_connections_count(self) -> int:
        """
        دریافت تعداد اتصالات فعال.

        Returns:
            int: تعداد اتصالات فعال.
        """
        return self._active_connections

    async def wait_for_connections(self, timeout: float = 30.0) -> bool:
        """
        انتظار برای آزاد شدن اتصالات.

        Args:
            timeout: زمان انتظار بر حسب ثانیه.

        Returns:
            bool: True در صورت آزاد شدن تمام اتصالات.
        """
        start_time = asyncio.get_event_loop().time()
        while self._active_connections > 0:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"Timeout waiting for connections to release. Active: {self._active_connections}")
                return False
            await asyncio.sleep(0.1)
        return True