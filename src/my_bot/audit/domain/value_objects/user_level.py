# my_bot_project/src/my_bot/domain/value_objects/user_level.py
"""
ارزش‌مقدار سطح کاربری (User Level Value Object).

این کلاس نمایانگر سطح کاربری در سیستم است که بر اساس امتیاز کاربر
تعیین می‌شود. سطوح مختلف شامل برنز، نقره، طلا، پلاتین و الماس هستند
که هر کدام امتیاز حداقل و حداکثر خاص خود را دارند.
سطح کاربری به‌صورت غیرقابل تغییر (Immutable) ذخیره می‌شود.
"""

from enum import Enum
from typing import Optional


class UserLevel(str, Enum):
    """
    سطوح مختلف کاربری در سیستم.

    هر سطح دارای محدوده امتیاز مخصوص به خود است و کاربران با
    کسب امتیاز بیشتر به سطوح بالاتر ارتقا می‌یابند.

    سطوح:
        BRONZE: برنز (پایه) - ۰ تا ۹۹ امتیاز
        SILVER: نقره - ۱۰۰ تا ۴۹۹ امتیاز
        GOLD: طلا - ۵۰۰ تا ۹۹۹ امتیاز
        PLATINUM: پلاتین - ۱۰۰۰ تا ۴۹۹۹ امتیاز
        DIAMOND: الماس - ۵۰۰۰ امتیاز به بالا
    """

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

    @classmethod
    def from_points(cls, points: int) -> "UserLevel":
        """
        دریافت سطح کاربری بر اساس امتیاز.

        Args:
            points: امتیاز کاربر.

        Returns:
            سطح کاربری متناسب با امتیاز.
        """
        if points >= 5000:
            return cls.DIAMOND
        elif points >= 1000:
            return cls.PLATINUM
        elif points >= 500:
            return cls.GOLD
        elif points >= 100:
            return cls.SILVER
        else:
            return cls.BRONZE

    @classmethod
    def from_string(cls, value: str) -> Optional["UserLevel"]:
        """
        تبدیل یک رشته به سطح کاربری.

        Args:
            value: رشته‌ای که نمایانگر سطح کاربری است.

        Returns:
            سطح کاربری متناظر با رشته داده شده، یا None در صورت عدم تطابق.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    @property
    def display_name(self) -> str:
        """
        دریافت نام نمایشی سطح کاربری (به فارسی).

        Returns:
            نام نمایشی سطح کاربری.
        """
        display_names = {
            UserLevel.BRONZE: "برنز",
            UserLevel.SILVER: "نقره",
            UserLevel.GOLD: "طلا",
            UserLevel.PLATINUM: "پلاتین",
            UserLevel.DIAMOND: "الماس",
        }
        return display_names.get(self, self.value)

    @property
    def emoji(self) -> str:
        """
        دریافت ایموجی متناسب با سطح کاربری.

        Returns:
            ایموجی نمایشی برای سطح کاربری.
        """
        emojis = {
            UserLevel.BRONZE: "🥉",
            UserLevel.SILVER: "🥈",
            UserLevel.GOLD: "🥇",
            UserLevel.PLATINUM: "💎",
            UserLevel.DIAMOND: "👑",
        }
        return emojis.get(self, "⭐")

    @property
    def color_code(self) -> str:
        """
        دریافت کد رنگ مناسب برای نمایش سطح کاربری.

        Returns:
            کد رنگ هگزادسیمال.
        """
        colors = {
            UserLevel.BRONZE: "#CD7F32",  # برنز
            UserLevel.SILVER: "#C0C0C0",  # نقره
            UserLevel.GOLD: "#FFD700",    # طلا
            UserLevel.PLATINUM: "#E5E4E2", # پلاتین
            UserLevel.DIAMOND: "#B9F2FF", # الماس
        }
        return colors.get(self, "#808080")

    @property
    def min_points(self) -> int:
        """
        دریافت حداقل امتیاز مورد نیاز برای این سطح.

        Returns:
            حداقل امتیاز برای این سطح.
        """
        min_points_map = {
            UserLevel.BRONZE: 0,
            UserLevel.SILVER: 100,
            UserLevel.GOLD: 500,
            UserLevel.PLATINUM: 1000,
            UserLevel.DIAMOND: 5000,
        }
        return min_points_map.get(self, 0)

    @property
    def max_points(self) -> Optional[int]:
        """
        دریافت حداکثر امتیاز برای این سطح.

        Returns:
            حداکثر امتیاز برای این سطح، یا None برای آخرین سطح.
        """
        max_points_map = {
            UserLevel.BRONZE: 99,
            UserLevel.SILVER: 499,
            UserLevel.GOLD: 999,
            UserLevel.PLATINUM: 4999,
            UserLevel.DIAMOND: None,  # نامحدود
        }
        return max_points_map.get(self)

    @property
    def next_level(self) -> Optional["UserLevel"]:
        """
        دریافت سطح بعدی.

        Returns:
            سطح بعدی یا None در صورت آخرین سطح بودن.
        """
        levels = [UserLevel.BRONZE, UserLevel.SILVER, UserLevel.GOLD,
                  UserLevel.PLATINUM, UserLevel.DIAMOND]
        try:
            current_index = levels.index(self)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
            return None
        except ValueError:
            return None

    @property
    def previous_level(self) -> Optional["UserLevel"]:
        """
        دریافت سطح قبلی.

        Returns:
            سطح قبلی یا None در صورت اولین سطح بودن.
        """
        levels = [UserLevel.BRONZE, UserLevel.SILVER, UserLevel.GOLD,
                  UserLevel.PLATINUM, UserLevel.DIAMOND]
        try:
            current_index = levels.index(self)
            if current_index > 0:
                return levels[current_index - 1]
            return None
        except ValueError:
            return None

    def points_to_next_level(self, current_points: int) -> Optional[int]:
        """
        دریافت امتیاز مورد نیاز برای رسیدن به سطح بعدی.

        Args:
            current_points: امتیاز فعلی کاربر.

        Returns:
            تعداد امتیاز مورد نیاز برای ارتقا به سطح بعدی،
            یا None اگر در بالاترین سطح باشد.
        """
        next_lvl = self.next_level
        if next_lvl is None:
            return None
        required = next_lvl.min_points
        return max(0, required - current_points)

    def get_progress(self, current_points: int) -> float:
        """
        دریافت درصد پیشرفت به سمت سطح بعدی.

        Args:
            current_points: امتیاز فعلی کاربر.

        Returns:
            درصد پیشرفت (۰ تا ۱۰۰).
        """
        min_pts = self.min_points
        max_pts = self.max_points

        # اگر در آخرین سطح هستیم، پیشرفت کامل است
        if max_pts is None:
            return 100.0

        if current_points <= min_pts:
            return 0.0

        if current_points >= max_pts:
            return 100.0

        total_range = max_pts - min_pts
        current_progress = current_points - min_pts
        return (current_progress / total_range) * 100

    def is_higher_than(self, other: "UserLevel") -> bool:
        """
        بررسی اینکه آیا این سطح بالاتر از سطح دیگر است.

        Args:
            other: سطح دیگر برای مقایسه.

        Returns:
            True اگر این سطح بالاتر باشد.
        """
        return self.min_points > other.min_points

    def is_lower_than(self, other: "UserLevel") -> bool:
        """
        بررسی اینکه آیا این سطح پایین‌تر از سطح دیگر است.

        Args:
            other: سطح دیگر برای مقایسه.

        Returns:
            True اگر این سطح پایین‌تر باشد.
        """
        return self.min_points < other.min_points

    def is_higher_or_equal(self, other: "UserLevel") -> bool:
        """
        بررسی اینکه آیا این سطح بالاتر یا مساوی سطح دیگر است.

        Args:
            other: سطح دیگر برای مقایسه.

        Returns:
            True اگر این سطح بالاتر یا مساوی باشد.
        """
        return self.min_points >= other.min_points

    def __str__(self) -> str:
        """نمایش رشته‌ای سطح کاربری."""
        return f"{self.emoji} {self.display_name}"

    def __repr__(self) -> str:
        """نمایش رسمی برای دیباگ."""
        return f"UserLevel.{self.name}"


# ----------------------------------------------
# توابع کمکی
# ----------------------------------------------

def get_level_from_points(points: int) -> UserLevel:
    """
    دریافت سطح کاربری بر اساس امتیاز (تابع کمکی).

    Args:
        points: امتیاز کاربر.

    Returns:
        سطح کاربری.
    """
    return UserLevel.from_points(points)


def get_level_display_name(level: UserLevel) -> str:
    """
    دریافت نام نمایشی سطح کاربری.

    Args:
        level: سطح کاربری.

    Returns:
        نام نمایشی.
    """
    return level.display_name


def get_level_emoji(level: UserLevel) -> str:
    """
    دریافت ایموجی سطح کاربری.

    Args:
        level: سطح کاربری.

    Returns:
        ایموجی متناسب با سطح.
    """
    return level.emoji


__all__ = [
    "UserLevel",
    "get_level_from_points",
    "get_level_display_name",
    "get_level_emoji",
]