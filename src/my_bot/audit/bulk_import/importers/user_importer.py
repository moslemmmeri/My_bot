# my_bot_project/src/my_bot/bulk_import/importers/user_importer.py
"""
واردکننده کاربران (User Importer).

این کلاس مسئولیت واردات انبوه کاربران از فایل‌های اکسل یا CSV را بر عهده دارد.
داده‌های وارداتی شامل اطلاعات کاربران مانند نام، نام کاربری، شماره تلفن، ایمیل و غیره است.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from my_bot.bulk_import.parsers.excel_reader import ExcelReader
from my_bot.bulk_import.parsers.csv_reader import CSVReader
from my_bot.bulk_import.validators.row_validator import RowValidator
from my_bot.bulk_import.validators.data_validator import DataValidator
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.not_found_errors import UserNotFoundError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserImporter:
    """
    واردکننده کاربران از فایل‌های اکسل یا CSV.

    این کلاس داده‌های کاربران را از فایل خوانده، اعتبارسنجی کرده
    و در دیتابیس ذخیره می‌کند.

    Attributes:
        user_repository: ریپازیتوری کاربر.
        row_validator: اعتبارسنج ردیف‌ها.
        data_validator: اعتبارسنج داده‌ها.
        default_role: نقش پیش‌فرض برای کاربران جدید (پیش‌فرض: "user").
        default_level: سطح پیش‌فرض برای کاربران جدید (پیش‌فرض: "bronze").
        required_headers: هدرهای مورد نیاز در فایل.
    """

    REQUIRED_HEADERS = ["telegram_id", "first_name"]

    def __init__(
        self,
        user_repository: UserRepository,
        default_role: str = "user",
        default_level: str = "bronze",
    ) -> None:
        """
        مقداردهی اولیه UserImporter.

        Args:
            user_repository: ریپازیتوری کاربر.
            default_role: نقش پیش‌فرض برای کاربران جدید (پیش‌فرض: "user").
            default_level: سطح پیش‌فرض برای کاربران جدید (پیش‌فرض: "bronze").
        """
        self._user_repository = user_repository
        self._row_validator = RowValidator()
        self._data_validator = DataValidator()
        self.default_role = default_role
        self.default_level = default_level

        logger.info(
            f"UserImporter initialized: default_role={default_role}, "
            f"default_level={default_level}"
        )

    async def import_from_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        header_row: int = 1,
        skip_rows: int = 0,
    ) -> Dict[str, Any]:
        """
        واردات کاربران از فایل اکسل.

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
        logger.info(f"Importing users from Excel file: {file_path}")

        # ایجاد ExcelReader
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
        واردات کاربران از محتوای فایل اکسل به‌صورت bytes.

        Args:
            file_content: محتوای فایل اکسل.
            sheet_name: نام شیت (اختیاری).
            header_row: شماره ردیف هدر (پیش‌فرض: ۱).
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند (پیش‌فرض: ۰).

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        logger.info("Importing users from Excel bytes")

        # ایجاد ExcelReader
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
        واردات کاربران از فایل CSV.

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
        logger.info(f"Importing users from CSV file: {file_path}")

        # ایجاد CSVReader
        reader = CSVReader(
            file_path=file_path,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            skip_rows=skip_rows,
        )

        # بارگذاری داده‌ها
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
        واردات کاربران از محتوای فایل CSV به‌صورت bytes.

        Args:
            file_content: محتوای فایل CSV.
            delimiter: جداکننده فیلدها (پیش‌فرض: ',').
            encoding: کدگذاری فایل (اختیاری).
            has_header: آیا فایل دارای هدر است (پیش‌فرض: True).
            skip_rows: تعداد ردیف‌های ابتدایی که نادیده گرفته شوند (پیش‌فرض: ۰).

        Returns:
            Dict[str, Any]: نتیجه واردات.
        """
        logger.info("Importing users from CSV bytes")

        # ایجاد CSVReader
        reader = CSVReader(
            file_content=file_content,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header,
            skip_rows=skip_rows,
        )

        # بارگذاری داده‌ها
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
        # اعتبارسنجی هدرها
        required_headers = self.REQUIRED_HEADERS + ["last_name", "phone_number", "email", "username", "role", "level"]
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
        # اعتبارسنجی هدرها
        required_headers = self.REQUIRED_HEADERS + ["last_name", "phone_number", "email", "username", "role", "level"]
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

                # تبدیل به موجودیت کاربر
                user = self._create_user_from_row(row)

                # ذخیره در دیتابیس
                saved_user = await self._user_repository.save(user)

                logger.debug(f"User imported: telegram_id={saved_user.telegram_id}")
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
            f"User import completed: {imported} imported, "
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

        # اعتبارسنجی telegram_id (باید عدد صحیح مثبت باشد)
        telegram_id = row.get("telegram_id")
        if telegram_id is not None and telegram_id != "":
            try:
                telegram_id_int = int(telegram_id)
                if telegram_id_int <= 0:
                    errors.append("telegram_id باید یک عدد صحیح مثبت باشد.")
            except (ValueError, TypeError):
                errors.append("telegram_id باید یک عدد صحیح باشد.")

        # اعتبارسنجی شماره تلفن (در صورت وجود)
        phone = row.get("phone_number")
        if phone and str(phone).strip():
            try:
                from my_bot.shared.utils.text_validators import validate_phone
                validate_phone(str(phone))
            except ValidationError as e:
                errors.append(str(e))

        # اعتبارسنجی ایمیل (در صورت وجود)
        email = row.get("email")
        if email and str(email).strip():
            try:
                from my_bot.shared.utils.text_validators import validate_email
                validate_email(str(email))
            except ValidationError as e:
                errors.append(str(e))

        # اعتبارسنجی نقش (در صورت وجود)
        role = row.get("role")
        if role and str(role).strip():
            from my_bot.core.constants.user_roles import UserRole
            try:
                UserRole(str(role).lower())
            except ValueError:
                errors.append(f"نقش '{role}' نامعتبر است.")

        # اعتبارسنجی سطح (در صورت وجود)
        level = row.get("level")
        if level and str(level).strip():
            from my_bot.domain.value_objects.user_level import UserLevel
            try:
                UserLevel(str(level).lower())
            except ValueError:
                errors.append(f"سطح '{level}' نامعتبر است.")

        return errors

    def _create_user_from_row(self, row: Dict[str, Any]) -> User:
        """
        ساخت موجودیت کاربر از ردیف داده.

        Args:
            row: دیکشنری داده‌های ردیف.

        Returns:
            User: موجودیت کاربر.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        from my_bot.core.constants.user_roles import UserRole
        from my_bot.domain.value_objects.user_level import UserLevel

        # استخراج و تبدیل داده‌ها
        telegram_id = row.get("telegram_id")
        if telegram_id is None or telegram_id == "":
            raise ValidationError(
                message="telegram_id نمی‌تواند خالی باشد.",
                context={"row": row},
            )

        try:
            telegram_id = int(telegram_id)
        except (ValueError, TypeError):
            raise ValidationError(
                message="telegram_id باید یک عدد صحیح باشد.",
                context={"telegram_id": telegram_id},
            )

        if telegram_id <= 0:
            raise ValidationError(
                message="telegram_id باید یک عدد صحیح مثبت باشد.",
                context={"telegram_id": telegram_id},
            )

        # استخراج سایر فیلدها
        first_name = row.get("first_name")
        if first_name is None or first_name == "":
            raise ValidationError(
                message="first_name نمی‌تواند خالی باشد.",
                context={"row": row},
            )

        # تبدیل نقش و سطح
        role_str = row.get("role")
        role = UserRole.USER
        if role_str:
            try:
                role = UserRole(str(role_str).lower())
            except ValueError:
                # اگر نقش نامعتبر است، از پیش‌فرض استفاده می‌کنیم
                logger.warning(f"Invalid role '{role_str}', using default: {self.default_role}")

        level_str = row.get("level")
        level = UserLevel.BRONZE
        if level_str:
            try:
                level = UserLevel(str(level_str).lower())
            except ValueError:
                # اگر سطح نامعتبر است، از پیش‌فرض استفاده می‌کنیم
                logger.warning(f"Invalid level '{level_str}', using default: {self.default_level}")

        # ساخت کاربر
        user = User(
            telegram_id=telegram_id,
            username=row.get("username") or None,
            first_name=str(first_name).strip(),
            last_name=str(row.get("last_name", "")).strip() or None,
            phone_number=str(row.get("phone_number", "")).strip() or None,
            email=str(row.get("email", "")).strip() or None,
            role=role,
            level=level,
            is_active=True,
            is_banned=False,
        )

        return user

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
            "telegram_id",
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "email",
            "role",
            "level",
        ]

    def generate_template(self) -> List[Dict[str, Any]]:
        """
        تولید قالب برای واردات کاربران.

        Returns:
            List[Dict[str, Any]]: یک ردیف نمونه به‌عنوان قالب.
        """
        return [
            {
                "telegram_id": 123456789,
                "first_name": "علی",
                "last_name": "رضایی",
                "username": "alirezaei",
                "phone_number": "09123456789",
                "email": "ali@example.com",
                "role": "user",
                "level": "bronze",
            }
        ]