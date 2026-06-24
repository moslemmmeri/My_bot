# my_bot_project/src/my_bot/export/exporters/user_exporter.py
"""
خروجی‌گیرنده کاربران (User Exporter).

این کلاس مسئولیت خروجی‌گیری از اطلاعات کاربران در فرمت‌های مختلف
(Excel, CSV, JSON, PDF) را بر عهده دارد.
"""

import json
import csv
from io import BytesIO, StringIO
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.user import User
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.value_objects.user_level import UserLevel
from my_bot.core.constants.user_roles import UserRole
from my_bot.export.formatters.excel_formatter import ExcelFormatter
from my_bot.export.formatters.pdf_formatter import PDFFormatter

logger = get_logger(__name__)


class UserExporter:
    """
    خروجی‌گیرنده کاربران.

    این کلاس با استفاده از UserRepository، داده‌های کاربران را دریافت
    کرده و در فرمت‌های مختلف خروجی می‌دهد.

    Attributes:
        user_repository: ریپازیتوری کاربر.
        excel_formatter: فرمت‌کننده اکسل.
        pdf_formatter: فرمت‌کننده PDF.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        excel_formatter: Optional[ExcelFormatter] = None,
        pdf_formatter: Optional[PDFFormatter] = None,
    ) -> None:
        """
        مقداردهی اولیه UserExporter.

        Args:
            user_repository: ریپازیتوری کاربر.
            excel_formatter: فرمت‌کننده اکسل (در صورت None، نمونه جدید ایجاد می‌شود).
            pdf_formatter: فرمت‌کننده PDF (در صورت None، نمونه جدید ایجاد می‌شود).
        """
        self._user_repository = user_repository
        self._excel_formatter = excel_formatter or ExcelFormatter()
        self._pdf_formatter = pdf_formatter or PDFFormatter()

        logger.info("UserExporter initialized.")

    async def export_users(
        self,
        format_type: str = "excel",
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        limit: Optional[int] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از کاربران.

        Args:
            format_type: نوع خروجی ('excel', 'csv', 'json', 'pdf').
            filters: فیلترهای اعمال‌شده (اختیاری).
            fields: لیست فیلدهای مورد نیاز (اختیاری).
            sort_by: نام فیلد برای مرتب‌سازی (اختیاری).
            sort_desc: مرتب‌سازی نزولی (پیش‌فرض False).
            limit: حداکثر تعداد کاربران (اختیاری).

        Returns:
            bytes: محتوای فایل خروجی (برای Excel, PDF).
            str: محتوای خروجی (برای CSV, JSON).

        Raises:
            ValidationError: اگر نوع خروجی نامعتبر باشد یا فیلدها نامعتبر باشند.
            DatabaseError: در صورت بروز خطا در دریافت داده‌ها.
        """
        logger.info(f"Exporting users in format: {format_type}")

        try:
            # دریافت کاربران
            users = await self._get_users(filters, sort_by, sort_desc, limit)

            if not users:
                logger.warning("No users found for export.")
                return self._get_empty_export(format_type)

            # تبدیل کاربران به دیکشنری
            user_data = self._convert_users_to_dict(users, fields)

            # خروجی‌گیری در فرمت مورد نظر
            if format_type == "excel":
                return await self._export_to_excel(user_data)
            elif format_type == "csv":
                return await self._export_to_csv(user_data)
            elif format_type == "json":
                return await self._export_to_json(user_data)
            elif format_type == "pdf":
                return await self._export_to_pdf(user_data)
            else:
                raise ValidationError(
                    message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                    context={"format_type": format_type, "supported": ["excel", "csv", "json", "pdf"]},
                )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error exporting users: {e}")
            raise DatabaseError(
                message=f"خطا در خروجی‌گیری کاربران: {str(e)}",
                context={"format": format_type, "error": str(e)},
            )

    async def export_user_by_id(
        self,
        user_id: int,
        format_type: str = "json",
        fields: Optional[List[str]] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از یک کاربر خاص با شناسه.

        Args:
            user_id: شناسه کاربر.
            format_type: نوع خروجی ('excel', 'csv', 'json', 'pdf').
            fields: لیست فیلدهای مورد نیاز (اختیاری).

        Returns:
            bytes: محتوای فایل خروجی.
            str: محتوای خروجی.

        Raises:
            ValidationError: اگر کاربر وجود نداشته باشد یا نوع خروجی نامعتبر باشد.
        """
        logger.info(f"Exporting user with id: {user_id}")

        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise ValidationError(
                message=f"کاربر با شناسه {user_id} یافت نشد.",
                context={"user_id": user_id},
            )

        user_data = self._convert_users_to_dict([user], fields)

        if format_type == "json":
            return json.dumps(user_data[0], ensure_ascii=False, indent=2)
        elif format_type == "csv":
            return await self._export_to_csv(user_data)
        elif format_type == "excel":
            return await self._export_to_excel(user_data)
        elif format_type == "pdf":
            return await self._export_to_pdf(user_data)
        else:
            raise ValidationError(
                message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                context={"format_type": format_type},
            )

    async def export_user_by_telegram_id(
        self,
        telegram_id: int,
        format_type: str = "json",
        fields: Optional[List[str]] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از یک کاربر خاص با شناسه تلگرام.

        Args:
            telegram_id: شناسه تلگرام کاربر.
            format_type: نوع خروجی.
            fields: لیست فیلدهای مورد نیاز (اختیاری).

        Returns:
            Union[bytes, str]: محتوای خروجی.

        Raises:
            ValidationError: اگر کاربر وجود نداشته باشد.
        """
        logger.info(f"Exporting user with telegram_id: {telegram_id}")

        user = await self._user_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise ValidationError(
                message=f"کاربر با شناسه تلگرام {telegram_id} یافت نشد.",
                context={"telegram_id": telegram_id},
            )

        user_data = self._convert_users_to_dict([user], fields)

        if format_type == "json":
            return json.dumps(user_data[0], ensure_ascii=False, indent=2)
        elif format_type == "csv":
            return await self._export_to_csv(user_data)
        elif format_type == "excel":
            return await self._export_to_excel(user_data)
        elif format_type == "pdf":
            return await self._export_to_pdf(user_data)
        else:
            raise ValidationError(
                message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                context={"format_type": format_type},
            )

    async def _get_users(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        limit: Optional[int] = None,
    ) -> List[User]:
        """
        دریافت کاربران با اعمال فیلترها.

        Args:
            filters: فیلترها (اختیاری).
            sort_by: نام فیلد برای مرتب‌سازی (اختیاری).
            sort_desc: مرتب‌سازی نزولی.
            limit: حداکثر تعداد.

        Returns:
            List[User]: لیست کاربران.
        """
        # اعمال فیلترها و دریافت کاربران
        # در اینجا از روش‌های مختلف ریپازیتوری استفاده می‌کنیم

        # اگر فیلتر مشخصی وجود نداشته باشد، همه کاربران را دریافت می‌کنیم
        if not filters:
            users = await self._user_repository.get_all(
                skip=0,
                limit=limit or 1000,
                order_by=sort_by or "created_at",
                order_desc=sort_desc,
            )
        else:
            # در صورت وجود فیلتر، از متدهای خاص استفاده می‌کنیم
            # یا از count با فیلتر و سپس get_all استفاده می‌کنیم
            users = []
            # اینجا می‌توان فیلترهای مختلف را اعمال کرد
            # برای سادگی، همه کاربران را دریافت کرده و در حافظه فیلتر می‌کنیم
            all_users = await self._user_repository.get_all(
                skip=0,
                limit=limit or 1000,
                order_by=sort_by or "created_at",
                order_desc=sort_desc,
            )

            for user in all_users:
                match = True
                for key, value in filters.items():
                    if key == "role" and user.role.value != value:
                        match = False
                        break
                    elif key == "level" and user.level.value != value:
                        match = False
                        break
                    elif key == "is_active" and user.is_active != value:
                        match = False
                        break
                    elif key == "is_banned" and user.is_banned != value:
                        match = False
                        break
                    elif key == "min_points" and user.points < value:
                        match = False
                        break
                    elif key == "max_points" and user.points > value:
                        match = False
                        break
                    # می‌توان فیلترهای دیگری نیز اضافه کرد
                if match:
                    users.append(user)

        return users

    def _convert_users_to_dict(
        self,
        users: List[User],
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        تبدیل کاربران به دیکشنری با فیلدهای مشخص.

        Args:
            users: لیست کاربران.
            fields: لیست فیلدهای مورد نیاز (اختیاری).

        Returns:
            List[Dict[str, Any]]: لیست دیکشنری‌های کاربران.
        """
        if not users:
            return []

        # همه فیلدهای ممکن
        all_fields = [
            "id",
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "email",
            "role",
            "level",
            "points",
            "is_active",
            "is_banned",
            "last_activity",
            "created_at",
            "updated_at",
        ]

        # اگر فیلد خاصی مشخص نشده، از همه فیلدها استفاده کن
        if not fields:
            fields = all_fields

        result = []
        for user in users:
            user_dict = user.to_dict()

            # فیلتر کردن فیلدها
            filtered_dict = {}
            for field in fields:
                if field in user_dict:
                    filtered_dict[field] = user_dict[field]

            # تبدیل enumها به رشته
            if "role" in filtered_dict and filtered_dict["role"]:
                try:
                    role = UserRole(filtered_dict["role"])
                    filtered_dict["role_display"] = role.get_display_name()
                except ValueError:
                    pass

            if "level" in filtered_dict and filtered_dict["level"]:
                try:
                    level = UserLevel(filtered_dict["level"])
                    filtered_dict["level_display"] = level.display_name
                    filtered_dict["level_emoji"] = level.emoji
                except ValueError:
                    pass

            result.append(filtered_dict)

        return result

    async def _export_to_excel(self, data: List[Dict[str, Any]]) -> bytes:
        """
        خروجی‌گیری به فرمت Excel.

        Args:
            data: لیست دیکشنری‌های داده.

        Returns:
            bytes: محتوای فایل Excel.
        """
        if not data:
            return self._get_empty_export("excel")

        # استفاده از ExcelFormatter
        sheet_name = "کاربران"
        return await self._excel_formatter.format_data(data, sheet_name)

    async def _export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """
        خروجی‌گیری به فرمت CSV.

        Args:
            data: لیست دیکشنری‌های داده.

        Returns:
            str: محتوای CSV.
        """
        if not data:
            return self._get_empty_export("csv")

        # دریافت هدرها
        headers = list(data[0].keys())

        # ایجاد CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, encoding="utf-8-sig")
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    async def _export_to_json(self, data: List[Dict[str, Any]]) -> str:
        """
        خروجی‌گیری به فرمت JSON.

        Args:
            data: لیست دیکشنری‌های داده.

        Returns:
            str: محتوای JSON.
        """
        if not data:
            return "[]"

        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    async def _export_to_pdf(self, data: List[Dict[str, Any]]) -> bytes:
        """
        خروجی‌گیری به فرمت PDF.

        Args:
            data: لیست دیکشنری‌های داده.

        Returns:
            bytes: محتوای فایل PDF.
        """
        if not data:
            return self._get_empty_export("pdf")

        # استفاده از PDFFormatter
        title = "گزارش کاربران"
        headers = list(data[0].keys())
        rows = data

        return await self._pdf_formatter.format_table(
            title=title,
            headers=headers,
            rows=rows,
        )

    def _get_empty_export(self, format_type: str) -> Union[bytes, str]:
        """
        دریافت خروجی خالی برای فرمت مشخص.

        Args:
            format_type: نوع خروجی.

        Returns:
            Union[bytes, str]: خروجی خالی.
        """
        if format_type == "excel":
            # Excel خالی
            return self._excel_formatter.create_empty_workbook()
        elif format_type == "csv":
            return "هیچ داده‌ای برای خروجی وجود ندارد."
        elif format_type == "json":
            return "[]"
        elif format_type == "pdf":
            # PDF خالی
            return self._pdf_formatter.create_empty_pdf("هیچ داده‌ای برای خروجی وجود ندارد.")
        else:
            return ""

    def get_export_fields(self) -> List[str]:
        """
        دریافت لیست فیلدهای قابل خروجی‌گیری.

        Returns:
            List[str]: لیست فیلدها.
        """
        return [
            "id",
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "email",
            "role",
            "role_display",
            "level",
            "level_display",
            "level_emoji",
            "points",
            "is_active",
            "is_banned",
            "last_activity",
            "created_at",
            "updated_at",
        ]

    def get_supported_formats(self) -> List[str]:
        """
        دریافت لیست فرمت‌های پشتیبانی‌شده.

        Returns:
            List[str]: لیست فرمت‌ها.
        """
        return ["excel", "csv", "json", "pdf"]