from app.models.transfer import StockTransfer
from app.models.inventory import Inventory
from app.services.inventory_service import InventoryService
from app.extensions import db
from datetime import datetime
import uuid

class TransferService:
    @staticmethod
    def create_transfer(source_canteen_id, dest_canteen_id, product_id, quantity, user_id):
        transfer = StockTransfer(
            source_canteen_id=source_canteen_id,
            destination_canteen_id=dest_canteen_id,
            product_id=product_id,
            quantity=quantity,
            requested_by=user_id,
            idempotency_key=str(uuid.uuid4())
        )
        db.session.add(transfer)
        db.session.commit()
        return transfer

    @staticmethod
    def approve_transfer(transfer_id, user_id):
        transfer = StockTransfer.query.get(transfer_id)
        if transfer.status != 'REQUESTED':
            raise ValueError(f"Transfer cannot be approved from status {transfer.status}")
            
        transfer.status = 'APPROVED'
        transfer.approved_by = user_id
        db.session.commit()
        return transfer

    @staticmethod
    def dispatch_transfer(transfer_id, user_id):
        transfer = StockTransfer.query.get(transfer_id)
        if transfer.status != 'APPROVED':
            raise ValueError(f"Transfer cannot be dispatched from status {transfer.status}")
            
        # Deduct from source inventory
        InventoryService.validate_and_decrement(
            product_id=transfer.product_id,
            quantity=transfer.quantity,
            user_id=user_id,
            reference_id=f"TRANSFER_OUT_{transfer.id}"
        )
        
        transfer.status = 'DISPATCHED'
        transfer.dispatched_by = user_id
        db.session.commit()
        return transfer

    @staticmethod
    def receive_transfer(transfer_id, user_id):
        transfer = StockTransfer.query.get(transfer_id)
        if transfer.status not in ['DISPATCHED', 'IN_TRANSIT']:
            raise ValueError(f"Transfer cannot be received from status {transfer.status}")
            
        # Add to destination inventory
        # We need to find the equivalent product in the destination canteen
        # For MVP, assume the global product or same product name exists
        from app.models.product import Product
        from app.models.stall import Stall
        
        source_prod = Product.query.get(transfer.product_id)
        
        # Find matching product in destination
        # Simplest approach: matching global_product_id or name
        dest_prod = Product.query.join(Stall).filter(
            Stall.canteen_id == transfer.destination_canteen_id,
            ((Product.global_product_id == source_prod.global_product_id) if source_prod.global_product_id else (Product.name == source_prod.name))
        ).first()
        
        if not dest_prod:
            # Need to create it or fail. MVP: fail.
            raise ValueError("Destination product mapping not found.")
            
        InventoryService.restock(
            product_id=dest_prod.id,
            quantity=transfer.quantity,
            user_id=user_id,
            reason=f"TRANSFER_IN_{transfer.id}"
        )
        
        transfer.status = 'RECEIVED'
        transfer.received_by = user_id
        db.session.commit()
        return transfer
