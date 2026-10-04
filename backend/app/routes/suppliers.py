from flask import Blueprint, jsonify, request
from app.models.supplier import Supplier, SupplierProduct
from app.models.product import Product
from app.extensions import db
from app.auth.middleware import require_auth, require_role

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/api/v1/suppliers')

@suppliers_bp.route('', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_suppliers(current_user):
    suppliers = Supplier.query.all()
    return jsonify(success=True, data=[{
        "id": s.id,
        "name": s.name,
        "contact_person": s.contact_person,
        "phone": s.phone,
        "email": s.email,
        "status": s.status,
        "lead_time": s.lead_time
    } for s in suppliers])

@suppliers_bp.route('', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def create_supplier(current_user):
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify(success=False, error={"code": "VALIDATION_ERROR", "message": "Supplier name is required"}), 400
        
    supplier = Supplier(
        name=data['name'],
        contact_person=data.get('contact_person'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        payment_terms=data.get('payment_terms'),
        lead_time=data.get('lead_time')
    )
    db.session.add(supplier)
    db.session.commit()
    
    return jsonify(success=True, data={"id": supplier.id, "name": supplier.name}), 201

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_supplier(current_user, supplier_id):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Supplier not found"}), 404
        
    products = [{
        "id": sp.id,
        "product_id": sp.product_id,
        "product_name": sp.product.name,
        "purchase_price": float(sp.purchase_price),
        "min_order_quantity": sp.min_order_quantity,
        "pack_size": sp.pack_size,
        "is_preferred": sp.is_preferred
    } for sp in supplier.products.all()]
        
    return jsonify(success=True, data={
        "id": supplier.id,
        "name": supplier.name,
        "contact_person": supplier.contact_person,
        "phone": supplier.phone,
        "email": supplier.email,
        "address": supplier.address,
        "status": supplier.status,
        "payment_terms": supplier.payment_terms,
        "lead_time": supplier.lead_time,
        "products": products
    })

@suppliers_bp.route('/<int:supplier_id>', methods=['PATCH'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def update_supplier(current_user, supplier_id):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Supplier not found"}), 404
        
    data = request.get_json()
    
    if 'name' in data: supplier.name = data['name']
    if 'contact_person' in data: supplier.contact_person = data['contact_person']
    if 'phone' in data: supplier.phone = data['phone']
    if 'email' in data: supplier.email = data['email']
    if 'address' in data: supplier.address = data['address']
    if 'status' in data: supplier.status = data['status']
    if 'payment_terms' in data: supplier.payment_terms = data['payment_terms']
    if 'lead_time' in data: supplier.lead_time = data['lead_time']
    
    db.session.commit()
    
    return jsonify(success=True, data={"id": supplier.id, "status": supplier.status})

@suppliers_bp.route('/<int:supplier_id>/products', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def add_supplier_product(current_user, supplier_id):
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Supplier not found"}), 404
        
    data = request.get_json()
    product_id = data.get('product_id')
    purchase_price = data.get('purchase_price')
    
    if not product_id or purchase_price is None or float(purchase_price) < 0:
        return jsonify(success=False, error={"code": "VALIDATION_ERROR", "message": "Invalid product_id or purchase_price"}), 400
        
    product = Product.query.get(product_id)
    if not product:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Product not found"}), 404
        
    existing = SupplierProduct.query.filter_by(supplier_id=supplier_id, product_id=product_id).first()
    if existing:
        return jsonify(success=False, error={"code": "CONFLICT", "message": "Supplier already supplies this product"}), 409
        
    sp = SupplierProduct(
        supplier_id=supplier_id,
        product_id=product_id,
        supplier_sku=data.get('supplier_sku'),
        purchase_price=purchase_price,
        min_order_quantity=data.get('min_order_quantity', 1),
        pack_size=data.get('pack_size', 'Unit'),
        pack_conversion_factor=data.get('pack_conversion_factor', 1),
        lead_time=data.get('lead_time'),
        is_preferred=data.get('is_preferred', False)
    )
    
    # If preferred, we should unset others? For MVP, just simple insert
    db.session.add(sp)
    db.session.commit()
    
    return jsonify(success=True, data={"id": sp.id}), 201
