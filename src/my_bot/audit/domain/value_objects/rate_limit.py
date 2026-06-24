# my_bot_project/src/my_bot/domain/value_objects/rate_limit.py
"""
ارزش‌مقدار محدودیت نرخ درخواست (Rate Limit Value Object).

این کلاس نمایانگر محدودیت نرخ درخواست برای کاربران است و
از الگوریتم Sliding Window برای محاسبه دقیق تعداد درخواست‌های
مجاز در بازه‌های زمانی مشخص استفاده می‌کند.
محدودیت نرخ به‌صورت غیرقابل تغییر (Immutable) ذخیره می‌شود.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RateLimit:
    """
    ارزش‌مقدار محدودیت نرخ درخواست.

    این کلاس با استفاده از الگوریتم Sliding Window، محدودیت نرخ
    درخواست را برای کاربران مدیریت می‌کند.

    Attributes:
        requests_per_window: تعداد درخواست‌های مجاز در هر پنجره.
        window_seconds: طول پنجره‌ی زمانی بر حسب ثانیه.
        storage_backend: نوع ذخیره‌سازی (مثلاً 'redis' یا 'local').
        key_prefix: پیشوند کلیدها در ذخیره‌سازی.
        block_duration_seconds: مدت زمان بلاک شدن پس از تجاوز از حد (پیش‌فرض ۳۰۰).
        enable_blocking: فعال‌سازی بلاک کردن کاربران متخلف (پیش‌فرض True).
        whitelist_ids: لیست شناسه‌های کاربران معاف از محدودیت (اختیاری).
    """

    requests_per_window: int
    window_seconds: int
    storage_backend: str
    key_prefix: str = "rate_limit"
    block_duration_seconds: int = 300
    enable_blocking: bool = True
    whitelist_ids: Optional[List[int]] = None

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_requests_per_window()
        self._validate_window_seconds()
        self._validate_block_duration()
        self._validate_storage_backend()
        self._validate_whitelist()

    def _validate_requests_per_window(self) -> None:
        """اعتبارسنجی تعداد درخواست‌های مجاز."""
        if self.requests_per_window <= 0:
            raise ValidationError(
                message="تعداد درخواست‌های مجاز باید بیشتر از صفر باشد.",
                context={"requests_per_window": self.requests_per_window},
            )

    def _validate_window_seconds(self) -> None:
        """اعتبارسنجی طول پنجره زمانی."""
        if self.window_seconds <= 0:
            raise ValidationError(
                message="طول پنجره زمانی باید بیشتر از صفر باشد.",
                context={"window_seconds": self.window_seconds},
            )

    def _validate_block_duration(self) -> None:
        """اعتبارسنجی مدت زمان بلاک."""
        if self.block_duration_seconds < 0:
            raise ValidationError(
                message="مدت زمان بلاک نمی‌تواند منفی باشد.",
                context={"block_duration_seconds": self.block_duration_seconds},
            )

    def _validate_storage_backend(self) -> None:
        """اعتبارسنجی نوع ذخیره‌سازی."""
        if self.storage_backend not in ("redis", "local"):
            raise ValidationError(
                message=f"نوع ذخیره‌سازی '{self.storage_backend}' مجاز نیست. گزینه‌های مجاز: redis, local",
                context={"storage_backend": self.storage_backend},
            )

    def _validate_whitelist(self) -> None:
        """اعتبارسنجی لیست سفید."""
        if self.whitelist_ids is not None:
            if not isinstance(self.whitelist_ids, list):
                raise ValidationError(
                    message="لیست سفید باید به‌صورت لیست باشد.",
                    context={"whitelist_ids": self.whitelist_ids},
                )
            for user_id in self.whitelist_ids:
                if not isinstance(user_id, int) or user_id <= 0:
                    raise ValidationError(
                        message="شناسه‌های کاربران در لیست سفید باید اعداد صحیح مثبت باشند.",
                        context={"user_id": user_id},
                    )

    def get_window_start(self, current_time: datetime) -> datetime:
        """
        دریافت زمان شروع پنجره‌ی فعلی.

        Args:
            current_time: زمان فعلی.

        Returns:
            زمان شروع پنجره (جاری).
        """
        return current_time - timedelta(seconds=self.window_seconds)

    def is_whitelisted(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر در لیست سفید قرار دارد.

        Args:
            user_id: شناسه کاربر.

        Returns:
            True اگر کاربر در لیست سفید باشد.
        """
        if self.whitelist_ids is None:
            return False
        return user_id in self.whitelist_ids

    def check_limit(
        self,
        user_id: int,
        request_history: List[datetime],
        current_time: Optional[datetime] = None,
    ) -> Tuple[bool, int, Optional[int]]:
        """
        بررسی محدودیت نرخ درخواست برای یک کاربر با استفاده از الگوریتم Sliding Window.

        Args:
            user_id: شناسه کاربر.
            request_history: لیست زمان‌های درخواست‌های قبلی.
            current_time: زمان فعلی (اختیاری، پیش‌فرض: زمان حال).

        Returns:
            Tuple شامل:
                - bool: آیا درخواست مجاز است؟
                - int: تعداد درخواست‌های باقی‌مانده در پنجره.
                - Optional[int]: زمان انتظار پیشنهادی برای تلاش مجدد (در صورت غیرمجاز بودن).
        """
        if self.is_whitelisted(user_id):
            return True, self.requests_per_window, None

        if current_time is None:
            current_time = datetime.now()

        # محاسبه زمان شروع پنجره
        window_start = self.get_window_start(current_time)

        # فیلتر کردن درخواست‌های قدیمی‌تر از پنجره
        valid_requests = [
            req_time for req_time in request_history
            if req_time >= window_start and req_time <= current_time
        ]

        # تعداد درخواست‌های معتبر در پنجره
        current_count = len(valid_requests)

        # محاسبه درخواست‌های باقی‌مانده
        remaining = max(0, self.requests_per_window - current_count)

        # بررسی محدودیت
        if current_count >= self.requests_per_window:
            # محاسبه زمان انتظار برای تلاش مجدد
            # قدیمی‌ترین درخواست در پنجره را پیدا می‌کنیم
            if valid_requests:
                oldest_request = min(valid_requests)
                wait_time = self.window_seconds - (current_time - oldest_request).seconds
                return False, 0, max(1, wait_time)
            return False, 0, self.window_seconds

        return True, remaining, None

    def get_redis_key(self, user_id: int, action: str = "default") -> str:
        """
        تولید کلید مناسب برای ذخیره‌سازی در Redis.

        Args:
            user_id: شناسه کاربر.
            action: نوع عملیات (اختیاری).

        Returns:
            کلید Redis.
        """
        return f"{self.key_prefix}:{action}:{user_id}"

    def get_local_key(self, user_id: int, action: str = "default") -> str:
        """
        تولید کلید مناسب برای ذخیره‌سازی محلی (Local).

        Args:
            user_id: شناسه کاربر.
            action: نوع عملیات (اختیاری).

        Returns:
            کلید محلی.
        """
        return f"{self.key_prefix}_{action}_{user_id}"

    def to_dict(self) -> Dict:
        """
        تبدیل ارزش‌مقدار به دیکشنری برای سریال‌سازی.

        Returns:
            دیکشنری شامل اطلاعات محدودیت نرخ.
        """
        return {
            "requests_per_window": self.requests_per_window,
            "window_seconds": self.window_seconds,
            "storage_backend": self.storage_backend,
            "key_prefix": self.key_prefix,
            "block_duration_seconds": self.block_duration_seconds,
            "enable_blocking": self.enable_blocking,
            "whitelist_ids": self.whitelist_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RateLimit":
        """
        ساخت ارزش‌مقدار از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات محدودیت نرخ.

        Returns:
            نمونه‌ای از RateLimit.
        """
        return cls(
            requests_per_window=data["requests_per_window"],
            window_seconds=data["window_seconds"],
            storage_backend=data.get("storage_backend", "local"),
            key_prefix=data.get("key_prefix", "rate_limit"),
            block_duration_seconds=data.get("block_duration_seconds", 300),
            enable_blocking=data.get("enable_blocking", True),
            whitelist_ids=data.get("whitelist_ids"),
        )

    def __str__(self) -> str:
        """نمایش رشته‌ای محدودیت نرخ."""
        return (
            f"RateLimit(requests={self.requests_per_window}, "
            f"window={self.window_seconds}s, backend={self.storage_backend})"
        )