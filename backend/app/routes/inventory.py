from flask import Blueprint, jsonify, request
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Product
from app.services.inventory_service import InventoryService
from app.extensions import db
from app.auth.middleware import require_auth, require_role

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api/v1/inventory')

@inventory_bp.route('/', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_inventory(current_user):
    """
    Get all inventory with support for filters.
    """
    query = Inventory.query.join(Product)
    
    stall_id = request.args.get('stall_id')
    status = request.args.get('status')
    
    if stall_id:
        query = query.filter(Product.stall_id == stall_id)
        
    items = query.all()
    result = []
    for inv in items:
        state = InventoryService.get_stock_status(inv.quantity, inv.low_stock_threshold)
        if status and state != status:
            continue
            
        result.append({
            "id": inv.id,
            "product_id": inv.product_id,
            "product_name": inv.product.name,
            "stall_id": inv.product.stall_id,
            "quantity": inv.quantity,
            "low_stock_threshold": inv.low_stock_threshold,
            "status": state,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        })
    return jsonify(success=True, data=result)

@inventory_bp.route('/<int:product_id>/restock', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def restock(current_user, product_id):
    """
    Restock a product.
    """
    data = request.get_json()
    quantity = data.get('quantity')
    
    if not quantity or not isinstance(quantity, int) or quantity <= 0:
        return jsonify(success=False, error={"code": "INVALID_QUANTITY", "message": "Valid quantity required"}), 400
        
    try:
        txn, new_qty, threshold = InventoryService.restock(
            product_id=product_id,
            quantity=quantity,
            user_id=current_user.id,
            reason=data.get('reason', 'RESTOCK')
        )
        db.session.commit()
        
        # Publish event (Phase 7 implementation)
        from app.services.event_service import EventService
        EventService.publish_inventory_updated(
            product_id=product_id,
            quantity=new_qty,
            status=InventoryService.get_stock_status(new_qty, threshold),
            transaction_type='RESTOCK'
        )
        
        return jsonify(success=True, data={
            "product_id": product_id,
            "new_quantity": new_qty,
            "status": InventoryService.get_stock_status(new_qty, threshold)
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": str(e)}), 400

@inventory_bp.route('/<int:product_id>/adjust', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def adjust(current_user, product_id):
    """
    Manually adjust inventory quantity.
    """
    data = request.get_json()
    new_quantity = data.get('new_quantity')
    reason = data.get('reason')
    
    if new_quantity is None or not isinstance(new_quantity, int) or new_quantity < 0:
        return jsonify(success=False, error={"code": "INVALID_QUANTITY", "message": "Valid new_quantity required"}), 400
        
    if not reason:
        return jsonify(success=False, error={"code": "MISSING_REASON", "message": "Adjustment reason required"}), 400
        
    try:
        txn, new_qty, threshold = InventoryService.adjust_stock(
            product_id=product_id,
            new_quantity=new_quantity,
            user_id=current_user.id,
            reason=reason
        )
        db.session.commit()
        
        # Publish event
        from app.services.event_service import EventService
        EventService.publish_inventory_updated(
            product_id=product_id,
            quantity=new_qty,
            status=InventoryService.get_stock_status(new_qty, threshold),
            transaction_type='MANUAL_ADJUSTMENT'
        )
        
        return jsonify(success=True, data={
            "product_id": product_id,
            "new_quantity": new_qty,
            "status": InventoryService.get_stock_status(new_qty, threshold)
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": str(e)}), 400

@inventory_bp.route('/<int:product_id>/history', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_history(current_user, product_id):
    """
    Get inventory history for a product.
    """
    history = InventoryTransaction.query.filter_by(product_id=product_id).order_by(InventoryTransaction.created_at.desc()).limit(50).all()
    result = []
    for txn in history:
        result.append({
            "id": txn.id,
            "transaction_type": txn.transaction_type,
            "quantity_change": txn.quantity_change,
            "previous_quantity": txn.previous_quantity,
            "new_quantity": txn.new_quantity,
            "reason": txn.reason,
            "reference_id": txn.reference_id,
            "performed_by": txn.user.name if txn.user else None,
            "created_at": txn.created_at.isoformat() if txn.created_at else None
        })
    return jsonify(success=True, data=result)
