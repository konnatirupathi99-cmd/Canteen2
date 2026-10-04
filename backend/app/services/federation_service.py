import json
import logging
import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.inventory import Inventory
from app.models.organization import Canteen
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)

class FederationService:
    """
    Phase 19: Enterprise Intelligence & Federated Operations
    Handles network-wide intelligence, cross-canteen state and event synchronization.
    """
    
    @staticmethod
    def detect_network_inventory_imbalance(institution_id, product_id, needed_quantity):
        """
        Milestone 13: Cross-Canteen Inventory Intelligence.
        Finds a canteen within the same institution that has excess stock of the requested product.
        """
        # Find all canteens in the institution
        canteens = Canteen.query.filter_by(institution_id=institution_id).all()
        canteen_ids = [c.id for c in canteens]
        
        if not canteen_ids:
            return None
            
        # Find inventory in those canteens
        # Excess is defined as quantity > (low_stock_threshold * 2) + needed_quantity
        surplus_inventory = Inventory.query.filter(
            Inventory.canteen_id.in_(canteen_ids),
            Inventory.product_id == product_id,
            Inventory.quantity > (Inventory.low_stock_threshold * 2) + needed_quantity
        ).order_by(Inventory.quantity.desc()).first()
        
        if surplus_inventory:
            return {
                "source_canteen_id": surplus_inventory.canteen_id,
                "available_surplus": surplus_inventory.quantity - surplus_inventory.low_stock_threshold
            }
            
        return None

    @staticmethod
    def publish_federated_event(institution_id, campus_id, event_type, payload, scope='ENTERPRISE'):
        """
        Milestone 4: Federated Event Schema.
        Publishes an event to the enterprise event bus (simulated via OutboxEvent).
        """
        correlation_id = str(uuid.uuid4())
        
        # In a real enterprise system, this goes to Kafka/EventBridge.
        # We reuse OutboxEvent but mark it with federated metadata.
        federated_payload = {
            "federation": {
                "institution_id": institution_id,
                "campus_id": campus_id,
                "scope": scope,
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "data": payload
        }
        
        event = OutboxEvent(
            aggregate_type='FEDERATION',
            aggregate_id=str(institution_id),
            event_type=f"FEDERATED_{event_type}",
            payload=federated_payload
        )
        
        db.session.add(event)
        db.session.commit()
        return event.id
