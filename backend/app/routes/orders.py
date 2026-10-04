from flask import Blueprint, request, jsonify, g
from app.models.order import Order, OrderItem, Fulfillment
from app.models.product import Product
from app.models.inventory import Inventory, InventoryTransaction
from app.extensions import db
from app.auth.middleware import require_auth, require_role
from datetime import datetime
import uuid

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')

@orders_bp.route('/checkout', methods=['POST'])
@require_auth
@require_role(['CASHIER', 'ORG_ADMIN', 'CANTEEN_MANAGER'])
def checkout(current_user):
    data = request.get_json()
    if not data or 'items' not in data or not isinstance(data['items'], list):
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": "Invalid request format"}), 400

    items_data = data['items']
    if not items_data:
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": "Cart is empty"}), 400

    try:
        # Generate Order Number
        order_number = datetime.utcnow().strftime('%Y%m%d') + '-' + str(uuid.uuid4())[:8].upper()

        subtotal = 0
        order_items = []
        stall_items_map = {} # stall_id -> list of order_items
        inventory_events_to_publish = []

        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')

            if not product_id or not quantity or quantity <= 0:
                db.session.rollback()
                return jsonify(success=False, error={"code": "INVALID_QUANTITY", "message": "Invalid product or quantity"}), 400

            product = Product.query.get(product_id)
            if not product:
                db.session.rollback()
                return jsonify(success=False, error={"code": "PRODUCT_NOT_FOUND", "message": f"Product {product_id} not found"}), 404
                
            if product.status != 'ACTIVE' or product.availability != 'AVAILABLE':
                db.session.rollback()
                return jsonify(success=False, error={"code": "PRODUCT_UNAVAILABLE", "message": f"{product.name} is not available"}), 400

            # Atomic Inventory Deduction using InventoryService
            try:
                from app.services.inventory_service import InventoryService
                txn, new_qty, threshold, status_changed = InventoryService.validate_and_decrement(
                    product_id=product.id,
                    quantity=quantity,
                    user_id=current_user.id,
                    reference_id=f"Order {order_number}"
                )
                from app.services.inventory_service import InventoryService
                inventory_events_to_publish.append({
                    "product_id": product.id,
                    "quantity": new_qty,
                    "status": InventoryService.get_stock_status(new_qty, threshold),
                    "type": "SALE"
                })
            except ValueError as e:
                db.session.rollback()
                return jsonify(success=False, error={
                    "code": "INSUFFICIENT_STOCK" if "Insufficient" in str(e) else "INVALID_QUANTITY", 
                    "message": f"{str(e)} for {product.name}",
                    "product_id": product_id
                }), 400

            item_subtotal = float(product.price) * quantity
            subtotal += item_subtotal

            # Create Order Item (without order_id and fulfillment_id initially)
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
            cashier_id=current_user.id,
            organization_id=g.tenant_id,
            subtotal=subtotal,
            total=subtotal,
            status='PLACED'
        )
        db.session.add(order)
        db.session.flush() # Get order.id

        # Group by Stall and Create Fulfillments
        fulfillments = {}
        for stall_id, order_item in order_items:
            if stall_id not in fulfillments:
                fulfillment = Fulfillment(
                    order_id=order.id,
                    stall_id=stall_id,
                    status='PLACED',
                    organization_id=g.tenant_id
                )
                db.session.add(fulfillment)
                db.session.flush() # Get fulfillment.id
                fulfillments[stall_id] = fulfillment
            
            fulfillment = fulfillments[stall_id]
            order_item.order_id = order.id
            order_item.fulfillment_id = fulfillment.id
            db.session.add(order_item)

        db.session.commit()

        # Publish inventory updates
        from app.services.event_service import EventService
        for ev in inventory_events_to_publish:
            EventService.publish_inventory_updated(
                product_id=ev['product_id'],
                quantity=ev['quantity'],
                status=ev['status'],
                transaction_type=ev['type']
            )

        # Phase 6: Here is where the ORDER_CREATED event will be published

        return jsonify(success=True, order={
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total": float(order.total)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error={"code": "ORDER_CREATION_FAILED", "message": str(e)}), 500

@orders_bp.route('/<int:order_id>', methods=['GET'])
@require_auth
def get_order(current_user, order_id):
    order = Order.query.filter_by(id=order_id, organization_id=g.tenant_id).first()
    if not order:
        return jsonify(success=False, error={"code": "NOT_FOUND"}), 404
        
    return jsonify(success=True, order={
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "total": float(order.total),
        "items": [{
            "product_name": item.product_name_snapshot,
            "quantity": item.quantity,
            "subtotal": float(item.subtotal)
        } for item in order.items]
    })
