# my_bot_project/src/my_bot/infrastructure/database/migrations/versions/002_add_forms.py
"""
شماره نسخه: 002_add_forms
توضیحات: اضافه کردن جداول و فیلدهای مربوط به فرم‌ها و بهبود ساختار دیتابیس

این مهاجرت شامل تغییرات زیر است:
- اضافه کردن فیلدهای جدید به جدول forms
- ایجاد جدول form_fields برای ذخیره فیلدهای فرم به‌صورت مجزا
- اضافه کردن فیلدهای جدید به جدول form_responses
- ایجاد جدول form_analytics برای ذخیره آمار فرم‌ها
- بهینه‌سازی ایندکس‌ها
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID
from datetime import datetime

# ----------------------------------------------
# اطلاعات نسخه
# ----------------------------------------------
revision = "002_add_forms"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    ارتقاء دیتابیس به این نسخه.
    """

    # ----------------------------------------------
    # 1. اضافه کردن فیلدهای جدید به جدول forms
    # ----------------------------------------------
    # اضافه کردن فیلد 'submission_message' برای پیام پس از ارسال
    op.add_column(
        "forms",
        sa.Column("submission_message", sa.Text, nullable=True)
    )

    # اضافه کردن فیلد 'is_editable' برای اجازه ویرایش پس از ارسال
    op.add_column(
        "forms",
        sa.Column("is_editable", sa.Boolean, nullable=False, server_default="false")
    )

    # اضافه کردن فیلد 'save_progress' برای ذخیره خودکار پیشرفت
    op.add_column(
        "forms",
        sa.Column("save_progress", sa.Boolean, nullable=False, server_default="false")
    )

    # اضافه کردن فیلد 'notification_emails' برای ایمیل‌های نوتیفیکیشن
    op.add_column(
        "forms",
        sa.Column("notification_emails", JSON, nullable=True)
    )

    # اضافه کردن فیلد 'webhook_url' برای وب‌هوک پس از ارسال
    op.add_column(
        "forms",
        sa.Column("webhook_url", sa.Text, nullable=True)
    )

    # ----------------------------------------------
    # 2. ایجاد جدول form_fields (فیلدهای فرم به‌صورت مجزا)
    # ----------------------------------------------
    op.create_table(
        "form_fields",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("form_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("placeholder", sa.String(200), nullable=True),
        sa.Column("help_text", sa.Text, nullable=True),
        sa.Column("default_value", sa.Text, nullable=True),
        sa.Column("options", JSON, nullable=True),
        sa.Column("validation_rules", JSON, nullable=True),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("group_name", sa.String(100), nullable=True),
        sa.Column("css_class", sa.String(100), nullable=True),
        sa.Column("width", sa.String(20), nullable=True),
        sa.Column("is_hidden", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_readonly", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.Index("ix_form_fields_form_id", "form_id"),
        sa.Index("ix_form_fields_name", "name"),
        sa.Index("ix_form_fields_field_type", "field_type"),
        sa.UniqueConstraint("form_id", "name", name="uq_form_fields_form_id_name"),
    )

    # ----------------------------------------------
    # 3. اضافه کردن فیلدهای جدید به جدول form_responses
    # ----------------------------------------------
    # اضافه کردن فیلد 'status' برای وضعیت پاسخ (draft, submitted, reviewed)
    op.add_column(
        "form_responses",
        sa.Column("status", sa.String(20), nullable=False, server_default="submitted")
    )

    # اضافه کردن فیلد 'completed_at' برای زمان تکمیل
    op.add_column(
        "form_responses",
        sa.Column("completed_at", sa.DateTime(), nullable=True)
    )

    # اضافه کردن فیلد 'session_id' برای ردیابی جلسه کاربر
    op.add_column(
        "form_responses",
        sa.Column("session_id", sa.String(100), nullable=True)
    )

    # اضافه کردن فیلد 'ip_address' برای ثبت IP کاربر
    op.add_column(
        "form_responses",
        sa.Column("ip_address", sa.String(45), nullable=True)
    )

    # اضافه کردن فیلد 'user_agent' برای ثبت مرورگر کاربر
    op.add_column(
        "form_responses",
        sa.Column("user_agent", sa.Text, nullable=True)
    )

    # اضافه کردن فیلد 'referrer' برای ثبت منبع ارجاع
    op.add_column(
        "form_responses",
        sa.Column("referrer", sa.Text, nullable=True)
    )

    # ----------------------------------------------
    # 4. ایجاد جدول form_analytics (آمار فرم‌ها)
    # ----------------------------------------------
    op.create_table(
        "form_analytics",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("form_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("views", sa.Integer, nullable=False, server_default="0"),
        sa.Column("starts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("submissions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("abandoned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_completion_time", sa.Float, nullable=True),
        sa.Column("drop_off_step", sa.Integer, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.Index("ix_form_analytics_form_id", "form_id"),
        sa.Index("ix_form_analytics_date", "date"),
        sa.Index("ix_form_analytics_form_id_date", "form_id", "date", unique=True),
    )

    # ----------------------------------------------
    # 5. ایجاد جدول form_submission_logs (لاگ ارسال‌ها)
    # ----------------------------------------------
    op.create_table(
        "form_submission_logs",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("form_id", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("details", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["response_id"], ["form_responses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_form_submission_logs_form_id", "form_id"),
        sa.Index("ix_form_submission_logs_response_id", "response_id"),
        sa.Index("ix_form_submission_logs_user_id", "user_id"),
        sa.Index("ix_form_submission_logs_created_at", "created_at"),
    )

    # ----------------------------------------------
    # 6. اضافه کردن فیلدهای جدید به جدول broadcasts
    # ----------------------------------------------
    op.add_column(
        "broadcasts",
        sa.Column("send_attempts", sa.Integer, nullable=False, server_default="0")
    )

    op.add_column(
        "broadcasts",
        sa.Column("last_error", sa.Text, nullable=True)
    )

    op.add_column(
        "broadcasts",
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0")
    )

    # ----------------------------------------------
    # 7. بهینه‌سازی ایندکس‌ها
    # ----------------------------------------------
    # اضافه کردن ایندکس ترکیبی برای جدول orders
    op.create_index(
        "ix_orders_user_status",
        "orders",
        ["user_id", "status"],
        unique=False,
    )

    # اضافه کردن ایندکس ترکیبی برای جدول payments
    op.create_index(
        "ix_payments_user_status",
        "payments",
        ["user_id", "status"],
        unique=False,
    )

    # اضافه کردن ایندکس برای جدول tickets
    op.create_index(
        "ix_tickets_status_priority",
        "tickets",
        ["status", "priority"],
        unique=False,
    )

    # اضافه کردن ایندکس برای جدول coupon (valid_from, valid_until)
    op.create_index(
        "ix_coupons_valid_dates",
        "coupons",
        ["valid_from", "valid_until"],
        unique=False,
    )

    # ----------------------------------------------
    # 8. ایجاد جدول feature_flags (مدیریت فیچر فلاگ‌ها)
    # ----------------------------------------------
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("usage_limit", sa.Integer, nullable=True),
        sa.Column("current_usage", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dependencies", JSON, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_feature_flags_name", "name"),
        sa.Index("ix_feature_flags_enabled", "enabled"),
        sa.Index("ix_feature_flags_expires_at", "expires_at"),
    )

    # ----------------------------------------------
    # 9. ایجاد جدول settings (تنظیمات سیستم)
    # ----------------------------------------------
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_editable", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_settings_key", "key"),
        sa.Index("ix_settings_category", "category"),
        sa.Index("ix_settings_is_public", "is_public"),
    )

    # ----------------------------------------------
    # 10. اضافه کردن فیلدهای جدید به جدول users
    # ----------------------------------------------
    op.add_column(
        "users",
        sa.Column("language", sa.String(10), nullable=True)
    )

    op.add_column(
        "users",
        sa.Column("timezone", sa.String(50), nullable=True)
    )

    op.add_column(
        "users",
        sa.Column("avatar_url", sa.Text, nullable=True)
    )

    op.add_column(
        "users",
        sa.Column("bio", sa.Text, nullable=True)
    )

    op.add_column(
        "users",
        sa.Column("last_login", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "users",
        sa.Column("login_count", sa.Integer, nullable=False, server_default="0")
    )

    op.add_column(
        "users",
        sa.Column("referral_code", sa.String(20), nullable=True, unique=True)
    )

    op.add_column(
        "users",
        sa.Column("referred_by", sa.Integer(), nullable=True)
    )

    # اضافه کردن ایندکس برای فیلدهای جدید
    op.create_index("ix_users_language", "users", ["language"])
    op.create_index("ix_users_last_login", "users", ["last_login"])
    op.create_index("ix_users_referral_code", "users", ["referral_code"])


def downgrade() -> None:
    """
    بازگشت به نسخه قبلی (حذف تغییرات).
    """

    # حذف ایندکس‌های اضافه‌شده
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_index("ix_users_last_login", table_name="users")
    op.drop_index("ix_users_language", table_name="users")

    # حذف فیلدهای اضافه‌شده به جدول users
    op.drop_column("users", "referred_by")
    op.drop_column("users", "referral_code")
    op.drop_column("users", "login_count")
    op.drop_column("users", "last_login")
    op.drop_column("users", "bio")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "timezone")
    op.drop_column("users", "language")

    # حذف جدول settings
    op.drop_table("settings")

    # حذف جدول feature_flags
    op.drop_table("feature_flags")

    # حذف ایندکس‌های اضافه‌شده
    op.drop_index("ix_coupons_valid_dates", table_name="coupons")
    op.drop_index("ix_tickets_status_priority", table_name="tickets")
    op.drop_index("ix_payments_user_status", table_name="payments")
    op.drop_index("ix_orders_user_status", table_name="orders")

    # حذف فیلدهای اضافه‌شده به جدول broadcasts
    op.drop_column("broadcasts", "retry_count")
    op.drop_column("broadcasts", "last_error")
    op.drop_column("broadcasts", "send_attempts")

    # حذف جدول form_submission_logs
    op.drop_table("form_submission_logs")

    # حذف جدول form_analytics
    op.drop_table("form_analytics")

    # حذف فیلدهای اضافه‌شده به جدول form_responses
    op.drop_column("form_responses", "referrer")
    op.drop_column("form_responses", "user_agent")
    op.drop_column("form_responses", "ip_address")
    op.drop_column("form_responses", "session_id")
    op.drop_column("form_responses", "completed_at")
    op.drop_column("form_responses", "status")

    # حذف جدول form_fields
    op.drop_table("form_fields")

    # حذف فیلدهای اضافه‌شده به جدول forms
    op.drop_column("forms", "webhook_url")
    op.drop_column("forms", "notification_emails")
    op.drop_column("forms", "save_progress")
    op.drop_column("forms", "is_editable")
    op.drop_column("forms", "submission_message")