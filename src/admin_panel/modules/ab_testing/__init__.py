# my_bot_project/src/admin_panel/modules/__init__.py
"""
ماژول‌های پنل مدیریت (Admin Panel Modules).

این ماژول شامل تمام ماژول‌های مدیریتی سیستم است که هر کدام مسئولیت
یک بخش خاص از پنل مدیریت را بر عهده دارند.

ماژول‌های موجود:
- user_management: مدیریت کاربران
- order_management: مدیریت سفارشات
- analytics: آمار و تحلیل
- content_management: مدیریت محتوا
- backup_restore: پشتیبان‌گیری و بازیابی
- monitoring: پایش سیستم
- admin_management: مدیریت ادمین‌ها
- advanced_search: جستجوی پیشرفته
- settings: تنظیمات سیستم
- logs_viewer: مشاهده لاگ‌ها
- broadcast: ارسال گروهی
- error_logs: خطاهای سیستم
- system_health: سلامت سیستم
- tickets: تیکت‌های پشتیبانی
- coupons: کوپن‌های تخفیف
- feedback_management: مدیریت بازخوردها
- ab_testing: تست‌های A/B
- behavior_analytics: تحلیل رفتار
- feature_management: مدیریت فیچر فلاگ‌ها
"""

# ----------------------------------------------
# Import User Management
# ----------------------------------------------
from admin_panel.modules.user_management.handlers.list_users import ListUsersHandler
from admin_panel.modules.user_management.handlers.view_user import ViewUserHandler
from admin_panel.modules.user_management.handlers.edit_user import EditUserHandler
from admin_panel.modules.user_management.handlers.delete_user import DeleteUserHandler

# ----------------------------------------------
# Import Order Management
# ----------------------------------------------
from admin_panel.modules.order_management.handlers.list_orders import ListOrdersHandler
from admin_panel.modules.order_management.handlers.view_order import ViewOrderHandler
from admin_panel.modules.order_management.handlers.edit_order import EditOrderHandler
from admin_panel.modules.order_management.handlers.delete_order import DeleteOrderHandler

# ----------------------------------------------
# Import Analytics
# ----------------------------------------------
from admin_panel.modules.analytics.handlers.show_dashboard import ShowDashboardHandler
from admin_panel.modules.analytics.handlers.show_reports import ShowReportsHandler

# ----------------------------------------------
# Import Content Management
# ----------------------------------------------
from admin_panel.modules.content_management.handlers.list_content import ListContentHandler
from admin_panel.modules.content_management.handlers.edit_content import EditContentHandler
from admin_panel.modules.content_management.handlers.add_content import AddContentHandler

# ----------------------------------------------
# Import Backup & Restore
# ----------------------------------------------
from admin_panel.modules.backup_restore.handlers.backup_now import BackupNowHandler
from admin_panel.modules.backup_restore.handlers.restore_backup import RestoreBackupHandler

# ----------------------------------------------
# Import Monitoring
# ----------------------------------------------
from admin_panel.modules.monitoring.handlers.show_monitoring import ShowMonitoringHandler

# ----------------------------------------------
# Import Admin Management
# ----------------------------------------------
from admin_panel.modules.admin_management.handlers.list_admins import ListAdminsHandler
from admin_panel.modules.admin_management.handlers.add_admin import AddAdminHandler
from admin_panel.modules.admin_management.handlers.remove_admin import RemoveAdminHandler

# ----------------------------------------------
# Import Advanced Search
# ----------------------------------------------
from admin_panel.modules.advanced_search.handlers.search_form import SearchFormHandler
from admin_panel.modules.advanced_search.handlers.search_results import SearchResultsHandler

# ----------------------------------------------
# Import Settings
# ----------------------------------------------
from admin_panel.modules.settings.handlers.view_settings import ViewSettingsHandler
from admin_panel.modules.settings.handlers.edit_setting import EditSettingHandler

# ----------------------------------------------
# Import Logs Viewer
# ----------------------------------------------
from admin_panel.modules.logs_viewer.handlers.view_logs import ViewLogsHandler
from admin_panel.modules.logs_viewer.handlers.filter_logs import FilterLogsHandler

# ----------------------------------------------
# Import Broadcast
# ----------------------------------------------
from admin_panel.modules.broadcast.handlers.compose_broadcast import ComposeBroadcastHandler
from admin_panel.modules.broadcast.handlers.send_broadcast import SendBroadcastHandler
from admin_panel.modules.broadcast.handlers.preview_broadcast import PreviewBroadcastHandler

