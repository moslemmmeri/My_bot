# my_bot_project/src/my_bot/domain/entities/ab_test.py
"""
موجودیت تست A/B (AB Test Entity).

این کلاس نمایانگر یک آزمایش A/B در سیستم است که برای مقایسه‌ی دو یا چند نسخه
از یک پیام، فرم، یا سایر محتواها استفاده می‌شود. هدف از تست A/B،
بهبود نرخ تبدیل، تعامل کاربران یا سایر معیارهای کلیدی است.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


class ABTestStatus(str, Enum):
    """وضعیت‌های مختلف تست A/B."""
    DRAFT = "draft"              # پیش‌نویس
    ACTIVE = "active"            # در حال اجرا
    PAUSED = "paused"            # متوقف‌شده موقت
    COMPLETED = "completed"      # تکمیل‌شده
    ARCHIVED = "archived"        # بایگانی‌شده


class ABTestType(str, Enum):
    """نوع تست A/B."""
    MESSAGE = "message"          # تست روی پیام‌ها
    FORM = "form"                # تست روی فرم‌ها
    BUTTON = "button"            # تست روی دکمه‌ها
    PRICE = "price"              # تست روی قیمت‌ها
    CONTENT = "content"          # تست روی محتوا
    FLOW = "flow"                # تست روی جریان کاربری


class ABTestMetric(str, Enum):
    """معیارهای اندازه‌گیری در تست A/B."""
    CLICK_RATE = "click_rate"                    # نرخ کلیک
    CONVERSION_RATE = "conversion_rate"          # نرخ تبدیل
    SUBMISSION_RATE = "submission_rate"          # نرخ ارسال فرم
    COMPLETION_RATE = "completion_rate"          # نرخ تکمیل
    PURCHASE_RATE = "purchase_rate"              # نرخ خرید
    RETENTION_RATE = "retention_rate"            # نرخ بازگشت کاربر
    ENGAGEMENT_TIME = "engagement_time"          # زمان تعامل
    BOUNCE_RATE = "bounce_rate"                  # نرخ پرش


@dataclass
class ABTestVariant:
    """
    یک نسخه (Variant) در تست A/B.

    Attributes:
        id: شناسه یکتای نسخه (در دیتابیس).
        name: نام نسخه (مثلاً 'Control', 'Variant A', 'Variant B').
        description: توضیحات نسخه.
        config: پیکربندی نسخه (شامل محتوا، تنظیمات و ...).
        weight: وزن (احتمال نمایش) (پیش‌فرض ۱.۰).
        is_control: آیا نسخه‌ی کنترل است.
        conversions: تعداد تبدیل‌ها.
        impressions: تعداد نمایش‌ها.
        metadata: داده‌های اضافی.
    """
    name: str
    description: str
    config: Dict[str, Any]
    weight: float = 1.0
    is_control: bool = False
    conversions: int = 0
    impressions: int = 0
    id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه."""
        self._validate_name()
        self._validate_weight()

    def _validate_name(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError(
                message="نام نسخه نمی‌تواند خالی باشد.",
                context={"variant_id": self.id},
            )

    def _validate_weight(self) -> None:
        if self.weight <= 0:
            raise ValidationError(
                message="وزن نسخه باید مثبت باشد.",
                context={"variant_id": self.id, "weight": self.weight},
            )

    def add_impression(self) -> None:
        """افزایش تعداد نمایش‌ها."""
        self.impressions += 1

    def add_conversion(self) -> None:
        """افزایش تعداد تبدیل‌ها."""
        self.conversions += 1

    def get_conversion_rate(self) -> float:
        """
        محاسبه نرخ تبدیل.

        Returns:
            نرخ تبدیل (۰ تا ۱).
        """
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "weight": self.weight,
            "is_control": self.is_control,
            "conversions": self.conversions,
            "impressions": self.impressions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ABTestVariant":
        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data["description"],
            config=data.get("config", {}),
            weight=data.get("weight", 1.0),
            is_control=data.get("is_control", False),
            conversions=data.get("conversions", 0),
            impressions=data.get("impressions", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ABTest:
    """
    موجودیت تست A/B.

    Attributes:
        id: شناسه یکتای تست.
        name: نام تست.
        description: توضیحات تست.
        test_type: نوع تست (پیام، فرم، و ...).
        metric: معیار اندازه‌گیری.
        variants: لیست نسخه‌های تست.
        status: وضعیت تست (پیش‌فرض DRAFT).
        start_date: تاریخ شروع (اختیاری).
        end_date: تاریخ پایان (اختیاری).
        target_audience: فیلترهای مخاطب هدف (اختیاری).
        sample_size: حجم نمونه‌ی هدف (اختیاری).
        current_sample: حجم نمونه‌ی فعلی.
        confidence_level: سطح اطمینان (پیش‌فرض ۰.۹۵).
        minimum_effect: حداقل اثر قابل تشخیص (اختیاری).
        created_by: شناسه کاربر ایجادکننده.
        created_at: زمان ایجاد.
        updated_at: زمان آخرین به‌روزرسانی.
        metadata: داده‌های اضافی.
    """
    name: str
    test_type: ABTestType
    metric: ABTestMetric
    variants: List[ABTestVariant]
    created_by: int
    description: Optional[str] = None
    status: ABTestStatus = ABTestStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    target_audience: Optional[Dict[str, Any]] = None
    sample_size: Optional[int] = None
    current_sample: int = 0
    confidence_level: float = 0.95
    minimum_effect: Optional[float] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """اعتبارسنجی اولیه."""
        self._validate_name()
        self._validate_variants()
        self._validate_dates()
        self._validate_weights()

    def _validate_name(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError(
                message="نام تست نمی‌تواند خالی باشد.",
                context={"test_id": self.id},
            )

    def _validate_variants(self) -> None:
        if len(self.variants) < 2:
            raise ValidationError(
                message="تست A/B باید حداقل ۲ نسخه داشته باشد.",
                context={"test_id": self.id, "variants_count": len(self.variants)},
            )

        # بررسی وجود حداقل یک کنترل
        if not any(v.is_control for v in self.variants):
            raise ValidationError(
                message="حداقل یکی از نسخه‌ها باید به‌عنوان کنترل انتخاب شود.",
                context={"test_id": self.id},
            )

        # بررسی یکتایی نام‌ها
        names = [v.name for v in self.variants]
        if len(names) != len(set(names)):
            raise ValidationError(
                message="نام‌های نسخه‌ها باید یکتا باشند.",
                context={"test_id": self.id, "names": names},
            )

    def _validate_dates(self) -> None:
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(
                message="تاریخ شروع باید قبل از تاریخ پایان باشد.",
                context={"test_id": self.id, "start_date": self.start_date, "end_date": self.end_date},
            )

    def _validate_weights(self) -> None:
        # وزن‌ها باید مثبت باشند و مجموع آنها مهم نیست (نرمال‌سازی می‌شود)
        for variant in self.variants:
            if variant.weight <= 0:
                raise ValidationError(
                    message=f"وزن نسخهٔ '{variant.name}' باید مثبت باشد.",
                    context={"test_id": self.id, "variant": variant.name},
                )

    def get_variant(self, variant_name: str) -> Optional[ABTestVariant]:
        """
        دریافت یک نسخه با نام مشخص.

        Args:
            variant_name: نام نسخه.

        Returns:
            نسخه‌ی مورد نظر یا None در صورت عدم وجود.
        """
        for variant in self.variants:
            if variant.name == variant_name:
                return variant
        return None

    def get_control_variant(self) -> Optional[ABTestVariant]:
        """
        دریافت نسخه‌ی کنترل.

        Returns:
            نسخه‌ی کنترل یا None در صورت عدم وجود.
        """
        for variant in self.variants:
            if variant.is_control:
                return variant
        return None

    def get_variant_by_weight(self, random_value: float) -> Optional[ABTestVariant]:
        """
        انتخاب یک نسخه بر اساس وزن‌ها با استفاده از یک مقدار تصادفی.

        Args:
            random_value: عدد تصادفی بین ۰ و ۱.

        Returns:
            نسخه‌ی انتخاب‌شده.
        """
        if not self.variants:
            return None

        # نرمال‌سازی وزن‌ها
        total_weight = sum(v.weight for v in self.variants)
        if total_weight == 0:
            return self.variants[0]

        # محاسبه وزن‌های تجمعی
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.weight / total_weight
            if random_value <= cumulative:
                return variant

        return self.variants[-1]

    def start(self) -> None:
        """شروع اجرای تست."""
        if self.status != ABTestStatus.DRAFT:
            raise ValidationError(
                message="فقط تست‌های در وضعیت DRAFT قابل شروع هستند.",
                context={"test_id": self.id, "current_status": self.status.value},
            )
        self.status = ABTestStatus.ACTIVE
        self.start_date = datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"AB Test {self.id} started.")

    def pause(self) -> None:
        """متوقف کردن موقت تست."""
        if self.status != ABTestStatus.ACTIVE:
            raise ValidationError(
                message="فقط تست‌های در وضعیت ACTIVE قابل توقف هستند.",
                context={"test_id": self.id, "current_status": self.status.value},
            )
        self.status = ABTestStatus.PAUSED
        self.updated_at = datetime.now()
        logger.info(f"AB Test {self.id} paused.")

    def resume(self) -> None:
        """ادامه دادن تست پس از توقف."""
        if self.status != ABTestStatus.PAUSED:
            raise ValidationError(
                message="فقط تست‌های در وضعیت PAUSED قابل ادامه هستند.",
                context={"test_id": self.id, "current_status": self.status.value},
            )
        self.status = ABTestStatus.ACTIVE
        self.updated_at = datetime.now()
        logger.info(f"AB Test {self.id} resumed.")

    def complete(self) -> None:
        """تکمیل تست و پایان اجرا."""
        if self.status not in (ABTestStatus.ACTIVE, ABTestStatus.PAUSED):
            raise ValidationError(
                message="فقط تست‌های در وضعیت ACTIVE یا PAUSED قابل تکمیل هستند.",
                context={"test_id": self.id, "current_status": self.status.value},
            )
        self.status = ABTestStatus.COMPLETED
        self.end_date = datetime.now()
        self.updated_at = datetime.now()
        logger.info(f"AB Test {self.id} completed.")

    def archive(self) -> None:
        """بایگانی کردن تست."""
        if self.status == ABTestStatus.DRAFT:
            raise ValidationError(
                message="تست‌های پیش‌نویس قابل بایگانی نیستند. ابتدا کامل یا لغو کنید.",
                context={"test_id": self.id, "current_status": self.status.value},
            )
        self.status = ABTestStatus.ARCHIVED
        self.updated_at = datetime.now()
        logger.info(f"AB Test {self.id} archived.")

    def add_impression(self, variant_name: str) -> None:
        """
        ثبت یک نمایش برای یک نسخه.

        Args:
            variant_name: نام نسخه.
        """
        variant = self.get_variant(variant_name)
        if not variant:
            raise ValidationError(
                message=f"نسخهٔ '{variant_name}' در تست وجود ندارد.",
                context={"test_id": self.id, "variant_name": variant_name},
            )
        variant.add_impression()
        self.current_sample += 1
        self.updated_at = datetime.now()

    def add_conversion(self, variant_name: str) -> None:
        """
        ثبت یک تبدیل برای یک نسخه.

        Args:
            variant_name: نام نسخه.
        """
        variant = self.get_variant(variant_name)
        if not variant:
            raise ValidationError(
                message=f"نسخهٔ '{variant_name}' در تست وجود ندارد.",
                context={"test_id": self.id, "variant_name": variant_name},
            )
        variant.add_conversion()
        self.updated_at = datetime.now()

    def get_statistics(self) -> Dict[str, Any]:
        """
        محاسبه آمار تست (نرخ تبدیل، فاصله اطمینان، و ...).

        Returns:
            دیکشنری شامل آمار هر نسخه و مقایسه‌ها.
        """
        stats = {}
        control = self.get_control_variant()
        if not control:
            return stats

        control_rate = control.get_conversion_rate()

        for variant in self.variants:
            if variant.is_control:
                stats[variant.name] = {
                    "impressions": variant.impressions,
                    "conversions": variant.conversions,
                    "conversion_rate": control_rate,
                    "lift": 0.0,
                    "improvement": "control",
                    "is_control": True,
                }
            else:
                rate = variant.get_conversion_rate()
                lift = rate - control_rate if control_rate > 0 else 0.0
                improvement = f"{lift * 100:+.2f}%" if control_rate > 0 else "N/A"
                stats[variant.name] = {
                    "impressions": variant.impressions,
                    "conversions": variant.conversions,
                    "conversion_rate": rate,
                    "lift": lift,
                    "improvement": improvement,
                    "is_control": False,
                }

        return stats

    def get_winner(self) -> Optional[ABTestVariant]:
        """
        تعیین نسخه‌ی برنده بر اساس نرخ تبدیل.

        Returns:
            نسخه‌ی با بیشترین نرخ تبدیل، یا None در صورت عدم تفاوت معنی‌دار.
        """
        if self.status != ABTestStatus.COMPLETED:
            return None

        best = None
        best_rate = -1.0

        for variant in self.variants:
            rate = variant.get_conversion_rate()
            if rate > best_rate:
                best_rate = rate
                best = variant

        return best

    def is_sample_size_reached(self) -> bool:
        """
        بررسی رسیدن به حجم نمونه‌ی هدف.

        Returns:
            True اگر حجم نمونه به حد نصاب رسیده باشد.
        """
        if self.sample_size is None:
            return False
        return self.current_sample >= self.sample_size

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل موجودیت تست A/B به دیکشنری."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type.value,
            "metric": self.metric.value,
            "variants": [v.to_dict() for v in self.variants],
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "target_audience": self.target_audience,
            "sample_size": self.sample_size,
            "current_sample": self.current_sample,
            "confidence_level": self.confidence_level,
            "minimum_effect": self.minimum_effect,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ABTest":
        """ساخت موجودیت تست A/B از دیکشنری."""
        test_type = ABTestType(data.get("test_type", "message"))
        metric = ABTestMetric(data.get("metric", "click_rate"))
        status = ABTestStatus(data.get("status", "draft"))

        variants = []
        for v_data in data.get("variants", []):
            variants.append(ABTestVariant.from_dict(v_data))

        start_date = None
        if data.get("start_date"):
            try:
                start_date = datetime.fromisoformat(data["start_date"])
            except (ValueError, TypeError):
                pass

        end_date = None
        if data.get("end_date"):
            try:
                end_date = datetime.fromisoformat(data["end_date"])
            except (ValueError, TypeError):
                pass

        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()

        updated_at = None
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                updated_at = datetime.now()

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description"),
            test_type=test_type,
            metric=metric,
            variants=variants,
            status=status,
            start_date=start_date,
            end_date=end_date,
            target_audience=data.get("target_audience"),
            sample_size=data.get("sample_size"),
            current_sample=data.get("current_sample", 0),
            confidence_level=data.get("confidence_level", 0.95),
            minimum_effect=data.get("minimum_effect"),
            created_by=data["created_by"],
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        return f"ABTest(id={self.id}, name={self.name}, status={self.status.value}, variants={len(self.variants)})"