# src/admin_panel/modules/coupons/handlers/list_coupons.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.coupons.services import CouponService
from admin_panel.modules.coupons.keyboards import CouponFilterKeyboard

logger = get_logger(__name__)


@requires_admin
async def list_coupons(query: CallbackQuery) -> None:
    """
    Display the list of coupons with pagination and filters.
    Callback data format:
        - "admin_coupons" (main menu)
        - "admin_coupons_list:{page}" (pagination)
        - "admin_coupons_list:{page}:{status}" (with status filter)
    """
    try:
        # Parse callback data
        parts = query.data.split(":")
        page = 1
        status = None
        coupon_type = None

        if len(parts) >= 2:
            page = int(parts[1]) if parts[1].isdigit() else 1
        if len(parts) >= 3:
            status = parts[2] if parts[2] != "all" else None
        if len(parts) >= 4:
            coupon_type = parts[3] if parts[3] != "all" else None

        service = CouponService()
        result = await service.list_coupons(
            page=page,
            page_size=10,
            status=status,
            coupon_type=coupon_type,
        )

        items = result.get("items", [])
        total = result.get("total", 0)
        current_page = result.get("page", 1)
        total_pages = (total + 9) // 10 if total > 0 else 1

        # Build text
        if not items:
            text = "🎫 **لیست کوپن‌ها**\n\nهیچ کوپنی یافت نشد."
            keyboard = CouponFilterKeyboard.get_empty_keyboard(
                back_callback="admin_panel"
            )
            await query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await query.answer()
            return

        status_names = {
            "active": "🟢 فعال",
            "inactive": "🔴 غیرفعال",
            "expired": "⚪ منقضی",
            "used": "🔵 استفاده شده",
        }
        type_names = {
            "percentage": "درصدی",
            "fixed": "ثابت",
        }

        text = f"🎫 **لیست کوپن‌ها** (صفحه {current_page} از {total_pages})\n\n"
        for idx, coupon in enumerate(items, start=(page-1)*10 + 1):
            coupon_id = coupon.get("id")
            code = coupon.get("code", "بدون کد")
            discount = coupon.get("discount_value", 0)
            discount_type = coupon.get("discount_type", "percentage")
            status = coupon.get("status", "inactive")
            usage_limit = coupon.get("usage_limit", 0)
            used_count = coupon.get("used_count", 0)
            expires_at = coupon.get("expires_at", "نامشخص")

            status_display = status_names.get(status, status)
            type_display = type_names.get(discount_type, discount_type)
            discount_display = f"{discount}%" if discount_type == "percentage" else f"{discount:,} تومان"

            text += f"{idx}. 🏷️ **{code}**\n"
            text += f"   💰 تخفیف: {discount_display} | 📊 {status_display}\n"
            text += f"   📈 استفاده: {used_count}/{usage_limit if usage_limit else '∞'}\n"
            text += f"   📅 انقضا: {expires_at[:10] if expires_at != 'نامشخص' else expires_at}\n"
            text += f"   🆔 {coupon_id}\n\n"

        # Build keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Pagination row
        nav_row = []
        if current_page > 1:
            prev_callback = f"admin_coupons_list:{current_page - 1}"
            if status:
                prev_callback += f":{status}"
            if coupon_type:
                prev_callback += f":{coupon_type}"
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ قبلی",
                    callback_data=prev_callback
                )
            )
        nav_row.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="admin_coupons_noop"
            )
        )
        if current_page < total_pages:
            next_callback = f"admin_coupons_list:{current_page + 1}"
            if status:
                next_callback += f":{status}"
            if coupon_type:
                next_callback += f":{coupon_type}"
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️ بعدی",
                    callback_data=next_callback
                )
            )
        keyboard.inline_keyboard.append(nav_row)

        # Filter row
        filter_row = []
        if status or coupon_type:
            filter_row.append(
                InlineKeyboardButton(
                    text="🧹 پاک کردن فیلترها",
                    callback_data="admin_coupons_list:1"
                )
            )
        else:
            filter_row.append(
                InlineKeyboardButton(
                    text="🔍 فیلتر",
                    callback_data="admin_coupons_filter"
                )
            )
        keyboard.inline_keyboard.append(filter_row)

        # Quick view buttons for first 5 coupons
        for coupon in items[:5]:
            coupon_id = coupon.get("id")
            code = coupon.get("code", "بدون کد")[:15]
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🏷️ {code}",
                    callback_data=f"admin_coupons_view:{coupon_id}"
                )
            ])

        # Action buttons
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="➕ ایجاد کوپن جدید",
                callback_data="admin_coupons_create"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="📊 آمار کوپن‌ها",
                callback_data="admin_coupons_stats"
            )
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="🔙 بازگشت به پنل مدیریت",
                callback_data="admin_panel"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except DatabaseError as e:
        logger.error(f"Database error in list_coupons: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت لیست کوپن‌ها. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in list_coupons: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش لیست کوپن‌ها.",
            reply_markup=get_back_button("admin_panel")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)