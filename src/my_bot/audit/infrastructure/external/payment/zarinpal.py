# my_bot_project/src/my_bot/infrastructure/external/payment/zarinpal.py
"""
درگاه پرداخت زرین‌پال (Zarinpal Gateway).

این کلاس پیاده‌سازی درگاه پرداخت زرین‌پال است که با استفاده از API زرین‌پال،
عملیات شروع پرداخت، تأیید پرداخت و بازگشت وجه را انجام می‌دهد.
"""

import json
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime

import aiohttp
from aiohttp import ClientTimeout

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


class ZarinpalGateway:
    """
    درگاه پرداخت زرین‌پال.

    این کلاس مسئولیت ارتباط با API زرین‌پال برای انجام عملیات پرداخت را بر عهده دارد.

    Attributes:
        merchant_id: شناسه پذیرنده در زرین‌پال.
        sandbox: حالت Sandbox برای تست.
        timeout: زمان timeout برای درخواست‌ها.
        api_url: آدرس API زرین‌پال.
        callback_url: آدرس بازگشت پس از پرداخت.
    """

    def __init__(
        self,
        merchant_id: str,
        sandbox: bool = False,
        timeout: int = 30,
        callback_url: Optional[str] = None,
    ) -> None:
        """
        مقداردهی اولیه درگاه زرین‌پال.

        Args:
            merchant_id: شناسه پذیرنده در زرین‌پال.
            sandbox: حالت Sandbox برای تست (پیش‌فرض False).
            timeout: زمان timeout برای درخواست‌ها (پیش‌فرض ۳۰ ثانیه).
            callback_url: آدرس بازگشت پس از پرداخت (اختیاری).
        """
        self.merchant_id = merchant_id
        self.sandbox = sandbox
        self.timeout = ClientTimeout(total=timeout)
        self.callback_url = callback_url

        # انتخاب آدرس API بر اساس حالت
        if sandbox:
            self.api_url = "https://sandbox.zarinpal.com/pg/v4/payment"
        else:
            self.api_url = "https://api.zarinpal.com/pg/v4/payment"

        # آدرس بازگشت
        self.redirect_url = f"{self.api_url}/{merchant_id}/"

        logger.info(
            f"ZarinpalGateway initialized: merchant_id={merchant_id[:4]}***, "
            f"sandbox={sandbox}, api_url={self.api_url}"
        )

    async def initiate_payment(
        self,
        amount: Money,
        callback_url: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        شروع فرآیند پرداخت در زرین‌پال.

        Args:
            amount: مبلغ پرداختی.
            callback_url: آدرس بازگشت پس از پرداخت.
            description: توضیحات پرداخت (اختیاری).
            metadata: داده‌های اضافی (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل لینک پرداخت و شناسه تراکنش.

        Raises:
            PaymentGatewayError: در صورت بروز خطا در زرین‌پال.
        """
        try:
            # تبدیل مبلغ به ریال (زرین‌پال ریال دریافت می‌کند)
            amount_rial = int(amount.amount)

            # آماده‌سازی داده‌های درخواست
            payment_data = {
                "merchant_id": self.merchant_id,
                "amount": amount_rial,
                "callback_url": callback_url or self.callback_url,
                "description": description or "پرداخت از طریق ربات تلگرام",
                "metadata": {
                    "mobile": metadata.get("mobile") if metadata else None,
                    "email": metadata.get("email") if metadata else None,
                    **(metadata or {}),
                },
            }

            # حذف None values
            payment_data = {k: v for k, v in payment_data.items() if v is not None}

            logger.info(
                f"Initiating Zarinpal payment: amount={amount_rial}, "
                f"callback={callback_url}"
            )

            # ارسال درخواست به زرین‌پال
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                response = await session.post(
                    f"{self.api_url}/request.json",
                    json=payment_data,
                    headers={"Content-Type": "application/json"},
                )

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Zarinpal API error: {response.status} - {error_text}")
                    raise PaymentGatewayError(
                        message=f"خطا در ارتباط با زرین‌پال: {response.status}",
                        context={"status_code": response.status, "response": error_text},
                    )

                result = await response.json()
                logger.debug(f"Zarinpal payment initiation response: {result}")

                # پردازش پاسخ
                if result.get("data", {}).get("code") == 100:
                    authority = result["data"]["authority"]

                    # لینک پرداخت
                    if self.sandbox:
                        payment_url = f"https://sandbox.zarinpal.com/pg/StartPay/{authority}"
                    else:
                        payment_url = f"https://www.zarinpal.com/pg/StartPay/{authority}"

                    return PaymentGatewayResponseDTO(
                        success=True,
                        transaction_id=authority,
                        payment_url=payment_url,
                        message="درخواست پرداخت با موفقیت ایجاد شد.",
                        gateway_data={
                            "authority": authority,
                            "merchant_id": self.merchant_id,
                            "amount": amount_rial,
                        },
                    )
                else:
                    error_code = result.get("data", {}).get("code")
                    error_message = result.get("data", {}).get("message", "خطای ناشناخته")
                    logger.error(f"Zarinpal payment initiation failed: code={error_code}, message={error_message}")
                    raise PaymentGatewayError(
                        message=f"خطا در شروع پرداخت زرین‌پال: {error_message}",
                        context={"code": error_code, "response": result},
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to Zarinpal: {e}")
            raise PaymentGatewayError(
                message="خطا در ارتباط با درگاه زرین‌پال. لطفاً دوباره تلاش کنید.",
                context={"error": str(e)},
            )
        except PaymentGatewayError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Zarinpal payment initiation: {e}")
            raise PaymentGatewayError(
                message=f"خطای غیرمنتظره در شروع پرداخت: {str(e)}",
                context={"error": str(e)},
            )

    async def verify_payment(
        self,
        transaction_id: str,
        amount: Money,
        callback_data: Dict[str, Any],
    ) -> PaymentGatewayResponseDTO:
        """
        تأیید پرداخت انجام‌شده در زرین‌پال.

        Args:
            transaction_id: شناسه تراکنش (Authority).
            amount: مبلغ پرداختی.
            callback_data: داده‌های بازگشتی از زرین‌پال.

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت تأیید.

        Raises:
            PaymentVerificationError: در صورت عدم تأیید پرداخت.
            PaymentGatewayError: در صورت بروز خطا در زرین‌پال.
        """
        try:
            # تبدیل مبلغ به ریال
            amount_rial = int(amount.amount)

            # دریافت وضعیت از callback_data
            status = callback_data.get("Status")
            authority = callback_data.get("Authority")

            if not authority:
                raise PaymentVerificationError(
                    message="شناسه Authority در داده‌های بازگشتی یافت نشد.",
                    context={"callback_data": callback_data},
                )

            # اگر وضعیت ناموفق است
            if status != "OK":
                logger.warning(f"Zarinpal payment verification failed: status={status}")
                raise PaymentVerificationError(
                    message=f"پرداخت ناموفق بود. کد وضعیت: {status}",
                    context={"status": status, "authority": authority},
                )

            # آماده‌سازی داده‌های تأیید
            verify_data = {
                "merchant_id": self.merchant_id,
                "authority": authority,
                "amount": amount_rial,
            }

            logger.info(f"Verifying Zarinpal payment: authority={authority}, amount={amount_rial}")

            # ارسال درخواست تأیید به زرین‌پال
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                response = await session.post(
                    f"{self.api_url}/verify.json",
                    json=verify_data,
                    headers={"Content-Type": "application/json"},
                )

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Zarinpal verify API error: {response.status} - {error_text}")
                    raise PaymentGatewayError(
                        message=f"خطا در تأیید پرداخت زرین‌پال: {response.status}",
                        context={"status_code": response.status, "response": error_text},
                    )

                result = await response.json()
                logger.debug(f"Zarinpal payment verification response: {result}")

                # پردازش پاسخ
                data = result.get("data", {})
                code = data.get("code")

                if code == 100:
                    # پرداخت موفق
                    ref_id = data.get("ref_id")
                    logger.info(f"Zarinpal payment verified: ref_id={ref_id}")

                    return PaymentGatewayResponseDTO(
                        success=True,
                        transaction_id=authority,
                        tracking_code=ref_id,
                        reference_id=ref_id,
                        message="پرداخت با موفقیت تأیید شد.",
                        gateway_data={
                            "ref_id": ref_id,
                            "card_pan": data.get("card_pan"),
                            "card_hash": data.get("card_hash"),
                            "fee": data.get("fee"),
                            "fee_type": data.get("fee_type"),
                        },
                    )
                else:
                    error_message = data.get("message", "خطای ناشناخته")
                    logger.error(f"Zarinpal payment verification failed: code={code}, message={error_message}")

                    if code == 101:
                        # پرداخت قبلاً تأیید شده است
                        logger.warning(f"Payment already verified: authority={authority}")
                        return PaymentGatewayResponseDTO(
                            success=True,
                            transaction_id=authority,
                            tracking_code=data.get("ref_id"),
                            message="پرداخت قبلاً تأیید شده است.",
                            gateway_data={"already_verified": True},
                        )
                    else:
                        raise PaymentVerificationError(
                            message=f"تأیید پرداخت در زرین‌پال ناموفق بود: {error_message}",
                            context={"code": code, "authority": authority},
                        )

        except PaymentVerificationError:
            raise
        except PaymentGatewayError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Network error connecting to Zarinpal for verification: {e}")
            raise PaymentGatewayError(
                message="خطا در ارتباط با درگاه زرین‌پال برای تأیید پرداخت.",
                context={"error": str(e)},
            )
        except Exception as e:
            logger.error(f"Unexpected error in Zarinpal payment verification: {e}")
            raise PaymentVerificationError(
                message=f"خطای غیرمنتظره در تأیید پرداخت: {str(e)}",
                context={"error": str(e)},
            )

    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Money] = None,
        reason: Optional[str] = None,
    ) -> PaymentGatewayResponseDTO:
        """
        بازگشت وجه پرداخت در زرین‌پال.

        توجه: زرین‌پال از طریق API بازگشت وجه را پشتیبانی نمی‌کند و باید
        به‌صورت دستی در پنل زرین‌پال انجام شود. این متد برای سازگاری
        با اینترفیس درگاه‌ها پیاده‌سازی شده است.

        Args:
            transaction_id: شناسه تراکنش (Authority).
            amount: مبلغ برای بازگشت (اختیاری).
            reason: دلیل بازگشت وجه (اختیاری).

        Returns:
            PaymentGatewayResponseDTO: پاسخ درگاه شامل وضعیت بازگشت وجه.

        Raises:
            PaymentRefundError: در صورت خطا در بازگشت وجه.
        """
        logger.warning(
            f"Zarinpal refund requested but not supported via API: "
            f"transaction_id={transaction_id}, amount={amount}, reason={reason}"
        )

        # زرین‌پال بازگشت وجه از طریق API را پشتیبانی نمی‌کند
        raise PaymentRefundError(
            message="بازگشت وجه از طریق API زرین‌پال پشتیبانی نمی‌شود. لطفاً به‌صورت دستی در پنل زرین‌پال اقدام کنید.",
            context={
                "transaction_id": transaction_id,
                "amount": amount.amount if amount else None,
                "reason": reason,
            },
        )

    async def get_payment_status(
        self,
        transaction_id: str,
    ) -> PaymentStatus:
        """
        دریافت وضعیت پرداخت از زرین‌پال.

        Args:
            transaction_id: شناسه تراکنش (Authority).

        Returns:
            PaymentStatus: وضعیت پرداخت.

        Raises:
            PaymentGatewayError: در صورت بروز خطا در زرین‌پال.
        """
        try:
            # زرین‌پال API مستقیمی برای دریافت وضعیت ندارد
            # بنابراین فقط می‌توانیم بررسی کنیم که آیا تراکنش قبلاً تأیید شده است
            logger.warning(
                f"Zarinpal get_payment_status not fully supported: transaction_id={transaction_id}"
            )
            return PaymentStatus.PENDING

        except Exception as e:
            logger.error(f"Error getting Zarinpal payment status: {e}")
            return PaymentStatus.FAILED

    def verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str,
    ) -> bool:
        """
        اعتبارسنجی امضای وب‌هوک زرین‌پال.

        Args:
            payload: داده‌های وب‌هوک.
            signature: امضای دریافتی.
            secret: کلید مخفی.

        Returns:
            bool: True اگر امضا معتبر باشد.
        """
        try:
            # تبدیل payload به JSON
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            expected = hmac.new(
                secret.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected, signature)

        except Exception as e:
            logger.error(f"Error verifying Zarinpal webhook signature: {e}")
            return False

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش وب‌هوک دریافتی از زرین‌پال.

        Args:
            webhook_data: داده‌های وب‌هوک.

        Returns:
            Dict[str, Any]: نتیجه پردازش وب‌هوک.
        """
        # استخراج اطلاعات از وب‌هوک
        authority = webhook_data.get("Authority")
        status = webhook_data.get("Status")
        ref_id = webhook_data.get("RefID")

        result = {
            "success": False,
            "transaction_id": authority,
            "reference_id": ref_id,
            "tracking_code": ref_id,
            "event_type": "payment_verification",
            "message": "",
        }

        if status == "OK" and ref_id:
            result["success"] = True
            result["message"] = "Payment verified successfully"
        else:
            result["message"] = f"Payment failed or pending: status={status}"

        return result