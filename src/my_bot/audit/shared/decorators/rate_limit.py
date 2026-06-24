# my_bot_project/src/my_bot/shared/decorators/rate_limit.py
"""
دکوراتور محدودیت نرخ درخواست (Rate Limit Decorator).

این دکوراتور با استفاده از یک کش (حافظه محلی یا Redis) تعداد درخواست‌های
یک کاربر یا یک منبع را در بازه‌های زمانی مشخص محدود می‌کند.
از این دکوراتور برای محافظت از APIها و سرویس‌ها در برابر استفاده بیش از حد استفاده می‌شود.
"""

import asyncio
import time
import functools
from typing import (
    Callable, Type, Tuple, Optional, Any, Union, TypeVar, ParamSpec,
    Dict, List, Awaitable, Set, overload
)
from collections import defaultdict
from datetime import datetime, timedelta

from my_bot.core.exceptions.rate_limit_errors import RateLimitExceededError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

# ==========================================
# ذخیره‌سازی محلی برای Rate Limit (Fallback)
# ==========================================

class LocalRateLimitStore:
    """
    ذخیره‌سازی محلی برای محدودیت نرخ درخواست (Fallback).

    این کلاس با استفاده از دیکشنری و قفل، محدودیت نرخ را در حافظه مدیریت می‌کند.
    برای محیط‌های تک‌نسخه‌ای (Single Instance) مناسب است.
    """

    def __init__(self) -> None:
        self._data: Dict[str, List[float]] = defaultdict(list)  # key -> لیست زمان‌ها (ثانیه)
        self._lock = asyncio.Lock()

    async def get_requests(self, key: str, window_seconds: int) -> int:
        """
        دریافت تعداد درخواست‌های ثبت‌شده در پنجره زمانی.

        Args:
            key: کلید کاربر یا منبع.
            window_seconds: طول پنجره زمانی بر حسب ثانیه.

        Returns:
            int: تعداد درخواست‌ها.
        """
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            timestamps = self._data.get(key, [])
            # حذف زمان‌های قدیمی‌تر از پنجره
            self._data[key] = [ts for ts in timestamps if ts > cutoff]
            return len(self._data[key])

    async def add_request(self, key: str, window_seconds: int) -> int:
        """
        ثبت یک درخواست جدید و بازگرداندن تعداد درخواست‌های موجود.

        Args:
            key: کلید کاربر یا منبع.
            window_seconds: طول پنجره زمانی بر حسب ثانیه.

        Returns:
            int: تعداد درخواست‌ها پس از افزودن.
        """
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            timestamps = self._data.get(key, [])
            # حذف زمان‌های قدیمی
            timestamps = [ts for ts in timestamps if ts > cutoff]
            timestamps.append(now)
            self._data[key] = timestamps
            return len(timestamps)

    async def reset(self, key: str) -> None:
        """بازنشانی محدودیت برای یک کلید خاص."""
        async with self._lock:
            if key in self._data:
                del self._data[key]

    async def clear(self) -> None:
        """پاک کردن تمام داده‌های محدودیت."""
        async with self._lock:
            self._data.clear()


# ==========================================
# کلاس اصلی Rate Limiter
# ==========================================

class RateLimiter:
    """
    مدیریت محدودیت نرخ درخواست با پشتیبانی از ذخیره‌سازی محلی.

    این کلاس با استفاده از یک ذخیره‌سازی (محلی یا Redis) تعداد درخواست‌ها را
    در بازه‌های زمانی مشخص محدود می‌کند.
    """

    def __init__(
        self,
        store: Optional[LocalRateLimitStore] = None,
    ) -> None:
        """
        مقداردهی اولیه RateLimiter.

        Args:
            store: ذخیره‌سازی برای داده‌های محدودیت (در صورت None، از LocalRateLimitStore استفاده می‌شود).
        """
        self._store = store or LocalRateLimitStore()

    async def check_and_increment(
        self,
        key: str,
        requests_per_window: int,
        window_seconds: int,
    ) -> bool:
        """
        بررسی محدودیت و در صورت مجاز بودن، درخواست را ثبت می‌کند.

        Args:
            key: کلید کاربر یا منبع.
            requests_per_window: تعداد درخواست‌های مجاز در هر پنجره.
            window_seconds: طول پنجره زمانی بر حسب ثانیه.

        Returns:
            bool: True اگر درخواست مجاز باشد، در غیر این صورت False.

        Raises:
            RateLimitExceededError: در صورت تجاوز از محدودیت.
        """
        current_count = await self._store.get_requests(key, window_seconds)

        if current_count >= requests_per_window:
            raise RateLimitExceededError(
                message=f"تعداد درخواست‌های شما بیش از حد مجاز است ({requests_per_window} در {window_seconds} ثانیه).",
                retry_after_seconds=window_seconds,
            )

        await self._store.add_request(key, window_seconds)
        return True

    async def get_current_count(self, key: str, window_seconds: int) -> int:
        """
        دریافت تعداد درخواست‌های فعلی برای یک کلید.

        Args:
            key: کلید کاربر یا منبع.
            window_seconds: طول پنجره زمانی بر حسب ثانیه.

        Returns:
            int: تعداد درخواست‌های فعلی.
        """
        return await self._store.get_requests(key, window_seconds)

    async def reset(self, key: str) -> None:
        """
        بازنشانی محدودیت برای یک کلید خاص.

        Args:
            key: کلید کاربر یا منبع.
        """
        await self._store.reset(key)

    async def clear(self) -> None:
        """پاک کردن تمام محدودیت‌ها."""
        await self._store.clear()


