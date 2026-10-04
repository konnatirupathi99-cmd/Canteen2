from ..extensions import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default='USD')
    
    # INITIATED, PENDING, AUTHORIZED, CAPTURED, FAILED, CANCELLED, REFUNDED, UNKNOWN
    status = db.Column(db.String(50), nullable=False, default='INITIATED')
    
    provider = db.Column(db.String(50), nullable=False) # e.g., 'STRIPE', 'PAYPAL', 'CASH'
    provider_transaction_id = db.Column(db.String(100), nullable=True)
    
    idempotency_key = db.Column(db.String(100), unique=True, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f"<Payment {self.id} - {self.status}>"
