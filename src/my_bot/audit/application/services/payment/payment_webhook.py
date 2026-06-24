# my_bot_project/src/my_bot/application/services/payment/payment_webhook.py
"""
سرویس پردازش وب‌هوک پرداخت (Payment Webhook Service).

این سرویس مسئولیت دریافت، پردازش و اعتبارسنجی وب‌هوک‌های دریافتی
از درگاه‌های پرداخت مختلف را بر عهده دارد. وب‌هوک‌ها می‌توانند
شامل رویدادهای تأیید پرداخت، بازگشت وجه، یا وضعیت‌های دیگر باشند.
"""

import json
import hmac
import hashlib
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime

from my_bot.application.dtos.payment_dto import PaymentWebhookDTO, PaymentResponseDTO
from my_bot.application.services.payment.payment_verification import PaymentVerificationService
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.exceptions.payment_errors import (
    PaymentWebhookError,
    PaymentVerificationError,
)
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.interfaces.repositories.payment_repository import PaymentRepository
from my_bot.domain.interfaces.messaging.message_publisher import MessagePublisher

logger = get_logger(__name__)


@dataclass
class WebhookHandler:
    """
    ساختار یک هندلر برای وب‌هوک‌های درگاه پرداخت.

    Attributes:
        gateway: نام درگاه پرداخت.
        secret: کلید مخفی برای اعتبارسنجی (اختیاری).
        handler: تابع پردازش وب‌هوک.
        is_active: فعال بودن هندلر.
    """
    gateway: str
    handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    secret: Optional[str] = None
    is_active: bool = True


