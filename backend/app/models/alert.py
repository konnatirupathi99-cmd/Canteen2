from ..extensions import db
from datetime import datetime

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False, index=True) # LOW_STOCK, OUT_OF_STOCK, HIGH_DEMAND, STOCKOUT_RISK, RESTOCK_RECOMMENDED, HIGH_WASTE, LONG_FULFILLMENT_TIME
    severity = db.Column(db.String(20), nullable=False, default='INFO') # INFO, WARNING, CRITICAL
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=True, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='CASCADE'), nullable=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    message = db.Column(db.String(255), nullable=False)
    
    status = db.Column(db.String(20), nullable=False, default='ACTIVE', index=True) # ACTIVE, ACKNOWLEDGED, RESOLVED
    
    # Deduplication key to prevent spam
    deduplication_key = db.Column(db.String(100), unique=True, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product')
    stall = db.relationship('Stall')

    def __repr__(self):
        return f"<Alert {self.severity} {self.alert_type} ({self.status})>"
