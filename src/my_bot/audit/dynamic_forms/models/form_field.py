# my_bot_project/src/my_bot/dynamic_forms/models/form_field.py
"""
فیلد فرم پویا (Dynamic Form Field).

این ماژول شامل کلاس `DynamicFormField` است که یک فیلد را در فرم پویا تعریف می‌کند.
هر فیلد دارای نوع، برچسب، اعتبارسنجی‌ها، گزینه‌ها (برای فیلدهای انتخابی) و
سایر ویژگی‌های مرتبط است.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import re
from datetime import datetime

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class FieldType(str, Enum):
    """
    انواع فیلدهای قابل استفاده در فرم پویا.

    Attributes:
        TEXT: فیلد متنی ساده
        TEXTAREA: فیلد متنی چندخطی
        NUMBER: فیلد عددی
        EMAIL: فیلد ایمیل
        PHONE: فیلد تلفن
        DATE: فیلد تاریخ
        TIME: فیلد زمان
        DATETIME: فیلد تاریخ و زمان
        SELECT: فیلد انتخاب از لیست (تک انتخابی)
        MULTI_SELECT: فیلد انتخاب از لیست (چند انتخابی)
        RADIO: فیلد دکمه‌های رادیویی (تک انتخابی)
        CHECKBOX: فیلد چک‌باکس (چند انتخابی)
        BOOLEAN: فیلد بولی (True/False)
        RATING: فیلد امتیاز (۱ تا ۵)
        FILE: فیلد آپلود فایل
        URL: فیلد آدرس اینترنتی
        COLOR: فیلد انتخاب رنگ
        RANGE: فیلد بازه عددی
        HIDDEN: فیلد مخفی
        BUTTON: دکمه (برای اقدامات خاص)
        DIVIDER: جداکننده (غیرقابل پر کردن)
        LABEL: برچسب (غیرقابل پر کردن)
        CUSTOM: فیلد سفارشی
    """

    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    BOOLEAN = "boolean"
    RATING = "rating"
    FILE = "file"
    URL = "url"
    COLOR = "color"
    RANGE = "range"
    HIDDEN = "hidden"
    BUTTON = "button"
    DIVIDER = "divider"
    LABEL = "label"
    CUSTOM = "custom"

    # لیست انواع فیلدهای قابل پر کردن توسط کاربر
    INPUT_TYPES = {
        TEXT, TEXTAREA, NUMBER, EMAIL, PHONE, DATE, TIME, DATETIME,
        SELECT, MULTI_SELECT, RADIO, CHECKBOX, BOOLEAN, RATING,
        FILE, URL, COLOR, RANGE, HIDDEN
    }

    # لیست انواع فیلدهای انتخابی (با گزینه‌ها)
    SELECTION_TYPES = {
        SELECT, MULTI_SELECT, RADIO, CHECKBOX
    }

    # لیست انواع فیلدهای متنی
    TEXT_TYPES = {
        TEXT, TEXTAREA, EMAIL, PHONE, URL
    }

    # لیست انواع فیلدهایی که نیاز به اعتبارسنجی ویژه دارند
    SPECIAL_VALIDATION_TYPES = {
        EMAIL, PHONE, URL, DATE, TIME, DATETIME, RATING
    }


@dataclass
class DynamicFormField:
    """
    فیلد فرم پویا.

    Attributes:
        name: نام فیلد (یکتا در فرم).
        label: برچسب نمایشی فیلد.
        field_type: نوع فیلد (از FieldType).
        is_required: آیا فیلد اجباری است (پیش‌فرض False).
        placeholder: متن راهنما (اختیاری).
        help_text: متن کمک (اختیاری).
        default_value: مقدار پیش‌فرض (اختیاری).
        options: لیست گزینه‌ها (برای فیلدهای انتخابی).
        validation_rules: قوانین اعتبارسنجی (min, max, pattern, ...).
        order: ترتیب نمایش (پیش‌فرض ۰).
        group: گروه فیلد (برای دسته‌بندی).
        css_class: کلاس CSS (اختیاری).
        width: عرض فیلد (به‌عنوان درصد یا مقدار ثابت).
        is_hidden: آیا فیلد مخفی است (پیش‌فرض False).
        is_readonly: آیا فیلد فقط خواندنی است (پیش‌فرض False).
        metadata: داده‌های اضافی.
    """

    name: str
    label: str
    field_type: Union[str, FieldType]
    is_required: bool = False
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    default_value: Optional[Any] = None
    options: List[Dict[str, Any]] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    group: Optional[str] = None
    css_class: Optional[str] = None
    width: Optional[str] = None
    is_hidden: bool = False
    is_readonly: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه پس از ساخت آبجکت."""
        # تبدیل نوع فیلد به Enum در صورت نیاز
        if isinstance(self.field_type, str):
            try:
                self.field_type = FieldType(self.field_type)
            except ValueError:
                raise ValidationError(
                    message=f"نوع فیلد '{self.field_type}' نامعتبر است.",
                    context={"field_name": self.name, "field_type": self.field_type},
                )

        self._validate_name()
        self._validate_label()
        self._validate_type()
        self._validate_options()
        self._validate_validation_rules()
        self._validate_default_value()

    def _validate_name(self) -> None:
        """اعتبارسنجی نام فیلد."""
        if not self.name or not self.name.strip():
            raise ValidationError(
                message="نام فیلد نمی‌تواند خالی باشد.",
                context={"field_name": self.name},
            )
        # نام باید فقط شامل حروف، اعداد، خط تیره و زیرخط باشد
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.name):
            raise ValidationError(
                message=f"نام فیلد '{self.name}' فقط می‌تواند شامل حروف، اعداد، '-' و '_' باشد.",
                context={"field_name": self.name},
            )

    def _validate_label(self) -> None:
        """اعتبارسنجی برچسب فیلد."""
        if not self.label or not self.label.strip():
            raise ValidationError(
                message="برچسب فیلد نمی‌تواند خالی باشد.",
                context={"field_name": self.name},
            )

    def _validate_type(self) -> None:
        """اعتبارسنجی نوع فیلد."""
        valid_types = [t.value for t in FieldType]
        if self.field_type.value not in valid_types:
            raise ValidationError(
                message=f"نوع فیلد '{self.field_type.value}' نامعتبر است.",
                context={"field_name": self.name, "field_type": self.field_type.value},
            )

    def _validate_options(self) -> None:
        """اعتبارسنجی گزینه‌های فیلد (برای فیلدهای انتخابی)."""
        if self.field_type in FieldType.SELECTION_TYPES:
            if not self.options or len(self.options) < 2:
                raise ValidationError(
                    message=f"فیلد '{self.name}' از نوع انتخابی است و باید حداقل ۲ گزینه داشته باشد.",
                    context={"field_name": self.name, "field_type": self.field_type.value},
                )
            # بررسی ساختار گزینه‌ها
            for opt in self.options:
                if "value" not in opt or "label" not in opt:
                    raise ValidationError(
                        message=f"گزینه‌های فیلد '{self.name}' باید شامل 'value' و 'label' باشند.",
                        context={"field_name": self.name, "option": opt},
                    )

    def _validate_validation_rules(self) -> None:
        """اعتبارسنجی قوانین اعتبارسنجی."""
        # min و max برای فیلدهای عددی
        if self.field_type == FieldType.NUMBER:
            if "min" in self.validation_rules:
                try:
                    float(self.validation_rules["min"])
                except (ValueError, TypeError):
                    raise ValidationError(
                        message=f"قانون 'min' برای فیلد عددی '{self.name}' باید عدد باشد.",
                        context={"field_name": self.name, "min": self.validation_rules["min"]},
                    )
            if "max" in self.validation_rules:
                try:
                    float(self.validation_rules["max"])
                except (ValueError, TypeError):
                    raise ValidationError(
                        message=f"قانون 'max' برای فیلد عددی '{self.name}' باید عدد باشد.",
                        context={"field_name": self.name, "max": self.validation_rules["max"]},
                    )

        # min و max برای فیلدهای متنی (طول)
        if self.field_type in FieldType.TEXT_TYPES:
            if "min_length" in self.validation_rules:
                if not isinstance(self.validation_rules["min_length"], int) or self.validation_rules["min_length"] < 0:
                    raise ValidationError(
                        message=f"قانون 'min_length' برای فیلد متنی '{self.name}' باید عدد صحیح مثبت باشد.",
                        context={"field_name": self.name, "min_length": self.validation_rules["min_length"]},
                    )
            if "max_length" in self.validation_rules:
                if not isinstance(self.validation_rules["max_length"], int) or self.validation_rules["max_length"] <= 0:
                    raise ValidationError(
                        message=f"قانون 'max_length' برای فیلد متنی '{self.name}' باید عدد صحیح مثبت باشد.",
                        context={"field_name": self.name, "max_length": self.validation_rules["max_length"]},
                    )

        # pattern برای فیلدهای متنی
        if "pattern" in self.validation_rules:
            try:
                re.compile(self.validation_rules["pattern"])
            except re.error as e:
                raise ValidationError(
                    message=f"الگوی regex '{self.validation_rules['pattern']}' برای فیلد '{self.name}' معتبر نیست: {e}",
                    context={"field_name": self.name, "pattern": self.validation_rules["pattern"]},
                )

    def _validate_default_value(self) -> None:
        """اعتبارسنجی مقدار پیش‌فرض."""
        if self.default_value is not None:
            # برای فیلدهای انتخابی، مقدار پیش‌فرض باید در گزینه‌ها باشد
            if self.field_type in FieldType.SELECTION_TYPES:
                if self.field_type in (FieldType.SELECT, FieldType.RADIO):
                    if self.default_value not in [opt["value"] for opt in self.options]:
                        raise ValidationError(
                            message=f"مقدار پیش‌فرض '{self.default_value}' در گزینه‌های فیلد '{self.name}' وجود ندارد.",
                            context={"field_name": self.name, "default_value": self.default_value},
                        )
                elif self.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
                    if not isinstance(self.default_value, list):
                        raise ValidationError(
                            message=f"مقدار پیش‌فرض فیلد چندانتخابی '{self.name}' باید لیست باشد.",
                            context={"field_name": self.name, "default_value": self.default_value},
                        )
                    for val in self.default_value:
                        if val not in [opt["value"] for opt in self.options]:
                            raise ValidationError(
                                message=f"مقدار پیش‌فرض '{val}' در گزینه‌های فیلد '{self.name}' وجود ندارد.",
                                context={"field_name": self.name, "default_value": val},
                            )

            # برای فیلد بولی، مقدار پیش‌فرض باید بولی باشد
            if self.field_type == FieldType.BOOLEAN:
                if not isinstance(self.default_value, bool):
                    raise ValidationError(
                        message=f"مقدار پیش‌فرض فیلد بولی '{self.name}' باید True یا False باشد.",
                        context={"field_name": self.name, "default_value": self.default_value},
                    )

            # برای فیلد امتیاز، مقدار پیش‌فرض باید بین ۱ تا ۵ باشد
            if self.field_type == FieldType.RATING:
                if not isinstance(self.default_value, (int, float)) or not (1 <= self.default_value <= 5):
                    raise ValidationError(
                        message=f"مقدار پیش‌فرض فیلد امتیاز '{self.name}' باید بین ۱ تا ۵ باشد.",
                        context={"field_name": self.name, "default_value": self.default_value},
                    )

    def validate(self, value: Any) -> Optional[str]:
        """
        اعتبارسنجی یک مقدار ورودی بر اساس قوانین فیلد.

        Args:
            value: مقدار ورودی برای اعتبارسنجی.

        Returns:
            پیام خطا در صورت نامعتبر بودن، یا None در صورت معتبر بودن.
        """
        # اگر فیلد اجباری نیست و مقدار خالی است، معتبر است
        if not self.is_required and (value is None or value == "" or value == []):
            return None

        # بررسی فیلدهای اجباری
        if self.is_required:
            if value is None or value == "" or value == []:
                return f"فیلد '{self.label}' اجباری است."

        # اگر مقدار None یا خالی است و اجباری هم نیست، معتبر است
        if value is None or value == "":
            return None

        # اعتبارسنجی بر اساس نوع فیلد
        if self.field_type == FieldType.TEXT:
            return self._validate_text(value)
        elif self.field_type == FieldType.TEXTAREA:
            return self._validate_text(value)
        elif self.field_type == FieldType.NUMBER:
            return self._validate_number(value)
        elif self.field_type == FieldType.EMAIL:
            return self._validate_email(value)
        elif self.field_type == FieldType.PHONE:
            return self._validate_phone(value)
        elif self.field_type == FieldType.URL:
            return self._validate_url(value)
        elif self.field_type == FieldType.DATE:
            return self._validate_date(value)
        elif self.field_type == FieldType.TIME:
            return self._validate_time(value)
        elif self.field_type == FieldType.DATETIME:
            return self._validate_datetime(value)
        elif self.field_type in FieldType.SELECTION_TYPES:
            return self._validate_selection(value)
        elif self.field_type == FieldType.BOOLEAN:
            return self._validate_boolean(value)
        elif self.field_type == FieldType.RATING:
            return self._validate_rating(value)
        elif self.field_type == FieldType.RANGE:
            return self._validate_range(value)
        elif self.field_type == FieldType.COLOR:
            return self._validate_color(value)

        return None

    def _validate_text(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد متنی."""
        if not isinstance(value, str):
            return f"فیلد '{self.label}' باید متن باشد."

        # اعمال قوانین طول
        if "min_length" in self.validation_rules:
            min_len = self.validation_rules["min_length"]
            if len(value) < min_len:
                return f"طول متن باید حداقل {min_len} کاراکتر باشد."

        if "max_length" in self.validation_rules:
            max_len = self.validation_rules["max_length"]
            if len(value) > max_len:
                return f"طول متن نباید بیشتر از {max_len} کاراکتر باشد."

        # اعمال الگوی regex
        if "pattern" in self.validation_rules:
            pattern = self.validation_rules["pattern"]
            if not re.match(pattern, value):
                return f"متن با الگوی تعیین‌شده مطابقت ندارد."

        return None

    def _validate_number(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد عددی."""
        try:
            num = float(value)
        except (ValueError, TypeError):
            return f"فیلد '{self.label}' باید عدد باشد."

        # اعمال قوانین min و max
        if "min" in self.validation_rules:
            if num < float(self.validation_rules["min"]):
                return f"مقدار باید حداقل {self.validation_rules['min']} باشد."

        if "max" in self.validation_rules:
            if num > float(self.validation_rules["max"]):
                return f"مقدار نباید بیشتر از {self.validation_rules['max']} باشد."

        # اعمال قوانین step (برای اعداد اعشاری)
        if "step" in self.validation_rules:
            step = float(self.validation_rules["step"])
            if num % step != 0:
                return f"مقدار باید مضربی از {step} باشد."

        return None

    def _validate_email(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد ایمیل."""
        if not isinstance(value, str):
            return f"فیلد '{self.label}' باید متن باشد."

        # اعتبارسنجی ساده ایمیل
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            return "آدرس ایمیل معتبر نیست."

        return None

    def _validate_phone(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد تلفن."""
        if not isinstance(value, str):
            return f"فیلد '{self.label}' باید متن باشد."

        # اعتبارسنجی ساده شماره تلفن
        phone_pattern = r"^\+?[0-9]{10,15}$"
        if not re.match(phone_pattern, value):
            return "شماره تلفن معتبر نیست."

        return None

    def _validate_url(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد آدرس اینترنتی."""
        if not isinstance(value, str):
            return f"فیلد '{self.label}' باید متن باشد."

        url_pattern = r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
        if not re.match(url_pattern, value):
            return "آدرس اینترنتی معتبر نیست."

        return None

    def _validate_date(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد تاریخ."""
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except (ValueError, TypeError):
            return "تاریخ معتبر نیست (فرمت: YYYY-MM-DD)."
        return None

    def _validate_time(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد زمان."""
        try:
            datetime.strptime(value, "%H:%M")
        except (ValueError, TypeError):
            return "زمان معتبر نیست (فرمت: HH:MM)."
        return None

    def _validate_datetime(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد تاریخ و زمان."""
        try:
            datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return "تاریخ و زمان معتبر نیست (فرمت: ISO 8601)."
        return None

    def _validate_selection(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد انتخابی."""
        valid_values = [opt["value"] for opt in self.options]

        if self.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
            # چند انتخابی
            if not isinstance(value, list):
                return f"فیلد '{self.label}' باید لیستی از مقادیر باشد."
            for val in value:
                if val not in valid_values:
                    return f"مقدار '{val}' در گزینه‌ها وجود ندارد."
        else:
            # تک انتخابی
            if value not in valid_values:
                return f"مقدار '{value}' در گزینه‌ها وجود ندارد."

        return None

    def _validate_boolean(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد بولی."""
        if not isinstance(value, bool):
            return f"فیلد '{self.label}' باید بولی (True/False) باشد."
        return None

    def _validate_rating(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد امتیاز."""
        try:
            rating = float(value)
        except (ValueError, TypeError):
            return f"فیلد '{self.label}' باید عدد باشد."

        if not (1 <= rating <= 5):
            return "امتیاز باید بین ۱ تا ۵ باشد."

        return None

    def _validate_range(self, value: Any) -> Optional[str]:
        """اعتبارسنجی فیلد بازه عددی."""
        return self._validate_number(value)

    def _validate_color(self, value: str) -> Optional[str]:
        """اعتبارسنجی فیلد رنگ."""
        if not isinstance(value, str):
            return f"فیلد '{self.label}' باید متن باشد."

        color_pattern = r"^#?[0-9a-fA-F]{6}$"
        if not re.match(color_pattern, value):
            return "کد رنگ معتبر نیست (فرمت: #RRGGBB)."

        return None

    def get_default_display(self) -> Any:
        """
        دریافت مقدار پیش‌فرض به‌صورت مناسب برای نمایش.

        Returns:
            مقدار پیش‌فرض یا None در صورت عدم وجود.
        """
        if self.default_value is None:
            return None

        # برای فیلدهای انتخابی، برچسب گزینه را برمی‌گرداند
        if self.field_type in FieldType.SELECTION_TYPES:
            if self.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
                if isinstance(self.default_value, list):
                    labels = []
                    for val in self.default_value:
                        for opt in self.options:
                            if opt.get("value") == val:
                                labels.append(opt.get("label", val))
                                break
                    return labels
            else:
                for opt in self.options:
                    if opt.get("value") == self.default_value:
                        return opt.get("label", self.default_value)
        return self.default_value

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل فیلد فرم به دیکشنری برای سریال‌سازی.

        Returns:
            دیکشنری شامل اطلاعات فیلد.
        """
        return {
            "name": self.name,
            "label": self.label,
            "type": self.field_type.value,
            "is_required": self.is_required,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
            "default_value": self.default_value,
            "options": self.options,
            "validation_rules": self.validation_rules,
            "order": self.order,
            "group": self.group,
            "css_class": self.css_class,
            "width": self.width,
            "is_hidden": self.is_hidden,
            "is_readonly": self.is_readonly,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DynamicFormField":
        """
        ساخت فیلد فرم از دیکشنری.

        Args:
            data: دیکشنری شامل اطلاعات فیلد.

        Returns:
            نمونه‌ای از DynamicFormField.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        return cls(
            name=data["name"],
            label=data["label"],
            field_type=data.get("type", "text"),
            is_required=data.get("is_required", False),
            placeholder=data.get("placeholder"),
            help_text=data.get("help_text"),
            default_value=data.get("default_value"),
            options=data.get("options", []),
            validation_rules=data.get("validation_rules", {}),
            order=data.get("order", 0),
            group=data.get("group"),
            css_class=data.get("css_class"),
            width=data.get("width"),
            is_hidden=data.get("is_hidden", False),
            is_readonly=data.get("is_readonly", False),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """نمایش رشته‌ای فیلد فرم."""
        return f"DynamicFormField(name={self.name}, label={self.label}, type={self.field_type.value})"