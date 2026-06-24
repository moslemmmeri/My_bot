# src/admin_panel/modules/order_management/handlers/delete_order.py
"""
Handler for deleting an order from the admin panel.
Only accessible to admins with proper permissions.
Uses inline keyboard callbacks for interaction.
"""

from typing import Optional

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from my_bot.core.exceptions import PermissionDeniedError, NotFoundError, DatabaseError
from my_bot.core.logger import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.common.cancel_buttons import get_cancel_button

from admin_panel.core.permissions.permission_checker import requires_admin
from admin_panel.modules.order_management.services.order_delete_service import OrderDeleteService

logger = get_logger(__name__)


class DeleteOrderHandler:
    """Handles the deletion of orders via admin panel."""

    def __init__(self, delete_service: OrderDeleteService) -> None:
        self.delete_service = delete_service

    @requires_admin
    async def confirm_deletion(self, query: CallbackQuery) -> None:
        """
        Show a confirmation keyboard before deleting the order.
        Callback data format: "delete_order_confirm:{order_id}"
        """
        try:
            _, order_id_str = query.data.split(":", 1)
            order_id = int(order_id_str)
        except (ValueError, IndexError):
            await query.answer("❌ شناسه سفارش نامعتبر است.", show_alert=True)
            return

        # Store order_id in the user's state (optional) or pass via callback.
        # We'll use a temporary inline keyboard with confirm/cancel.
        confirm_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ بله، حذف شود",
                        callback_data=f"delete_order_execute:{order_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ لغو",
                        callback_data="admin_orders"  # return to order list
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به لیست سفارشات",
                        callback_data="admin_orders"
                    )
                ]
            ]
        )

        try:
            # Fetch order summary to show in confirmation message
            order_summary = await self.delete_service.get_order_summary(order_id)
            text = (
                f"⚠️ **تأیید حذف سفارش**\n\n"
                f"آیا از حذف سفارش زیر اطمینان دارید؟\n"
                f"🆔 شناسه: `{order_id}`\n"
                f"👤 کاربر: {order_summary.get('user_name', 'نامشخص')}\n"
                f"💰 مبلغ: {order_summary.get('total', 0):,} تومان\n"
                f"📅 تاریخ: {order_summary.get('created_at', 'نامشخص')}\n\n"
                f"این عمل **غیرقابل بازگشت** است."
            )
            await query.message.edit_text(
                text,
                reply_markup=confirm_kb,
                parse_mode="Markdown"
            )
            await query.answer()
        except NotFoundError as e:
            logger.warning(f"Order {order_id} not found for deletion: {e}")
            await query.message.edit_text(
                "❌ سفارش مورد نظر یافت نشد.",
                reply_markup=get_back_button("admin_orders")
            )
            await query.answer("سفارش یافت نشد!", show_alert=True)
        except Exception as e:
            logger.error(f"Error showing deletion confirmation for order {order_id}: {e}")
            await query.answer("خطا در نمایش تأییدیه حذف!", show_alert=True)

    @requires_admin
    async def execute_deletion(self, query: CallbackQuery) -> None:
        """
        Execute the deletion after confirmation.
        Callback data format: "delete_order_execute:{order_id}"
        """
        try:
            _, order_id_str = query.data.split(":", 1)
            order_id = int(order_id_str)
        except (ValueError, IndexError):
            await query.answer("❌ شناسه سفارش نامعتبر است.", show_alert=True)
            return

        try:
            # Perform deletion
            await self.delete_service.delete_order(order_id, admin_id=query.from_user.id)

            # Log the action
            logger.info(f"Order {order_id} deleted by admin {query.from_user.id}")

            # Success message
            await query.message.edit_text(
                f"✅ سفارش با شناسه `{order_id}` با موفقیت حذف شد.",
                reply_markup=get_back_button("admin_orders"),
                parse_mode="Markdown"
            )
            await query.answer("سفارش حذف شد.")
        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for admin {query.from_user.id} to delete order {order_id}: {e}")
            await query.answer("❌ شما مجوز حذف این سفارش را ندارید.", show_alert=True)
        except NotFoundError as e:
            logger.warning(f"Order {order_id} not found during deletion: {e}")
            await query.message.edit_text(
                "❌ سفارش مورد نظر قبلاً حذف شده یا وجود ندارد.",
                reply_markup=get_back_button("admin_orders")
            )
            await query.answer("سفارش یافت نشد!", show_alert=True)
        except DatabaseError as e:
            logger.error(f"Database error while deleting order {order_id}: {e}")
            await query.answer("❌ خطای پایگاه داده. لطفاً بعداً تلاش کنید.", show_alert=True)
        except Exception as e:
            logger.error(f"Unexpected error deleting order {order_id}: {e}", exc_info=True)
            await query.answer("❌ خطای غیرمنتظره. لطفاً با پشتیبانی تماس بگیرید.", show_alert=True)

    @requires_admin
    async def cancel_deletion(self, query: CallbackQuery) -> None:
        """
        Cancel the deletion process and return to order list.
        """
        try:
            await query.message.edit_text(
                "🔙 عملیات حذف لغو شد.",
                reply_markup=get_back_button("admin_orders")
            )
            await query.answer("لغو شد.")
        except TelegramBadRequest as e:
            # Handle if message already edited
            logger.debug(f"Telegram error while canceling deletion: {e}")
            await query.answer()
        except Exception as e:
            logger.error(f"Error canceling deletion: {e}")
            await query.answer("خطا در لغو عملیات!", show_alert=True)