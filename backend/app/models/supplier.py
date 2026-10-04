from ..extensions import db
from datetime import datetime

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True, index=True)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(50), nullable=False, default='ACTIVE', index=True) # ACTIVE, INACTIVE, SUSPENDED, ARCHIVED
    payment_terms = db.Column(db.String(100), nullable=True)
    lead_time = db.Column(db.Integer, nullable=True) # Default lead time in days
    
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship('SupplierProduct', backref='supplier', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Supplier {self.name} ({self.status})>"


class SupplierProduct(db.Model):
    __tablename__ = 'supplier_products'

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    
    supplier_sku = db.Column(db.String(100), nullable=True)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False)
    min_order_quantity = db.Column(db.Integer, nullable=False, default=1)
    pack_size = db.Column(db.String(50), nullable=True, default='Unit') # Procurement unit e.g. Case of 24
    pack_conversion_factor = db.Column(db.Integer, nullable=False, default=1) # 1 procurement unit = X inventory units
    lead_time = db.Column(db.Integer, nullable=True) # Override supplier default
    
    is_preferred = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(50), nullable=False, default='ACTIVE')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product')

    __table_args__ = (
        db.UniqueConstraint('supplier_id', 'product_id', name='uix_supplier_product'),
    )

    def __repr__(self):
        return f"<SupplierProduct Supplier:{self.supplier_id} Product:{self.product_id} Price:{self.purchase_price}>"
