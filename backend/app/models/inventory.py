from ..extensions import db
from datetime import datetime

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
        db.CheckConstraint('low_stock_threshold >= 0', name='check_threshold_non_negative')
    )

    product = db.relationship('Product', backref=db.backref('inventory', uselist=False))

    def __repr__(self):
        return f"<Inventory ProductID:{self.product_id} Qty:{self.quantity}>"

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    quantity_change = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False) # SALE, RESTOCK, ADJUSTMENT, RETURN, DAMAGE
    reference_id = db.Column(db.String(100), nullable=True) # e.g. Order #1001
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reason = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    product = db.relationship('Product', backref='inventory_transactions')
    user = db.relationship('User', backref='inventory_transactions')

    def __repr__(self):
        return f"<InvTx ProductID:{self.product_id} Type:{self.transaction_type} Change:{self.quantity_change}>"
