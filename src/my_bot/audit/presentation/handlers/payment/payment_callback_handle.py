# my_bot_project/src/my_bot/presentation/handlers/payment/payment_callback_handler.py
"""
هندلر بازگشت از درگاه پرداخت (Payment Callback Handler).

این هندلر مسئولیت پردازش بازگشت کاربر از درگاه پرداخت،
تأیید تراکنش و نمایش نتیجه پرداخت را بر عهده دارد.
"""

from typing import Optional, Dict, Any

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.use_cases.payment.confirm_payment import ConfirmPaymentUseCase
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.payment.payment_keyboards import get_payment_result_keyboard
from my_bot.shared.utils.message_pool import MessagePool

logger = get_logger(__name__)


class PaymentCallbackHandler:
    """
    هندلر بازگشت از درگاه پرداخت.

    این کلاس مسئولیت پردازش بازگشت کاربر از درگاه پرداخت را بر عهده دارد.
    """

    def __init__(
        self,
        confirm_payment_use_case: ConfirmPaymentUseCase,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            confirm_payment_use_case: Use Case تأیید پرداخت.
        """
        self._confirm_payment_use_case = confirm_payment_use_case

    async def handle_callback(
        self,
        callback: CallbackQuery,
        payment_id: int,
        status: str = "success",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        پردازش بازگشت از درگاه پرداخت.

        Args:
            callback: کالبک دریافتی از تلگرام.
            payment_id: شناسه پرداخت.
            status: وضعیت بازگشت (success, failed, canceled).
            data: داده‌های اضافی (اختیاری).
        """
        try:
            # نمایش پیام در حال پردازش
            await callback.message.edit_text(
                text="⏳ **در حال تأیید پرداخت...**\n\nلطفاً منتظر بمانید.",
                parse_mode="Markdown",
            )

            # اگر وضعیت ناموفق یا لغو شده باشد، نیازی به تأیید نیست
            if status in ("failed", "canceled"):
                payment_status = PaymentStatus.FAILED if status == "failed" else PaymentStatus.CANCELED
                await self._show_payment_result(
                    callback.message,
                    payment_id,
                    payment_status,
                    data,
                )
                await callback.answer("❌ پرداخت ناموفق بود.")
                return

            # تأیید پرداخت
            try:
                result = await self._confirm_payment_use_case.execute(
                    payment_id=payment_id,
                    callback_data=data or {},
                )

                # نمایش نتیجه پرداخت
                await self._show_payment_result(
                    callback.message,
                    payment_id,
                    result.status,
                    data,
                )

                # پاسخ به کالبک
                if result.is_success():
                    await callback.answer("✅ پرداخت با موفقیت تأیید شد!")
                else:
                    await callback.answer("⚠️ پرداخت ناموفق بود.", show_alert=True)

            except Exception as e:
                logger.error(f"Error confirming payment {payment_id}: {e}")

                # نمایش خطا
                await self._show_payment_result(
                    callback.message,
                    payment_id,
                    PaymentStatus.FAILED,
                    {"error": str(e)},
                )
                await callback.answer("⚠️ خطا در تأیید پرداخت.", show_alert=True)

        except Exception as e:
            logger.error(f"Error handling payment callback: {e}")
            await callback.message.edit_text(
                text="⚠️ **خطا در پردازش بازگشت از درگاه**\n\n"
                "متأسفانه خطایی در پردازش بازگشت از درگاه پرداخت رخ داد.\n\n"
                "لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=get_back_button("profile"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ خطا در پردازش بازگشت.", show_alert=True)

    async def handle_webhook(
        self,
        payment_id: int,
        data: Dict[str, Any],
        gateway_name: str,
    ) -> Dict[str, Any]:
        """
        پردازش وب‌هوک دریافتی از درگاه پرداخت.

        Args:
            payment_id: شناسه پرداخت.
            data: داده‌های وب‌هوک.
            gateway_name: نام درگاه پرداخت.

        Returns:
            Dict[str, Any]: نتیجه پردازش وب‌هوک.
        """
        try:
            result = await self._confirm_payment_use_case.execute_by_webhook(
                gateway_name=gateway_name,
                webhook_data=data,
            )

            logger.info(
                f"Webhook processed: payment_id={payment_id}, "
                f"status={result.status.value}"
            )

            return {
                "success": True,
                "payment_id": payment_id,
                "status": result.status.value,
                "message": "Payment verified successfully",
            }

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {
                "success": False,
                "payment_id": payment_id,
                "error": str(e),
                "message": "Webhook processing failed",
            }

    async def _show_payment_result(
        self,
        message: Message,
        payment_id: int,
        status: PaymentStatus,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        نمایش نتیجه پرداخت به کاربر.

        Args:
            message: پیام برای ارسال پاسخ.
            payment_id: شناسه پرداخت.
            status: وضعیت پرداخت.
            data: داده‌های اضافی (اختیاری).
        """
        # ساخت پیام نتیجه
        result_text = self._build_result_text(status, data)

        # انتخاب کیبورد مناسب
        keyboard = get_payment_result_keyboard(status, payment_id)

        # ارسال پیام
        await message.edit_text(
            text=result_text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    def _build_result_text(self, status: PaymentStatus, data: Optional[Dict[str, Any]] = None) -> str:
        """
        ساخت متن نتیجه پرداخت.

        Args:
            status: وضعیت پرداخت.
            data: داده‌های اضافی (اختیاری).

        Returns:
            str: متن نتیجه پرداخت.
        """
        if status == PaymentStatus.SUCCESS:
            message = MessagePool.get_random_payment_success()
            lines = [
                f"✅ {message}",
                "",
                "💰 **پرداخت با موفقیت انجام شد!**",
                "",
                f"🆔 شناسه پرداخت: `{data.get('payment_id', 'نامشخص') if data else 'نامشخص'}`",
            ]

            if data and data.get("tracking_code"):
                lines.append(f"🔑 کد رهگیری: `{data['tracking_code']}`")

            if data and data.get("amount"):
                lines.append(f"💰 مبلغ: {data['amount']:,.0f} تومان")

            lines.extend([
                "",
                "📌 **مراحل بعدی:**",
                "• وضعیت سفارش شما به‌روزرسانی خواهد شد.",
                "• پیام تأیید نهایی برای شما ارسال می‌شود.",
                "",
                "🙏 از اعتماد شما سپاسگزاریم!",
            ])

        elif status == PaymentStatus.FAILED:
            lines = [
                "❌ **پرداخت ناموفق بود**",
                "",
                "متأسفانه پرداخت شما با خطا مواجه شد.",
            ]

            if data and data.get("error"):
                lines.append(f"⚠️ دلیل: {data['error']}")

            lines.extend([
                "",
                "💡 **چه کاری می‌توانید انجام دهید؟**",
                "• بررسی اطلاعات کارت و موجودی حساب",
                "• استفاده از درگاه پرداخت دیگر",
                "• تماس با پشتیبانی",
                "",
                "برای تلاش مجدد، لطفاً دوباره اقدام کنید.",
            ])

        elif status == PaymentStatus.CANCELED:
            lines = [
                "🚫 **پرداخت لغو شد**",
                "",
                "شما پرداخت را لغو کردید.",
                "",
                "💡 اگر نیاز به کمک دارید، با پشتیبانی تماس بگیرید.",
            ]

        else:
            lines = [
                "⏳ **وضعیت نامشخص**",
                "",
                "وضعیت پرداخت شما در حال بررسی است.",
                "",
                "💡 لطفاً چند دقیقه دیگر وضعیت را بررسی کنید.",
            ]

        return "\n".join(lines)