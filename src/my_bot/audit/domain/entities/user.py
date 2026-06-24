# my_bot_project/src/my_bot/domain/entities/user.py
"""
موجودیت کاربر (User Entity).

این کلاس نمایانگر یک کاربر در سیستم است و شامل اطلاعات پایه، نقش، سطح، امتیاز و
سایر ویژگی‌های مربوط به کاربر می‌باشد. همچنین متدهای کمکی برای بررسی دسترسی،
ارتقاء سطح و مدیریت امتیاز در این موجودیت قرار دارند.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from my_bot.core.constants.user_roles import UserRole
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.email import Email
from my_bot.domain.value_objects.phone import Phone
from my_bot.domain.value_objects.user_level import UserLevel

logger = get_logger(__name__)


@dataclass
class User:
    """
    موجودیت کاربر در سیستم.

    Attributes:
        id: شناسه یکتای کاربر در دیتابیس (در صورت ذخیره‌شده).
        telegram_id: شناسه تلگرام کاربر (unique).
        username: نام کاربری تلگرام (اختیاری).
        first_name: نام کوچک.
        last_name: نام خانوادگی (اختیاری).
        phone_number: شماره تماس (اختیاری، با اعتبارسنجی).
        email: آدرس ایمیل (اختیاری، با اعتبارسنجی).
        role: نقش کاربری (پیش‌فرض: USER).
        level: سطح کاربری (پیش‌فرض: BRONZE).
        points: امتیاز کاربر (پیش‌فرض: ۰).
        is_active: وضعیت فعال بودن حساب (پیش‌فرض: True).
        is_banned: وضعیت مسدود بودن (پیش‌فرض: False).
        last_activity: زمان آخرین فعالیت (اختیاری).
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی (اختیاری).
    """

    id: Optional[int] = None
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    role: UserRole = UserRole.USER
    level: UserLevel = UserLevel.BRONZE
    points: int = 0
    is_active: bool = True
    is_banned: bool = False
    last_activity: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        self._validate_email()
        self._validate_phone()
        self._validate_points()

    def _validate_email(self) -> None:
        """اعتبارسنجی آدرس ایمیل (در صورت وجود)."""
        if self.email:
            try:
                Email(self.email)
            except ValidationError as e:
                logger.warning(f"Invalid email for user {self.telegram_id}: {e}")
                raise

    def _validate_phone(self) -> None:
        """اعتبارسنجی شماره تماس (در صورت وجود)."""
        if self.phone_number:
            try:
                Phone(self.phone_number)
            except ValidationError as e:
                logger.warning(f"Invalid phone for user {self.telegram_id}: {e}")
                raise

    def _validate_points(self) -> None:
        """اعتبارسنجی امتیاز (نباید منفی باشد)."""
        if self.points < 0:
            raise ValidationError(
                message="امتیاز کاربر نمی‌تواند منفی باشد.",
                context={"telegram_id": self.telegram_id, "points": self.points},
            )

    @property
    def full_name(self) -> str:
        """دریافت نام کامل کاربر."""
        if self.first_name:
            if self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.first_name
        return self.username or f"User_{self.telegram_id}"

    @property
    def display_name(self) -> str:
        """دریافت نام نمایشی کاربر (برای استفاده در UI)."""
        name = self.full_name
        if self.username:
            return f"{name} (@{self.username})"
        return name

    def add_points(self, amount: int) -> None:
        """
        افزایش امتیاز کاربر.

        Args:
            amount: مقدار امتیاز برای افزایش (باید مثبت باشد).

        Raises:
            ValidationError: اگر مقدار منفی باشد.
        """
        if amount <= 0:
            raise ValidationError(
                message="مقدار امتیاز برای افزایش باید مثبت باشد.",
                context={"telegram_id": self.telegram_id, "amount": amount},
            )
        self.points += amount
        self._update_level()
        self.updated_at = datetime.now()
        logger.debug(f"User {self.telegram_id} gained {amount} points. Total: {self.points}")

    def deduct_points(self, amount: int) -> bool:
        """
        کاهش امتیاز کاربر (در صورت کافی بودن).

        Args:
            amount: مقدار امتیاز برای کاهش.

        Returns:
            True اگر امتیاز کافی بود و کاهش انجام شد، در غیر این صورت False.
        """
        if amount <= 0:
            raise ValidationError(
                message="مقدار امتیاز برای کاهش باید مثبت باشد.",
                context={"telegram_id": self.telegram_id, "amount": amount},
            )
        if self.points < amount:
            logger.warning(f"User {self.telegram_id} has insufficient points: {self.points} < {amount}")
            return False

        self.points -= amount
        self._update_level()
        self.updated_at = datetime.now()
        logger.debug(f"User {self.telegram_id} spent {amount} points. Remaining: {self.points}")
        return True

    def _update_level(self) -> None:
        """به‌روزرسانی سطح کاربر بر اساس امتیاز."""
        new_level = UserLevel.from_points(self.points)
        if new_level != self.level:
            old_level = self.level
            self.level = new_level
            logger.info(f"User {self.telegram_id} upgraded from {old_level.display_name} to {self.level.display_name}")

    def has_permission(self, required_role: UserRole) -> bool:
        """
        بررسی اینکه آیا کاربر دارای سطح دسترسی کافی است.

        Args:
            required_role: نقش مورد نیاز.

        Returns:
            True اگر کاربر نقش مورد نیاز یا بالاتر را داشته باشد.
        """
        return self.role.get_permission_level() >= required_role.get_permission_level()

    def can_manage_users(self) -> bool:
        """بررسی اینکه آیا کاربر مجاز به مدیریت کاربران است."""
        return self.role.can_manage_users()

    def can_manage_orders(self) -> bool:
        """بررسی اینکه آیا کاربر مجاز به مدیریت سفارشات است."""
        return self.role.can_manage_orders()

    def can_send_broadcast(self) -> bool:
        """بررسی اینکه آیا کاربر مجاز به ارسال پیام گروهی است."""
        return self.role.can_send_broadcast()

    def can_manage_settings(self) -> bool:
        """بررسی اینکه آیا کاربر مجاز به مدیریت تنظیمات است."""
        return self.role.can_manage_settings()

    def is_admin(self) -> bool:
        """بررسی اینکه آیا کاربر ادمین است."""
        return self.role == UserRole.ADMIN

    def is_manager(self) -> bool:
        """بررسی اینکه آیا کاربر مدیر ارشد است."""
        return self.role == UserRole.MANAGER

    def is_operator(self) -> bool:
        """بررسی اینکه آیا کاربر اپراتور است."""
        return self.role == UserRole.OPERATOR

    def is_regular_user(self) -> bool:
        """بررسی اینکه آیا کاربر عادی است."""
        return self.role == UserRole.USER

    def is_guest(self) -> bool:
        """بررسی اینکه آیا کاربر مهمان است."""
        return self.role == UserRole.GUEST

    def ban(self) -> None:
        """مسدود کردن کاربر."""
        if not self.is_banned:
            self.is_banned = True
            self.is_active = False
            self.updated_at = datetime.now()
            logger.info(f"User {self.telegram_id} has been banned.")

    def unban(self) -> None:
        """رفع مسدودیت کاربر."""
        if self.is_banned:
            self.is_banned = False
            self.is_active = True
            self.updated_at = datetime.now()
            logger.info(f"User {self.telegram_id} has been unbanned.")

    def deactivate(self) -> None:
        """غیرفعال کردن حساب کاربری."""
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.now()
            logger.info(f"User {self.telegram_id} account deactivated.")

    def activate(self) -> None:
        """فعال کردن حساب کاربری."""
        if not self.is_active and not self.is_banned:
            self.is_active = True
            self.updated_at = datetime.now()
            logger.info(f"User {self.telegram_id} account activated.")

    def update_activity(self) -> None:
        """به‌روزرسانی زمان آخرین فعالیت."""
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل موجودیت کاربر به دیکشنری (برای ذخیره‌سازی یا سریال‌سازی).

        Returns:
            دیکشنری شامل اطلاعات کاربر.
        """
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "email": self.email,
            "role": self.role.value,
            "level": self.level.value,
            "points": self.points,
            "is_active": self.is_active,
            "is_banned": self.is_banned,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        ساخت موجودیت کاربر از دیکشنری (برای دیسریال‌سازی).

        Args:
            data: دیکشنری شامل اطلاعات کاربر.

        Returns:
            نمونه‌ای از کلاس User.
        """
        # تبدیل نقش و سطح از رشته به Enum
        role = UserRole.from_string(data.get("role", "user"))
        if not role:
            role = UserRole.USER

        level = UserLevel.from_string(data.get("level", "bronze"))
        if not level:
            level = UserLevel.BRONZE

        # تبدیل تاریخ‌ها
        last_activity = None
        if data.get("last_activity"):
            try:
                last_activity = datetime.fromisoformat(data["last_activity"])
            except (ValueError, TypeError):
                pass

        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()

        updated_at = None
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                updated_at = datetime.now()

        return cls(
            id=data.get("id"),
            telegram_id=data.get("telegram_id"),
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            phone_number=data.get("phone_number"),
            email=data.get("email"),
            role=role,
            level=level,
            points=data.get("points", 0),
            is_active=data.get("is_active", True),
            is_banned=data.get("is_banned", False),
            last_activity=last_activity,
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )