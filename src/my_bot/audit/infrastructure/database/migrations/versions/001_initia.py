# my_bot_project/src/my_bot/infrastructure/database/migrations/versions/001_initial.py
"""
شماره نسخه: 001_initial
توضیحات: ایجاد جداول اولیه دیتابیس

این مهاجرت شامل ایجاد تمام جداول اصلی سیستم است که بر اساس موجودیت‌های
لایه دامنه طراحی شده‌اند.

جداول ایجادشده:
- users
- orders
- order_items
- payments
- coupons
- forms
- form_responses
- tickets
- ticket_messages
- broadcasts
- feedbacks
- ab_tests
- ab_test_variants
- audit_logs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID
from datetime import datetime

# ----------------------------------------------
# اطلاعات نسخه
# ----------------------------------------------
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    ارتقاء دیتابیس به این نسخه.
    """
    # ایجاد جدول users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(32), nullable=True),
        sa.Column("first_name", sa.String(64), nullable=True),
        sa.Column("last_name", sa.String(64), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("level", sa.String(20), nullable=False, server_default="bronze"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_activity", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.Index("ix_users_telegram_id", "telegram_id"),
        sa.Index("ix_users_role", "role"),
        sa.Index("ix_users_level", "level"),
    )

    # ایجاد جدول orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(50), nullable=False, unique=True),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IRR"),
        sa.Column("coupon_code", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_id", sa.String(50), nullable=True),
        sa.Column("shipping_address", sa.Text, nullable=True),
        sa.Column("tracking_code", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_orders_user_id", "user_id"),
        sa.Index("ix_orders_order_number", "order_number"),
        sa.Index("ix_orders_status", "status"),
        sa.Index("ix_orders_created_at", "created_at"),
    )

    # ایجاد جدول order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(50), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IRR"),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.Index("ix_order_items_order_id", "order_id"),
        sa.Index("ix_order_items_product_id", "product_id"),
    )

    # ایجاد جدول payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.String(50), nullable=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IRR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("gateway", sa.String(50), nullable=False, server_default="mock"),
        sa.Column("transaction_id", sa.String(100), nullable=True),
        sa.Column("tracking_code", sa.String(100), nullable=True),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("callback_url", sa.Text, nullable=True),
        sa.Column("callback_data", JSON, nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("expired_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_payments_user_id", "user_id"),
        sa.Index("ix_payments_status", "status"),
        sa.Index("ix_payments_transaction_id", "transaction_id"),
        sa.Index("ix_payments_tracking_code", "tracking_code"),
        sa.Index("ix_payments_created_at", "created_at"),
    )

    # ایجاد جدول coupons
    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IRR"),
        sa.Column("min_order_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("max_discount_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("user_usage_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("user_usage_count", JSON, nullable=True),  # dict {user_id: count}
        sa.Column("valid_from", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("applicable_products", JSON, nullable=True),  # list of product ids
        sa.Column("applicable_users", JSON, nullable=True),    # list of user ids
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.Index("ix_coupons_code", "code"),
        sa.Index("ix_coupons_is_active", "is_active"),
        sa.Index("ix_coupons_valid_until", "valid_until"),
    )

    # ایجاد جدول forms
    op.create_table(
        "forms",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("form_type", sa.String(50), nullable=False),
        sa.Column("fields", JSON, nullable=False),  # لیست فیلدها
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_login", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_multistep", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("steps", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("submit_button_text", sa.String(50), nullable=False, server_default="✅ ارسال"),
        sa.Column("success_message", sa.Text, nullable=True),
        sa.Column("redirect_url", sa.Text, nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_submissions", sa.Integer(), nullable=True),
        sa.Column("submission_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_forms_title", "title"),
        sa.Index("ix_forms_form_type", "form_type"),
        sa.Index("ix_forms_is_active", "is_active"),
        sa.Index("ix_forms_created_by", "created_by"),
    )

    # ایجاد جدول form_responses
    op.create_table(
        "form_responses",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("form_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("answers", JSON, nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("validation_errors", JSON, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_form_responses_form_id", "form_id"),
        sa.Index("ix_form_responses_user_id", "user_id"),
        sa.Index("ix_form_responses_submitted_at", "submitted_at"),
    )

    # ایجاد جدول tickets
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(30), nullable=False, server_default="general"),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_tickets_user_id", "user_id"),
        sa.Index("ix_tickets_status", "status"),
        sa.Index("ix_tickets_assigned_to", "assigned_to"),
        sa.Index("ix_tickets_created_at", "created_at"),
    )

    # ایجاد جدول ticket_messages
    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_ticket_messages_ticket_id", "ticket_id"),
        sa.Index("ix_ticket_messages_created_at", "created_at"),
    )

    # ایجاد جدول broadcasts
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("filter", JSON, nullable=False),  # BroadcastFilter as dict
        sa.Column("media_url", sa.Text, nullable=True),
        sa.Column("media_group", JSON, nullable=True),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("keyboard", JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_user_ids", JSON, nullable=True),  # list of user ids
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_broadcasts_status", "status"),
        sa.Index("ix_broadcasts_scheduled_at", "scheduled_at"),
        sa.Index("ix_broadcasts_created_at", "created_at"),
    )

    # ایجاد جدول feedbacks
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False, server_default="general"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("rating", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("response", sa.Text, nullable=True),
        sa.Column("responded_by", sa.Integer(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responded_by"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_feedbacks_user_id", "user_id"),
        sa.Index("ix_feedbacks_category", "category"),
        sa.Index("ix_feedbacks_status", "status"),
        sa.Index("ix_feedbacks_created_at", "created_at"),
    )

    # ایجاد جدول ab_tests
    op.create_table(
        "ab_tests",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("test_type", sa.String(30), nullable=False),
        sa.Column("metric", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("target_audience", JSON, nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("current_sample", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_level", sa.Float, nullable=False, server_default="0.95"),
        sa.Column("minimum_effect", sa.Float, nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.Index("ix_ab_tests_status", "status"),
        sa.Index("ix_ab_tests_test_type", "test_type"),
        sa.Index("ix_ab_tests_created_at", "created_at"),
    )

    # ایجاد جدول ab_test_variants
    op.create_table(
        "ab_test_variants",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("config", JSON, nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("is_control", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["test_id"], ["ab_tests.id"], ondelete="CASCADE"),
        sa.Index("ix_ab_test_variants_test_id", "test_id"),
        sa.Index("ix_ab_test_variants_name", "name"),
    )

    # ایجاد جدول audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(32), nullable=True),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="success"),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("changes", JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", JSON, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_audit_logs_user_id", "user_id"),
        sa.Index("ix_audit_logs_action", "action"),
        sa.Index("ix_audit_logs_entity_type", "entity_type"),
        sa.Index("ix_audit_logs_entity_id", "entity_id"),
        sa.Index("ix_audit_logs_created_at", "created_at"),
        sa.Index("ix_audit_logs_username", "username"),
    )


def downgrade() -> None:
    """
    بازگشت به نسخه قبلی (حذف جداول).
    """
    # حذف جداول به ترتیب معکوس
    op.drop_table("audit_logs")
    op.drop_table("ab_test_variants")
    op.drop_table("ab_tests")
    op.drop_table("feedbacks")
    op.drop_table("broadcasts")
    op.drop_table("ticket_messages")
    op.drop_table("tickets")
    op.drop_table("form_responses")
    op.drop_table("forms")
    op.drop_table("coupons")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("users")