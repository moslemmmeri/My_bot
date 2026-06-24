# my_bot_project/src/admin_panel/modules/user_management/services/user_edit_service.py
"""
سرویس ویرایش کاربر (User Edit Service).

این سرویس مسئولیت اعتبارسنجی و ذخیره‌سازی تغییرات اطلاعات کاربران
در پنل مدیریت را بر عهده دارد.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.constants.user_roles import UserRole
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.value_objects.email import Email
from my_bot.domain.value_objects.phone import Phone
from my_bot.domain.value_objects.user_level import UserLevel
from my_bot.shared.utils.text_validators import validate_email, validate_phone

logger = get_logger(__name__)


class UserEditService:
    """
    سرویس ویرایش کاربر.

    این کلاس با استفاده از UserRepository، عملیات ویرایش اطلاعات کاربران
    را با اعتبارسنجی کامل انجام می‌دهد.

    Attributes:
        user_repository: ریپازیتوری کاربر.
    """

    # فیلدهای قابل ویرایش با نوع‌های مجاز
    EDITABLE_FIELDS = {
        "first_name": str,
        "last_name": str,
        "username": str,
        "phone_number": str,
        "email": str,
        "role": str,
        "level": str,
        "points": int,
        "is_active": bool,
        "is_banned": bool,
    }

    def __init__(self, user_repository: UserRepository) -> None:
        """
        مقداردهی اولیه سرویس.

        Args:
            user_repository: ریپازیتوری کاربر.
        """
        self._user_repository = user_repository
        logger.info("UserEditService initialized.")

    async def update_user(
        self,
        user_id: int,
        updates: Dict[str, Any],
        validate_only: bool = False,
    ) -> Tuple[bool, List[str], Optional[User]]:
        """
        به‌روزرسانی اطلاعات کاربر.

        Args:
            user_id: شناسه کاربر.
            updates: دیکشنری تغییرات (نام فیلد -> مقدار جدید).
            validate_only: فقط اعتبارسنجی انجام شود (بدون ذخیره).

        Returns:
            Tuple شامل:
                - success: آیا عملیات موفق بوده
                - errors: لیست خطاها
                - user: کاربر به‌روزرسانی‌شده (در صورت موفقیت و validate_only=False)

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            DatabaseError: در صورت بروز خطا در ذخیره‌سازی.
        """
        if not updates:
            return False, ["هیچ تغییری برای اعمال وجود ندارد."], None

        # دریافت کاربر
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            return False, [f"کاربر با شناسه {user_id} یافت نشد."], None

        # اعتبارسنجی و آماده‌سازی تغییرات
        validated_updates, errors = await self._validate_updates(user, updates)

        if errors:
            return False, errors, None

        if not validated_updates:
            return False, ["هیچ تغییری برای اعمال وجود ندارد."], None

        # اگر فقط اعتبارسنجی است، برگردان
        if validate_only:
            return True, [], user

        # اعمال تغییرات
        try:
            for field, value in validated_updates.items():
                setattr(user, field, value)

            # به‌روزرسانی زمان
            user.updated_at = datetime.now()

            # ذخیره در دیتابیس
            updated_user = await self._user_repository.save(user)
            logger.info(f"User {user_id} updated with fields: {list(validated_updates.keys())}")

            return True, [], updated_user

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise DatabaseError(
                message=f"خطا در ذخیره‌سازی تغییرات کاربر: {str(e)}",
                context={"user_id": user_id, "updates": validated_updates},
            )

    async def _validate_updates(
        self,
        user: User,
        updates: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        اعتبارسنجی و آماده‌سازی تغییرات.

        Args:
            user: کاربر جاری.
            updates: تغییرات پیشنهادی.

        Returns:
            Tuple شامل:
                - validated_updates: تغییرات اعتبارسنجی‌شده
                - errors: لیست خطاها
        """
        validated_updates = {}
        errors = []

        for field, value in updates.items():
            # بررسی وجود فیلد
            if field not in self.EDITABLE_FIELDS:
                errors.append(f"فیلد '{field}' قابل ویرایش نیست.")
                continue

            # بررسی نوع داده
            expected_type = self.EDITABLE_FIELDS[field]
            if not isinstance(value, expected_type):
                # تلاش برای تبدیل
                try:
                    if expected_type == bool:
                        if isinstance(value, str):
                            value = value.lower() in ("true", "بله", "1", "yes", "فعال")
                        elif isinstance(value, int):
                            value = bool(value)
                        else:
                            raise ValueError()
                    elif expected_type == int:
                        value = int(value)
                    elif expected_type == str:
                        value = str(value)
                except (ValueError, TypeError):
                    errors.append(f"نوع داده فیلد '{field}' نامعتبر است. نوع مورد انتظار: {expected_type.__name__}")
                    continue

            # اعتبارسنجی اختصاصی هر فیلد
            validation_error = await self._validate_field(field, value, user)
            if validation_error:
                errors.append(validation_error)
                continue

            # اگر مقدار با مقدار فعلی یکسان است، نادیده بگیر
            current_value = getattr(user, field, None)
            if current_value == value:
                continue

            validated_updates[field] = value

        return validated_updates, errors

    async def _validate_field(self, field: str, value: Any, user: User) -> Optional[str]:
        """
        اعتبارسنجی یک فیلد خاص.

        Args:
            field: نام فیلد.
            value: مقدار جدید.
            user: کاربر جاری (برای بررسی‌های وابسته).

        Returns:
            Optional[str]: پیام خطا یا None در صورت معتبر بودن.
        """
        if field == "username":
            if value is None:
                return None
            value_str = str(value).strip()
            if not value_str:
                return "نام کاربری نمی‌تواند خالی باشد."
            if len(value_str) < 3:
                return "نام کاربری باید حداقل ۳ کاراکتر باشد."
            if len(value_str) > 32:
                return "نام کاربری نباید بیشتر از ۳۲ کاراکتر باشد."
            if not value_str.isalnum():
                return "نام کاربری فقط می‌تواند شامل حروف و اعداد باشد."
            # بررسی یکتایی (در صورت تغییر)
            if value_str != user.username:
                exists = await self._user_repository.exists_by_username(value_str)
                if exists:
                    return f"نام کاربری '{value_str}' قبلاً توسط کاربر دیگری استفاده شده است."

        elif field == "phone_number":
            if value is None:
                return None
            value_str = str(value).strip()
            if value_str:
                try:
                    validate_phone(value_str)
                    # بررسی یکتایی
                    if value_str != user.phone_number:
                        exists = await self._user_repository.exists_by_phone(value_str)
                        if exists:
                            return f"شماره تلفن '{value_str}' قبلاً توسط کاربر دیگری استفاده شده است."
                except ValidationError as e:
                    return str(e)

        elif field == "email":
            if value is None:
                return None
            value_str = str(value).strip()
            if value_str:
                try:
                    validate_email(value_str)
                    # بررسی یکتایی
                    if value_str != user.email:
                        exists = await self._user_repository.exists_by_email(value_str)
                        if exists:
                            return f"ایمیل '{value_str}' قبلاً توسط کاربر دیگری استفاده شده است."
                except ValidationError as e:
                    return str(e)

        elif field == "role":
            if value is None:
                return None
            value_str = str(value).lower()
            try:
                UserRole(value_str)
            except ValueError:
                valid_roles = [r.value for r in UserRole]
                return f"نقش '{value}' نامعتبر است. نقش‌های مجاز: {', '.join(valid_roles)}"

        elif field == "level":
            if value is None:
                return None
            value_str = str(value).lower()
            try:
                UserLevel(value_str)
            except ValueError:
                valid_levels = [l.value for l in UserLevel]
                return f"سطح '{value}' نامعتبر است. سطوح مجاز: {', '.join(valid_levels)}"

        elif field == "points":
            try:
                points = int(value)
                if points < 0:
                    return "امتیاز نمی‌تواند منفی باشد."
            except (ValueError, TypeError):
                return "امتیاز باید یک عدد صحیح باشد."

        elif field == "first_name":
            if value is not None:
                value_str = str(value).strip()
                if len(value_str) > 64:
                    return "نام نباید بیشتر از ۶۴ کاراکتر باشد."

        elif field == "last_name":
            if value is not None:
                value_str = str(value).strip()
                if len(value_str) > 64:
                    return "نام خانوادگی نباید بیشتر از ۶۴ کاراکتر باشد."

        return None

    async def update_single_field(
        self,
        user_id: int,
        field: str,
        value: Any,
    ) -> Tuple[bool, List[str], Optional[User]]:
        """
        به‌روزرسانی یک فیلد خاص از کاربر.

        Args:
            user_id: شناسه کاربر.
            field: نام فیلد.
            value: مقدار جدید.

        Returns:
            Tuple شامل موفقیت، خطاها و کاربر به‌روزرسانی‌شده.
        """
        return await self.update_user(user_id, {field: value})

    def get_editable_fields(self) -> Dict[str, str]:
        """
        دریافت لیست فیلدهای قابل ویرایش با نام نمایشی.

        Returns:
            Dict[str, str]: دیکشنری نگاشت نام فیلد به نام نمایشی.
        """
        display_names = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "username": "نام کاربری",
            "phone_number": "شماره تلفن",
            "email": "ایمیل",
            "role": "نقش",
            "level": "سطح",
            "points": "امتیاز",
            "is_active": "وضعیت فعال بودن",
            "is_banned": "وضعیت مسدود بودن",
        }
        return {k: display_names.get(k, k) for k in self.EDITABLE_FIELDS.keys()}