class PaymentWebhookService:
    """
    سرویس پردازش وب‌هوک پرداخت.

    این کلاس مسئولیت دریافت و پردازش وب‌هوک‌های دریافتی از درگاه‌های
    پرداخت مختلف را بر عهده دارد.
    """

    def __init__(
        self,
        payment_repository: PaymentRepository,
        verification_service: PaymentVerificationService,
        message_publisher: Optional[MessagePublisher] = None,
    ) -> None:
        """
        مقداردهی اولیه سرویس وب‌هوک.

        Args:
            payment_repository: ریپازیتوری پرداخت.
            verification_service: سرویس تأیید پرداخت.
            message_publisher: انتشاردهنده پیام (اختیاری).
        """
        self._payment_repository = payment_repository
        self._verification_service = verification_service
        self._message_publisher = message_publisher
        self._handlers: Dict[str, WebhookHandler] = {}

    def register_handler(
        self,
        gateway: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        secret: Optional[str] = None,
        is_active: bool = True,
    ) -> None:
        """
        ثبت یک هندلر برای درگاه پرداخت خاص.

        Args:
            gateway: نام درگاه پرداخت.
            handler: تابع پردازش وب‌هوک (async).
            secret: کلید مخفی برای اعتبارسنجی (اختیاری).
            is_active: فعال بودن هندلر (پیش‌فرض True).
        """
        self._handlers[gateway] = WebhookHandler(
            gateway=gateway,
            handler=handler,
            secret=secret,
            is_active=is_active,
        )
        logger.info(f"Webhook handler registered for gateway: {gateway}")

    def unregister_handler(self, gateway: str) -> bool:
        """
        حذف یک هندلر.

        Args:
            gateway: نام درگاه پرداخت.

        Returns:
            True در صورت حذف موفق، False در صورت عدم وجود.
        """
        if gateway in self._handlers:
            del self._handlers[gateway]
            logger.info(f"Webhook handler unregistered for gateway: {gateway}")
            return True
        return False

    async def process_webhook(
        self,
        gateway: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
    ) -> PaymentWebhookDTO:
        """
        پردازش وب‌هوک دریافتی از یک درگاه پرداخت.

        Args:
            gateway: نام درگاه پرداخت.
            payload: داده‌های وب‌هوک.
            signature: امضای دریافتی برای اعتبارسنجی (اختیاری).

        Returns:
            PaymentWebhookDTO: نتیجه پردازش وب‌هوک.

        Raises:
            PaymentWebhookError: اگر وب‌هوک نامعتبر باشد یا خطایی رخ دهد.
        """
        # بررسی وجود هندلر
        handler_info = self._handlers.get(gateway)
        if not handler_info:
            raise PaymentWebhookError(
                message=f"هیچ هندلری برای درگاه '{gateway}' ثبت نشده است.",
                context={"gateway": gateway},
            )

        if not handler_info.is_active:
            raise PaymentWebhookError(
                message=f"هندلر درگاه '{gateway}' غیرفعال است.",
                context={"gateway": gateway},
            )

        # اعتبارسنجی امضا (در صورت وجود)
        if handler_info.secret and signature:
            if not self._validate_signature(
                payload=payload,
                signature=signature,
                secret=handler_info.secret,
            ):
                raise PaymentWebhookError(
                    message="امضای وب‌هوک نامعتبر است.",
                    context={"gateway": gateway},
                )

        try:
            # پردازش وب‌هوک با هندلر
            processed_data = await handler_info.handler(payload)

            # تبدیل به DTO
            webhook_dto = self._to_dto(processed_data, gateway)

            # پردازش رویداد وب‌هوک
            result = await self._process_webhook_event(webhook_dto)

            logger.info(f"Webhook processed successfully for gateway: {gateway}")
            return result

        except PaymentWebhookError:
            raise
        except Exception as e:
            logger.error(f"Error processing webhook for gateway {gateway}: {e}")
            raise PaymentWebhookError(
                message=f"خطا در پردازش وب‌هوک: {str(e)}",
                context={"gateway": gateway, "error": str(e)},
            )

    async def _process_webhook_event(
        self,
        webhook_dto: PaymentWebhookDTO,
    ) -> PaymentWebhookDTO:
        """
        پردازش رویداد وب‌هوک.

        Args:
            webhook_dto: داده‌های وب‌هوک.

        Returns:
            PaymentWebhookDTO: نتیجه پردازش.

        Raises:
            PaymentWebhookError: در صورت خطا در پردازش.
        """
        # بر اساس نوع رویداد اقدام می‌کنیم
        event_type = webhook_dto.event_type

        if event_type == "payment_success":
            return await self._handle_payment_success(webhook_dto)

        elif event_type == "payment_failed":
            return await self._handle_payment_failed(webhook_dto)

        elif event_type == "payment_refunded":
            return await self._handle_payment_refunded(webhook_dto)

        elif event_type == "payment_verification":
            return await self._handle_payment_verification(webhook_dto)

        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            webhook_dto.success = True
            webhook_dto.message = f"Event type '{event_type}' handled as unknown."
            return webhook_dto

    async def _handle_payment_success(
        self,
        webhook_dto: PaymentWebhookDTO,
    ) -> PaymentWebhookDTO:
        """
        پردازش رویداد پرداخت موفق.

        Args:
            webhook_dto: داده‌های وب‌هوک.

        Returns:
            PaymentWebhookDTO: نتیجه پردازش.
        """
        try:
            # دریافت پرداخت با شناسه تراکنش
            payment = await self._payment_repository.get_by_transaction_id(
                webhook_dto.transaction_id
            )

            if not payment:
                # اگر پرداخت وجود ندارد، سعی می‌کنیم آن را ایجاد کنیم (در صورت امکان)
                logger.warning(f"Payment not found for transaction: {webhook_dto.transaction_id}")
                webhook_dto.success = False
                webhook_dto.message = "Payment not found."
                return webhook_dto

            if not payment.id:
                webhook_dto.success = False
                webhook_dto.message = "Payment ID is missing."
                return webhook_dto

            # اگر پرداخت در وضعیت نهایی است، نیازی به تأیید مجدد نیست
            if payment.status.is_final():
                webhook_dto.success = True
                webhook_dto.message = f"Payment already in final status: {payment.status.value}"
                return webhook_dto

            # تأیید پرداخت
            await self._verification_service.verify_payment(
                payment_id=payment.id,
                callback_data=webhook_dto.raw_data,
                gateway_name=webhook_dto.gateway,
            )

            webhook_dto.success = True
            webhook_dto.message = "Payment verified successfully."
            return webhook_dto

        except PaymentVerificationError as e:
            logger.error(f"Payment verification failed: {e}")
            webhook_dto.success = False
            webhook_dto.message = f"Verification failed: {e.message}"
            webhook_dto.error = str(e)
            return webhook_dto

        except Exception as e:
            logger.error(f"Error handling payment success webhook: {e}")
            webhook_dto.success = False
            webhook_dto.message = f"Error: {str(e)}"
            webhook_dto.error = str(e)
            return webhook_dto

    async def _handle_payment_failed(
        self,
        webhook_dto: PaymentWebhookDTO,
    ) -> PaymentWebhookDTO:
        """
        پردازش رویداد پرداخت ناموفق.

        Args:
            webhook_dto: داده‌های وب‌هوک.

        Returns:
            PaymentWebhookDTO: نتیجه پردازش.
        """
        try:
            payment = await self._payment_repository.get_by_transaction_id(
                webhook_dto.transaction_id
            )

            if not payment:
                webhook_dto.success = False
                webhook_dto.message = "Payment not found."
                return webhook_dto

            # علامت‌گذاری پرداخت به‌عنوان ناموفق
            payment.mark_as_failed(
                webhook_dto.message or "Payment failed from webhook"
            )
            await self._payment_repository.save(payment)

            # انتشار رویداد پرداخت ناموفق
            if self._message_publisher:
                await self._message_publisher.publish_event(
                    event_type="payment.failed",
                    event_data={
                        "payment_id": payment.id,
                        "user_id": payment.user_id,
                        "order_id": payment.order_id,
                        "transaction_id": webhook_dto.transaction_id,
                        "error": webhook_dto.message,
                    },
                    source="PaymentWebhookService",
                )

            webhook_dto.success = True
            webhook_dto.message = "Payment marked as failed."
            return webhook_dto

        except Exception as e:
            logger.error(f"Error handling payment failed webhook: {e}")
            webhook_dto.success = False
            webhook_dto.message = f"Error: {str(e)}"
            webhook_dto.error = str(e)
            return webhook_dto

    async def _handle_payment_refunded(
        self,
        webhook_dto: PaymentWebhookDTO,
    ) -> PaymentWebhookDTO:
        """
        پردازش رویداد بازگشت وجه.

        Args:
            webhook_dto: داده‌های وب‌هوک.

        Returns:
            PaymentWebhookDTO: نتیجه پردازش.
        """
        try:
            payment = await self._payment_repository.get_by_transaction_id(
                webhook_dto.transaction_id
            )

            if not payment:
                webhook_dto.success = False
                webhook_dto.message = "Payment not found."
                return webhook_dto

            # علامت‌گذاری پرداخت به‌عنوان بازگشت‌وجه
            payment.mark_as_refunded(webhook_dto.message or "Refunded from webhook")
            await self._payment_repository.save(payment)

            # انتشار رویداد بازگشت وجه
            if self._message_publisher:
                await self._message_publisher.publish_event(
                    event_type="payment.refunded",
                    event_data={
                        "payment_id": payment.id,
                        "user_id": payment.user_id,
                        "order_id": payment.order_id,
                        "transaction_id": webhook_dto.transaction_id,
                        "reason": webhook_dto.message,
                    },
                    source="PaymentWebhookService",
                )

            webhook_dto.success = True
            webhook_dto.message = "Payment marked as refunded."
            return webhook_dto

        except Exception as e:
            logger.error(f"Error handling payment refunded webhook: {e}")
            webhook_dto.success = False
            webhook_dto.message = f"Error: {str(e)}"
            webhook_dto.error = str(e)
            return webhook_dto

    async def _handle_payment_verification(
        self,
        webhook_dto: PaymentWebhookDTO,
    ) -> PaymentWebhookDTO:
        """
        پردازش رویداد تأیید پرداخت (شبیه به payment_success).

        Args:
            webhook_dto: داده‌های وب‌هوک.

        Returns:
            PaymentWebhookDTO: نتیجه پردازش.
        """
        return await self._handle_payment_success(webhook_dto)

    def _validate_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str,
    ) -> bool:
        """
        اعتبارسنجی امضای وب‌هوک.

        Args:
            payload: داده‌های وب‌هوک.
            signature: امضای دریافتی.
            secret: کلید مخفی.

        Returns:
            True اگر امضا معتبر باشد.
        """
        try:
            # محاسبه هش HMAC با SHA-256
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            expected = hmac.new(
                secret.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # مقایسه با امضای دریافتی (مقایسه امن با استفاده از hmac.compare_digest)
            return hmac.compare_digest(expected, signature)

        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            return False

    def _to_dto(
        self,
        data: Dict[str, Any],
        gateway: str,
    ) -> PaymentWebhookDTO:
        """
        تبدیل داده‌های وب‌هوک به PaymentWebhookDTO.

        Args:
            data: داده‌های وب‌هوک.
            gateway: نام درگاه پرداخت.

        Returns:
            PaymentWebhookDTO: داده‌های وب‌هوک به‌صورت DTO.
        """
        # استخراج اطلاعات کلیدی
        transaction_id = data.get("transaction_id") or data.get("tracking_code") or data.get("id")
        if not transaction_id:
            for key in ["Authority", "authority", "payment_id", "ref_id", "ref", "order_id"]:
                if key in data:
                    transaction_id = data[key]
                    break

        event_type = data.get("event_type") or data.get("type") or "payment_verification"
        status = data.get("status") or data.get("result") or "unknown"

        return PaymentWebhookDTO(
            gateway=gateway,
            transaction_id=str(transaction_id) if transaction_id else "",
            event_type=event_type,
            status=status,
            amount=data.get("amount"),
            currency=data.get("currency", "IRR"),
            tracking_code=data.get("tracking_code") or data.get("ref_id"),
            message=data.get("message") or data.get("description") or data.get("reason"),
            raw_data=data,
            success=False,  # در ابتدا False است، بعداً تنظیم می‌شود
        )

    async def health_check(self) -> bool:
        """
        بررسی سلامت سرویس وب‌هوک.

        Returns:
            True اگر سرویس سالم باشد.
        """
        return True

    def get_registered_gateways(self) -> list[str]:
        """
        دریافت لیست درگاه‌های ثبت‌شده.

        Returns:
            list[str]: لیست نام درگاه‌ها.
        """
        return list(self._handlers.keys())

    def is_gateway_active(self, gateway: str) -> bool:
        """
        بررسی فعال بودن یک درگاه.

        Args:
            gateway: نام درگاه.

        Returns:
            True اگر درگاه فعال باشد.
        """
        handler = self._handlers.get(gateway)
        return handler is not None and handler.is_active