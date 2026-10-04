import json
from datetime import datetime, timezone
from app.extensions import db
from app.models.twin import OperationalSnapshot
from app.models import Canteen, Stall, Product, Inventory, Fulfillment, SupplierProduct

class DigitalTwinService:
    @staticmethod
    def generate_snapshot(institution_id, name=None, source_event_id=None):
        """
        Milestone 4: Operational Snapshots
        Generates a point-in-time copy of the operational state for a given institution.
        This forms the baseline for all simulations (Milestone 11 - no production side effects).
        """
        state_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "canteens": [],
            "stalls": {},
            "inventory": {},
            "active_orders": {},
            "suppliers": {}
        }
        
        # 1. Fetch Canteens
        # Assuming we filter by institution if Canteen has it, or via Campus. 
        # For MVP, we'll fetch all and filter locally or just fetch all if institution_id is None.
        canteens = Canteen.query.all()
        for c in canteens:
            state_data["canteens"].append({
                "id": c.id,
                "name": c.name,
                "campus_id": c.campus_id
            })
            
        # 2. Fetch Stalls & Kitchen Capacity
        stalls = Stall.query.all()
        for s in stalls:
            state_data["stalls"][s.id] = {
                "name": s.name,
                "canteen_id": s.canteen_id,
                "status": s.status,
                "capacity": 10 # Base assumed capacity
            }
            
        # 3. Fetch Inventory
        inventories = Inventory.query.all()
        for inv in inventories:
            state_data["inventory"][inv.product_id] = {
                "quantity": int(inv.quantity),
                "low_stock_threshold": inv.low_stock_threshold
            }
            
        # 4. Fetch Active Orders (Queues & Kitchen Load)
        active_statuses = ['ACCEPTED', 'PREPARING']
        active_fulfillments = Fulfillment.query.filter(Fulfillment.status.in_(active_statuses)).all()
        for f in active_fulfillments:
            if f.stall_id not in state_data["active_orders"]:
                state_data["active_orders"][f.stall_id] = 0
            state_data["active_orders"][f.stall_id] += 1
            
        # 5. Fetch Suppliers
        suppliers = SupplierProduct.query.all()
        for sp in suppliers:
            if sp.product_id not in state_data["suppliers"]:
                state_data["suppliers"][sp.product_id] = []
            state_data["suppliers"][sp.product_id].append({
                "supplier_id": sp.supplier_id,
                "lead_time_hours": sp.lead_time_hours,
                "unit_price": float(sp.unit_price),
                "reliability_score": sp.reliability_score
            })
            
        snapshot = OperationalSnapshot(
            institution_id=institution_id,
            name=name or f"Auto-Snapshot {datetime.now(timezone.utc).isoformat()}",
            source_event_id=source_event_id,
            state_data=state_data
        )
        
        db.session.add(snapshot)
        db.session.commit()
        
        return snapshot

    @staticmethod
    def get_latest_snapshot(institution_id):
        return OperationalSnapshot.query.filter_by(
            institution_id=institution_id
        ).order_by(OperationalSnapshot.timestamp.desc()).first()
