# my_bot_project/src/my_bot/shared/decorators/log_execution.py
"""
دکوراتور ثبت لاگ اجرا (Log Execution Decorator).

این دکوراتور با ثبت اطلاعاتی مانند زمان شروع، پایان، آرگومان‌ها، مقدار بازگشتی،
زمان اجرا و خطاهای احتمالی، به دیباگ و مانیتورینگ توابع کمک می‌کند.
از این دکوراتور برای ردیابی عملکرد و عیب‌یابی استفاده می‌شود.
"""

import asyncio
import functools
import time
import inspect
from typing import (
    Callable, Optional, Any, TypeVar, ParamSpec,
    Dict, List, Tuple, Union, Awaitable,
)
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


# ==========================================
# دکوراتور اصلی
# ==========================================

def log_execution(
    log_level: str = "DEBUG",
    log_args: bool = True,
    log_result: bool = True,
    log_duration: bool = True,
    log_exceptions: bool = True,
    max_arg_length: int = 500,
    max_result_length: int = 1000,
    exclude_args: Optional[List[str]] = None,
    log_function_name: bool = True,
    log_module_name: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    دکوراتور برای ثبت لاگ اجرای توابع.

    Args:
        log_level: سطح لاگ (پیش‌فرض: "DEBUG").
        log_args: ثبت آرگومان‌ها (پیش‌فرض: True).
        log_result: ثبت مقدار بازگشتی (پیش‌فرض: True).
        log_duration: ثبت زمان اجرا (پیش‌فرض: True).
        log_exceptions: ثبت استثناها (پیش‌فرض: True).
        max_arg_length: حداکثر طول نمایش آرگومان‌ها (پیش‌فرض: ۵۰۰).
        max_result_length: حداکثر طول نمایش نتیجه (پیش‌فرض: ۱۰۰۰).
        exclude_args: لیست نام آرگومان‌هایی که نباید لاگ شوند (مثلاً برای حذف اطلاعات حساس).
        log_function_name: ثبت نام تابع (پیش‌فرض: True).
        log_module_name: ثبت نام ماژول (پیش‌فرض: True).

    Returns:
        Callable: دکوراتور.

    Example:
        @log_execution(log_level="INFO", log_args=True, log_result=True)
        async def process_order(order_id: int, user_id: int) -> dict:
            ...

        @log_execution(exclude_args=["password", "token"])
        def authenticate(username: str, password: str) -> bool:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        is_async = asyncio.iscoroutinefunction(func)
        func_name = func.__name__
        module_name = func.__module__

        # سطح لاگ
        log_level_map = {
            "DEBUG": logger.debug,
            "INFO": logger.info,
            "WARNING": logger.warning,
            "ERROR": logger.error,
            "CRITICAL": logger.critical,
        }
        log_func = log_level_map.get(log_level.upper(), logger.debug)

        # نام نمایشی تابع
        display_name = f"{module_name}.{func_name}" if log_module_name else func_name

        def format_arg(arg: Any) -> str:
            """فرمت‌سازی یک آرگومان برای نمایش."""
            if arg is None:
                return "None"
            if isinstance(arg, (int, float, bool)):
                return str(arg)
            if isinstance(arg, str):
                if len(arg) > max_arg_length:
                    return f"{arg[:max_arg_length]}... (truncated)"
                return arg
            if isinstance(arg, (list, tuple)):
                if len(arg) > 10:
                    return f"[{len(arg)} items]"
                return str(arg)
            if isinstance(arg, dict):
                if len(arg) > 5:
                    return f"{{{len(arg)} keys}}"
                return str(arg)
            # برای اشیاء دیگر، نام کلاس را نشان دهیم
            return f"<{arg.__class__.__name__}>"

        def format_result(result: Any) -> str:
            """فرمت‌سازی مقدار بازگشتی برای نمایش."""
            if result is None:
                return "None"
            if isinstance(result, (int, float, bool)):
                return str(result)
            if isinstance(result, str):
                if len(result) > max_result_length:
                    return f"{result[:max_result_length]}... (truncated)"
                return result
            if isinstance(result, (list, tuple)):
                if len(result) > 10:
                    return f"[{len(result)} items]"
                return str(result)
            if isinstance(result, dict):
                if len(result) > 5:
                    return f"{{{len(result)} keys}}"
                return str(result)
            return f"<{result.__class__.__name__}>"

        def get_signature(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
            """ساخت رشته نمایش آرگومان‌ها."""
            if not log_args:
                return ""

            # استخراج نام پارامترها از تابع
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            # ساختن دیکشنری آرگومان‌ها
            all_args = {}
            for i, value in enumerate(args):
                if i < len(param_names):
                    name = param_names[i]
                    if exclude_args and name in exclude_args:
                        all_args[name] = "***"
                    else:
                        all_args[name] = format_arg(value)
                else:
                    all_args[f"arg{i}"] = format_arg(value)

            for name, value in kwargs.items():
                if exclude_args and name in exclude_args:
                    all_args[name] = "***"
                else:
                    all_args[name] = format_arg(value)

            # ساخت رشته
            arg_parts = [f"{k}={v}" for k, v in all_args.items()]
            if len(arg_parts) > 10:
                # اگر آرگومان‌ها زیاد است، فقط تعدادی را نشان دهیم
                arg_parts = arg_parts[:10] + [f"... ({len(arg_parts) - 10} more)"]
            return ", ".join(arg_parts)

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع همزمان."""
            start_time = time.time()
            start_dt = datetime.now()

            # لاگ ورود
            if log_function_name:
                signature = get_signature(args, kwargs)
                log_func(
                    f"Calling {display_name}({signature}) at {start_dt.isoformat()}"
                )

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                end_dt = datetime.now()

                # لاگ خروج
                if log_function_name:
                    result_str = format_result(result) if log_result else ""
                    duration_str = f" in {duration:.4f}s" if log_duration else ""
                    log_func(
                        f"{display_name} returned {result_str}{duration_str} "
                        f"at {end_dt.isoformat()}"
                    )
                return result

            except Exception as e:
                duration = time.time() - start_time
                if log_exceptions:
                    log_func(
                        f"{display_name} raised {e.__class__.__name__}: {e} "
                        f"after {duration:.4f}s"
                    )
                raise

        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            """Wrapper برای توابع غیرهمزمان."""
            start_time = time.time()
            start_dt = datetime.now()

            # لاگ ورود
            if log_function_name:
                signature = get_signature(args, kwargs)
                log_func(
                    f"Calling {display_name}({signature}) at {start_dt.isoformat()}"
                )

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                end_dt = datetime.now()

                # لاگ خروج
                if log_function_name:
                    result_str = format_result(result) if log_result else ""
                    duration_str = f" in {duration:.4f}s" if log_duration else ""
                    log_func(
                        f"{display_name} returned {result_str}{duration_str} "
                        f"at {end_dt.isoformat()}"
                    )
                return result

            except Exception as e:
                duration = time.time() - start_time
                if log_exceptions:
                    log_func(
                        f"{display_name} raised {e.__class__.__name__}: {e} "
                        f"after {duration:.4f}s"
                    )
                raise

        return async_wrapper if is_async else sync_wrapper

    return decorator


# ==========================================
# دکوراتورهای از پیش پیکربندی‌شده
# ==========================================

def debug_log(func: Callable) -> Callable:
    """
    دکوراتور برای لاگ دیباگ با تنظیمات پیش‌فرض (سطح DEBUG).

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return log_execution(
        log_level="DEBUG",
        log_args=True,
        log_result=True,
        log_duration=True,
        log_exceptions=True,
    )(func)


def info_log(func: Callable) -> Callable:
    """
    دکوراتور برای لاگ اطلاعات با تنظیمات پیش‌فرض (سطح INFO).

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return log_execution(
        log_level="INFO",
        log_args=False,  # برای اطلاعات عمومی، آرگومان‌ها را لاگ نکنیم
        log_result=False,
        log_duration=True,
        log_exceptions=True,
    )(func)


def error_log(func: Callable) -> Callable:
    """
    دکوراتور برای لاگ خطاها (فقط زمان بروز استثنا).

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return log_execution(
        log_level="ERROR",
        log_args=False,
        log_result=False,
        log_duration=True,
        log_exceptions=True,
    )(func)


def silent_log(func: Callable) -> Callable:
    """
    دکوراتور برای لاگ حداقلی (فقط نام تابع و مدت زمان).

    Args:
        func: تابع برای تزئین.

    Returns:
        Callable: تابع تزئین‌شده.
    """
    return log_execution(
        log_level="DEBUG",
        log_args=False,
        log_result=False,
        log_duration=True,
        log_exceptions=False,
    )(func)


# ==========================================
# تابع کمکی برای لاگ دستی
# ==========================================

def log_function_call(
    func_name: str,
    args: Tuple[Any, ...] = (),
    kwargs: Optional[Dict[str, Any]] = None,
    level: str = "DEBUG",
) -> None:
    """
    تابع کمکی برای لاگ کردن یک فراخوانی تابع بدون استفاده از دکوراتور.

    Args:
        func_name: نام تابع.
        args: آرگومان‌های موقعیتی.
        kwargs: آرگومان‌های نام‌دار.
        level: سطح لاگ.
    """
    log_level_map = {
        "DEBUG": logger.debug,
        "INFO": logger.info,
        "WARNING": logger.warning,
        "ERROR": logger.error,
        "CRITICAL": logger.critical,
    }
    log_func = log_level_map.get(level.upper(), logger.debug)

    kwargs = kwargs or {}
    arg_str = ", ".join([str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()])
    if len(arg_str) > 200:
        arg_str = arg_str[:200] + "... (truncated)"
    log_func(f"Function call: {func_name}({arg_str})")