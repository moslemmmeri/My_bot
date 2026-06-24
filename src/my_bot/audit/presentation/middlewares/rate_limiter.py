# my_bot_project/src/my_bot/presentation/middlewares/rate_limiter.py
"""
میدلور محدودیت نرخ درخواست (Rate Limiter Middleware).

این میدلور با استفاده از الگوریتم Sliding Window، تعداد درخواست‌های
هر کاربر را در بازه‌های زمانی مشخص محدود می‌کند و از حملات
تلاش مجدد و سوءاستفاده جلوگیری می‌نماید.
"""

import asyncio
import time
from typing import Optional, Dict, Any, Tuple
from collections import defaultdict, deque

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from aiogram.types import User
from aiogram.exceptions import TelegramRetryAfter

from my_bot.core.config.rate_limit_config import RateLimitConfig
from my_bot.core.exceptions.rate_limit_errors import RateLimitExceededError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.rate_limit import RateLimit

logger = get_logger(__name__)


class RateLimiterMiddleware(BaseMiddleware):
    """
    میدلور محدودیت نرخ درخواست با الگوریتم Sliding Window.

    این میدلور با استفاده از الگوریتم Sliding Window، تعداد درخواست‌های
    هر کاربر را در بازه‌های زمانی مشخص محدود می‌کند.

    Attributes:
        config: پیکربندی محدودیت نرخ درخواست.
        _rate_limit: ارزش‌مقدار RateLimit برای اعمال محدودیت.
        _user_requests: ذخیره‌سازی محلی درخواست‌های کاربران (Fallback).
        _blocked_users: ذخیره‌سازی کاربران مسدود شده (Fallback).
        _lock: قفل برای عملیات اتمیک روی دیکشنری‌ها.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """
        مقداردهی اولیه میدلور.

        Args:
            config: پیکربندی محدودیت نرخ درخواست.
        """
        super().__init__()
        self.config = config

        # ایجاد ارزش‌مقدار RateLimit
        self._rate_limit = RateLimit(
            requests_per_window=config.requests_per_window,
            window_seconds=config.window_seconds,
            storage_backend=config.storage_backend,
            key_prefix=config.key_prefix,
            block_duration_seconds=config.block_duration_seconds,
            enable_blocking=config.enable_blocking,
            whitelist_ids=config.whitelist_ids,
        )

        # ذخیره‌سازی محلی (برای Fallback)
        self._user_requests: Dict[int, deque] = defaultdict(deque)
        self._blocked_users: Dict[int, float] = {}  # user_id -> block_until_timestamp
        self._lock = asyncio.Lock()

        logger.info(
            f"RateLimiterMiddleware initialized: "
            f"requests={config.requests_per_window}, "
            f"window={config.window_seconds}s, "
            f"backend={config.storage_backend}, "
            f"blocking={config.enable_blocking}"
        )

    async def __call__(self, handler, event: Update, data: Dict[str, Any]) -> Any:
        """
        پردازش ورودی و اعمال محدودیت نرخ درخواست.

        Args:
            handler: هندلر بعدی در زنجیره.
            event: رویداد دریافتی از تلگرام.
            data: داده‌های زمینه (Context Data).

        Returns:
            Any: نتیجه پردازش توسط هندلر بعدی.

        Raises:
            RateLimitExceededError: در صورت تجاوز از محدودیت نرخ درخواست.
        """
        # استخراج کاربر از رویداد
        user = self._get_user_from_event(event)
        if not user:
            # اگر کاربر وجود نداشت، ادامه پردازش
            return await handler(event, data)

        user_id = user.id

        # اگر کاربر در لیست سفید است، محدودیت اعمال نمی‌شود
        if self._rate_limit.is_whitelisted(user_id):
            return await handler(event, data)

        # اگر محدودیت غیرفعال است، ادامه پردازش
        if not self.config.enabled:
            return await handler(event, data)

        # بررسی مسدود بودن کاربر
        if await self._is_user_blocked(user_id):
            # اگر کاربر مسدود است، خطا پرتاب می‌کنیم
            block_until = self._blocked_users.get(user_id)
            retry_after = int(block_until - time.time()) if block_until else 60
            raise RateLimitExceededError(
                message="شما به دلیل ارسال درخواست‌های بیش از حد محدود شده‌اید.",
                retry_after_seconds=retry_after,
            )

        # بررسی محدودیت نرخ درخواست
        is_allowed, remaining, wait_time = await self._check_rate_limit(user_id)

        if not is_allowed:
            # اگر از محدودیت تجاوز شده و مسدودسازی فعال است، کاربر را مسدود می‌کنیم
            if self._rate_limit.enable_blocking:
                await self._block_user(user_id, self._rate_limit.block_duration_seconds)

            raise RateLimitExceededError(
                message="تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید.",
                retry_after_seconds=wait_time or self._rate_limit.window_seconds,
            )

        # ثبت درخواست جدید
        await self._record_request(user_id)

        # ادامه پردازش
        return await handler(event, data)

    async def _check_rate_limit(self, user_id: int) -> Tuple[bool, int, Optional[int]]:
        """
        بررسی محدودیت نرخ درخواست برای یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Tuple شامل:
                - bool: آیا درخواست مجاز است؟
                - int: تعداد درخواست‌های باقی‌مانده.
                - Optional[int]: زمان انتظار پیشنهادی (در صورت غیرمجاز بودن).
        """
        if self.config.storage_backend == "redis":
            # استفاده از Redis (با کش)
            return await self._check_redis_rate_limit(user_id)
        else:
            # استفاده از Local Storage
            return await self._check_local_rate_limit(user_id)

    async def _check_redis_rate_limit(self, user_id: int) -> Tuple[bool, int, Optional[int]]:
        """
        بررسی محدودیت نرخ با استفاده از Redis.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Tuple شامل وضعیت مجاز، تعداد باقی‌مانده و زمان انتظار.
        """
        try:
            # در عمل، باید از RedisAdapter استفاده کنیم
            # اینجا یک پیاده‌سازی شبیه‌سازی‌شده است
            # برای استفاده واقعی، باید به Redis متصل شود

            # برای سادگی، از Local استفاده می‌کنیم
            logger.debug(f"Using Redis rate limit check for user {user_id} (simulated)")
            return await self._check_local_rate_limit(user_id)

        except Exception as e:
            logger.error(f"Redis rate limit check error: {e}")
            # Fallback به Local
            return await self._check_local_rate_limit(user_id)

    async def _check_local_rate_limit(self, user_id: int) -> Tuple[bool, int, Optional[int]]:
        """
        بررسی محدودیت نرخ با استفاده از Local Storage.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Tuple شامل وضعیت مجاز، تعداد باقی‌مانده و زمان انتظار.
        """
        async with self._lock:
            now = time.time()
            window_start = now - self._rate_limit.window_seconds

            # دریافت تاریخچه درخواست‌های کاربر
            requests = self._user_requests.get(user_id, deque())

            # حذف درخواست‌های قدیمی‌تر از پنجره
            while requests and requests[0] < window_start:
                requests.popleft()

            # تعداد درخواست‌های معتبر در پنجره
            current_count = len(requests)

            # محاسبه درخواست‌های باقی‌مانده
            remaining = max(0, self._rate_limit.requests_per_window - current_count)

            # بررسی محدودیت
            if current_count >= self._rate_limit.requests_per_window:
                # محاسبه زمان انتظار (قدیمی‌ترین درخواست + window_seconds - now)
                if requests:
                    wait_time = int(requests[0] + self._rate_limit.window_seconds - now)
                    wait_time = max(1, wait_time)
                else:
                    wait_time = self._rate_limit.window_seconds
                return False, 0, wait_time

            return True, remaining, None

    async def _record_request(self, user_id: int) -> None:
        """
        ثبت یک درخواست جدید برای کاربر.

        Args:
            user_id: شناسه کاربر.
        """
        if self.config.storage_backend == "redis":
            try:
                # استفاده از Redis
                logger.debug(f"Recording request in Redis for user {user_id} (simulated)")
                await self._record_local_request(user_id)
            except Exception as e:
                logger.error(f"Redis record request error: {e}")
                await self._record_local_request(user_id)
        else:
            await self._record_local_request(user_id)

    async def _record_local_request(self, user_id: int) -> None:
        """
        ثبت یک درخواست جدید در Local Storage.

        Args:
            user_id: شناسه کاربر.
        """
        async with self._lock:
            now = time.time()
            requests = self._user_requests.get(user_id, deque())
            requests.append(now)
            self._user_requests[user_id] = requests

            # محدود کردن اندازه (برای جلوگیری از مصرف بیش از حد حافظه)
            if len(requests) > self._rate_limit.requests_per_window * 2:
                while len(requests) > self._rate_limit.requests_per_window:
                    requests.popleft()

    async def _is_user_blocked(self, user_id: int) -> bool:
        """
        بررسی مسدود بودن یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            bool: True اگر کاربر مسدود باشد.
        """
        if not self._rate_limit.enable_blocking:
            return False

        block_until = self._blocked_users.get(user_id)
        if block_until is None:
            return False

        if time.time() < block_until:
            return True

        # اگر زمان مسدودیت تمام شده، حذف می‌کنیم
        async with self._lock:
            if user_id in self._blocked_users:
                del self._blocked_users[user_id]

        return False

    async def _block_user(self, user_id: int, duration_seconds: int) -> None:
        """
        مسدود کردن یک کاربر به مدت مشخص.

        Args:
            user_id: شناسه کاربر.
            duration_seconds: مدت زمان مسدودیت بر حسب ثانیه.
        """
        async with self._lock:
            block_until = time.time() + duration_seconds
            self._blocked_users[user_id] = block_until
            logger.warning(f"User {user_id} blocked for {duration_seconds}s")

    async def unblock_user(self, user_id: int) -> None:
        """
        رفع مسدودیت یک کاربر.

        Args:
            user_id: شناسه کاربر.
        """
        async with self._lock:
            if user_id in self._blocked_users:
                del self._blocked_users[user_id]
                logger.info(f"User {user_id} unblocked")

    async def reset_user_requests(self, user_id: int) -> None:
        """
        بازنشانی تاریخچه درخواست‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.
        """
        async with self._lock:
            if user_id in self._user_requests:
                self._user_requests[user_id].clear()
                logger.debug(f"User {user_id} request history reset")

    async def get_user_status(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت وضعیت محدودیت نرخ درخواست برای یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Dict[str, Any]: وضعیت کاربر.
        """
        is_blocked = await self._is_user_blocked(user_id)
        is_whitelisted = self._rate_limit.is_whitelisted(user_id)

        if is_whitelisted:
            return {
                "user_id": user_id,
                "status": "whitelisted",
                "is_blocked": False,
                "requests_count": 0,
                "limit": self._rate_limit.requests_per_window,
                "window_seconds": self._rate_limit.window_seconds,
            }

        async with self._lock:
            requests = self._user_requests.get(user_id, deque())
            now = time.time()
            window_start = now - self._rate_limit.window_seconds

            # حذف درخواست‌های قدیمی
            while requests and requests[0] < window_start:
                requests.popleft()

            current_count = len(requests)
            remaining = max(0, self._rate_limit.requests_per_window - current_count)

            return {
                "user_id": user_id,
                "status": "blocked" if is_blocked else "active",
                "is_blocked": is_blocked,
                "requests_count": current_count,
                "remaining": remaining,
                "limit": self._rate_limit.requests_per_window,
                "window_seconds": self._rate_limit.window_seconds,
                "block_until": self._blocked_users.get(user_id),
            }

    def _get_user_from_event(self, event: Update) -> Optional[User]:
        """
        استخراج کاربر از رویداد تلگرام.

        Args:
            event: رویداد دریافتی.

        Returns:
            Optional[User]: کاربر یا None در صورت عدم وجود.
        """
        if event.message and event.message.from_user:
            return event.message.from_user
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user
        if event.inline_query and event.inline_query.from_user:
            return event.inline_query.from_user
        if event.chosen_inline_result and event.chosen_inline_result.from_user:
            return event.chosen_inline_result.from_user
        return None

    async def get_global_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت کلی محدودیت نرخ درخواست.

        Returns:
            Dict[str, Any]: وضعیت کلی.
        """
        async with self._lock:
            total_users = len(self._user_requests)
            blocked_users = len(self._blocked_users)

            return {
                "total_users": total_users,
                "blocked_users": blocked_users,
                "is_enabled": self.config.enabled,
                "requests_per_window": self._rate_limit.requests_per_window,
                "window_seconds": self._rate_limit.window_seconds,
                "storage_backend": self._rate_limit.storage_backend,
                "blocking_enabled": self._rate_limit.enable_blocking,
                "whitelist_count": len(self._rate_limit.whitelist_ids) if self._rate_limit.whitelist_ids else 0,
            }

    async def clear_expired_blocks(self) -> None:
        """
        پاک کردن مسدودیت‌های منقضی‌شده.
        """
        now = time.time()
        async with self._lock:
            expired = [
                user_id for user_id, block_until in self._blocked_users.items()
                if block_until <= now
            ]
            for user_id in expired:
                del self._blocked_users[user_id]

            if expired:
                logger.info(f"Cleared {len(expired)} expired user blocks")

    async def clear_all_data(self) -> None:
        """
        پاک کردن تمام داده‌های محدودیت نرخ درخواست.
        """
        async with self._lock:
            self._user_requests.clear()
            self._blocked_users.clear()
            logger.info("Rate limiter data cleared")