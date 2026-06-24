# my_bot_project/src/my_bot/shared/utils/date_helpers.py
"""
توابع کمکی تاریخ و زمان (Date Helpers).

این ماژول شامل توابع کمکی برای کار با تاریخ و زمان است که در سراسر
پروژه مورد استفاده قرار می‌گیرند. شامل فرمت‌سازی، تبدیل، محاسبه بازه‌ها،
تشخیص منطقه زمانی و اعتبارسنجی است.
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, Tuple, Union, List
import pytz
from zoneinfo import ZoneInfo

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


# ==========================================
# ثابت‌های زمان
# ==========================================

# فرمت‌های استاندارد تاریخ و زمان
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
DATETIME_ISO_WITH_TZ = "%Y-%m-%dT%H:%M:%S%z"

# منطقه زمانی پیش‌فرض
DEFAULT_TIMEZONE = "Asia/Tehran"

# مناطق زمانی پشتیبانی‌شده
SUPPORTED_TIMEZONES = [
    "Asia/Tehran",
    "UTC",
    "Asia/Dubai",
    "Europe/London",
    "America/New_York",
    "America/Los_Angeles",
    "Asia/Tokyo",
    "Australia/Sydney",
]


# ==========================================
# دریافت زمان فعلی
# ==========================================

def now(timezone_str: Optional[str] = None) -> datetime:
    """
    دریافت زمان فعلی با منطقه زمانی مشخص.

    Args:
        timezone_str: نام منطقه زمانی (اختیاری، پیش‌فرض: DEFAULT_TIMEZONE).

    Returns:
        datetime: زمان فعلی با منطقه زمانی.
    """
    tz = get_timezone(timezone_str or DEFAULT_TIMEZONE)
    return datetime.now(tz)


def today(timezone_str: Optional[str] = None) -> date:
    """
    دریافت تاریخ امروز با منطقه زمانی مشخص.

    Args:
        timezone_str: نام منطقه زمانی (اختیاری، پیش‌فرض: DEFAULT_TIMEZONE).

    Returns:
        date: تاریخ امروز.
    """
    return now(timezone_str).date()


def utc_now() -> datetime:
    """
    دریافت زمان فعلی در UTC.

    Returns:
        datetime: زمان فعلی در UTC.
    """
    return datetime.now(timezone.utc)


# ==========================================
# منطقه زمانی
# ==========================================

def get_timezone(timezone_str: str) -> ZoneInfo:
    """
    دریافت شیء منطقه زمانی.

    Args:
        timezone_str: نام منطقه زمانی.

    Returns:
        ZoneInfo: شیء منطقه زمانی.

    Raises:
        ValidationError: اگر منطقه زمانی نامعتبر باشد.
    """
    if not timezone_str or not timezone_str.strip():
        timezone_str = DEFAULT_TIMEZONE

    try:
        return ZoneInfo(timezone_str)
    except Exception as e:
        logger.warning(f"Invalid timezone '{timezone_str}': {e}. Using default.")
        return ZoneInfo(DEFAULT_TIMEZONE)


def get_timezone_offset(timezone_str: str) -> str:
    """
    دریافت offset منطقه زمانی به‌صورت رشته (مثلاً +03:30).

    Args:
        timezone_str: نام منطقه زمانی.

    Returns:
        str: offset منطقه زمانی.

    Raises:
        ValidationError: اگر منطقه زمانی نامعتبر باشد.
    """
    tz = get_timezone(timezone_str)
    now = datetime.now(tz)
    offset = now.utcoffset()
    if offset is None:
        return "+00:00"

    hours = offset.total_seconds() // 3600
    minutes = (offset.total_seconds() % 3600) // 60
    return f"{'+' if hours >= 0 else ''}{int(hours):02d}:{int(minutes):02d}"


def get_timezone_name(timezone_str: str) -> str:
    """
    دریافت نام نمایشی منطقه زمانی.

    Args:
        timezone_str: نام منطقه زمانی.

    Returns:
        str: نام نمایشی منطقه زمانی.

    Raises:
        ValidationError: اگر منطقه زمانی نامعتبر باشد.
    """
    tz = get_timezone(timezone_str)
    return str(tz)


def get_supported_timezones() -> List[str]:
    """
    دریافت لیست مناطق زمانی پشتیبانی‌شده.

    Returns:
        List[str]: لیست نام مناطق زمانی.
    """
    return SUPPORTED_TIMEZONES.copy()


# ==========================================
# فرمت‌سازی تاریخ و زمان
# ==========================================

def format_datetime(
    dt: datetime,
    format_str: Optional[str] = None,
    timezone_str: Optional[str] = None,
) -> str:
    """
    فرمت‌سازی یک شیء datetime به‌صورت رشته.

    Args:
        dt: شیء datetime.
        format_str: فرمت مورد نظر (اختیاری، پیش‌فرض: DATETIME_FORMAT).
        timezone_str: منطقه زمانی برای تبدیل (اختیاری).

    Returns:
        str: رشته فرمت‌شده.

    Raises:
        ValidationError: اگر datetime نامعتبر باشد.
    """
    if dt is None:
        raise ValidationError(
            message="datetime نمی‌تواند None باشد.",
            context={"dt": dt},
        )

    if format_str is None:
        format_str = DATETIME_FORMAT

    # تبدیل به منطقه زمانی مشخص (در صورت وجود)
    if timezone_str:
        tz = get_timezone(timezone_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)

    return dt.strftime(format_str)


def format_date(dt: Union[datetime, date], timezone_str: Optional[str] = None) -> str:
    """
    فرمت‌سازی تاریخ به‌صورت رشته (YYYY-MM-DD).

    Args:
        dt: شیء datetime یا date.
        timezone_str: منطقه زمانی برای تبدیل (اختیاری).

    Returns:
        str: تاریخ فرمت‌شده.
    """
    if isinstance(dt, datetime):
        if timezone_str:
            tz = get_timezone(timezone_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            else:
                dt = dt.astimezone(tz)
        return dt.strftime(DATE_FORMAT)
    else:
        return dt.strftime(DATE_FORMAT)


def format_time(dt: Union[datetime, time], timezone_str: Optional[str] = None) -> str:
    """
    فرمت‌سازی زمان به‌صورت رشته (HH:MM:SS).

    Args:
        dt: شیء datetime یا time.
        timezone_str: منطقه زمانی برای تبدیل (اختیاری).

    Returns:
        str: زمان فرمت‌شده.
    """
    if isinstance(dt, datetime):
        if timezone_str:
            tz = get_timezone(timezone_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            else:
                dt = dt.astimezone(tz)
        return dt.strftime(TIME_FORMAT)
    else:
        return dt.strftime(TIME_FORMAT)


def format_iso_datetime(dt: datetime, timezone_str: Optional[str] = None) -> str:
    """
    فرمت‌سازی datetime به‌صورت ISO 8601.

    Args:
        dt: شیء datetime.
        timezone_str: منطقه زمانی برای تبدیل (اختیاری).

    Returns:
        str: رشته ISO فرمت‌شده.
    """
    if timezone_str:
        tz = get_timezone(timezone_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)
    return dt.isoformat()


def format_persian_date(dt: Union[datetime, date], timezone_str: Optional[str] = None) -> str:
    """
    فرمت‌سازی تاریخ به‌صورت شمسی (فارسی).

    توجه: این تابع از کتابخانه‌های تبدیل تاریخ شمسی استفاده می‌کند.
    برای استفاده واقعی، باید کتابخانه‌های مناسب مثل `jdatetime` را نصب کنید.

    Args:
        dt: شیء datetime یا date.
        timezone_str: منطقه زمانی برای تبدیل (اختیاری).

    Returns:
        str: تاریخ شمسی فرمت‌شده.
    """
    # این یک پیاده‌سازی ساده است و نیاز به کتابخانه jdatetime دارد
    # برای استفاده واقعی، jdatetime را نصب کنید
    try:
        import jdatetime

        if isinstance(dt, datetime):
            if timezone_str:
                tz = get_timezone(timezone_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tz)
                else:
                    dt = dt.astimezone(tz)
            gregorian = dt.date()
        else:
            gregorian = dt

        jalali = jdatetime.date.fromgregorian(date=gregorian)
        return jalali.strftime("%Y/%m/%d")
    except ImportError:
        # Fallback به میلادی
        logger.warning("jdatetime not installed. Using Gregorian date.")
        return format_date(dt, timezone_str)


# ==========================================
# تبدیل و پارسینگ
# ==========================================

def parse_datetime(
    date_str: str,
    format_str: Optional[str] = None,
    timezone_str: Optional[str] = None,
) -> datetime:
    """
    پارسینگ یک رشته به شیء datetime.

    Args:
        date_str: رشته تاریخ و زمان.
        format_str: فرمت رشته (اختیاری، پیش‌فرض: DATETIME_FORMAT).
        timezone_str: منطقه زمانی برای اعمال (اختیاری).

    Returns:
        datetime: شیء datetime.

    Raises:
        ValidationError: اگر رشته قابل پارسینگ نباشد.
    """
    if not date_str or not date_str.strip():
        raise ValidationError(
            message="رشته تاریخ نمی‌تواند خالی باشد.",
            context={"date_str": date_str},
        )

    if format_str is None:
        format_str = DATETIME_FORMAT

    try:
        dt = datetime.strptime(date_str.strip(), format_str)
        if timezone_str:
            tz = get_timezone(timezone_str)
            dt = dt.replace(tzinfo=tz)
        return dt
    except ValueError as e:
        raise ValidationError(
            message=f"رشته تاریخ '{date_str}' با فرمت '{format_str}' مطابقت ندارد.",
            context={"date_str": date_str, "format": format_str, "error": str(e)},
        )


def parse_date(date_str: str, timezone_str: Optional[str] = None) -> date:
    """
    پارسینگ یک رشته به شیء date.

    Args:
        date_str: رشته تاریخ (فرمت: YYYY-MM-DD).
        timezone_str: منطقه زمانی برای اعمال (اختیاری).

    Returns:
        date: شیء date.

    Raises:
        ValidationError: اگر رشته قابل پارسینگ نباشد.
    """
    dt = parse_datetime(date_str, DATE_FORMAT, timezone_str)
    return dt.date()


def parse_iso_datetime(date_str: str, timezone_str: Optional[str] = None) -> datetime:
    """
    پارسینگ رشته ISO 8601 به شیء datetime.

    Args:
        date_str: رشته ISO 8601.
        timezone_str: منطقه زمانی برای اعمال (اختیاری).

    Returns:
        datetime: شیء datetime.

    Raises:
        ValidationError: اگر رشته قابل پارسینگ نباشد.
    """
    try:
        dt = datetime.fromisoformat(date_str)
        if timezone_str:
            tz = get_timezone(timezone_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            else:
                dt = dt.astimezone(tz)
        return dt
    except ValueError as e:
        raise ValidationError(
            message=f"رشته ISO '{date_str}' معتبر نیست.",
            context={"date_str": date_str, "error": str(e)},
        )


# ==========================================
# محاسبه بازه‌های زمانی
# ==========================================

def get_date_range(
    start_date: Union[datetime, date, str],
    end_date: Union[datetime, date, str],
    inclusive: bool = True,
) -> Tuple[datetime, datetime]:
    """
    تبدیل تاریخ‌های شروع و پایان به اشیاء datetime.

    Args:
        start_date: تاریخ شروع.
        end_date: تاریخ پایان.
        inclusive: آیا تاریخ‌های شروع و پایان شامل شوند (پیش‌فرض True).

    Returns:
        Tuple[datetime, datetime]: تاریخ‌های شروع و پایان.

    Raises:
        ValidationError: اگر تاریخ‌ها نامعتبر باشند یا شروع بعد از پایان باشد.
    """
    # تبدیل به datetime
    if isinstance(start_date, str):
        start = parse_datetime(start_date)
    elif isinstance(start_date, date) and not isinstance(start_date, datetime):
        start = datetime.combine(start_date, datetime.min.time())
    else:
        start = start_date

    if isinstance(end_date, str):
        end = parse_datetime(end_date)
    elif isinstance(end_date, date) and not isinstance(end_date, datetime):
        end = datetime.combine(end_date, datetime.max.time())
    else:
        end = end_date

    # اعتبارسنجی
    if start > end:
        raise ValidationError(
            message="تاریخ شروع باید قبل از تاریخ پایان باشد.",
            context={"start_date": start, "end_date": end},
        )

    # تنظیم زمان (برای بازه‌های شامل)
    if inclusive:
        if isinstance(start_date, (date, str)) and not isinstance(start_date, datetime):
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        if isinstance(end_date, (date, str)) and not isinstance(end_date, datetime):
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start, end


def get_date_range_days(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> int:
    """
    محاسبه تعداد روزهای بین دو تاریخ.

    Args:
        start_date: تاریخ شروع.
        end_date: تاریخ پایان.

    Returns:
        int: تعداد روزها.

    Raises:
        ValidationError: اگر تاریخ‌ها نامعتبر باشند.
    """
    if isinstance(start_date, datetime):
        start = start_date.date()
    else:
        start = start_date

    if isinstance(end_date, datetime):
        end = end_date.date()
    else:
        end = end_date

    delta = end - start
    return abs(delta.days)


def get_date_range_weeks(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> float:
    """
    محاسبه تعداد هفته‌های بین دو تاریخ.

    Args:
        start_date: تاریخ شروع.
        end_date: تاریخ پایان.

    Returns:
        float: تعداد هفته‌ها.
    """
    days = get_date_range_days(start_date, end_date)
    return days / 7.0


def get_date_range_months(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> int:
    """
    محاسبه تعداد ماه‌های بین دو تاریخ.

    Args:
        start_date: تاریخ شروع.
        end_date: تاریخ پایان.

    Returns:
        int: تعداد ماه‌ها.
    """
    if isinstance(start_date, datetime):
        start = start_date.date()
    else:
        start = start_date

    if isinstance(end_date, datetime):
        end = end_date.date()
    else:
        end = end_date

    return (end.year - start.year) * 12 + (end.month - start.month)


def get_day_range(start_date: Union[datetime, date], end_date: Union[datetime, date]) -> List[date]:
    """
    دریافت لیست تمام روزهای بین دو تاریخ.

    Args:
        start_date: تاریخ شروع.
        end_date: تاریخ پایان.

    Returns:
        List[date]: لیست روزها.
    """
    if isinstance(start_date, datetime):
        start = start_date.date()
    else:
        start = start_date

    if isinstance(end_date, datetime):
        end = end_date.date()
    else:
        end = end_date

    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)

    return days


# ==========================================
# اعتبارسنجی
# ==========================================

def is_valid_datetime(date_str: str, format_str: Optional[str] = None) -> bool:
    """
    بررسی معتبر بودن یک رشته datetime.

    Args:
        date_str: رشته تاریخ و زمان.
        format_str: فرمت رشته (اختیاری).

    Returns:
        bool: True اگر معتبر باشد.
    """
    try:
        parse_datetime(date_str, format_str)
        return True
    except ValidationError:
        return False


def is_valid_date(date_str: str) -> bool:
    """
    بررسی معتبر بودن یک رشته تاریخ.

    Args:
        date_str: رشته تاریخ.

    Returns:
        bool: True اگر معتبر باشد.
    """
    return is_valid_datetime(date_str, DATE_FORMAT)


def is_valid_time(time_str: str) -> bool:
    """
    بررسی معتبر بودن یک رشته زمان.

    Args:
        time_str: رشته زمان.

    Returns:
        bool: True اگر معتبر باشد.
    """
    try:
        datetime.strptime(time_str, TIME_FORMAT)
        return True
    except ValueError:
        return False


# ==========================================
# تبدیل به مناطق زمانی مختلف
# ==========================================

def convert_timezone(dt: datetime, target_timezone: str) -> datetime:
    """
    تبدیل datetime به منطقه زمانی دیگر.

    Args:
        dt: شیء datetime.
        target_timezone: منطقه زمانی مقصد.

    Returns:
        datetime: datetime با منطقه زمانی جدید.

    Raises:
        ValidationError: اگر منطقه زمانی نامعتبر باشد.
    """
    if dt is None:
        raise ValidationError(
            message="datetime نمی‌تواند None باشد.",
            context={"dt": dt},
        )

    tz = get_timezone(target_timezone)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.astimezone(tz)
    return dt


def to_utc(dt: datetime) -> datetime:
    """
    تبدیل datetime به UTC.

    Args:
        dt: شیء datetime.

    Returns:
        datetime: datetime در UTC.
    """
    return convert_timezone(dt, "UTC")


def to_local(dt: datetime, timezone_str: Optional[str] = None) -> datetime:
    """
    تبدیل datetime به منطقه زمانی محلی.

    Args:
        dt: شیء datetime.
        timezone_str: منطقه زمانی محلی (اختیاری، پیش‌فرض: DEFAULT_TIMEZONE).

    Returns:
        datetime: datetime در منطقه زمانی محلی.
    """
    tz_str = timezone_str or DEFAULT_TIMEZONE
    return convert_timezone(dt, tz_str)


# ==========================================
# تفریق و جمع تاریخ
# ==========================================

def add_days(dt: datetime, days: int) -> datetime:
    """
    افزودن تعداد روز به datetime.

    Args:
        dt: شیء datetime.
        days: تعداد روز برای افزودن (می‌تواند منفی باشد).

    Returns:
        datetime: datetime جدید.
    """
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    افزودن تعداد ساعت به datetime.

    Args:
        dt: شیء datetime.
        hours: تعداد ساعت برای افزودن (می‌تواند منفی باشد).

    Returns:
        datetime: datetime جدید.
    """
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    افزودن تعداد دقیقه به datetime.

    Args:
        dt: شیء datetime.
        minutes: تعداد دقیقه برای افزودن (می‌تواند منفی باشد).

    Returns:
        datetime: datetime جدید.
    """
    return dt + timedelta(minutes=minutes)


def start_of_day(dt: datetime) -> datetime:
    """
    دریافت ابتدای روز (۰۰:۰۰:۰۰).

    Args:
        dt: شیء datetime.

    Returns:
        datetime: ابتدای روز.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """
    دریافت انتهای روز (۲۳:۵۹:۵۹.۹۹۹۹۹۹).

    Args:
        dt: شیء datetime.

    Returns:
        datetime: انتهای روز.
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_week(dt: datetime) -> datetime:
    """
    دریافت ابتدای هفته (دوشنبه).

    Args:
        dt: شیء datetime.

    Returns:
        datetime: ابتدای هفته.
    """
    days_to_subtract = dt.weekday()  # 0 = Monday, 6 = Sunday
    return start_of_day(dt - timedelta(days=days_to_subtract))


def end_of_week(dt: datetime) -> datetime:
    """
    دریافت انتهای هفته (یکشنبه).

    Args:
        dt: شیء datetime.

    Returns:
        datetime: انتهای هفته.
    """
    days_to_add = 6 - dt.weekday()
    return end_of_day(dt + timedelta(days=days_to_add))


def start_of_month(dt: datetime) -> datetime:
    """
    دریافت ابتدای ماه.

    Args:
        dt: شیء datetime.

    Returns:
        datetime: ابتدای ماه.
    """
    return start_of_day(dt.replace(day=1))


def end_of_month(dt: datetime) -> datetime:
    """
    دریافت انتهای ماه.

    Args:
        dt: شیء datetime.

    Returns:
        datetime: انتهای ماه.
    """
    # محاسبه روز اول ماه بعد
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)

    return end_of_day(next_month - timedelta(days=1))