# my_bot_project/src/my_bot/presentation/handlers/payment/coupon_apply_handler.py
"""
هندلر اعمال کد تخفیف (Coupon Apply Handler).

این هندلر مسئولیت اعمال کدهای تخفیف به پرداخت‌ها و سفارشات را بر عهده دارد.
"""

from typing import Optional, Dict, Any

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode

from my_bot.application.services.coupon.coupon_validation import CouponValidationService
from my_bot.application.services.coupon.coupon_generation import CouponGenerationService
from my_bot.core.exceptions.not_found_errors import CouponNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.presentation.keyboards.common.back_buttons import get_back_button
from my_bot.presentation.keyboards.payment.coupon_keyboards import get_coupon_keyboard
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class CouponApplyHandler:
    """
    هندلر اعمال کد تخفیف.

    این کلاس مسئولیت اعمال کدهای تخفیف به پرداخت‌ها و سفارشات را بر عهده دارد.
    """

    def __init__(
        self,
        coupon_validation_service: CouponValidationService,
        coupon_generation_service: Optional[CouponGenerationService] = None,
    ) -> None:
        """
        مقداردهی اولیه هندلر.

        Args:
            coupon_validation_service: سرویس اعتبارسنجی کوپن.
            coupon_generation_service: سرویس تولید کوپن (اختیاری).
        """
        self._coupon_validation_service = coupon_validation_service
        self._coupon_generation_service = coupon_generation_service
        self._user_coupons: Dict[int, Dict[str, Any]] = {}

    async def apply_coupon(self, callback: CallbackQuery) -> None:
        """
        شروع فرآیند اعمال کد تخفیف.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # دریافت مبلغ سفارش از وضعیت کاربر (در عمل، باید از وضعیت کاربر دریافت شود)
            # برای سادگی، یک مقدار پیش‌فرض استفاده می‌کنیم
            order_amount = Money(1000000, "IRR")

            # ذخیره مبلغ در وضعیت کاربر
            self._user_coupons[user_id] = {
                "order_amount": order_amount,
                "order_id": None,
                "applied_coupon": None,
            }

            # نمایش پیام درخواست کد تخفیف
            await callback.message.edit_text(
                text=self._build_coupon_request_text(),
                reply_markup=get_coupon_keyboard(),
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

            # دریافت وضعیت کاربر
            user_state = self._user_coupons.get(user_id)
            if not user_state:
                await message.answer(
                    "⚠️ اطلاعات پرداخت یافت نشد. لطفاً دوباره تلاش کنید.",
                    reply_markup=get_back_button("payment"),
                )
                return

            # اعتبارسنجی کد تخفیف
            try:
                validation = await self._coupon_validation_service.validate_coupon(
                    coupon_code=coupon_code,
                    user_id=user_id,
                    order_amount=user_state["order_amount"],
                )

                if validation.is_valid:
                    # ذخیره کد تخفیف در وضعیت کاربر
                    user_state["applied_coupon"] = coupon_code
                    self._user_coupons[user_id] = user_state

                    # نمایش پیام موفقیت
                    await message.answer(
                        self._build_success_message(validation),
                        reply_markup=get_back_button("payment"),
                        parse_mode="Markdown",
                    )

                    logger.info(f"Coupon {coupon_code} applied for user {user_id}")
                else:
                    # نمایش پیام خطا
                    await message.answer(
                        self._build_error_message(validation),
                        reply_markup=get_coupon_keyboard(),
                        parse_mode="Markdown",
                    )

            except CouponNotFoundError:
                await message.answer(
                    "⚠️ **کد تخفیف یافت نشد**\n\n"
                    "کد وارد شده در سیستم موجود نیست.\n\n"
                    "لطفاً کد را بررسی کرده و دوباره تلاش کنید.",
                    reply_markup=get_coupon_keyboard(),
                    parse_mode="Markdown",
                )

            except ValidationError as e:
                await message.answer(
                    f"⚠️ **خطا در اعتبارسنجی کد تخفیف**\n\n"
                    f"{e.message}\n\n"
                    "لطفاً دوباره تلاش کنید.",
                    reply_markup=get_coupon_keyboard(),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error handling coupon input: {e}")
            await message.answer(
                "⚠️ خطا در اعتبارسنجی کد تخفیف. لطفاً دوباره تلاش کنید.",
                reply_markup=get_coupon_keyboard(),
            )

    async def remove_coupon(self, callback: CallbackQuery) -> None:
        """
        حذف کد تخفیف اعمال‌شده.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            if user_id in self._user_coupons:
                self._user_coupons[user_id]["applied_coupon"] = None

            await callback.message.edit_text(
                text="✅ **کد تخفیف با موفقیت حذف شد.**\n\n"
                "می‌توانید کد جدیدی وارد کنید.",
                reply_markup=get_coupon_keyboard(),
                parse_mode="Markdown",
            )
            await callback.answer("کد تخفیف حذف شد.")

        except Exception as e:
            logger.error(f"Error removing coupon: {e}")
            await callback.answer("⚠️ خطا در حذف کد تخفیف.", show_alert=True)

    async def show_available_coupons(self, callback: CallbackQuery) -> None:
        """
        نمایش لیست کوپن‌های قابل استفاده برای کاربر.

        Args:
            callback: کالبک دریافتی از تلگرام.
        """
        try:
            user_id = callback.from_user.id

            # دریافت کوپن‌های معتبر برای کاربر
            coupons = await self._coupon_validation_service.get_valid_coupons_for_user(
                user_id=user_id,
                order_amount=Money(1000000, "IRR"),  # مبلغ پیش‌فرض
                limit=10,
            )

            if not coupons:
                await callback.message.edit_text(
                    text="📭 **کوپن‌های قابل استفاده**\n\n"
                    "در حال حاضر هیچ کوپن قابل استفاده‌ای برای شما وجود ندارد.",
                    reply_markup=get_back_button("payment"),
                    parse_mode="Markdown",
                )
                await callback.answer()
                return

            # ساخت متن لیست کوپن‌ها
            text = self._build_coupon_list_text(coupons)

            await callback.message.edit_text(
                text=text,
                reply_markup=get_back_button("payment"),
                parse_mode="Markdown",
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error showing available coupons: {e}")
            await callback.answer("⚠️ خطا در نمایش کوپن‌ها.", show_alert=True)

    def _build_coupon_request_text(self) -> str:
        """
        ساخت متن درخواست کد تخفیف.

        Returns:
            str: متن درخواست کد تخفیف.
        """
        return (
            "🎫 **اعمال کد تخفیف**\n\n"
            "لطفاً کد تخفیف خود را در پیام زیر وارد کنید.\n\n"
            "⚠️ **نکات مهم:**\n"
            "• کد تخفیف به حروف بزرگ و کوچک حساس نیست.\n"
            "• کد تخفیف باید دقیقاً وارد شود.\n"
            "• برخی کدها دارای محدودیت تاریخ اعتبار هستند.\n\n"
            "💡 برای مشاهده کوپن‌های قابل استفاده، روی دکمه «📋 مشاهده کوپن‌ها» کلیک کنید."
        )

    def _build_success_message(self, validation) -> str:
        """
        ساخت پیام موفقیت اعمال کد تخفیف.

        Args:
            validation: نتیجه اعتبارسنجی.

        Returns:
            str: پیام موفقیت.
        """
        lines = [
            "✅ **کد تخفیف با موفقیت اعمال شد!**",
            "",
            f"🎫 کد: `{validation.coupon.code}`",
            f"💰 مبلغ تخفیف: {validation.discount_amount.amount:,.0f} تومان",
        ]

        if validation.coupon.description:
            lines.append(f"📝 توضیحات: {validation.coupon.description}")

        lines.extend([
            "",
            "💡 مبلغ نهایی قابل پرداخت کاهش یافت.",
        ])

        return "\n".join(lines)

    def _build_error_message(self, validation) -> str:
        """
        ساخت پیام خطای اعتبارسنجی.

        Args:
            validation: نتیجه اعتبارسنجی.

        Returns:
            str: پیام خطا.
        """
        return (
            "⚠️ **کد تخفیف نامعتبر است**\n\n"
            f"دلیل: {validation.message}\n\n"
            "لطفاً کد را بررسی کرده و دوباره تلاش کنید."
        )

    def _build_coupon_list_text(self, coupons) -> str:
        """
        ساخت متن لیست کوپن‌ها.

        Args:
            coupons: لیست کوپن‌ها.

        Returns:
            str: متن لیست کوپن‌ها.
        """
        lines = ["🎫 **کوپن‌های قابل استفاده**", ""]

        for i, coupon in enumerate(coupons, 1):
            discount_display = coupon.get_discount_display()
            status = "✅ فعال" if coupon.is_usable() else "⏸️ غیرفعال"

            lines.extend([
                f"{i}. **{coupon.code}**",
                f"   💰 تخفیف: {discount_display}",
                f"   📌 وضعیت: {status}",
            ])

            if coupon.min_order_amount:
                lines.append(
                    f"   💳 حداقل سفارش: {coupon.min_order_amount:,.0f} تومان"
                )

            if coupon.valid_until:
                lines.append(
                    f"   📅 انقضا: {coupon.valid_until.strftime('%Y-%m-%d')}"
                )

            if coupon.description:
                lines.append(f"   📝 {coupon.description}")

            lines.append("")

        lines.append(
            "💡 **نکته**: برای اعمال هر کد، آن را در پیام وارد کنید."
        )

        return "\n".join(lines)

    def get_applied_coupon(self, user_id: int) -> Optional[str]:
        """
        دریافت کد تخفیف اعمال‌شده برای کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            Optional[str]: کد تخفیف یا None.
        """
        user_state = self._user_coupons.get(user_id)
        if user_state:
            return user_state.get("applied_coupon")
        return None

    def clear_user_coupon(self, user_id: int) -> None:
        """
        پاک کردن کد تخفیف کاربر.

        Args:
            user_id: شناسه کاربر.
        """
        if user_id in self._user_coupons:
            self._user_coupons[user_id]["applied_coupon"] = None