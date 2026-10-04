import time
import random
from app.extensions import db
from app.models.payment import Payment
from datetime import datetime

class CircuitBreakerOpenException(Exception):
    pass

class ExternalPaymentProviderException(Exception):
    pass

class PaymentCircuitBreaker:
    _failures = 0
    _last_failure_time = None
    _threshold = 3
    _reset_timeout = 30 # seconds

    @classmethod
    def call(cls, func, *args, **kwargs):
        now = time.time()
        
        # Check state
        if cls._failures >= cls._threshold:
            if now - cls._last_failure_time > cls._reset_timeout:
                # Half-Open: allow one try
                pass
            else:
                raise CircuitBreakerOpenException("Payment provider is currently unavailable (Circuit Breaker OPEN).")

        try:
            result = func(*args, **kwargs)
            # Success, reset if we were in Half-Open or just clear failures
            cls._failures = 0
            cls._last_failure_time = None
            return result
        except ExternalPaymentProviderException as e:
            cls._failures += 1
            cls._last_failure_time = time.time()
            raise e

class PaymentService:
    @staticmethod
    def initiate_payment(order, organization_id, amount, provider="MOCK_PROVIDER", idempotency_key=None):
        # 1. Idempotency Check
        if idempotency_key:
            existing = Payment.query.filter_by(idempotency_key=idempotency_key).first()
            if existing:
                return existing

        payment = Payment(
            order_id=order.id,
            organization_id=organization_id,
            amount=amount,
            status='INITIATED',
            provider=provider,
            idempotency_key=idempotency_key
        )
        db.session.add(payment)
        db.session.flush()
        
        return payment

    @staticmethod
    def process_payment(payment_id):
        payment = Payment.query.with_for_update().get(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment.status in ['CAPTURED', 'AUTHORIZED']:
            return payment # Already processed
            
        payment.status = 'PENDING'
        db.session.flush() # Save pending state before calling external provider
        
        # Call external provider through Circuit Breaker
        try:
            result = PaymentCircuitBreaker.call(PaymentService._mock_external_payment_call, payment)
            payment.status = result['status']
            payment.provider_transaction_id = result['transaction_id']
            payment.updated_at = datetime.utcnow()
            db.session.flush()
            return payment
        except CircuitBreakerOpenException as cbe:
            # Safe Fallback: Payment remains PENDING/UNKNOWN for reconciliation later
            payment.status = 'UNKNOWN'
            payment.error_message = str(cbe)
            db.session.flush()
            return payment
        except ExternalPaymentProviderException as epe:
            payment.status = 'FAILED'
            payment.error_message = str(epe)
            db.session.flush()
            return payment

    @staticmethod
    def _mock_external_payment_call(payment):
        # Simulate network latency
        time.sleep(0.5)
        
        # Simulate Chaos / Failure (10% chance of failure)
        if random.random() < 0.1:
            raise ExternalPaymentProviderException("Provider timed out or returned 500.")
            
        return {
            "status": "CAPTURED",
            "transaction_id": f"txn_{int(time.time())}_{payment.id}"
        }
