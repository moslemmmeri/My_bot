# my_bot_project/src/my_bot/export/exporters/analytics_exporter.py
"""
خروجی‌گیرنده تحلیل‌ها و آمار (Analytics Exporter).

این کلاس مسئولیت خروجی‌گیری از تحلیل‌ها، آمار و گزارش‌های سیستم
در فرمت‌های مختلف (Excel, CSV, JSON, PDF) را بر عهده دارد.
"""

import json
import csv
from io import StringIO
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.repositories.user_repository import UserRepository
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.export.formatters.excel_formatter import ExcelFormatter
from my_bot.export.formatters.pdf_formatter import PDFFormatter

logger = get_logger(__name__)


class AnalyticsExporter:
    """
    خروجی‌گیرنده تحلیل‌ها و آمار.

    این کلاس با استفاده از ریپازیتوری‌های مختلف، داده‌های آماری را دریافت
    کرده و در فرمت‌های مختلف خروجی می‌دهد.

    Attributes:
        order_repository: ریپازیتوری سفارش.
        user_repository: ریپازیتوری کاربر.
        payment_repository: ریپازیتوری پرداخت.
        form_repository: ریپازیتوری فرم.
        excel_formatter: فرمت‌کننده اکسل.
        pdf_formatter: فرمت‌کننده PDF.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        payment_repository: Optional[PaymentRepository] = None,
        form_repository: Optional[FormRepository] = None,
        excel_formatter: Optional[ExcelFormatter] = None,
        pdf_formatter: Optional[PDFFormatter] = None,
    ) -> None:
        """
        مقداردهی اولیه AnalyticsExporter.

        Args:
            order_repository: ریپازیتوری سفارش.
            user_repository: ریپازیتوری کاربر.
            payment_repository: ریپازیتوری پرداخت (اختیاری).
            form_repository: ریپازیتوری فرم (اختیاری).
            excel_formatter: فرمت‌کننده اکسل (در صورت None، نمونه جدید ایجاد می‌شود).
            pdf_formatter: فرمت‌کننده PDF (در صورت None، نمونه جدید ایجاد می‌شود).
        """
        self._order_repository = order_repository
        self._user_repository = user_repository
        self._payment_repository = payment_repository
        self._form_repository = form_repository
        self._excel_formatter = excel_formatter or ExcelFormatter()
        self._pdf_formatter = pdf_formatter or PDFFormatter()

        logger.info("AnalyticsExporter initialized.")

    async def export_analytics(
        self,
        format_type: str = "excel",
        report_type: str = "summary",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_details: bool = False,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از تحلیل‌ها و آمار.

        Args:
            format_type: نوع خروجی ('excel', 'csv', 'json', 'pdf').
            report_type: نوع گزارش ('summary', 'detailed', 'orders', 'users', 'payments').
            date_from: تاریخ شروع (اختیاری).
            date_to: تاریخ پایان (اختیاری).
            include_details: شامل جزئیات بیشتر (پیش‌فرض False).

        Returns:
            Union[bytes, str]: محتوای خروجی.

        Raises:
            ValidationError: اگر نوع خروجی یا گزارش نامعتبر باشد.
            DatabaseError: در صورت بروز خطا در دریافت داده‌ها.
        """
        logger.info(f"Exporting analytics report: type={report_type}, format={format_type}")

        try:
            # دریافت داده‌های تحلیلی
            analytics_data = await self._get_analytics_data(report_type, date_from, date_to, include_details)

            if not analytics_data:
                logger.warning("No analytics data found.")
                return self._get_empty_export(format_type)

            # خروجی‌گیری در فرمت مورد نظر
            if format_type == "excel":
                return await self._export_to_excel(analytics_data, report_type)
            elif format_type == "csv":
                return await self._export_to_csv(analytics_data)
            elif format_type == "json":
                return await self._export_to_json(analytics_data)
            elif format_type == "pdf":
                return await self._export_to_pdf(analytics_data, report_type)
            else:
                raise ValidationError(
                    message=f"نوع خروجی '{format_type}' پشتیبانی نمی‌شود.",
                    context={"format_type": format_type, "supported": ["excel", "csv", "json", "pdf"]},
                )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            raise DatabaseError(
                message=f"خطا در خروجی‌گیری تحلیل‌ها: {str(e)}",
                context={"report_type": report_type, "format": format_type, "error": str(e)},
            )

    async def export_dashboard_report(
        self,
        format_type: str = "pdf",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Union[bytes, str]:
        """
        خروجی‌گیری از داشبورد مدیریتی.

        Args:
            format_type: نوع خروجی.
            date_from: تاریخ شروع (اختیاری).
            date_to: تاریخ پایان (اختیاری).

        Returns:
            Union[bytes, str]: محتوای خروجی.
        """
        logger.info("Exporting dashboard report")

        return await self.export_analytics(
            format_type=format_type,
            report_type="dashboard",
            date_from=date_from,
            date_to=date_to,
            include_details=True,
        )

    async def _get_analytics_data(
        self,
        report_type: str,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        include_details: bool,
    ) -> Dict[str, Any]:
        """
        دریافت داده‌های تحلیلی.

        Args:
            report_type: نوع گزارش.
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.
            include_details: شامل جزئیات.

        Returns:
            Dict[str, Any]: داده‌های تحلیلی.

        Raises:
            ValidationError: اگر نوع گزارش نامعتبر باشد.
        """
        if report_type == "summary":
            return await self._get_summary_report(date_from, date_to)
        elif report_type == "detailed":
            return await self._get_detailed_report(date_from, date_to, include_details)
        elif report_type == "orders":
            return await self._get_orders_report(date_from, date_to, include_details)
        elif report_type == "users":
            return await self._get_users_report(date_from, date_to, include_details)
        elif report_type == "payments":
            return await self._get_payments_report(date_from, date_to, include_details)
        elif report_type == "dashboard":
            return await self._get_dashboard_data(date_from, date_to)
        else:
            raise ValidationError(
                message=f"نوع گزارش '{report_type}' پشتیبانی نمی‌شود.",
                context={"report_type": report_type, "supported": ["summary", "detailed", "orders", "users", "payments", "dashboard"]},
            )

    async def _get_summary_report(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ) -> Dict[str, Any]:
        """
        دریافت گزارش خلاصه.

        Args:
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.

        Returns:
            Dict[str, Any]: داده‌های خلاصه.
        """
        # دریافت آمار از ریپازیتوری‌ها
        order_stats = await self._order_repository.get_statistics(date_from, date_to)

        user_stats = {}
        if self._user_repository:
            # برای سادگی، یک متد get_statistics در UserRepository فرض می‌کنیم
            # در صورت عدم وجود، از روش‌های دیگر استفاده می‌کنیم
            try:
                user_stats = await self._user_repository.get_statistics()
            except AttributeError:
                # اگر متد وجود نداشت، به‌صورت دستی آمار را جمع‌آوری می‌کنیم
                users = await self._user_repository.get_all(skip=0, limit=10000)
                user_stats = {
                    "total_users": len(users),
                    "active_users": sum(1 for u in users if u.is_active and not u.is_banned),
                    "banned_users": sum(1 for u in users if u.is_banned),
                    "users_by_role": {},
                    "users_by_level": {},
                }
                for user in users:
                    user_stats["users_by_role"][user.role.value] = user_stats["users_by_role"].get(user.role.value, 0) + 1
                    user_stats["users_by_level"][user.level.value] = user_stats["users_by_level"].get(user.level.value, 0) + 1

        payment_stats = {}
        if self._payment_repository:
            payment_stats = await self._payment_repository.get_statistics(date_from, date_to)

        form_stats = {}
        if self._form_repository:
            form_stats = await self._form_repository.get_statistics()

        # ترکیب داده‌ها
        return {
            "report_type": "summary",
            "period": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "orders": order_stats,
            "users": user_stats,
            "payments": payment_stats,
            "forms": form_stats,
        }

    async def _get_detailed_report(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        include_details: bool,
    ) -> Dict[str, Any]:
        """
        دریافت گزارش دقیق.

        Args:
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.
            include_details: شامل جزئیات.

        Returns:
            Dict[str, Any]: داده‌های دقیق.
        """
        # شروع با گزارش خلاصه
        data = await self._get_summary_report(date_from, date_to)

        if include_details:
            # افزودن جزئیات سفارشات
            orders = await self._order_repository.get_orders_by_date_range(
                start_date=date_from or datetime.min,
                end_date=date_to or datetime.now(),
                skip=0,
                limit=10000,
            )
            data["orders_details"] = [
                {
                    "order_number": o.order_number,
                    "total_amount": float(o.total_amount.amount),
                    "status": o.status.value,
                    "created_at": o.created_at.isoformat(),
                    "user_id": o.user_id,
                    "items_count": len(o.items),
                }
                for o in orders
            ]

            # افزودن جزئیات کاربران (در صورت امکان)
            if self._user_repository:
                users = await self._user_repository.get_all(skip=0, limit=10000)
                data["users_details"] = [
                    {
                        "id": u.id,
                        "username": u.username,
                        "role": u.role.value,
                        "level": u.level.value,
                        "is_active": u.is_active,
                        "created_at": u.created_at.isoformat(),
                    }
                    for u in users[:1000]  # محدود کردن برای جلوگیری از حجم بالا
                ]

        return data

    async def _get_orders_report(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        include_details: bool,
    ) -> Dict[str, Any]:
        """
        دریافت گزارش سفارشات.

        Args:
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.
            include_details: شامل جزئیات.

        Returns:
            Dict[str, Any]: داده‌های سفارشات.
        """
        orders = await self._order_repository.get_orders_by_date_range(
            start_date=date_from or datetime.min,
            end_date=date_to or datetime.now(),
            skip=0,
            limit=10000,
        )

        # آمار سفارشات
        total_orders = len(orders)
        total_revenue = sum(float(o.total_amount.amount) for o in orders if o.status.value in ["paid", "processing", "shipped", "delivered"])
        status_counts = {}
        for order in orders:
            status = order.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        data = {
            "report_type": "orders",
            "period": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": total_revenue / total_orders if total_orders > 0 else 0,
            "status_counts": status_counts,
        }

        if include_details:
            data["orders"] = [
                {
                    "order_number": o.order_number,
                    "total_amount": float(o.total_amount.amount),
                    "status": o.status.value,
                    "created_at": o.created_at.isoformat(),
                    "user_id": o.user_id,
                    "items_count": len(o.items),
                }
                for o in orders[:1000]  # محدود کردن
            ]

        return data

    async def _get_users_report(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        include_details: bool,
    ) -> Dict[str, Any]:
        """
        دریافت گزارش کاربران.

        Args:
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.
            include_details: شامل جزئیات.

        Returns:
            Dict[str, Any]: داده‌های کاربران.
        """
        if not self._user_repository:
            return {"report_type": "users", "error": "User repository not available"}

        # دریافت کاربران
        users = await self._user_repository.get_all(skip=0, limit=10000)

        # فیلتر بر اساس تاریخ (در صورت وجود)
        if date_from or date_to:
            filtered_users = []
            for user in users:
                if date_from and user.created_at < date_from:
                    continue
                if date_to and user.created_at > date_to:
                    continue
                filtered_users.append(user)
            users = filtered_users

        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active and not u.is_banned)
        banned_users = sum(1 for u in users if u.is_banned)

        role_counts = {}
        level_counts = {}
        for user in users:
            role_counts[user.role.value] = role_counts.get(user.role.value, 0) + 1
            level_counts[user.level.value] = level_counts.get(user.level.value, 0) + 1

        data = {
            "report_type": "users",
            "period": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "roles": role_counts,
            "levels": level_counts,
        }

        if include_details:
            data["users"] = [
                {
                    "id": u.id,
                    "username": u.username,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "role": u.role.value,
                    "level": u.level.value,
                    "points": u.points,
                    "is_active": u.is_active,
                    "is_banned": u.is_banned,
                    "created_at": u.created_at.isoformat(),
                }
                for u in users[:1000]
            ]

        return data

    async def _get_payments_report(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        include_details: bool,
    ) -> Dict[str, Any]:
        """
        دریافت گزارش پرداخت‌ها.

        Args:
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.
            include_details: شامل جزئیات.

        Returns:
            Dict[str, Any]: داده‌های پرداخت‌ها.
        """
        if not self._payment_repository:
            return {"report_type": "payments", "error": "Payment repository not available"}

        payments = await self._payment_repository.get_payments_by_date_range(
            start_date=date_from or datetime.min,
            end_date=date_to or datetime.now(),
            skip=0,
            limit=10000,
        )

        total_payments = len(payments)
        successful_payments = sum(1 for p in payments if p.status.value == "success")
        failed_payments = sum(1 for p in payments if p.status.value == "failed")
        total_amount = sum(float(p.amount.amount) for p in payments if p.status.value == "success")

        gateway_counts = {}
        for p in payments:
            gateway = p.gateway
            gateway_counts[gateway] = gateway_counts.get(gateway, 0) + 1

        data = {
            "report_type": "payments",
            "period": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "total_amount": total_amount,
            "gateway_counts": gateway_counts,
        }

        if include_details:
            data["payments"] = [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "amount": float(p.amount.amount),
                    "status": p.status.value,
                    "gateway": p.gateway,
                    "created_at": p.created_at.isoformat(),
                }
                for p in payments[:1000]
            ]

        return data

    async def _get_dashboard_data(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ) -> Dict[str, Any]:
        """
        دریافت داده‌های داشبورد.

        Args:
            date_from: تاریخ شروع.
            date_to: تاریخ پایان.

        Returns:
            Dict[str, Any]: داده‌های داشبورد.
        """
        # دریافت خلاصه آمار
        summary = await self._get_summary_report(date_from, date_to)

        # دریافت داده‌های روزانه (برای نمودارها)
        daily_stats = []
        if date_from and date_to:
            current = date_from
            while current <= date_to:
                next_day = current + timedelta(days=1)
                orders_day = await self._order_repository.get_orders_by_date_range(
                    start_date=current,
                    end_date=next_day,
                    skip=0,
                    limit=10000,
                )
                daily_stats.append({
                    "date": current.isoformat(),
                    "orders_count": len(orders_day),
                    "revenue": sum(float(o.total_amount.amount) for o in orders_day if o.status.value in ["paid", "processing", "shipped", "delivered"]),
                })
                current = next_day

        # دریافت محصولات پرفروش
        top_products = []
        if self._order_repository:
            top_products = await self._order_repository.get_top_products(limit=10, start_date=date_from, end_date=date_to)

        return {
            "report_type": "dashboard",
            "period": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "summary": summary,
            "daily_stats": daily_stats,
            "top_products": top_products,
        }

    async def _export_to_excel(self, data: Dict[str, Any], report_type: str) -> bytes:
        """
        خروجی‌گیری به فرمت Excel.

        Args:
            data: داده‌ها.
            report_type: نوع گزارش.

        Returns:
            bytes: محتوای فایل Excel.
        """
        # تبدیل داده‌ها به فرمت مناسب برای Excel
        # برای گزارش‌های مختلف، چندین شیت ایجاد می‌کنیم
        # اینجا یک پیاده‌سازی ساده داریم که فقط یک شیت اصلی ایجاد می‌کند
        # در نسخه کامل، می‌توان شیت‌های جداگانه برای هر بخش ایجاد کرد

        # اگر داده‌ها شامل لیست هستند، آنها را به شیت اضافه می‌کنیم
        if "orders" in data and data["orders"]:
            return await self._excel_formatter.format_data(data["orders"], "سفارشات")

        if "users" in data and data["users"]:
            return await self._excel_formatter.format_data(data["users"], "کاربران")

        if "payments" in data and data["payments"]:
            return await self._excel_formatter.format_data(data["payments"], "پرداخت‌ها")

        # اگر داده‌ها دیکشنری هستند، آنها را به یک لیست تک‌ردیفی تبدیل می‌کنیم
        flat_data = [data]
        return await self._excel_formatter.format_data(flat_data, f"گزارش_{report_type}")

    async def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """
        خروجی‌گیری به فرمت CSV.

        Args:
            data: داده‌ها.

        Returns:
            str: محتوای CSV.
        """
        # ساده‌سازی: فقط داده‌های خلاصه را به CSV تبدیل می‌کنیم
        # در نسخه کامل، می‌توان چندین CSV جداگانه تولید کرد
        flat_data = [data]
        headers = list(data.keys())
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, encoding="utf-8-sig")
        writer.writeheader()
        writer.writerows(flat_data)
        return output.getvalue()

    async def _export_to_json(self, data: Dict[str, Any]) -> str:
        """
        خروجی‌گیری به فرمت JSON.

        Args:
            data: داده‌ها.

        Returns:
            str: محتوای JSON.
        """
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    async def _export_to_pdf(self, data: Dict[str, Any], report_type: str) -> bytes:
        """
        خروجی‌گیری به فرمت PDF.

        Args:
            data: داده‌ها.
            report_type: نوع گزارش.

        Returns:
            bytes: محتوای فایل PDF.
        """
        # ساده‌سازی: داده‌ها را به‌صورت یک جدول ساده PDF خروجی می‌دهیم
        # اگر داده‌ها شامل لیست هستند
        if "orders" in data and data["orders"]:
            headers = list(data["orders"][0].keys()) if data["orders"] else []
            rows = data["orders"]
            return await self._pdf_formatter.format_table(
                title=f"گزارش {report_type} - سفارشات",
                headers=headers,
                rows=rows,
            )
        elif "users" in data and data["users"]:
            headers = list(data["users"][0].keys()) if data["users"] else []
            rows = data["users"]
            return await self._pdf_formatter.format_table(
                title=f"گزارش {report_type} - کاربران",
                headers=headers,
                rows=rows,
            )
        elif "payments" in data and data["payments"]:
            headers = list(data["payments"][0].keys()) if data["payments"] else []
            rows = data["payments"]
            return await self._pdf_formatter.format_table(
                title=f"گزارش {report_type} - پرداخت‌ها",
                headers=headers,
                rows=rows,
            )
        else:
            # داده‌های خلاصه را به‌صورت متن ساده PDF می‌دهیم
            lines = []
            for key, value in data.items():
                if not isinstance(value, (dict, list)):
                    lines.append(f"{key}: {value}")
            return await self._pdf_formatter.format_text(
                title=f"گزارش {report_type}",
                content="\n".join(lines),
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
            return "{}"
        elif format_type == "pdf":
            return self._pdf_formatter.create_empty_pdf("هیچ داده‌ای برای خروجی وجود ندارد.")
        else:
            return ""

    def get_report_types(self) -> List[str]:
        """
        دریافت لیست انواع گزارش‌های قابل خروجی‌گیری.

        Returns:
            List[str]: لیست انواع گزارش.
        """
        return ["summary", "detailed", "orders", "users", "payments", "dashboard"]

    def get_supported_formats(self) -> List[str]:
        """
        دریافت لیست فرمت‌های پشتیبانی‌شده.

        Returns:
            List[str]: لیست فرمت‌ها.
        """
        return ["excel", "csv", "json", "pdf"]