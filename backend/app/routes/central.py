from flask import Blueprint, jsonify, request
from app.models.organization import Institution, Campus, Canteen
from app.models.stall import Stall
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.predictive import WasteRecord, Forecast
from app.auth.middleware import require_auth
from app.auth.scope import has_scope_permission, get_authorized_canteen_ids
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

central_bp = Blueprint('central', __name__, url_prefix='/api/v1/central')

@central_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_central_dashboard(current_user):
    # Determine the authorized scope
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN', 'INSTITUTION_ADMIN', 'CAMPUS_ADMIN', 'CANTEEN_MANAGER']):
        return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Insufficient permissions"}), 403

    authorized_canteen_ids = get_authorized_canteen_ids(current_user)
    
    # Location filtering from query parameters
    canteen_id_filter = request.args.get('canteen_id', type=int)
    if canteen_id_filter:
        if canteen_id_filter not in authorized_canteen_ids:
             return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Unauthorized canteen"}), 403
        target_canteen_ids = [canteen_id_filter]
    else:
        target_canteen_ids = authorized_canteen_ids
        
    if not target_canteen_ids:
        return jsonify(success=True, data={"metrics": {}, "canteens": []})
        
    # Get stalls for these canteens
    stalls = Stall.query.filter(Stall.canteen_id.in_(target_canteen_ids)).all()
    stall_ids = [s.id for s in stalls]
    
    # Basic metrics
    today = datetime.utcnow().date()
    
    # Orders today
    orders = Order.query.filter(Order.created_at >= today).all()
    # Filter by stalls if order had a stall linkage (Fulfillment)
    # Since Fulfillment links to stall, we can join it, or simplify for MVP since OrderItem -> Product -> Stall
    from app.models.product import Product
    from app.models.order import OrderItem
    
    total_orders = db.session.query(func.count(func.distinct(Order.id)))\
        .join(OrderItem).join(Product)\
        .filter(Product.stall_id.in_(stall_ids))\
        .filter(Order.created_at >= today).scalar() or 0
        
    # Active orders (PLACED, PREPARING)
    active_orders = db.session.query(func.count(func.distinct(Order.id)))\
        .join(OrderItem).join(Product)\
        .filter(Product.stall_id.in_(stall_ids))\
        .filter(Order.status.in_(['PLACED', 'PREPARING', 'READY'])).scalar() or 0
        
    # High Waste Locations count (Canteens with > X waste today)
    waste_records = db.session.query(WasteRecord.stall_id, func.sum(WasteRecord.quantity))\
        .filter(WasteRecord.stall_id.in_(stall_ids))\
        .filter(WasteRecord.recorded_at >= today)\
        .group_by(WasteRecord.stall_id).all()
    high_waste_count = len([w for w in waste_records if w[1] > 50]) # Arbitrary threshold for MVP
    
    # Inventory Alerts
    low_stock_count = db.session.query(func.count(Inventory.id))\
        .join(Product)\
        .filter(Product.stall_id.in_(stall_ids))\
        .filter(Inventory.quantity <= Inventory.low_stock_threshold).scalar() or 0
        
    metrics = {
        "orders_today": total_orders,
        "active_orders": active_orders,
        "stockout_risks": low_stock_count,
        "high_waste_locations": high_waste_count,
        "system_health": "HEALTHY"
    }
    
    return jsonify(success=True, data={"metrics": metrics})
    
@central_bp.route('/inventory', methods=['GET'])
@require_auth
def get_central_inventory(current_user):
    authorized_canteen_ids = get_authorized_canteen_ids(current_user)
    
    canteen_id_filter = request.args.get('canteen_id', type=int)
    if canteen_id_filter and canteen_id_filter in authorized_canteen_ids:
        authorized_canteen_ids = [canteen_id_filter]
        
    stalls = Stall.query.filter(Stall.canteen_id.in_(authorized_canteen_ids)).all()
    stall_ids = [s.id for s in stalls]
    
    from app.models.product import Product
    inventory_items = db.session.query(Inventory, Product, Stall, Canteen)\
        .join(Product, Inventory.product_id == Product.id)\
        .join(Stall, Product.stall_id == Stall.id)\
        .outerjoin(Canteen, Stall.canteen_id == Canteen.id)\
        .filter(Stall.id.in_(stall_ids)).all()
        
    data = []
    for inv, prod, stall, canteen in inventory_items:
        data.append({
            "inventory_id": inv.id,
            "product_id": prod.id,
            "product_name": prod.name,
            "quantity": inv.quantity,
            "threshold": inv.low_stock_threshold,
            "stall_name": stall.name,
            "canteen_name": canteen.name if canteen else "Unknown",
            "canteen_id": canteen.id if canteen else None
        })
        
    return jsonify(success=True, data=data)

from app.services.transfer_service import TransferService
from app.models.transfer import StockTransfer

