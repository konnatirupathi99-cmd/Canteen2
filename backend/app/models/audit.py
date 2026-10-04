from ..extensions import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    action = db.Column(db.String(100), nullable=False) # e.g. PRODUCT_CREATED, PRICE_CHANGED
    entity_type = db.Column(db.String(50), nullable=False) # e.g. Product, Category, Order
    entity_id = db.Column(db.Integer, nullable=False)
    
    # Store JSON snapshots of the changes
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id}>"
