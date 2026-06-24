# src/tests/unit/application/test_payment_service.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from decimal import Decimal

from my_bot.core.exceptions import NotFoundError, ValidationError, DatabaseError, PaymentError
from my_bot.domain.entities.payment import Payment
from my_bot.application.services.payment.payment_gateway import PaymentGatewayService
from my_bot.application.services.payment.payment_verification import PaymentVerificationService


class TestPaymentGatewayService:
    """Unit tests for PaymentGatewayService."""

    @pytest.fixture
    def mock_payment_repo(self):
        """Create a mock payment repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_order_repo(self):
        """Create a mock order repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock external payment gateway."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_payment_repo, mock_order_repo, mock_gateway):
        """Create PaymentGatewayService instance with mocks."""
        return PaymentGatewayService(
            payment_repo=mock_payment_repo,
            order_repo=mock_order_repo,
            gateway=mock_gateway,
        )

    @pytest.mark.asyncio
    async def test_initiate_payment_success(self, service, mock_payment_repo, mock_order_repo, mock_gateway):
        """Test initiating a payment successfully."""
        # Setup
        mock_order_repo.find_by_id.return_value = Mock(
            id=1,
            user_id=1,
            total_amount=100000,
            status="pending",
        )
        mock_gateway.create_payment.return_value = {
            "transaction_id": "txn_123456",
            "payment_url": "https://payment.example.com/pay/123456",
            "status": "pending",
        }
        mock_payment_repo.save.return_value = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            payment_url="https://payment.example.com/pay/123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Execute
        result = await service.initiate_payment(
            order_id=1,
            user_id=1,
            amount=100000,
        )

        # Assert
        assert result["order_id"] == 1
        assert result["amount"] == 100000
        assert result["status"] == "pending"
        assert result["transaction_id"] == "txn_123456"
        assert result["payment_url"] == "https://payment.example.com/pay/123456"
        mock_order_repo.find_by_id.assert_called_once_with(1)
        mock_gateway.create_payment.assert_called_once_with(
            amount=100000,
            order_id=1,
            user_id=1,
        )
        mock_payment_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_payment_order_not_found(self, service, mock_order_repo):
        """Test initiating payment for non-existent order."""
        mock_order_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.initiate_payment(order_id=1, user_id=1, amount=100000)
        assert "Order 1 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initiate_payment_invalid_amount(self, service, mock_order_repo):
        """Test initiating payment with invalid amount."""
        mock_order_repo.find_by_id.return_value = Mock(id=1, user_id=1, total_amount=100000)

        with pytest.raises(ValidationError) as exc_info:
            await service.initiate_payment(order_id=1, user_id=1, amount=0)
        assert "Amount must be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initiate_payment_amount_mismatch(self, service, mock_order_repo):
        """Test initiating payment with amount mismatch."""
        mock_order_repo.find_by_id.return_value = Mock(id=1, user_id=1, total_amount=100000)

        with pytest.raises(ValidationError) as exc_info:
            await service.initiate_payment(order_id=1, user_id=1, amount=50000)
        assert "Amount does not match order total" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initiate_payment_gateway_error(self, service, mock_order_repo, mock_gateway):
        """Test gateway error when initiating payment."""
        mock_order_repo.find_by_id.return_value = Mock(id=1, user_id=1, total_amount=100000)
        mock_gateway.create_payment.side_effect = Exception("Gateway connection error")

        with pytest.raises(PaymentError) as exc_info:
            await service.initiate_payment(order_id=1, user_id=1, amount=100000)
        assert "Failed to initiate payment" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_payment_success(self, service, mock_payment_repo, mock_gateway):
        """Test verifying a payment successfully."""
        # Setup
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment
        mock_gateway.get_payment_status.return_value = {
            "status": "completed",
            "reference_id": "ref_123456",
        }
        mock_payment_repo.save.return_value = payment

        # Execute
        result = await service.verify_payment(transaction_id="txn_123456")

        # Assert
        assert result["status"] == "completed"
        mock_payment_repo.find_by_transaction_id.assert_called_once_with("txn_123456")
        mock_gateway.get_payment_status.assert_called_once_with("txn_123456")
        mock_payment_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_payment_not_found(self, service, mock_payment_repo):
        """Test verifying a payment that does not exist."""
        mock_payment_repo.find_by_transaction_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.verify_payment(transaction_id="txn_invalid")
        assert "Payment with transaction_id 'txn_invalid' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_payment_already_completed(self, service, mock_payment_repo):
        """Test verifying a payment that is already completed."""
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="completed",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment

        result = await service.verify_payment(transaction_id="txn_123456")
        assert result["status"] == "completed"
        mock_gateway.get_payment_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_refund_payment_success(self, service, mock_payment_repo, mock_gateway):
        """Test refunding a payment successfully."""
        # Setup
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="completed",
            transaction_id="txn_123456",
            reference_id="ref_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_id.return_value = payment
        mock_gateway.refund_payment.return_value = {"status": "refunded", "refund_id": "refund_789"}
        mock_payment_repo.save.return_value = payment

        # Execute
        result = await service.refund_payment(payment_id=1)

        # Assert
        assert result["status"] == "refunded"
        mock_payment_repo.find_by_id.assert_called_once_with(1)
        mock_gateway.refund_payment.assert_called_once_with(transaction_id="txn_123456")
        mock_payment_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_refund_payment_not_found(self, service, mock_payment_repo):
        """Test refunding a payment that does not exist."""
        mock_payment_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.refund_payment(payment_id=1)
        assert "Payment 1 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_refund_payment_not_completed(self, service, mock_payment_repo):
        """Test refunding a payment that is not completed."""
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_id.return_value = payment

        with pytest.raises(PaymentError) as exc_info:
            await service.refund_payment(payment_id=1)
        assert "Only completed payments can be refunded" in str(exc_info.value)


