# my_bot_project/src/my_bot/bootstrap/app/shutdown_hooks.py
"""
هک‌های خاموش‌سازی برنامه (Shutdown Hooks).

این ماژول شامل کلاس `ShutdownHooks` است که امکان ثبت و اجرای
توابع خاموش‌سازی (Shutdown) را در زمان پایان برنامه فراهم می‌کند.
از این هک‌ها می‌توان برای انجام عملیات‌های پاکسازی مانند بستن اتصالات دیتابیس،
ذخیره‌سازی وضعیت، توقف زمان‌بندی‌ها و ... استفاده کرد.
"""

from typing import List, Callable, Awaitable, Optional

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class ShutdownHooks:
    """
    مدیریت هک‌های خاموش‌سازی.

    این کلاس با استفاده از یک لیست داخلی، توابعی را که باید در زمان
    خاموش‌سازی برنامه اجرا شوند، ذخیره کرده و آنها را به‌ترتیب اجرا می‌کند.

    Attributes:
        _hooks: لیست توابع async برای اجرا در shutdown.
        _allow_errors: آیا خطاها در حین اجرای هک‌ها نادیده گرفته شوند.
    """

    def __init__(self, allow_errors: bool = False) -> None:
        """
        مقداردهی اولیه ShutdownHooks.

        Args:
            allow_errors: آیا خطاها در حین اجرای هک‌ها نادیده گرفته شوند (پیش‌فرض False).
        """
        self._hooks: List[Callable[[], Awaitable[None]]] = []
        self._allow_errors = allow_errors
        logger.info(f"ShutdownHooks initialized (allow_errors={allow_errors}).")

    def register(self, hook: Callable[[], Awaitable[None]]) -> None:
        """
        ثبت یک تابع خاموش‌سازی.

        Args:
            hook: تابع async که هنگام shutdown اجرا می‌شود.
        """
        self._hooks.append(hook)
        logger.debug(f"Shutdown hook registered: {hook.__name__}")

    async def run_all(self) -> None:
        """
        اجرای تمام هک‌های ثبت‌شده به‌ترتیب.

        اگر `allow_errors` True باشد، خطاها لاگ شده و ادامه می‌یابد.
        در غیر این صورت، اولین خطا propagate می‌شود.
        """
        if not self._hooks:
            logger.debug("No shutdown hooks to run.")
            return

        logger.info(f"Running {len(self._hooks)} shutdown hooks...")

        for hook in self._hooks:
            try:
                await hook()
                logger.debug(f"Shutdown hook executed successfully: {hook.__name__}")
            except Exception as e:
                logger.error(f"Shutdown hook '{hook.__name__}' failed: {e}")
                if not self._allow_errors:
                    raise

        logger.info("All shutdown hooks completed.")

    def clear(self) -> None:
        """پاک کردن تمام هک‌های ثبت‌شده."""
        self._hooks.clear()
        logger.debug("Shutdown hooks cleared.")

    def get_hooks(self) -> List[Callable[[], Awaitable[None]]]:
        """
        دریافت لیست هک‌های ثبت‌شده.

        Returns:
            List[Callable[[], Awaitable[None]]]: لیست هک‌ها.
        """
        return self._hooks.copy()

    def count(self) -> int:
        """
        تعداد هک‌های ثبت‌شده.

        Returns:
            int: تعداد هک‌ها.
        """
        return len(self._hooks)

    def set_allow_errors(self, allow_errors: bool) -> None:
        """
        تنظیم حالت نادیده‌گرفتن خطاها.

        Args:
            allow_errors: True اگر خطاها نادیده گرفته شوند.
        """
        self._allow_errors = allow_errors
        logger.debug(f"Allow errors set to: {allow_errors}")