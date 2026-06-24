# my_bot_project/src/my_bot/bootstrap/container/repository_registry.py
"""
ثبت‌کننده ریپازیتوری‌ها (Repository Registry).

این ماژول شامل کلاس `RepositoryRegistry` است که مسئولیت ثبت تمام
ریپازیتوری‌های مورد نیاز سیستم در ظرف DI را بر عهده دارد.
با استفاده از این رجیستری، ریپازیتوری‌ها به‌صورت متمرکز ثبت و مدیریت می‌شوند.
"""

from typing import Dict, Any, Optional, Callable, List

from my_bot.core.logger.logger_setup import get_logger
from my_bot.bootstrap.container.di_container import DIContainer

logger = get_logger(__name__)


class RepositoryRegistry:
    """
    ثبت‌کننده ریپازیتوری‌ها در ظرف DI.

    این کلاس با دریافت یک ظرف DI، ریپازیتوری‌ها را به‌صورت Factory یا Singleton
    در آن ثبت می‌کند. همچنین امکان دریافت و بررسی وجود ریپازیتوری‌ها را فراهم می‌کند.

    Attributes:
        container: ظرف DI برای ثبت ریپازیتوری‌ها.
        _repositories: دیکشنری نگاشت نام ریپازیتوری به تابع سازنده یا نمونه.
    """

    def __init__(self, container: DIContainer) -> None:
        """
        مقداردهی اولیه RepositoryRegistry.

        Args:
            container: ظرف DI برای ثبت ریپازیتوری‌ها.
        """
        self._container = container
        self._repositories: Dict[str, Callable] = {}

        logger.info("RepositoryRegistry initialized.")

    def register(self, name: str, factory: Callable, is_singleton: bool = True) -> None:
        """
        ثبت یک ریپازیتوری در ظرف.

        Args:
            name: نام ریپازیتوری.
            factory: تابع سازنده که یک نمونه از ریپازیتوری را برمی‌گرداند.
            is_singleton: آیا به‌صورت Singleton باشد (پیش‌فرض True).
        """
        self._repositories[name] = factory

        if is_singleton:
            # اگر factory یک نمونه باشد (نه تابع)، آن را مستقیماً ثبت می‌کنیم
            if not callable(factory) or isinstance(factory, type):
                self._container.register_singleton(name, factory)
            else:
                # اگر factory یک تابع باشد، آن را به‌صورت Singleton ثبت می‌کنیم
                # با یک تابع wrapper که نمونه را ذخیره می‌کند
                instance = None

                def singleton_factory():
                    nonlocal instance
                    if instance is None:
                        instance = factory()
                    return instance

                self._container.register_factory(name, singleton_factory)
        else:
            self._container.register_factory(name, factory)

        logger.debug(f"Repository registered: {name} (singleton={is_singleton})")

    def register_factory(self, name: str, factory: Callable) -> None:
        """
        ثبت یک Factory برای ریپازیتوری.

        Args:
            name: نام ریپازیتوری.
            factory: تابعی که نمونه‌ی ریپازیتوری را ایجاد می‌کند.
        """
        self.register(name, factory, is_singleton=False)

    def register_singleton(self, name: str, instance: Any) -> None:
        """
        ثبت یک نمونه Singleton برای ریپازیتوری.

        Args:
            name: نام ریپازیتوری.
            instance: نمونه‌ی ریپازیتوری.
        """
        self.register(name, lambda: instance, is_singleton=True)

    def register_all(self, repositories: Dict[str, Callable], is_singleton: bool = True) -> None:
        """
        ثبت چندین ریپازیتوری به‌صورت یکجا.

        Args:
            repositories: دیکشنری نگاشت نام ریپازیتوری به تابع سازنده یا نمونه.
            is_singleton: آیا به‌صورت Singleton باشند.
        """
        for name, factory in repositories.items():
            self.register(name, factory, is_singleton)

    def get(self, name: str) -> Any:
        """
        دریافت یک ریپازیتوری از ظرف.

        Args:
            name: نام ریپازیتوری.

        Returns:
            نمونه‌ی ریپازیتوری.

        Raises:
            KeyError: اگر ریپازیتوری ثبت نشده باشد.
        """
        if name not in self._repositories:
            raise KeyError(f"Repository '{name}' not registered.")
        return self._container.resolve(name)

    def has(self, name: str) -> bool:
        """
        بررسی وجود یک ریپازیتوری در ظرف.

        Args:
            name: نام ریپازیتوری.

        Returns:
            True اگر ریپازیتوری ثبت شده باشد.
        """
        return name in self._repositories

    def get_all(self) -> List[str]:
        """
        دریافت لیست تمام ریپازیتوری‌های ثبت‌شده.

        Returns:
            List[str]: لیست نام ریپازیتوری‌ها.
        """
        return list(self._repositories.keys())

    def get_all_instances(self) -> Dict[str, Any]:
        """
        دریافت نمونه‌های تمام ریپازیتوری‌های ثبت‌شده.

        Returns:
            Dict[str, Any]: دیکشنری نگاشت نام ریپازیتوری به نمونه.

        Raises:
            KeyError: اگر ریپازیتوری ثبت نشده باشد.
        """
        return {name: self.get(name) for name in self._repositories.keys()}

    def clear(self) -> None:
        """
        پاک کردن تمام ریپازیتوری‌های ثبت‌شده.

        این متد برای تست‌ها یا بازنشانی پیکربندی استفاده می‌شود.
        """
        self._repositories.clear()
        logger.info("All repositories cleared from registry.")

    def __len__(self) -> int:
        """
        تعداد ریپازیتوری‌های ثبت‌شده.

        Returns:
            int: تعداد ریپازیتوری‌ها.
        """
        return len(self._repositories)

    def __contains__(self, name: str) -> bool:
        """
        بررسی وجود یک ریپازیتوری.

        Args:
            name: نام ریپازیتوری.

        Returns:
            bool: True اگر وجود داشته باشد.
        """
        return self.has(name)