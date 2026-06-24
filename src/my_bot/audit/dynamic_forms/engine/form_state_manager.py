# my_bot_project/src/my_bot/dynamic_forms/engine/form_state_manager.py
"""
مدیریت وضعیت فرم‌های پویا (Form State Manager).

این ماژول شامل کلاس `FormStateManager` است که مسئولیت مدیریت وضعیت
فرم در حین پر کردن (ذخیره پیشرفت، بازیابی، انقضا) را بر عهده دارد.
وضعیت هر کاربر شامل شناسه فرم، پاسخ‌های فعلی، مرحله جاری و زمان شروع است.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.infrastructure.cache.cache_manager import CacheManager

logger = get_logger(__name__)


@dataclass
class FormState:
    """
    وضعیت یک فرم در حال پر کردن توسط یک کاربر.

    Attributes:
        form_id: شناسه فرم.
        user_id: شناسه کاربر.
        answers: پاسخ‌های ثبت‌شده (نام فیلد -> مقدار).
        current_step: شماره مرحله فعلی (از ۱ شروع می‌شود).
        total_steps: تعداد کل مراحل (برای نمایش پیشرفت).
        started_at: زمان شروع پر کردن فرم.
        last_updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی (اختیاری).
    """
    form_id: int
    user_id: int
    answers: Dict[str, Any] = field(default_factory=dict)
    current_step: int = 1
    total_steps: int = 1
    started_at: datetime = field(default_factory=datetime.now)
    last_updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل وضعیت به دیکشنری برای سریال‌سازی.

        Returns:
            Dict[str, Any]: دیکشنری وضعیت.
        """
        return {
            "form_id": self.form_id,
            "user_id": self.user_id,
            "answers": self.answers,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormState":
        """
        ساخت وضعیت از دیکشنری.

        Args:
            data: دیکشنری داده‌ها.

        Returns:
            FormState: نمونه وضعیت.
        """
        started_at = None
        if data.get("started_at"):
            try:
                started_at = datetime.fromisoformat(data["started_at"])
            except (ValueError, TypeError):
                started_at = datetime.now()

        last_updated_at = None
        if data.get("last_updated_at"):
            try:
                last_updated_at = datetime.fromisoformat(data["last_updated_at"])
            except (ValueError, TypeError):
                last_updated_at = datetime.now()

        return cls(
            form_id=data["form_id"],
            user_id=data["user_id"],
            answers=data.get("answers", {}),
            current_step=data.get("current_step", 1),
            total_steps=data.get("total_steps", 1),
            started_at=started_at or datetime.now(),
            last_updated_at=last_updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )


class FormStateManager:
    """
    مدیریت وضعیت فرم‌ها در حین پر کردن.

    این کلاس با استفاده از حافظه داخلی و (اختیاری) کش، وضعیت فرم‌ها را
    ذخیره، بازیابی و به‌روزرسانی می‌کند. همچنین از انقضای خودکار وضعیت‌های
    منقضی‌شده پشتیبانی می‌کند.

    Attributes:
        cache_manager: مدیر کش (اختیاری).
        state_ttl_seconds: زمان انقضای وضعیت بر حسب ثانیه (پیش‌فرض ۳۶۰۰).
        use_cache: استفاده از کش (در صورت وجود).
        _local_cache: ذخیره‌سازی محلی (در صورت عدم وجود کش).
        _lock: قفل برای عملیات اتمیک.
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        state_ttl_seconds: int = 3600,
        use_cache: bool = True,
    ) -> None:
        """
        مقداردهی اولیه FormStateManager.

        Args:
            cache_manager: مدیر کش (اختیاری).
            state_ttl_seconds: زمان انقضای وضعیت بر حسب ثانیه (پیش‌فرض ۱ ساعت).
            use_cache: استفاده از کش (در صورت وجود).
        """
        self.cache_manager = cache_manager
        self.state_ttl_seconds = state_ttl_seconds
        self.use_cache = use_cache and cache_manager is not None

        # ذخیره‌سازی محلی (Fallback)
        self._local_cache: Dict[str, FormState] = {}
        self._lock = None  # در صورت نیاز می‌توان از asyncio.Lock استفاده کرد
        # اما برای سادگی از دیکشنری با قفل داخلی استفاده نمی‌کنیم
        # در محیط async بهتر است از asyncio.Lock استفاده شود

        logger.info(
            f"FormStateManager initialized: ttl={state_ttl_seconds}s, "
            f"use_cache={self.use_cache}, cache_manager={cache_manager is not None}"
        )

    async def create_state(
        self,
        form_id: int,
        user_id: int,
        total_steps: int = 1,
        initial_answers: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FormState:
        """
        ایجاد یک وضعیت جدید برای فرم.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.
            total_steps: تعداد کل مراحل.
            initial_answers: پاسخ‌های اولیه (اختیاری).
            metadata: داده‌های اضافی (اختیاری).

        Returns:
            FormState: وضعیت ایجادشده.

        Raises:
            ValidationError: اگر شناسه فرم یا کاربر نامعتبر باشد.
        """
        if form_id <= 0 or user_id <= 0:
            raise ValidationError(
                message="شناسه فرم و کاربر باید معتبر باشند.",
                context={"form_id": form_id, "user_id": user_id},
            )

        state = FormState(
            form_id=form_id,
            user_id=user_id,
            answers=initial_answers or {},
            current_step=1,
            total_steps=max(1, total_steps),
            started_at=datetime.now(),
            last_updated_at=datetime.now(),
            metadata=metadata or {},
        )

        await self._save_state(state)
        logger.debug(f"Created form state: form_id={form_id}, user_id={user_id}")
        return state

    async def get_state(self, form_id: int, user_id: int) -> Optional[FormState]:
        """
        دریافت وضعیت یک فرم برای کاربر.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            Optional[FormState]: وضعیت در صورت وجود، در غیر این صورت None.
        """
        key = self._get_key(form_id, user_id)
        state = None

        # تلاش از کش
        if self.use_cache:
            try:
                cached = await self.cache_manager.get(key)
                if cached:
                    # اگر داده‌های کش به‌صورت دیکشنری است
                    if isinstance(cached, dict):
                        state = FormState.from_dict(cached)
                    elif isinstance(cached, str):
                        # اگر به‌صورت JSON ذخیره شده است
                        data = json.loads(cached)
                        state = FormState.from_dict(data)
                    logger.debug(f"State retrieved from cache: {key}")
            except Exception as e:
                logger.warning(f"Error retrieving state from cache: {e}")

        # اگر در کش پیدا نشد، از حافظه محلی
        if state is None:
            state = self._local_cache.get(key)
            if state:
                logger.debug(f"State retrieved from local cache: {key}")

        # اگر وضعیت پیدا شد، بررسی انقضا
        if state:
            if self._is_expired(state):
                logger.debug(f"State expired: {key}")
                await self.clear_state(form_id, user_id)
                return None

        return state

    async def update_state(
        self,
        form_id: int,
        user_id: int,
        answers: Optional[Dict[str, Any]] = None,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[FormState]:
        """
        به‌روزرسانی وضعیت یک فرم.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.
            answers: پاسخ‌های جدید (با پاسخ‌های قبلی ادغام می‌شود).
            current_step: شماره مرحله جدید.
            total_steps: تعداد کل مراحل جدید.
            metadata: داده‌های اضافی جدید (با متادیتای قبلی ادغام می‌شود).

        Returns:
            Optional[FormState]: وضعیت به‌روزرسانی‌شده یا None در صورت عدم وجود.
        """
        state = await self.get_state(form_id, user_id)
        if not state:
            logger.warning(f"State not found for update: form_id={form_id}, user_id={user_id}")
            return None

        # به‌روزرسانی فیلدها
        if answers is not None:
            state.answers.update(answers)

        if current_step is not None:
            state.current_step = max(1, min(current_step, state.total_steps))

        if total_steps is not None:
            state.total_steps = max(1, total_steps)

        if metadata is not None:
            state.metadata.update(metadata)

        state.last_updated_at = datetime.now()

        await self._save_state(state)
        logger.debug(f"State updated: form_id={form_id}, user_id={user_id}, step={state.current_step}")
        return state

    async def save_answer(
        self,
        form_id: int,
        user_id: int,
        field_name: str,
        value: Any,
    ) -> Optional[FormState]:
        """
        ذخیره پاسخ یک فیلد در وضعیت فرم.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.
            field_name: نام فیلد.
            value: مقدار پاسخ.

        Returns:
            Optional[FormState]: وضعیت به‌روزرسانی‌شده یا None.
        """
        return await self.update_state(
            form_id=form_id,
            user_id=user_id,
            answers={field_name: value},
        )

    async def get_answer(
        self,
        form_id: int,
        user_id: int,
        field_name: str,
    ) -> Optional[Any]:
        """
        دریافت پاسخ یک فیلد خاص.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.
            field_name: نام فیلد.

        Returns:
            Optional[Any]: مقدار پاسخ یا None در صورت عدم وجود.
        """
        state = await self.get_state(form_id, user_id)
        if not state:
            return None
        return state.answers.get(field_name)

    async def clear_state(self, form_id: int, user_id: int) -> bool:
        """
        حذف وضعیت یک فرم.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            bool: True در صورت حذف موفق.
        """
        key = self._get_key(form_id, user_id)

        # حذف از کش
        if self.use_cache:
            try:
                await self.cache_manager.delete(key)
                logger.debug(f"State removed from cache: {key}")
            except Exception as e:
                logger.warning(f"Error removing state from cache: {e}")

        # حذف از حافظه محلی
        if key in self._local_cache:
            del self._local_cache[key]
            logger.debug(f"State removed from local cache: {key}")

        return True

    async def clear_all_user_states(self, user_id: int) -> int:
        """
        حذف تمام وضعیت‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            int: تعداد وضعیت‌های حذف‌شده.
        """
        count = 0
        keys_to_delete = []

        # پاک کردن از حافظه محلی
        for key, state in list(self._local_cache.items()):
            if state.user_id == user_id:
                del self._local_cache[key]
                count += 1
                keys_to_delete.append(key)

        # پاک کردن از کش (با توجه به اینکه کش ممکن است کلیدهای مختلف داشته باشد،
        # باید الگوی کلیدها را بدانیم. در اینجا فرض می‌کنیم کلیدها فرمت دارند)
        if self.use_cache:
            try:
                # برای سادگی، کلیدها را یکی‌یکی حذف می‌کنیم
                for key in keys_to_delete:
                    await self.cache_manager.delete(key)
            except Exception as e:
                logger.warning(f"Error clearing user states from cache: {e}")

        logger.info(f"Cleared {count} states for user {user_id}")
        return count

    async def cleanup_expired_states(self) -> int:
        """
        پاک کردن وضعیت‌های منقضی‌شده.

        Returns:
            int: تعداد وضعیت‌های حذف‌شده.
        """
        expired_keys = []
        for key, state in self._local_cache.items():
            if self._is_expired(state):
                expired_keys.append(key)

        for key in expired_keys:
            del self._local_cache[key]

        # همچنین می‌توان در کش نیز پاکسازی کرد، اما کش خودش TTL دارد
        # و نیاز به پاکسازی دستی ندارد.

        logger.info(f"Cleaned up {len(expired_keys)} expired states")
        return len(expired_keys)

    def _is_expired(self, state: FormState) -> bool:
        """
        بررسی انقضای یک وضعیت.

        Args:
            state: وضعیت فرم.

        Returns:
            bool: True اگر وضعیت منقضی شده باشد.
        """
        if self.state_ttl_seconds <= 0:
            return False
        elapsed = (datetime.now() - state.last_updated_at).total_seconds()
        return elapsed > self.state_ttl_seconds

    def _get_key(self, form_id: int, user_id: int) -> str:
        """
        تولید کلید یکتا برای وضعیت.

        Args:
            form_id: شناسه فرم.
            user_id: شناسه کاربر.

        Returns:
            str: کلید.
        """
        return f"form_state:{form_id}:{user_id}"

    async def _save_state(self, state: FormState) -> None:
        """
        ذخیره وضعیت در کش و حافظه محلی.

        Args:
            state: وضعیت فرم.
        """
        key = self._get_key(state.form_id, state.user_id)

        # ذخیره در حافظه محلی
        self._local_cache[key] = state

        # ذخیره در کش
        if self.use_cache:
            try:
                state_dict = state.to_dict()
                await self.cache_manager.set(
                    key=key,
                    value=state_dict,
                    ttl=self.state_ttl_seconds,
                )
                logger.debug(f"State saved to cache: {key}")
            except Exception as e:
                logger.warning(f"Error saving state to cache: {e}")

    async def get_all_user_states(self, user_id: int) -> List[FormState]:
        """
        دریافت تمام وضعیت‌های یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            List[FormState]: لیست وضعیت‌ها.
        """
        states = []
        for state in self._local_cache.values():
            if state.user_id == user_id:
                states.append(state)

        # اگر از کش استفاده می‌کنیم، ممکن است وضعیت‌هایی در کش باشند که در حافظه محلی نیستند
        # اما برای سادگی، فقط حافظه محلی را بررسی می‌کنیم.
        # در نسخه کامل، باید از کش نیز خوانده شود.

        return states

    async def get_state_count(self) -> int:
        """
        دریافت تعداد وضعیت‌های موجود.

        Returns:
            int: تعداد وضعیت‌ها.
        """
        return len(self._local_cache)

    async def get_expired_count(self) -> int:
        """
        دریافت تعداد وضعیت‌های منقضی‌شده.

        Returns:
            int: تعداد وضعیت‌های منقضی‌شده.
        """
        count = 0
        for state in self._local_cache.values():
            if self._is_expired(state):
                count += 1
        return count

    async def clear_all(self) -> int:
        """
        پاک کردن تمام وضعیت‌ها.

        Returns:
            int: تعداد وضعیت‌های حذف‌شده.
        """
        count = len(self._local_cache)
        self._local_cache.clear()

        # در کش، نمی‌توان به‌سادگی همه را پاک کرد، اما می‌توان الگوی کلیدها را حذف کرد
        if self.use_cache:
            try:
                # این کار به پاک کردن همه کلیدهای با پیشوند form_state: نیاز دارد
                # که ممکن است پشتیبانی نشود، بنابراین فقط لاگ می‌کنیم
                logger.warning("Clearing all states from cache is not fully supported.")
            except Exception as e:
                logger.warning(f"Error clearing states from cache: {e}")

        logger.info(f"Cleared all {count} states")
        return count

    def set_ttl(self, ttl_seconds: int) -> None:
        """
        تنظیم زمان انقضای جدید.

        Args:
            ttl_seconds: زمان انقضا بر حسب ثانیه.
        """
        if ttl_seconds < 0:
            raise ValueError("TTL cannot be negative")
        self.state_ttl_seconds = ttl_seconds
        logger.info(f"State TTL set to {ttl_seconds} seconds")