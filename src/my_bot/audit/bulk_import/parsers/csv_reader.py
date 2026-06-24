# my_bot_project/src/my_bot/bulk_import/parsers/csv_reader.py
"""
خواننده فایل‌های CSV (CSV Reader).

این کلاس با استفاده از کتابخانه csv استاندارد پایتون و همچنین pandas (در صورت وجود)،
فایل‌های CSV را با کدگذاری‌های مختلف خوانده و به فرمت مناسب برای واردات انبوه
داده‌ها تبدیل می‌کند.
"""

import csv
import codecs
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Iterator, TextIO
from io import BytesIO, StringIO, TextIOWrapper
import chardet

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class CSVReader:
    """
    خواننده فایل‌های CSV برای واردات انبوه.

    این کلاس با استفاده از کتابخانه csv استاندارد، فایل‌های CSV را
    با کدگذاری‌های مختلف (UTF-8, Windows-1256, ISO-8859-1 و ...) خوانده
    و داده‌ها را به‌صورت لیست دیکشنری یا لیست لیست بازمی‌گرداند.

    Attributes:
        file_path: مسیر فایل CSV (اختیاری).
        file_content: محتوای فایل به‌صورت bytes (اختیاری).
        delimiter: جداکننده فیلدها (پیش‌فرض: ',').
        quotechar: کاراکتر نقل‌قول (پیش‌فرض: '"').
        encoding: کدگذاری فایل (در صورت None، به‌صورت خودکار تشخیص داده می‌شود).
        has_header: آیا فایل دارای ردیف هدر است (پیش‌فرض: True).
        header_row: شماره ردیف هدر (پیش‌فرض: ۰ برای اولین ردیف).
        skip_rows: تعداد ردیف‌های ابتدایی که باید نادیده گرفته شوند (پیش‌فرض: ۰).
        headers: لیست هدرها (در صورت عدم وجود هدر، به‌صورت خودکار تولید می‌شود).
        _data: داده‌های خوانده‌شده (کش).
        _is_loaded: وضعیت بارگذاری فایل.
    """

    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        delimiter: str = ",",
        quotechar: str = '"',
        encoding: Optional[str] = None,
        has_header: bool = True,
        header_row: int = 0,
        skip_rows: int = 0,
    ) -> None:
        """
        مقداردهی اولیه CSVReader.

        Args:
            file_path: مسیر فایل CSV (اختیاری).
            file_content: محتوای فایل به‌صورت bytes (اختیاری).
            delimiter: جداکننده فیلدها (پیش‌فرض: ',').
            quotechar: کاراکتر نقل‌قول (پیش‌فرض: '"').
            encoding: کدگذاری فایل (در صورت None، به‌صورت خودکار تشخیص داده می‌شود).
            has_header: آیا فایل دارای ردیف هدر است (پیش‌فرض: True).
            header_row: شماره ردیف هدر (پیش‌فرض: ۰ برای اولین ردیف).
            skip_rows: تعداد ردیف‌های ابتدایی که باید نادیده گرفته شوند (پیش‌فرض: ۰).

        Raises:
            ValidationError: اگر فایل معتبر نباشد یا قابل خواندن نباشد.
        """
        self.file_path = Path(file_path) if file_path else None
        self.file_content = file_content
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self.has_header = has_header
        self.header_row = header_row
        self.skip_rows = skip_rows
        self.headers: List[str] = []
        self._data: List[Dict[str, Any]] = []
        self._is_loaded = False
        self._detected_encoding: Optional[str] = None

        logger.info(
            f"CSVReader initialized: file_path={file_path}, "
            f"delimiter={delimiter}, encoding={encoding}, has_header={has_header}"
        )

    def _detect_encoding(self, content: bytes) -> str:
        """
        تشخیص کدگذاری فایل با استفاده از chardet.

        Args:
            content: محتوای فایل به‌صورت bytes.

        Returns:
            str: کدگذاری تشخیص‌داده‌شده.

        Raises:
            ValidationError: اگر کدگذاری قابل تشخیص نباشد.
        """
        try:
            result = chardet.detect(content)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)

            # اگر اطمینان کم بود، از UTF-8 استفاده کن
            if confidence < 0.7:
                logger.debug(f"Low confidence ({confidence}) for encoding: {encoding}, using UTF-8")
                encoding = 'utf-8'

            # برخی کدگذاری‌ها را اصلاح می‌کنیم
            if encoding and encoding.lower() == 'ascii':
                encoding = 'utf-8'

            logger.debug(f"Detected encoding: {encoding} (confidence: {confidence})")
            return encoding

        except Exception as e:
            logger.warning(f"Error detecting encoding: {e}, falling back to UTF-8")
            return 'utf-8'

    def _read_file_content(self) -> str:
        """
        خواندن محتوای فایل و تبدیل به رشته با کدگذاری مناسب.

        Returns:
            str: محتوای فایل به‌صورت رشته.

        Raises:
            ValidationError: اگر فایل قابل خواندن نباشد.
        """
        try:
            content = self.file_content
            if content is None:
                # خواندن از مسیر
                if not self.file_path or not self.file_path.exists():
                    raise ValidationError(
                        message="فایل CSV یافت نشد.",
                        context={"file_path": str(self.file_path)},
                    )

                with open(self.file_path, 'rb') as f:
                    content = f.read()

            # تشخیص کدگذاری (در صورت عدم مشخص بودن)
            if self.encoding is None:
                self._detected_encoding = self._detect_encoding(content)
                encoding = self._detected_encoding
            else:
                encoding = self.encoding

            # تلاش برای دیکد کردن با کدگذاری تشخیص‌داده‌شده
            try:
                text = content.decode(encoding)
            except UnicodeDecodeError:
                # اگر با کدگذاری اصلی خطا داد، با UTF-8 امتحان کن
                logger.warning(f"Failed to decode with {encoding}, trying UTF-8")
                try:
                    text = content.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    # اگر باز هم خطا داد، با ISO-8859-1 امتحان کن
                    text = content.decode('iso-8859-1', errors='replace')
                    logger.warning("Used ISO-8859-1 as fallback encoding")

            logger.debug(f"File content read: {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise ValidationError(
                message=f"خطا در خواندن فایل CSV: {str(e)}",
                context={"file_path": str(self.file_path), "error": str(e)},
            )

    def _parse_csv(self, text: str) -> List[List[str]]:
        """
        پارس کردن محتوای CSV با استفاده از csv.reader.

        Args:
            text: محتوای فایل به‌صورت رشته.

        Returns:
            List[List[str]]: داده‌های CSV به‌صورت لیست لیست.

        Raises:
            ValidationError: اگر داده‌ها قابل پارس نباشند.
        """
        try:
            # استفاده از csv.reader با تنظیمات مشخص
            reader = csv.reader(
                StringIO(text),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                quoting=csv.QUOTE_MINIMAL,
            )

            rows = []
            for row in reader:
                rows.append(row)

            logger.debug(f"Parsed {len(rows)} rows from CSV")
            return rows

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValidationError(
                message=f"خطا در پارس کردن فایل CSV: {str(e)}",
                context={"error": str(e)},
            )

    def _extract_headers(self, rows: List[List[str]]) -> List[str]:
        """
        استخراج هدرها از داده‌ها.

        Args:
            rows: داده‌های CSV.

        Returns:
            List[str]: لیست هدرها.

        Raises:
            ValidationError: اگر هدرها معتبر نباشند.
        """
        if not rows:
            raise ValidationError(
                message="فایل CSV خالی است.",
                context={},
            )

        if self.has_header and len(rows) > self.header_row:
            # استفاده از ردیف هدر
            header_row = rows[self.header_row]
            headers = [str(col).strip() if col else f"col_{i+1}" for i, col in enumerate(header_row)]

            # اگر هدرها خالی یا نامعتبر هستند، به‌صورت خودکار تولید می‌کنیم
            if not headers or all(h == "" or h == f"col_{i+1}" for i, h in enumerate(headers)):
                logger.warning("Headers are empty or invalid, generating auto headers")
                headers = [f"col_{i+1}" for i in range(len(header_row))]

        else:
            # اگر هدر وجود ندارد، به‌صورت خودکار تولید می‌کنیم
            max_cols = max((len(row) for row in rows), default=0)
            headers = [f"col_{i+1}" for i in range(max_cols)]

        logger.debug(f"Headers extracted: {len(headers)} columns")
        return headers

    def _convert_rows_to_dict(
        self,
        rows: List[List[str]],
        headers: List[str],
        start_row: int,
    ) -> List[Dict[str, Any]]:
        """
        تبدیل ردیف‌ها به دیکشنری با استفاده از هدرها.

        Args:
            rows: داده‌های CSV.
            headers: لیست هدرها.
            start_row: ردیف شروع برای داده‌ها.

        Returns:
            List[Dict[str, Any]]: داده‌ها به‌صورت دیکشنری.
        """
        data = []

        for row in rows[start_row:]:
            # اگر ردیف خالی است یا همه ستون‌ها None هستند، نادیده بگیر
            if not row or all(col is None or col == '' for col in row):
                continue

            row_dict = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else ''
                row_dict[header] = self._convert_value(value)

            data.append(row_dict)

        return data

    def _convert_value(self, value: str) -> Any:
        """
        تبدیل مقدار رشته به نوع مناسب.

        Args:
            value: مقدار رشته.

        Returns:
            Any: مقدار تبدیل‌شده.
        """
        if not value or value.strip() == '':
            return None

        value = value.strip()

        # تبدیل به عدد صحیح
        try:
            if value.isdigit():
                return int(value)
        except (ValueError, AttributeError):
            pass

        # تبدیل به عدد اعشاری
        try:
            if '.' in value:
                return float(value)
        except (ValueError, AttributeError):
            pass

        # تبدیل به بولی
        if value.lower() in ('true', 'yes', 'y', '1'):
            return True
        if value.lower() in ('false', 'no', 'n', '0'):
            return False

        # باقی موارد به‌صورت رشته
        return value

    def load(self) -> None:
        """
        بارگذاری فایل CSV و پارس کردن داده‌ها.

        Raises:
            ValidationError: اگر فایل قابل بارگذاری نباشد.
        """
        try:
            # خواندن محتوا
            text = self._read_file_content()

            # پارس کردن CSV
            rows = self._parse_csv(text)

            # استخراج هدرها
            self.headers = self._extract_headers(rows)

            # تعیین ردیف شروع برای داده‌ها
            start_row = self.header_row + 1 if self.has_header else 0
            start_row = max(start_row, self.skip_rows)

            # تبدیل به دیکشنری
            self._data = self._convert_rows_to_dict(rows, self.headers, start_row)

            self._is_loaded = True
            logger.info(
                f"CSV file loaded: {len(self._data)} rows, "
                f"{len(self.headers)} columns, "
                f"encoding={self._detected_encoding or self.encoding}"
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise ValidationError(
                message=f"خطا در بارگذاری فایل CSV: {str(e)}",
                context={"file_path": str(self.file_path), "error": str(e)},
            )

    def read_rows(
        self,
        start_row: Optional[int] = None,
        end_row: Optional[int] = None,
        as_dict: bool = True,
    ) -> Union[List[Dict[str, Any]], List[List[Any]]]:
        """
        خواندن ردیف‌های داده.

        Args:
            start_row: شماره ردیف شروع (اختیاری، از ۰ شروع می‌شود).
            end_row: شماره ردیف پایان (اختیاری، از ۰ شروع می‌شود).
            as_dict: خروجی به‌صورت دیکشنری (پیش‌فرض True) یا لیست.

        Returns:
            لیست دیکشنری‌ها یا لیست لیست‌ها.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        if not self._data:
            return []

        start = start_row if start_row is not None else 0
        end = end_row if end_row is not None else len(self._data)

        if start < 0:
            start = 0
        if end > len(self._data):
            end = len(self._data)

        if start >= end:
            return []

        data_slice = self._data[start:end]

        if as_dict:
            return data_slice
        else:
            # تبدیل به لیست لیست
            result = []
            for row in data_slice:
                result.append([row.get(header) for header in self.headers])
            return result

    def read_column(self, column: Union[int, str]) -> List[Any]:
        """
        خواندن یک ستون خاص.

        Args:
            column: شماره ستون (از ۰ شروع) یا نام ستون.

        Returns:
            List[Any]: لیست مقادیر ستون.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد یا ستون نامعتبر باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        if not self._data:
            return []

        if isinstance(column, str):
            if column not in self.headers:
                raise ValidationError(
                    message=f"ستون '{column}' در فایل وجود ندارد.",
                    context={"column": column, "available_headers": self.headers},
                )
            return [row.get(column) for row in self._data]
        else:
            if column < 0 or column >= len(self.headers):
                raise ValidationError(
                    message=f"ستون شماره {column} خارج از محدوده است.",
                    context={"column": column, "max_column": len(self.headers) - 1},
                )
            header = self.headers[column]
            return [row.get(header) for row in self._data]

    def get_headers(self) -> List[str]:
        """
        دریافت لیست هدرها.

        Returns:
            List[str]: لیست هدرها.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        return self.headers.copy()

    def get_row_count(self) -> int:
        """
        دریافت تعداد ردیف‌های داده.

        Returns:
            int: تعداد ردیف‌ها.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        return len(self._data)

    def get_column_count(self) -> int:
        """
        دریافت تعداد ستون‌ها.

        Returns:
            int: تعداد ستون‌ها.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        return len(self.headers)

    def get_sample_rows(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        دریافت نمونه‌ای از ردیف‌های داده (برای پیش‌نمایش).

        Args:
            count: تعداد ردیف‌های نمونه (پیش‌فرض: ۵).

        Returns:
            List[Dict[str, Any]]: نمونه ردیف‌ها.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        return self._data[:count]

    def validate_headers(
        self,
        required_headers: List[str],
        case_sensitive: bool = False,
    ) -> Dict[str, bool]:
        """
        اعتبارسنجی وجود هدرهای مورد نیاز.

        Args:
            required_headers: لیست هدرهای مورد نیاز.
            case_sensitive: آیا تطابق حروف بزرگ/کوچک مهم است (پیش‌فرض False).

        Returns:
            Dict[str, bool]: دیکشنری نام هدر به وجود/عدم وجود.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        headers_lower = [h.lower() for h in self.headers]
        result = {}

        for required in required_headers:
            if case_sensitive:
                result[required] = required in self.headers
            else:
                result[required] = required.lower() in headers_lower

        return result

    def validate_headers_raise(
        self,
        required_headers: List[str],
        case_sensitive: bool = False,
    ) -> None:
        """
        اعتبارسنجی هدرهای مورد نیاز و پرتاب خطا در صورت عدم وجود.

        Args:
            required_headers: لیست هدرهای مورد نیاز.
            case_sensitive: آیا تطابق حروف بزرگ/کوچک مهم است (پیش‌فرض False).

        Raises:
            ValidationError: اگر هدر مورد نیاز وجود نداشته باشد.
        """
        result = self.validate_headers(required_headers, case_sensitive)
        missing = [h for h, exists in result.items() if not exists]

        if missing:
            raise ValidationError(
                message=f"هدرهای زیر در فایل وجود ندارند: {', '.join(missing)}",
                context={"missing_headers": missing, "required_headers": required_headers},
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        دریافت خلاصه اطلاعات فایل.

        Returns:
            Dict[str, Any]: خلاصه فایل شامل تعداد ردیف‌ها، ستون‌ها، هدرها و ...
        """
        if not self._is_loaded:
            return {
                "is_loaded": False,
                "message": "فایل CSV بارگذاری نشده است.",
            }

        return {
            "is_loaded": True,
            "file_path": str(self.file_path) if self.file_path else None,
            "encoding": self._detected_encoding or self.encoding,
            "delimiter": self.delimiter,
            "has_header": self.has_header,
            "headers": self.headers,
            "row_count": len(self._data),
            "column_count": len(self.headers),
            "sample_rows": self.get_sample_rows(3),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل تمام داده‌ها به دیکشنری.

        Returns:
            Dict[str, Any]: داده‌های کامل.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        return {
            "headers": self.headers,
            "data": self._data,
            "metadata": {
                "row_count": len(self._data),
                "column_count": len(self.headers),
                "encoding": self._detected_encoding or self.encoding,
                "delimiter": self.delimiter,
            },
        }

    def clear(self) -> None:
        """
        پاک کردن داده‌های بارگذاری‌شده و آزادسازی منابع.
        """
        self._data.clear()
        self.headers.clear()
        self._is_loaded = False
        self._detected_encoding = None
        logger.info("CSVReader data cleared.")

    def __enter__(self):
        """پشتیبانی از Context Manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """خروج از Context Manager."""
        self.clear()

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterator برای پیمایش ردیف‌های داده.

        Yields:
            Dict[str, Any]: هر ردیف به‌صورت دیکشنری.

        Raises:
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        yield from self._data

    def __len__(self) -> int:
        """تعداد ردیف‌ها."""
        return len(self._data)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        """
        دسترسی به یک ردیف خاص با ایندکس.

        Args:
            index: ایندکس ردیف.

        Returns:
            Dict[str, Any]: ردیف مورد نظر.

        Raises:
            IndexError: اگر ایندکس خارج از محدوده باشد.
            ValidationError: اگر فایل بارگذاری نشده باشد.
        """
        if not self._is_loaded:
            raise ValidationError(
                message="فایل CSV بارگذاری نشده است. لطفاً ابتدا load() را فراخوانی کنید.",
                context={},
            )

        return self._data[index]