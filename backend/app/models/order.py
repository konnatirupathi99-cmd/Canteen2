from ..extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    status = db.Column(db.String(50), nullable=False, default='PLACED', index=True) # PLACED, PREPARING, READY, FULFILLED, CANCELLED
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('total >= 0', name='check_total_positive'),
    )

    cashier = db.relationship('User', foreign_keys=[cashier_id], backref='processed_orders')
    customer = db.relationship('User', foreign_keys=[customer_id], backref='placed_orders')
    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', cascade='all, delete-orphan')
    fulfillments = db.relationship('Fulfillment', backref='order', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status})>"

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    fulfillment_id = db.Column(db.Integer, db.ForeignKey('fulfillments.id', ondelete='CASCADE'), nullable=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    # Historical snapshot
    product_name_snapshot = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_order_quantity_positive'),
        db.CheckConstraint('unit_price >= 0', name='check_order_unit_price_positive')
    )

    product = db.relationship('Product')

    def __repr__(self):
        return f"<OrderItem {self.quantity}x {self.product_name_snapshot}>"

class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User')

    def __repr__(self):
        return f"<OrderStatusHistory Order:{self.order_id} {self.previous_status}->{self.new_status}>"

class Fulfillment(db.Model):
    __tablename__ = 'fulfillments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    status = db.Column(db.String(50), nullable=False, default='PLACED', index=True) # PLACED, PREPARING, READY, FULFILLED, CANCELLED
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stall = db.relationship('Stall')
    items = db.relationship('OrderItem', backref='fulfillment', lazy='joined')
    
    def __repr__(self):
        return f"<Fulfillment Order:{self.order_id} Stall:{self.stall_id} Status:{self.status}>"
