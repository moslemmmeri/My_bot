# my_bot_project/src/my_bot/bootstrap/container/service_registry.py
"""
ثبت سرویس‌های لایه کاربرد و زیرساخت (Service Registry).

این ماژول شامل کلاس‌های `ServiceRegistry` و `RepositoryRegistry` است که
مسئولیت ثبت سرویس‌ها و ریپازیتوری‌ها در ظرف DI را بر عهده دارند.
با استفاده از این رجیستری‌ها، مدیریت وابستگی‌ها به‌صورت متمرکز انجام می‌شود.
"""

from typing import Dict, Any, Optional, Type, Callable, List
from functools import lru_cache

from my_bot.core.logger.logger_setup import get_logger
from my_bot.bootstrap.container.di_container import DIContainer

logger = get_logger(__name__)


class RepositoryRegistry:
    """
    ثبت‌کننده ریپازیتوری‌ها در ظرف DI.

    این کلاس مسئولیت ثبت تمام ریپازیتوری‌های مورد نیاز سیستم را بر عهده دارد.
    با استفاده از این رجیستری، ریپازیتوری‌ها به‌صورت متمرکز ثبت و مدیریت می‌شوند.

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

    def register(self, name: str, factory: Callable) -> None:
        """
        ثبت یک ریپازیتوری در ظرف.

        Args:
            name: نام ریپازیتوری.
            factory: تابع سازنده که یک نمونه از ریپازیتوری را برمی‌گرداند.
        """
        self._repositories[name] = factory
        self._container.register_factory(name, factory)
        logger.debug(f"Repository registered: {name}")

    def register_all(self, factories: Dict[str, Callable]) -> None:
        """
        ثبت چندین ریپازیتوری به‌صورت یکجا.

        Args:
            factories: دیکشنری نگاشت نام ریپازیتوری به تابع سازنده.
        """
        for name, factory in factories.items():
            self.register(name, factory)

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


class ServiceRegistry:
    """
    ثبت‌کننده سرویس‌های لایه کاربرد در ظرف DI.

    این کلاس مسئولیت ثبت تمام سرویس‌های لایه کاربرد و زیرساخت را بر عهده دارد.
    سرویس‌ها شامل سرویس‌های کاربر، سفارش، پرداخت، فرم، تیکت، کوپن و ... هستند.

    Attributes:
        container: ظرف DI برای ثبت سرویس‌ها.
        _services: دیکشنری نگاشت نام سرویس به تابع سازنده یا نمونه.
    """

    def __init__(self, container: DIContainer) -> None:
        """
        مقداردهی اولیه ServiceRegistry.

        Args:
            container: ظرف DI برای ثبت سرویس‌ها.
        """
        self._container = container
        self._services: Dict[str, Callable] = {}

        logger.info("ServiceRegistry initialized.")

    def register(self, name: str, factory: Callable, is_singleton: bool = True) -> None:
        """
        ثبت یک سرویس در ظرف.

        Args:
            name: نام سرویس.
            factory: تابع سازنده یا نمونه‌ی سرویس.
            is_singleton: آیا به‌صورت Singleton باشد.
        """
        self._services[name] = factory

        if is_singleton:
            # اگر factory یک نمونه باشد، آن را مستقیماً ثبت می‌کنیم
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

        logger.debug(f"Service registered: {name} (singleton={is_singleton})")

    def register_factory(self, name: str, factory: Callable) -> None:
        """
        ثبت یک Factory برای سرویس.

        Args:
            name: نام سرویس.
            factory: تابعی که نمونه‌ی سرویس را ایجاد می‌کند.
        """
        self.register(name, factory, is_singleton=False)

    def register_singleton(self, name: str, instance: Any) -> None:
        """
        ثبت یک نمونه Singleton.

        Args:
            name: نام سرویس.
            instance: نمونه‌ی سرویس.
        """
        self.register(name, lambda: instance, is_singleton=True)

    def register_all(self, services: Dict[str, Callable], is_singleton: bool = True) -> None:
        """
        ثبت چندین سرویس به‌صورت یکجا.

        Args:
            services: دیکشنری نگاشت نام سرویس به تابع سازنده یا نمونه.
            is_singleton: آیا به‌صورت Singleton باشند.
        """
        for name, factory in services.items():
            self.register(name, factory, is_singleton)

    def get(self, name: str) -> Any:
        """
        دریافت یک سرویس از ظرف.

        Args:
            name: نام سرویس.

        Returns:
            نمونه‌ی سرویس.

        Raises:
            KeyError: اگر سرویس ثبت نشده باشد.
        """
        if name not in self._services:
            raise KeyError(f"Service '{name}' not registered.")
        return self._container.resolve(name)

    def has(self, name: str) -> bool:
        """
        بررسی وجود یک سرویس در ظرف.

        Args:
            name: نام سرویس.

        Returns:
            True اگر سرویس ثبت شده باشد.
        """
        return name in self._services

    def get_all(self) -> List[str]:
        """
        دریافت لیست تمام سرویس‌های ثبت‌شده.

        Returns:
            List[str]: لیست نام سرویس‌ها.
        """
        return list(self._services.keys())


# ==============================================
# توابع کمکی برای ساخت Factoryهای سرویس‌ها
# ==============================================

def create_service_factory(
    service_class: Type,
    dependencies: Dict[str, str],
    container: DIContainer,
) -> Callable:
    """
    ایجاد یک Factory برای سرویس با تزریق وابستگی‌ها.

    Args:
        service_class: کلاس سرویس.
        dependencies: دیکشنری نگاشت نام پارامتر به نام سرویس در ظرف.
        container: ظرف DI.

    Returns:
        Callable: تابع Factory.
    """
    def factory() -> Any:
        # دریافت وابستگی‌ها از ظرف
        resolved_deps = {}
        for param_name, service_name in dependencies.items():
            resolved_deps[param_name] = container.resolve(service_name)

        # ساخت نمونه سرویس
        return service_class(**resolved_deps)

    return factory


def create_repository_factory(
    repository_class: Type,
    db_manager_name: str = "database_session_manager",
    container: Optional[DIContainer] = None,
) -> Callable:
    """
    ایجاد یک Factory برای ریپازیتوری.

    Args:
        repository_class: کلاس ریپازیتوری.
        db_manager_name: نام سرویس DatabaseSessionManager در ظرف.
        container: ظرف DI (اختیاری، در صورت عدم وجود، باید بعداً تنظیم شود).

    Returns:
        Callable: تابع Factory.
    """
    def factory() -> Any:
        if container is None:
            raise RuntimeError("Container not provided for repository factory.")

        db_manager = container.resolve(db_manager_name)
        return repository_class(db_manager)

    return factory