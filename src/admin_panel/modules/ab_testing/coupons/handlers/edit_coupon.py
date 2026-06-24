# src/admin_panel/modules/coupons/handlers/edit_coupon.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta

from my_bot.core.exceptions import NotFoundError, DatabaseError, ValidationError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.coupons.services import CouponService
from admin_panel.modules.coupons.keyboards import CouponActionsKeyboard, CouponTypeKeyboard
from admin_panel.modules.coupons.validators import CouponValidator

logger = get_logger(__name__)


@requires_admin
async def edit_coupon(query: CallbackQuery) -> None:
    """
    Show edit menu for a coupon.
    Callback data format: "admin_coupons_edit:{coupon_id}"
    """
    try:
        _, coupon_id_str = query.data.split(":", 1)
        coupon_id = int(coupon_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه کوپن نامعتبر است.", show_alert=True)
        return

    try:
        service = CouponService()
        coupon = await service.get_coupon(coupon_id)

        if not coupon:
            await query.message.edit_text(
                "❌ کوپن مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_coupons")
            )
            await query.answer("کوپن یافت نشد!", show_alert=True)
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

        text = (
            f"✏️ **ویرایش کوپن**\n\n"
            f"🆔 شناسه: `{coupon_id}`\n"
            f"🏷️ کد: `{coupon.get('code')}`\n"
            f"💰 نوع تخفیف: {type_names.get(coupon.get('discount_type'), coupon.get('discount_type'))}\n"
            f"💵 مقدار: {coupon.get('discount_value')}{'%' if coupon.get('discount_type') == 'percentage' else ' تومان'}\n"
            f"📊 وضعیت: {status_names.get(coupon.get('status'), coupon.get('status'))}\n"
            f"📈 استفاده: {coupon.get('used_count', 0)}/{coupon.get('usage_limit', 0) if coupon.get('usage_limit', 0) > 0 else '∞'}\n"
            f"📅 تاریخ انقضا: {coupon.get('expires_at', 'نامشخص')}\n"
            f"📅 ایجاد: {coupon.get('created_at', 'نامشخص')}\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        keyboard = CouponActionsKeyboard.get_edit_keyboard(
            coupon_id=coupon_id,
            back_callback="admin_coupons"
        )

        await query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await query.answer()
    except NotFoundError as e:
        logger.warning(f"Coupon {coupon_id} not found: {e}")
        await query.message.edit_text(
            "❌ کوپن مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("کوپن یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in edit_coupon: {e}")
        await query.answer("❌ خطا در دریافت اطلاعات کوپن!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in edit_coupon: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def edit_coupon_field(query: CallbackQuery) -> None:
    """
    Edit a specific field of the coupon.
    Callback data format: "admin_coupons_edit_field:{coupon_id}:{field}"
    """
    try:
        _, coupon_id_str, field = query.data.split(":", 2)
        coupon_id = int(coupon_id_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = CouponService()
        coupon = await service.get_coupon(coupon_id)

        if not coupon:
            await query.message.edit_text(
                "❌ کوپن مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_coupons")
            )
            await query.answer("کوپن یافت نشد!", show_alert=True)
            return

        field_names = {
            "code": "کد کوپن",
            "discount_type": "نوع تخفیف",
            "discount_value": "مقدار تخفیف",
            "usage_limit": "محدودیت استفاده",
            "expires_at": "تاریخ انقضا",
        }

        current_value = coupon.get(field)
        display_value = current_value

        if field == "discount_type":
            type_names = {"percentage": "درصدی", "fixed": "ثابت"}
            display_value = type_names.get(current_value, current_value)
        elif field == "expires_at":
            display_value = current_value or "نامشخص"

        text = (
            f"✏️ **ویرایش {field_names.get(field, field)}**\n\n"
            f"🆔 شناسه: `{coupon_id}`\n"
            f"📝 مقدار فعلی: `{display_value}`\n\n"
            f"لطفاً مقدار جدید را وارد کنید:\n"
        )

        # Build keyboard based on field type
        if field == "discount_type":
            keyboard = CouponTypeKeyboard.get_type_selection_keyboard(
                back_callback=f"admin_coupons_edit:{coupon_id}",
                current_type=current_value,
            )
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ انصراف",
                            callback_data=f"admin_coupons_edit:{coupon_id}"
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
    except NotFoundError as e:
        logger.warning(f"Coupon {coupon_id} not found: {e}")
        await query.message.edit_text(
            "❌ کوپن مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("کوپن یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in edit_coupon_field: {e}")
        await query.answer("❌ خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in edit_coupon_field: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def update_coupon_field(query: CallbackQuery) -> None:
    """
    Update a specific field of the coupon.
    Callback data format: "admin_coupons_update_field:{coupon_id}:{field}:{value}"
    """
    try:
        parts = query.data.split(":", 3)
        if len(parts) < 4:
            await query.answer("❌ داده نامعتبر است.", show_alert=True)
            return
        _, coupon_id_str, field, value = parts[0], parts[1], parts[2], parts[3]
        coupon_id = int(coupon_id_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = CouponService()
        validator = CouponValidator()

        # Validate based on field type
        if field == "discount_type":
            if value not in ["percentage", "fixed"]:
                raise ValidationError("نوع تخفیف نامعتبر است.")
        elif field == "discount_value":
            value = float(value)
            if value <= 0:
                raise ValidationError("مقدار تخفیف باید مثبت باشد.")
        elif field == "usage_limit":
            value = int(value)
            if value < 0:
                raise ValidationError("محدودیت استفاده نمی‌تواند منفی باشد.")
        elif field == "expires_at":
            # Parse date
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                try:
                    days = int(value)
                    value = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                except ValueError:
                    raise ValidationError("فرمت تاریخ نامعتبر است. از YYYY-MM-DD استفاده کنید.")

        # Update the field
        updated = await service.update_coupon_field(
            coupon_id=coupon_id,
            field=field,
            value=value,
            updated_by=query.from_user.id,
        )

        field_names = {
            "code": "کد کوپن",
            "discount_type": "نوع تخفیف",
            "discount_value": "مقدار تخفیف",
            "usage_limit": "محدودیت استفاده",
            "expires_at": "تاریخ انقضا",
        }

        await query.message.edit_text(
            f"✅ **{field_names.get(field, field)} با موفقیت بروزرسانی شد!**\n\n"
            f"🆔 شناسه: `{coupon_id}`\n"
            f"📝 مقدار جدید: `{value}`",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به ویرایش کوپن",
                            callback_data=f"admin_coupons_edit:{coupon_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به لیست کوپن‌ها",
                            callback_data="admin_coupons"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Coupon {coupon_id} field {field} updated to {value} by admin {query.from_user.id}")
        await query.answer("بروزرسانی شد!")
    except ValidationError as e:
        logger.warning(f"Validation error updating coupon field: {e}")
        await query.message.edit_text(
            f"❌ خطا: {str(e)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔄 تلاش مجدد",
                            callback_data=f"admin_coupons_edit_field:{coupon_id}:{field}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به ویرایش کوپن",
                            callback_data=f"admin_coupons_edit:{coupon_id}"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        await query.answer("خطا در اعتبارسنجی!", show_alert=True)
    except NotFoundError as e:
        logger.warning(f"Coupon {coupon_id} not found: {e}")
        await query.message.edit_text(
            "❌ کوپن مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("کوپن یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error updating coupon: {e}")
        await query.message.edit_text(
            "❌ خطا در بروزرسانی کوپن. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error updating coupon: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در بروزرسانی کوپن.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def edit_coupon_status(query: CallbackQuery) -> None:
    """
    Change coupon status (active/inactive).
    Callback data format: "admin_coupons_edit_status:{coupon_id}"
    """
    try:
        _, coupon_id_str = query.data.split(":", 1)
        coupon_id = int(coupon_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه کوپن نامعتبر است.", show_alert=True)
        return

    try:
        service = CouponService()
        coupon = await service.get_coupon(coupon_id)

        if not coupon:
            await query.message.edit_text(
                "❌ کوپن مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_coupons")
            )
            await query.answer("کوپن یافت نشد!", show_alert=True)
            return

        current_status = coupon.get("status", "inactive")
        new_status = "active" if current_status == "inactive" else "inactive"

        status_names = {
            "active": "فعال",
            "inactive": "غیرفعال",
        }

        text = (
            f"📊 **تغییر وضعیت کوپن**\n\n"
            f"🆔 شناسه: `{coupon_id}`\n"
            f"🏷️ کد: `{coupon.get('code')}`\n"
            f"📊 وضعیت فعلی: {status_names.get(current_status, current_status)}\n\n"
            f"آیا می‌خواهید وضعیت کوپن را به **{status_names.get(new_status, new_status)}** تغییر دهید؟"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ تغییر به {status_names.get(new_status, new_status)}",
                        callback_data=f"admin_coupons_set_status:{coupon_id}:{new_status}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"admin_coupons_edit:{coupon_id}"
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
    except NotFoundError as e:
        logger.warning(f"Coupon {coupon_id} not found: {e}")
        await query.message.edit_text(
            "❌ کوپن مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("کوپن یافت نشد!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in edit_coupon_status: {e}")
        await query.answer("❌ خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in edit_coupon_status: {e}", exc_info=True)
        await query.answer("❌ خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def set_coupon_status(query: CallbackQuery) -> None:
    """
    Set coupon status.
    Callback data format: "admin_coupons_set_status:{coupon_id}:{status}"
    """
    try:
        _, coupon_id_str, status = query.data.split(":", 2)
        coupon_id = int(coupon_id_str)
    except ValueError:
        await query.answer("❌ داده نامعتبر است.", show_alert=True)
        return

    try:
        service = CouponService()
        updated = await service.update_coupon_field(
            coupon_id=coupon_id,
            field="status",
            value=status,
            updated_by=query.from_user.id,
        )

        status_names = {
            "active": "🟢 فعال",
            "inactive": "🔴 غیرفعال",
            "expired": "⚪ منقضی",
            "used": "🔵 استفاده شده",
        }

        await query.message.edit_text(
            f"✅ **وضعیت کوپن با موفقیت تغییر یافت!**\n\n"
            f"🆔 شناسه: `{coupon_id}`\n"
            f"📊 وضعیت جدید: {status_names.get(status, status)}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به ویرایش کوپن",
                            callback_data=f"admin_coupons_edit:{coupon_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 بازگشت به لیست کوپن‌ها",
                            callback_data="admin_coupons"
                        )
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Coupon {coupon_id} status changed to {status} by admin {query.from_user.id}")
        await query.answer("وضعیت تغییر یافت!")
    except NotFoundError as e:
        logger.warning(f"Coupon {coupon_id} not found: {e}")
        await query.message.edit_text(
            "❌ کوپن مورد نظر یافت نشد.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("کوپن یافت نشد!", show_alert=True)
    except ValidationError as e:
        logger.warning(f"Validation error in set_coupon_status: {e}")
        await query.answer(f"❌ {str(e)}", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error in set_coupon_status: {e}")
        await query.message.edit_text(
            "❌ خطا در تغییر وضعیت کوپن. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in set_coupon_status: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در تغییر وضعیت کوپن.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)