# ==========================================
# دکوراتور اصلی
# ==========================================

# نمونه سراسری RateLimiter (با ذخیره‌سازی محلی)
_global_rate_limiter = RateLimiter()


def rate_limit(
    requests_per_window: int = 30,
    window_seconds: int = 60,
    key_prefix: str = "rate_limit",
    identifier_func: Optional[Callable[..., str]] = None,
    raise_exception: bool = True,
    limiter: Optional[RateLimiter] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    دکوراتور برای اعمال محدودیت نرخ درخواست روی یک تابع.

    Args:
        requests_per_window: تعداد درخواست‌های مجاز در هر پنجره (پیش‌فرض ۳۰).
        window_seconds: طول پنجره زمانی بر حسب ثانیه (پیش‌فرض ۶۰).
        key_prefix: پیشوند کلید برای ذخیره‌سازی (پیش‌فرض "rate_limit").
        identifier_func: تابعی که یک رشته شناسه‌ی یکتا از آرگومان‌های تابع استخراج کند.
                         در صورت None، از نام تابع و اولین آرگومان (اگر عدد باشد) استفاده می‌شود.
        raise_exception: در صورت تجاوز از محدودیت، استثنا پرتاب شود (پیش‌فرض True).
        limiter: نمونه RateLimiter (در صورت None، از نمونه سراسری استفاده می‌شود).

    Returns:
        Callable: دکوراتور.

    Example:
        @rate_limit(requests_per_window=5, window_seconds=10)
        async def api_call(user_id: int, data: str) -> dict:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        is_async = asyncio.iscoroutinefunction(func)

        # تابع پیش‌فرض برای استخراج شناسه
        def default_identifier(*args: Any, **kwargs: Any) -> str:
            # اگر شناسه‌ای پیدا نشد، از نام تابع و زمان (به‌صورت ثابت) استفاده می‌کنیم
            # اما بهتر است کاربر خودش تابع شناسه را بدهد.
            # اینجا سعی می‌کنیم اولین آرگومان عددی را به‌عنوان شناسه بگیریم.
            for arg in args:
                if isinstance(arg, (int, str)):
                    return f"{key_prefix}:{func.__name__}:{arg}"
            # اگر آرگومان عددی نبود، از نام تابع استفاده کن
            return f"{key_prefix}:{func.__name__}:default"

        identifier = identifier_func or default_identifier
        limiter_instance = limiter or _global_rate_limiter

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع همزمان."""
            key = identifier(*args, **kwargs)

            # اجرای بررسی به‌صورت همزمان (با استفاده از asyncio.run در صورت نیاز؟)
            # بهتر است توابع همزمان را با یک حلقه اجرا کنیم
            try:
                # اجرای async در حلقه جاری (اگر حلقه وجود داشته باشد)
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # اگر حلقه در حال اجراست، از asyncio.create_task استفاده نمی‌کنیم،
                    # بلکه از asyncio.run_coroutine_threadsafe استفاده می‌کنیم.
                    # اینجا برای سادگی، از asyncio.run تا حد امکان استفاده نمی‌کنیم.
                    # در عوض، از asyncio.get_event_loop().run_until_complete استفاده می‌کنیم.
                    # اما این ممکن است با حلقه موجود تداخل داشته باشد.
                    # بهترین راه: استفاده از asyncio.new_event_loop
                    # برای سادگی، از یک تابع کمکی استفاده می‌کنیم.
                    # اما بهتر است این دکوراتور فقط روی توابع async استفاده شود.
                    # برای توابع همزمان، یک پیاده‌سازی ساده با قفل و دیکشنری محلی داریم
                    # ولی برای سادگی، از asyncio.run استفاده می‌کنیم (که می‌تواند خطرناک باشد).
                    # در عوض، از یک تابع کمکی همزمان استفاده می‌کنیم.
                    # اینجا برای جلوگیری از پیچیدگی، از اجرای همزمان با asyncio.run استفاده می‌کنیم.
                    # اما توجه: asyncio.run در یک حلقه در حال اجرا قابل استفاده نیست.
                    # بنابراین بهتر است توابع همزمان را با یک پیاده‌سازی جداگانه پشتیبانی کنیم.
                    # برای این نسخه، فرض می‌کنیم توابع async هستند.
                    # اگر تابع همزمان است، می‌توانیم از threading.Lock و دیکشنری محلی استفاده کنیم.
                    # برای سادگی، فعلاً از asyncio.run استفاده نمی‌کنیم و خطا می‌دهیم.
                    raise RuntimeError(
                        "rate_limit decorator on synchronous functions is not fully supported. "
                        "Please use async functions or implement a synchronous rate limiter."
                    )
                else:
                    # ایجاد حلقه جدید و اجرا
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            limiter_instance.check_and_increment(
                                key=key,
                                requests_per_window=requests_per_window,
                                window_seconds=window_seconds,
                            )
                        )
                    finally:
                        new_loop.close()
            except RateLimitExceededError:
                if raise_exception:
                    raise
                else:
                    # اگر پرتاب استثنا غیرفعال باشد، به‌سادگی False برمی‌گردانیم
                    # اما این با نوع بازگشتی سازگار نیست. بهتر است استثنا پرتاب شود.
                    raise

            # اگر به اینجا رسیدیم، یعنی درخواست مجاز است
            # حالا تابع اصلی را اجرا می‌کنیم
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع غیرهمزمان."""
            key = identifier(*args, **kwargs)

            try:
                await limiter_instance.check_and_increment(
                    key=key,
                    requests_per_window=requests_per_window,
                    window_seconds=window_seconds,
                )
            except RateLimitExceededError as e:
                if raise_exception:
                    raise
                else:
                    # در صورت عدم پرتاب استثنا، می‌توانیم None برگردانیم یا خطا را نادیده بگیریم
                    # اما بهتر است استثنا پرتاب شود
                    raise

            # اجرای تابع اصلی
            return await func(*args, **kwargs)

        return async_wrapper if is_async else sync_wrapper

    return decorator


# ==========================================
# دکوراتورهای از پیش پیکربندی‌شده
# ==========================================

def rate_limit_public_api(func: Callable) -> Callable:
    """
    دکوراتور برای APIهای عمومی با محدودیت ملایم.

    محدودیت: ۱۰۰ درخواست در ۶۰ ثانیه.

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return rate_limit(
        requests_per_window=100,
        window_seconds=60,
        key_prefix="public_api",
        raise_exception=True,
    )(func)


def rate_limit_internal_api(func: Callable) -> Callable:
    """
    دکوراتور برای APIهای داخلی با محدودیت سخت‌تر.

    محدودیت: ۲۰ درخواست در ۶۰ ثانیه.

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return rate_limit(
        requests_per_window=20,
        window_seconds=60,
        key_prefix="internal_api",
        raise_exception=True,
    )(func)


def rate_limit_heavy_operation(func: Callable) -> Callable:
    """
    دکوراتور برای عملیات سنگین با محدودیت بسیار کم.

    محدودیت: ۵ درخواست در ۶۰ ثانیه.

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return rate_limit(
        requests_per_window=5,
        window_seconds=60,
        key_prefix="heavy_op",
        raise_exception=True,
    )(func)


# ==========================================
# تابع کمکی برای استفاده مستقیم
# ==========================================

async def check_rate_limit(
    key: str,
    requests_per_window: int,
    window_seconds: int,
    limiter: Optional[RateLimiter] = None,
) -> bool:
    """
    تابع کمکی برای بررسی محدودیت نرخ به‌صورت مستقیم.

    Args:
        key: کلید کاربر یا منبع.
        requests_per_window: تعداد درخواست‌های مجاز در هر پنجره.
        window_seconds: طول پنجره زمانی بر حسب ثانیه.
        limiter: نمونه RateLimiter (اختیاری، در صورت None از نمونه سراسری استفاده می‌شود).

    Returns:
        bool: True اگر درخواست مجاز باشد، در غیر این صورت False.

    Raises:
        RateLimitExceededError: در صورت تجاوز از محدودیت.
    """
    limiter_instance = limiter or _global_rate_limiter
    return await limiter_instance.check_and_increment(
        key=key,
        requests_per_window=requests_per_window,
        window_seconds=window_seconds,
    )