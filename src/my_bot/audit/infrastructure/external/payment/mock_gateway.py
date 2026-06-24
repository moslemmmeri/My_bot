# my_bot_project/src/my_bot/infrastructure/external/payment/mock_gateway.py
"""
درگاه پرداخت شبیه‌سازی‌شده (Mock Payment Gateway).

این کلاس یک درگاه پرداخت شبیه‌سازی‌شده برای تست و توسعه است که
بدون اتصال به سرویس خارجی، عملیات پرداخت را شبیه‌سازی می‌کند.
برای تست‌های محلی و توسعه بسیار مفید است.
"""

import uuid
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from my_bot.application.dtos.payment_dto import PaymentGatewayResponseDTO
from my_bot.core.constants.payment_statuses import PaymentStatus
from my_bot.core.exceptions.payment_errors import (
    PaymentGatewayError,
    PaymentVerificationError,
    PaymentRefundError,
)
from my_bot.core.logger.logger_setup import get_logger
from my_bot.domain.value_objects.money import Money

logger = get_logger(__name__)


class MockPaymentGateway:
    """
    درگاه پرداخت شبیه‌سازی‌شده.

    این کلاس برای تست و توسعه استفاده می‌شود و پرداخت‌ها را به‌صورت
    شبیه‌سازی‌شده پردازش می‌کند. می‌توان آن را به‌گون‌های تنظیم کرد که
    پرداخت‌ها به‌صورت خودکار تأیید شوند یا با خطا مواجه شوند.

    Attributes:
        auto_approve: آیا پرداخت‌ها به‌صورت خودکار تأیید شوند.
        fail_rate: نرخ خطا (۰ تا ۱) برای شبیه‌سازی خطاهای تصادفی.
        _transactions: دیکشنری نگاشت شناسه تراکنش به اطلاعات آن.
        _refundable_time: مدت زمان قابل بازگشت وجه (ثانیه).
    """

    def __init__(
        self,
        auto_approve: bool = True,
        fail_rate: float = 0.0,
        refundable_time: int = 3600,  # 1 ساعت
    ) -> None:
        """
        مقداردهی اولیه درگاه شبیه‌سازی‌شده.

        Args:
            auto_approve: آیا پرداخت‌ها به‌صورت خودکار تأیید شوند.
            fail_rate: نرخ خطا (۰ تا ۱) برای شبیه‌سازی خطاهای تصادفی.
            refundable_time: مدت زمان قابل بازگشت وجه بر حسب ثانیه.
        """
        self._auto_approve = auto_approve
        self._fail_rate = max(0.0, min(1.0, fail_rate))
        self._refundable_time = refundable_time
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._counter = 0

        logger.info(
            f"MockPaymentGateway initialized: auto_approve={auto_approve}, "
            f"fail_rate={fail_rate}, refundable_time={refundable_time}s"
        )

    async def initiate_payment(
        self,
        amount: Money,
        callback_url: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        شروع فرآیند پرداخت در درگاه شبیه‌سازی‌شده.

        Args:
            amount: مبلغ پرداختی.
            callback_url: آدرس بازگشت پس از پرداخت.
            description: توضیحات پرداخت (اختیاری).
            metadata: داده‌های اضافی (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل لینک پرداخت و شناسه تراکنش.

        Raises:
            PaymentGatewayError: در صورت بروز خطا (با توجه به fail_rate).
        """
        # شبیه‌سازی خطای تصادفی
        import random
        if random.random() < self._fail_rate:
            logger.warning("Mock payment initiation failed (simulated error)")
            raise PaymentGatewayError(
                message="خطای شبیه‌سازی‌شده در درگاه پرداخت.",
                context={"fail_rate": self._fail_rate},
            )

        # تولید شناسه تراکنش
        self._counter += 1
        transaction_id = f"mock_{self._counter}_{uuid.uuid4().hex[:8]}"

        # ذخیره تراکنش
        self._transactions[transaction_id] = {
            "amount": float(amount.amount),
            "currency": amount.currency,
            "callback_url": callback_url,
            "description": description,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now(),
            "paid_at": None,
            "refunded_at": None,
            "refund_amount": None,
            "refund_reason": None,
        }

        # لینک پرداخت شبیه‌سازی‌شده
        payment_url = f"https://mock-gateway.example.com/pay/{transaction_id}"

        logger.info(
            f"Mock payment initiated: transaction_id={transaction_id}, "
            f"amount={amount.amount}, auto_approve={self._auto_approve}"
        )

        return PaymentGatewayResponseDTO(
            success=True,
            transaction_id=transaction_id,
            payment_url=payment_url,
            message="درخواست پرداخت با موفقیت ایجاد شد.",
            gateway_data={
                "mock": True,
                "auto_approve": self._auto_approve,
                "transaction_id": transaction_id,
            },
        )

    async def verify_payment(
        self,
        transaction_id: str,
        amount: Money,
        callback_data: Dict[str, Any],
    ) -> PaymentGatewayResponseDTO:
        """
        تأیید پرداخت در درگاه شبیه‌سازی‌شده.

        Args:
            transaction_id: شناسه تراکنش.
            amount: مبلغ پرداختی.
            callback_data: داده‌های بازگشتی (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت تأیید.

        Raises:
            PaymentVerificationError: در صورت عدم تأیید پرداخت.
            PaymentGatewayError: در صورت بروز خطا.
        """
        if transaction_id not in self._transactions:
            logger.warning(f"Transaction {transaction_id} not found")
            raise PaymentVerificationError(
                message=f"تراکنش با شناسه {transaction_id} یافت نشد.",
                context={"transaction_id": transaction_id},
            )

        transaction = self._transactions[transaction_id]
        now = datetime.now()

        # شبیه‌سازی خطای تصادفی
        import random
        if random.random() < self._fail_rate * 0.5:  # نرخ خطای کمتر برای تأیید
            logger.warning(f"Mock payment verification failed (simulated error): {transaction_id}")
            transaction["status"] = "failed"
            raise PaymentVerificationError(
                message="خطای شبیه‌سازی‌شده در تأیید پرداخت.",
                context={"transaction_id": transaction_id},
            )

        # بررسی وضعیت
        current_status = transaction.get("status")

        if current_status == "paid":
            logger.info(f"Payment already verified: {transaction_id}")
            return PaymentGatewayResponseDTO(
                success=True,
                transaction_id=transaction_id,
                tracking_code=transaction.get("ref_id"),
                message="پرداخت قبلاً تأیید شده است.",
                gateway_data={"already_verified": True},
            )

        if current_status == "refunded":
            logger.warning(f"Payment already refunded: {transaction_id}")
            raise PaymentVerificationError(
                message="پرداخت قبلاً بازگشت داده شده است.",
                context={"transaction_id": transaction_id},
            )

        # تأیید خودکار یا بر اساس callback_data
        status = callback_data.get("status", "success") if callback_data else "success"
        user_approved = status == "success"

        if self._auto_approve or user_approved:
            # پرداخت موفق
            ref_id = f"REF{transaction_id[-8:]}"
            transaction["status"] = "paid"
            transaction["paid_at"] = now
            transaction["ref_id"] = ref_id
            transaction["callback_data"] = callback_data

            logger.info(f"Mock payment verified: transaction_id={transaction_id}, ref_id={ref_id}")
            return PaymentGatewayResponseDTO(
                success=True,
                transaction_id=transaction_id,
                tracking_code=ref_id,
                reference_id=ref_id,
                message="پرداخت با موفقیت تأیید شد.",
                gateway_data={
                    "verified": True,
                    "auto_approved": self._auto_approve,
                    "ref_id": ref_id,
                },
            )
        else:
            # پرداخت ناموفق
            transaction["status"] = "failed"
            logger.warning(f"Mock payment verification failed: {transaction_id}")
            raise PaymentVerificationError(
                message="پرداخت توسط کاربر لغو شد.",
                context={"transaction_id": transaction_id},
            )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Money] = None,
        reason: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        بازگشت وجه پرداخت در درگاه شبیه‌سازی‌شده.

        Args:
            transaction_id: شناسه تراکنش.
            amount: مبلغ برای بازگشت (در صورت عدم مشخص بودن، کل مبلغ بازگشت می‌خورد).
            reason: دلیل بازگشت وجه (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت بازگشت وجه.

        Raises:
            PaymentRefundError: در صورت خطا در بازگشت وجه.
            PaymentGatewayError: در صورت بروز خطا.
        """
        if transaction_id not in self._transactions:
            logger.warning(f"Transaction {transaction_id} not found for refund")
            raise PaymentRefundError(
                message=f"تراکنش با شناسه {transaction_id} یافت نشد.",
                context={"transaction_id": transaction_id},
            )

        transaction = self._transactions[transaction_id]
        now = datetime.now()

        # شبیه‌سازی خطای تصادفی
        import random
        if random.random() < self._fail_rate * 0.3:
            logger.warning(f"Mock payment refund failed (simulated error): {transaction_id}")
            raise PaymentRefundError(
                message="خطای شبیه‌سازی‌شده در بازگشت وجه.",
                context={"transaction_id": transaction_id},
            )

        # بررسی وضعیت تراکنش
        current_status = transaction.get("status")

        if current_status != "paid":
            logger.warning(f"Payment {transaction_id} is not paid. Status: {current_status}")
            raise PaymentRefundError(
                message="فقط پرداخت‌های موفق قابل بازگشت هستند.",
                context={"transaction_id": transaction_id, "status": current_status},
            )

        # بررسی زمان قابل بازگشت
        paid_at = transaction.get("paid_at")
        if paid_at:
            elapsed = (now - paid_at).total_seconds()
            if elapsed > self._refundable_time:
                logger.warning(f"Payment {transaction_id} is past refundable time: {elapsed}s")
                raise PaymentRefundError(
                    message="زمان بازگشت وجه برای این پرداخت به پایان رسیده است.",
                    context={
                        "transaction_id": transaction_id,
                        "elapsed_seconds": elapsed,
                        "max_refundable_seconds": self._refundable_time,
                    },
                )

        # محاسبه مبلغ بازگشت
        refund_amount = amount.amount if amount else transaction["amount"]
        if refund_amount > transaction["amount"]:
            logger.warning(f"Refund amount {refund_amount} exceeds transaction amount {transaction['amount']}")
            raise PaymentRefundError(
                message="مبلغ بازگشت نمی‌تواند بیشتر از مبلغ اصلی باشد.",
                context={
                    "transaction_id": transaction_id,
                    "refund_amount": refund_amount,
                    "original_amount": transaction["amount"],
                },
            )

        # انجام بازگشت وجه
        transaction["status"] = "refunded"
        transaction["refunded_at"] = now
        transaction["refund_amount"] = refund_amount
        transaction["refund_reason"] = reason

        logger.info(
            f"Mock payment refunded: transaction_id={transaction_id}, "
            f"amount={refund_amount}, reason={reason}"
        )

        return PaymentGatewayResponseDTO(
            success=True,
            transaction_id=transaction_id,
            message="بازگشت وجه با موفقیت انجام شد.",
            gateway_data={
                "refunded": True,
                "amount": refund_amount,
                "reason": reason,
                "refunded_at": now.isoformat(),
            },
        )

    async def get_payment_status(
        self,
        transaction_id: str,
    ) -> PaymentStatus:
        """
        دریافت وضعیت پرداخت از درگاه شبیه‌سازی‌شده.

        Args:
            transaction_id: شناسه تراکنش.

        Returns:
            PaymentStatus: وضعیت پرداخت.

        Raises:
            PaymentGatewayError: در صورت بروز خطا.
        """
        if transaction_id not in self._transactions:
            logger.warning(f"Transaction {transaction_id} not found for status check")
            return PaymentStatus.FAILED

        status_map = {
            "pending": PaymentStatus.PENDING,
            "paid": PaymentStatus.SUCCESS,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
            "cancelled": PaymentStatus.CANCELED,
        }

        current_status = self._transactions[transaction_id].get("status", "pending")
        return status_map.get(current_status, PaymentStatus.PENDING)

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش وب‌هوک دریافتی از درگاه شبیه‌سازی‌شده.

        Args:
            webhook_data: داده‌های وب‌هوک.

        Returns:
            Dict[str, Any]: نتیجه پردازش وب‌هوک.
        """
        transaction_id = webhook_data.get("transaction_id")
        status = webhook_data.get("status", "success")

        result = {
            "success": False,
            "transaction_id": transaction_id,
            "event_type": "payment_verification",
            "message": "",
        }

        if not transaction_id:
            result["message"] = "شناسه تراکنش در وب‌هوک یافت نشد."
            return result

        if transaction_id not in self._transactions:
            result["message"] = f"تراکنش {transaction_id} یافت نشد."
            return result

        transaction = self._transactions[transaction_id]

        if status == "success":
            # پردازش وب‌هوک موفق
            ref_id = f"WEBHOOK{transaction_id[-6:]}"
            transaction["status"] = "paid"
            transaction["paid_at"] = datetime.now()
            transaction["ref_id"] = ref_id
            transaction["webhook_data"] = webhook_data

            result["success"] = True
            result["reference_id"] = ref_id
            result["tracking_code"] = ref_id
            result["message"] = "Webhook processed successfully"
        else:
            result["message"] = f"Webhook status: {status}"

        return result

    def reset_transactions(self) -> None:
        """بازنشانی تمام تراکنش‌ها (برای تست)."""
        self._transactions.clear()
        self._counter = 0
        logger.info("MockPaymentGateway transactions reset.")

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک تراکنش (برای تست).

        Args:
            transaction_id: شناسه تراکنش.

        Returns:
            اطلاعات تراکنش یا None در صورت عدم وجود.
        """
        return self._transactions.get(transaction_id)

    def get_transactions_count(self) -> int:
        """
        دریافت تعداد تراکنش‌های ثبت‌شده (برای تست).

        Returns:
            تعداد تراکنش‌ها.
        """
        return len(self._transactions)