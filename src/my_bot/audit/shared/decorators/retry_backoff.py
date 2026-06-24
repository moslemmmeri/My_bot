# my_bot_project/src/my_bot/shared/decorators/retry_backoff.py
"""
دکوراتور تلاش مجدد با Backoff (Retry with Backoff Decorator).

این دکوراتور با استفاده از الگوریتم Backoff نمایی، عملیات‌های ناموفق
را به‌صورت خودکار تکرار می‌کند. از این دکوراتور برای افزایش پایداری
در برابر خطاهای موقتی (مثل مشکلات شبکه، Timeout و ...) استفاده می‌شود.
"""

import asyncio
import time
import random
import functools
from typing import Callable, Type, Tuple, Optional, Any, Union, TypeVar, ParamSpec
from functools import wraps

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)

# Type variables for better typing
P = ParamSpec("P")
T = TypeVar("T")


def retry_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    raise_on_failure: bool = True,
    log_attempts: bool = True,
    add_jitter: bool = False,
    jitter_factor: float = 0.1,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    دکوراتور برای تلاش مجدد با Backoff نمایی.

    این دکوراتور تابع را به‌صورت مکرر در صورت بروز خطاهای مشخص
    اجرا می‌کند و بین هر تلاش با تأخیر Backoff نمایی منتظر می‌ماند.

    Args:
        max_retries: حداکثر تعداد تلاش‌های مجدد (پیش‌فرض ۳).
        initial_delay: تأخیر اولیه بر حسب ثانیه (پیش‌فرض ۱ ثانیه).
        backoff_factor: ضریب افزایش تأخیر (پیش‌فرض ۲).
        exceptions: استثناهایی که باعث تلاش مجدد می‌شوند (پیش‌فرض Exception).
        raise_on_failure: در صورت شکست همه تلاش‌ها، استثنا پرتاب شود (پیش‌فرض True).
        log_attempts: آیا تلاش‌ها لاگ شوند (پیش‌فرض True).
        add_jitter: افزودن جیتر تصادفی به تأخیر (پیش‌فرض False).
        jitter_factor: حداکثر درصد جیتر (پیش‌فرض ۰.۱ = ۱۰٪).

    Returns:
        Callable: دکوراتور.

    Example:
        @retry_backoff(max_retries=3, initial_delay=1, backoff_factor=2)
        async def fetch_data(url: str) -> dict:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # تشخیص async بودن تابع
        is_async = asyncio.iscoroutinefunction(func)

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع همزمان."""
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    # محاسبه تأخیر با Backoff نمایی
                    delay = initial_delay * (backoff_factor ** (attempt - 1))

                    # افزودن جیتر (در صورت فعال بودن)
                    if add_jitter:
                        jitter = delay * jitter_factor * (random.random() * 2 - 1)
                        delay = max(0, delay + jitter)

                    if log_attempts:
                        logger.warning(
                            f"Retry {attempt}/{max_retries} for {func.__name__} "
                            f"after {delay:.2f}s due to: {e}"
                        )

                    time.sleep(delay)

            # اگر همه تلاش‌ها ناموفق بودند
            if raise_on_failure and last_exception is not None:
                raise last_exception

            # اگر raise_on_failure False باشد، آخرین خطا را برمی‌گردانیم (یا None)
            return None  # type: ignore

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع غیرهمزمان."""
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    # محاسبه تأخیر با Backoff نمایی
                    delay = initial_delay * (backoff_factor ** (attempt - 1))

                    # افزودن جیتر (در صورت فعال بودن)
                    if add_jitter:
                        jitter = delay * jitter_factor * (random.random() * 2 - 1)
                        delay = max(0, delay + jitter)

                    if log_attempts:
                        logger.warning(
                            f"Retry {attempt}/{max_retries} for {func.__name__} "
                            f"after {delay:.2f}s due to: {e}"
                        )

                    await asyncio.sleep(delay)

            # اگر همه تلاش‌ها ناموفق بودند
            if raise_on_failure and last_exception is not None:
                raise last_exception

            # اگر raise_on_failure False باشد، آخرین خطا را برمی‌گردانیم (یا None)
            return None  # type: ignore

        return async_wrapper if is_async else sync_wrapper

    return decorator


