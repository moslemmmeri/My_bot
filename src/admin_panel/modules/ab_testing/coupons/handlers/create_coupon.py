# src/admin_panel/modules/coupons/handlers/create_coupon.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta

from my_bot.core.exceptions import DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.coupons.services import CouponService
from admin_panel.modules.coupons.keyboards import CouponTypeKeyboard
from admin_panel.modules.coupons.validators import CouponValidator

logger = get_logger(__name__)


@requires_admin
async def create_coupon(query: CallbackQuery) -> None:
    """
    Start the coupon creation process.
    Show coupon type selection.
    Callback data: "admin_coupons_create"
    """
    try:
        text = (
            "➕ **ایجاد کوپن جدید**\n\n"
            "نوع تخفیف کوپن را انتخاب کنید:"
        )
        keyboard = CouponTypeKeyboard.get_type_selection_keyboard(
            back_callback="admin_coupons"
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except Exception as e:
        logger.error(f"Error showing create coupon menu: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطا در نمایش فرم ایجاد کوپن.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا!", show_alert=True)


@requires_admin
async def create_coupon_type(query: CallbackQuery) -> None:
    """
    Handle coupon type selection and ask for code.
    Callback data format: "admin_coupons_create_type:{type}"
    """
    try:
        _, discount_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ نوع تخفیف نامعتبر است.", show_alert=True)
        return

    # Store type in callback data for next step
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"➕ **ایجاد کوپن جدید**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n\n"
        f"لطفاً **کد** کوپن را وارد کنید:\n"
        f"(ترجیحاً حروف بزرگ و بدون فاصله)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def create_coupon_code(query: CallbackQuery) -> None:
    """
    Handle code input and ask for discount value.
    Callback data format: "admin_coupons_create_code:{type}:{code}"
    """
    try:
        _, discount_type, code = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش کد",
                    callback_data=f"admin_coupons_create_retry_code:{discount_type}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    value_label = "درصد" if discount_type == "percentage" else "مبلغ (تومان)"
    await query.message.edit_text(
        f"➕ **ایجاد کوپن جدید**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n\n"
        f"لطفاً **مقدار تخفیف** را به {value_label} وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def create_coupon_value(query: CallbackQuery) -> None:
    """
    Handle discount value input and ask for usage limit.
    Callback data format: "admin_coupons_create_value:{type}:{code}:{value}"
    """
    try:
        _, discount_type, code, value_str = query.data.split(":", 3)
        value = float(value_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش مقدار",
                    callback_data=f"admin_coupons_create_retry_value:{discount_type}:{code}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"➕ **ایجاد کوپن جدید**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n"
        f"💵 مقدار: {value}{'%' if discount_type == 'percentage' else ' تومان'}\n\n"
        f"لطفاً **محدودیت استفاده** را وارد کنید:\n"
        f"(0 = نامحدود)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def create_coupon_limit(query: CallbackQuery) -> None:
    """
    Handle usage limit input and ask for expiration date.
    Callback data format: "admin_coupons_create_limit:{type}:{code}:{value}:{limit}"
    """
    try:
        _, discount_type, code, value_str, limit_str = query.data.split(":", 4)
        value = float(value_str)
        limit = int(limit_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش محدودیت",
                    callback_data=f"admin_coupons_create_retry_limit:{discount_type}:{code}:{value}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"➕ **ایجاد کوپن جدید**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n"
        f"💵 مقدار: {value}{'%' if discount_type == 'percentage' else ' تومان'}\n"
        f"📊 محدودیت استفاده: {limit if limit > 0 else 'نامحدود'}\n\n"
        f"لطفاً **تاریخ انقضا** را وارد کنید:\n"
        f"(فرمت: YYYY-MM-DD یا تعداد روز از امروز)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def create_coupon_expiry(query: CallbackQuery) -> None:
    """
    Handle expiry date input and show confirmation.
    Callback data format: "admin_coupons_create_expiry:{type}:{code}:{value}:{limit}:{expiry}"
    """
    try:
        _, discount_type, code, value_str, limit_str, expiry = query.data.split(":", 5)
        value = float(value_str)
        limit = int(limit_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    # Parse expiry date
    try:
        # Try to parse as date
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
    except ValueError:
        try:
            # Try to parse as days from now
            days = int(expiry)
            expiry_date = datetime.now() + timedelta(days=days)
        except ValueError:
            await query.answer("❌ تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید.", show_alert=True)
            return

    # Show confirmation
    text = (
        f"✅ **تأیید نهایی ایجاد کوپن**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n"
        f"💵 مقدار: {value}{'%' if discount_type == 'percentage' else ' تومان'}\n"
        f"📊 محدودیت استفاده: {limit if limit > 0 else 'نامحدود'}\n"
        f"📅 تاریخ انقضا: {expiry_date.strftime('%Y-%m-%d')}\n\n"
        f"آیا از ایجاد این کوپن اطمینان دارید؟"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، ایجاد شود",
                    callback_data=f"admin_coupons_create_save:{discount_type}:{code}:{value}:{limit}:{expiry_date.strftime('%Y-%m-%d')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش تاریخ",
                    callback_data=f"admin_coupons_create_retry_expiry:{discount_type}:{code}:{value}:{limit}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def save_coupon(query: CallbackQuery) -> None:
    """
    Save the coupon to database.
    Callback data format: "admin_coupons_create_save:{type}:{code}:{value}:{limit}:{expiry}"
    """
    try:
        _, discount_type, code, value_str, limit_str, expiry = query.data.split(":", 5)
        value = float(value_str)
        limit = int(limit_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        # Validate data
        validator = CouponValidator()
        validated = validator.validate_create({
            "code": code,
            "discount_type": discount_type,
            "discount_value": value,
            "usage_limit": limit,
            "expires_at": expiry,
            "created_by": query.from_user.id,
        })

        # Save coupon
        service = CouponService()
        coupon = await service.create_coupon(**validated)

        text = (
            f"✅ **کوپن با موفقیت ایجاد شد!**\n\n"
            f"🏷️ کد: `{coupon.get('code')}`\n"
            f"💰 نوع تخفیف: {coupon.get('discount_type')}\n"
            f"💵 مقدار: {coupon.get('discount_value')}{'%' if coupon.get('discount_type') == 'percentage' else ' تومان'}\n"
            f"📊 محدودیت استفاده: {coupon.get('usage_limit') if coupon.get('usage_limit') > 0 else 'نامحدود'}\n"
            f"📅 تاریخ انقضا: {coupon.get('expires_at', 'نامشخص')}\n"
            f"🆔 شناسه: `{coupon.get('id')}`"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 مشاهده کوپن",
                        callback_data=f"admin_coupons_view:{coupon.get('id')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش کوپن",
                        callback_data=f"admin_coupons_edit:{coupon.get('id')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ ایجاد کوپن جدید",
                        callback_data="admin_coupons_create"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست کوپن‌ها",
                        callback_data="admin_coupons"
                    )
                ]
            ]
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Coupon created: {coupon.get('code')} by admin {query.from_user.id}")
        await query.answer("کوپن ایجاد شد!")
    except ValidationError as e:
        logger.warning(f"Validation error in save_coupon: {e}")
        await query.message.edit_text(
            f"❌ خطای اعتبارسنجی:\n{str(e)}",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in save_coupon: {e}")
        await query.message.edit_text(
            "❌ خطا در ایجاد کوپن. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in save_coupon: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در ایجاد کوپن.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def retry_code(query: CallbackQuery) -> None:
    """
    Retry entering coupon code.
    Callback data format: "admin_coupons_create_retry_code:{type}"
    """
    try:
        _, discount_type = query.data.split(":", 1)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **ویرایش کد کوپن**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n\n"
        f"لطفاً **کد** کوپن را وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def retry_value(query: CallbackQuery) -> None:
    """
    Retry entering discount value.
    Callback data format: "admin_coupons_create_retry_value:{type}:{code}"
    """
    try:
        _, discount_type, code = query.data.split(":", 2)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش کد",
                    callback_data=f"admin_coupons_create_retry_code:{discount_type}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    value_label = "درصد" if discount_type == "percentage" else "مبلغ (تومان)"
    await query.message.edit_text(
        f"✏️ **ویرایش مقدار تخفیف**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n\n"
        f"لطفاً **مقدار تخفیف** را به {value_label} وارد کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def retry_limit(query: CallbackQuery) -> None:
    """
    Retry entering usage limit.
    Callback data format: "admin_coupons_create_retry_limit:{type}:{code}:{value}"
    """
    try:
        _, discount_type, code, value_str = query.data.split(":", 3)
        value = float(value_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش مقدار",
                    callback_data=f"admin_coupons_create_retry_value:{discount_type}:{code}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **ویرایش محدودیت استفاده**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n"
        f"💵 مقدار: {value}{'%' if discount_type == 'percentage' else ' تومان'}\n\n"
        f"لطفاً **محدودیت استفاده** را وارد کنید:\n"
        f"(0 = نامحدود)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


@requires_admin
async def retry_expiry(query: CallbackQuery) -> None:
    """
    Retry entering expiry date.
    Callback data format: "admin_coupons_create_retry_expiry:{type}:{code}:{value}:{limit}"
    """
    try:
        _, discount_type, code, value_str, limit_str = query.data.split(":", 4)
        value = float(value_str)
        limit = int(limit_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ویرایش محدودیت",
                    callback_data=f"admin_coupons_create_retry_limit:{discount_type}:{code}:{value}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ انصراف",
                    callback_data="admin_coupons"
                )
            ]
        ]
    )

    await query.message.edit_text(
        f"✏️ **ویرایش تاریخ انقضا**\n\n"
        f"💰 نوع تخفیف: {discount_type}\n"
        f"🏷️ کد: `{code}`\n"
        f"💵 مقدار: {value}{'%' if discount_type == 'percentage' else ' تومان'}\n"
        f"📊 محدودیت استفاده: {limit if limit > 0 else 'نامحدود'}\n\n"
        f"لطفاً **تاریخ انقضا** را وارد کنید:\n"
        f"(فرمت: YYYY-MM-DD یا تعداد روز از امروز)",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.answer()