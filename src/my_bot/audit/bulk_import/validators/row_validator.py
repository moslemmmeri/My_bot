# my_bot_project/src/my_bot/bulk_import/validators/row_validator.py
"""
اعتبارسنجی ردیف‌های واردات انبوه (Row Validator).

این کلاس مسئولیت اعتبارسنجی هر ردیف از داده‌های وارداتی را بر عهده دارد.
اعتبارسنجی شامل بررسی فیلدهای اجباری، نوع داده‌ها، فرمت‌ها و مقادیر مجاز است.
"""

import json
import re
from typing import Optional, List, Dict, Any, Callable, Union
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.constants.user_roles import UserRole
from my_bot.core.constants.form_types import FormType
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.domain.value_objects.user_level import UserLevel
from my_bot.domain.value_objects.email import Email
from my_bot.domain.value_objects.phone import Phone
from my_bot.shared.utils.text_validators import (
    validate_email,
    validate_phone,
    validate_url,
    validate_date,
    validate_time,
    validate_color,
)

logger = get_logger(__name__)


class RowValidator:
    """
    اعتبارسنجی ردیف‌های داده در واردات انبوه.

    این کلاس با استفاده از قوانین تعریف‌شده، هر ردیف از داده‌ها را
    اعتبارسنجی کرده و خطاها را بازمی‌گرداند.

    Attributes:
        strict_mode: حالت سخت‌گیرانه (پیش‌فرض True).
        custom_validators: دیکشنری نگاشت نام فیلد به تابع اعتبارسنجی سفارشی.
    """

    def __init__(self, strict_mode: bool = True) -> None:
        """
        مقداردهی اولیه RowValidator.

        Args:
            strict_mode: حالت سخت‌گیرانه (پیش‌فرض True).
        """
        self.strict_mode = strict_mode
        self._custom_validators: Dict[str, Callable] = {}

        # ثبت اعتبارسنجی‌های پیش‌فرض
        self._register_default_validators()

        logger.info(f"RowValidator initialized: strict_mode={strict_mode}")

    def _register_default_validators(self) -> None:
        """
        ثبت اعتبارسنجی‌های پیش‌فرض برای فیلدهای رایج.
        """
        # اعتبارسنجی‌های پیش‌فرض
        self._custom_validators["email"] = self._validate_email_field
        self._custom_validators["phone"] = self._validate_phone_field
        self._custom_validators["phone_number"] = self._validate_phone_field
        self._custom_validators["url"] = self._validate_url_field
        self._custom_validators["website"] = self._validate_url_field
        self._custom_validators["date"] = self._validate_date_field
        self._custom_validators["time"] = self._validate_time_field
        self._custom_validators["color"] = self._validate_color_field
        self._custom_validators["role"] = self._validate_role_field
        self._custom_validators["level"] = self._validate_level_field
        self._custom_validators["form_type"] = self._validate_form_type_field
        self._custom_validators["status"] = self._validate_status_field
        self._custom_validators["payment_status"] = self._validate_payment_status_field

    def register_validator(self, field_name: str, validator: Callable) -> None:
        """
        ثبت یک اعتبارسنجی سفارشی برای یک فیلد.

        Args:
            field_name: نام فیلد.
            validator: تابع اعتبارسنجی که یک مقدار می‌گیرد و خطا (یا None) برمی‌گرداند.
        """
        self._custom_validators[field_name] = validator
        logger.debug(f"Custom validator registered for field: {field_name}")

    def validate_row(
        self,
        row: Dict[str, Any],
        required_fields: Optional[List[str]] = None,
        field_validators: Optional[Dict[str, Callable]] = None,
    ) -> List[str]:
        """
        اعتبارسنجی یک ردیف از داده‌ها.

        Args:
            row: دیکشنری داده‌های ردیف.
            required_fields: لیست فیلدهای اجباری (اختیاری).
            field_validators: دیکشنری نگاشت نام فیلد به تابع اعتبارسنجی (اختیاری).

        Returns:
            List[str]: لیست خطاها (در صورت عدم وجود خطا، لیست خالی است).
        """
        errors = []

        # اعتبارسنجی فیلدهای اجباری
        if required_fields:
            errors.extend(self.validate_required_fields(row, required_fields))

        # اعتبارسنجی فیلدها با استفاده از validators
        validators = field_validators or {}
        for field_name, validator in validators.items():
            value = row.get(field_name)
            try:
                error = validator(value)
                if error:
                    errors.append(f"{field_name}: {error}")
            except Exception as e:
                errors.append(f"{field_name}: خطا در اعتبارسنجی: {str(e)}")

        # اعتبارسنجی با استفاده از اعتبارسنجی‌های ثبت‌شده
        for field_name, value in row.items():
            if field_name in self._custom_validators and field_name not in validators:
                try:
                    error = self._custom_validators[field_name](value)
                    if error:
                        errors.append(f"{field_name}: {error}")
                except Exception as e:
                    errors.append(f"{field_name}: خطا در اعتبارسنجی: {str(e)}")

        return errors

    def validate_required_fields(
        self,
        row: Dict[str, Any],
        required_fields: List[str],
    ) -> List[str]:
        """
        اعتبارسنجی فیلدهای اجباری.

        Args:
            row: دیکشنری داده‌های ردیف.
            required_fields: لیست فیلدهای اجباری.

        Returns:
            List[str]: لیست خطاها.
        """
        errors = []

        for field in required_fields:
            value = row.get(field)
            if value is None or value == "" or (isinstance(value, list) and not value):
                errors.append(f"فیلد '{field}' اجباری است و نمی‌تواند خالی باشد.")

        return errors

    def validate_field_type(
        self,
        value: Any,
        expected_type: type,
        field_name: str,
    ) -> Optional[str]:
        """
        اعتبارسنجی نوع یک فیلد.

        Args:
            value: مقدار فیلد.
            expected_type: نوع مورد انتظار.
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        if not isinstance(value, expected_type):
            return f"نوع فیلد باید {expected_type.__name__} باشد."

        return None

    def validate_field_in_list(
        self,
        value: Any,
        allowed_values: List[Any],
        field_name: str,
    ) -> Optional[str]:
        """
        اعتبارسنجی اینکه مقدار فیلد در لیست مجاز باشد.

        Args:
            value: مقدار فیلد.
            allowed_values: لیست مقادیر مجاز.
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        if value not in allowed_values:
            return f"مقدار '{value}' مجاز نیست. مقادیر مجاز: {', '.join(map(str, allowed_values))}"

        return None

    def validate_field_length(
        self,
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field_name: str = "فیلد",
    ) -> Optional[str]:
        """
        اعتبارسنجی طول یک فیلد متنی.

        Args:
            value: مقدار فیلد.
            min_length: حداقل طول مجاز (اختیاری).
            max_length: حداکثر طول مجاز (اختیاری).
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        if not isinstance(value, str):
            return f"فیلد باید رشته باشد."

        length = len(value)

        if min_length is not None and length < min_length:
            return f"طول فیلد باید حداقل {min_length} کاراکتر باشد."

        if max_length is not None and length > max_length:
            return f"طول فیلد نباید بیشتر از {max_length} کاراکتر باشد."

        return None

    def validate_integer(
        self,
        value: Any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        field_name: str = "فیلد",
    ) -> Optional[str]:
        """
        اعتبارسنجی یک عدد صحیح.

        Args:
            value: مقدار فیلد.
            min_value: حداقل مقدار مجاز (اختیاری).
            max_value: حداکثر مقدار مجاز (اختیاری).
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        try:
            num = int(value)
        except (ValueError, TypeError):
            return f"فیلد باید یک عدد صحیح باشد."

        if min_value is not None and num < min_value:
            return f"مقدار باید حداقل {min_value} باشد."

        if max_value is not None and num > max_value:
            return f"مقدار نباید بیشتر از {max_value} باشد."

        return None

    def validate_float(
        self,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: str = "فیلد",
    ) -> Optional[str]:
        """
        اعتبارسنجی یک عدد اعشاری.

        Args:
            value: مقدار فیلد.
            min_value: حداقل مقدار مجاز (اختیاری).
            max_value: حداکثر مقدار مجاز (اختیاری).
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        try:
            num = float(value)
        except (ValueError, TypeError):
            return f"فیلد باید یک عدد باشد."

        if min_value is not None and num < min_value:
            return f"مقدار باید حداقل {min_value} باشد."

        if max_value is not None and num > max_value:
            return f"مقدار نباید بیشتر از {max_value} باشد."

        return None

    def validate_boolean(
        self,
        value: Any,
        field_name: str = "فیلد",
    ) -> Optional[str]:
        """
        اعتبارسنجی یک مقدار بولی.

        Args:
            value: مقدار فیلد.
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, str):
            if value.lower() in ("true", "false", "1", "0", "yes", "no"):
                return None

        return f"فیلد باید یک مقدار بولی باشد (true/false)."

    def validate_json(
        self,
        value: Any,
        field_name: str = "فیلد",
    ) -> Optional[str]:
        """
        اعتبارسنجی یک مقدار JSON.

        Args:
            value: مقدار فیلد.
            field_name: نام فیلد (برای نمایش در خطا).

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        if value is None or value == "":
            return None

        if isinstance(value, (dict, list)):
            return None

        if isinstance(value, str):
            try:
                json.loads(value)
                return None
            except json.JSONDecodeError:
                return f"مقدار باید یک JSON معتبر باشد."

        return f"مقدار باید یک JSON معتبر باشد (دیکشنری، لیست یا رشته JSON)."

    # ==========================================
    # اعتبارسنجی‌های پیش‌فرض برای فیلدهای خاص
    # ==========================================

    def _validate_email_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد ایمیل."""
        if value is None or value == "":
            return None

        try:
            validate_email(str(value))
            return None
        except Exception as e:
            return str(e)

    def _validate_phone_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد شماره تلفن."""
        if value is None or value == "":
            return None

        try:
            validate_phone(str(value))
            return None
        except Exception as e:
            return str(e)

    def _validate_url_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد آدرس اینترنتی."""
        if value is None or value == "":
            return None

        try:
            validate_url(str(value))
            return None
        except Exception as e:
            return str(e)

    def _validate_date_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد تاریخ."""
        if value is None or value == "":
            return None

        try:
            validate_date(str(value))
            return None
        except Exception as e:
            return str(e)

    def _validate_time_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد زمان."""
        if value is None or value == "":
            return None

        try:
            validate_time(str(value))
            return None
        except Exception as e:
            return str(e)

    def _validate_color_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد کد رنگ."""
        if value is None or value == "":
            return None

        try:
            validate_color(str(value))
            return None
        except Exception as e:
            return str(e)

    def _validate_role_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد نقش کاربری."""
        if value is None or value == "":
            return None

        try:
            valid_roles = [r.value for r in UserRole]
            if str(value).lower() not in valid_roles:
                return f"نقش '{value}' نامعتبر است. نقش‌های مجاز: {', '.join(valid_roles)}"
            return None
        except Exception as e:
            return str(e)

    def _validate_level_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد سطح کاربری."""
        if value is None or value == "":
            return None

        try:
            valid_levels = [l.value for l in UserLevel]
            if str(value).lower() not in valid_levels:
                return f"سطح '{value}' نامعتبر است. سطوح مجاز: {', '.join(valid_levels)}"
            return None
        except Exception as e:
            return str(e)

    def _validate_form_type_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد نوع فرم."""
        if value is None or value == "":
            return None

        try:
            valid_types = [t.value for t in FormType]
            if str(value).lower() not in valid_types:
                return f"نوع فرم '{value}' نامعتبر است. انواع مجاز: {', '.join(valid_types)}"
            return None
        except Exception as e:
            return str(e)

    def _validate_status_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد وضعیت سفارش."""
        if value is None or value == "":
            return None

        try:
            valid_statuses = [s.value for s in OrderStatus]
            if str(value).lower() not in valid_statuses:
                return f"وضعیت '{value}' نامعتبر است. وضعیت‌های مجاز: {', '.join(valid_statuses)}"
            return None
        except Exception as e:
            return str(e)

    def _validate_payment_status_field(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد وضعیت پرداخت."""
        if value is None or value == "":
            return None

        try:
            valid_statuses = [s.value for s in PaymentStatus]
            if str(value).lower() not in valid_statuses:
                return f"وضعیت پرداخت '{value}' نامعتبر است. وضعیت‌های مجاز: {', '.join(valid_statuses)}"
            return None
        except Exception as e:
            return str(e)

    # ==========================================
    # متدهای اعتبارسنجی ترکیبی
    # ==========================================

    def validate_user_row(self, row: Dict[str, Any]) -> List[str]:
        """
        اعتبارسنجی یک ردیف برای واردات کاربر.

        Args:
            row: دیکشنری داده‌های ردیف.

        Returns:
            List[str]: لیست خطاها.
        """
        required_fields = ["telegram_id", "first_name"]
        field_validators = {
            "telegram_id": lambda v: self.validate_integer(v, min_value=1, field_name="telegram_id"),
            "first_name": lambda v: self.validate_field_length(v, min_length=1, max_length=64, field_name="first_name"),
            "last_name": lambda v: self.validate_field_length(v, max_length=64, field_name="last_name"),
            "username": lambda v: self.validate_field_length(v, min_length=3, max_length=32, field_name="username"),
            "email": lambda v: self._validate_email_field(v),
            "phone_number": lambda v: self._validate_phone_field(v),
            "role": lambda v: self._validate_role_field(v),
            "level": lambda v: self._validate_level_field(v),
            "is_active": lambda v: self.validate_boolean(v, field_name="is_active"),
            "is_banned": lambda v: self.validate_boolean(v, field_name="is_banned"),
            "points": lambda v: self.validate_integer(v, min_value=0, field_name="points"),
        }

        return self.validate_row(row, required_fields, field_validators)

    def validate_form_row(self, row: Dict[str, Any]) -> List[str]:
        """
        اعتبارسنجی یک ردیف برای واردات فرم.

        Args:
            row: دیکشنری داده‌های ردیف.

        Returns:
            List[str]: لیست خطاها.
        """
        required_fields = ["title", "form_type", "fields"]
        field_validators = {
            "title": lambda v: self.validate_field_length(v, min_length=1, max_length=200, field_name="title"),
            "form_type": lambda v: self._validate_form_type_field(v),
            "fields": lambda v: self.validate_json(v, field_name="fields"),
            "description": lambda v: self.validate_field_length(v, max_length=1000, field_name="description"),
            "is_active": lambda v: self.validate_boolean(v, field_name="is_active"),
            "is_public": lambda v: self.validate_boolean(v, field_name="is_public"),
            "requires_login": lambda v: self.validate_boolean(v, field_name="requires_login"),
            "is_multistep": lambda v: self.validate_boolean(v, field_name="is_multistep"),
            "steps": lambda v: self.validate_integer(v, min_value=1, field_name="steps"),
            "submit_button_text": lambda v: self.validate_field_length(v, min_length=1, max_length=50, field_name="submit_button_text"),
            "max_submissions": lambda v: self.validate_integer(v, min_value=1, field_name="max_submissions"),
            "redirect_url": lambda v: self._validate_url_field(v),
        }

        return self.validate_row(row, required_fields, field_validators)

    def validate_order_row(self, row: Dict[str, Any]) -> List[str]:
        """
        اعتبارسنجی یک ردیف برای واردات سفارش.

        Args:
            row: دیکشنری داده‌های ردیف.

        Returns:
            List[str]: لیست خطاها.
        """
        required_fields = ["user_id", "order_number", "total_amount"]
        field_validators = {
            "user_id": lambda v: self.validate_integer(v, min_value=1, field_name="user_id"),
            "order_number": lambda v: self.validate_field_length(v, min_length=1, max_length=50, field_name="order_number"),
            "subtotal": lambda v: self.validate_float(v, min_value=0, field_name="subtotal"),
            "discount_amount": lambda v: self.validate_float(v, min_value=0, field_name="discount_amount"),
            "total_amount": lambda v: self.validate_float(v, min_value=0, field_name="total_amount"),
            "status": lambda v: self._validate_status_field(v),
            "payment_id": lambda v: self.validate_field_length(v, max_length=50, field_name="payment_id"),
            "tracking_code": lambda v: self.validate_field_length(v, max_length=100, field_name="tracking_code"),
            "coupon_code": lambda v: self.validate_field_length(v, max_length=50, field_name="coupon_code"),
        }

        return self.validate_row(row, required_fields, field_validators)

    def get_row_summary(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        دریافت خلاصه یک ردیف (برای گزارش‌گیری).

        Args:
            row: دیکشنری داده‌های ردیف.

        Returns:
            Dict[str, Any]: خلاصه ردیف.
        """
        return {
            "row_count": len(row),
            "fields": list(row.keys()),
            "non_empty_fields": [k for k, v in row.items() if v is not None and v != ""],
            "empty_fields": [k for k, v in row.items() if v is None or v == ""],
        }