class TestPaymentVerificationService:
    """Unit tests for PaymentVerificationService."""

    @pytest.fixture
    def mock_payment_repo(self):
        """Create a mock payment repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_order_repo(self):
        """Create a mock order repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock external payment gateway."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_payment_repo, mock_order_repo, mock_gateway):
        """Create PaymentVerificationService instance with mocks."""
        return PaymentVerificationService(
            payment_repo=mock_payment_repo,
            order_repo=mock_order_repo,
            gateway=mock_gateway,
        )

    @pytest.mark.asyncio
    async def test_verify_callback_success(self, service, mock_payment_repo, mock_order_repo, mock_gateway):
        """Test verifying a payment via callback/webhook successfully."""
        # Setup
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment
        mock_gateway.verify_callback.return_value = {"status": "success"}
        mock_order_repo.update_status.return_value = Mock(id=1, status="paid")
        mock_payment_repo.save.return_value = payment

        # Execute
        result = await service.verify_callback(
            transaction_id="txn_123456",
            callback_data={"status": "success", "reference": "ref_123"},
        )

        # Assert
        assert result["status"] == "paid"
        mock_payment_repo.find_by_transaction_id.assert_called_once_with("txn_123456")
        mock_gateway.verify_callback.assert_called_once()
        mock_order_repo.update_status.assert_called_once_with(1, "paid")
        mock_payment_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_callback_invalid_signature(self, service, mock_payment_repo, mock_gateway):
        """Test callback verification with invalid signature."""
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment
        mock_gateway.verify_callback.side_effect = Exception("Invalid signature")

        with pytest.raises(PaymentError) as exc_info:
            await service.verify_callback(
                transaction_id="txn_123456",
                callback_data={"status": "success"},
            )
        assert "Invalid callback signature" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_callback_payment_not_found(self, service, mock_payment_repo):
        """Test callback verification for non-existent payment."""
        mock_payment_repo.find_by_transaction_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.verify_callback(
                transaction_id="txn_invalid",
                callback_data={"status": "success"},
            )
        assert "Payment not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_callback_payment_already_verified(self, service, mock_payment_repo):
        """Test callback verification for already verified payment."""
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="completed",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment

        result = await service.verify_callback(
            transaction_id="txn_123456",
            callback_data={"status": "success"},
        )
        assert result["status"] == "completed"
        mock_gateway.verify_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_payment_status_success(self, service, mock_payment_repo, mock_gateway):
        """Test checking payment status successfully."""
        # Setup
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment
        mock_gateway.get_payment_status.return_value = {"status": "completed"}
        mock_payment_repo.save.return_value = payment

        # Execute
        result = await service.check_payment_status(transaction_id="txn_123456")

        # Assert
        assert result["status"] == "completed"
        mock_gateway.get_payment_status.assert_called_once_with("txn_123456")
        mock_payment_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_payment_status_payment_not_found(self, service, mock_payment_repo):
        """Test checking payment status for non-existent payment."""
        mock_payment_repo.find_by_transaction_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.check_payment_status(transaction_id="txn_invalid")
        assert "Payment not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_payment_status_gateway_error(self, service, mock_payment_repo, mock_gateway):
        """Test gateway error when checking payment status."""
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment
        mock_gateway.get_payment_status.side_effect = Exception("Gateway error")

        with pytest.raises(PaymentError) as exc_info:
            await service.check_payment_status(transaction_id="txn_123456")
        assert "Failed to check payment status" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_payment_status_no_change(self, service, mock_payment_repo, mock_gateway):
        """Test checking payment status when status hasn't changed."""
        payment = Payment(
            id=1,
            order_id=1,
            user_id=1,
            amount=100000,
            status="pending",
            transaction_id="txn_123456",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_payment_repo.find_by_transaction_id.return_value = payment
        mock_gateway.get_payment_status.return_value = {"status": "pending"}
        mock_payment_repo.save.return_value = payment

        result = await service.check_payment_status(transaction_id="txn_123456")
        assert result["status"] == "pending"
        mock_gateway.get_payment_status.assert_called_once_with("txn_123456")
        # Should not save if status unchanged
        mock_payment_repo.save.assert_not_called()