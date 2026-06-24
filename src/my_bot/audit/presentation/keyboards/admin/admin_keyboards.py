# my_bot_project/src/my_bot/presentation/keyboards/admin/admin_keyboards.py
"""
کیبوردهای پنل مدیریت (Admin Keyboards).

این ماژول شامل تمام کیبوردهای شیشه‌ای (Inline Keyboard) مربوط به
پنل مدیریت است. تمام تعاملات ادمین با سیستم از طریق این دکمه‌ها انجام می‌شود
و هیچ نیازی به تایپ دستورات متنی نیست.
"""

from typing import Optional, List, Dict, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ==============================================
# کیبورد اصلی پنل مدیریت
# ==============================================

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد اصلی پنل مدیریت.

    Returns:
        InlineKeyboardMarkup: کیبورد اصلی پنل مدیریت با تمام گزینه‌ها.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("👥 کاربران", callback_data="admin_users"),
            InlineKeyboardButton("📦 سفارشات", callback_data="admin_orders"),
        ],
        [
            InlineKeyboardButton("📊 آمار و تحلیل", callback_data="admin_analytics"),
            InlineKeyboardButton("✉️ ارسال گروهی", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("📝 مدیریت محتوا", callback_data="admin_content"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings"),
        ],
        [
            InlineKeyboardButton("📑 لاگ‌ها", callback_data="admin_logs"),
            InlineKeyboardButton("🚨 خطاها", callback_data="admin_errors"),
        ],
        [
            InlineKeyboardButton("🏷️ فیچر فلاگ", callback_data="admin_features"),
            InlineKeyboardButton("💳 کوپن‌ها", callback_data="admin_coupons"),
        ],
        [
            InlineKeyboardButton("🎫 تیکت‌ها", callback_data="admin_tickets"),
            InlineKeyboardButton("🔄 پشتیبان", callback_data="admin_backup"),
        ],
        [
            InlineKeyboardButton("💚 سلامت سیستم", callback_data="admin_health"),
            InlineKeyboardButton("📌 A/B تست", callback_data="admin_abtest"),
        ],
        [
            InlineKeyboardButton("📖 مستندات", callback_data="admin_docs"),
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main"),
        ],
    ])


# ==============================================
# کیبورد مدیریت کاربران
# ==============================================

