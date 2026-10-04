from app.extensions import socketio, db
from app.models.outbox import OutboxEvent
import uuid
from datetime import datetime
import json

class EventService:
    @staticmethod
    def publish_inventory_updated(product_id, quantity, status, transaction_type):
        """
        Publishes INVENTORY_UPDATED event to all clients.
        If stock is 0, it also conceptually represents STOCK_DEPLETED for the frontend.
        """
        event_type = 'INVENTORY_UPDATED'
        if quantity == 0 and transaction_type == 'SALE':
            event_type = 'STOCK_DEPLETED'
        elif transaction_type == 'RESTOCK':
            event_type = 'STOCK_REPLENISHED'

        payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "product_id": product_id,
            "payload": {
                "available_quantity": quantity,
                "stock_status": status
            }
        }
        
        # Write to Outbox
        outbox = OutboxEvent(
            id=payload["event_id"],
            aggregate_type="Product",
            aggregate_id=str(product_id),
            event_type=event_type,
            payload=payload
        )
        db.session.add(outbox)
        # Commit should happen outside in the calling transaction, 
        # but if this is called outside transaction, we might need a flush.
        db.session.flush()

        # Broadcast globally to the 'inventory.global' room/channel.
        # SocketIO will handle sending this to connected clients.
        socketio.emit(event_type, payload)
        
        # Also broadcast a generic INVENTORY_UPDATED for easy syncing
        if event_type != 'INVENTORY_UPDATED':
             socketio.emit('INVENTORY_UPDATED', payload)

    @staticmethod
    def publish_order_created(order, fulfillments):
        event_id = str(uuid.uuid4())
        payload = {
            "event_id": event_id,
            "event_type": "ORDER_CREATED",
            "timestamp": datetime.utcnow().isoformat(),
            "order_id": order.id,
            "order_number": order.order_number,
            "payload": {
                "status": order.status,
                "total": float(order.total),
                "customer_id": order.customer_id,
                "fulfillments": [f.id for f in fulfillments.values()] if isinstance(fulfillments, dict) else [f.id for f in fulfillments]
            }
        }

        # Write to Outbox
        outbox = OutboxEvent(
            id=event_id,
            aggregate_type="Order",
            aggregate_id=str(order.id),
            event_type="ORDER_CREATED",
            payload=payload
        )
        db.session.add(outbox)
        db.session.flush()

        socketio.emit("ORDER_CREATED", payload)

    @staticmethod
    def publish_order_status_changed(order, new_status):
        event_id = str(uuid.uuid4())
        payload = {
            "event_id": event_id,
            "event_type": "ORDER_STATUS_CHANGED",
            "timestamp": datetime.utcnow().isoformat(),
            "order_id": order.id,
            "order_number": order.order_number,
            "payload": {
                "new_status": new_status,
                "customer_id": order.customer_id
            }
        }

        # Write to Outbox
        outbox = OutboxEvent(
            id=event_id,
            aggregate_type="Order",
            aggregate_id=str(order.id),
            event_type="ORDER_STATUS_CHANGED",
            payload=payload
        )
        db.session.add(outbox)
        db.session.flush()

        socketio.emit("ORDER_STATUS_CHANGED", payload)
