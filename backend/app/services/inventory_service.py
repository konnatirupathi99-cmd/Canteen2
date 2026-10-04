from app.extensions import db
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Product
from datetime import datetime

class InventoryService:
    
    @staticmethod
    def get_stock_status(quantity, threshold):
        if quantity <= 0:
            return 'OUT_OF_STOCK'
        if quantity <= threshold:
            return 'LOW_STOCK'
        return 'IN_STOCK'

    @staticmethod
    def validate_and_decrement(product_id, quantity, user_id, reference_id):
        """
        Atomically decrements stock and returns the created InventoryTransaction.
        Raises ValueError if stock is insufficient.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Atomic decrement
        updated = db.session.execute(
            db.text("""
                UPDATE inventory 
                SET quantity = quantity - :req, updated_at = :now
                WHERE product_id = :pid AND quantity >= :req
                RETURNING quantity, low_stock_threshold
            """),
            {"req": quantity, "pid": product_id, "now": datetime.utcnow()}
        ).fetchone()

        if not updated:
            raise ValueError("Insufficient stock")

        new_quantity = updated[0]
        threshold = updated[1]
        previous_quantity = new_quantity + quantity

        txn = InventoryTransaction(
            product_id=product_id,
            transaction_type='SALE',
            quantity_change=-quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference_id=reference_id,
            performed_by=user_id
        )
        db.session.add(txn)

        status_changed = InventoryService.get_stock_status(previous_quantity, threshold) != InventoryService.get_stock_status(new_quantity, threshold)
        
        # Trigger Alerts if needed
        from app.services.alert_service import AlertService
        if new_quantity == 0:
            AlertService.trigger_alert(
                alert_type='OUT_OF_STOCK',
                severity='CRITICAL',
                message=f"Product {product_id} is OUT OF STOCK.",
                product_id=product_id,
                deduplication_key=f"out_of_stock_{product_id}"
            )
        elif new_quantity <= threshold:
            AlertService.trigger_alert(
                alert_type='LOW_STOCK',
                severity='WARNING',
                message=f"Product {product_id} is LOW ON STOCK ({new_quantity} left).",
                product_id=product_id,
                deduplication_key=f"low_stock_{product_id}"
            )
        
        return txn, new_quantity, threshold, status_changed

    @staticmethod
    def restock(product_id, quantity, user_id, reason="RESTOCK"):
        """
        Adds to stock and creates a RESTOCK transaction.
        """
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")

        updated = db.session.execute(
            db.text("""
                UPDATE inventory
                SET quantity = quantity + :qty, updated_at = :now
                WHERE product_id = :pid
                RETURNING quantity, low_stock_threshold
            """),
            {"qty": quantity, "pid": product_id, "now": datetime.utcnow()}
        ).fetchone()

        if not updated:
            raise ValueError("Inventory not found")

        new_quantity = updated[0]
        threshold = updated[1]
        previous_quantity = new_quantity - quantity

        txn = InventoryTransaction(
            product_id=product_id,
            transaction_type='RESTOCK',
            quantity_change=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reason=reason,
            performed_by=user_id
        )
        db.session.add(txn)
        
        # Resolve alerts
        from app.services.alert_service import AlertService
        if new_quantity > 0:
            AlertService.resolve_alert_by_key(f"out_of_stock_{product_id}")
        if new_quantity > threshold:
            AlertService.resolve_alert_by_key(f"low_stock_{product_id}")
            
        return txn, new_quantity, threshold

    @staticmethod
    def adjust_stock(product_id, new_quantity, user_id, reason):
        """
        Sets exact stock amount (useful for manual corrections).
        """
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")

        inv = Inventory.query.filter_by(product_id=product_id).with_for_update().first()
        if not inv:
            raise ValueError("Inventory not found")

        previous_quantity = inv.quantity
        quantity_change = new_quantity - previous_quantity
        
        if quantity_change == 0:
            return None, new_quantity, inv.low_stock_threshold # No change

        inv.quantity = new_quantity
        inv.updated_at = datetime.utcnow()

        txn = InventoryTransaction(
            product_id=product_id,
            transaction_type='MANUAL_ADJUSTMENT',
            quantity_change=quantity_change,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reason=reason,
            performed_by=user_id
        )
        db.session.add(txn)
        
        # Resolve or trigger alerts
        from app.services.alert_service import AlertService
        if new_quantity == 0:
            AlertService.trigger_alert(alert_type='OUT_OF_STOCK', severity='CRITICAL', message=f"Product {product_id} is OUT OF STOCK.", product_id=product_id, deduplication_key=f"out_of_stock_{product_id}")
        elif new_quantity <= inv.low_stock_threshold:
            AlertService.trigger_alert(alert_type='LOW_STOCK', severity='WARNING', message=f"Product {product_id} is LOW ON STOCK ({new_quantity} left).", product_id=product_id, deduplication_key=f"low_stock_{product_id}")
        
        if new_quantity > 0:
            AlertService.resolve_alert_by_key(f"out_of_stock_{product_id}")
        if new_quantity > inv.low_stock_threshold:
            AlertService.resolve_alert_by_key(f"low_stock_{product_id}")
        
        return txn, new_quantity, inv.low_stock_threshold

