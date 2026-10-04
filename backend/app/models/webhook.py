from ..extensions import db
from datetime import datetime

class WebhookSubscription(db.Model):
    __tablename__ = 'webhook_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    url = db.Column(db.String(512), nullable=False)
    secret = db.Column(db.String(255), nullable=False) # Used for HMAC signature
    
    event_types = db.Column(db.JSON, nullable=False) # e.g. ["ORDER_CREATED", "INVENTORY_LOW"]
    
    status = db.Column(db.String(50), nullable=False, default='ACTIVE') # ACTIVE, SUSPENDED
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WebhookSubscription {self.url} ({self.status})>"

class WebhookDelivery(db.Model):
    __tablename__ = 'webhook_deliveries'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('webhook_subscriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    event_id = db.Column(db.String(50), nullable=False, index=True) # Maps to OutboxEvent.id
    
    status = db.Column(db.String(50), nullable=False) # PENDING, SUCCESS, FAILED
    
    response_status = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    
    attempt_count = db.Column(db.Integer, default=1)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<WebhookDelivery {self.status} on {self.subscription_id}>"
