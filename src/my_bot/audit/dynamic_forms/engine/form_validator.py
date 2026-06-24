# my_bot_project/src/my_bot/dynamic_forms/engine/form_validator.py
"""
اعتبارسنجی فرم‌های پویا (Form Validator).

این ماژول شامل کلاس `FormValidator` است که مسئولیت اعتبارسنجی داده‌های
ورودی فرم‌ها بر اساس قوانین تعریف‌شده در فیلدها را بر عهده دارد.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import re

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.dynamic_forms.models.form_definition import FormDefinition
from my_bot.dynamic_forms.models.form_field import DynamicFormField, FieldType

logger = get_logger(__name__)


class FormValidator:
    """
    اعتبارسنجی داده‌های فرم‌های پویا.

    این کلاس با استفاده از قوانین تعریف‌شده در فیلدها، داده‌های ورودی
    را اعتبارسنجی کرده و خطاها را بازمی‌گرداند.

    Attributes:
        strict_mode: حالت سخت‌گیرانه (اعتبارسنجی دقیق‌تر).
        allow_extra_fields: اجازه فیلدهای اضافی در داده‌ها.
        skip_missing_fields: نادیده گرفتن فیلدهای گم‌شده (برای فرم‌های ناقص).
    """

    def __init__(
        self,
        strict_mode: bool = True,
        allow_extra_fields: bool = False,
        skip_missing_fields: bool = False,
    ) -> None:
        """
        مقداردهی اولیه FormValidator.

        Args:
            strict_mode: حالت سخت‌گیرانه (اعتبارسنجی دقیق‌تر).
            allow_extra_fields: اجازه فیلدهای اضافی در داده‌ها.
            skip_missing_fields: نادیده گرفتن فیلدهای گم‌شده.
        """
        self.strict_mode = strict_mode
        self.allow_extra_fields = allow_extra_fields
        self.skip_missing_fields = skip_missing_fields

        logger.info(
            f"FormValidator initialized: strict_mode={strict_mode}, "
            f"allow_extra={allow_extra_fields}, skip_missing={skip_missing_fields}"
        )

    def validate(
        self,
        form: FormDefinition,
        data: Dict[str, Any],
        validate_all_fields: bool = True,
    ) -> List[Dict[str, str]]:
        """
        اعتبارسنجی داده‌های فرم.

        Args:
            form: تعریف فرم.
            data: داده‌های ورودی (نام فیلد -> مقدار).
            validate_all_fields: اعتبارسنجی تمام فیلدها (حتی آنهایی که داده ندارند).

        Returns:
            List[Dict[str, str]]: لیست خطاها (هر خطا شامل field و message).

        Raises:
            ValidationError: در صورت بروز خطاهای حیاتی.
        """
        errors = []

        # بررسی فیلدهای اضافی (در صورت غیرمجاز بودن)
        if not self.allow_extra_fields:
            extra_fields = set(data.keys()) - set(f.name for f in form.fields)
            if extra_fields:
                for field in extra_fields:
                    errors.append({
                        "field": field,
                        "message": f"فیلد '{field}' در فرم تعریف نشده است."
                    })

        # اعتبارسنجی فیلدها
        for field in form.fields:
            value = data.get(field.name)

            # اگر فیلد اجباری است و مقدار ندارد
            if field.is_required and (value is None or value == "" or value == []):
                errors.append({
                    "field": field.name,
                    "message": f"فیلد '{field.label}' اجباری است."
                })
                continue

            # اگر فیلد اجباری نیست و مقدار ندارد، نادیده بگیر
            if value is None or value == "" or value == []:
                if validate_all_fields:
                    # اگر قرار است همه فیلدها اعتبارسنجی شوند، اما مقدار ندارند،
                    # فقط برای فیلدهای اجباری خطا می‌دهیم
                    continue
                continue

            # اعتبارسنجی مقدار فیلد
            validation_error = self._validate_field_value(field, value)
            if validation_error:
                errors.append({
                    "field": field.name,
                    "message": validation_error,
                })

        # اگر فرم دارای تابع اعتبارسنجی سفارشی است
        if form.on_validate:
            try:
                custom_errors = form.on_validate(data)
                if custom_errors:
                    if isinstance(custom_errors, list):
                        errors.extend(custom_errors)
                    elif isinstance(custom_errors, dict):
                        for field, message in custom_errors.items():
                            errors.append({"field": field, "message": message})
            except Exception as e:
                logger.error(f"Error in custom validation: {e}")
                raise ValidationError(
                    message=f"خطا در اعتبارسنجی سفارشی: {str(e)}",
                    context={"form_id": form.id},
                )

        return errors

    def validate_required_fields(
        self,
        form: FormDefinition,
        data: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        بررسی فیلدهای اجباری فرم.

        Args:
            form: تعریف فرم.
            data: داده‌های ورودی.

        Returns:
            List[Dict[str, str]]: لیست خطاهای فیلدهای اجباری.
        """
        errors = []

        for field in form.fields:
            if field.is_required:
                value = data.get(field.name)
                if value is None or value == "" or value == []:
                    errors.append({
                        "field": field.name,
                        "message": f"فیلد '{field.label}' اجباری است."
                    })

        return errors

    def _validate_field_value(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """
        اعتبارسنجی مقدار یک فیلد.

        Args:
            field: فیلد فرم.
            value: مقدار ورودی.

        Returns:
            Optional[str]: پیام خطا در صورت نامعتبر بودن، یا None.
        """
        # اعتبارسنجی بر اساس نوع فیلد
        if field.field_type == FieldType.TEXT:
            return self._validate_text(field, value)
        elif field.field_type == FieldType.TEXTAREA:
            return self._validate_text(field, value)
        elif field.field_type == FieldType.NUMBER:
            return self._validate_number(field, value)
        elif field.field_type == FieldType.EMAIL:
            return self._validate_email(field, value)
        elif field.field_type == FieldType.PHONE:
            return self._validate_phone(field, value)
        elif field.field_type == FieldType.URL:
            return self._validate_url(field, value)
        elif field.field_type == FieldType.DATE:
            return self._validate_date(field, value)
        elif field.field_type == FieldType.TIME:
            return self._validate_time(field, value)
        elif field.field_type == FieldType.DATETIME:
            return self._validate_datetime(field, value)
        elif field.field_type in FieldType.SELECTION_TYPES:
            return self._validate_selection(field, value)
        elif field.field_type == FieldType.BOOLEAN:
            return self._validate_boolean(field, value)
        elif field.field_type == FieldType.RATING:
            return self._validate_rating(field, value)
        elif field.field_type == FieldType.RANGE:
            return self._validate_range(field, value)
        elif field.field_type == FieldType.COLOR:
            return self._validate_color(field, value)

        return None

    def _validate_text(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد متنی."""
        if not isinstance(value, str):
            return f"فیلد '{field.label}' باید متن باشد."

        # اعمال قوانین طول
        if "min_length" in field.validation_rules:
            min_len = field.validation_rules["min_length"]
            if len(value) < min_len:
                return f"طول متن باید حداقل {min_len} کاراکتر باشد."

        if "max_length" in field.validation_rules:
            max_len = field.validation_rules["max_length"]
            if len(value) > max_len:
                return f"طول متن نباید بیشتر از {max_len} کاراکتر باشد."

        # اعمال الگوی regex
        if "pattern" in field.validation_rules:
            pattern = field.validation_rules["pattern"]
            if not re.match(pattern, value):
                return f"متن با الگوی تعیین‌شده مطابقت ندارد."

        return None

    def _validate_number(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد عددی."""
        try:
            num = float(value)
        except (ValueError, TypeError):
            return f"فیلد '{field.label}' باید عدد باشد."

        # اعمال قوانین min و max
        if "min" in field.validation_rules:
            if num < float(field.validation_rules["min"]):
                return f"مقدار باید حداقل {field.validation_rules['min']} باشد."

        if "max" in field.validation_rules:
            if num > float(field.validation_rules["max"]):
                return f"مقدار نباید بیشتر از {field.validation_rules['max']} باشد."

        # اعمال قوانین step (برای اعداد اعشاری)
        if "step" in field.validation_rules:
            step = float(field.validation_rules["step"])
            if num % step != 0:
                return f"مقدار باید مضربی از {step} باشد."

        return None

    def _validate_email(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد ایمیل."""
        if not isinstance(value, str):
            return f"فیلد '{field.label}' باید متن باشد."

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            return "آدرس ایمیل معتبر نیست."

        return None

    def _validate_phone(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد تلفن."""
        if not isinstance(value, str):
            return f"فیلد '{field.label}' باید متن باشد."

        phone_pattern = r"^\+?[0-9]{10,15}$"
        if not re.match(phone_pattern, value):
            return "شماره تلفن معتبر نیست."

        return None

    def _validate_url(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد آدرس اینترنتی."""
        if not isinstance(value, str):
            return f"فیلد '{field.label}' باید متن باشد."

        url_pattern = r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
        if not re.match(url_pattern, value):
            return "آدرس اینترنتی معتبر نیست."

        return None

    def _validate_date(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد تاریخ."""
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except (ValueError, TypeError):
            return "تاریخ معتبر نیست (فرمت: YYYY-MM-DD)."
        return None

    def _validate_time(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد زمان."""
        try:
            datetime.strptime(value, "%H:%M")
        except (ValueError, TypeError):
            return "زمان معتبر نیست (فرمت: HH:MM)."
        return None

    def _validate_datetime(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد تاریخ و زمان."""
        try:
            datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return "تاریخ و زمان معتبر نیست (فرمت: ISO 8601)."
        return None

    def _validate_selection(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد انتخابی."""
        valid_values = [opt["value"] for opt in field.options]

        if field.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
            if not isinstance(value, list):
                return f"فیلد '{field.label}' باید لیستی از مقادیر باشد."
            for val in value:
                if val not in valid_values:
                    return f"مقدار '{val}' در گزینه‌ها وجود ندارد."
        else:
            if value not in valid_values:
                return f"مقدار '{value}' در گزینه‌ها وجود ندارد."

        return None

    def _validate_boolean(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد بولی."""
        if not isinstance(value, bool):
            return f"فیلد '{field.label}' باید بولی (True/False) باشد."
        return None

    def _validate_rating(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد امتیاز."""
        try:
            rating = float(value)
        except (ValueError, TypeError):
            return f"فیلد '{field.label}' باید عدد باشد."

        if not (1 <= rating <= 5):
            return "امتیاز باید بین ۱ تا ۵ باشد."

        return None

    def _validate_range(self, field: DynamicFormField, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد بازه عددی."""
        return self._validate_number(field, value)

    def _validate_color(self, field: DynamicFormField, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد رنگ."""
        if not isinstance(value, str):
            return f"فیلد '{field.label}' باید متن باشد."

        color_pattern = r"^#?[0-9a-fA-F]{6}$"
        if not re.match(color_pattern, value):
            return "کد رنگ معتبر نیست (فرمت: #RRGGBB)."

        return None

    def validate_condition(
        self,
        form: FormDefinition,
        data: Dict[str, Any],
        condition: Dict[str, Any],
    ) -> bool:
        """
        اعتبارسنجی یک شرط در فرم.

        Args:
            form: تعریف فرم.
            data: داده‌های ورودی.
            condition: شرط برای بررسی (با فرمت مشخص).

        Returns:
            bool: True اگر شرط برقرار باشد.
        """
        try:
            field_name = condition.get("field")
            operator = condition.get("operator", "eq")
            value = condition.get("value")

            if not field_name:
                return False

            field = form.get_field(field_name)
            if not field:
                return False

            field_value = data.get(field_name)

            if operator == "eq":
                return field_value == value
            elif operator == "neq":
                return field_value != value
            elif operator == "gt":
                return float(field_value) > float(value)
            elif operator == "gte":
                return float(field_value) >= float(value)
            elif operator == "lt":
                return float(field_value) < float(value)
            elif operator == "lte":
                return float(field_value) <= float(value)
            elif operator == "contains":
                return value in str(field_value)
            elif operator == "not_contains":
                return value not in str(field_value)
            elif operator == "in":
                return field_value in value
            elif operator == "not_in":
                return field_value not in value
            elif operator == "empty":
                return field_value is None or field_value == ""
            elif operator == "not_empty":
                return field_value is not None and field_value != ""

            return False

        except Exception as e:
            logger.error(f"Error validating condition: {e}")
            return False

    def get_field_errors(
        self,
        field: DynamicFormField,
        value: Any,
    ) -> List[str]:
        """
        دریافت خطاهای یک فیلد خاص.

        Args:
            field: فیلد فرم.
            value: مقدار ورودی.

        Returns:
            List[str]: لیست پیام‌های خطا.
        """
        errors = []
        error = self._validate_field_value(field, value)
        if error:
            errors.append(error)
        return errors

    def validate_step(
        self,
        form: FormDefinition,
        step: int,
        data: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        اعتبارسنجی یک مرحله خاص از فرم.

        Args:
            form: تعریف فرم.
            step: شماره مرحله (از ۱ شروع می‌شود).
            data: داده‌های ورودی.

        Returns:
            List[Dict[str, str]]: لیست خطاهای مرحله.
        """
        errors = []
        fields = form.get_fields_by_step(step)

        for field in fields:
            value = data.get(field.name)
            if field.is_required and (value is None or value == "" or value == []):
                errors.append({
                    "field": field.name,
                    "message": f"فیلد '{field.label}' اجباری است."
                })
                continue

            if value is None or value == "" or value == []:
                continue

            validation_error = self._validate_field_value(field, value)
            if validation_error:
                errors.append({
                    "field": field.name,
                    "message": validation_error,
                })

        return errors

    def is_valid(
        self,
        form: FormDefinition,
        data: Dict[str, Any],
    ) -> bool:
        """
        بررسی کلی اعتبار داده‌های فرم.

        Args:
            form: تعریف فرم.
            data: داده‌های ورودی.

        Returns:
            bool: True اگر داده‌ها معتبر باشند.
        """
        errors = self.validate(form, data)
        return len(errors) == 0

    def is_step_valid(
        self,
        form: FormDefinition,
        step: int,
        data: Dict[str, Any],
    ) -> bool:
        """
        بررسی اعتبار یک مرحله خاص از فرم.

        Args:
            form: تعریف فرم.
            step: شماره مرحله.
            data: داده‌های ورودی.

        Returns:
            bool: True اگر مرحله معتبر باشد.
        """
        errors = self.validate_step(form, step, data)
        return len(errors) == 0