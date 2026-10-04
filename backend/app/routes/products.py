from flask import Blueprint, jsonify, request, g
from app.models.product import Product
from app.models.category import Category
from app.models.stall import Stall
from app.extensions import db
from app.auth.middleware import require_auth

products_bp = Blueprint('products', __name__, url_prefix='/api/v1')

@products_bp.route('/products', methods=['GET'])
@require_auth
def get_products(current_user):
    """
    Returns products. For Phase 5 POS, we can filter by active/available.
    """
    query = Product.query.filter_by(organization_id=g.tenant_id)

    # Apply filters if provided in query params
    category_id = request.args.get('category_id')
    stall_id = request.args.get('stall_id')
    status = request.args.get('status')
    availability = request.args.get('availability')

    if category_id:
        query = query.filter_by(category_id=category_id)
    if stall_id:
        query = query.filter_by(stall_id=stall_id)
    if status:
        query = query.filter_by(status=status)
    if availability:
        query = query.filter_by(availability=availability)

    products = query.all()
    
    result = []
    for p in products:
        # Determine effective inventory state
        inv = p.inventory
        if not inv:
            state = "OUT_OF_STOCK"
            qty = 0
            threshold = 0
        else:
            qty = inv.quantity
            threshold = inv.low_stock_threshold
            if qty == 0:
                state = "OUT_OF_STOCK"
            elif qty <= threshold:
                state = "LOW_STOCK"
            else:
                state = "IN_STOCK"

        result.append({
            "id": p.id,
            "name": p.name,
            "category": {
                "id": p.category.id,
                "name": p.category.name
            } if p.category else None,
            "stall": {
                "id": p.stall.id,
                "name": p.stall.name
            } if p.stall else None,
            "price": float(p.price),
            "availability": p.availability,
            "status": p.status,
            "preparation_time": p.preparation_time,
            "inventory": {
                "quantity": qty,
                "low_stock_threshold": threshold,
                "state": state
            }
        })

    return jsonify(success=True, data=result)

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify(success=True, data=[{"id": c.id, "name": c.name} for c in categories])

@products_bp.route('/stalls', methods=['GET'])
@require_auth
def get_stalls(current_user):
    stalls = Stall.query.filter_by(organization_id=g.tenant_id).all()
    return jsonify(success=True, data=[{"id": s.id, "name": s.name} for s in stalls])
