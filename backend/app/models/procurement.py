from ..extensions import db
from datetime import datetime

class PurchaseRequest(db.Model):
    __tablename__ = 'purchase_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default='DRAFT', index=True) # DRAFT, SUBMITTED, APPROVED, REJECTED, CONVERTED_TO_PO, CANCELLED
    reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[requested_by])
    items = db.relationship('PurchaseRequestItem', backref='purchase_request', lazy='joined', cascade='all, delete-orphan')

class PurchaseRequestItem(db.Model):
    __tablename__ = 'purchase_request_items'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_requests.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True, index=True)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product')
    supplier = db.relationship('Supplier')


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    order_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expected_delivery_date = db.Column(db.DateTime, nullable=True)
    
    status = db.Column(db.String(50), nullable=False, default='DRAFT', index=True) # DRAFT, PENDING_APPROVAL, APPROVED, SENT, CONFIRMED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED, CLOSED
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    tax = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    
    notes = db.Column(db.Text, nullable=True)
    supplier_reference = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('Supplier')
    creator = db.relationship('User', foreign_keys=[created_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='joined', cascade='all, delete-orphan')


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    ordered_quantity = db.Column(db.Integer, nullable=False)
    procurement_unit = db.Column(db.String(50), nullable=False, default='Unit')
    pack_conversion_factor = db.Column(db.Integer, nullable=False, default=1)
    
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    received_quantity = db.Column(db.Integer, nullable=False, default=0)
    remaining_quantity = db.Column(db.Integer, nullable=False) # ordered_quantity - received_quantity
    
    __table_args__ = (
        db.CheckConstraint('ordered_quantity > 0', name='check_po_quantity_positive'),
        db.CheckConstraint('received_quantity >= 0', name='check_po_received_positive'),
        db.CheckConstraint('remaining_quantity >= 0', name='check_po_remaining_positive'),
    )

    product = db.relationship('Product')


class GoodsReceipt(db.Model):
    __tablename__ = 'goods_receipts'

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='RESTRICT'), nullable=False, index=True)
    receiving_user = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    status = db.Column(db.String(50), nullable=False, default='DRAFT', index=True) # DRAFT, SUBMITTED, VERIFIED, CANCELLED
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User')
    purchase_order = db.relationship('PurchaseOrder')
    items = db.relationship('GoodsReceiptItem', backref='goods_receipt', lazy='joined', cascade='all, delete-orphan')


class GoodsReceiptItem(db.Model):
    __tablename__ = 'goods_receipt_items'

    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('goods_receipts.id', ondelete='CASCADE'), nullable=False, index=True)
    po_item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_items.id', ondelete='RESTRICT'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    expected_quantity = db.Column(db.Integer, nullable=False)
    received_quantity = db.Column(db.Integer, nullable=False, default=0)
    rejected_quantity = db.Column(db.Integer, nullable=False, default=0)
    damaged_quantity = db.Column(db.Integer, nullable=False, default=0)
    accepted_quantity = db.Column(db.Integer, nullable=False, default=0) # Must equal received - rejected - damaged
    
    batch_number = db.Column(db.String(100), nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)

    po_item = db.relationship('PurchaseOrderItem')
    product = db.relationship('Product')
