# my_bot_project/src/my_bot/audit/audit_logger.py
"""
ثبت‌کننده لاگ‌های حسابرسی (Audit Logger).

این ماژول شامل کلاس `AuditLogger` است که مسئولیت ثبت رویدادهای حسابرسی
در سیستم را بر عهده دارد. با استفاده از این کلاس می‌توان فعالیت‌های کاربران،
تغییرات داده‌ها و رویدادهای امنیتی را ثبت و پیگیری کرد.
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from my_bot.core.logger.logger_setup import get_logger
from my_bot.core.exceptions.db_errors import DatabaseError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.domain.entities.audit_log import AuditLog, AuditAction, AuditStatus
from my_bot.domain.interfaces.repositories.audit_repository import AuditRepository

logger = get_logger(__name__)


class AuditLogger:
    """
    ثبت‌کننده رویدادهای حسابرسی.

    این کلاس با استفاده از AuditRepository، رویدادهای حسابرسی را ذخیره می‌کند
    و متدهای کمکی برای ثبت انواع مختلف رویدادها فراهم می‌آورد.

    Attributes:
        repository: ریپازیتوری لاگ‌های حسابرسی.
        default_status: وضعیت پیش‌فرض برای رویدادها (پیش‌فرض: SUCCESS).
        enabled: فعال بودن ثبت لاگ‌های حسابرسی (پیش‌فرض: True).
    """

    def __init__(
        self,
        repository: AuditRepository,
        default_status: AuditStatus = AuditStatus.SUCCESS,
        enabled: bool = True,
    ) -> None:
        """
        مقداردهی اولیه AuditLogger.

        Args:
            repository: ریپازیتوری لاگ‌های حسابرسی.
            default_status: وضعیت پیش‌فرض برای رویدادها (پیش‌فرض: SUCCESS).
            enabled: فعال بودن ثبت لاگ‌های حسابرسی (پیش‌فرض: True).
        """
        self._repository = repository
        self._default_status = default_status
        self._enabled = enabled

        logger.info(
            f"AuditLogger initialized: default_status={default_status.value}, "
            f"enabled={enabled}"
        )

    async def log_event(
        self,
        action: AuditAction,
        entity_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        message: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد حسابرسی عمومی.

        Args:
            action: نوع عملیات.
            entity_type: نوع موجودیت (مثلاً 'user', 'order').
            user_id: شناسه کاربر انجام‌دهنده (اختیاری).
            username: نام کاربری (اختیاری).
            entity_id: شناسه موجودیت (اختیاری).
            status: وضعیت عملیات (در صورت None از default_status استفاده می‌شود).
            message: پیام توضیحی (اختیاری).
            changes: تغییرات اعمال‌شده (اختیاری).
            ip_address: آدرس IP کاربر (اختیاری).
            user_agent: مرورگر یا کلاینت کاربر (اختیاری).
            session_id: شناسه جلسه (اختیاری).
            request_id: شناسه درخواست (اختیاری).
            duration_ms: مدت زمان اجرا بر حسب میلی‌ثانیه (اختیاری).
            metadata: داده‌های اضافی (اختیاری).

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None در صورت غیرفعال بودن حسابرسی.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
            DatabaseError: در صورت بروز خطا در ذخیره‌سازی.
        """
        if not self._enabled:
            logger.debug("Audit logging is disabled, skipping log_event.")
            return None

        # اعتبارسنجی اولیه
        if not user_id and not username:
            raise ValidationError(
                message="حداقل یکی از user_id یا username باید مشخص شود.",
                context={"action": action.value, "entity_type": entity_type},
            )

        if not entity_type or not entity_type.strip():
            raise ValidationError(
                message="نوع موجودیت نمی‌تواند خالی باشد.",
                context={"action": action.value},
            )

        # ایجاد لاگ
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            username=username,
            entity_id=entity_id,
            status=status or self._default_status,
            message=message,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        # ذخیره در دیتابیس
        try:
            saved_log = await self._repository.save(audit_log)
            logger.debug(
                f"Audit log saved: id={saved_log.id}, action={action.value}, "
                f"entity={entity_type}, user={user_id or username}"
            )
            return saved_log
        except Exception as e:
            logger.error(f"Error saving audit log: {e}")
            raise DatabaseError(
                message=f"خطا در ذخیره‌سازی لاگ حسابرسی: {str(e)}",
                context={"action": action.value, "entity_type": entity_type},
            )

    async def log_user_action(
        self,
        action: AuditAction,
        user_id: int,
        target_user_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به کاربر (مدیریت کاربران).

        Args:
            action: نوع عملیات (CREATE, UPDATE, DELETE, ...).
            user_id: شناسه کاربر انجام‌دهنده (ادمین یا خود کاربر).
            target_user_id: شناسه کاربر هدف (در صورت وجود).
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی برای log_event.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "user"
        entity_id = str(target_user_id) if target_user_id else None

        # اضافه کردن اطلاعات هدف به پیام
        if target_user_id and not message:
            message = f"عملیات {action.value} روی کاربر {target_user_id}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_order_action(
        self,
        action: AuditAction,
        user_id: int,
        order_id: str,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به سفارش.

        Args:
            action: نوع عملیات (CREATE, UPDATE, DELETE, ...).
            user_id: شناسه کاربر انجام‌دهنده.
            order_id: شناسه سفارش.
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "order"
        if not message:
            message = f"عملیات {action.value} روی سفارش {order_id}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=order_id,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_payment_action(
        self,
        action: AuditAction,
        user_id: int,
        payment_id: str,
        amount: Optional[float] = None,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به پرداخت.

        Args:
            action: نوع عملیات (CREATE, UPDATE, ...).
            user_id: شناسه کاربر انجام‌دهنده.
            payment_id: شناسه پرداخت.
            amount: مبلغ پرداخت (اختیاری).
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "payment"
        meta = kwargs.get("metadata", {})
        if amount is not None:
            meta["amount"] = amount
        kwargs["metadata"] = meta

        if not message:
            message = f"عملیات {action.value} روی پرداخت {payment_id}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=payment_id,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_form_action(
        self,
        action: AuditAction,
        user_id: int,
        form_id: str,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به فرم.

        Args:
            action: نوع عملیات (CREATE, UPDATE, DELETE, ...).
            user_id: شناسه کاربر انجام‌دهنده.
            form_id: شناسه فرم.
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "form"
        if not message:
            message = f"عملیات {action.value} روی فرم {form_id}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=form_id,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_ticket_action(
        self,
        action: AuditAction,
        user_id: int,
        ticket_id: str,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به تیکت پشتیبانی.

        Args:
            action: نوع عملیات (CREATE, UPDATE, ...).
            user_id: شناسه کاربر انجام‌دهنده.
            ticket_id: شناسه تیکت.
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "ticket"
        if not message:
            message = f"عملیات {action.value} روی تیکت {ticket_id}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=ticket_id,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_coupon_action(
        self,
        action: AuditAction,
        user_id: int,
        coupon_code: str,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به کوپن تخفیف.

        Args:
            action: نوع عملیات (CREATE, UPDATE, DELETE, ...).
            user_id: شناسه کاربر انجام‌دهنده.
            coupon_code: کد کوپن.
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "coupon"
        if not message:
            message = f"عملیات {action.value} روی کوپن {coupon_code}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=coupon_code,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_broadcast_action(
        self,
        action: AuditAction,
        user_id: int,
        broadcast_id: str,
        target_count: Optional[int] = None,
        sent_count: Optional[int] = None,
        failed_count: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد مربوط به ارسال گروهی.

        Args:
            action: نوع عملیات (CREATE, SEND, ...).
            user_id: شناسه کاربر انجام‌دهنده.
            broadcast_id: شناسه ارسال گروهی.
            target_count: تعداد کاربران هدف (اختیاری).
            sent_count: تعداد ارسال موفق (اختیاری).
            failed_count: تعداد ارسال ناموفق (اختیاری).
            changes: تغییرات اعمال‌شده (اختیاری).
            message: پیام توضیحی (اختیاری).
            status: وضعیت عملیات (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        entity_type = "broadcast"
        meta = kwargs.get("metadata", {})
        if target_count is not None:
            meta["target_count"] = target_count
        if sent_count is not None:
            meta["sent_count"] = sent_count
        if failed_count is not None:
            meta["failed_count"] = failed_count
        kwargs["metadata"] = meta

        if not message:
            message = f"عملیات {action.value} روی ارسال گروهی {broadcast_id}"

        return await self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=broadcast_id,
            user_id=user_id,
            message=message,
            changes=changes,
            status=status,
            **kwargs,
        )

    async def log_login(
        self,
        user_id: int,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت رویداد ورود کاربر.

        Args:
            user_id: شناسه کاربر.
            username: نام کاربری (اختیاری).
            ip_address: آدرس IP (اختیاری).
            user_agent: مرورگر (اختیاری).
            success: آیا ورود موفق بوده (پیش‌فرض True).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.LOGIN
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILED
        message = f"ورود کاربر {user_id}" + (" موفق" if success else " ناموفق")

        return await self.log_event(
            action=action,
            entity_type="user",
            entity_id=str(user_id),
            user_id=user_id,
            username=username,
            status=status,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )

    async def log_logout(
        self,
        user_id: int,
        username: Optional[str] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت رویداد خروج کاربر.

        Args:
            user_id: شناسه کاربر.
            username: نام کاربری (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.LOGOUT
        message = f"خروج کاربر {user_id}"

        return await self.log_event(
            action=action,
            entity_type="user",
            entity_id=str(user_id),
            user_id=user_id,
            username=username,
            status=AuditStatus.SUCCESS,
            message=message,
            **kwargs,
        )

    async def log_permission_change(
        self,
        user_id: int,
        target_user_id: int,
        old_role: str,
        new_role: str,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت تغییر نقش یا دسترسی کاربر.

        Args:
            user_id: شناسه کاربر انجام‌دهنده.
            target_user_id: شناسه کاربر هدف.
            old_role: نقش قبلی.
            new_role: نقش جدید.
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.PERMISSION
        changes = {"old_role": old_role, "new_role": new_role}
        message = f"تغییر نقش کاربر {target_user_id} از {old_role} به {new_role}"

        return await self.log_user_action(
            action=action,
            user_id=user_id,
            target_user_id=target_user_id,
            changes=changes,
            message=message,
            **kwargs,
        )

    async def log_feature_toggle(
        self,
        user_id: int,
        feature_name: str,
        old_state: bool,
        new_state: bool,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت تغییر وضعیت فیچر فلاگ.

        Args:
            user_id: شناسه کاربر انجام‌دهنده.
            feature_name: نام فیچر.
            old_state: وضعیت قبلی.
            new_state: وضعیت جدید.
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.FEATURE
        changes = {"feature": feature_name, "old_state": old_state, "new_state": new_state}
        status_text = "فعال" if new_state else "غیرفعال"
        message = f"تغییر وضعیت فیچر {feature_name} به {status_text}"

        return await self.log_event(
            action=action,
            entity_type="feature_flag",
            entity_id=feature_name,
            user_id=user_id,
            changes=changes,
            message=message,
            **kwargs,
        )

    async def log_backup(
        self,
        user_id: int,
        backup_type: str,
        success: bool = True,
        file_size: Optional[int] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت رویداد پشتیبان‌گیری.

        Args:
            user_id: شناسه کاربر انجام‌دهنده.
            backup_type: نوع پشتیبان (مانند 'database', 'files').
            success: آیا پشتیبان‌گیری موفق بوده (پیش‌فرض True).
            file_size: حجم فایل پشتیبان بر حسب بایت (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.BACKUP
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILED
        meta = kwargs.get("metadata", {})
        if file_size is not None:
            meta["file_size"] = file_size
        kwargs["metadata"] = meta

        message = f"عملیات پشتیبان‌گیری {backup_type}" + (" موفق" if success else " ناموفق")

        return await self.log_event(
            action=action,
            entity_type="backup",
            user_id=user_id,
            status=status,
            message=message,
            **kwargs,
        )

    async def log_export(
        self,
        user_id: int,
        export_type: str,
        format_type: str,
        count: Optional[int] = None,
        success: bool = True,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت رویداد خروجی‌گیری.

        Args:
            user_id: شناسه کاربر انجام‌دهنده.
            export_type: نوع خروجی (مانند 'users', 'orders').
            format_type: فرمت خروجی (مانند 'excel', 'pdf').
            count: تعداد رکوردهای خروجی (اختیاری).
            success: آیا خروجی‌گیری موفق بوده (پیش‌فرض True).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.EXPORT
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILED
        meta = kwargs.get("metadata", {})
        meta["export_type"] = export_type
        meta["format"] = format_type
        if count is not None:
            meta["count"] = count
        kwargs["metadata"] = meta

        message = f"خروجی‌گیری {export_type} به فرمت {format_type}" + (" موفق" if success else " ناموفق")

        return await self.log_event(
            action=action,
            entity_type="export",
            user_id=user_id,
            status=status,
            message=message,
            **kwargs,
        )

    async def log_import(
        self,
        user_id: int,
        import_type: str,
        count: Optional[int] = None,
        success: bool = True,
        errors: Optional[List[str]] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت رویداد واردات.

        Args:
            user_id: شناسه کاربر انجام‌دهنده.
            import_type: نوع واردات (مانند 'users', 'forms').
            count: تعداد رکوردهای واردشده (اختیاری).
            success: آیا واردات موفق بوده (پیش‌فرض True).
            errors: لیست خطاها (اختیاری).
            **kwargs: پارامترهای اضافی.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        action = AuditAction.IMPORT
        status = AuditStatus.SUCCESS if success else AuditStatus.FAILED
        meta = kwargs.get("metadata", {})
        meta["import_type"] = import_type
        if count is not None:
            meta["count"] = count
        if errors:
            meta["errors"] = errors[:5]  # فقط ۵ خطا برای جلوگیری از حجم بالا
        kwargs["metadata"] = meta

        message = f"واردات {import_type}" + (" موفق" if success else " ناموفق")

        return await self.log_event(
            action=action,
            entity_type="import",
            user_id=user_id,
            status=status,
            message=message,
            **kwargs,
        )

    async def log_custom(
        self,
        action: AuditAction,
        entity_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs,
    ) -> Optional[AuditLog]:
        """
        ثبت یک رویداد سفارشی.

        Args:
            action: نوع عملیات.
            entity_type: نوع موجودیت.
            user_id: شناسه کاربر (اختیاری).
            username: نام کاربری (اختیاری).
            message: پیام توضیحی (اختیاری).
            **kwargs: پارامترهای اضافی برای log_event.

        Returns:
            Optional[AuditLog]: لاگ ثبت‌شده یا None.
        """
        return await self.log_event(
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            username=username,
            message=message,
            **kwargs,
        )

    def enable(self) -> None:
        """فعال کردن ثبت لاگ‌های حسابرسی."""
        self._enabled = True
        logger.info("Audit logging enabled.")

    def disable(self) -> None:
        """غیرفعال کردن ثبت لاگ‌های حسابرسی."""
        self._enabled = False
        logger.info("Audit logging disabled.")

    def is_enabled(self) -> bool:
        """بررسی فعال بودن ثبت لاگ‌های حسابرسی."""
        return self._enabled

    async def get_user_audit_trail(
        self,
        user_id: int,
        limit: int = 50,
        skip: int = 0,
    ) -> List[AuditLog]:
        """
        دریافت تاریخچه حسابرسی یک کاربر.

        Args:
            user_id: شناسه کاربر.
            limit: حداکثر تعداد رکوردها (پیش‌فرض ۵۰).
            skip: تعداد رکوردهای نادیده گرفته شده (پیش‌فرض ۰).

        Returns:
            List[AuditLog]: لیست لاگ‌های کاربر.
        """
        return await self._repository.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    async def get_entity_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> List[AuditLog]:
        """
        دریافت تاریخچه حسابرسی یک موجودیت خاص.

        Args:
            entity_type: نوع موجودیت.
            entity_id: شناسه موجودیت.
            limit: حداکثر تعداد رکوردها (پیش‌فرض ۵۰).
            skip: تعداد رکوردهای نادیده گرفته شده (پیش‌فرض ۰).

        Returns:
            List[AuditLog]: لیست لاگ‌های موجودیت.
        """
        return await self._repository.get_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            skip=skip,
            limit=limit,
        )