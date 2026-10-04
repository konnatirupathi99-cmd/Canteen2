from flask import Blueprint, jsonify, request, g
from sqlalchemy.orm import joinedload
from ..models import Canteen, Stall, Product, Inventory, User, Order, OrderItem, Fulfillment
from ..extensions import db
from ..auth.middleware import require_auth, require_role
from ..services.inventory_service import InventoryService

customer_bp = Blueprint('customer', __name__, url_prefix='/api/v1/customer')

# ==============================================================================
# CANTEEN DISCOVERY
# ==============================================================================

@customer_bp.route('/canteens', methods=['GET'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def get_canteens(current_user):
    campus_id = request.args.get('campus_id')
    
    query = Canteen.query.filter_by(organization_id=g.tenant_id)
    if campus_id:
        query = query.filter_by(campus_id=campus_id)
        
    canteens = query.all()
    
    result = []
    for c in canteens:
        # In a real app, calculate estimated preparation time or queue size here
        result.append({
            'id': c.id,
            'name': c.name,
            'campus_id': c.campus_id,
            'status': 'OPEN', # MVP mock, ideally based on operating hours
            'estimated_preparation_min': 5 # mock
        })
        
    return jsonify({'success': True, 'canteens': result}), 200

@customer_bp.route('/canteens/<int:canteen_id>', methods=['GET'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def get_canteen(current_user, canteen_id):
    c = Canteen.query.filter_by(id=canteen_id, organization_id=g.tenant_id).first_or_404()
    return jsonify({
        'success': True, 
        'canteen': {
            'id': c.id,
            'name': c.name,
            'campus_id': c.campus_id,
            'status': 'OPEN',
            'estimated_preparation_min': 5
        }
    }), 200

# ==============================================================================
# STALL DISCOVERY
# ==============================================================================

@customer_bp.route('/canteens/<int:canteen_id>/stalls', methods=['GET'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def get_canteen_stalls(current_user, canteen_id):
    stalls = Stall.query.filter_by(canteen_id=canteen_id, organization_id=g.tenant_id).all()
    
    result = []
    for s in stalls:
        result.append({
            'id': s.id,
            'name': s.name,
            'canteen_id': s.canteen_id,
            'status': s.status,
            'estimated_preparation_min': 5 # mock
        })
        
    return jsonify({'success': True, 'stalls': result}), 200

# ==============================================================================
# LIVE MENU
# ==============================================================================

@customer_bp.route('/stalls/<int:stall_id>/menu', methods=['GET'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def get_live_menu(current_user, stall_id):
    # Only active products in the current tenant's stall
    products = Product.query.filter_by(stall_id=stall_id, status='ACTIVE', organization_id=g.tenant_id).all()
    
    # We need real-time availability from inventory
    # Fetch inventory for all products in this stall
    product_ids = [p.id for p in products]
    inventories = {inv.product_id: inv for inv in Inventory.query.filter(Inventory.product_id.in_(product_ids)).all()}
    
    result = []
    for p in products:
        inv = inventories.get(p.id)
        stock_quantity = int(inv.quantity) if inv else 0
        
        # Calculate availability status
        status = 'AVAILABLE'
        if stock_quantity <= 0:
            status = 'OUT_OF_STOCK'
        elif stock_quantity < 10:
            status = 'LOW_STOCK'
            
        result.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'category': p.category.name if p.category else None,
            'price': float(p.price),
            'preparation_time': p.preparation_time,
            'availability': status,
            'stock_quantity': stock_quantity # Optional, might want to hide exact count
        })
        
    return jsonify({'success': True, 'menu': result}), 200

# ==============================================================================
# CART & CHECKOUT (Atomic, Idempotent, Inventory-aware)
# ==============================================================================
import uuid
from datetime import datetime
from ..services.event_service import EventService

@customer_bp.route('/cart/validate', methods=['POST'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def validate_cart(current_user):
    data = request.get_json()
    items_data = data.get('items', [])
    
    if not items_data:
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": "Cart is empty"}), 400
        
    validation_results = []
    is_valid = True
    subtotal = 0
    
    for item in items_data:
        product_id = item.get('product_id')
        qty = item.get('quantity', 0)
        
        product = Product.query.get(product_id)
        if not product:
            validation_results.append({"product_id": product_id, "status": "NOT_FOUND"})
            is_valid = False
            continue
            
        if product.status != 'ACTIVE' or product.availability != 'AVAILABLE':
            validation_results.append({"product_id": product_id, "status": "UNAVAILABLE", "name": product.name})
            is_valid = False
            continue
            
        inv = Inventory.query.filter_by(product_id=product.id).first()
        stock = int(inv.quantity) if inv else 0
        
        if stock < qty:
            validation_results.append({
                "product_id": product_id, 
                "status": "INSUFFICIENT_STOCK", 
                "name": product.name,
                "requested": qty,
                "available": stock
            })
            is_valid = False
            continue
            
        subtotal += float(product.price) * qty
        validation_results.append({
            "product_id": product_id,
            "status": "VALID",
            "name": product.name,
            "price": float(product.price),
            "subtotal": float(product.price) * qty
        })
        
    return jsonify({
        "success": True,
        "is_valid": is_valid,
        "results": validation_results,
        "calculated_subtotal": subtotal
    }), 200

import hashlib
import json
from ..models.idempotency import IdempotencyRecord
from ..models.outbox import OutboxEvent

@customer_bp.route('/orders', methods=['POST'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def create_customer_order(current_user):
    # STEP 14: Idempotency check
    idempotency_key = request.headers.get('Idempotency-Key')
    if not idempotency_key:
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": "Idempotency-Key header is required"}), 400
        
    data = request.get_json()
    request_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
    from flask import Response

    # Check for existing idempotency record
    record = IdempotencyRecord.query.get(idempotency_key)
    if record:
        if record.request_hash != request_hash:
            return jsonify(success=False, error={"code": "IDEMPOTENCY_CONFLICT", "message": "Idempotency key reused with different request"}), 409
        if record.response_body:
            return Response(record.response_body, status=record.response_status_code, mimetype='application/json')
        return jsonify(success=False, error={"code": "CONCURRENT_REQUEST", "message": "Request is already being processed"}), 409

    # Try to lock the idempotency key (creates it)
    try:
        record = IdempotencyRecord(idempotency_key=idempotency_key, customer_id=current_user.id, request_hash=request_hash)
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error={"code": "CONCURRENT_REQUEST", "message": "Request is already being processed"}), 409

    items_data = data.get('items', [])
    payment_method = data.get('payment_method', 'ONLINE')
    
    if not items_data:
        record.response_body = json.dumps({"success": False, "error": {"code": "BAD_REQUEST", "message": "Cart is empty"}})
        record.response_status_code = 400
        db.session.commit()
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": "Cart is empty"}), 400

    try:
        # Generate Customer Order Number
        order_number = f"C-{datetime.utcnow().strftime('%y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

        subtotal = 0
        order_items = []
        inventory_events = []

        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')

            if not product_id or not quantity or quantity <= 0:
                db.session.rollback()
                resp = {"success": False, "error": {"code": "INVALID_QUANTITY", "message": "Invalid product or quantity"}}
                record.response_body = json.dumps(resp)
                record.response_status_code = 400
                db.session.commit()
                return jsonify(resp), 400

            product = Product.query.get(product_id)
            if not product or product.status != 'ACTIVE' or product.availability != 'AVAILABLE':
                db.session.rollback()
                resp = {"success": False, "error": {"code": "PRODUCT_UNAVAILABLE", "message": "Product unavailable"}}
                record.response_body = json.dumps(resp)
                record.response_status_code = 400
                db.session.commit()
                return jsonify(resp), 400

            # Atomic Inventory Deduction (Phase 7 mechanism)
            try:
                txn, new_qty, threshold, status_changed = InventoryService.validate_and_decrement(
                    product_id=product.id,
                    quantity=quantity,
                    user_id=current_user.id,
                    reference_id=f"Order {order_number}"
                )
                inventory_events.append({
                    "product_id": product.id,
                    "quantity": new_qty,
                    "status": InventoryService.get_stock_status(new_qty, threshold),
                    "type": "SALE"
                })
            except ValueError as e:
                db.session.rollback()
                resp = {"success": False, "error": {"code": "INSUFFICIENT_STOCK", "message": str(e)}}
                record.response_body = json.dumps(resp)
                record.response_status_code = 400
                db.session.commit()
                return jsonify(resp), 400

            item_subtotal = float(product.price) * quantity
            subtotal += item_subtotal

            order_item = OrderItem(
                product_id=product.id,
                product_name_snapshot=product.name,
                quantity=quantity,
                unit_price=product.price,
                subtotal=item_subtotal
            )
            order_items.append((product.stall_id, order_item))

        # Create Order
        order = Order(
            order_number=order_number,
            customer_id=current_user.id,
            organization_id=g.tenant_id,
            subtotal=subtotal,
            total=subtotal,
            status='PLACED'
        )
        db.session.add(order)
        db.session.flush()

        # STEP 16: Payment Integration/Abstraction (Phase 22 Resilient Payment)
        from app.services.payment_service import PaymentService
        payment_status_to_order = 'PAYMENT_PENDING'
        if payment_method == 'ONLINE':
            payment = PaymentService.initiate_payment(order, g.tenant_id, subtotal, provider='STRIPE', idempotency_key=f"pay_{idempotency_key}")
            payment = PaymentService.process_payment(payment.id)
            if payment.status == 'FAILED':
                raise ValueError(f"Payment failed: {payment.error_message}")
            elif payment.status in ['CAPTURED', 'AUTHORIZED']:
                payment_status_to_order = 'CONFIRMED'
            else:
                # UNKNOWN or PENDING
                payment_status_to_order = 'PAYMENT_PENDING'

        order.status = payment_status_to_order
        db.session.flush()

        fulfillments = {}
        for stall_id, order_item in order_items:
            if stall_id not in fulfillments:
                fulfillment = Fulfillment(
                    order_id=order.id,
                    stall_id=stall_id,
                    status=payment_status_to_order,
                    organization_id=g.tenant_id
                )
                db.session.add(fulfillment)
                db.session.flush()
                fulfillments[stall_id] = fulfillment
            
            fulfillment = fulfillments[stall_id]
            order_item.order_id = order.id
            order_item.fulfillment_id = fulfillment.id
            db.session.add(order_item)

        db.session.commit()

        # Update Idempotency Record
        resp = {
            "success": True, 
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total": float(order.total)
            }
        }
        record.response_body = json.dumps(resp)
        record.response_status_code = 201
        db.session.commit()

        # Emit events asynchronously
        for ev in inventory_events:
            EventService.publish_inventory_updated(
                product_id=ev['product_id'],
                quantity=ev['quantity'],
                status=ev['status'],
                transaction_type=ev['type']
            )
            
        EventService.publish_order_created(order, fulfillments)

        return jsonify(resp), 201

    except Exception as e:
        db.session.rollback()
        resp = {"success": False, "error": {"code": "ORDER_FAILED", "message": str(e)}}
        record.response_body = json.dumps(resp)
        record.response_status_code = 500
        db.session.commit()
        return jsonify(resp), 500

# ==============================================================================
# ORDER TRACKING & HISTORY
# ==============================================================================

@customer_bp.route('/orders', methods=['GET'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def get_orders(current_user):
    # Customer Data Isolation (Only their own orders in this tenant)
    orders = Order.query.filter_by(customer_id=current_user.id, organization_id=g.tenant_id).order_by(Order.created_at.desc()).all()
    
    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "total": float(o.total),
            "created_at": o.created_at.isoformat()
        })
        
    return jsonify({"success": True, "orders": result}), 200

@customer_bp.route('/orders/<int:order_id>', methods=['GET'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def get_order(current_user, order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id, organization_id=g.tenant_id).first()
    if not order:
        return jsonify(success=False, error={"code": "NOT_FOUND"}), 404
        
    items = []
    for item in order.items:
        items.append({
            "product_name": item.product_name_snapshot,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
            "fulfillment_status": item.fulfillment.status if item.fulfillment else order.status
        })
        
    return jsonify({
        "success": True,
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total": float(order.total),
            "created_at": order.created_at.isoformat(),
            "items": items,
            "pickup_code": order.order_number[-4:] # Simple deterministic pickup code based on order number
        }
    }), 200

@customer_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def cancel_order(current_user, order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id, organization_id=g.tenant_id).first()
    if not order:
        return jsonify(success=False, error={"code": "NOT_FOUND"}), 404
        
    # Cancellation policy: Only if PLACED, PAYMENT_PENDING, or CONFIRMED
    if order.status not in ['PLACED', 'PAYMENT_PENDING', 'CONFIRMED']:
        return jsonify(success=False, error={"code": "NOT_CANCELLABLE", "message": f"Order cannot be cancelled in status {order.status}"}), 400
        
    # Actually process cancellation (RESTOCK inventory)
    try:
        for item in order.items:
            InventoryService.restock(
                product_id=item.product_id,
                quantity=item.quantity,
                user_id=current_user.id,
                reason=f"Order {order.order_number} Cancelled"
            )
            
        order.status = 'CANCELLED'
        for f in order.fulfillments:
            f.status = 'CANCELLED'
            
        db.session.commit()
        
        EventService.publish_order_status_changed(order, 'CANCELLED')
        
        return jsonify({"success": True, "message": "Order cancelled successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error={"code": "CANCELLATION_FAILED", "message": str(e)}), 500

@customer_bp.route('/feedback', methods=['POST'])
@require_auth
@require_role(['CUSTOMER', 'ORG_ADMIN'])
def submit_feedback(current_user):
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment')
    order_id = data.get('order_id')
    stall_id = data.get('stall_id')
    
    if not rating or rating < 1 or rating > 5:
        return jsonify(success=False, error={"code": "INVALID_RATING", "message": "Rating must be between 1 and 5"}), 400
        
    from app.models.feedback import CustomerFeedback
    feedback = CustomerFeedback(
        customer_id=current_user.id,
        order_id=order_id,
        stall_id=stall_id,
        rating=rating,
        comment=comment,
        category=data.get('category')
    )
    db.session.add(feedback)
    
    # Milestone 10: Direct Integration to Intelligence
    if rating <= 2:
        from app.models.intelligence import IntelligenceSignal
        signal = IntelligenceSignal(
            type='NEGATIVE_FEEDBACK',
            severity='MEDIUM' if rating == 2 else 'HIGH',
            message=f"Poor customer rating received: {rating}/5",
            context_data=json.dumps({"stall_id": stall_id, "comment": comment}),
            stall_id=stall_id
        )
        db.session.add(signal)
        
    db.session.commit()
    
    return jsonify(success=True, message="Feedback submitted successfully"), 201