# ==========================================
# دکوراتورهای از پیش پیکربندی‌شده
# ==========================================

def retry_network_operation(func: Callable) -> Callable:
    """
    دکوراتور برای عملیات شبکه با تنظیمات پیش‌فرض مناسب.

    این دکوراتور با max_retries=5, initial_delay=0.5, backoff_factor=1.5
    و جیتر فعال، برای عملیات شبکه بهینه‌سازی شده است.

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return retry_backoff(
        max_retries=5,
        initial_delay=0.5,
        backoff_factor=1.5,
        exceptions=(ConnectionError, TimeoutError, OSError),
        add_jitter=True,
        log_attempts=True,
    )(func)


def retry_database_operation(func: Callable) -> Callable:
    """
    دکوراتور برای عملیات دیتابیس با تنظیمات پیش‌فرض مناسب.

    این دکوراتور برای عملیات دیتابیس با max_retries=3, initial_delay=0.5,
    backoff_factor=2.0 و جیتر غیرفعال بهینه‌سازی شده است.

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    from my_bot.core.exceptions.db_errors import DatabaseError, ConnectionError as DBConnectionError

    return retry_backoff(
        max_retries=3,
        initial_delay=0.5,
        backoff_factor=2.0,
        exceptions=(DBConnectionError, DatabaseError, TimeoutError),
        add_jitter=False,
        log_attempts=True,
    )(func)


def retry_external_api(func: Callable) -> Callable:
    """
    دکوراتور برای APIهای خارجی با تنظیمات پیش‌فرض مناسب.

    این دکوراتور برای APIهای خارجی با max_retries=4, initial_delay=1.0,
    backoff_factor=2.0 و جیتر فعال بهینه‌سازی شده است.

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return retry_backoff(
        max_retries=4,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(ConnectionError, TimeoutError, OSError, ValueError),
        add_jitter=True,
        log_attempts=True,
    )(func)


# ==========================================
# تابع کمکی برای استفاده مستقیم
# ==========================================

async def retry_async(
    func: Callable[P, T],
    *args: P.args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    **kwargs: P.kwargs,
) -> T:
    """
    تابع کمکی برای اجرای یک تابع async با مکانیزم Retry.

    این تابع به‌صورت مستقیم بدون نیاز به دکوراتور، یک تابع async را
    با Retry اجرا می‌کند.

    Args:
        func: تابع async برای اجرا.
        *args: آرگومان‌های تابع.
        max_retries: حداکثر تعداد تلاش‌ها (پیش‌فرض ۳).
        initial_delay: تأخیر اولیه (پیش‌فرض ۱ ثانیه).
        backoff_factor: ضریب Backoff (پیش‌فرض ۲).
        exceptions: استثناهای قابل تلاش مجدد (پیش‌فرض Exception).
        **kwargs: آرگومان‌های نام‌دار تابع.

    Returns:
        T: نتیجه تابع.

    Raises:
        آخرین استثنا در صورت شکست همه تلاش‌ها.
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                break

            delay = initial_delay * (backoff_factor ** (attempt - 1))
            logger.warning(
                f"Retry {attempt}/{max_retries} for {func.__name__} "
                f"after {delay:.2f}s due to: {e}"
            )
            await asyncio.sleep(delay)

    # اگر همه تلاش‌ها ناموفق بودند
    if last_exception is not None:
        raise last_exception

    # اگر هیچ خطایی رخ نداد (عملاً غیرممکن)
    raise RuntimeError(f"Unexpected failure in retry_async for {func.__name__}")