def get_admin_users_keyboard(
    page: int = 0,
    total_pages: int = 1,
    users: Optional[List[Dict[str, Any]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت کاربران.

    Args:
        page: شماره صفحه فعلی (برای صفحه‌بندی).
        total_pages: تعداد کل صفحات.
        users: لیست کاربران برای نمایش (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت کاربران.
    """
    keyboard = []

    # نمایش کاربران (در صورت وجود)
    if users:
        for user in users:
            user_id = user.get("id")
            username = user.get("username") or user.get("full_name") or f"کاربر {user_id}"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"👤 {username}",
                    callback_data=f"admin_user_view:{user_id}"
                )
            ])

    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_users_page:{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_users_page:{page + 1}")
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # دکمه‌های عملیاتی
    keyboard.append([
        InlineKeyboardButton("➕ افزودن کاربر", callback_data="admin_user_add"),
        InlineKeyboardButton("🔍 جستجو", callback_data="admin_user_search"),
    ])

    # دکمه‌های فیلتر
    keyboard.append([
        InlineKeyboardButton("📊 فیلتر", callback_data="admin_user_filter"),
        InlineKeyboardButton("📥 خروجی", callback_data="admin_user_export"),
    ])

    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================
# کیبورد مدیریت سفارشات
# ==============================================

def get_admin_orders_keyboard(
    page: int = 0,
    total_pages: int = 1,
    orders: Optional[List[Dict[str, Any]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت سفارشات.

    Args:
        page: شماره صفحه فعلی.
        total_pages: تعداد کل صفحات.
        orders: لیست سفارشات (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت سفارشات.
    """
    keyboard = []

    # نمایش سفارشات (در صورت وجود)
    if orders:
        for order in orders:
            order_id = order.get("id")
            order_number = order.get("order_number", f"سفارش {order_id}")
            status = order.get("status", "pending")
            status_emoji = {
                "pending": "⏳",
                "paid": "✅",
                "processing": "🔄",
                "shipped": "🚚",
                "delivered": "📦",
                "canceled": "❌",
                "refunded": "💰",
                "on_hold": "🔍",
                "failed": "⚠️",
            }.get(status, "❓")

            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status_emoji} {order_number}",
                    callback_data=f"admin_order_view:{order_id}"
                )
            ])

    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_orders_page:{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_orders_page:{page + 1}")
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # دکمه‌های عملیاتی
    keyboard.append([
        InlineKeyboardButton("📊 فیلتر", callback_data="admin_order_filter"),
        InlineKeyboardButton("📥 خروجی", callback_data="admin_order_export"),
    ])

    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================
# کیبورد آمار و تحلیل
# ==============================================

def get_admin_analytics_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد آمار و تحلیل.

    Returns:
        InlineKeyboardMarkup: کیبورد آمار و تحلیل.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("📊 داشبورد", callback_data="admin_analytics_dashboard"),
            InlineKeyboardButton("📈 گزارشات", callback_data="admin_analytics_reports"),
        ],
        [
            InlineKeyboardButton("👥 تحلیل کاربران", callback_data="admin_analytics_users"),
            InlineKeyboardButton("🛒 تحلیل سفارشات", callback_data="admin_analytics_orders"),
        ],
        [
            InlineKeyboardButton("💰 تحلیل مالی", callback_data="admin_analytics_financial"),
            InlineKeyboardButton("📊 فرم‌ها", callback_data="admin_analytics_forms"),
        ],
        [
            InlineKeyboardButton("📥 خروجی", callback_data="admin_analytics_export"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# کیبورد ارسال گروهی
# ==============================================

def get_admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد ارسال گروهی.

    Returns:
        InlineKeyboardMarkup: کیبورد ارسال گروهی.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("📝 ارسال جدید", callback_data="admin_broadcast_new"),
            InlineKeyboardButton("📋 لیست ارسال‌ها", callback_data="admin_broadcast_list"),
        ],
        [
            InlineKeyboardButton("🕐 زمان‌بندی‌شده", callback_data="admin_broadcast_scheduled"),
            InlineKeyboardButton("📊 آمار ارسال‌ها", callback_data="admin_broadcast_stats"),
        ],
        [
            InlineKeyboardButton("🔍 فیلتر کاربران", callback_data="admin_broadcast_filter"),
            InlineKeyboardButton("📝 قالب‌ها", callback_data="admin_broadcast_templates"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# کیبورد مدیریت محتوا
# ==============================================

def get_admin_content_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت محتوا.

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت محتوا.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("📝 فرم‌ها", callback_data="admin_content_forms"),
            InlineKeyboardButton("📄 صفحات", callback_data="admin_content_pages"),
        ],
        [
            InlineKeyboardButton("📢 اطلاعیه‌ها", callback_data="admin_content_announcements"),
            InlineKeyboardButton("🏷️ برچسب‌ها", callback_data="admin_content_tags"),
        ],
        [
            InlineKeyboardButton("📁 فایل‌ها", callback_data="admin_content_files"),
            InlineKeyboardButton("➕ افزودن محتوا", callback_data="admin_content_add"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# کیبورد تنظیمات
# ==============================================

def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تنظیمات.

    Returns:
        InlineKeyboardMarkup: کیبورد تنظیمات.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("⚙️ تنظیمات عمومی", callback_data="admin_settings_general"),
            InlineKeyboardButton("🔐 امنیت", callback_data="admin_settings_security"),
        ],
        [
            InlineKeyboardButton("📧 ایمیل", callback_data="admin_settings_email"),
            InlineKeyboardButton("📱 پیامک", callback_data="admin_settings_sms"),
        ],
        [
            InlineKeyboardButton("💳 پرداخت", callback_data="admin_settings_payment"),
            InlineKeyboardButton("🌐 چندزبانی", callback_data="admin_settings_language"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# کیبورد مدیریت فیچر فلاگ
# ==============================================

def get_admin_features_keyboard(
    features: Optional[Dict[str, bool]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت فیچر فلاگ‌ها.

    Args:
        features: دیکشنری نام فیچر به وضعیت (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت فیچر فلاگ‌ها.
    """
    keyboard = []

    if features:
        for name, enabled in features.items():
            status = "✅ فعال" if enabled else "❌ غیرفعال"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status} {name}",
                    callback_data=f"admin_feature_toggle:{name}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton("➕ افزودن فیچر", callback_data="admin_feature_add"),
    ])

    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================
# کیبورد مدیریت کوپن‌ها
# ==============================================

def get_admin_coupons_keyboard(
    coupons: Optional[List[Dict[str, Any]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت کوپن‌ها.

    Args:
        coupons: لیست کوپن‌ها (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت کوپن‌ها.
    """
    keyboard = []

    if coupons:
        for coupon in coupons:
            code = coupon.get("code", "نامشخص")
            status = "✅" if coupon.get("is_active", False) else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status} {code}",
                    callback_data=f"admin_coupon_view:{coupon.get('id')}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton("➕ ایجاد کوپن", callback_data="admin_coupon_create"),
        InlineKeyboardButton("📋 لیست کوپن‌ها", callback_data="admin_coupon_list"),
    ])

    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================
# کیبورد مدیریت تیکت‌ها
# ==============================================

def get_admin_tickets_keyboard(
    tickets: Optional[List[Dict[str, Any]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت تیکت‌ها.

    Args:
        tickets: لیست تیکت‌ها (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت تیکت‌ها.
    """
    keyboard = []

    if tickets:
        for ticket in tickets:
            ticket_id = ticket.get("id")
            subject = ticket.get("subject", f"تیکت {ticket_id}")
            status = ticket.get("status", "open")
            status_emoji = {
                "open": "🟢",
                "in_progress": "🟡",
                "resolved": "✅",
                "closed": "🔴",
            }.get(status, "❓")

            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status_emoji} {subject}",
                    callback_data=f"admin_ticket_view:{ticket_id}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton("📊 فیلتر", callback_data="admin_ticket_filter"),
        InlineKeyboardButton("📥 خروجی", callback_data="admin_ticket_export"),
    ])

    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================
# کیبورد مدیریت پشتیبان
# ==============================================

def get_admin_backup_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت پشتیبان.

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت پشتیبان.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("📦 ایجاد پشتیبان", callback_data="admin_backup_create"),
            InlineKeyboardButton("🔄 بازیابی پشتیبان", callback_data="admin_backup_restore"),
        ],
        [
            InlineKeyboardButton("📋 لیست پشتیبان‌ها", callback_data="admin_backup_list"),
            InlineKeyboardButton("🗑️ حذف پشتیبان", callback_data="admin_backup_delete"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# کیبورد سلامت سیستم
# ==============================================

def get_admin_health_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد سلامت سیستم.

    Returns:
        InlineKeyboardMarkup: کیبورد سلامت سیستم.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("💚 بررسی سلامت", callback_data="admin_health_check"),
            InlineKeyboardButton("📊 وضعیت سرویس‌ها", callback_data="admin_health_status"),
        ],
        [
            InlineKeyboardButton("🗄️ دیتابیس", callback_data="admin_health_db"),
            InlineKeyboardButton("⚡ کش", callback_data="admin_health_cache"),
        ],
        [
            InlineKeyboardButton("🌐 سرویس‌های خارجی", callback_data="admin_health_external"),
            InlineKeyboardButton("📈 عملکرد", callback_data="admin_health_performance"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# کیبورد مدیریت A/B تست
# ==============================================

def get_admin_abtest_keyboard(
    tests: Optional[List[Dict[str, Any]]] = None,
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مدیریت A/B تست.

    Args:
        tests: لیست تست‌ها (اختیاری).

    Returns:
        InlineKeyboardMarkup: کیبورد مدیریت A/B تست.
    """
    keyboard = []

    if tests:
        for test in tests:
            test_id = test.get("id")
            name = test.get("name", f"تست {test_id}")
            status = test.get("status", "draft")
            status_emoji = {
                "draft": "📝",
                "active": "🟢",
                "paused": "⏸️",
                "completed": "✅",
                "archived": "📦",
            }.get(status, "❓")

            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status_emoji} {name}",
                    callback_data=f"admin_abtest_view:{test_id}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton("➕ ایجاد تست", callback_data="admin_abtest_create"),
        InlineKeyboardButton("📊 نتایج", callback_data="admin_abtest_results"),
    ])

    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==============================================
# کیبورد مشاهده لاگ‌ها و خطاها
# ==============================================

def get_admin_logs_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مشاهده لاگ‌ها.

    Returns:
        InlineKeyboardMarkup: کیبورد مشاهده لاگ‌ها.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("📋 لاگ‌های اخیر", callback_data="admin_logs_recent"),
            InlineKeyboardButton("🔍 جستجو", callback_data="admin_logs_search"),
        ],
        [
            InlineKeyboardButton("📊 فیلتر", callback_data="admin_logs_filter"),
            InlineKeyboardButton("📥 خروجی", callback_data="admin_logs_export"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


def get_admin_errors_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد مشاهده خطاها.

    Returns:
        InlineKeyboardMarkup: کیبورد مشاهده خطاها.
    """
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[
        [
            InlineKeyboardButton("🚨 خطاهای اخیر", callback_data="admin_errors_recent"),
            InlineKeyboardButton("📊 آمار خطاها", callback_data="admin_errors_stats"),
        ],
        [
            InlineKeyboardButton("🔍 جستجو", callback_data="admin_errors_search"),
            InlineKeyboardButton("🗑️ پاک کردن", callback_data="admin_errors_clear"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="admin_panel"),
        ],
    ])


# ==============================================
# دکمه‌های کمکی و عمومی
# ==============================================

def get_admin_back_button(callback_data: str = "admin_panel") -> InlineKeyboardMarkup:
    """
    ساخت یک دکمه بازگشت به پنل مدیریت.

    Args:
        callback_data: داده‌ی کالبک (پیش‌فرض: "admin_panel").

    Returns:
        InlineKeyboardMarkup: کیبورد با دکمه بازگشت.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به پنل مدیریت", callback_data=callback_data)]
    ])


def get_admin_action_buttons(
    actions: List[Dict[str, Any]],
) -> InlineKeyboardMarkup:
    """
    ساخت دکمه‌های عملیاتی سفارشی برای ماژول‌های مدیریت.

    Args:
        actions: لیست دیکشنری‌های هر دکمه با کلیدهای 'text' و 'callback'.

    Returns:
        InlineKeyboardMarkup: کیبورد با دکمه‌های عملیاتی.
    """
    keyboard = []
    for action in actions:
        keyboard.append([
            InlineKeyboardButton(
                text=action.get("text", "عملیات"),
                callback_data=action.get("callback", "admin_action")
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_confirm_keyboard(
    confirm_callback: str = "admin_confirm",
    cancel_callback: str = "admin_cancel",
) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد تأیید/انصراف برای عملیات‌های مدیریتی.

    Args:
        confirm_callback: داده‌ی کالبک برای تأیید.
        cancel_callback: داده‌ی کالبک برای انصراف.

    Returns:
        InlineKeyboardMarkup: کیبورد تأیید/انصراف.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأیید", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ انصراف", callback_data=cancel_callback),
        ]
    ])