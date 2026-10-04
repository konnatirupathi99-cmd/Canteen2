from ..extensions import db
from datetime import datetime, timezone
import uuid

class OutboxEvent(db.Model):
    __tablename__ = 'outbox_events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_type = db.Column(db.String(50), nullable=False) # e.g., 'Order'
    aggregate_id = db.Column(db.String(50), nullable=False)   # e.g., order.id
    event_type = db.Column(db.String(50), nullable=False)     # e.g., 'ORDER_CONFIRMED'
    payload = db.Column(db.JSON, nullable=False)              # The event data
    version = db.Column(db.String(10), nullable=False, default='v1')
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    correlation_id = db.Column(db.String(50), nullable=True, index=True)
    producer = db.Column(db.String(100), nullable=False, default='core_service')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<OutboxEvent {self.event_type} - {self.id}>"
