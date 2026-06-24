# my_bot_project/src/my_bot/application/services/payment/payment_verification.py
"""
سرویس تأیید پرداخت (Payment Verification Service).

این سرویس مسئولیت تأیید و اعتبارسنجی پرداخت‌های انجام‌شده را بر عهده دارد.
شامل عملیات‌های تأیید با درگاه، اعتبارسنجی داده‌های بازگشتی،
بروزرسانی وضعیت پرداخت و مدیریت خطاهای تأیید است.
"""

from typing import Optional, Dict, Any

from my_bot.application.dtos.payment_dto import PaymentCallbackDTO, PaymentResponseDTO
from my_bot.application.services.payment.payment_gateway import PaymentGatewayService
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.exceptions.not_found_errors import PaymentNotFoundError
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.payment_errors import (
    PaymentVerificationError,
    PaymentGatewayError,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.payment import Payment
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.repositories.order_repository import OrderRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class PaymentVerificationService:
    """
    سرویس تأیید پرداخت.

    این کلاس مسئولیت تأیید و اعتبارسنجی پرداخت‌های انجام‌شده را بر عهده دارد.
    """

    def __init__(
        self,
        payment_repository: PaymentRepository,
        order_repository: OrderRepository,
        gateway_service: PaymentGatewayService,
        message_publisher: Optional[MessagePublisher] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس تأیید پرداخت.

        Args:
            payment_repository: ریپازیتوری پرداخت.
            order_repository: ریپازیتوری سفارش.
            gateway_service: سرویس درگاه پرداخت.
            message_publisher: انتشاردهنده پیام (اختیاری).
        """
        self._payment_repository = payment_repository
        self._order_repository = order_repository
        self._gateway_service = gateway_service
        self._message_publisher = message_publisher

    async def verify_payment(
        self,
        payment_id: int,
        callback_data: Dict[str, Any],
        gateway_name: Optional[str] = None,
    ) -> PaymentResponseDTO:
        """
        تأیید یک پرداخت با استفاده از داده‌های بازگشتی از درگاه.

        Args:
            payment_id: شناسه پرداخت در سیستم.
            callback_data: داده‌های بازگشتی از درگاه.
            gateway_name: نام درگاه پرداخت (اختیاری).

        Returns:
            PaymentResponseDTO: اطلاعات پرداخت تأییدشده.

        Raises:
            PaymentNotFoundError: اگر پرداخت وجود نداشته باشد.
            PaymentVerificationError: اگر تأیید پرداخت ناموفق باشد.
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        # دریافت پرداخت از دیتابیس
        payment = await self._payment_repository.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id=str(payment_id))

        # بررسی وضعیت فعلی پرداخت
        if payment.status.is_final():
            logger.warning(f"Payment {payment_id} already in final status: {payment.status.value}")
            return PaymentResponseDTO.from_entity(payment)

        # اعتبارسنجی داده‌های بازگشتی
        try:
            callback_dto = self._validate_callback_data(callback_data)
        except ValidationError as e:
            logger.error(f"Invalid callback data for payment {payment_id}: {e}")
            await self._mark_payment_as_failed(payment, str(e))
            raise PaymentVerificationError(
                message="داده‌های بازگشتی از درگاه نامعتبر است.",
                context={"payment_id": payment_id, "error": str(e)},
            )

        try:
            # تأیید پرداخت با درگاه
            gateway_response = await self._gateway_service.verify_payment(
                transaction_id=callback_dto.transaction_id,
                amount=payment.amount,
                callback_data=callback_data,
                gateway_name=gateway_name or payment.gateway,
            )

            if not gateway_response.success:
                await self._mark_payment_as_failed(
                    payment,
                    gateway_response.message or "Payment verification failed",
                )
                raise PaymentVerificationError(
                    message=gateway_response.message or "تأیید پرداخت ناموفق بود.",
                    context={"payment_id": payment_id},
                )

            # بروزرسانی پرداخت به‌عنوان موفق
            updated_payment = await self._update_payment_success(
                payment,
                transaction_id=callback_dto.transaction_id,
                reference_id=callback_dto.reference_id,
                tracking_code=gateway_response.tracking_code,
                callback_data=callback_data,
            )

            logger.info(f"Payment {payment_id} verified successfully.")
            return PaymentResponseDTO.from_entity(updated_payment)

        except (PaymentGatewayError, PaymentVerificationError) as e:
            # اگر خطای درگاه یا تأیید رخ داد، پرداخت را ناموفق علامت بزن
            await self._mark_payment_as_failed(payment, str(e))
            raise

        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {e}")
            await self._mark_payment_as_failed(payment, f"Unexpected error: {str(e)}")
            raise PaymentVerificationError(
                message=f"خطای غیرمنتظره در تأیید پرداخت: {str(e)}",
                context={"payment_id": payment_id},
            )

    async def verify_by_transaction_id(
        self,
        transaction_id: str,
        callback_data: Dict[str, Any],
        gateway_name: Optional[str] = None,
    ) -> PaymentResponseDTO:
        """
        تأیید پرداخت با شناسه تراکنش در درگاه.

        Args:
            transaction_id: شناسه تراکنش در درگاه.
            callback_data: داده‌های بازگشتی از درگاه.
            gateway_name: نام درگاه پرداخت (اختیاری).

        Returns:
            PaymentResponseDTO: اطلاعات پرداخت تأییدشده.

        Raises:
            PaymentNotFoundError: اگر پرداخت وجود نداشته باشد.
            PaymentVerificationError: اگر تأیید پرداخت ناموفق باشد.
        """
        # دریافت پرداخت با شناسه تراکنش
        payment = await self._payment_repository.get_by_transaction_id(transaction_id)
        if not payment:
            raise PaymentNotFoundError(payment_id=f"transaction_{transaction_id}")

        if not payment.id:
            raise PaymentNotFoundError(payment_id="unknown")

        return await self.verify_payment(payment.id, callback_data, gateway_name)

    async def verify_webhook_payment(
        self,
        gateway_name: str,
        webhook_data: Dict[str, Any],
    ) -> PaymentResponseDTO:
        """
        پردازش وب‌هوک دریافتی از درگاه برای تأیید پرداخت.

        Args:
            gateway_name: نام درگاه پرداخت.
            webhook_data: داده‌های وب‌هوک.

        Returns:
            PaymentResponseDTO: اطلاعات پرداخت تأییدشده.

        Raises:
            PaymentVerificationError: اگر تأیید پرداخت ناموفق باشد.
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        # دریافت درگاه
        gateway = self._gateway_service.get_gateway(gateway_name)

        try:
            # پردازش وب‌هوک توسط درگاه
            webhook_result = await gateway.process_webhook(webhook_data)
            if not webhook_result.success:
                raise PaymentVerificationError(
                    message=webhook_result.message or "پردازش وب‌هوک ناموفق بود.",
                    context={"gateway": gateway_name},
                )

            # دریافت پرداخت با شناسه تراکنش
            payment = await self._payment_repository.get_by_transaction_id(
                webhook_result.transaction_id
            )
            if not payment:
                raise PaymentNotFoundError(
                    payment_id=f"transaction_{webhook_result.transaction_id}"
                )

            if not payment.id:
                raise PaymentNotFoundError(payment_id="unknown")

            # بروزرسانی پرداخت
            updated_payment = await self._update_payment_success(
                payment,
                transaction_id=webhook_result.transaction_id,
                reference_id=webhook_result.reference_id,
                tracking_code=webhook_result.tracking_code,
                callback_data=webhook_data,
            )

            logger.info(f"Payment {payment.id} verified via webhook.")
            return PaymentResponseDTO.from_entity(updated_payment)

        except (PaymentGatewayError, PaymentVerificationError):
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise PaymentVerificationError(
                message=f"خطا در پردازش وب‌هوک: {str(e)}",
                context={"gateway": gateway_name},
            )

    async def check_payment_status(
        self,
        payment_id: int,
        gateway_name: Optional[str] = None,
    ) -> PaymentStatus:
        """
        بررسی وضعیت پرداخت از درگاه و بروزرسانی در سیستم.

        Args:
            payment_id: شناسه پرداخت.
            gateway_name: نام درگاه پرداخت (اختیاری).

        Returns:
            PaymentStatus: وضعیت پرداخت.

        Raises:
            PaymentNotFoundError: اگر پرداخت وجود نداشته باشد.
        """
        payment = await self._payment_repository.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id=str(payment_id))

        # اگر پرداخت در وضعیت نهایی است، وضعیت فعلی را برمی‌گردانیم
        if payment.status.is_final():
            return payment.status

        try:
            # دریافت وضعیت از درگاه
            status = await self._gateway_service.get_payment_status(
                transaction_id=payment.transaction_id or "unknown",
                gateway_name=gateway_name or payment.gateway,
            )

            # اگر وضعیت تغییر کرده، بروزرسانی می‌کنیم
            if status != payment.status:
                if status == PaymentStatus.SUCCESS:
                    await self._update_payment_success(payment, payment.transaction_id or "")
                elif status == PaymentStatus.FAILED:
                    await self._mark_payment_as_failed(payment, "Payment failed from gateway")
                elif status == PaymentStatus.REFUNDED:
                    await self._mark_payment_as_refunded(payment, "Refunded from gateway")

            return status

        except Exception as e:
            logger.error(f"Error checking payment status for {payment_id}: {e}")
            return payment.status

    async def _update_payment_success(
        self,
        payment: Payment,
        transaction_id: str,
        reference_id: Optional[str] = None,
        tracking_code: Optional[str] = None,
        callback_data: Optional[Dict[str, Any]] = None,
    ) -> Payment:
        """
        بروزرسانی پرداخت به‌عنوان موفق.

        Args:
            payment: موجودیت پرداخت.
            transaction_id: شناسه تراکنش در درگاه.
            reference_id: شناسه مرجع (اختیاری).
            tracking_code: کد رهگیری (اختیاری).
            callback_data: داده‌های بازگشتی (اختیاری).

        Returns:
            Payment: پرداخت به‌روزرسانی‌شده.
        """
        # بروزرسانی پرداخت
        payment.mark_as_success(
            transaction_id=transaction_id,
            reference_id=reference_id,
            tracking_code=tracking_code,
            callback_data=callback_data,
        )

        # ذخیره در دیتابیس
        updated_payment = await self._payment_repository.save(payment)

        # بروزرسانی سفارش مرتبط
        if payment.order_id:
            try:
                await self._order_repository.add_payment_id(
                    order_id=int(payment.order_id),
                    payment_id=str(updated_payment.id) if updated_payment.id else "",
                )
                await self._order_repository.update_status(
                    order_id=int(payment.order_id),
                    new_status="paid",
                    reason="Payment successful",
                )
                logger.info(f"Order {payment.order_id} marked as paid for payment {updated_payment.id}")
            except Exception as e:
                logger.error(f"Error updating order {payment.order_id}: {e}")

        # انتشار رویداد پرداخت موفق
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="payment.succeeded",
                event_data={
                    "payment_id": updated_payment.id,
                    "user_id": updated_payment.user_id,
                    "order_id": updated_payment.order_id,
                    "amount": updated_payment.amount.amount,
                    "currency": updated_payment.amount.currency,
                    "transaction_id": transaction_id,
                    "tracking_code": tracking_code,
                },
                source="PaymentVerificationService",
            )

            # ارسال نوتیفیکیشن به کاربر
            if updated_payment.user_id:
                await self._message_publisher.publish_notification(
                    user_id=updated_payment.user_id,
                    notification_type="payment_success",
                    data={
                        "amount": updated_payment.amount.amount,
                        "currency": updated_payment.amount.currency,
                        "order_id": updated_payment.order_id,
                        "tracking_code": tracking_code,
                    },
                )

        return updated_payment

    async def _mark_payment_as_failed(
        self,
        payment: Payment,
        error_message: str,
    ) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان ناموفق.

        Args:
            payment: موجودیت پرداخت.
            error_message: پیام خطا.
        """
        payment.mark_as_failed(error_message)
        await self._payment_repository.save(payment)

        logger.warning(f"Payment {payment.id} marked as failed: {error_message}")

        # انتشار رویداد پرداخت ناموفق
        if self._message_publisher:
            await self._message_publisher.publish_event(
                event_type="payment.failed",
                event_data={
                    "payment_id": payment.id,
                    "user_id": payment.user_id,
                    "order_id": payment.order_id,
                    "error": error_message,
                },
                source="PaymentVerificationService",
            )

    async def _mark_payment_as_refunded(
        self,
        payment: Payment,
        reason: Optional[str] = None,
    ) -> None:
        """
        علامت‌گذاری پرداخت به‌عنوان بازگشت‌وجه.

        Args:
            payment: موجودیت پرداخت.
            reason: دلیل بازگشت وجه (اختیاری).
        """
        payment.mark_as_refunded(reason)
        await self._payment_repository.save(payment)

        logger.info(f"Payment {payment.id} marked as refunded")

    def _validate_callback_data(self, callback_data: Dict[str, Any]) -> PaymentCallbackDTO:
        """
        اعتبارسنجی داده‌های بازگشتی از درگاه.

        Args:
            callback_data: داده‌های بازگشتی.

        Returns:
            PaymentCallbackDTO: داده‌های اعتبارسنجی‌شده.

        Raises:
            ValidationError: اگر داده‌ها نامعتبر باشند.
        """
        # بررسی وجود فیلدهای اجباری
        if not callback_data:
            raise ValidationError(
                message="داده‌های بازگشتی نمی‌تواند خالی باشد.",
                context={"callback_data": callback_data},
            )

        # استخراج اطلاعات کلیدی
        transaction_id = callback_data.get("transaction_id") or callback_data.get("tracking_code")
        if not transaction_id:
            # تلاش برای یافتن در مکان‌های دیگر
            for key in ["Authority", "authority", "id", "payment_id", "ref_id", "ref"]:
                if key in callback_data:
                    transaction_id = callback_data[key]
                    break

        if not transaction_id:
            raise ValidationError(
                message="شناسه تراکنش در داده‌های بازگشتی یافت نشد.",
                context={"callback_data": callback_data},
            )

        return PaymentCallbackDTO(
            transaction_id=str(transaction_id),
            reference_id=callback_data.get("reference_id") or callback_data.get("ref_id"),
            tracking_code=callback_data.get("tracking_code"),
            status=callback_data.get("status", "success"),
            metadata=callback_data,
        )