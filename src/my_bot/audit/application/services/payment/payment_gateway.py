# my_bot_project/src/my_bot/application/services/payment/payment_gateway.py
"""
سرویس درگاه پرداخت (Payment Gateway Service).

این سرویس مسئولیت ارتباط با درگاه‌های پرداخت مختلف را بر عهده دارد.
شامل ایجاد درخواست پرداخت، تأیید پرداخت، و مدیریت بازگشت وجه است.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type, Union

from my_bot.application.dtos.payment_dto import (
    PaymentCreateDTO,
    PaymentResponseDTO,
    PaymentCallbackDTO,
    PaymentGatewayResponseDTO,
)
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.exceptions.validation_errors import ValidationError
from my_bot.core.exceptions.payment_errors import (
    PaymentGatewayError,
    PaymentVerificationError,
    PaymentRefundError,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.entities.payment import Payment
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class BasePaymentGateway(ABC):
    """
    کلاس پایه برای درگاه‌های پرداخت.

    این کلاس اینترفیس مشترک برای تمام درگاه‌های پرداخت را تعریف می‌کند.
    """

    @abstractmethod
    async def initiate_payment(
        self,
        amount: Money,
        callback_url: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        شروع فرآیند پرداخت.

        Args:
            amount: مبلغ پرداختی.
            callback_url: آدرس بازگشت پس از پرداخت.
            description: توضیحات پرداخت (اختیاری).
            metadata: داده‌های اضافی (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل لینک پرداخت و شناسه تراکنش.

        Raises:
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        pass

    @abstractmethod
    async def verify_payment(
        self,
        transaction_id: str,
        amount: Money,
        callback_data: Dict[str, Any],
    ) -> PaymentGatewayResponseDTO:
        """
        تأیید پرداخت انجام‌شده.

        Args:
            transaction_id: شناسه تراکنش در درگاه.
            amount: مبلغ پرداختی.
            callback_data: داده‌های بازگشتی از درگاه.

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت تأیید.

        Raises:
            PaymentVerificationError: در صورت عدم تأیید پرداخت.
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Money] = None,
        reason: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        بازگشت وجه پرداخت.

        Args:
            transaction_id: شناسه تراکنش در درگاه.
            amount: مبلغ برای بازگشت (در صورت عدم مشخص بودن، کل مبلغ بازگشت می‌خورد).
            reason: دلیل بازگشت وجه (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت بازگشت وجه.

        Raises:
            PaymentRefundError: در صورت خطا در بازگشت وجه.
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        pass

    @abstractmethod
    async def get_payment_status(
        self,
        transaction_id: str,
    ) -> PaymentStatus:
        """
        دریافت وضعیت پرداخت از درگاه.

        Args:
            transaction_id: شناسه تراکنش در درگاه.

        Returns:
            PaymentStatus: وضعیت پرداخت.

        Raises:
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        pass


class MockGateway(BasePaymentGateway):
    """
    درگاه پرداخت شبیه‌سازی‌شده (برای تست و توسعه).

    این درگاه برای تست‌های محلی و توسعه استفاده می‌شود و
    پرداخت‌ها را به‌صورت شبیه‌سازی‌شده پردازش می‌کند.
    """

    def __init__(self, auto_approve: bool = True) -> None:
        """
        مقداردهی اولیه درگاه شبیه‌سازی‌شده.

        Args:
            auto_approve: آیا پرداخت‌ها به‌صورت خودکار تأیید شوند.
        """
        self._auto_approve = auto_approve
        self._transactions: Dict[str, Dict[str, Any]] = {}

    async def initiate_payment(
        self,
        amount: Money,
        callback_url: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentGatewayResponseDTO:
        """شروع پرداخت در درگاه شبیه‌سازی‌شده."""
        import uuid
        transaction_id = f"mock_{uuid.uuid4().hex[:16]}"

        # ذخیره تراکنش
        self._transactions[transaction_id] = {
            "amount": amount.amount,
            "currency": amount.currency,
            "callback_url": callback_url,
            "description": description,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": __import__("datetime").datetime.now(),
        }

        # لینک پرداخت شبیه‌سازی‌شده
        payment_url = f"https://mock-gateway.com/pay/{transaction_id}"

        logger.info(f"Mock payment initiated: {transaction_id}, amount={amount.amount}")
        return PaymentGatewayResponseDTO(
            success=True,
            transaction_id=transaction_id,
            payment_url=payment_url,
            gateway_data={"mock": True, "auto_approve": self._auto_approve},
        )

    async def verify_payment(
        self,
        transaction_id: str,
        amount: Money,
        callback_data: Dict[str, Any],
    ) -> PaymentGatewayResponseDTO:
        """تأیید پرداخت در درگاه شبیه‌سازی‌شده."""
        if transaction_id not in self._transactions:
            raise PaymentVerificationError(
                message=f"تراکنش با شناسه {transaction_id} یافت نشد.",
                context={"transaction_id": transaction_id},
            )

        transaction = self._transactions[transaction_id]

        # تأیید خودکار یا بر اساس callback_data
        if self._auto_approve or callback_data.get("status") == "success":
            transaction["status"] = "success"
            logger.info(f"Mock payment verified: {transaction_id}")
            return PaymentGatewayResponseDTO(
                success=True,
                transaction_id=transaction_id,
                gateway_data={"verified": True, "auto_approved": self._auto_approve},
            )
        else:
            transaction["status"] = "failed"
            logger.warning(f"Mock payment verification failed: {transaction_id}")
            raise PaymentVerificationError(
                message=f"تأیید پرداخت ناموفق بود.",
                context={"transaction_id": transaction_id},
            )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Money] = None,
        reason: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """بازگشت وجه در درگاه شبیه‌سازی‌شده."""
        if transaction_id not in self._transactions:
            raise PaymentRefundError(
                message=f"تراکنش با شناسه {transaction_id} یافت نشد.",
                context={"transaction_id": transaction_id},
            )

        transaction = self._transactions[transaction_id]
        if transaction["status"] != "success":
            raise PaymentRefundError(
                message="فقط پرداخت‌های موفق قابل بازگشت هستند.",
                context={"transaction_id": transaction_id, "status": transaction["status"]},
            )

        refund_amount = amount.amount if amount else transaction["amount"]
        transaction["status"] = "refunded"
        transaction["refund_amount"] = refund_amount
        transaction["refund_reason"] = reason

        logger.info(f"Mock payment refunded: {transaction_id}, amount={refund_amount}")
        return PaymentGatewayResponseDTO(
            success=True,
            transaction_id=transaction_id,
            gateway_data={"refunded": True, "amount": refund_amount},
        )

    async def get_payment_status(
        self,
        transaction_id: str,
    ) -> PaymentStatus:
        """دریافت وضعیت پرداخت از درگاه شبیه‌سازی‌شده."""
        if transaction_id not in self._transactions:
            return PaymentStatus.FAILED

        status = self._transactions[transaction_id].get("status", "pending")
        mapping = {
            "pending": PaymentStatus.PENDING,
            "processing": PaymentStatus.PROCESSING,
            "success": PaymentStatus.SUCCESS,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
        }
        return mapping.get(status, PaymentStatus.PENDING)


class PaymentGatewayService:
    """
    سرویس درگاه پرداخت.

    این کلاس مسئولیت مدیریت درگاه‌های پرداخت مختلف و انتخاب درگاه مناسب
    برای هر پرداخت را بر عهده دارد.
    """

    def __init__(self, default_gateway: Optional[str] = "mock") -> None:
        """
        مقداردهی اولیه سرویس درگاه پرداخت.

        Args:
            default_gateway: نام درگاه پیش‌فرض.
        """
        self._gateways: Dict[str, BasePaymentGateway] = {}
        self._default_gateway = default_gateway or "mock"

        # ثبت درگاه‌های موجود
        self._register_gateway("mock", MockGateway())

    def _register_gateway(self, name: str, gateway: BasePaymentGateway) -> None:
        """
        ثبت یک درگاه پرداخت.

        Args:
            name: نام درگاه.
            gateway: نمونه‌ی درگاه.
        """
        self._gateways[name] = gateway
        logger.info(f"Payment gateway '{name}' registered.")

    def get_gateway(self, name: Optional[str] = None) -> BasePaymentGateway:
        """
        دریافت یک درگاه پرداخت با نام مشخص.

        Args:
            name: نام درگاه (در صورت None، درگاه پیش‌فرض برگردانده می‌شود).

        Returns:
            BasePaymentGateway: نمونه‌ی درگاه.

        Raises:
            PaymentGatewayError: اگر درگاه مورد نظر یافت نشد.
        """
        gateway_name = name or self._default_gateway
        if gateway_name not in self._gateways:
            raise PaymentGatewayError(
                message=f"درگاه پرداخت '{gateway_name}' یافت نشد.",
                context={"gateway": gateway_name, "available_gateways": list(self._gateways.keys())},
            )
        return self._gateways[gateway_name]

    async def initiate_payment(
        self,
        payment: Payment,
        callback_url: str,
        gateway_name: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        شروع فرآیند پرداخت.

        Args:
            payment: موجودیت پرداخت.
            callback_url: آدرس بازگشت پس از پرداخت.
            gateway_name: نام درگاه (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه.

        Raises:
            PaymentGatewayError: در صورت بروز خطا در درگاه.
        """
        gateway = self.get_gateway(gateway_name)

        try:
            response = await gateway.initiate_payment(
                amount=payment.amount,
                callback_url=callback_url,
                description=payment.description,
                metadata={
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "user_id": payment.user_id,
                },
            )
            logger.info(f"Payment initiated: {response.transaction_id}")
            return response

        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in payment initiation: {e}")
            raise PaymentGatewayError(
                message=f"خطای غیرمنتظره در شروع پرداخت: {str(e)}",
                context={"payment_id": payment.id},
            )

    async def verify_payment(
        self,
        transaction_id: str,
        amount: Money,
        callback_data: Dict[str, Any],
        gateway_name: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        تأیید پرداخت انجام‌شده.

        Args:
            transaction_id: شناسه تراکنش در درگاه.
            amount: مبلغ پرداختی.
            callback_data: داده‌های بازگشتی از درگاه.
            gateway_name: نام درگاه (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت تأیید.

        Raises:
            PaymentVerificationError: در صورت عدم تأیید پرداخت.
        """
        gateway = self.get_gateway(gateway_name)

        try:
            response = await gateway.verify_payment(
                transaction_id=transaction_id,
                amount=amount,
                callback_data=callback_data,
            )
            logger.info(f"Payment verified: {transaction_id}")
            return response

        except PaymentVerificationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {e}")
            raise PaymentVerificationError(
                message=f"خطای غیرمنتظره در تأیید پرداخت: {str(e)}",
                context={"transaction_id": transaction_id},
            )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Money] = None,
        reason: Optional[str] = None,
        gateway_name: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        بازگشت وجه پرداخت.

        Args:
            transaction_id: شناسه تراکنش در درگاه.
            amount: مبلغ برای بازگشت (اختیاری).
            reason: دلیل بازگشت وجه (اختیاری).
            gateway_name: نام درگاه (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت بازگشت وجه.

        Raises:
            PaymentRefundError: در صورت خطا در بازگشت وجه.
        """
        gateway = self.get_gateway(gateway_name)

        try:
            response = await gateway.refund_payment(
                transaction_id=transaction_id,
                amount=amount,
                reason=reason,
            )
            logger.info(f"Payment refunded: {transaction_id}")
            return response

        except PaymentRefundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in payment refund: {e}")
            raise PaymentRefundError(
                message=f"خطای غیرمنتظره در بازگشت وجه: {str(e)}",
                context={"transaction_id": transaction_id},
            )

    async def get_payment_status(
        self,
        transaction_id: str,
        gateway_name: Optional[str] = None,
    ) -> PaymentStatus:
        """
        دریافت وضعیت پرداخت.

        Args:
            transaction_id: شناسه تراکنش.
            gateway_name: نام درگاه (اختیاری).

        Returns:
            PaymentStatus: وضعیت پرداخت.
        """
        gateway = self.get_gateway(gateway_name)

        try:
            return await gateway.get_payment_status(transaction_id)
        except Exception as e:
            logger.error(f"Error getting payment status for {transaction_id}: {e}")
            return PaymentStatus.FAILED