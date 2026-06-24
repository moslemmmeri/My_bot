# my_bot_project/src/my_bot/bulk_import/importers/form_importer.py
"""
واردکننده فرم‌ها (Form Importer).

این کلاس مسئولیت واردات انبوه فرم‌ها از فایل‌های اکسل یا CSV را بر عهده دارد.
داده‌های وارداتی شامل اطلاعات فرم مانند عنوان، نوع، فیلدها، تنظیمات و غیره است.
"""

import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from my_bot.bulk_import.parsers.excel_reader import ExcelReader
from my_bot.bulk_import.parsers.csv_reader import CSVReader
from my_bot.bulk_import.validators.row_validator import RowValidator
from my_bot.bulk_import.validators.data_validator import DataValidator
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.not_found_errors import FormNotFoundError, UserNotFoundError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.constants.form_types import FormType
from my_bot.domain.entities.form import Form
from my_bot.domain.value_objects.form_field import FormField
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class FormImporter:
    """
    واردکننده فرم‌ها از فایل‌های اکسل یا CSV.

    این کلاس داده‌های فرم‌ها را از فایل خوانده، اعتبارسنجی کرده
    و در دیتابیس ذخیره می‌کند.

    Attributes:
        form_repository: ریپازیتوری فرم.
        user_repository: ریپازیتوری کاربر (برای یافتن سازنده).
        row_validator: اعتبارسنج ردیف‌ها.
        data_validator: اعتبارسنج داده‌ها.
        default_creator_id: شناسه پیش‌فرض سازنده (در صورت عدم وجود).
        required_headers: هدرهای مورد نیاز در فایل.
    """

    REQUIRED_HEADERS = ["title", "form_type", "fields"]

    def __init__(
        self,
        form_repository: FormRepository,
        user_repository: UserRepository,
        default_creator_id: Optional[int] = None,
    ) -> None:
        """
        مقداردهی اولیه FormImporter.

        Args:
            form_repository: ریپازیتوری فرم.
            user_repository: ریپازیتوری کاربر (برای یافتن سازنده).
            default_creator_id: شناسه پیش‌فرض سازنده در صورت عدم وجود.
        """
        self._form_repository = form_repository
        self._user_repository = user_repository
        self._row_validator = RowValidator()
        self._data_validator = DataValidator()
        self.default_creator_id = default_creator_id

        logger.info(
            f"FormImporter initialized: default_creator_id={default_creator_id}"
        )

    async def import_from_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        header_row: int = 1,
        skip_rows: int = 0,
    ) -> Dict[str, Any]:
        """
        واردات فرم‌ها از فایل اکسل.

        Args:
            file_path: مسیر فایل اکسل.
            sheet_name: نام شیت (اختیاری).
            header_row: شماره ردیف هدر (پیش‌فرض: ۱).
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند (پیش‌فرض: ۰).

        Returns:
            Dict[str, Any]: نتیجه واردات شامل:
                - total_rows: تعداد کل ردیف‌ها
                - imported: تعداد واردات موفق
                - failed: تعداد واردات ناموفق
                - errors: لیست خطاها
                - skipped: تعداد ردیف‌های نادیده‌گرفته‌شده

        Raises:
            ValidationError: اگر فایل معتبر نباشد یا هدرهای مورد نیاز وجود نداشته باشند.
        """
        logger.info(f"Importing forms from Excel file: {file_path}")

        reader = ExcelReader(
            file_path=file_path,
            header_row=header_row,
            sheet_name=sheet_name,
        )

        return await self._import_from_reader(reader, skip_rows)

    async def import_from_excel_bytes(
        self,
        file_content: bytes,
        sheet_name: Optional[str] = None,
        header_row: int = 1,
        skip_rows: int = 0,
    ) -> Dict[str, Any]:
        """
        واردات فرم‌ها از محتوای فایل اکسل به‌صورت bytes.

        Args:
            file_content: محتوای فایل اکسل.
            sheet_name: نام شیت (اختیاری).
            header_row: شماره ردیف هدر (پیش‌فرض: ۱).
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند (پیش‌فرض: ۰).

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        logger.info("Importing forms from Excel bytes")

        reader = ExcelReader(
            file_content=file_content,
            header_row=header_row,
            sheet_name=sheet_name,
        )

        return await self._import_from_reader(reader, skip_rows)

    async def import_from_csv(
        self,
        file_path: str,
        delimiter: str = ",",
        encoding: Optional[str] = None,
        has_header: bool = True,
        skip_rows: int = 0,
    ) -> Dict[str, Any]:
        """
        واردات فرم‌ها از فایل CSV.

        Args:
            file_path: مسیر فایل CSV.
            delimiter: جداکننده فیلدها (پیش‌فرض: ',').
            encoding: کدگذاری فایل (اختیاری).
            has_header: آیا فایل دارای هدر است (پیش‌فرض: True).
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند (پیش‌فرض: ۰).

        Returns:
            Dict[str, Any]: نتیجه واردات.

        Raises:
            ValidationError: اگر فایل معتبر نباشد یا هدرهای مورد نیاز وجود نداشته باشند.
        """
        logger.info(f"Importing forms from CSV file: {file_path}")

        reader = CSVReader(
            file_path=file_path,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            skip_rows=skip_rows,
        )

        reader.load()

        return await self._import_from_csv_reader(reader)

    async def import_from_csv_bytes(
        self,
        file_content: bytes,
        delimiter: str = ",",
        encoding: Optional[str] = None,
        has_header: bool = True,
        skip_rows: int = 0,
    ) -> Dict[str, Any]:
        """
        واردات فرم‌ها از محتوای فایل CSV به‌صورت bytes.

        Args:
            file_content: محتوای فایل CSV.
            delimiter: جداکننده فیلدها (پیش‌فرض: ',').
            encoding: کدگذاری فایل (اختیاری).
            has_header: آیا فایل دارای هدر است (پیش‌فرض: True).
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند (پیش‌فرض: ۰).

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        logger.info("Importing forms from CSV bytes")

        reader = CSVReader(
            file_content=file_content,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            skip_rows=skip_rows,
        )

        reader.load()

        return await self._import_from_csv_reader(reader)

    async def _import_from_reader(
        self,
        reader: ExcelReader,
        skip_rows: int = 0,
    ) -> Dict[str, Any]:
        """
        واردات از ExcelReader.

        Args:
            reader: نمونه ExcelReader.
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند.

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        # اعتبارسنجی هدرهای مورد نیاز
        required_headers = self.REQUIRED_HEADERS + ["description", "is_active", "is_public", "requires_login", "is_multistep", "steps"]
        reader.validate_headers_raise(required_headers, case_sensitive=False)

        # دریافت داده‌ها
        start_row = reader.header_row + 1 + skip_rows
        rows = reader.read_rows(start_row=start_row, as_dict=True)

        if not rows:
            return {
                "total_rows": 0,
                "imported": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [],
            }

        return await self._import_rows(rows)

    async def _import_from_csv_reader(
        self,
        reader: CSVReader,
    ) -> Dict[str, Any]:
        """
        واردات از CSVReader.

        Args:
            reader: نمونه CSVReader.

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        # اعتبارسنجی هدرهای مورد نیاز
        required_headers = self.REQUIRED_HEADERS + ["description", "is_active", "is_public", "requires_login", "is_multistep", "steps"]
        reader.validate_headers_raise(required_headers, case_sensitive=False)

        # دریافت داده‌ها
        rows = reader.read_rows(as_dict=True)

        if not rows:
            return {
                "total_rows": 0,
                "imported": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [],
            }

        return await self._import_rows(rows)

    async def _import_rows(
        self,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        واردات ردیف‌های داده.

        Args:
            rows: لیست ردیف‌ها.

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        imported = 0
        failed = 0
        skipped = 0
        errors = []

        # بررسی وجود سازنده پیش‌فرض
        creator_id = self.default_creator_id
        if creator_id:
            creator = await self._user_repository.get_by_id(creator_id)
            if not creator:
                logger.warning(f"Default creator with id {creator_id} not found. Using None.")
                creator_id = None

        for idx, row in enumerate(rows, start=1):
            try:
                # اعتبارسنجی ردیف
                validation_errors = self._validate_row(row)
                if validation_errors:
                    errors.append({
                        "row": idx,
                        "errors": validation_errors,
                    })
                    failed += 1
                    continue

                # تبدیل به موجودیت فرم
                form = await self._create_form_from_row(row, creator_id)

                # ذخیره در دیتابیس
                saved_form = await self._form_repository.save(form)

                logger.debug(f"Form imported: id={saved_form.id}, title={saved_form.title}")
                imported += 1

            except ValidationError as e:
                errors.append({
                    "row": idx,
                    "errors": [str(e)],
                    "data": row,
                })
                failed += 1
                logger.warning(f"Validation error in row {idx}: {e}")

            except DatabaseError as e:
                errors.append({
                    "row": idx,
                    "errors": [f"Database error: {str(e)}"],
                    "data": row,
                })
                failed += 1
                logger.error(f"Database error in row {idx}: {e}")

            except Exception as e:
                errors.append({
                    "row": idx,
                    "errors": [f"Unexpected error: {str(e)}"],
                    "data": row,
                })
                failed += 1
                logger.error(f"Unexpected error in row {idx}: {e}")

        result = {
            "total_rows": len(rows),
            "imported": imported,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
        }

        logger.info(
            f"Form import completed: {imported} imported, "
            f"{failed} failed, {skipped} skipped"
        )

        return result

    def _validate_row(self, row: Dict[str, Any]) -> List[str]:
        """
        اعتبارسنجی یک ردیف از داده‌ها.

        Args:
            row: دیکشنری داده‌های ردیف.

        Returns:
            List[str]: لیست خطاها.
        """
        errors = []

        # اعتبارسنجی فیلدهای اجباری
        for field in self.REQUIRED_HEADERS:
            value = row.get(field)
            if value is None or value == "":
                errors.append(f"فیلد '{field}' اجباری است و نمی‌تواند خالی باشد.")

        # اعتبارسنجی عنوان
        title = row.get("title")
        if title and str(title).strip():
            if len(str(title).strip()) > 200:
                errors.append("عنوان فرم نباید بیشتر از ۲۰۰ کاراکتر باشد.")

        # اعتبارسنجی نوع فرم
        form_type = row.get("form_type")
        if form_type and str(form_type).strip():
            try:
                FormType(str(form_type).lower())
            except ValueError:
                errors.append(f"نوع فرم '{form_type}' نامعتبر است.")

        # اعتبارسنجی فیلدها (JSON)
        fields_raw = row.get("fields")
        if fields_raw:
            try:
                if isinstance(fields_raw, str):
                    fields_data = json.loads(fields_raw)
                else:
                    fields_data = fields_raw

                if not isinstance(fields_data, list) or len(fields_data) == 0:
                    errors.append("فیلدها باید یک لیست غیرخالی باشند.")

                for f in fields_data:
                    if not isinstance(f, dict):
                        errors.append("هر فیلد باید به‌صورت دیکشنری باشد.")
                        continue
                    if "name" not in f or "label" not in f:
                        errors.append("هر فیلد باید شامل 'name' و 'label' باشد.")
                    if "type" not in f:
                        errors.append("هر فیلد باید دارای 'type' باشد.")

            except json.JSONDecodeError:
                errors.append("فیلد 'fields' باید یک JSON معتبر باشد.")

        # اعتبارسنجی booleanها
        bool_fields = ["is_active", "is_public", "requires_login", "is_multistep"]
        for field in bool_fields:
            value = row.get(field)
            if value is not None and str(value).strip():
                if str(value).lower() not in ("true", "false", "1", "0", "yes", "no"):
                    errors.append(f"فیلد '{field}' باید یک مقدار بولی باشد (true/false).")

        # اعتبارسنجی steps (عدد صحیح مثبت)
        steps = row.get("steps")
        if steps is not None and steps != "":
            try:
                steps_int = int(steps)
                if steps_int < 1:
                    errors.append("تعداد مراحل باید حداقل ۱ باشد.")
            except (ValueError, TypeError):
                errors.append("تعداد مراحل باید یک عدد صحیح باشد.")

        return errors

    async def _create_form_from_row(
        self,
        row: Dict[str, Any],
        default_creator_id: Optional[int] = None,
    ) -> Form:
        """
        ساخت موجودیت فرم از ردیف داده.

        Args:
            row: دیکشنری داده‌های ردیف.
            default_creator_id: شناسه سازنده پیش‌فرض (اختیاری).

        Returns:
            Form: موجودیت فرم.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        # استخراج و تبدیل داده‌ها
        title = row.get("title")
        if not title or not str(title).strip():
            raise ValidationError(
                message="عنوان فرم نمی‌تواند خالی باشد.",
                context={"row": row},
            )

        form_type_str = row.get("form_type")
        if not form_type_str or not str(form_type_str).strip():
            raise ValidationError(
                message="نوع فرم نمی‌تواند خالی باشد.",
                context={"row": row},
            )

        try:
            form_type = FormType(str(form_type_str).lower())
        except ValueError:
            raise ValidationError(
                message=f"نوع فرم '{form_type_str}' نامعتبر است.",
                context={"row": row},
            )

        # پردازش فیلدها
        fields_raw = row.get("fields")
        if not fields_raw:
            raise ValidationError(
                message="فیلدها نمی‌توانند خالی باشند.",
                context={"row": row},
            )

        try:
            if isinstance(fields_raw, str):
                fields_data = json.loads(fields_raw)
            else:
                fields_data = fields_raw

            if not isinstance(fields_data, list) or len(fields_data) == 0:
                raise ValidationError(
                    message="فیلدها باید یک لیست غیرخالی باشند.",
                    context={"row": row},
                )

            fields = []
            for f_data in fields_data:
                if not isinstance(f_data, dict):
                    raise ValidationError(
                        message="هر فیلد باید به‌صورت دیکشنری باشد.",
                        context={"field_data": f_data},
                    )

                # ساخت FormField با استفاده از from_dict
                try:
                    field = FormField.from_dict(f_data)
                    fields.append(field)
                except Exception as e:
                    raise ValidationError(
                        message=f"خطا در ساخت فیلد: {str(e)}",
                        context={"field_data": f_data},
                    )

        except json.JSONDecodeError:
            raise ValidationError(
                message="فیلد 'fields' باید یک JSON معتبر باشد.",
                context={"row": row},
            )

        # پردازش booleanها
        def parse_bool(value: Any) -> bool:
            if value is None:
                return False
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes", "active")

        is_active = parse_bool(row.get("is_active"))
        is_public = parse_bool(row.get("is_public"))
        requires_login = parse_bool(row.get("requires_login"))
        is_multistep = parse_bool(row.get("is_multistep"))

        # پردازش steps
        steps = 1
        steps_raw = row.get("steps")
        if steps_raw is not None and steps_raw != "":
            try:
                steps = int(steps_raw)
                if steps < 1:
                    steps = 1
            except (ValueError, TypeError):
                steps = 1

        # استخراج سازنده
        created_by = default_creator_id

        # ساخت فرم
        form = Form(
            title=str(title).strip(),
            description=str(row.get("description", "")).strip() or None,
            form_type=form_type,
            fields=fields,
            created_by=created_by,
            is_active=is_active,
            is_public=is_public,
            requires_login=requires_login,
            is_multistep=is_multistep,
            steps=steps,
            submit_button_text=row.get("submit_button_text") or "✅ ارسال",
            success_message=str(row.get("success_message", "")).strip() or None,
            redirect_url=str(row.get("redirect_url", "")).strip() or None,
            max_submissions=int(row.get("max_submissions")) if row.get("max_submissions") else None,
            metadata={},
        )

        return form

    def get_required_headers(self) -> List[str]:
        """
        دریافت لیست هدرهای مورد نیاز.

        Returns:
            List[str]: لیست هدرهای مورد نیاز.
        """
        return self.REQUIRED_HEADERS.copy()

    def get_template_headers(self) -> List[str]:
        """
        دریافت لیست هدرهای کامل قالب.

        Returns:
            List[str]: لیست هدرهای قالب.
        """
        return [
            "title",
            "form_type",
            "description",
            "is_active",
            "is_public",
            "requires_login",
            "is_multistep",
            "steps",
            "submit_button_text",
            "success_message",
            "redirect_url",
            "max_submissions",
            "fields",
        ]

    def generate_template(self) -> List[Dict[str, Any]]:
        """
        تولید قالب برای واردات فرم‌ها.

        Returns:
            List[Dict[str, Any]]: یک ردیف نمونه به‌عنوان قالب.
        """
        return [
            {
                "title": "فرم نمونه",
                "form_type": "survey",
                "description": "این یک فرم نمونه برای واردات است.",
                "is_active": "true",
                "is_public": "true",
                "requires_login": "false",
                "is_multistep": "false",
                "steps": "1",
                "submit_button_text": "✅ ارسال",
                "success_message": "با تشکر از شما!",
                "redirect_url": "https://example.com",
                "max_submissions": "100",
                "fields": json.dumps([
                    {
                        "name": "full_name",
                        "label": "نام و نام خانوادگی",
                        "type": "text",
                        "is_required": True,
                        "placeholder": "لطفاً نام خود را وارد کنید",
                    },
                    {
                        "name": "email",
                        "label": "ایمیل",
                        "type": "email",
                        "is_required": True,
                    },
                    {
                        "name": "message",
                        "label": "پیام",
                        "type": "textarea",
                        "is_required": False,
                    },
                    {
                        "name": "rating",
                        "label": "امتیاز",
                        "type": "rating",
                        "is_required": True,
                    },
                ]),
            }
        ]