import time
from app import create_app
from app.extensions import db
from app.models.order import Order
from app.models.payment import Payment
from app.services.payment_service import PaymentService, PaymentCircuitBreaker, ExternalPaymentProviderException, CircuitBreakerOpenException

def run_reconciliation(app):
    """
    Background worker that reconciles inconsistent states.
    In Phase 22, we focus on Payment-Order reconciliation.
    """
    with app.app_context():
        app.logger.info("Reconciliation worker started.")
        while True:
            try:
                # 1. Payment Reconciliation: Find UNKNOWN or PENDING payments older than 1 minute
                # For SQLite, we just query PENDING/UNKNOWN and filter in Python or use a basic date filter
                # Here we just fetch them all and do a simple check.
                payments = Payment.query.filter(Payment.status.in_(['UNKNOWN', 'PENDING'])).all()
                for payment in payments:
                    # In a real system, we'd query the external provider for the true status
                    app.logger.info(f"Reconciling Payment {payment.id} for Order {payment.order_id}")
                    
                    try:
                        # Call external provider through Circuit Breaker to get status
                        result = PaymentCircuitBreaker.call(PaymentService._mock_external_payment_call, payment)
                        payment.status = result['status']
                        payment.provider_transaction_id = result['transaction_id']
                        
                        order = Order.query.get(payment.order_id)
                        if payment.status in ['CAPTURED', 'AUTHORIZED']:
                            order.status = 'CONFIRMED'
                            for f in order.fulfillments:
                                f.status = 'CONFIRMED'
                        else:
                            order.status = 'PAYMENT_FAILED'
                            # Should also restock inventory here if failed!
                            from app.services.inventory_service import InventoryService
                            for item in order.items:
                                InventoryService.restock(item.product_id, item.quantity, order.customer_id, reason="Payment Failed Reconciliation")

                        db.session.commit()
                        app.logger.info(f"Payment {payment.id} reconciled to {payment.status}")
                        
                        # Emit order status change via EventService
                        from app.services.event_service import EventService
                        EventService.publish_order_status_changed(order, order.status)
                        
                    except CircuitBreakerOpenException:
                        app.logger.warning("Circuit breaker open, skipping reconciliation")
                    except ExternalPaymentProviderException:
                        # Payment provider confirms failure
                        payment.status = 'FAILED'
                        order = Order.query.get(payment.order_id)
                        order.status = 'PAYMENT_FAILED'
                        
                        # Restock
                        from app.services.inventory_service import InventoryService
                        for item in order.items:
                            InventoryService.restock(item.product_id, item.quantity, order.customer_id, reason="Payment Failed Reconciliation")
                            
                        db.session.commit()
                        
                        from app.services.event_service import EventService
                        EventService.publish_order_status_changed(order, order.status)

                time.sleep(10) # Run every 10 seconds for demo
            except Exception as e:
                app.logger.error(f"Reconciliation encountered an error: {e}")
                db.session.rollback()
                time.sleep(5)

if __name__ == '__main__':
    app = create_app()
    run_reconciliation(app)
