from ..extensions import db
from datetime import datetime

class Policy(db.Model):
    __tablename__ = 'policies'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Scope resolution
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id', ondelete='CASCADE'), nullable=True, index=True)
    canteen_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='CASCADE'), nullable=True, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='CASCADE'), nullable=True, index=True)
    
    policy_key = db.Column(db.String(100), nullable=False, index=True)
    policy_value = db.Column(db.Text, nullable=False)
    
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Policy {self.policy_key}={self.policy_value}>"
