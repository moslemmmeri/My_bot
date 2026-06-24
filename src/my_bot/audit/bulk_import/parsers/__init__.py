# my_bot_project/src/my_bot/bulk_import/parsers/__init__.py
"""
ماژول پارسرهای واردات انبوه (Bulk Import Parsers).

این ماژول شامل کلاس‌های خواندن فایل‌های مختلف برای واردات انبوه است:
- ExcelReader: خواندن فایل‌های اکسل (xlsx, xls)
- CSVReader: خواندن فایل‌های CSV با کدگذاری‌های مختلف
"""

from my_bot.bulk_import.parsers.excel_reader import ExcelReader
from my_bot.bulk_import.parsers.csv_reader import CSVReader

__all__ = [
    "ExcelReader",
    "CSVReader",
]