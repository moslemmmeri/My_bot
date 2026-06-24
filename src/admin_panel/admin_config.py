# my_bot_project/src/admin_panel/core/admin_config.py
"""
پیکربندی پنل مدیریت (Admin Config).

این کلاس شامل تنظیمات مربوط به پنل مدیریت مانند دسترسی‌ها،
امنیت، لاگ‌گیری و سایر پارامترهای مرتبط با مدیریت سیستم است.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

from my_bot.core.exceptions.config_errors import ConfigurationError
from my_bot.core.logger.logger_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class AdminConfig:
    """
    پیکربندی پنل مدیریت.

    Attributes:
        enabled: فعال بودن پنل مدیریت (پیش‌فرض True)
        access_roles: لیست نقش‌های دارای دسترسی به پنل مدیریت
        default_permission: مجوز پیش‌فرض برای کاربران عادی
        audit_enabled: فعال بودن ثبت لاگ‌های مدیریتی (پیش‌فرض True)
        max_login_attempts: حداکثر تعداد تلاش‌های ناموفق برای ورود (پیش‌فرض ۵)
        session_timeout: زمان انقضای جلسه بر حسب دقیقه (پیش‌فرض ۶۰)
        backup_enabled: فعال بودن پشتیبان‌گیری خودکار (پیش‌فرض True)
        backup_interval: بازه زمانی پشتیبان‌گیری بر حسب ساعت (پیش‌فرض ۲۴)
        backup_retention_days: تعداد روزهای نگهداری پشتیبان‌ها (پیش‌فرض ۷)
        enable_advanced_search: فعال بودن جستجوی پیشرفته (پیش‌فرض True)
        enable_export: فعال بودن خروجی‌گیری (پیش‌فرض True)
        enable_import: فعال بودن واردات (پیش‌فرض True)
        max_export_rows: حداکثر تعداد ردیف‌های قابل خروجی (پیش‌فرض ۱۰۰۰۰)
        max_import_rows: حداکثر تعداد ردیف‌های قابل واردات (پیش‌فرض ۵۰۰۰)
        allowed_ips: لیست IPهای مجاز برای دسترسی به پنل (خالی = همه)
        allow_api_access: اجازه دسترسی به API مدیریت (پیش‌فرض False)
        api_rate_limit: محدودیت نرخ درخواست برای API مدیریت (پیش‌فرض ۶۰)
        default_timezone: منطقه زمانی پیش‌فرض برای گزارش‌ها (پیش‌فرض 'Asia/Tehran')
        ui_theme: تم رابط کاربری (پیش‌فرض 'dark')
        language: زبان پیش‌فرض پنل (پیش‌فرض 'fa')
        show_documentation: نمایش مستندات در پنل (پیش‌فرض True)
        show_logs: نمایش لاگ‌ها در پنل (پیش‌فرض True)
        show_errors: نمایش خطاها در پنل (پیش‌فرض True)
        show_health: نمایش سلامت سیستم در پنل (پیش‌فرض True)
        show_ab_tests: نمایش تست‌های A/B در پنل (پیش‌فرض True)
    """

    enabled: bool = True
    access_roles: List[str] = field(
        default_factory=lambda: ["admin", "manager", "operator"]
    )
    default_permission: str = "dashboard.view"
    audit_enabled: bool = True
    max_login_attempts: int = 5
    session_timeout: int = 60
    backup_enabled: bool = True
    backup_interval: int = 24
    backup_retention_days: int = 7
    enable_advanced_search: bool = True
    enable_export: bool = True
    enable_import: bool = True
    max_export_rows: int = 10000
    max_import_rows: int = 5000
    allowed_ips: List[str] = field(default_factory=list)
    allow_api_access: bool = False
    api_rate_limit: int = 60
    default_timezone: str = "Asia/Tehran"
    ui_theme: str = "dark"
    language: str = "fa"
    show_documentation: bool = True
    show_logs: bool = True
    show_errors: bool = True
    show_health: bool = True
    show_ab_tests: bool = True

    @classmethod
    def from_env(cls) -> "AdminConfig":
        """
        بارگذاری پیکربندی پنل مدیریت از متغیرهای محیطی.

        Returns:
            AdminConfig: نمونه پیکربندی.

        Raises:
            ConfigurationError: در صورت بروز خطا در بارگذاری.
        """
        try:
            enabled = os.getenv("ADMIN_ENABLED", "true").lower() in ("true", "1", "yes")

            access_roles_str = os.getenv("ADMIN_ACCESS_ROLES", "admin,manager,operator")
            access_roles = [r.strip() for r in access_roles_str.split(",") if r.strip()]

            audit_enabled = os.getenv("ADMIN_AUDIT_ENABLED", "true").lower() in ("true", "1", "yes")

            max_login_attempts = int(os.getenv("ADMIN_MAX_LOGIN_ATTEMPTS", "5"))
            session_timeout = int(os.getenv("ADMIN_SESSION_TIMEOUT", "60"))
            backup_enabled = os.getenv("ADMIN_BACKUP_ENABLED", "true").lower() in ("true", "1", "yes")
            backup_interval = int(os.getenv("ADMIN_BACKUP_INTERVAL", "24"))
            backup_retention_days = int(os.getenv("ADMIN_BACKUP_RETENTION_DAYS", "7"))

            enable_advanced_search = os.getenv("ADMIN_ADVANCED_SEARCH", "true").lower() in ("true", "1", "yes")
            enable_export = os.getenv("ADMIN_EXPORT_ENABLED", "true").lower() in ("true", "1", "yes")
            enable_import = os.getenv("ADMIN_IMPORT_ENABLED", "true").lower() in ("true", "1", "yes")

            max_export_rows = int(os.getenv("ADMIN_MAX_EXPORT_ROWS", "10000"))
            max_import_rows = int(os.getenv("ADMIN_MAX_IMPORT_ROWS", "5000"))

            allowed_ips_str = os.getenv("ADMIN_ALLOWED_IPS", "")
            allowed_ips = [ip.strip() for ip in allowed_ips_str.split(",") if ip.strip()]

            allow_api_access = os.getenv("ADMIN_API_ACCESS", "false").lower() in ("true", "1", "yes")
            api_rate_limit = int(os.getenv("ADMIN_API_RATE_LIMIT", "60"))

            default_timezone = os.getenv("ADMIN_TIMEZONE", "Asia/Tehran")
            ui_theme = os.getenv("ADMIN_UI_THEME", "dark")
            language = os.getenv("ADMIN_LANGUAGE", "fa")

            show_documentation = os.getenv("ADMIN_SHOW_DOCS", "true").lower() in ("true", "1", "yes")
            show_logs = os.getenv("ADMIN_SHOW_LOGS", "true").lower() in ("true", "1", "yes")
            show_errors = os.getenv("ADMIN_SHOW_ERRORS", "true").lower() in ("true", "1", "yes")
            show_health = os.getenv("ADMIN_SHOW_HEALTH", "true").lower() in ("true", "1", "yes")
            show_ab_tests = os.getenv("ADMIN_SHOW_AB_TESTS", "true").lower() in ("true", "1", "yes")

            config = cls(
                enabled=enabled,
                access_roles=access_roles,
                audit_enabled=audit_enabled,
                max_login_attempts=max_login_attempts,
                session_timeout=session_timeout,
                backup_enabled=backup_enabled,
                backup_interval=backup_interval,
                backup_retention_days=backup_retention_days,
                enable_advanced_search=enable_advanced_search,
                enable_export=enable_export,
                enable_import=enable_import,
                max_export_rows=max_export_rows,
                max_import_rows=max_import_rows,
                allowed_ips=allowed_ips,
                allow_api_access=allow_api_access,
                api_rate_limit=api_rate_limit,
                default_timezone=default_timezone,
                ui_theme=ui_theme,
                language=language,
                show_documentation=show_documentation,
                show_logs=show_logs,
                show_errors=show_errors,
                show_health=show_health,
                show_ab_tests=show_ab_tests,
            )

            logger.info(
                f"AdminConfig loaded: enabled={enabled}, "
                f"access_roles={access_roles}, audit_enabled={audit_enabled}"
            )
            return config

        except ValueError as e:
            raise ConfigurationError(
                message=f"خطا در بارگذاری پیکربندی پنل مدیریت: {str(e)}",
                context={"error": str(e)},
            )
        except Exception as e:
            raise ConfigurationError(
                message=f"خطای غیرمنتظره در بارگذاری پیکربندی پنل مدیریت: {str(e)}",
                context={"error": str(e)},
            )

    def is_ip_allowed(self, ip: str) -> bool:
        """
        بررسی مجاز بودن یک آدرس IP برای دسترسی به پنل مدیریت.

        Args:
            ip: آدرس IP برای بررسی.

        Returns:
            bool: True اگر IP مجاز باشد.
        """
        if not self.allowed_ips:
            return True
        return ip in self.allowed_ips

    def get_access_roles(self) -> List[str]:
        """
        دریافت لیست نقش‌های دارای دسترسی به پنل مدیریت.

        Returns:
            List[str]: لیست نقش‌ها.
        """
        return self.access_roles.copy()

    def to_dict(self) -> dict:
        """
        تبدیل پیکربندی به دیکشنری.

        Returns:
            dict: دیکشنری شامل تمام تنظیمات.
        """
        return {
            "enabled": self.enabled,
            "access_roles": self.access_roles,
            "audit_enabled": self.audit_enabled,
            "max_login_attempts": self.max_login_attempts,
            "session_timeout": self.session_timeout,
            "backup_enabled": self.backup_enabled,
            "backup_interval": self.backup_interval,
            "backup_retention_days": self.backup_retention_days,
            "enable_advanced_search": self.enable_advanced_search,
            "enable_export": self.enable_export,
            "enable_import": self.enable_import,
            "max_export_rows": self.max_export_rows,
            "max_import_rows": self.max_import_rows,
            "allowed_ips": self.allowed_ips,
            "allow_api_access": self.allow_api_access,
            "api_rate_limit": self.api_rate_limit,
            "default_timezone": self.default_timezone,
            "ui_theme": self.ui_theme,
            "language": self.language,
            "show_documentation": self.show_documentation,
            "show_logs": self.show_logs,
            "show_errors": self.show_errors,
            "show_health": self.show_health,
            "show_ab_tests": self.show_ab_tests,
        }

    def __str__(self) -> str:
        """نمایش رشته‌ای پیکربندی."""
        return f"AdminConfig(enabled={self.enabled}, roles={self.access_roles})"