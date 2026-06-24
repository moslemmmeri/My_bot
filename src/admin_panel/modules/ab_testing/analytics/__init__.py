# src/admin_panel/modules/analytics/__init__.py
from .handlers import (
    show_dashboard,
    show_reports,
    show_user_stats,
    show_order_stats,
    show_payment_stats,
    show_behavior_analytics,
)
from .services import (
    AnalyticsCalculator,
    ChartGenerator,
    UserAnalyticsService,
    OrderAnalyticsService,
    PaymentAnalyticsService,
    BehaviorAnalyticsService,
)
from .keyboards import (
    AnalyticsMenuKeyboard,
    DateFiltersKeyboard,
    ReportTypeKeyboard,
)
from .dtos import (
    AnalyticsDTO,
    UserStatDTO,
    OrderStatDTO,
    PaymentStatDTO,
    BehaviorDTO,
)

__all__ = [
    # handlers
    "show_dashboard",
    "show_reports",
    "show_user_stats",
    "show_order_stats",
    "show_payment_stats",
    "show_behavior_analytics",
    # services
    "AnalyticsCalculator",
    "ChartGenerator",
    "UserAnalyticsService",
    "OrderAnalyticsService",
    "PaymentAnalyticsService",
    "BehaviorAnalyticsService",
    # keyboards
    "AnalyticsMenuKeyboard",
    "DateFiltersKeyboard",
    "ReportTypeKeyboard",
    # dtos
    "AnalyticsDTO",
    "UserStatDTO",
    "OrderStatDTO",
    "PaymentStatDTO",
    "BehaviorDTO",
]