# my_bot_project/src/my_bot/export/exporters/order_exporter.py
"""
خروجی‌گیرنده سفارشات (Order Exporter).

این کلاس مسئولیت خروجی‌گیری از اطلاعات سفارشات در فرمت‌های مختلف
(Excel, CSV, JSON, PDF) را بر عهده دارد.
"""

import json
import csv
from io import StringIO
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.constants.order_statuses import OrderStatus
from my_bot.domain.entities.order import Order
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.value_objects.money import Money
from my_bot.export.formatters.excel_formatter import ExcelFormatter
from my_bot.export.formatters.pdf_formatter import PDFFormatter

logger = get_logger(__name__)


class OrderExporter:
    """
    خروجی‌گیرنده سفارشات.

    این کلاس با استفاده از OrderRepository، داده‌های سفارشات را دریافت
    کرده و در فرمت‌های مختلف خروجی می‌دهد.

    Attributes:
        order_repository: ریپازیتوری سفارش.
        excel_formatter: فرمت‌کننده اکسل.
        pdf_formatter: فرمت‌کننده PDF.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        excel_formatter: Optional[ExcelFormatter] = None,
        pdf_formatter: Optional[PDFFormatter] = None,
    ) -> None:
        """
        مقداردهی اولیه OrderExporter.

        Args:
            order_repository: ریپازیتوری سفارش.
            excel_formatter: فرمت‌کننده اکسل (در صورت None، نمونه جدید ایجاد می‌شود).
            pdf_formatter: فرمت‌کننده PDF (در صورت None، نمونه جدید ایجاد می‌شود).
        """
        self._order_repository = order_repository
        self._excel_formatter = excel_formatter or ExcelFormatter()
        self._pdf_formatter = pdf_formatter or PDFFormatter()

        logger.info("OrderExporter initialized.")

    async def export_orders(
        self,
        format_type: str = "excel",
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        limit: Optional[int] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از سفارشات.

        Args:
            format_type: نوع خروجی ('excel', 'csv', 'json', 'pdf').
            filters: فیلترهای اعمال‌شده (اختیاری).
            fields: لیست فیلدهای مورد نیاز (اختیاری).
            sort_by: نام فیلد برای مرتب‌سازی (اختیاری).
            sort_desc: مرتب‌سازی نزولی (پیش‌فرض False).
            limit: حداکثر تعداد سفارشات (اختیاری).

        Returns:
            bytes: محتوای فایل خروجی (برای Excel, PDF).
            str: محتوای خروجی (برای CSV, JSON).

        Raises:
            ValidationError: اگر نوع خروجی نامعتبر باشد یا فیلدها نامعتبر باشند.
            DatabaseError: در صورت بروز خطا در دریافت داده‌ها.
        """
        logger.info(f"Exporting orders in format: {format_type}")

        try:
            # دریافت سفارشات
            orders = await self._get_orders(filters, sort_by, sort_desc, limit)

            if not orders:
                logger.warning("No orders found for export.")
                return self._get_empty_export(format_type)

            # تبدیل سفارشات به دیکشنری
            order_data = self._convert_orders_to_dict(orders, fields)

            # خروجی‌گیری در فرمت مورد نظر
            if format_type == "excel":
                return await self._export_to_excel(order_data)
            elif format_type == "csv":
                return await self._export_to_csv(order_data)
            elif format_type == "json":
                return await self._export_to_json(order_data)
            elif format_type == "pdf":
                return await self._export_to_pdf(order_data)
            else:
                raise ValidationError(
                    message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                    context={"format_type": format_type, "supported": ["excel", "csv", "json", "pdf"]},
                )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error exporting orders: {e}")
            raise DatabaseError(
                message=f"خطا در خروجی‌گیری سفارشات: {str(e)}",
                context={"format": format_type, "error": str(e)},
            )

    async def export_order_by_id(
        self,
        order_id: int,
        format_type: str = "json",
        fields: Optional[List[str]] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از یک سفارش خاص با شناسه.

        Args:
            order_id: شناسه سفارش.
            format_type: نوع خروجی.
            fields: لیست فیلدهای مورد نیاز (اختیاری).

        Returns:
            Union[bytes, str]: محتوای خروجی.

        Raises:
            ValidationError: اگر سفارش وجود نداشته باشد یا نوع خروجی نامعتبر باشد.
        """
        logger.info(f"Exporting order with id: {order_id}")

        order = await self._order_repository.get_by_id(order_id)
        if not order:
            raise ValidationError(
                message=f"سفارش با شناسه {order_id} یافت نشد.",
                context={"order_id": order_id},
            )

        order_data = self._convert_orders_to_dict([order], fields)

        if format_type == "json":
            return json.dumps(order_data[0], ensure_ascii=False, indent=2)
        elif format_type == "csv":
            return await self._export_to_csv(order_data)
        elif format_type == "excel":
            return await self._export_to_excel(order_data)
        elif format_type == "pdf":
            return await self._export_to_pdf(order_data)
        else:
            raise ValidationError(
                message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                context={"format_type": format_type},
            )

    async def export_order_by_number(
        self,
        order_number: str,
        format_type: str = "json",
        fields: Optional[List[str]] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از یک سفارش خاص با شماره سفارش.

        Args:
            order_number: شماره سفارش.
            format_type: نوع خروجی.
            fields: لیست فیلدهای مورد نیاز (اختیاری).

        Returns:
            Union[bytes, str]: محتوای خروجی.

        Raises:
            ValidationError: اگر سفارش وجود نداشته باشد.
        """
        logger.info(f"Exporting order with order_number: {order_number}")

        order = await self._order_repository.get_by_order_number(order_number)
        if not order:
            raise ValidationError(
                message=f"سفارش با شماره {order_number} یافت نشد.",
                context={"order_number": order_number},
            )

        order_data = self._convert_orders_to_dict([order], fields)

        if format_type == "json":
            return json.dumps(order_data[0], ensure_ascii=False, indent=2)
        elif format_type == "csv":
            return await self._export_to_csv(order_data)
        elif format_type == "excel":
            return await self._export_to_excel(order_data)
        elif format_type == "pdf":
            return await self._export_to_pdf(order_data)
        else:
            raise ValidationError(
                message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                context={"format_type": format_type},
            )

    async def _get_orders(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        limit: Optional[int] = None,
    ) -> List[Order]:
        """
        دریافت سفارشات با اعمال فیلترها.

        Args:
            filters: فیلترها (اختیاری).
            sort_by: نام فیلد برای مرتب‌سازی (اختیاری).
            sort_desc: مرتب‌سازی نزولی.
            limit: حداکثر تعداد.

        Returns:
            List[Order]: لیست سفارشات.
        """
        # دریافت سفارشات از ریپازیتوری
        orders = await self._order_repository.get_all(
            skip=0,
            limit=limit or 1000,
            order_by=sort_by or "created_at",
            order_desc=sort_desc,
        )

        # اعمال فیلترهای اضافی (در صورت وجود)
        if filters:
            filtered = []
            for order in orders:
                match = True
                for key, value in filters.items():
                    if key == "status" and order.status.value != value:
                        match = False
                        break
                    elif key == "user_id" and order.user_id != value:
                        match = False
                        break
                    elif key == "min_total" and order.total_amount.amount < value:
                        match = False
                        break
                    elif key == "max_total" and order.total_amount.amount > value:
                        match = False
                        break
                    elif key == "date_from" and order.created_at < value:
                        match = False
                        break
                    elif key == "date_to" and order.created_at > value:
                        match = False
                        break
                if match:
                    filtered.append(order)
            return filtered

        return orders

    def _convert_orders_to_dict(
        self,
        orders: List[Order],
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        تبدیل سفارشات به دیکشنری با فیلدهای مشخص.

        Args:
            orders: لیست سفارشات.
            fields: لیست فیلدهای مورد نیاز (اختیاری).

        Returns:
            List[Dict[str, Any]]: لیست دیکشنری‌های سفارشات.
        """
        if not orders:
            return []

        # همه فیلدهای ممکن
        all_fields = [
            "id",
            "user_id",
            "order_number",
            "subtotal",
            "discount_amount",
            "total_amount",
            "currency",
            "coupon_code",
            "status",
            "payment_id",
            "shipping_address",
            "tracking_code",
            "notes",
            "created_at",
            "updated_at",
            "items_count",
            "total_quantity",
        ]

        if not fields:
            fields = all_fields

        result = []
        for order in orders:
            order_dict = order.to_dict()

            # اضافه کردن فیلدهای محاسبه‌شده
            order_dict["items_count"] = len(order.items)
            order_dict["total_quantity"] = sum(item.quantity for item in order.items)

            # فیلتر کردن فیلدها
            filtered_dict = {}
            for field in fields:
                if field in order_dict:
                    filtered_dict[field] = order_dict[field]

            # تبدیل enum status به نمایش مناسب
            if "status" in filtered_dict and filtered_dict["status"]:
                try:
                    status = OrderStatus(filtered_dict["status"])
                    filtered_dict["status_display"] = status.get_display_name()
                    filtered_dict["status_emoji"] = status.get_emoji()
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

        sheet_name = "سفارشات"
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

        headers = list(data[0].keys())
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

        title = "گزارش سفارشات"
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
            return self._excel_formatter.create_empty_workbook()
        elif format_type == "csv":
            return "هیچ داده‌ای برای خروجی وجود ندارد."
        elif format_type == "json":
            return "[]"
        elif format_type == "pdf":
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
            "user_id",
            "order_number",
            "subtotal",
            "discount_amount",
            "total_amount",
            "currency",
            "coupon_code",
            "status",
            "status_display",
            "status_emoji",
            "payment_id",
            "shipping_address",
            "tracking_code",
            "notes",
            "created_at",
            "updated_at",
            "items_count",
            "total_quantity",
        ]

    def get_supported_formats(self) -> List[str]:
        """
        دریافت لیست فرمت‌های پشتیبانی‌شده.

        Returns:
            List[str]: لیست فرمت‌ها.
        """
        return ["excel", "csv", "json", "pdf"]