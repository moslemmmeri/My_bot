# my_bot_project/src/my_bot/bulk_import/validators/data_validator.py
"""
اعتبارسنجی داده‌های واردات انبوه (Data Validator).

این کلاس مسئولیت اعتبارسنجی کلی داده‌های وارداتی را بر عهده دارد.
اعتبارسنجی شامل بررسی یکپارچگی داده‌ها، عدم تکراری بودن،
اعتبارسنجی ارجاعات و قوانین کسب‌وکار است.
"""

from typing import Optional, List, Dict, Any, Set, Tuple, Callable
from collections import defaultdict

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.validation_errors import ValidationError

logger = get_logger(__name__)


class DataValidator:
    """
    اعتبارسنجی کلی داده‌های واردات انبوه.

    این کلاس با استفاده از قوانین تعریف‌شده، مجموعه داده‌ها را
    اعتبارسنجی کرده و خطاها و هشدارها را بازمی‌گرداند.

    Attributes:
        strict_mode: حالت سخت‌گیرانه (پیش‌فرض True).
        max_errors: حداکثر تعداد خطاهای مجاز قبل از توقف (پیش‌فرض ۱۰۰).
        _custom_rules: قوانین اعتبارسنجی سفارشی.
    """

    def __init__(self, strict_mode: bool = True, max_errors: int = 100) -> None:
        """
        مقداردهی اولیه DataValidator.

        Args:
            strict_mode: حالت سخت‌گیرانه (پیش‌فرض True).
            max_errors: حداکثر تعداد خطاهای مجاز قبل از توقف (پیش‌فرض ۱۰۰).
        """
        self.strict_mode = strict_mode
        self.max_errors = max_errors
        self._custom_rules: Dict[str, Callable] = {}

        logger.info(
            f"DataValidator initialized: strict_mode={strict_mode}, "
            f"max_errors={max_errors}"
        )

    def register_rule(self, rule_name: str, rule_func: Callable) -> None:
        """
        ثبت یک قانون اعتبارسنجی سفارشی.

        Args:
            rule_name: نام قانون.
            rule_func: تابع اعتبارسنجی که لیست ردیف‌ها را گرفته و خطاها را برمی‌گرداند.
        """
        self._custom_rules[rule_name] = rule_func
        logger.debug(f"Custom validation rule registered: {rule_name}")

    def validate_data(
        self,
        rows: List[Dict[str, Any]],
        unique_fields: Optional[List[str]] = None,
        required_fields: Optional[List[str]] = None,
        foreign_keys: Optional[Dict[str, List[str]]] = None,
        custom_rules: Optional[Dict[str, Callable]] = None,
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی کلی داده‌ها.

        Args:
            rows: لیست ردیف‌های داده.
            unique_fields: لیست فیلدهایی که باید یکتا باشند.
            required_fields: لیست فیلدهای اجباری (در تمام ردیف‌ها).
            foreign_keys: دیکشنری نگاشت نام فیلد به لیست مقادیر مجاز (برای اعتبارسنجی ارجاع).
            custom_rules: قوانین اعتبارسنجی سفارشی (اختیاری).

        Returns:
            Dict[str, Any]: نتیجه اعتبارسنجی شامل:
                - is_valid: آیا داده‌ها معتبر هستند
                - errors: لیست خطاها
                - warnings: لیست هشدارها
                - stats: آمار (تعداد ردیف‌ها، تعداد خطاها و ...)

        Raises:
            ValidationError: در صورت بروز خطاهای حیاتی.
        """
        errors = []
        warnings = []
        stats = {
            "total_rows": len(rows),
            "valid_rows": 0,
            "invalid_rows": 0,
            "errors_count": 0,
            "warnings_count": 0,
        }

        # اگر داده‌ها خالی هستند
        if not rows:
            return {
                "is_valid": False,
                "errors": ["داده‌ها خالی هستند."],
                "warnings": [],
                "stats": stats,
            }

        # ۱. اعتبارسنجی فیلدهای اجباری (در تمام ردیف‌ها)
        if required_fields:
            missing_fields = self._check_required_fields(rows, required_fields)
            if missing_fields:
                errors.append(f"فیلدهای اجباری در برخی ردیف‌ها وجود ندارند: {', '.join(missing_fields)}")
                stats["errors_count"] += len(missing_fields)

        # ۲. اعتبارسنجی یکتایی
        if unique_fields:
            duplicates = self._check_uniqueness(rows, unique_fields)
            for field, duplicate_values in duplicates.items():
                if duplicate_values:
                    errors.append(f"مقادیر تکراری در فیلد '{field}': {', '.join(map(str, duplicate_values))}")
                    stats["errors_count"] += len(duplicate_values)

        # ۳. اعتبارسنجی ارجاعات (Foreign Keys)
        if foreign_keys:
            invalid_refs = self._check_foreign_keys(rows, foreign_keys)
            for field, invalid_values in invalid_refs.items():
                if invalid_values:
                    errors.append(f"مقادیر نامعتبر در فیلد '{field}': {', '.join(map(str, invalid_values))}")
                    stats["errors_count"] += len(invalid_values)

        # ۴. اعتبارسنجی ردیف‌ها (خطاهای سطح ردیف)
        row_errors = self._validate_rows(rows)
        if row_errors:
            errors.extend(row_errors)
            stats["errors_count"] += len(row_errors)

        # ۵. اعتبارسنجی با استفاده از قوانین سفارشی
        rules = custom_rules or {}
        rules.update(self._custom_rules)
        for rule_name, rule_func in rules.items():
            try:
                rule_errors = rule_func(rows)
                if rule_errors:
                    if isinstance(rule_errors, list):
                        errors.extend(rule_errors)
                        stats["errors_count"] += len(rule_errors)
                    elif isinstance(rule_errors, str):
                        errors.append(rule_errors)
                        stats["errors_count"] += 1
            except Exception as e:
                errors.append(f"خطا در قانون '{rule_name}': {str(e)}")
                stats["errors_count"] += 1

        # محاسبه آمار
        stats["invalid_rows"] = len(errors)
        stats["valid_rows"] = len(rows) - stats["invalid_rows"]

        # بروزرسانی is_valid
        is_valid = len(errors) == 0

        # اگر در حالت سخت‌گیرانه هستیم و تعداد خطاها از حد مجاز بیشتر است
        if self.strict_mode and stats["errors_count"] > self.max_errors:
            raise ValidationError(
                message=f"تعداد خطاها ({stats['errors_count']}) از حد مجاز ({self.max_errors}) بیشتر است.",
                context={
                    "errors_count": stats["errors_count"],
                    "max_errors": self.max_errors,
                    "sample_errors": errors[:10],
                },
            )

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "stats": stats,
        }

    def _check_required_fields(
        self,
        rows: List[Dict[str, Any]],
        required_fields: List[str],
    ) -> List[str]:
        """
        بررسی فیلدهای اجباری در تمام ردیف‌ها.

        Args:
            rows: لیست ردیف‌ها.
            required_fields: لیست فیلدهای اجباری.

        Returns:
            List[str]: لیست فیلدهایی که در برخی ردیف‌ها وجود ندارند.
        """
        missing_fields = set()

        for field in required_fields:
            for row in rows:
                if field not in row or row[field] is None or row[field] == "":
                    missing_fields.add(field)
                    break

        return list(missing_fields)

    def _check_uniqueness(
        self,
        rows: List[Dict[str, Any]],
        unique_fields: List[str],
    ) -> Dict[str, List[Any]]:
        """
        بررسی یکتایی مقادیر در فیلدهای مشخص.

        Args:
            rows: لیست ردیف‌ها.
            unique_fields: لیست فیلدهایی که باید یکتا باشند.

        Returns:
            Dict[str, List[Any]]: دیکشنری نگاشت نام فیلد به لیست مقادیر تکراری.
        """
        duplicates: Dict[str, Set[Any]] = defaultdict(set)

        for field in unique_fields:
            seen = set()
            for row in rows:
                value = row.get(field)
                if value is not None and value != "":
                    if value in seen:
                        duplicates[field].add(value)
                    else:
                        seen.add(value)

        # تبدیل set به list
        return {k: list(v) for k, v in duplicates.items() if v}

    def _check_foreign_keys(
        self,
        rows: List[Dict[str, Any]],
        foreign_keys: Dict[str, List[str]],
    ) -> Dict[str, List[Any]]:
        """
        اعتبارسنجی ارجاعات (Foreign Keys).

        Args:
            rows: لیست ردیف‌ها.
            foreign_keys: دیکشنری نگاشت نام فیلد به لیست مقادیر مجاز.

        Returns:
            Dict[str, List[Any]]: دیکشنری نگاشت نام فیلد به لیست مقادیر نامعتبر.
        """
        invalid_values: Dict[str, Set[Any]] = defaultdict(set)

        for field, valid_values in foreign_keys.items():
            valid_set = set(valid_values)
            for row in rows:
                value = row.get(field)
                if value is not None and value != "":
                    if value not in valid_set:
                        invalid_values[field].add(value)

        return {k: list(v) for k, v in invalid_values.items() if v}

    def _validate_rows(self, rows: List[Dict[str, Any]]) -> List[str]:
        """
        اعتبارسنجی ردیف‌ها (برای اعتبارسنجی‌های ساده‌تر).

        Args:
            rows: لیست ردیف‌ها.

        Returns:
            List[str]: لیست خطاها.
        """
        errors = []

        # بررسی ردیف‌های خالی
        for idx, row in enumerate(rows, start=1):
            if not row or all(v is None or v == "" for v in row.values()):
                errors.append(f"ردیف {idx} خالی است.")
                continue

            # بررسی ردیف‌هایی که تمام مقادیر None دارند
            non_empty = {k: v for k, v in row.items() if v is not None and v != ""}
            if not non_empty:
                errors.append(f"ردیف {idx} هیچ مقدار معتبری ندارد.")

        return errors

    def check_data_consistency(
        self,
        rows: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
    ) -> List[str]:
        """
        اعتبارسنجی یکپارچگی داده‌ها با استفاده از قوانین شرطی.

        هر قانون به‌صورت دیکشنری با کلیدهای زیر تعریف می‌شود:
        - field: نام فیلد
        - operator: عملگر مقایسه ('eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'not_in')
        - value: مقدار برای مقایسه
        - error_message: پیام خطا

        Args:
            rows: لیست ردیف‌ها.
            rules: لیست قوانین یکپارچگی.

        Returns:
            List[str]: لیست خطاها.
        """
        errors = []

        for rule in rules:
            field = rule.get("field")
            operator = rule.get("operator", "eq")
            value = rule.get("value")
            error_message = rule.get("error_message", f"قانون یکپارچگی برای فیلد '{field}' نقض شد.")

            if not field:
                continue

            for idx, row in enumerate(rows, start=1):
                row_value = row.get(field)

                # اعمال عملگر
                if not self._evaluate_condition(row_value, operator, value):
                    errors.append(f"ردیف {idx}: {error_message}")

        return errors

    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """
        ارزیابی یک شرط.

        Args:
            actual: مقدار واقعی.
            operator: عملگر.
            expected: مقدار مورد انتظار.

        Returns:
            bool: نتیجه شرط.
        """
        if operator == "eq":
            return actual == expected
        elif operator == "ne":
            return actual != expected
        elif operator == "gt":
            try:
                return float(actual) > float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == "gte":
            try:
                return float(actual) >= float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == "lt":
            try:
                return float(actual) < float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == "lte":
            try:
                return float(actual) <= float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == "in":
            return actual in expected if isinstance(expected, (list, tuple, set)) else False
        elif operator == "not_in":
            return actual not in expected if isinstance(expected, (list, tuple, set)) else True
        elif operator == "contains":
            return expected in str(actual) if actual is not None else False
        elif operator == "not_contains":
            return expected not in str(actual) if actual is not None else True
        else:
            return False

    def check_dependencies(
        self,
        rows: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
    ) -> List[str]:
        """
        اعتبارسنجی وابستگی‌های بین فیلدها.

        هر وابستگی به‌صورت دیکشنری با کلیدهای زیر تعریف می‌شود:
        - field: نام فیلد اصلی
        - depends_on: نام فیلد وابسته
        - condition: شرطی که باید برقرار باشد

        Args:
            rows: لیست ردیف‌ها.
            dependencies: لیست وابستگی‌ها.

        Returns:
            List[str]: لیست خطاها.
        """
        errors = []

        for dep in dependencies:
            field = dep.get("field")
            depends_on = dep.get("depends_on")
            condition = dep.get("condition", {})
            error_message = dep.get("error_message", f"وابستگی '{field}' به '{depends_on}' نقض شد.")

            if not field or not depends_on:
                continue

            for idx, row in enumerate(rows, start=1):
                field_value = row.get(field)
                depends_value = row.get(depends_on)

                # اگر فیلد وابسته مقدار داشته باشد، فیلد اصلی باید شرط را داشته باشد
                if depends_value is not None and depends_value != "":
                    # اعمال شرط
                    condition_field = condition.get("field", field)
                    condition_operator = condition.get("operator", "eq")
                    condition_value = condition.get("value")

                    actual = row.get(condition_field)

                    if not self._evaluate_condition(actual, condition_operator, condition_value):
                        errors.append(f"ردیف {idx}: {error_message}")

        return errors

    def get_data_quality_report(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        دریافت گزارش کیفیت داده‌ها.

        Args:
            rows: لیست ردیف‌ها.

        Returns:
            Dict[str, Any]: گزارش کیفیت شامل:
                - total_rows: تعداد کل ردیف‌ها
                - empty_rows: تعداد ردیف‌های خالی
                - complete_rows: تعداد ردیف‌های کامل (بدون فیلد خالی)
                - field_completeness: درصد تکمیل هر فیلد
                - unique_values: تعداد مقادیر یکتا برای هر فیلد
                - null_counts: تعداد مقادیر خالی برای هر فیلد
        """
        if not rows:
            return {
                "total_rows": 0,
                "empty_rows": 0,
                "complete_rows": 0,
                "field_completeness": {},
                "unique_values": {},
                "null_counts": {},
            }

        total_rows = len(rows)
        empty_rows = 0
        complete_rows = 0
        field_counts = defaultdict(int)
        field_null_counts = defaultdict(int)
        field_unique_counts = defaultdict(set)

        for row in rows:
            # بررسی ردیف خالی
            if not row or all(v is None or v == "" for v in row.values()):
                empty_rows += 1
                continue

            # بررسی کامل بودن ردیف
            is_complete = all(v is not None and v != "" for v in row.values())
            if is_complete:
                complete_rows += 1

            # جمع‌آوری آمار فیلدها
            for field, value in row.items():
                if value is not None and value != "":
                    field_counts[field] += 1
                    field_unique_counts[field].add(str(value))
                else:
                    field_null_counts[field] += 1

        # محاسبه درصد تکمیل
        field_completeness = {}
        for field in set(field_counts.keys()) | set(field_null_counts.keys()):
            total = field_counts[field] + field_null_counts[field]
            field_completeness[field] = (field_counts[field] / total * 100) if total > 0 else 0

        return {
            "total_rows": total_rows,
            "empty_rows": empty_rows,
            "complete_rows": complete_rows,
            "field_completeness": field_completeness,
            "unique_values": {k: len(v) for k, v in field_unique_counts.items()},
            "null_counts": dict(field_null_counts),
        }

    def get_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        دریافت خلاصه داده‌ها (برای گزارش‌گیری).

        Args:
            rows: لیست ردیف‌ها.

        Returns:
            Dict[str, Any]: خلاصه داده‌ها.
        """
        if not rows:
            return {
                "total_rows": 0,
                "columns": [],
                "sample": [],
                "quality_report": {},
            }

        columns = list(rows[0].keys()) if rows else []
        sample = rows[:5] if len(rows) > 5 else rows

        return {
            "total_rows": len(rows),
            "columns": columns,
            "sample": sample,
            "quality_report": self.get_data_quality_report(rows),
        }