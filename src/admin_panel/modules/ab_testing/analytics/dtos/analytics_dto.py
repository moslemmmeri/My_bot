# src/admin_panel/modules/analytics/dtos/analytics_dto.py
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class AnalyticsDTO:
    """Data Transfer Object for analytics data."""
    
    total_users: int = 0
    new_users: int = 0
    total_orders: int = 0
    today_orders: int = 0
    total_revenue: float = 0.0
    today_revenue: float = 0.0
    pending_orders: int = 0
    paid_orders: int = 0
    shipped_orders: int = 0
    delivered_orders: int = 0
    cancelled_orders: int = 0
    successful_payments: int = 0
    failed_payments: int = 0
    average_order_value: float = 0.0
    conversion_rate: float = 0.0
    return_rate: float = 0.0
    growth_rate: float = 0.0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalyticsDTO":
        """Create AnalyticsDTO from dictionary."""
        return cls(
            total_users=data.get('total_users', 0),
            new_users=data.get('new_users', 0),
            total_orders=data.get('total_orders', 0),
            today_orders=data.get('today_orders', 0),
            total_revenue=float(data.get('total_revenue', 0.0)),
            today_revenue=float(data.get('today_revenue', 0.0)),
            pending_orders=data.get('pending_orders', 0),
            paid_orders=data.get('paid_orders', 0),
            shipped_orders=data.get('shipped_orders', 0),
            delivered_orders=data.get('delivered_orders', 0),
            cancelled_orders=data.get('cancelled_orders', 0),
            successful_payments=data.get('successful_payments', 0),
            failed_payments=data.get('failed_payments', 0),
            average_order_value=float(data.get('average_order_value', 0.0)),
            conversion_rate=float(data.get('conversion_rate', 0.0)),
            return_rate=float(data.get('return_rate', 0.0)),
            growth_rate=float(data.get('growth_rate', 0.0)),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            additional_data=data.get('additional_data', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert AnalyticsDTO to dictionary."""
        result = {
            'total_users': self.total_users,
            'new_users': self.new_users,
            'total_orders': self.total_orders,
            'today_orders': self.today_orders,
            'total_revenue': self.total_revenue,
            'today_revenue': self.today_revenue,
            'pending_orders': self.pending_orders,
            'paid_orders': self.paid_orders,
            'shipped_orders': self.shipped_orders,
            'delivered_orders': self.delivered_orders,
            'cancelled_orders': self.cancelled_orders,
            'successful_payments': self.successful_payments,
            'failed_payments': self.failed_payments,
            'average_order_value': self.average_order_value,
            'conversion_rate': self.conversion_rate,
            'return_rate': self.return_rate,
            'growth_rate': self.growth_rate,
            'additional_data': self.additional_data
        }
        if self.period_start:
            result['period_start'] = self.period_start.isoformat()
        if self.period_end:
            result['period_end'] = self.period_end.isoformat()
        return result

    def get_summary_text(self) -> str:
        """Get formatted summary text for display."""
        lines = [
            "📊 **خلاصه آمار**",
            f"👥 کل کاربران: {self.total_users:,}",
            f"🆕 کاربران جدید: {self.new_users:,}",
            f"🛒 کل سفارشات: {self.total_orders:,}",
            f"📅 سفارشات امروز: {self.today_orders:,}",
            f"💰 درآمد کل: {self.total_revenue:,.0f} تومان",
            f"💰 درآمد امروز: {self.today_revenue:,.0f} تومان",
            f"📊 میانگین ارزش سفارش: {self.average_order_value:,.0f} تومان",
            f"📈 نرخ تبدیل: {self.conversion_rate:.1f}%",
            f"🔄 نرخ بازگشت: {self.return_rate:.1f}%",
            f"📈 نرخ رشد: {self.growth_rate:.1f}%",
        ]
        if self.period_start and self.period_end:
            lines.insert(1, f"📅 بازه: {self.period_start.strftime('%Y-%m-%d')} تا {self.period_end.strftime('%Y-%m-%d')}")
        return "\n".join(lines)