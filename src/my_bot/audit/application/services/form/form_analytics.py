# my_bot_project/src/my_bot/application/services/form/form_analytics.py
"""
سرویس تحلیل فرم (Form Analytics Service).

این سرویس مسئولیت تحلیل داده‌های فرم‌ها، محاسبه آمار،
گزارش‌گیری و تحلیل رفتار کاربران در تعامل با فرم‌ها را بر عهده دارد.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from my_bot.application.dtos.form_dto import FormResponseDTO, FormAnalyticsDTO
from my_bot.core.exceptions.not_found_errors import FormNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.form import Form
from my_bot.domain.entities.form_response import FormResponse
from my_bot.domain.interfaces.repositories.form_repository import FormRepository
from my_bot.domain.interfaces.cache.cache_interface import CacheInterface
from my_bot.domain.value_objects.form_field import FieldType

logger = get_logger(__name__)


class FormAnalyticsService:
    """
    سرویس تحلیل و گزارش‌گیری از فرم‌ها.

    این کلاس مسئولیت تحلیل داده‌های فرم‌ها، محاسبه آمار و
    گزارش‌گیری از پاسخ‌های ارسال‌شده را بر عهده دارد.
    """

    def __init__(
        self,
        form_repository: FormRepository,
        cache: Optional[CacheInterface] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس تحلیل فرم.

        Args:
            form_repository: ریپازیتوری فرم.
            cache: کش برای ذخیره‌سازی موقت (اختیاری).
        """
        self._form_repository = form_repository
        self._cache = cache
        self._cache_ttl = 3600  # 1 ساعت برای تحلیل‌ها

    async def get_form_analytics(
        self,
        form_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FormAnalyticsDTO:
        """
        دریافت تحلیل کامل یک فرم.

        Args:
            form_id: شناسه فرم.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            FormAnalyticsDTO: تحلیل فرم.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        # بررسی وجود فرم
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # بررسی کش
        cache_key = f"form_analytics:{form_id}:{start_date}:{end_date}"
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                try:
                    return FormAnalyticsDTO.from_dict(cached)
                except Exception:
                    pass

        # دریافت پاسخ‌ها
        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,
            include_invalid=True,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            filtered = []
            for response in responses:
                if start_date and response.submitted_at < start_date:
                    continue
                if end_date and response.submitted_at > end_date:
                    continue
                filtered.append(response)
            responses = filtered

        # محاسبه تحلیل‌ها
        analytics = await self._calculate_analytics(form, responses)

        # ذخیره در کش
        if self._cache:
            await self._cache.set(
                cache_key,
                analytics.to_dict(),
                ttl=self._cache_ttl,
            )

        return analytics

    async def get_form_statistics(
        self,
        form_id: int,
    ) -> Dict[str, Any]:
        """
        دریافت آمار کلی یک فرم.

        Args:
            form_id: شناسه فرم.

        Returns:
            Dict[str, Any]: آمار فرم.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # دریافت آمار از ریپازیتوری
        stats = await self._form_repository.get_response_statistics(form_id)

        return {
            "form_id": form_id,
            "form_title": form.title,
            "form_type": form.form_type.value,
            "total_responses": stats.get("total_responses", 0),
            "valid_responses": stats.get("valid_responses", 0),
            "invalid_responses": stats.get("invalid_responses", 0),
            "unique_users": stats.get("unique_users", 0),
            "submission_rate": stats.get("submission_rate", 0.0),
            "responses_today": stats.get("responses_today", 0),
            "responses_this_week": stats.get("responses_this_week", 0),
            "responses_this_month": stats.get("responses_this_month", 0),
            "last_response_at": stats.get("last_response_at"),
            "created_at": form.created_at.isoformat() if form.created_at else None,
            "expires_at": form.expires_at.isoformat() if form.expires_at else None,
            "is_active": form.is_active,
            "is_public": form.is_public,
            "max_submissions": form.max_submissions,
        }

    async def get_response_distribution(
        self,
        form_id: int,
        field_name: str,
    ) -> Dict[str, Any]:
        """
        دریافت توزیع پاسخ‌ها برای یک فیلد خاص.

        Args:
            form_id: شناسه فرم.
            field_name: نام فیلد.

        Returns:
            Dict[str, Any]: توزیع پاسخ‌ها.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            ValidationError: اگر فیلد وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # بررسی وجود فیلد
        field = form.get_field(field_name)
        if not field:
            raise ValidationError(
                message=f"فیلد '{field_name}' در فرم وجود ندارد.",
                context={"form_id": form_id, "field_name": field_name},
            )

        # دریافت پاسخ‌ها
        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,
            include_invalid=False,  # فقط پاسخ‌های معتبر
        )

        # محاسبه توزیع
        distribution = {}
        total_responses = len(responses)

        for response in responses:
            value = response.answers.get(field_name)
            if value is None:
                continue

            # برای فیلدهای چند انتخابی، مقادیر را جدا می‌کنیم
            if field.field_type in (FieldType.MULTI_SELECT, FieldType.CHECKBOX):
                if isinstance(value, list):
                    for item in value:
                        distribution[item] = distribution.get(item, 0) + 1
                else:
                    distribution[str(value)] = distribution.get(str(value), 0) + 1
            else:
                # برای فیلدهای عددی، دسته‌بندی می‌کنیم
                if field.field_type == FieldType.NUMBER and isinstance(value, (int, float)):
                    # دسته‌بندی بر اساس بازه‌ها
                    bins = self._create_bins(value, distribution)
                    for bin_key, bin_value in bins.items():
                        distribution[bin_key] = distribution.get(bin_key, 0) + bin_value
                else:
                    distribution[str(value)] = distribution.get(str(value), 0) + 1

        # محاسبه درصدها
        total = sum(distribution.values())
        if total > 0:
            for key in distribution:
                distribution[key] = {
                    "count": distribution[key],
                    "percentage": (distribution[key] / total) * 100,
                }

        return {
            "field_name": field_name,
            "field_label": field.label,
            "field_type": field.field_type,
            "total_responses": total_responses,
            "distribution": distribution,
        }

    async def get_completion_rate(
        self,
        form_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        محاسبه نرخ تکمیل فرم.

        Args:
            form_id: شناسه فرم.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, float]: نرخ تکمیل (overall, by_step).

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # دریافت پاسخ‌ها
        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,
            include_invalid=True,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            filtered = []
            for response in responses:
                if start_date and response.submitted_at < start_date:
                    continue
                if end_date and response.submitted_at > end_date:
                    continue
                filtered.append(response)
            responses = filtered

        total = len(responses)
        if total == 0:
            return {
                "overall": 0.0,
                "by_step": {},
                "valid_rate": 0.0,
                "invalid_rate": 0.0,
            }

        # محاسبه نرخ تکمیل کلی
        valid_count = sum(1 for r in responses if r.is_valid)
        completion_rate = (valid_count / total) * 100

        # محاسبه نرخ تکمیل به‌تفکیک مراحل (برای فرم‌های چند مرحله‌ای)
        by_step = {}
        if form.is_multistep:
            for step in range(1, form.steps + 1):
                step_fields = form.get_fields_by_step(step)
                step_field_names = [f.name for f in step_fields]
                completed_count = 0
                for response in responses:
                    has_all_fields = all(
                        response.answers.get(field_name) is not None
                        for field_name in step_field_names
                    )
                    if has_all_fields:
                        completed_count += 1
                by_step[f"step_{step}"] = (completed_count / total) * 100

        # محاسبه نرخ پاسخ‌های معتبر و نامعتبر
        invalid_count = total - valid_count
        valid_rate = (valid_count / total) * 100
        invalid_rate = (invalid_count / total) * 100

        return {
            "overall": completion_rate,
            "by_step": by_step,
            "valid_rate": valid_rate,
            "invalid_rate": invalid_rate,
        }

    async def get_average_response_time(
        self,
        form_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        محاسبه میانگین زمان پاسخ‌دهی به فرم.

        Args:
            form_id: شناسه فرم.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: میانگین زمان پاسخ‌دهی.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # دریافت پاسخ‌ها با زمان
        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,
            include_invalid=False,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            filtered = []
            for response in responses:
                if start_date and response.submitted_at < start_date:
                    continue
                if end_date and response.submitted_at > end_date:
                    continue
                filtered.append(response)
            responses = filtered

        if not responses:
            return {
                "average_seconds": 0,
                "min_seconds": 0,
                "max_seconds": 0,
                "median_seconds": 0,
                "total_responses": 0,
            }

        # محاسبه زمان پاسخ‌دهی (با فرض اینکه فرم زمان شروع دارد)
        # در واقعیت، باید زمان شروع و پایان را در پاسخ ذخیره کنیم
        # اینجا یک شبیه‌سازی ساده انجام می‌دهیم
        times = []
        for response in responses:
            # در عمل، زمان پاسخ‌دهی باید از متادیتا یا فیلدهای خاص گرفته شود
            # اینجا یک مقدار شبیه‌سازی‌شده استفاده می‌کنیم
            response_time = response.metadata.get("response_time_seconds")
            if response_time:
                times.append(float(response_time))

        if not times:
            return {
                "average_seconds": 0,
                "min_seconds": 0,
                "max_seconds": 0,
                "median_seconds": 0,
                "total_responses": len(responses),
                "message": "زمان پاسخ‌دهی در پاسخ‌ها ثبت نشده است.",
            }

        return {
            "average_seconds": statistics.mean(times),
            "min_seconds": min(times),
            "max_seconds": max(times),
            "median_seconds": statistics.median(times),
            "std_dev_seconds": statistics.stdev(times) if len(times) > 1 else 0,
            "total_responses": len(times),
        }

    async def get_user_engagement(
        self,
        form_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        دریافت میزان تعامل کاربران با فرم.

        Args:
            form_id: شناسه فرم.
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: داده‌های تعامل کاربران.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
        """
        form = await self._form_repository.get_by_id(form_id)
        if not form:
            raise FormNotFoundError(form_id=str(form_id))

        # دریافت پاسخ‌ها
        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,
            include_invalid=True,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            filtered = []
            for response in responses:
                if start_date and response.submitted_at < start_date:
                    continue
                if end_date and response.submitted_at > end_date:
                    continue
                filtered.append(response)
            responses = filtered

        # محاسبه تعاملات
        user_ids = set()
        daily_responses = defaultdict(int)
        hourly_responses = defaultdict(int)

        for response in responses:
            if response.user_id:
                user_ids.add(response.user_id)

            # پاسخ‌های روزانه
            date_key = response.submitted_at.date().isoformat()
            daily_responses[date_key] += 1

            # پاسخ‌های ساعتی
            hour_key = response.submitted_at.hour
            hourly_responses[hour_key] += 1

        total_responses = len(responses)
        unique_users = len(user_ids)

        # محاسبه نرخ تعامل
        interaction_rate = 0.0
        if total_responses > 0:
            interaction_rate = (unique_users / total_responses) * 100

        # یافتن پربازدیدترین روزها و ساعات
        most_active_day = max(daily_responses.items(), key=lambda x: x[1]) if daily_responses else None
        most_active_hour = max(hourly_responses.items(), key=lambda x: x[1]) if hourly_responses else None

        return {
            "total_responses": total_responses,
            "unique_users": unique_users,
            "interaction_rate": interaction_rate,
            "daily_responses": dict(daily_responses),
            "hourly_responses": dict(hourly_responses),
            "most_active_day": most_active_day[0] if most_active_day else None,
            "most_active_day_count": most_active_day[1] if most_active_day else 0,
            "most_active_hour": most_active_hour[0] if most_active_hour else None,
            "most_active_hour_count": most_active_hour[1] if most_active_hour else 0,
        }

    async def export_analytics(
        self,
        form_id: int,
        format_type: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        خروجی‌گیری از تحلیل‌های فرم.

        Args:
            form_id: شناسه فرم.
            format_type: نوع خروجی ('json', 'csv').
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: داده‌های خروجی.

        Raises:
            FormNotFoundError: اگر فرم وجود نداشته باشد.
            ValidationError: اگر نوع خروجی نامعتبر باشد.
        """
        if format_type not in ("json", "csv"):
            raise ValidationError(
                message=f"نوع خروجی '{format_type}' نامعتبر است.",
                context={"format_type": format_type},
            )

        # دریافت تحلیل کامل
        analytics = await self.get_form_analytics(form_id, start_date, end_date)

        # تبدیل به فرمت مورد نظر
        if format_type == "json":
            return analytics.to_dict()

        # برای CSV، داده‌ها را به فرمت جدولی تبدیل می‌کنیم
        # اینجا یک نمونه ساده انجام می‌دهیم
        responses = await self._form_repository.get_responses_by_form(
            form_id=form_id,
            skip=0,
            limit=10000,
            include_invalid=True,
        )

        # فیلتر بر اساس تاریخ
        if start_date or end_date:
            filtered = []
            for response in responses:
                if start_date and response.submitted_at < start_date:
                    continue
                if end_date and response.submitted_at > end_date:
                    continue
                filtered.append(response)
            responses = filtered

        # ایجاد داده‌های جدولی
        csv_data = {
            "headers": ["response_id", "user_id", "submitted_at", "is_valid"],
            "rows": []
        }

        for response in responses:
            row = [
                response.id,
                response.user_id,
                response.submitted_at.isoformat() if response.submitted_at else None,
                response.is_valid,
            ]
            # اضافه کردن پاسخ‌های فیلدها
            for field_name, value in response.answers.items():
                if field_name not in csv_data["headers"]:
                    csv_data["headers"].append(field_name)
                row.append(str(value))
            csv_data["rows"].append(row)

        return csv_data

    async def compare_forms(
        self,
        form_ids: List[int],
        metric: str = "submissions",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        مقایسه چند فرم با یکدیگر.

        Args:
            form_ids: لیست شناسه فرم‌ها.
            metric: معیار مقایسه ('submissions', 'completion_rate', 'average_time').
            start_date: تاریخ شروع (اختیاری).
            end_date: تاریخ پایان (اختیاری).

        Returns:
            Dict[str, Any]: نتایج مقایسه.

        Raises:
            ValidationError: اگر معیار نامعتبر باشد یا فرم‌ها وجود نداشته باشند.
        """
        valid_metrics = ("submissions", "completion_rate", "average_time")
        if metric not in valid_metrics:
            raise ValidationError(
                message=f"معیار '{metric}' نامعتبر است.",
                context={"metric": metric, "valid_metrics": valid_metrics},
            )

        results = {}
        for form_id in form_ids:
            form = await self._form_repository.get_by_id(form_id)
            if not form:
                raise FormNotFoundError(form_id=str(form_id))

            # دریافت آمار بر اساس معیار
            if metric == "submissions":
                stats = await self._form_repository.get_response_statistics(form_id)
                results[form_id] = {
                    "title": form.title,
                    "value": stats.get("total_responses", 0),
                }
            elif metric == "completion_rate":
                completion = await self.get_completion_rate(form_id, start_date, end_date)
                results[form_id] = {
                    "title": form.title,
                    "value": completion.get("overall", 0.0),
                }
            elif metric == "average_time":
                time_stats = await self.get_average_response_time(form_id, start_date, end_date)
                results[form_id] = {
                    "title": form.title,
                    "value": time_stats.get("average_seconds", 0.0),
                }

        # مرتب‌سازی بر اساس مقدار
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1]["value"],
            reverse=True,
        )

        return {
            "metric": metric,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "results": dict(sorted_results),
            "best_performer": sorted_results[0][0] if sorted_results else None,
        }

    async def _calculate_analytics(
        self,
        form: Form,
        responses: List[FormResponse],
    ) -> FormAnalyticsDTO:
        """
        محاسبه تحلیل‌های کامل فرم (داخلی).

        Args:
            form: موجودیت فرم.
            responses: لیست پاسخ‌ها.

        Returns:
            FormAnalyticsDTO: تحلیل فرم.
        """
        # آمار پایه
        total_responses = len(responses)
        valid_responses = sum(1 for r in responses if r.is_valid)
        invalid_responses = total_responses - valid_responses
        unique_users = len({r.user_id for r in responses if r.user_id})

        # توزیع زمانی
        daily_distribution = defaultdict(int)
        for response in responses:
            date_key = response.submitted_at.date().isoformat()
            daily_distribution[date_key] += 1

        # تحلیل فیلدها
        field_analytics = []
        for field in form.fields:
            field_analysis = await self._analyze_field(responses, field)
            field_analytics.append(field_analysis)

        # نرخ تکمیل
        completion_rate = (valid_responses / total_responses * 100) if total_responses > 0 else 0.0

        return FormAnalyticsDTO(
            form_id=form.id or 0,
            form_title=form.title,
            form_type=form.form_type.value,
            total_responses=total_responses,
            valid_responses=valid_responses,
            invalid_responses=invalid_responses,
            unique_users=unique_users,
            completion_rate=completion_rate,
            daily_distribution=dict(daily_distribution),
            field_analytics=field_analytics,
        )

    async def _analyze_field(
        self,
        responses: List[FormResponse],
        field,
    ) -> Dict[str, Any]:
        """
        تحلیل یک فیلد خاص (داخلی).

        Args:
            responses: لیست پاسخ‌ها.
            field: فیلد فرم.

        Returns:
            Dict[str, Any]: تحلیل فیلد.
        """
        values = []
        for response in responses:
            value = response.answers.get(field.name)
            if value is not None:
                values.append(value)

        total_responses = len(responses)
        filled_count = len(values)
        fill_rate = (filled_count / total_responses * 100) if total_responses > 0 else 0.0

        # تحلیل بر اساس نوع فیلد
        analysis = {
            "field_name": field.name,
            "field_label": field.label,
            "field_type": field.field_type,
            "total_responses": total_responses,
            "filled_count": filled_count,
            "fill_rate": fill_rate,
            "is_required": field.is_required,
        }

        # تحلیل ویژه برای فیلدهای عددی
        if field.field_type == FieldType.NUMBER:
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                analysis.update({
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "average": statistics.mean(numeric_values),
                    "median": statistics.median(numeric_values),
                })

        # تحلیل ویژه برای فیلدهای انتخابی
        elif field.field_type in (FieldType.SELECT, FieldType.RADIO):
            from collections import Counter
            counter = Counter(values)
            analysis.update({
                "distribution": dict(counter),
                "most_common": counter.most_common(1)[0] if counter else None,
            })

        return analysis

    def _create_bins(self, value: float, distribution: Dict) -> Dict[str, int]:
        """
        ایجاد دسته‌بندی برای مقادیر عددی.

        Args:
            value: مقدار عددی.
            distribution: دیکشنری توزیع.

        Returns:
            Dict[str, int]: دسته‌بندی‌ها.
        """
        # تعیین بازه‌ها
        if value <= 10:
            return {"0-10": 1}
        elif value <= 50:
            return {"11-50": 1}
        elif value <= 100:
            return {"51-100": 1}
        elif value <= 500:
            return {"101-500": 1}
        elif value <= 1000:
            return {"501-1000": 1}
        else:
            return {"1000+": 1}

    async def clear_cache(self, form_id: int) -> None:
        """
        پاک کردن کش تحلیل‌های یک فرم.

        Args:
            form_id: شناسه فرم.
        """
        if self._cache:
            pattern = f"form_analytics:{form_id}:*"
            await self._cache.delete_pattern(pattern)
            logger.info(f"Cache cleared for form analytics: form_id={form_id}")