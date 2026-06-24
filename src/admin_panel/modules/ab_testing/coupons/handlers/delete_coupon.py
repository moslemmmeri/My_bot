# src/admin_panel/modules/coupons/handlers/delete_coupon.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import NotFoundError, DatabaseError, PermissionDeniedError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.coupons.services import CouponService
from admin_panel.modules.coupons.keyboards import CouponActionsKeyboard

logger = get_logger(__name__)


@requires_admin
async def delete_coupon(query: CallbackQuery) -> None:
    """
    Show confirmation dialog for deleting a coupon.
    Callback data format: "admin_coupons_delete_confirm:{coupon_id}"
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

        text = (
            f"⚠️ **تأیید حذف کوپن**\n\n"
            f"🆔 شناسه: `{coupon_id}`\n"
            f"🏷️ کد: `{coupon.get('code')}`\n"
            f"💰 تخفیف: {coupon.get('discount_value')}{'%' if coupon.get('discount_type') == 'percentage' else ' تومان'}\n"
            f"📊 وضعیت: {coupon.get('status', 'نامشخص')}\n"
            f"📈 استفاده شده: {coupon.get('used_count', 0)} بار\n\n"
            f"آیا از حذف این کوپن اطمینان دارید؟\n"
            f"این عمل **غیرقابل بازگشت** است."
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"admin_coupons_delete_execute:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data=f"admin_coupons_view:{coupon_id}"
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
    except DatabaseError as e:
        logger.error(f"Database error in delete_coupon: {e}")
        await query.message.edit_text(
            "❌ خطا در دریافت اطلاعات کوپن.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error in delete_coupon: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در نمایش تأییدیه حذف.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def execute_delete_coupon(query: CallbackQuery) -> None:
    """
    Execute deletion of a coupon.
    Callback data format: "admin_coupons_delete_execute:{coupon_id}"
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

        # Delete the coupon
        await service.delete_coupon(coupon_id, deleted_by=query.from_user.id)

        await query.message.edit_text(
            f"✅ **کوپن با موفقیت حذف شد!**\n\n"
            f"🏷️ کد: `{coupon.get('code')}`\n"
            f"🆔 شناسه: `{coupon_id}`",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
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
        logger.info(f"Coupon {coupon_id} deleted by admin {query.from_user.id}")
        await query.answer("کوپن حذف شد!")
    except NotFoundError as e:
        logger.warning(f"Coupon {coupon_id} not found: {e}")
        await query.message.edit_text(
            "❌ کوپن مورد نظر قبلاً حذف شده یا وجود ندارد.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("کوپن یافت نشد!", show_alert=True)
    except PermissionDeniedError as e:
        logger.warning(f"Permission denied deleting coupon {coupon_id}: {e}")
        await query.message.edit_text(
            "❌ شما مجوز حذف این کوپن را ندارید.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("دسترسی غیرمجاز!", show_alert=True)
    except DatabaseError as e:
        logger.error(f"Database error deleting coupon {coupon_id}: {e}")
        await query.message.edit_text(
            "❌ خطا در حذف کوپن. لطفاً دوباره تلاش کنید.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطا!", show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error deleting coupon {coupon_id}: {e}", exc_info=True)
        await query.message.edit_text(
            "❌ خطای غیرمنتظره در حذف کوپن.",
            reply_markup=get_back_button("admin_coupons")
        )
        await query.answer("خطای غیرمنتظره!", show_alert=True)


@requires_admin
async def cancel_delete_coupon(query: CallbackQuery) -> None:
    """
    Cancel deletion and return to coupon view.
    Callback data format: "admin_coupons_delete_cancel:{coupon_id}"
    """
    try:
        _, coupon_id_str = query.data.split(":", 1)
        coupon_id = int(coupon_id_str)
    except (ValueError, IndexError):
        await query.answer("❌ شناسه کوپن نامعتبر است.", show_alert=True)
        return

    await query.message.edit_text(
        "❌ عملیات حذف کوپن لغو شد.",
        reply_markup=get_back_button(f"admin_coupons_view:{coupon_id}")
    )
    await query.answer("لغو شد.")