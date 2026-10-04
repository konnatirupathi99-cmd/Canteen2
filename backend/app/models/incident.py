from ..extensions import db
from datetime import datetime

class BusinessIncident(db.Model):
    __tablename__ = 'business_incidents'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    canteen_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='CASCADE'), nullable=True, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='CASCADE'), nullable=True, index=True)
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    incident_type = db.Column(db.String(50), nullable=False, index=True) # KITCHEN_DEGRADATION, PAYMENT_FAILURE_SPIKE, STOCKOUT_SPIKE
    severity = db.Column(db.String(20), nullable=False, default='WARNING') # WARNING, CRITICAL
    
    status = db.Column(db.String(20), nullable=False, default='OPEN', index=True) # OPEN, INVESTIGATING, MITIGATED, RESOLVED
    
    # Store JSON array of related alert IDs or order IDs that triggered this
    correlated_entities = db.Column(db.JSON, nullable=True) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    def __repr__(self):
        return f"<BusinessIncident {self.incident_type} ({self.status})>"
