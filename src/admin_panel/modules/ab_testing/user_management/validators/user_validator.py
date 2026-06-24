# my_bot_project/src/admin_panel/modules/user_management/validators/user_validator.py
"""
اعتبارسنجی اطلاعات کاربر (User Validator).

این ماژول شامل کلاس `UserValidator` است که مسئولیت اعتبارسنجی
داده‌های مربوط به کاربران را در پنل مدیریت بر عهده دارد.
"""

from typing import Optional, Dict, Any, List, Tuple

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.constants.user_roles import UserRole
from my_bot.domain.value_objects.user_level import UserLevel
from my_bot.shared.utils.text_validators import (
    validate_email,
    validate_phone,
    validate_length,
)

logger = get_logger(__name__)


class UserValidator:
    """
    اعتبارسنجی اطلاعات کاربران.

    این کلاس با استفاده از متدهای مختلف، داده‌های کاربران را
    اعتبارسنجی کرده و خطاها را بازمی‌گرداند.

    Attributes:
        strict_mode: حالت سخت‌گیرانه (پیش‌فرض True).
        max_name_length: حداکثر طول نام (پیش‌فرض ۶۴).
        max_username_length: حداکثر طول نام کاربری (پیش‌فرض ۳۲).
        min_username_length: حداقل طول نام کاربری (پیش‌فرض ۳).
    """

    def __init__(
        self,
        strict_mode: bool = True,
        max_name_length: int = 64,
        max_username_length: int = 32,
        min_username_length: int = 3,
    ) -> None:
        """
        مقداردهی اولیه UserValidator.

        Args:
            strict_mode: حالت سخت‌گیرانه (پیش‌فرض True).
            max_name_length: حداکثر طول نام (پیش‌فرض ۶۴).
            max_username_length: حداکثر طول نام کاربری (پیش‌فرض ۳۲).
            min_username_length: حداقل طول نام کاربری (پیش‌فرض ۳).
        """
        self.strict_mode = strict_mode
        self.max_name_length = max_name_length
        self.max_username_length = max_username_length
        self.min_username_length = min_username_length

        logger.info(
            f"UserValidator initialized: strict_mode={strict_mode}, "
            f"max_name_length={max_name_length}"
        )

    def validate_user_data(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        اعتبارسنجی کامل داده‌های یک کاربر.

        Args:
            data: دیکشنری داده‌های کاربر.

        Returns:
            List[Dict[str, str]]: لیست خطاها (هر خطا شامل field و message).

        Raises:
            ValidationError: در صورت بروز خطاهای حیاتی.
        """
        errors = []

        # اعتبارسنجی فیلدهای مختلف
        field_validators = {
            "telegram_id": self.validate_telegram_id,
            "first_name": self.validate_name,
            "last_name": self.validate_name,
            "username": self.validate_username,
            "phone_number": self.validate_phone,
            "email": self.validate_email,
            "role": self.validate_role,
            "level": self.validate_level,
            "points": self.validate_points,
            "is_active": self.validate_boolean,
            "is_banned": self.validate_boolean,
        }

        for field, value in data.items():
            if field in field_validators:
                try:
                    error = field_validators[field](value)
                    if error:
                        errors.append({"field": field, "message": error})
                except ValidationError as e:
                    errors.append({"field": field, "message": str(e)})

        return errors

    def validate_user(self, user) -> List[Dict[str, str]]:
        """
        اعتبارسنجی یک موجودیت کاربر.

        Args:
            user: موجودیت User.

        Returns:
            List[Dict[str, str]]: لیست خطاها.
        """
        data = {
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "phone_number": user.phone_number,
            "email": user.email,
            "role": user.role.value if user.role else None,
            "level": user.level.value if user.level else None,
            "points": user.points,
            "is_active": user.is_active,
            "is_banned": user.is_banned,
        }
        return self.validate_user_data(data)

    def validate_telegram_id(self, telegram_id: Any) -> Optional[str]:
        """
        اعتبارسنجی شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if telegram_id is None or telegram_id == "":
            return "شناسه تلگرام نمی‌تواند خالی باشد."

        try:
            telegram_id_int = int(telegram_id)
            if telegram_id_int <= 0:
                return "شناسه تلگرام باید یک عدد صحیح مثبت باشد."
        except (ValueError, TypeError):
            return "شناسه تلگرام باید یک عدد صحیح باشد."

        return None

    def validate_name(self, name: Any) -> Optional[str]:
        """
        اعتبارسنجی نام (نام یا نام خانوادگی).

        Args:
            name: نام.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if name is None or name == "":
            if self.strict_mode:
                return "نام نمی‌تواند خالی باشد."
            return None

        if not isinstance(name, str):
            return "نام باید متن باشد."

        name = name.strip()

        if len(name) < 1:
            return "نام نمی‌تواند خالی باشد."

        if len(name) > self.max_name_length:
            return f"نام نباید بیشتر از {self.max_name_length} کاراکتر باشد."

        # بررسی کاراکترهای مجاز (فقط حروف، فاصله، نقطه و خط تیره)
        if not all(c.isalpha() or c.isspace() or c in ".-" for c in name):
            return "نام فقط می‌تواند شامل حروف، فاصله، نقطه و خط تیره باشد."

        return None

    def validate_username(self, username: Any) -> Optional[str]:
        """
        اعتبارسنجی نام کاربری.

        Args:
            username: نام کاربری.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if username is None or username == "":
            return None  # نام کاربری اختیاری است

        if not isinstance(username, str):
            return "نام کاربری باید متن باشد."

        username = username.strip()

        if len(username) < self.min_username_length:
            return f"نام کاربری باید حداقل {self.min_username_length} کاراکتر باشد."

        if len(username) > self.max_username_length:
            return f"نام کاربری نباید بیشتر از {self.max_username_length} کاراکتر باشد."

        # بررسی کاراکترهای مجاز (فقط حروف، اعداد و زیرخط)
        if not username.replace("_", "").isalnum():
            return "نام کاربری فقط می‌تواند شامل حروف، اعداد و زیرخط باشد."

        return None

    def validate_phone(self, phone: Any) -> Optional[str]:
        """
        اعتبارسنجی شماره تلفن.

        Args:
            phone: شماره تلفن.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if phone is None or phone == "":
            return None  # شماره تلفن اختیاری است

        try:
            validate_phone(str(phone))
            return None
        except ValidationError as e:
            return str(e)

    def validate_email(self, email: Any) -> Optional[str]:
        """
        اعتبارسنجی آدرس ایمیل.

        Args:
            email: آدرس ایمیل.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if email is None or email == "":
            return None  # ایمیل اختیاری است

        try:
            validate_email(str(email))
            return None
        except ValidationError as e:
            return str(e)

    def validate_role(self, role: Any) -> Optional[str]:
        """
        اعتبارسنجی نقش کاربری.

        Args:
            role: نقش کاربری.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if role is None or role == "":
            if self.strict_mode:
                return "نقش کاربری نمی‌تواند خالی باشد."
            return None

        try:
            if isinstance(role, str):
                UserRole.from_string(role)
            else:
                # اگر از نوع UserRole است
                if role.value:
                    return None
            return None
        except (ValueError, AttributeError):
            valid_roles = [r.value for r in UserRole]
            return f"نقش '{role}' نامعتبر است. نقش‌های مجاز: {', '.join(valid_roles)}"

    def validate_level(self, level: Any) -> Optional[str]:
        """
        اعتبارسنجی سطح کاربری.

        Args:
            level: سطح کاربری.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if level is None or level == "":
            if self.strict_mode:
                return "سطح کاربری نمی‌تواند خالی باشد."
            return None

        try:
            if isinstance(level, str):
                UserLevel.from_string(level)
            else:
                # اگر از نوع UserLevel است
                if level.value:
                    return None
            return None
        except (ValueError, AttributeError):
            valid_levels = [l.value for l in UserLevel]
            return f"سطح '{level}' نامعتبر است. سطوح مجاز: {', '.join(valid_levels)}"

    def validate_points(self, points: Any) -> Optional[str]:
        """
        اعتبارسنجی امتیاز کاربر.

        Args:
            points: امتیاز.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if points is None:
            if self.strict_mode:
                return "امتیاز نمی‌تواند خالی باشد."
            return None

        try:
            points_int = int(points)
            if points_int < 0:
                return "امتیاز نمی‌تواند منفی باشد."
        except (ValueError, TypeError):
            return "امتیاز باید یک عدد صحیح باشد."

        return None

    def validate_boolean(self, value: Any) -> Optional[str]:
        """
        اعتبارسنجی مقدار بولی.

        Args:
            value: مقدار بولی.

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, str):
            if value.lower() in ("true", "false", "1", "0", "yes", "no", "بله", "خیر", "فعال", "غیرفعال"):
                return None

        return "مقدار باید بولی باشد (True/False یا بله/خیر)."

    def validate_user_update(
        self,
        current_user,
        new_data: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        اعتبارسنجی به‌روزرسانی کاربر (مقایسه با داده‌های فعلی).

        Args:
            current_user: موجودیت کاربر فعلی.
            new_data: داده‌های جدید.

        Returns:
            List[Dict[str, str]]: لیست خطاها.
        """
        errors = []

        # اگر هیچ داده‌ای برای به‌روزرسانی وجود ندارد
        if not new_data:
            errors.append({"field": "general", "message": "هیچ داده‌ای برای به‌روزرسانی وجود ندارد."})
            return errors

        # اعتبارسنجی هر فیلد جدید
        for field, value in new_data.items():
            if field == "telegram_id":
                error = self.validate_telegram_id(value)
                if error:
                    errors.append({"field": field, "message": error})
                elif current_user.telegram_id != value:
                    # بررسی تکراری بودن شناسه تلگرام (در صورت امکان)
                    # اینجا باید از دیتابیس بررسی شود که در سرویس انجام می‌شود
                    pass

            elif field in ("first_name", "last_name"):
                error = self.validate_name(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field == "username":
                error = self.validate_username(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field == "phone_number":
                error = self.validate_phone(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field == "email":
                error = self.validate_email(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field == "role":
                error = self.validate_role(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field == "level":
                error = self.validate_level(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field == "points":
                error = self.validate_points(value)
                if error:
                    errors.append({"field": field, "message": error})

            elif field in ("is_active", "is_banned"):
                error = self.validate_boolean(value)
                if error:
                    errors.append({"field": field, "message": error})

        return errors

    def is_valid_user(self, data: Dict[str, Any]) -> bool:
        """
        بررسی کلی اعتبار داده‌های کاربر.

        Args:
            data: دیکشنری داده‌های کاربر.

        Returns:
            bool: True اگر داده‌ها معتبر باشند.
        """
        errors = self.validate_user_data(data)
        return len(errors) == 0

    def get_supported_fields(self) -> List[str]:
        """
        دریافت لیست فیلدهای قابل اعتبارسنجی.

        Returns:
            List[str]: لیست فیلدها.
        """
        return [
            "telegram_id",
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "email",
            "role",
            "level",
            "points",
            "is_active",
            "is_banned",
        ]