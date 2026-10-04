from flask import Blueprint, jsonify, request
from app.models.procurement import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from app.models.supplier import Supplier
from app.models.product import Product
from app.extensions import db
from app.auth.middleware import require_auth, require_role
from datetime import datetime
import uuid

procurement_bp = Blueprint('procurement', __name__, url_prefix='/api/v1/procurement')

def generate_po_number():
    date_str = datetime.utcnow().strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:6].upper()
    return f"PO-{date_str}-{short_uuid}"

def generate_receipt_number():
    date_str = datetime.utcnow().strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:6].upper()
    return f"GR-{date_str}-{short_uuid}"

@procurement_bp.route('/requests', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def create_purchase_request(current_user):
    data = request.get_json()
    items_data = data.get('items', [])
    
    if not items_data:
        return jsonify(success=False, error={"code": "VALIDATION_ERROR", "message": "Items are required"}), 400
        
    req = PurchaseRequest(
        request_number=f"PR-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}",
        requested_by=current_user.id,
        reason=data.get('reason'),
        status='SUBMITTED'
    )
    db.session.add(req)
    db.session.flush()
    
    for item in items_data:
        pri = PurchaseRequestItem(
            request_id=req.id,
            product_id=item['product_id'],
            supplier_id=item.get('supplier_id'),
            quantity=item['quantity']
        )
        db.session.add(pri)
        
    db.session.commit()
    return jsonify(success=True, data={"id": req.id, "request_number": req.request_number}), 201

@procurement_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def approve_purchase_request(current_user, request_id):
    req = PurchaseRequest.query.get(request_id)
    if not req or req.status != 'SUBMITTED':
        return jsonify(success=False, error={"code": "INVALID_STATE", "message": "Request not found or not in SUBMITTED state"}), 400
        
    req.status = 'APPROVED'
    
    # Auto-convert to PO for MVP
    # Group items by supplier to create POs
    supplier_items = {}
    for item in req.items:
        sup_id = item.supplier_id
        if not sup_id:
            # Try to find preferred supplier or just any supplier
            from app.models.supplier import SupplierProduct
            sp = SupplierProduct.query.filter_by(product_id=item.product_id).first()
            if sp:
                sup_id = sp.supplier_id
            else:
                continue # Cannot order without supplier
                
        if sup_id not in supplier_items:
            supplier_items[sup_id] = []
        supplier_items[sup_id].append(item)
        
    pos = []
    for sup_id, items in supplier_items.items():
        po = PurchaseOrder(
            po_number=generate_po_number(),
            supplier_id=sup_id,
            created_by=req.requested_by,
            approved_by=current_user.id,
            status='APPROVED'
        )
        db.session.add(po)
        db.session.flush()
        
        subtotal = 0
        for req_item in items:
            from app.models.supplier import SupplierProduct
            sp = SupplierProduct.query.filter_by(supplier_id=sup_id, product_id=req_item.product_id).first()
            price = sp.purchase_price if sp else 0
            
            po_item = PurchaseOrderItem(
                po_id=po.id,
                product_id=req_item.product_id,
                ordered_quantity=req_item.quantity,
                unit_price=price,
                subtotal=req_item.quantity * price,
                remaining_quantity=req_item.quantity
            )
            subtotal += po_item.subtotal
            db.session.add(po_item)
            
        po.subtotal = subtotal
        po.total = subtotal
        pos.append(po.po_number)
        
    req.status = 'CONVERTED_TO_PO'
    db.session.commit()
    
    return jsonify(success=True, data={"status": req.status, "purchase_orders": pos})

@procurement_bp.route('/orders/<int:po_id>/send', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def send_purchase_order(current_user, po_id):
    po = PurchaseOrder.query.get(po_id)
    if not po or po.status != 'APPROVED':
        return jsonify(success=False, error={"code": "INVALID_STATE"}), 400
    
    po.status = 'SENT'
    db.session.commit()
    return jsonify(success=True, data={"status": po.status})

@procurement_bp.route('/orders/<int:po_id>/confirm', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def confirm_purchase_order(current_user, po_id):
    data = request.get_json() or {}
    po = PurchaseOrder.query.get(po_id)
    if not po or po.status != 'SENT':
        return jsonify(success=False, error={"code": "INVALID_STATE"}), 400
    
    po.status = 'CONFIRMED'
    if data.get('expected_delivery_date'):
        po.expected_delivery_date = datetime.fromisoformat(data['expected_delivery_date'].replace('Z', '+00:00')).replace(tzinfo=None)
    
    db.session.commit()
    return jsonify(success=True, data={"status": po.status})

@procurement_bp.route('/receipts', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def receive_goods(current_user):
    data = request.get_json()
    po_id = data.get('po_id')
    items_data = data.get('items', [])
    
    po = PurchaseOrder.query.get(po_id)
    if not po or po.status not in ['CONFIRMED', 'PARTIALLY_RECEIVED']:
        return jsonify(success=False, error={"code": "INVALID_STATE", "message": "PO not ready for receiving"}), 400
        
    gr = GoodsReceipt(
        receipt_number=generate_receipt_number(),
        po_id=po.id,
        receiving_user=current_user.id,
        status='VERIFIED'
    )
    db.session.add(gr)
    db.session.flush()
    
    from app.services.inventory_service import InventoryService
    
    all_received = True
    any_received = False
    
    for item in items_data:
        po_item = PurchaseOrderItem.query.get(item['po_item_id'])
        if po_item.po_id != po.id:
            continue
            
        received = int(item.get('received_quantity', 0))
        rejected = int(item.get('rejected_quantity', 0))
        damaged = int(item.get('damaged_quantity', 0))
        accepted = received - rejected - damaged
        
        if accepted < 0 or received > po_item.remaining_quantity:
            return jsonify(success=False, error={"code": "VALIDATION_ERROR", "message": "Invalid receiving quantities"}), 400
            
        if received > 0:
            any_received = True
            
        gr_item = GoodsReceiptItem(
            receipt_id=gr.id,
            po_item_id=po_item.id,
            product_id=po_item.product_id,
            expected_quantity=po_item.remaining_quantity,
            received_quantity=received,
            rejected_quantity=rejected,
            damaged_quantity=damaged,
            accepted_quantity=accepted
        )
        db.session.add(gr_item)
        
        # Update PO Item
        po_item.received_quantity += received
        po_item.remaining_quantity -= received
        
        if po_item.remaining_quantity > 0:
            all_received = False
            
        # Update Inventory via Phase 7 mechanism
        if accepted > 0:
            InventoryService.restock(
                product_id=po_item.product_id,
                quantity=accepted,
                user_id=current_user.id,
                reason=f"GR-{gr.id}"
            )
            
    if any_received:
        po.status = 'RECEIVED' if all_received else 'PARTIALLY_RECEIVED'
    
    db.session.commit()
    
    return jsonify(success=True, data={"receipt_id": gr.id, "po_status": po.status}), 201
