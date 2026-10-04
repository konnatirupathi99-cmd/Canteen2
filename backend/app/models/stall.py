from ..extensions import db
from datetime import datetime

class Stall(db.Model):
    __tablename__ = 'stalls'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    canteen_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='CASCADE'), nullable=True, index=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='ACTIVE') # ACTIVE, INACTIVE, TEMPORARILY_CLOSED

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Stall {self.name}>"
