# my_bot_project/src/my_bot/infrastructure/database/session_manager.py
"""
مدیریت جلسات دیتابیس (Database Session Manager).

این ماژول شامل کلاس `DatabaseSessionManager` است که مسئولیت مدیریت
جلسات (Sessions) دیتابیس را با استفاده از SQLAlchemy و Connection Pool
بر عهده دارد. از پیکربندی دیتابیس برای ایجاد Engine و SessionFactory استفاده می‌کند.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy import text

from my_bot.core.config.db_config import DBConfig
from my_bot.core.exceptions.db_errors import ConnectionError, DatabaseError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class DatabaseSessionManager:
    """
    مدیریت جلسات دیتابیس با Connection Pool.

    این کلاس با استفاده از SQLAlchemy، اتصالات دیتابیس را مدیریت می‌کند
    و SessionFactory را برای ایجاد جلسات async فراهم می‌آورد.

    Attributes:
        config: پیکربندی دیتابیس.
        engine: موتور SQLAlchemy (AsyncEngine).
        session_factory: کارخانه تولید جلسات async.
        _is_initialized: وضعیت مقداردهی اولیه.
    """

    def __init__(self, config: DBConfig) -> None:
        """
        مقداردهی اولیه مدیر جلسات.

        Args:
            config: پیکربندی دیتابیس.
        """
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._is_initialized = False
        self._pool_size = config.pool_size
        self._max_overflow = config.max_overflow
        self._pool_timeout = config.pool_timeout
        self._pool_recycle = config.pool_recycle

        logger.info(
            f"DatabaseSessionManager initialized with config: "
            f"url={config.url[:30]}..., "
            f"pool_size={config.pool_size}, "
            f"max_overflow={config.max_overflow}"
        )

    async def initialize(self) -> None:
        """
        مقداردهی اولیه موتور دیتابیس و Session Factory.

        این متد باید قبل از استفاده از SessionManager فراخوانی شود.

        Raises:
            ConnectionError: در صورت بروز خطا در اتصال به دیتابیس.
        """
        if self._is_initialized:
            logger.warning("DatabaseSessionManager already initialized.")
            return

        try:
            # ایجاد موتور async با تنظیمات Connection Pool
            self._engine = await self._create_engine()

            # ایجاد Session Factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            # تست اتصال
            await self._test_connection()

            self._is_initialized = True
            logger.info("DatabaseSessionManager initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize DatabaseSessionManager: {e}")
            raise ConnectionError(reason=str(e))

    async def _create_engine(self) -> AsyncEngine:
        """
        ایجاد موتور SQLAlchemy با تنظیمات Connection Pool.

        Returns:
            AsyncEngine: موتور async.

        Raises:
            DatabaseError: در صورت بروز خطا در ایجاد موتور.
        """
        try:
            # تبدیل URL به فرمت async (در صورت نیاز)
            async_url = self.config.get_async_url()

            # تنظیمات Connection Pool
            pool_kwargs = {
                "pool_size": self._pool_size,
                "max_overflow": self._max_overflow,
                "pool_timeout": self._pool_timeout,
                "pool_recycle": self._pool_recycle,
                "pool_pre_ping": True,  # بررسی سلامت اتصال قبل از استفاده
            }

            # برای SQLite از NullPool استفاده می‌کنیم (بدون Connection Pool)
            if self.config.is_sqlite():
                pool_class = NullPool
                pool_kwargs = {}
                logger.info("Using SQLite with NullPool (no connection pooling).")
            else:
                pool_class = AsyncAdaptedQueuePool
                logger.info(
                    f"Using PostgreSQL with AsyncAdaptedQueuePool: "
                    f"pool_size={self._pool_size}, "
                    f"max_overflow={self._max_overflow}"
                )

            # ایجاد موتور
            engine = create_async_engine(
                async_url,
                poolclass=pool_class,
                pool_pre_ping=True,
                echo=self.config.echo,
                **pool_kwargs,
            )

            return engine

        except Exception as e:
            logger.error(f"Error creating database engine: {e}")
            raise DatabaseError(
                message=f"خطا در ایجاد موتور دیتابیس: {str(e)}",
                context={"url": self.config.url[:30]},
            )

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
                # اجرای یک کوئری ساده برای تست اتصال
                await conn.execute(text("SELECT 1"))
                logger.debug("Database connection test successful.")

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise ConnectionError(reason=f"Connection test failed: {str(e)}")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager برای دریافت یک جلسه دیتابیس.

        این متد یک جلسه async از Session Factory دریافت می‌کند و
        پس از اتمام کار، آن را به‌صورت خودکار بسته می‌کند.

        Yields:
            AsyncSession: جلسه دیتابیس.

        Raises:
            DatabaseError: در صورت عدم وجود Session Factory.
            ConnectionError: در صورت بروز خطا در ایجاد جلسه.
        """
        if not self._is_initialized:
            await self.initialize()

        if not self._session_factory:
            raise DatabaseError(
                message="Session factory not initialized.",
                context={},
            )

        session: Optional[AsyncSession] = None
        try:
            session = self._session_factory()
            yield session
        except Exception as e:
            logger.error(f"Error in database session: {e}")
            if session:
                await session.rollback()
            raise ConnectionError(reason=f"Session error: {str(e)}")
        finally:
            if session:
                await session.close()

    async def get_session(self) -> AsyncSession:
        """
        دریافت یک جلسه دیتابیس (بدون Context Manager).

        برای استفاده در مواردی که نیاز به مدیریت دستی جلسه دارید.

        Returns:
            AsyncSession: جلسه دیتابیس.

        Raises:
            DatabaseError: در صورت عدم وجود Session Factory.
        """
        if not self._is_initialized:
            await self.initialize()

        if not self._session_factory:
            raise DatabaseError(
                message="Session factory not initialized.",
                context={},
            )

        return self._session_factory()

    async def close(self) -> None:
        """
        بستن تمام اتصالات و آزادسازی منابع.

        این متد باید در زمان خاموش شدن برنامه فراخوانی شود.
        """
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            logger.info("DatabaseSessionManager closed successfully.")

    async def health_check(self) -> bool:
        """
        بررسی سلامت اتصال دیتابیس.

        Returns:
            bool: True در صورت سالم بودن اتصال.
        """
        try:
            if not self._is_initialized:
                await self.initialize()

            async with self.session() as session:
                await session.execute(text("SELECT 1"))
                return True

        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    async def get_pool_status(self) -> dict:
        """
        دریافت وضعیت Connection Pool.

        Returns:
            dict: اطلاعات وضعیت Pool.
        """
        status = {
            "is_initialized": self._is_initialized,
            "pool_size": self._pool_size,
            "max_overflow": self._max_overflow,
            "pool_timeout": self._pool_timeout,
            "pool_recycle": self._pool_recycle,
            "db_type": self.config.db_type(),
        }

        if self._engine:
            try:
                pool = self._engine.pool
                if pool:
                    status["pool_status"] = {
                        "size": pool.size(),
                        "checkedin": pool.checkedin(),
                        "overflow": pool.overflow(),
                        "total": pool.total(),
                    }
            except Exception as e:
                logger.warning(f"Could not get pool status: {e}")
                status["pool_error"] = str(e)

        return status