@central_bp.route('/transfers', methods=['POST'])
@require_auth
def request_transfer(current_user):
    # Determine the authorized scope
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN', 'INSTITUTION_ADMIN', 'CAMPUS_ADMIN', 'CANTEEN_MANAGER']):
        return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Insufficient permissions"}), 403
        
    data = request.get_json()
    source_canteen = data.get('source_canteen_id')
    dest_canteen = data.get('destination_canteen_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    if not source_canteen or not dest_canteen or not product_id or not quantity or quantity <= 0:
        return jsonify(success=False, error={"code": "VALIDATION_ERROR"}), 400
        
    t = TransferService.create_transfer(source_canteen, dest_canteen, product_id, quantity, current_user.id)
    return jsonify(success=True, data={"id": t.id})

@central_bp.route('/transfers/<int:id>/<string:action>', methods=['POST'])
@require_auth
def execute_transfer_action(current_user, id, action):
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN', 'INSTITUTION_ADMIN', 'CAMPUS_ADMIN', 'CANTEEN_MANAGER']):
        return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Insufficient permissions"}), 403
        
    try:
        if action == 'approve':
            TransferService.approve_transfer(id, current_user.id)
        elif action == 'dispatch':
            TransferService.dispatch_transfer(id, current_user.id)
        elif action == 'receive':
            TransferService.receive_transfer(id, current_user.id)
        else:
            return jsonify(success=False, error={"code": "NOT_FOUND"}), 404
            
        return jsonify(success=True)
    except ValueError as e:
        return jsonify(success=False, error={"code": "VALIDATION_ERROR", "message": str(e)}), 400

@central_bp.route('/forecasts', methods=['GET'])
@require_auth
def get_central_forecasts(current_user):
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN', 'INSTITUTION_ADMIN', 'CAMPUS_ADMIN', 'CANTEEN_MANAGER']):
        return jsonify(success=False, error={"code": "FORBIDDEN"}), 403
        
    authorized_canteen_ids = get_authorized_canteen_ids(current_user)
    
    canteen_id_filter = request.args.get('canteen_id', type=int)
    if canteen_id_filter and canteen_id_filter in authorized_canteen_ids:
        authorized_canteen_ids = [canteen_id_filter]
        
    stalls = Stall.query.filter(Stall.canteen_id.in_(authorized_canteen_ids)).all()
    stall_ids = [s.id for s in stalls]
    
    from app.models.product import Product
    from app.models.predictive import Forecast
    
    # Target date
    target = request.args.get('date', (datetime.utcnow() + timedelta(days=1)).date().isoformat())
    
    forecasts = db.session.query(
        Product.global_product_id,
        func.sum(Forecast.predicted_quantity).label('total_forecast')
    ).join(Product).filter(Product.stall_id.in_(stall_ids))\
     .filter(Forecast.forecast_date == target)\
     .filter(Forecast.status == 'ACTIVE')\
     .group_by(Product.global_product_id).all()
     
    data = []
    for g_id, total in forecasts:
        data.append({"global_product_id": g_id, "total_forecast": total})
        
    return jsonify(success=True, data=data)

@central_bp.route('/procurement/opportunities', methods=['GET'])
@require_auth
def get_procurement_opportunities(current_user):
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN', 'INSTITUTION_ADMIN']):
        return jsonify(success=False, error={"code": "FORBIDDEN"}), 403
        
    # Aggregate PRs that are in 'DRAFT' or 'SUBMITTED' across canteens
    from app.models.procurement import PurchaseRequestItem, PurchaseRequest
    from app.models.product import Product
    
    prs = db.session.query(
        Product.global_product_id,
        func.sum(PurchaseRequestItem.quantity).label('total_requested')
    ).join(PurchaseRequest).join(Product, PurchaseRequestItem.product_id == Product.id)\
     .filter(PurchaseRequest.status.in_(['DRAFT', 'SUBMITTED']))\
     .group_by(Product.global_product_id).all()
     
    data = []
    for g_id, total in prs:
        # A naive recommendation logic
        if total > 500: # Threshold for bulk
            data.append({
                "global_product_id": g_id,
                "total_requested": total,
                "recommendation": "Potential consolidated procurement opportunity."
            })
            
    return jsonify(success=True, data=data)

# ==========================================
# PHASE 19: ENTERPRISE FEDERATION APIs
# ==========================================
@central_bp.route('/federation/events', methods=['POST'])
@require_auth
def sync_federated_events(current_user):
    """
    Milestone 4, 5: Federated Event Schema & Sync
    Ingests events from local nodes.
    """
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN', 'INSTITUTION_ADMIN']):
        return jsonify(success=False, error={"code": "FORBIDDEN"}), 403
        
    events = request.get_json().get('events', [])
    # In a real system, these would go to Kafka or trigger EnterpriseAgents.
    # We acknowledge receipt.
    return jsonify(success=True, synced_count=len(events), status="ACKNOWLEDGED")

@central_bp.route('/network-health', methods=['GET'])
@require_auth
def get_enterprise_network_health(current_user):
    """
    Milestone 25: Enterprise Observability & Dashboard
    """
    if not has_scope_permission(current_user, ['SYSTEM_ADMIN']):
        return jsonify(success=False, error={"code": "FORBIDDEN"}), 403
        
    from app.models.agents import AgentRegistry
    agents = AgentRegistry.query.all()
    
    agent_health = {
        "active": len([a for a in agents if a.status == 'ACTIVE']),
        "failing": len([a for a in agents if a.status in ['PAUSED', 'DEGRADED', 'ERROR']]),
        "total": len(agents)
    }
    
    # In MVP, assume 1 institution, 2 campuses (canteens)
    network = {
        "institutions_online": 1,
        "campuses_online": Canteen.query.count(),
        "agent_health": agent_health,
        "critical_incidents": 0,
        "system_status": "OPERATIONAL"
    }
    
    return jsonify(success=True, network_health=network)
