# my_bot_project/src/my_bot/export/formatters/pdf_formatter.py
"""
فرمت‌کننده خروجی PDF (PDF Formatter).

این کلاس مسئولیت تبدیل داده‌ها به فرمت PDF را بر عهده دارد.
با استفاده از کتابخانه reportlab، فایل‌های PDF با قابلیت تنظیم
استایل، رنگ‌بندی، فونت و جداول حرفه‌ای ایجاد می‌کند.
"""

import io
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class PDFFormatter:
    """
    فرمت‌کننده خروجی PDF.

    این کلاس با استفاده از reportlab، داده‌ها را به‌صورت یک فایل PDF
    با استایل‌دهی مناسب تبدیل می‌کند.

    Attributes:
        page_size: اندازه صفحه (پیش‌فرض A4).
        margin: حاشیه صفحه (پیش‌فرض ۱ سانتی‌متر).
        font_name: نام فونت (پیش‌فرض 'B Nazanin').
        font_size: اندازه فونت (پیش‌فرض ۱۰).
        header_font_size: اندازه فونت هدرها (پیش‌فرض ۱۲).
        title_font_size: اندازه فونت عنوان (پیش‌فرض ۱۶).
        colors: رنگ‌های مورد استفاده.
        header_color: رنگ پس‌زمینه هدرها.
        alternate_row_color: رنگ ردیف‌های زوج.
        title_color: رنگ عنوان.
    """

    def __init__(
        self,
        page_size: tuple = A4,
        margin: float = 1.0 * cm,
        font_name: str = "B Nazanin",
        font_size: int = 10,
        header_font_size: int = 12,
        title_font_size: int = 16,
        header_color: str = "#4472C4",
        alternate_row_color: str = "#F0F0F0",
        title_color: str = "#333333",
    ) -> None:
        """
        مقداردهی اولیه PDFFormatter.

        Args:
            page_size: اندازه صفحه (پیش‌فرض A4).
            margin: حاشیه صفحه بر حسب سانتی‌متر (پیش‌فرض ۱).
            font_name: نام فونت (پیش‌فرض 'B Nazanin').
            font_size: اندازه فونت (پیش‌فرض ۱۰).
            header_font_size: اندازه فونت هدرها (پیش‌فرض ۱۲).
            title_font_size: اندازه فونت عنوان (پیش‌فرض ۱۶).
            header_color: رنگ پس‌زمینه هدرها.
            alternate_row_color: رنگ ردیف‌های زوج.
            title_color: رنگ عنوان.
        """
        self.page_size = page_size
        self.margin = margin
        self.font_name = font_name
        self.font_size = font_size
        self.header_font_size = header_font_size
        self.title_font_size = title_font_size

        # تبدیل رنگ‌های HEX به RGB
        self.header_color = self._hex_to_rgb(header_color)
        self.alternate_row_color = self._hex_to_rgb(alternate_row_color)
        self.title_color = self._hex_to_rgb(title_color)

        # ثبت فونت فارسی (در صورت وجود)
        self._register_fonts()

        # ایجاد استایل‌ها
        self.styles = self._create_styles()

        logger.info(
            f"PDFFormatter initialized: page_size={page_size}, "
            f"font_name={font_name}, font_size={font_size}"
        )

    def _register_fonts(self) -> None:
        """
        ثبت فونت‌های فارسی برای reportlab.

        تلاش می‌کند فونت‌های مختلف را از مسیرهای مختلف بارگذاری کند.
        """
        # لیست فونت‌های احتمالی
        font_paths = [
            "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/Arial.ttf",
        ]

        # برای فونت فارسی، از فونت پیش‌فرض reportlab استفاده می‌کنیم
        # اما اگر فونت فارسی در دسترس باشد، ثبت می‌کنیم
        try:
            # تلاش برای بارگذاری فونت فارسی (در صورت وجود)
            # در سیستم‌های لینوکسی، ممکن است فونت‌های فارسی وجود داشته باشند
            import os
            if os.path.exists("/usr/share/fonts/truetype/ttf-irannastaliq/irannastaliq.ttf"):
                pdfmetrics.registerFont(TTFont('IranNastaliq', '/usr/share/fonts/truetype/ttf-irannastaliq/irannastaliq.ttf'))
                self.font_name = 'IranNastaliq'
            elif os.path.exists("/System/Library/Fonts/Supplemental/Arial.ttf"):
                pdfmetrics.registerFont(TTFont('Arial', '/System/Library/Fonts/Supplemental/Arial.ttf'))
                self.font_name = 'Arial'
        except Exception as e:
            logger.debug(f"Could not register Persian font: {e}")

        # ثبت فونت پیش‌فرض
        try:
            # برای سیستم‌هایی که فونت Helvetica دارند
            pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica'))
        except Exception:
            pass

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """
        تبدیل کد رنگ HEX به RGB.

        Args:
            hex_color: کد رنگ HEX (مثلاً '#4472C4').

        Returns:
            tuple: RGB (مقادیر ۰ تا ۱).
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        return (0.5, 0.5, 0.5)  # خاکستری پیش‌فرض

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """
        ایجاد استایل‌های مختلف برای PDF.

        Returns:
            Dict[str, ParagraphStyle]: دیکشنری استایل‌ها.
        """
        styles = getSampleStyleSheet()
        custom_styles = {}

        # استایل عنوان
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=self.title_font_size,
            textColor=self.title_color,
            alignment=1,  # مرکز
            spaceAfter=12,
        )
        custom_styles['title'] = title_style

        # استایل هدر
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontName=self.font_name,
            fontSize=self.header_font_size,
            textColor=colors.white,
            alignment=0,  # چپ
            spaceAfter=6,
        )
        custom_styles['header'] = header_style

        # استایل متن معمولی
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=self.font_size,
            alignment=0,
            spaceAfter=4,
        )
        custom_styles['normal'] = normal_style

        # استایل متن برای سلول‌های جدول
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=self.font_size,
            alignment=0,
            spaceAfter=2,
        )
        custom_styles['cell'] = cell_style

        return custom_styles

    async def format_table(
        self,
        title: str,
        headers: List[str],
        rows: List[Dict[str, Any]],
        include_index: bool = True,
        landscape_mode: bool = False,
    ) -> bytes:
        """
        تبدیل داده‌های جدول به فایل PDF.

        Args:
            title: عنوان جدول.
            headers: لیست هدرها.
            rows: لیست دیکشنری‌های داده.
            include_index: شامل ستون شماره ردیف (پیش‌فرض True).
            landscape_mode: حالت افقی (پیش‌فرض False).

        Returns:
            bytes: محتوای فایل PDF.

        Raises:
            ValueError: اگر داده‌ها خالی باشند.
        """
        if not rows:
            logger.warning("No data provided for PDF table export.")
            return self.create_empty_pdf("هیچ داده‌ای برای خروجی وجود ندارد.")

        # انتخاب اندازه صفحه
        page_size = landscape(self.page_size) if landscape_mode else self.page_size

        # ایجاد PDF در حافظه
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # ساختار محتوا
        story = []

        # عنوان
        title_paragraph = Paragraph(title, self.styles['title'])
        story.append(title_paragraph)
        story.append(Spacer(1, 0.3 * inch))

        # تاریخ
        date_str = f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        date_paragraph = Paragraph(date_str, self.styles['normal'])
        story.append(date_paragraph)
        story.append(Spacer(1, 0.2 * inch))

        # ساخت داده‌های جدول
        table_data = []

        # هدرها
        header_row = []
        if include_index:
            header_row.append("ردیف")
        header_row.extend(headers)
        table_data.append(header_row)

        # ردیف‌های داده
        for idx, row in enumerate(rows, start=1):
            data_row = []
            if include_index:
                data_row.append(str(idx))

            for header in headers:
                value = row.get(header, "")
                if value is None:
                    value = ""
                # تبدیل به رشته و حذف کاراکترهای اضافی
                data_row.append(str(value))

            table_data.append(data_row)

        # ایجاد جدول
        table = Table(table_data, repeatRows=1)

        # استایل جدول
        style = self._create_table_style(len(header_row), len(table_data))
        table.setStyle(style)

        # اضافه کردن جدول به story
        story.append(table)

        # اضافه کردن شماره صفحه
        story.append(Spacer(1, 0.3 * inch))
        page_info = f"صفحه {doc.page} - {datetime.now().strftime('%Y-%m-%d')}"
        page_paragraph = Paragraph(page_info, self.styles['normal'])
        story.append(page_paragraph)

        # ایجاد PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"Error building PDF: {e}")
            raise

        buffer.seek(0)
        return buffer.getvalue()

    async def format_text(
        self,
        title: str,
        content: str,
        landscape_mode: bool = False,
    ) -> bytes:
        """
        تبدیل متن به فایل PDF.

        Args:
            title: عنوان.
            content: محتوای متن.
            landscape_mode: حالت افقی (پیش‌فرض False).

        Returns:
            bytes: محتوای فایل PDF.
        """
        # انتخاب اندازه صفحه
        page_size = landscape(self.page_size) if landscape_mode else self.page_size

        # ایجاد PDF در حافظه
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # ساختار محتوا
        story = []

        # عنوان
        title_paragraph = Paragraph(title, self.styles['title'])
        story.append(title_paragraph)
        story.append(Spacer(1, 0.3 * inch))

        # محتوا
        content_paragraph = Paragraph(content.replace("\n", "<br/>"), self.styles['normal'])
        story.append(content_paragraph)

        # اضافه کردن شماره صفحه
        story.append(Spacer(1, 0.3 * inch))
        page_info = f"صفحه {doc.page} - {datetime.now().strftime('%Y-%m-%d')}"
        page_paragraph = Paragraph(page_info, self.styles['normal'])
        story.append(page_paragraph)

        # ایجاد PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"Error building PDF: {e}")
            raise

        buffer.seek(0)
        return buffer.getvalue()

    async def format_report(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        landscape_mode: bool = False,
    ) -> bytes:
        """
        تبدیل یک گزارش ساختاریافته به فایل PDF.

        Args:
            title: عنوان گزارش.
            sections: لیست بخش‌های گزارش (هر بخش شامل title و content یا data).
            landscape_mode: حالت افقی (پیش‌فرض False).

        Returns:
            bytes: محتوای فایل PDF.
        """
        # انتخاب اندازه صفحه
        page_size = landscape(self.page_size) if landscape_mode else self.page_size

        # ایجاد PDF در حافظه
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # ساختار محتوا
        story = []

        # عنوان اصلی
        title_paragraph = Paragraph(title, self.styles['title'])
        story.append(title_paragraph)
        story.append(Spacer(1, 0.3 * inch))

        # تاریخ
        date_str = f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        date_paragraph = Paragraph(date_str, self.styles['normal'])
        story.append(date_paragraph)
        story.append(Spacer(1, 0.2 * inch))

        for section in sections:
            section_title = section.get("title", "")
            section_content = section.get("content")
            section_data = section.get("data")
            section_headers = section.get("headers")

            # عنوان بخش
            if section_title:
                header_paragraph = Paragraph(section_title, self.styles['header'])
                story.append(header_paragraph)

            # اگر محتوا وجود دارد
            if section_content:
                content_paragraph = Paragraph(
                    section_content.replace("\n", "<br/>"),
                    self.styles['normal'],
                )
                story.append(content_paragraph)

            # اگر داده‌های جدول وجود دارد
            if section_data and section_headers:
                table_data = [section_headers]
                for row in section_data:
                    if isinstance(row, dict):
                        row_data = [str(row.get(h, "")) for h in section_headers]
                    else:
                        row_data = [str(v) for v in row]
                    table_data.append(row_data)

                if len(table_data) > 1:
                    table = Table(table_data, repeatRows=1)
                    style = self._create_table_style(len(section_headers), len(table_data))
                    table.setStyle(style)
                    story.append(table)

            story.append(Spacer(1, 0.2 * inch))

        # شماره صفحه
        story.append(Spacer(1, 0.3 * inch))
        page_info = f"صفحه {doc.page} - {datetime.now().strftime('%Y-%m-%d')}"
        page_paragraph = Paragraph(page_info, self.styles['normal'])
        story.append(page_paragraph)

        # ایجاد PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"Error building PDF: {e}")
            raise

        buffer.seek(0)
        return buffer.getvalue()

    def _create_table_style(self, num_columns: int, num_rows: int) -> TableStyle:
        """
        ایجاد استایل برای جدول.

        Args:
            num_columns: تعداد ستون‌ها.
            num_rows: تعداد ردیف‌ها.

        Returns:
            TableStyle: استایل جدول.
        """
        style = TableStyle([
            # حاشیه کلی
            ('BOX', (0, 0), (-1, -1), 1, colors.black),

            # استایل هدرها (ردیف اول)
            ('BACKGROUND', (0, 0), (-1, 0), self.header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), self.header_font_size),
            ('BOLD', (0, 0), (-1, 0), 1),

            # استایل سلول‌های داده
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), self.font_size),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # حاشیه داخلی
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

            # رنگ‌آمیزی ردیف‌های زوج
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ])

        # اضافه کردن رنگ ردیف‌های زوج
        for row in range(1, num_rows, 2):
            style.add('BACKGROUND', (0, row), (-1, row), self.alternate_row_color)

        # تنظیم عرض ستون‌ها (به‌طور مساوی)
        col_width = 7.5 * cm / num_columns if num_columns > 0 else 1 * cm
        for col in range(num_columns):
            style.add('COLWIDTH', (col, 0), (col, -1), col_width)

        return style

    def create_empty_pdf(self, message: str = "هیچ داده‌ای برای خروجی وجود ندارد.") -> bytes:
        """
        ایجاد یک فایل PDF خالی با پیام.

        Args:
            message: پیامی که در PDF نمایش داده می‌شود.

        Returns:
            bytes: محتوای فایل PDF.
        """
        # ایجاد PDF در حافظه
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # ساختار محتوا
        story = []

        # عنوان
        title_paragraph = Paragraph("خروجی خالی", self.styles['title'])
        story.append(title_paragraph)
        story.append(Spacer(1, 0.5 * inch))

        # پیام
        message_paragraph = Paragraph(message, self.styles['normal'])
        story.append(message_paragraph)

        # ایجاد PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"Error building empty PDF: {e}")
            # در صورت خطا، یک PDF بسیار ساده ایجاد می‌کنیم
            buffer.seek(0)
            return self._create_simple_empty_pdf(message)

        buffer.seek(0)
        return buffer.getvalue()

    def _create_simple_empty_pdf(self, message: str) -> bytes:
        """
        ایجاد یک PDF خالی با استفاده از canvas (بدون reportlab platypus).

        Args:
            message: پیام.

        Returns:
            bytes: محتوای فایل PDF.
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=self.page_size)
        c.drawString(1 * inch, 5 * inch, message)
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    def set_font(self, font_name: str) -> None:
        """
        تنظیم فونت.

        Args:
            font_name: نام فونت.
        """
        self.font_name = font_name
        self.styles = self._create_styles()

    def set_colors(
        self,
        header_color: Optional[str] = None,
        alternate_row_color: Optional[str] = None,
        title_color: Optional[str] = None,
    ) -> None:
        """
        تنظیم رنگ‌ها.

        Args:
            header_color: رنگ پس‌زمینه هدرها.
            alternate_row_color: رنگ ردیف‌های زوج.
            title_color: رنگ عنوان.
        """
        if header_color:
            self.header_color = self._hex_to_rgb(header_color)
        if alternate_row_color:
            self.alternate_row_color = self._hex_to_rgb(alternate_row_color)
        if title_color:
            self.title_color = self._hex_to_rgb(title_color)

        # بازسازی استایل‌ها
        self.styles = self._create_styles()