# ----------------------------------------------
# Import Error Logs
# ----------------------------------------------
from admin_panel.modules.error_logs.handlers.view_errors import ViewErrorsHandler
from admin_panel.modules.error_logs.handlers.clear_errors import ClearErrorsHandler

# ----------------------------------------------
# Import System Health
# ----------------------------------------------
from admin_panel.modules.system_health.handlers.show_health import ShowHealthHandler

# ----------------------------------------------
# Import Tickets
# ----------------------------------------------
from admin_panel.modules.tickets.handlers.list_tickets import ListTicketsHandler
from admin_panel.modules.tickets.handlers.view_ticket import ViewTicketHandler
from admin_panel.modules.tickets.handlers.reply_ticket import ReplyTicketHandler
from admin_panel.modules.tickets.handlers.close_ticket import CloseTicketHandler

# ----------------------------------------------
# Import Coupons
# ----------------------------------------------
from admin_panel.modules.coupons.handlers.list_coupons import ListCouponsHandler
from admin_panel.modules.coupons.handlers.create_coupon import CreateCouponHandler
from admin_panel.modules.coupons.handlers.edit_coupon import EditCouponHandler
from admin_panel.modules.coupons.handlers.delete_coupon import DeleteCouponHandler

# ----------------------------------------------
# Import Feedback Management
# ----------------------------------------------
from admin_panel.modules.feedback_management.handlers.list_feedback import ListFeedbackHandler
from admin_panel.modules.feedback_management.handlers.view_feedback import ViewFeedbackHandler

# ----------------------------------------------
# Import AB Testing
# ----------------------------------------------
from admin_panel.modules.ab_testing.handlers.list_tests import ListTestsHandler
from admin_panel.modules.ab_testing.handlers.create_test import CreateTestHandler
from admin_panel.modules.ab_testing.handlers.view_results import ViewResultsHandler

# ----------------------------------------------
# Import Behavior Analytics
# ----------------------------------------------
from admin_panel.modules.behavior_analytics.handlers.show_behavior import ShowBehaviorHandler

# ----------------------------------------------
# Import Feature Management
# ----------------------------------------------
from admin_panel.modules.feature_management.handlers.list_features import ListFeaturesHandler
from admin_panel.modules.feature_management.handlers.toggle_feature import ToggleFeatureHandler
from admin_panel.modules.feature_management.handlers.add_feature import AddFeatureHandler


# ----------------------------------------------
# لیست اشیاء قابل export
# ----------------------------------------------
__all__ = [
    # User Management
    "ListUsersHandler",
    "ViewUserHandler",
    "EditUserHandler",
    "DeleteUserHandler",

    # Order Management
    "ListOrdersHandler",
    "ViewOrderHandler",
    "EditOrderHandler",
    "DeleteOrderHandler",

    # Analytics
    "ShowDashboardHandler",
    "ShowReportsHandler",

    # Content Management
    "ListContentHandler",
    "EditContentHandler",
    "AddContentHandler",

    # Backup & Restore
    "BackupNowHandler",
    "RestoreBackupHandler",

    # Monitoring
    "ShowMonitoringHandler",

    # Admin Management
    "ListAdminsHandler",
    "AddAdminHandler",
    "RemoveAdminHandler",

    # Advanced Search
    "SearchFormHandler",
    "SearchResultsHandler",

    # Settings
    "ViewSettingsHandler",
    "EditSettingHandler",

    # Logs Viewer
    "ViewLogsHandler",
    "FilterLogsHandler",

    # Broadcast
    "ComposeBroadcastHandler",
    "SendBroadcastHandler",
    "PreviewBroadcastHandler",

    # Error Logs
    "ViewErrorsHandler",
    "ClearErrorsHandler",

    # System Health
    "ShowHealthHandler",

    # Tickets
    "ListTicketsHandler",
    "ViewTicketHandler",
    "ReplyTicketHandler",
    "CloseTicketHandler",

    # Coupons
    "ListCouponsHandler",
    "CreateCouponHandler",
    "EditCouponHandler",
    "DeleteCouponHandler",

    # Feedback Management
    "ListFeedbackHandler",
    "ViewFeedbackHandler",

    # AB Testing
    "ListTestsHandler",
    "CreateTestHandler",
    "ViewResultsHandler",

    # Behavior Analytics
    "ShowBehaviorHandler",

    # Feature Management
    "ListFeaturesHandler",
    "ToggleFeatureHandler",
    "AddFeatureHandler",
]