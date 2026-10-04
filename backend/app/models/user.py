from ..extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False) # SYSTEM_ADMIN, ORG_ADMIN, CANTEEN_MANAGER, CASHIER, KITCHEN_STAFF, CUSTOMER
    status = db.Column(db.String(50), nullable=False, default='ACTIVE') # ACTIVE, INACTIVE, SUSPENDED
    
    # Nullable, only relevant if role == KITCHEN_STAFF
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='SET NULL'), nullable=True)
    
    # Multi-tenancy
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stall = db.relationship('Stall', backref='staff', foreign_keys=[stall_id])

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
