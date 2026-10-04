from ..extensions import db
from datetime import datetime

class GlobalProduct(db.Model):
    __tablename__ = 'global_products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    default_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    status = db.Column(db.String(50), nullable=False, default='ACTIVE')
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<GlobalProduct {self.name}>"

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    global_product_id = db.Column(db.Integer, db.ForeignKey('global_products.id', ondelete='SET NULL'), nullable=True, index=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # We use RESTRICT here to prevent accidentally deleting a stall/category that has active products.
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    status = db.Column(db.String(50), nullable=False, default='ACTIVE', index=True) # ACTIVE, INACTIVE, ARCHIVED
    availability = db.Column(db.String(50), nullable=False, default='AVAILABLE') # AVAILABLE, UNAVAILABLE
    preparation_time = db.Column(db.Integer, default=0) # in minutes
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add CHECK constraint for positive price
    __table_args__ = (
        db.CheckConstraint('price >= 0', name='check_price_positive'),
    )

    category = db.relationship('Category', backref='products')
    stall = db.relationship('Stall', backref='products')

    def __repr__(self):
        return f"<Product {self.name} - ₹{self.price}>"
