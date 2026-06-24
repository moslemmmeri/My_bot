# src/admin_panel/modules/coupons/keyboards/coupon_actions.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional


class CouponActionsKeyboard:
    """Keyboard for coupon actions in admin panel."""

    @staticmethod
    def get_action_keyboard(
        coupon_id: int,
        back_callback: str = "admin_coupons",
    ) -> InlineKeyboardMarkup:
        """Get keyboard with main actions for a coupon."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 مشاهده جزئیات",
                        callback_data=f"admin_coupons_view:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش کوپن",
                        callback_data=f"admin_coupons_edit:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ حذف کوپن",
                        callback_data=f"admin_coupons_delete_confirm:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_edit_keyboard(
        coupon_id: int,
        back_callback: str = "admin_coupons",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for editing coupon fields."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش کد",
                        callback_data=f"admin_coupons_edit_field:{coupon_id}:code"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش نوع تخفیف",
                        callback_data=f"admin_coupons_edit_field:{coupon_id}:discount_type"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش مقدار تخفیف",
                        callback_data=f"admin_coupons_edit_field:{coupon_id}:discount_value"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش محدودیت استفاده",
                        callback_data=f"admin_coupons_edit_field:{coupon_id}:usage_limit"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش تاریخ انقضا",
                        callback_data=f"admin_coupons_edit_field:{coupon_id}:expires_at"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 تغییر وضعیت",
                        callback_data=f"admin_coupons_edit_status:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به کوپن",
                        callback_data=f"admin_coupons_view:{coupon_id}"
                    )
                ]
            ]
        )

    @staticmethod
    def get_delete_confirmation_keyboard(
        coupon_id: int,
        back_callback: str = "admin_coupons",
    ) -> InlineKeyboardMarkup:
        """Get confirmation keyboard for deleting a coupon."""
        return InlineKeyboardMarkup(
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
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_status_toggle_keyboard(
        coupon_id: int,
        current_status: str,
        back_callback: str = "admin_coupons",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for toggling coupon status."""
        status_names = {
            "active": "فعال",
            "inactive": "غیرفعال",
        }
        new_status = "active" if current_status == "inactive" else "inactive"
        return InlineKeyboardMarkup(
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
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_view_keyboard(
        coupon_id: int,
        back_callback: str = "admin_coupons",
    ) -> InlineKeyboardMarkup:
        """Get keyboard for viewing a coupon."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ ویرایش کوپن",
                        callback_data=f"admin_coupons_edit:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ حذف کوپن",
                        callback_data=f"admin_coupons_delete_confirm:{coupon_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_back_keyboard(back_callback: str = "admin_coupons") -> InlineKeyboardMarkup:
        """Get simple back keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data=back_callback
                    )
                ]
            ]
        )

    @staticmethod
    def get_cancel_keyboard(back_callback: str = "admin_coupons") -> InlineKeyboardMarkup:
        """Get simple cancel keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ انصراف",
                        callback_data=back_callback
                    )
                ]
            ]
        )