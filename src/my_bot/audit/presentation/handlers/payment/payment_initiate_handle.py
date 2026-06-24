# my_bot_project/src/my_bot/presentation/handlers/payment/payment_initiate_handler.py
"""
هندلر شروع پرداخت (Payment Initiate Handler).

این هندلر مسئولیت شروع فرآیند پرداخت، نمایش اطلاعات پرداخت
و ارسال کاربر به درگاه پرداخت را بر عهده دارد.
"""

from typing import Optional, Dict, Any

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.use_cases.payment.initiate_payment import InitiatePaymentUseCase
from my_bot.application.use_cases.order.create_order import CreateOrderUseCase
from my_bot.application.services.coupon.coupon_validation import CouponValidationService
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.payment.payment_keyboards import get_payment_keyboard
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class PaymentInitiateHandler:
    """
    هندلر شروع پرداخت.

    این کلاس مسئولیت شروع فرآیند پرداخت را بر عهده دارد.
    """

    def __init__(
        self,
        initiate_payment_use_case: InitiatePaymentUseCase,
        coupon_validation_service: Optional[CouponValidationService] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            initiate_payment_use_case: Use Case شروع پرداخت.
            coupon_validation_service: سرویس اعتبارسنجی کوپن (اختیاری).
        """
        self._initiate_payment_use_case = initiate_payment_use_case
        self._coupon_validation_service = coupon_validation_service
        self._user_coupons: Dict[int, str] = {}  # ذخیره کد کوپن وارد شده توسط کاربر

    async def initiate_payment(
        self,
        callback: CallbackQuery,
        order_id: Optional[int] = None,
        amount: Optional[float] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        شروع فرآیند پرداخت.

        Args:
            callback: کالبک دریافتی از تلگرام.
            order_id: شناسه سفارش (اختیاری).
            amount: مبلغ پرداختی (اختیاری).
            description: توضیحات پرداخت (اختیاری).
        """
        try:
            user_id = callback.from_user.id

            # اگر order_id مشخص شده باشد، پرداخت برای سفارش انجام می‌شود
            if order_id:
                result = await self._initiate_payment_use_case.execute_for_order(
                    order_id=order_id,
                    user_id=user_id,
                )
            else:
                # پرداخت مستقیم با مبلغ مشخص
                if not amount or amount <= 0:
                    await callback.answer("⚠️ مبلغ پرداخت نامعتبر است.", show_alert=True)
                    return

                result = await self._initiate_payment_use_case.execute(
                    user_id=user_id,
                    amount=amount,
                    currency="IRR",
                    description=description or "پرداخت از طریق ربات",
                )

            # نمایش اطلاعات پرداخت
            payment = result["payment"]
            payment_url = result["payment_url"]

            # ساخت پیام پرداخت
            payment_text = self._build_payment_text(payment, payment_url)

            # کیبورد پرداخت
            keyboard = get_payment_keyboard(
                payment_id=payment.id,
                payment_url=payment_url,
                status=payment.status,
            )

            await callback.message.edit_text(
                text=payment_text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await callback.answer("💳 در حال آماده‌سازی پرداخت...")

        except Exception as e:
            logger.error(f"Error initiating payment: {e}")
            await callback.message.edit_text(
                text="⚠️ **خطا در شروع پرداخت**\n\n"
                "متأسفانه خطایی در شروع پرداخت رخ داد.\n"
                f"خطا: {str(e)}\n\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=get_back_button("profile"),
                parse_mode="Markdown",
            )
            await callback.answer("⚠️ خطا در شروع پرداخت.", show_alert=True)

    async def apply_coupon(self, callback: CallbackQuery) -> None:
        """
        اعمال کد تخفیف به پرداخت.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # درخواست وارد کردن کد تخفیف از کاربر
            await callback.message.edit_text(
                text="🎫 **اعمال کد تخفیف**\n\n"
                "لطفاً کد تخفیف خود را وارد کنید.\n\n"
                "⚠️ توجه: کد تخفیف باید به‌صورت دقیق وارد شود.",
                reply_markup=get_back_button("payment"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error applying coupon: {e}")
            await callback.answer("⚠️ خطا در اعمال کد تخفیف.", show_alert=True)

    async def handle_coupon_input(self, message: Message) -> None:
        """
        پردازش کد تخفیف وارد شده توسط کاربر.

        Args:
            message: پیام دریافتی از تلگرام.
        """
        try:
            user_id = message.from_user.id
            coupon_code = message.text.strip()

            if not coupon_code:
                await message.answer(
                    "⚠️ کد تخفیف نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید.",
                    reply_markup=get_back_button("payment"),
                )
                return

            # اعتبارسنجی کد تخفیف
            if self._coupon_validation_service:
                # دریافت مبلغ پرداخت از وضعیت کاربر
                # در عمل، باید مبلغ را از وضعیت کاربر دریافت کنیم
                # برای سادگی، از یک مبلغ ثابت استفاده می‌کنیم
                order_amount = Money(1000000, "IRR")

                validation = await self._coupon_validation_service.validate_coupon(
                    coupon_code=coupon_code,
                    user_id=user_id,
                    order_amount=order_amount,
                )

                if validation.is_valid:
                    # ذخیره کد تخفیف در وضعیت کاربر
                    self._user_coupons[user_id] = coupon_code

                    discount_amount = validation.discount_amount
                    await message.answer(
                        f"✅ **کد تخفیف با موفقیت اعمال شد!**\n\n"
                        f"🎫 کد: `{coupon_code}`\n"
                        f"💰 مبلغ تخفیف: {discount_amount.amount:,.0f} تومان\n\n"
                        f"مبلغ نهایی قابل پرداخت کاهش یافت.",
                        reply_markup=get_back_button("payment"),
                        parse_mode="Markdown",
                    )
                else:
                    await message.answer(
                        f"⚠️ **کد تخفیف نامعتبر است**\n\n"
                        f"دلیل: {validation.message}\n\n"
                        "لطفاً کد را بررسی کرده و دوباره تلاش کنید.",
                        reply_markup=get_back_button("payment"),
                        parse_mode="Markdown",
                    )
            else:
                await message.answer(
                    "⚠️ سرویس اعتبارسنجی کوپن در دسترس نیست.",
                    reply_markup=get_back_button("payment"),
                )

        except Exception as e:
            logger.error(f"Error handling coupon input: {e}")
            await message.answer(
                "⚠️ خطا در اعتبارسنجی کد تخفیف. لطفاً دوباره تلاش کنید.",
                reply_markup=get_back_button("payment"),
            )

    def _build_payment_text(self, payment, payment_url: Optional[str] = None) -> str:
        """
        ساخت متن اطلاعات پرداخت.

        Args:
            payment: اطلاعات پرداخت.
            payment_url: لینک پرداخت (اختیاری).

        Returns:
            str: متن پرداخت.
        """
        status_emoji = {
            "pending": "⏳",
            "processing": "🔄",
            "success": "✅",
            "failed": "❌",
            "canceled": "🚫",
            "refunded": "💰",
            "expired": "⌛",
        }.get(payment.status.value, "❓")

        lines = [
            "💳 **اطلاعات پرداخت**",
            "",
            f"🆔 شناسه پرداخت: `{payment.id}`",
            f"💰 مبلغ: {payment.get_formatted_amount()}",
            f"📌 وضعیت: {status_emoji} {payment.status.display_name}",
        ]

        if payment.order_id:
            lines.append(f"🛒 شناسه سفارش: `{payment.order_id}`")

        if payment.transaction_id:
            lines.append(f"🔑 شناسه تراکنش: `{payment.transaction_id}`")

        if payment.paid_at:
            lines.append(f"📅 تاریخ پرداخت: {payment.paid_at.strftime('%Y-%m-%d %H:%M')}")

        if payment.error_message:
            lines.append(f"⚠️ خطا: {payment.error_message}")

        if payment_url:
            lines.extend([
                "",
                "🔗 **لینک پرداخت**:",
                f"[کلیک کنید تا به درگاه پرداخت هدایت شوید]({payment_url})",
            ])

        lines.extend([
            "",
            "💡 **نکته**: پس از پرداخت، وضعیت سفارش به‌صورت خودکار به‌روزرسانی می‌شود.",
        ])

        return "\n".join(lines)

    def _build_coupon_text(self, coupon_code: str, discount_amount: float) -> str:
        """
        ساخت متن اعمال کد تخفیف.

        Args:
            coupon_code: کد تخفیف.
            discount_amount: مبلغ تخفیف.

        Returns:
            str: متن اعمال کد تخفیف.
        """
        return (
            f"✅ **کد تخفیف با موفقیت اعمال شد!**\n\n"
            f"🎫 کد: `{coupon_code}`\n"
            f"💰 مبلغ تخفیف: {discount_amount:,.0f} تومان\n\n"
            "مبلغ نهایی قابل پرداخت کاهش یافت."
        )