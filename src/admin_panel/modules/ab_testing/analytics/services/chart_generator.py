# src/admin_panel/modules/analytics/services/chart_generator.py
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger

logger = get_logger(__name__)

# Try to set Persian font
try:
    # For Persian support, use a font that supports Arabic/Persian script
    # You should have this font installed or provide path
    persian_font = fm.FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
except:
    persian_font = None


class ChartGenerator:
    """Service for generating analytics charts."""

    def __init__(self, width: int = 10, height: int = 6, dpi: int = 100) -> None:
        self.width = width
        self.height = height
        self.dpi = dpi
        self._setup_matplotlib()

    def _setup_matplotlib(self) -> None:
        """Configure matplotlib settings."""
        try:
            # Try to set Persian font
            if persian_font:
                plt.rcParams['font.family'] = persian_font.get_name()
            else:
                # Fallback to default
                plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['xtick.labelsize'] = 10
            plt.rcParams['ytick.labelsize'] = 10
            plt.rcParams['legend.fontsize'] = 10
        except Exception as e:
            logger.warning(f"Failed to configure matplotlib: {e}")

    def _format_currency(self, value: float, pos: Any) -> str:
        """Format currency values for charts."""
        if value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return str(int(value))

    def _create_figure(self) -> Tuple[Figure, Any]:
        """Create and configure a new figure with subplot."""
        fig, ax = plt.subplots(figsize=(self.width, self.height), dpi=self.dpi)
        fig.subplots_adjust(bottom=0.15, top=0.92, left=0.12, right=0.95)
        return fig, ax

    def _save_figure(self, fig: Figure) -> io.BytesIO:
        """Save figure to BytesIO object."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=self.dpi)
        buf.seek(0)
        plt.close(fig)
        return buf

    async def generate_revenue_chart(
        self,
        data: Dict[str, Any],
        title: str = "روند درآمد"
    ) -> io.BytesIO:
        """
        Generate a line chart showing revenue trend over time.
        Data should contain 'dates' and 'revenues' lists.
        """
        try:
            dates = data.get('dates', [])
            revenues = data.get('revenues', [])

            if not dates or not revenues:
                raise ValidationError("No data available for revenue chart")

            fig, ax = self._create_figure()

            # Convert string dates to datetime if needed
            date_labels = []
            for d in dates:
                if isinstance(d, str):
                    try:
                        date_labels.append(datetime.strptime(d, '%Y-%m-%d'))
                    except:
                        date_labels.append(d)
                else:
                    date_labels.append(d)

            ax.plot(date_labels, revenues, marker='o', linewidth=2, markersize=6, color='#2E86C1')

            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('تاریخ')
            ax.set_ylabel('درآمد (تومان)')
            ax.grid(True, alpha=0.3)

            # Format y-axis as currency
            ax.yaxis.set_major_formatter(FuncFormatter(self._format_currency))

            # Rotate x-axis labels for better readability
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

            fig.tight_layout()
            return self._save_figure(fig)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating revenue chart: {e}", exc_info=True)
            raise DatabaseError("Failed to generate revenue chart.") from e

    async def generate_status_distribution_chart(
        self,
        data: Dict[str, int],
        title: str = "توزیع وضعیت سفارشات"
    ) -> io.BytesIO:
        """
        Generate a pie chart showing order status distribution.
        Data should be dict with status names as keys and counts as values.
        """
        try:
            if not data:
                raise ValidationError("No data available for status distribution chart")

            fig, ax = self._create_figure()

            labels = list(data.keys())
            values = list(data.values())
            colors = ['#28B463', '#2E86C1', '#F39C12', '#17A589', '#E74C3C', '#95A5A6']

            # Map Persian labels for better readability
            label_map = {
                'pending': 'در انتظار',
                'paid': 'پرداخت شده',
                'shipped': 'ارسال شده',
                'delivered': 'تحویل شده',
                'cancelled': 'لغو شده',
                'failed': 'ناموفق',
            }
            display_labels = [label_map.get(str(label).lower(), str(label)) for label in labels]

            wedges, texts, autotexts = ax.pie(
                values,
                labels=display_labels,
                autopct='%1.1f%%',
                colors=colors[:len(values)],
                startangle=90,
                explode=[0.02] * len(values)
            )

            # Enhance text
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            ax.set_title(title, fontweight='bold')

            # Add legend with counts
            legend_labels = [f"{label}: {value}" for label, value in zip(display_labels, values)]
            ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0.5))

            fig.tight_layout()
            return self._save_figure(fig)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating status distribution chart: {e}", exc_info=True)
            raise DatabaseError("Failed to generate status distribution chart.") from e

    async def generate_orders_trend_chart(
        self,
        data: Dict[str, Any],
        title: str = "روند سفارشات"
    ) -> io.BytesIO:
        """
        Generate a bar chart showing order trends.
        Data should contain 'dates' and 'order_counts' lists.
        """
        try:
            dates = data.get('dates', [])
            order_counts = data.get('order_counts', [])

            if not dates or not order_counts:
                raise ValidationError("No data available for orders trend chart")

            fig, ax = self._create_figure()

            # Convert string dates to datetime if needed
            date_labels = []
            for d in dates:
                if isinstance(d, str):
                    try:
                        date_labels.append(datetime.strptime(d, '%Y-%m-%d'))
                    except:
                        date_labels.append(d)
                else:
                    date_labels.append(d)

            ax.bar(date_labels, order_counts, width=0.8, color='#28B463', alpha=0.8)

            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('تاریخ')
            ax.set_ylabel('تعداد سفارشات')
            ax.grid(True, alpha=0.3, axis='y')

            # Rotate x-axis labels
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

            fig.tight_layout()
            return self._save_figure(fig)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating orders trend chart: {e}", exc_info=True)
            raise DatabaseError("Failed to generate orders trend chart.") from e

    async def generate_comparison_chart(
        self,
        data: Dict[str, float],
        title: str = "مقایسه شاخص‌ها"
    ) -> io.BytesIO:
        """
        Generate a horizontal bar chart for comparing metrics.
        Data should be dict with metric names as keys and values as numbers.
        """
        try:
            if not data:
                raise ValidationError("No data available for comparison chart")

            fig, ax = self._create_figure()

            # Sort by value for better visualization
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            labels = [item[0] for item in sorted_items]
            values = [item[1] for item in sorted_items]

            # Map Persian labels
            label_map = {
                'total_users': 'کل کاربران',
                'new_users': 'کاربران جدید',
                'active_users': 'کاربران فعال',
                'total_orders': 'کل سفارشات',
                'total_revenue': 'درآمد کل',
                'conversion_rate': 'نرخ تبدیل',
                'return_rate': 'نرخ بازگشت',
            }
            display_labels = [label_map.get(str(label).lower(), str(label)) for label in labels]

            y_pos = range(len(display_labels))
            colors = ['#2E86C1'] * len(display_labels)
            colors[0] = '#E67E22'  # Highlight first item

            ax.barh(y_pos, values, color=colors, height=0.6)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(display_labels)
            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('مقدار')

            # Add value labels on bars
            for i, v in enumerate(values):
                ax.text(v + (max(values) * 0.01), i, f"{v:,.0f}", va='center')

            ax.grid(True, alpha=0.3, axis='x')

            fig.tight_layout()
            return self._save_figure(fig)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating comparison chart: {e}", exc_info=True)
            raise DatabaseError("Failed to generate comparison chart.") from e

    async def generate_peak_hours_chart(
        self,
        data: Dict[int, int],
        title: str = "ساعات اوج فعالیت"
    ) -> io.BytesIO:
        """
        Generate a bar chart showing peak activity hours.
        Data should be dict with hour (0-23) as key and count as value.
        """
        try:
            if not data:
                raise ValidationError("No data available for peak hours chart")

            fig, ax = self._create_figure()

            hours = sorted(data.keys())
            counts = [data[h] for h in hours]

            # Create hour labels
            hour_labels = [f"{h:02d}:00" for h in hours]

            ax.bar(hour_labels, counts, color='#E67E22', alpha=0.8)

            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('ساعت')
            ax.set_ylabel('تعداد سفارشات')
            ax.grid(True, alpha=0.3, axis='y')

            # Rotate x-axis labels
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

            fig.tight_layout()
            return self._save_figure(fig)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating peak hours chart: {e}", exc_info=True)
            raise DatabaseError("Failed to generate peak hours chart.") from e

    async def generate_combined_dashboard_chart(
        self,
        revenue_data: Dict[str, Any],
        status_data: Dict[str, int],
        title: str = "داشبورد تحلیلی"
    ) -> io.BytesIO:
        """
        Generate a combined dashboard with subplots.
        """
        try:
            fig = plt.figure(figsize=(self.width * 2, self.height * 1.5), dpi=self.dpi)

            # Revenue trend (top left)
            ax1 = plt.subplot(2, 2, 1)
            dates = revenue_data.get('dates', [])
            revenues = revenue_data.get('revenues', [])
            if dates and revenues:
                date_labels = []
                for d in dates:
                    if isinstance(d, str):
                        try:
                            date_labels.append(datetime.strptime(d, '%Y-%m-%d'))
                        except:
                            date_labels.append(d)
                    else:
                        date_labels.append(d)
                ax1.plot(date_labels, revenues, marker='o', linewidth=2, markersize=6, color='#2E86C1')
                ax1.set_title('روند درآمد', fontweight='bold')
                ax1.set_xlabel('تاریخ')
                ax1.set_ylabel('درآمد')
                ax1.grid(True, alpha=0.3)
                ax1.yaxis.set_major_formatter(FuncFormatter(self._format_currency))
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

            # Status distribution (top right)
            ax2 = plt.subplot(2, 2, 2)
            if status_data:
                labels = list(status_data.keys())
                values = list(status_data.values())
                label_map = {
                    'pending': 'در انتظار',
                    'paid': 'پرداخت شده',
                    'shipped': 'ارسال شده',
                    'delivered': 'تحویل شده',
                    'cancelled': 'لغو شده',
                    'failed': 'ناموفق',
                }
                display_labels = [label_map.get(str(label).lower(), str(label)) for label in labels]
                colors = ['#28B463', '#2E86C1', '#F39C12', '#17A589', '#E74C3C', '#95A5A6']
                wedges, texts, autotexts = ax2.pie(
                    values,
                    labels=display_labels,
                    autopct='%1.1f%%',
                    colors=colors[:len(values)],
                    startangle=90
                )
                ax2.set_title('توزیع وضعیت سفارشات', fontweight='bold')

            # Orders trend (bottom left)
            ax3 = plt.subplot(2, 2, 3)
            order_dates = revenue_data.get('order_dates', [])
            order_counts = revenue_data.get('order_counts', [])
            if order_dates and order_counts:
                date_labels = []
                for d in order_dates:
                    if isinstance(d, str):
                        try:
                            date_labels.append(datetime.strptime(d, '%Y-%m-%d'))
                        except:
                            date_labels.append(d)
                    else:
                        date_labels.append(d)
                ax3.bar(date_labels, order_counts, width=0.8, color='#28B463', alpha=0.8)
                ax3.set_title('روند سفارشات', fontweight='bold')
                ax3.set_xlabel('تاریخ')
                ax3.set_ylabel('تعداد سفارشات')
                ax3.grid(True, alpha=0.3, axis='y')
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

            # Summary stats (bottom right)
            ax4 = plt.subplot(2, 2, 4)
            ax4.axis('off')
            stats = revenue_data.get('stats', {})
            if stats:
                stats_text = (
                    f"📊 **خلاصه آمار**\n\n"
                    f"کل کاربران: {stats.get('total_users', 0):,}\n"
                    f"سفارشات امروز: {stats.get('today_orders', 0):,}\n"
                    f"درآمد امروز: {stats.get('today_revenue', 0):,} تومان\n"
                    f"میانگین ارزش سفارش: {stats.get('average_order_value', 0):,} تومان\n"
                    f"نرخ تبدیل: {stats.get('conversion_rate', 0):.1f}%"
                )
                ax4.text(0.1, 0.5, stats_text, transform=ax4.transAxes, fontsize=12, verticalalignment='center')

            fig.suptitle(title, fontsize=16, fontweight='bold')
            fig.tight_layout()
            return self._save_figure(fig)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating combined dashboard chart: {e}", exc_info=True)
            raise DatabaseError("Failed to generate combined dashboard chart.") from e