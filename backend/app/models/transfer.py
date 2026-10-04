from ..extensions import db
from datetime import datetime

class StockTransfer(db.Model):
    __tablename__ = 'stock_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    source_canteen_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='RESTRICT'), nullable=False, index=True)
    destination_canteen_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    # Actually the products being transferred
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    
    status = db.Column(db.String(50), nullable=False, default='REQUESTED') # REQUESTED, APPROVED, DISPATCHED, IN_TRANSIT, RECEIVED, COMPLETED, CANCELLED
    
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    dispatched_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    received_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    idempotency_key = db.Column(db.String(100), unique=True, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source_canteen = db.relationship('Canteen', foreign_keys=[source_canteen_id])
    destination_canteen = db.relationship('Canteen', foreign_keys=[destination_canteen_id])
    product = db.relationship('Product')

    def __repr__(self):
        return f"<StockTransfer {self.quantity} of {self.product_id} from {self.source_canteen_id} to {self.destination_canteen_id} ({self.status})>"
